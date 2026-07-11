# Prompt Patterns

Use these patterns when asking Gemini CLI for large-context help. Keep prompts explicit, bounded, and schema-first.

## Common Contract

Append this to most prompts or pass it as `--schema`.

```json
{
  "ok": true,
  "summary": "One concise paragraph.",
  "findings": [
    {
      "title": "Finding title",
      "severity": "critical|high|medium|low|info",
      "confidence": "high|medium|low",
      "evidence": ["path/to/file:line or symbol"],
      "explanation": "Why it matters.",
      "recommended_action": "Smallest useful next action."
    }
  ],
  "evidence": [
    { "path": "path/to/file", "symbol": "Name", "reason": "Why this file matters" }
  ],
  "uncertainty": ["Assumptions or missing evidence."],
  "next_steps": ["Local verification step for OpenCode."]
}
```

## Architecture Map

```text
Analyze this repository architecture using Gemini's large context window.

Context:
- Repo root: @./
- Focus areas: <areas>
- Ignore generated files, vendored code, lockfiles, and secrets.

Return JSON with:
- summary
- main_components: [{name, responsibility, key_files, dependencies}]
- request_or_data_flows: [{name, entrypoints, steps, storage, external_services}]
- cross_cutting_concerns: [{concern, files, notes}]
- risks_or_unknowns
- verification_steps_for_opencode
```

## Multi-File Bug Triage

```text
Investigate this bug report across the codebase, but do not edit files or run side-effecting commands.

Bug report:
<paste bug report>

Context:
- Relevant source: @src/
- Tests: @tests/
- Config: @package.json @tsconfig.json

Return JSON with:
- likely_root_causes ranked by confidence
- evidence with file paths and symbols
- reproduction_hypotheses
- minimal_fix_options
- tests_or_commands_opencode_should_run
- uncertainty
```

## Broad Code Review

```text
Review the current implementation for behavioral bugs, regressions, and missing tests. Prioritize correctness over style.

Context:
- Changed files: <paths or @paths>
- Nearby code: <paths or @paths>
- Product expectation: <brief expectation>

Return JSON with:
- findings ordered by severity
- each finding must include file evidence, user impact, and a concrete fix direction
- missing_tests
- false_positive_risks
```

## Dependency Or Call-Graph Trace

```text
Trace how <feature/symbol/API> is implemented and used across this codebase.

Context:
- Repo root: @./
- Known anchors: <symbols/files>

Return JSON with:
- entrypoints
- core_types_or_functions
- call_or_data_flow
- storage_or_network_boundaries
- tests_covering_the_flow
- files_opencode_should_read_next
```

## Migration Impact

```text
Estimate the impact of changing <old behavior/API> to <new behavior/API>.

Context:
- Repo root: @./
- Known affected files: <paths>
- Constraints: <compatibility, rollout, tests>

Return JSON with:
- affected_areas
- breakage_risks
- migration_sequence
- files_to_modify
- tests_to_add_or_update
- questions_before_implementation
```

## Prompt Hygiene

- Ask Gemini to cite paths and symbols, not vague module names.
- Ask for confidence levels and uncertainty.
- Ask for OpenCode verification steps, not blind implementation.
- Avoid sending unrelated directories just because the context window is large.
- Avoid asking Gemini to make final decisions about security, production safety, or data handling without local verification.
