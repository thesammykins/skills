# Plugin Loading And Dependencies

Read this file when deciding where a plugin should live, how it should import packages, or why it is not loading.

## Load locations

- Project-local plugins live in `.opencode/plugins/`.
- Global plugins live in `~/.config/opencode/plugins/`.
- npm plugins are listed in the `plugin` array in `opencode.json`.

## External dependencies

- Local plugins and local custom tools share dependencies from a `package.json` in the config directory that owns them.
- For project-local code, that usually means `.opencode/package.json`.
- OpenCode runs `bun install` for that config directory at startup.
- npm plugins and their dependencies are installed automatically with Bun and cached in `~/.cache/opencode/node_modules/`.

## Load order

OpenCode loads plugin sources in this order:

1. Global config in `~/.config/opencode/opencode.json`
2. Project config in `opencode.json`
3. Global plugin directory in `~/.config/opencode/plugins/`
4. Project plugin directory in `.opencode/plugins/`

Important consequences:

- Duplicate npm packages with the same name and version are loaded once.
- A local plugin and an npm plugin with similar names both load; they do not merge.
- Project-local plugin files load after global plugin files.

## Decide where the plugin belongs

- Use project-local files when behavior is repo-specific.
- Use a global plugin only when the user explicitly wants the behavior everywhere.
- Publish to npm when the plugin needs reuse across projects, versioning, or config-based installation.

## Verification checklist

- Confirm the intended load path exists and is the one OpenCode will scan.
- Confirm imported packages are present in the owning config directory `package.json` or in the npm package manifest.
- Start with one narrow hook or one narrow tool and verify observable behavior before expanding scope.
- Confirm the plugin actually loads through logs or visible behavior instead of assuming import success.
- Do not assume similar names will override or merge unless you are intentionally overriding a built-in tool.
