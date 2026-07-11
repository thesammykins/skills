---
name: opencode-server-integrations
description: Build and verify integrations against the OpenCode HTTP server exposed by `opencode serve`, including raw OpenAPI-style requests, SSE event handling, polyglot clients, and remote or headless setups. Use when integrating over HTTP directly instead of the SDK, when wiring non-Node clients, or when attaching tools to a running OpenCode backend. Prefer `opencode-sdk-builder` for Node/Bun work with `@opencode-ai/sdk`, and `opencode-plugin-author` for behavior implemented as OpenCode plugins.
---

# OpenCode Server Integrations

Treat this skill as the server-side integration guide for OpenCode over HTTP.

## Hold the boundary

- Prefer `opencode-sdk-builder` if the integration is in Node or Bun and can use `@opencode-ai/sdk`.
- Prefer `opencode-plugin-author` if the requested behavior should run inside OpenCode as a plugin, tool, hook, or built-in extension point.
- Use this skill when the client is polyglot, generated from OpenAPI, browser-based, remote, headless, or intentionally using raw HTTP.
- Use ACP only when the host expects an ACP subprocess over stdio or JSON-RPC. Do not force ACP into an HTTP integration.

Read supporting references only when needed.

- Read `references/server-session-and-events.md` when implementing the actual HTTP request flow, session lifecycle, or SSE handling.
- Read `references/server-runtime-auth-and-boundaries.md` when deciding how to start, secure, expose, or remotely operate the server.

## Start from the server surface

- Start the backend with `opencode serve`.
- Set `--port` and `--hostname` explicitly for stable automation. Defaults are `127.0.0.1:4096`.
- Add `--cors` once per allowed browser origin when the client runs in a browser.
- Set `OPENCODE_SERVER_PASSWORD` to enable HTTP basic auth. The username defaults to `opencode`, or override it with `OPENCODE_SERVER_USERNAME`.
- Use `http://<host>:<port>/doc` as the source of truth for the published OpenAPI 3.1 surface before writing client code.

Use `opencode attach <url>` only when you want a TUI connected to an existing remote backend. That is an operator workflow, not a replacement for HTTP client code.

## Build the integration around sessions

Model the workflow around a session, not around one-off prompts.

1. Check server health with `GET /global/health`.
2. Create or reuse a session with `POST /session` or `GET /session`.
3. Send work with `POST /session/:id/message` for synchronous replies or `POST /session/:id/prompt_async` for fire-and-forget submission.
4. Read conversation state with `GET /session/:id/message` or `GET /session/:id/message/:messageID`.
5. Abort long-running work with `POST /session/:id/abort` when needed.

Prefer the message endpoint over shelling out to `opencode run` when you are already integrating with a running server.

## Shape requests deliberately

- Pass `model`, `agent`, `system`, `tools`, and `parts` explicitly when the caller needs deterministic behavior.
- Treat `parts` as the real message payload. Do not assume plain text is the only content form.
- Use `noReply` only when the caller truly does not need an assistant response.
- Reuse the same session for iterative work so the server keeps context, todos, diffs, and permissions tied together.

## Handle events as a first-class stream

- Subscribe to `GET /event` for the standard instance event stream used during normal session work.
- Subscribe to `GET /global/event` only when the client specifically needs the global stream.
- Expect the first `/event` message to be `server.connected`.
- Build the client so SSE disconnects are recoverable. Reconnect, re-read session state, and continue instead of assuming the stream is durable.
- Treat SSE as progress and state notification, not as the sole source of truth. Confirm final state with normal REST reads.

## Keep remote and protocol boundaries clear

- Use `opencode serve` for HTTP integrations.
- Use `opencode acp` only for editors or tools that speak ACP over stdio.
- Use `/tui/*` endpoints only when you are intentionally driving an attached TUI client. Do not build general automation on TUI controls when the session and message APIs already cover the need.
- Use basic auth and narrow host binding before exposing the server beyond localhost.
- Add CORS only for known browser origins. Do not use broad origins by default.

## Verify end to end

Verify the exact path the user cares about.

1. Start `opencode serve` with explicit `--hostname`, `--port`, auth, and any required `--cors` values.
2. Confirm `GET /global/health` succeeds.
3. Open `/doc` and verify the paths and request fields you plan to use.
4. Create a session and send a minimal message.
5. Confirm the reply is readable through the message API.
6. Open an SSE connection to `/event` and confirm you receive `server.connected` plus follow-up events during a prompt.
7. If the client is remote, verify the same flow from the real network path, not only from localhost.

If verification fails, isolate the layer first: process startup, host binding, auth, CORS, HTTP request shape, session lifecycle, then SSE handling.
