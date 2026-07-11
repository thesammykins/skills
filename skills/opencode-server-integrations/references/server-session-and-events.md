# Server Session And Events

Read this file when implementing the actual HTTP client flow against `opencode serve`.

## Minimal session workflow

1. `GET /global/health`
2. `POST /session`
3. `POST /session/:id/message` for synchronous replies, or `POST /session/:id/prompt_async` for fire-and-forget submission
4. `GET /session/:id/message` or `GET /session/:id/message/:messageID`
5. `POST /session/:id/abort` when the run must stop early

Prefer this session-first workflow over repeatedly shelling out to `opencode run` when you already control a running server.

## Message request shape

The message body can include:

- `messageID`
- `model`
- `agent`
- `noReply`
- `system`
- `tools`
- `parts`

Treat `parts` as the real payload. Do not assume plain text is the only useful content form.

## Event streams

- `GET /event` is the standard instance event stream for normal session work.
- `GET /global/event` is the global stream.
- Expect the first `/event` message to be `server.connected`.
- Reconnect on SSE failure, then re-read session state before continuing.
- Use REST reads to confirm final state; do not trust SSE as the sole source of truth.

## Useful adjacent endpoints

- `GET /session/status` for status across all sessions
- `GET /session/:id/todo` for the todo list
- `GET /session/:id/diff` for file diff state
- `POST /session/:id/share` or `DELETE /session/:id/share` for sharing flows

## Verification checklist

- Verify health before creating sessions.
- Verify a session can receive at least one message and return a readable reply.
- Verify SSE produces `server.connected` and follow-up activity during a real prompt.
- Verify failure handling with a bad session ID or an aborted run.
