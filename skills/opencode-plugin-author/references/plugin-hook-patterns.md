# Plugin Hook Patterns

Read this file when implementing or reviewing a concrete OpenCode plugin behavior.

## Choose the narrowest hook

- Use `tool.execute.before` to block, rewrite, or validate a tool call before execution.
- Use `tool.execute.after` to inspect results, redact output, or add post-processing after execution.
- Use `shell.env` to inject environment variables into shell execution.
- Use `event` only when one handler filtering many event types is simpler than dedicated hooks.
- Use `experimental.session.compacting` only when the plugin must change compaction behavior, and treat it as unstable.

## Common patterns

### Block `.env` reads

```ts
export const EnvProtection = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool === "read" && output.args.filePath.includes(".env")) {
        throw new Error("Do not read .env files")
      }
    },
  }
}
```

### Patch-hook gotcha

- For patch interception, the tool name is `apply_patch`, not `patch`.
- The patch body lives in `output.args.patchText`, not `output.args.filePath`.

### Inject environment variables

```ts
export const InjectEnv = async () => {
  return {
    "shell.env": async (input, output) => {
      output.env.PROJECT_ROOT = input.cwd
    },
  }
}
```

### Add a plugin-provided tool

```ts
import { tool, type Plugin } from "@opencode-ai/plugin"

export const CustomToolsPlugin: Plugin = async () => {
  return {
    tool: {
      mytool: tool({
        description: "Example tool",
        args: { foo: tool.schema.string() },
        async execute(args) {
          return `Hello ${args.foo}`
        },
      }),
    },
  }
}
```

Use a plugin tool only when the behavior is still plugin-shaped. If the whole requirement is just "make a callable tool", prefer `.opencode/tools/`.

### Log through OpenCode

```ts
export const LoggingPlugin = async ({ client }) => {
  await client.app.log({
    body: {
      service: "my-plugin",
      level: "info",
      message: "Plugin initialized",
    },
  })

  return {}
}
```

## Review checklist

- Is the chosen hook the narrowest one that satisfies the requirement?
- Does the plugin avoid broad interception of unrelated tools or sessions?
- Are any built-in tool overrides explicit and intentional?
- Are guardrails tested on both allow and deny paths?
- Is unstable behavior, like compaction interception, clearly justified?
