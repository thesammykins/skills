# Gemini CLI Operations

Use this reference when the task involves installing, authenticating, selecting models, diagnosing quota, or scripting Gemini CLI. Facts here were checked against Gemini CLI official docs and local CLI help on 2026-05-05.

## Quick Checks

- Verify availability with `command -v gemini` and `gemini --version`.
- Use headless mode with `gemini -p "..."` or `gemini --prompt "..."`.
- Use `--output-format json` for one JSON envelope and `--output-format stream-json` for JSONL events.
- Use `--approval-mode=plan` for read-only context gathering.
- Use `--include-directories path1,path2` or repeated flags when analysis spans adjacent repos or packages.

## JSON Envelope

`gemini --output-format json` returns one JSON object.

```json
{
  "response": "model final answer as a string",
  "stats": { "models": {}, "tools": {}, "files": {} },
  "error": { "message": "optional failure details" }
}
```

The wrapper script parses this envelope and then parses `response` as JSON. If Gemini returns Markdown or prose, the wrapper emits `ok:false` with `error.kind:"model_response_not_json"`.

## Authentication

- Local interactive use should start with `gemini`, choose `Sign in with Google`, and complete browser auth.
- Google AI Pro and Ultra subscribers should sign in with the Google account attached to the subscription.
- Most individual Google accounts do not require a Google Cloud project.
- Workspace, school, company, Code Assist license, and Vertex AI paths may require `GOOGLE_CLOUD_PROJECT` or `GOOGLE_CLOUD_PROJECT_ID`.
- Headless mode uses cached credentials when available.
- Without cached login, headless mode needs environment-based auth such as `GEMINI_API_KEY` or Vertex AI variables.
- Never print or persist API keys, service account JSON, OAuth tokens, or `.gemini/.env` contents.

## Quotas And Limits

- Google account with Gemini Code Assist Individual: documented at 1,000 requests per user per day.
- Google AI Pro: documented at 1,500 requests per user per day.
- Google AI Ultra: documented at 2,000 requests per user per day.
- Gemini API key unpaid tier: documented at 250 requests per user per day and Flash-only access.
- Requests are also limited per user per minute and subject to service availability.
- Use `/stats model` in an interactive Gemini session to inspect current usage and limits.

If quota or auth blocks a task, do not loop. Fall back to `explore` agents or ask the user whether to switch authentication or wait.

## Model Selection

- Prefer `gemini-3.1-pro-preview` for high-context codebase reasoning when available.
- Use `pro` if the caller wants Gemini CLI's model alias routing.
- Use `flash` only when latency matters more than deep reasoning.
- Local CLI 0.40.1 supports `--model`, `--prompt`, `--output-format`, `--approval-mode`, `--include-directories`, and `--skip-trust`.

## Context Loading

- Use `@path` references in prompts to ask Gemini to read files or directories.
- Gemini's `@` path handling is git-aware by default and excludes common ignored content such as `.git`, `node_modules`, build outputs, and `.env` files.
- Use `--include-directories` for multi-root workspaces, monorepos with sibling packages, or docs living outside the repo root.
- Gemini also loads hierarchical `GEMINI.md` files. Keep OpenCode's own instructions authoritative for OpenCode behavior.

## Safety Defaults

- Use `--approval-mode=plan` for this skill.
- Do not use `--approval-mode=yolo` for context gathering.
- Use `--skip-trust` only when the caller has intentionally trusted the workspace.
- Treat Gemini output as advisory. Re-read local files before editing, filing findings, or making claims to the user.
