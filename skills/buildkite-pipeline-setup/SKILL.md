---
name: buildkite-pipeline-setup
description: Buildkite CI/CD pipeline setup, migration, validation, hardening, and live pipeline management. Use when Codex needs to create, review, debug, or update Buildkite pipelines, .buildkite/pipeline.yml files, steps, queues, triggers, artifacts, annotations, secrets, OIDC, or deployment stages.
---

# Buildkite Pipeline Setup

Use this skill to design, create, review, or update high-quality Buildkite pipelines. Treat repository files as the source of truth first; only change live Buildkite pipelines after the user explicitly confirms the organization, pipeline, and intended mutation.

## Workflow

1. Inspect the repo before designing anything.
   - Run `python3 <skill>/scripts/inspect_repo_ci.py <repo> --format text`.
   - Read existing CI files, package manifests, build scripts, deploy scripts, Docker files, and release docs.
   - If an existing `.buildkite/pipeline.yml` exists, inspect it before proposing replacements.
2. Design a visible multi-stage `.buildkite/pipeline.yml`.
   - Include separate, named steps for install/setup, lint/static checks, tests, build/package, artifacts, and deploy/release where applicable.
   - Use `wait` steps between materially different phases.
   - Use `block` or branch/tag conditions for deploys and releases.
   - Add stable `key` values to command, trigger, block, input, and group steps so dependencies and future edits are reliable.
   - Target queues or agents when repo evidence or user input identifies runner requirements.
3. Reject one-node pipelines.
   - Do not create a single command step that hides all work behind `make ci`, `scripts/ci.sh`, or a long shell block.
   - A single bootstrap step is acceptable only when it runs `buildkite-agent pipeline upload` and expands into a separately versioned, visible, multi-step dynamic pipeline.
4. Validate locally.
   - Run `python3 <skill>/scripts/check_buildkite_pipeline.py <repo>/.buildkite/pipeline.yml`.
   - Fix validation errors before presenting the pipeline as complete.
   - If the pipeline uploads another YAML file dynamically, validate that target file too.
5. Configure live Buildkite only after confirmation.
   - Before any live mutation, restate the Buildkite org slug, pipeline slug/name, repository URL, default branch, cluster/queue, and exact operation.
   - Use read-only MCP/API calls first (`list_pipelines`, `get_pipeline`, `list_builds`, `list_annotations`).
   - Do not call `update_pipeline`, `create_build`, `rebuild_build`, `cancel_build`, or equivalent mutating operations until the user confirms.

## Pipeline Quality Bar

- Prefer repo-discovered commands over generic guesses. Use existing scripts if they are clear, but split them into observable Buildkite steps where possible.
- Keep pipelines reviewable: short commands, explicit labels, stable keys, dependencies, artifacts, and annotations for important summaries.
- Use Buildkite Secrets or OIDC for credentials. Never place secret values in YAML, generated scripts, logs, or final summaries.
- Keep deploys conservative: default to protected branches/tags plus a manual `block` unless the repo already has a safer automated release convention.
- For monorepos, use groups or dynamic pipeline generation so each package/service has clear checks without collapsing into one opaque step.
- Set skip/cancel intermediate build behavior at the live pipeline level when appropriate, but record it separately from repo YAML because it is pipeline metadata.

## References

- Read `references/pipeline-patterns.md` when designing or reviewing YAML structure, step types, dynamic pipelines, artifacts, annotations, conditionals, queues, or deploy gates.
- Read `references/security-and-live-ops.md` before handling secrets, OIDC, Buildkite MCP/API operations, live pipeline settings, or production deploy behavior.

## Script Notes

- `scripts/inspect_repo_ci.py` is read-only and emits deterministic repo inventory. Use it to find commands and CI signals; do not treat its candidates as final without reading the relevant files.
- `scripts/check_buildkite_pipeline.py` validates local guardrails for generated pipelines. Passing this script is necessary but not sufficient; still reason about repo-specific behavior and run the repo's own tests when feasible.
