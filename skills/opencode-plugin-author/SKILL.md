---
name: opencode-plugin-author
description: Author and review OpenCode plugins that live in `.opencode/plugins/` or are loaded from npm packages. Use when deciding plugin vs custom tool, wiring plugin hooks or plugin-provided tools, setting up plugin dependencies, or verifying local and npm-loaded OpenCode plugin behavior. Prefer `opencode-sdk-builder` for Node or Bun app integrations built with `@opencode-ai/sdk`, and prefer `opencode-server-integrations` for raw HTTP integrations against `opencode serve`.
---

# OpenCode Plugin Author

Decide the extension point first.

- Use a plugin when the behavior must react to OpenCode runtime events, adjust execution through hooks, inject shell environment, add plugin-provided tools, or ship reusable behavior through `.opencode/plugins/` or npm.
- Use a custom tool in `.opencode/tools/` when the job is only to expose one or more callable tools to the model and no lifecycle hooks are needed.
- Prefer `opencode-sdk-builder` when the user is building a separate Node or Bun app around `@opencode-ai/sdk` rather than extending OpenCode from inside its plugin system.
- Prefer `opencode-server-integrations` when the user is integrating against `opencode serve` over HTTP instead of loading code into OpenCode.

Keep the implementation inside the OpenCode plugin boundary.

- Put project-local plugins in `.opencode/plugins/`.
- Put global plugins in `~/.config/opencode/plugins/` only when the user explicitly wants user-wide behavior.
- Load published plugins from npm through the `plugin` array in `opencode.json`.
- Do not treat generic Codex plugin formats as compatible with OpenCode plugins.

Read supporting references only when needed.

- Read `references/plugin-hook-patterns.md` when implementing or reviewing a specific hook, plugin tool, guardrail, or event-driven behavior.
- Read `references/plugin-loading-and-dependencies.md` when deciding local vs global vs npm loading, external dependencies, load order, or startup verification.

Start with the smallest working shape.

```ts
import type { Plugin } from "@opencode-ai/plugin"

export const MyPlugin: Plugin = async ({ client, $, directory, worktree, project }) => {
  return {
    // add only the hooks or tools you need
  }
}
```

Use JavaScript or TypeScript modules that export one or more plugin functions. Keep plugin logic narrow, explicit, and easy to trace.

Set up dependencies in the right place.

- For local plugins or local custom tools that import packages, add `.opencode/package.json` in the config directory that owns them.
- Rely on OpenCode running `bun install` for that config directory at startup.
- Use npm packaging when the user wants reuse across projects, versioning, or config-based loading.
- Avoid introducing dependencies for simple hook logic that can stay in plain JS or TS.

Choose hooks deliberately.

- Use `tool.execute.before` and `tool.execute.after` for guardrails, argument rewriting, auditing, or post-processing around tool calls.
- Use `shell.env` to inject environment variables into shell execution.
- Use session events such as `session.created`, `session.updated`, `session.idle`, and `session.error` for lifecycle behavior.
- Use `experimental.session.compacting` only when the plugin must influence compaction behavior, and treat it as an unstable surface.
- Use `permission.asked` or `permission.replied` only when the plugin truly needs to react to approval flow.
- Use `tui.*` hooks only for TUI-facing behavior.
- Use a broad `event` handler only when filtering many event types in one place is simpler than dedicated hooks.

Add plugin-provided tools only when the extension is still plugin-shaped.

- Define tools with `tool()` from `@opencode-ai/plugin`.
- Give every plugin tool a unique name unless intentionally overriding a built-in tool.
- Treat overriding built-ins as a high-risk change; do it only when the user explicitly wants replacement behavior.
- If the requirement is mostly "create a callable tool", prefer `.opencode/tools/` over a plugin.

Use the runtime helpers that OpenCode provides.

- Use `client.app.log()` for structured logging instead of `console.log`.
- Use Bun shell through `$` for subprocesses triggered by the plugin.
- Use `directory` for the session working directory and `worktree` for the repo root.
- Keep filesystem access scoped to the intended project or config directory.

Respect packaging and loading boundaries.

- Project config and global config merge; project-local `.opencode/plugins/` loads after global config and global plugin directories.
- Plugins from `opencode.json` and local plugin files can both load; similar names do not merge.
- Duplicate npm packages with the same name and version are loaded once.
- Document whether the plugin is meant to be local-only or npm-published before adding packaging files.

Author safely.

- Prefer pure functions and explicit hook conditions over hidden global state.
- Fail with clear errors when blocking dangerous behavior.
- Do not hardcode secrets in plugin code; read them from environment or config inputs.
- Avoid broad interception that changes unrelated tools or sessions.
- Comment only where the hook intent would otherwise be easy to misread.

Verify in a tight loop.

- Check the target load path first: `.opencode/plugins/`, `~/.config/opencode/plugins/`, or `opencode.json` plugin entries.
- If the plugin imports packages, confirm `.opencode/package.json` or the npm package manifest matches those imports.
- Start with one narrow hook or one narrow tool and verify behavior before adding more events.
- Exercise the exact event path the plugin depends on.
- Confirm logs or observable behavior through OpenCode rather than assuming the module loaded.
- Test both success and refusal paths for any guardrail hook.

Review plugins with these questions.

- Is a plugin actually needed, or would `.opencode/tools/` be simpler?
- Is the chosen hook the narrowest hook that satisfies the requirement?
- Are dependencies scoped to the correct config directory or npm package?
- Does the plugin avoid unsafe overrides, secret leakage, and unintended global behavior?
- Is the loading model clear: project-local, global-local, or npm?

Keep this skill focused on in-process OpenCode plugins. Hand off adjacent work instead of stretching scope.
