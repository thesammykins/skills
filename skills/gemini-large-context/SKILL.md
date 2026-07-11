---
name: gemini-large-context
description: >
  Use Gemini CLI in headless JSON mode for high-level codebase analysis, repo
  overviews, architecture reports, broad context gathering, unfamiliar codebase
  mapping, multi-file bug triage, dependency tracing, migration planning,
  cross-cutting reviews, and other tasks that benefit from Gemini's large
  context window. Use when a user asks to analyze or understand a codebase at a
  high level, explain main modules or flows, map a whole project, investigate a
  broad behavior across many files, or when local Grep/Glob or explore agents
  would require many passes. Fall back to explore agents when Gemini is
  unavailable, unauthenticated, quota-limited, privacy-sensitive, or when
  precise targeted search is enough.
---

# Gemini Large Context

Use Gemini CLI as a read-only large-context consultant. Keep OpenCode responsible for final edits, verification, and user-facing conclusions; treat Gemini output as evidence-gathering or a second-pass analysis that must be checked against local files before acting.

## Default Workflow

1. Scope the question locally first with `Glob`, `Grep`, and targeted reads so the Gemini prompt names the real repo, files, symbols, and desired output schema.
2. Use this skill when the useful context is broad: whole-repo architecture, cross-cutting behavior, dependency tracing, hidden coupling, broad code review, migration impact, or bug reports spanning many files.
3. Run Gemini in headless JSON mode with read-only approval using `scripts/gemini-json.mjs`; prefer `gemini-3.1-pro-preview` for high-context reasoning.
4. Require path-based evidence in the prompt. Gemini should cite files, symbols, commands, and uncertainty rather than making unsupported claims.
5. Parse the wrapper's normalized JSON, then verify important claims locally with OpenCode tools before editing or reporting findings.
6. Fall back to `explore` agents or normal local search when Gemini is not available, authentication fails, quota is exhausted, the code is sensitive, or the task is narrow enough for targeted grep.

## Wrapper Usage

Run from this skill directory, or use the absolute path shown by the skill loader:

```bash
node scripts/gemini-json.mjs \
  --model gemini-3.1-pro-preview \
  --workdir /path/to/repo \
  --include-dir /path/to/adjacent/package \
  --prompt 'Analyze @src/ and return the requested JSON schema.'
```

The wrapper always prints JSON for agent callers. On success, `response` is the parsed JSON object returned by Gemini. On failure, `error.kind` identifies the failure class.

Use `--prompt-file` for longer prompts and `--schema-file` when a task needs a precise result shape:

```bash
node scripts/gemini-json.mjs --workdir "$PWD" --prompt-file /tmp/gemini-prompt.md --schema-file /tmp/schema.json
```

## Prompt Contract

Ask Gemini for structured JSON only. A good prompt includes:

- The exact task and why Gemini's large context helps.
- Relevant directories with `@path` references or `--include-dir`.
- A required JSON schema with fields for `summary`, `findings`, `evidence`, `uncertainty`, and `next_steps`.
- Instructions to separate verified facts from hypotheses.
- Instructions to avoid edits, shell commands with side effects, and secret disclosure.

Read `references/prompt-patterns.md` for reusable schemas and prompts.

## Operational Notes

- Read `references/gemini-cli-operations.md` when installing, authenticating, selecting models, or diagnosing Gemini CLI behavior.
- Read `references/fallbacks.md` when Gemini fails, output is malformed, quota is hit, or the task should use `explore` instead.
- Do not pass secrets, `.env` contents, private keys, credentials, customer data, or unrelated personal files to Gemini.
- Do not let Gemini be the only source of truth for bugs, security findings, or implementation decisions; verify locally before acting.
- Prefer `--approval-mode=plan` for this skill. Do not run Gemini with broad write or shell approval for context gathering.
