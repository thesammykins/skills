# Fallbacks And Failure Handling

Use this reference when deciding between Gemini CLI, `explore` agents, and local tools.

## Prefer Gemini CLI

- Whole-repo architecture summaries where many files may matter.
- Cross-cutting bug reports with unknown entrypoints.
- Migration planning that spans packages, tests, docs, and config.
- Dependency tracing where the call graph is wider than a few files.
- Second-opinion analysis after local context gathering finds multiple plausible causes.

## Prefer Explore Agents Or Local Tools

- The target file, symbol, or string is already known.
- You need exact grep results, counts, or narrow file discovery.
- The repository contains sensitive or regulated data that should not leave the machine.
- Gemini CLI is unauthenticated, quota-limited, offline, or returning malformed output.
- The question requires deterministic local state, such as current git diff, test output, or generated artifacts.

## Error Handling

- `gemini_cli_not_found`: use local tools and tell the user Gemini CLI is not installed or not on PATH.
- `gemini_cli_failed`: inspect `error.message`; if it indicates auth or quota, fall back instead of retrying repeatedly.
- `gemini_cli_timeout`: narrow the prompt, add specific `@paths`, or split the task into smaller questions.
- `gemini_cli_output_not_json`: check CLI version and rerun once with a smaller prompt if the task still needs Gemini.
- `model_response_not_json`: tighten the schema and rerun once; after a second malformed response, fall back.
- `missing_prompt` or `invalid_arguments`: fix the wrapper call locally.

## Fallback Explore Prompt

When Gemini is unavailable, launch `explore` agents with a bounded request:

```text
Perform a medium-thorough codebase search for <question>. Return only:
- relevant files and symbols
- short evidence snippets or line references
- likely next files to read
- open questions
Do not edit files.
```

Use multiple `explore` agents in parallel for independent domains, such as API, UI, data layer, and tests.

## Verification Rule

Before acting on Gemini output, verify at least the files and symbols named in the top findings with local reads or greps. If Gemini cites missing files, wrong symbols, or stale behavior, downgrade confidence and continue with local exploration.
