# SDK Client And Session Patterns

Read this file when choosing SDK client mode or wiring the main session flow.

## Choose the client mode first

### Embedded client

Use `createOpencode()` when the integration should start and own its own OpenCode server process.

- Good fit for CLIs, scripts, tests, and local automation.
- Useful options include `hostname`, `port`, `signal`, `timeout`, and inline `config` overrides.
- Always close the embedded server when the process is done.

```ts
import { createOpencode } from "@opencode-ai/sdk"

const { client, server } = await createOpencode()

try {
  // use client
} finally {
  server.close()
}
```

### Attached client

Use `createOpencodeClient()` when a server is already running.

- Good fit for daemons, local web apps, long-lived tools, and repeated automation.
- Configure `baseUrl` explicitly.
- Use this layer for custom `fetch`, auth headers, or transport wrappers instead of rewriting SDK calls.

```ts
import { createOpencodeClient } from "@opencode-ai/sdk"

const client = createOpencodeClient({
  baseUrl: process.env.OPENCODE_BASE_URL ?? "http://127.0.0.1:4096",
})
```

## Prefer a session-first workflow

1. Create or reuse a session.
2. Inject durable context with `noReply: true` when needed.
3. Send the active task with `session.prompt()`.
4. Inspect prior turns with `session.messages()` or `session.message()` instead of reconstructing state manually.
5. Use `session.abort()`, fork, summarize, or delete deliberately.

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
```

## Related operations

- Use `session.command()` for slash-command behavior.
- Use `session.shell()` only when the integration intentionally delegates shell execution through OpenCode.
- Use `client.global.health()` as the cheapest reachability check before larger flows.

## Review checklist

- Is the client mode appropriate for the runtime?
- Does embedded mode clean up the server?
- Does the integration reuse sessions deliberately instead of creating sprawl?
- Does it use typed `parts` instead of hand-built blobs where structure matters?
