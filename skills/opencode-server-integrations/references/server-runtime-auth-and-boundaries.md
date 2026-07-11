# Server Runtime, Auth, And Boundaries

Read this file when deciding how to start, secure, expose, or remotely operate the server.

## Start the server deliberately

Use `opencode serve [--port <number>] [--hostname <string>] [--cors <origin>]`.

- Default host and port are `127.0.0.1:4096`.
- Pass `--port` and `--hostname` explicitly for stable automation.
- Pass `--cors` once per browser origin that needs access.
- Enable mDNS only when discovery is useful for the environment.

## Protect exposed servers

- Set `OPENCODE_SERVER_PASSWORD` to enable HTTP basic auth.
- The username defaults to `opencode`; override it with `OPENCODE_SERVER_USERNAME` when needed.
- Use narrow host binding and known CORS origins before exposing the server beyond localhost.

## Keep protocol boundaries clear

- Prefer `opencode-sdk-builder` for Node/Bun clients using `@opencode-ai/sdk`.
- Use raw HTTP here for polyglot, browser, generated OpenAPI, or intentionally low-level integrations.
- Use `opencode attach <url>` only when you want a TUI connected to an existing server.
- Use `/tui/*` endpoints only when intentionally driving a TUI client.
- Use `opencode acp` only for editors or hosts that expect ACP over stdio or JSON-RPC.

## Use the published spec

- Treat `http://<host>:<port>/doc` as the source of truth for the current OpenAPI 3.1 surface.
- Check `/doc` before generating clients or hardcoding endpoint assumptions.

## Remote verification checklist

- Verify the server starts with the intended host, port, auth, and CORS settings.
- Verify `GET /global/health` locally and from the real remote path if remote use matters.
- Verify `/doc` reflects the endpoints the client plans to use.
- Verify browser clients from the real origin, not just from localhost tools.
