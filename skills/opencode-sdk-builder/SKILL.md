---
name: opencode-sdk-builder
description: Build or review Node.js and Bun integrations that use `@opencode-ai/sdk` to control OpenCode programmatically. Use when wiring embedded or attached SDK clients, managing sessions and prompts, handling structured output or event streams, or validating a JS/TS integration against a local OpenCode instance. Prefer `opencode-plugin-author` for behavior that runs inside OpenCode as a plugin, and `opencode-server-integrations` for non-SDK or polyglot HTTP integrations against `opencode serve`.
---

# OpenCode SDK Builder

Use `@opencode-ai/sdk` for JavaScript or TypeScript integrations that should talk to OpenCode through the generated SDK instead of raw HTTP.

Do not use this skill for plugin authoring inside OpenCode. Prefer `opencode-plugin-author` when the behavior belongs in an OpenCode plugin.

Do not use this skill for other languages, handwritten HTTP clients, or generic OpenAPI integrations. Prefer `opencode-server-integrations` for direct `opencode serve` usage.

Read supporting references only when needed.

- Read `references/sdk-client-and-session-patterns.md` when choosing embedded vs attached client mode, wiring sessions, or reviewing the main request flow.
- Read `references/sdk-structured-output-and-events.md` when the integration needs machine-readable output, event streaming, or tighter verification around SDK response handling.

## Working Rules

- Prefer the SDK over manual fetch calls when the project is Node.js or Bun.
- Keep the integration thin: construct the client, create or attach to a session, send parts, inspect typed responses, and close embedded servers.
- Treat the installed SDK types and the package version in the workspace as the source of truth when examples in docs drift.
- Reuse an attached client for long-lived tools or repeat invocations to avoid restarting OpenCode on every request.
- Prefer typed `parts` arrays over building one large string when the request has distinct inputs.
- Treat sessions as durable conversation state. Create, reuse, fork, summarize, abort, or delete them deliberately.
- Verify behavior against a real local OpenCode instance before considering the work done.

## Client Choice

Choose the client mode before writing code.

### Embedded client

Use `createOpencode()` when the integration should boot and own its own OpenCode server process.

- Use for CLIs, scripts, tests, and local automations that should be self-contained.
- Pass inline `config` only for targeted overrides; assume normal `opencode.json` still applies.
- Close the server when the process is done.

Baseline pattern:

```ts
import { createOpencode } from "@opencode-ai/sdk"

const opencode = await createOpencode()
const { client, server } = opencode

try {
  // use client
} finally {
  server.close()
}
```

### Attached client

Use `createOpencodeClient()` when OpenCode is already running via `opencode serve`, `opencode web`, or another embedded owner.

- Use for daemons, local web apps, test harnesses, and tools that should avoid cold-start cost.
- Point `baseUrl` at the running server.
- If the integration needs custom fetch behavior, auth headers, or transport wrappers, put them here rather than rewriting SDK calls.

Baseline pattern:

```ts
import { createOpencodeClient } from "@opencode-ai/sdk"

const client = createOpencodeClient({
  baseUrl: process.env.OPENCODE_BASE_URL ?? "http://127.0.0.1:4096",
})
```

## Session Lifecycle

Manage sessions explicitly.

1. Create a session with a useful title when starting a new task thread.
2. Reuse an existing session when continuity matters.
3. Use `noReply: true` to inject context without triggering an assistant turn.
4. Abort a running session instead of layering another prompt on top of a stuck request.
5. Summarize or fork when the thread is getting long or when you need a branch of work.
6. Delete sessions only when cleanup is intentional.

Preferred flow:

```ts
const session = await client.session.create({
  body: { title: "Review OpenCode integration" },
})

await client.session.prompt({
  path: { id: session.data.id },
  body: {
    noReply: true,
    parts: [{ type: "text", text: "Repository context goes here." }],
  },
})

const reply = await client.session.prompt({
  path: { id: session.data.id },
  body: {
    parts: [{ type: "text", text: "Find integration risks." }],
  },
})
```

## Prompt And Message Patterns

- Send `parts` as structured inputs. Start with text parts unless the app already uses richer message parts.
- Keep durable instructions in earlier context turns; keep the current ask narrow and task-specific.
- Use `model` or `agent` only when the integration has a concrete reason to override defaults.
- Use `session.messages()` or `session.message()` when the integration needs to inspect prior turns instead of reconstructing state manually.
- Use `session.command()` for slash-command behavior and `session.shell()` only when the integration intentionally delegates shell execution through OpenCode.

Prefer this shape:

```ts
const result = await client.session.prompt({
  path: { id: sessionId },
  body: {
    parts: [
      { type: "text", text: "Review this plan." },
      { type: "text", text: planMarkdown },
    ],
  },
})
```

## Structured Output

Use structured output when the caller needs machine-consumable data, not prose parsing.

- Check the installed SDK type for the exact request field name before coding. The current docs use both `format` and `outputFormat` in different sections, so do not cargo-cult either name blindly.
- Pass a focused JSON schema using the field your installed SDK version exposes.
- Keep the schema small and well-described.
- Mark required fields explicitly.
- Check `result.data.info.error` for `StructuredOutputError` and handle retries or fallback behavior explicitly.
- Read the validated payload from `result.data.info.structured_output`.

Use text output when the caller needs narrative reasoning, diffs, or free-form recommendations.

## Event Streaming

Use `client.event.subscribe()` when the integration needs live status, progress, or cross-session observability.

- Consume the stream with `for await`.
- Stop listening when the task or process ends.
- Use streaming for monitoring and coordination, not as a substitute for fetching final typed resources.
- Treat the first connection event as transport confirmation, then filter for the event types the integration actually cares about.

Baseline pattern:

```ts
const events = await client.event.subscribe()

for await (const event of events.stream) {
  if (event.type === "server.connected") continue
  // handle relevant events
}
```

## Verification

Verify the integration with real calls.

1. Confirm OpenCode is reachable with `client.global.health()`.
2. Create a disposable session and send a minimal prompt.
3. Verify the expected response shape, including `parts`, message metadata, and structured output if used.
4. If using attached mode, test against a real `opencode serve` instance.
5. If using embedded mode, verify startup and clean shutdown.
6. If using event streaming, confirm the stream connects and emits at least one real event beyond the initial connection handshake.
7. Exercise failure paths: invalid session ID, aborted request, or malformed structured output expectations.

Do not mark the integration complete based only on static typing.

## Review Focus

When reviewing an `@opencode-ai/sdk` integration, check for:

- wrong client mode for the runtime shape
- leaked embedded servers or missing cleanup
- accidental session sprawl instead of reuse or fork
- stringly typed response handling where SDK types already exist
- parsing prose where structured output should be used
- event subscriptions that never terminate
- direct HTTP calls to `opencode serve` where the SDK should be the default
