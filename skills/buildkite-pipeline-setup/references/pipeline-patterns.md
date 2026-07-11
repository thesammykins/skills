# Buildkite Pipeline Patterns

Use these patterns after inspecting the repository. Prefer repo-owned scripts and manifests over generic templates.

## Official References

- Defining steps: https://buildkite.com/docs/pipelines/configure/defining-steps
- Command steps: https://buildkite.com/docs/pipelines/configure/step-types/command-step
- Conditionals: https://buildkite.com/docs/pipelines/configure/conditionals
- Pipeline upload CLI: https://buildkite.com/docs/agent/v3/cli/reference/pipeline
- Artifacts: https://buildkite.com/docs/guides/artifacts
- Annotations: https://buildkite.com/docs/pipelines/configure/annotations
- Queues: https://buildkite.com/docs/agent/v3/queues

## Baseline Shape

Start with a visible flow:

```yaml
steps:
  - label: ":package: Install"
    key: "install"
    command: "..."

  - wait

  - label: ":mag: Lint"
    key: "lint"
    command: "..."

  - label: ":test_tube: Test"
    key: "test"
    command: "..."
    artifact_paths:
      - "coverage/**/*"

  - wait

  - label: ":hammer: Build"
    key: "build"
    command: "..."
    artifact_paths:
      - "dist/**/*"
```

Adapt labels and commands to the repo. Stable `key` values should be lowercase, deterministic, and safe to reference from `depends_on`.

## Step Types

- Use command steps for install, lint, tests, builds, packaging, and deploy commands.
- Use `wait` between phases so failures stop later phases cleanly.
- Use `block` before production deploys, App Store submissions, destructive migrations, or irreversible releases.
- Use `trigger` steps for downstream deployment or integration pipelines when the repo already separates build and release ownership.
- Use `group` steps for monorepos, matrix-style package checks, or related jobs that should be visually collapsed without losing individual step visibility.
- Use `input` only when the build needs a human-supplied value; otherwise prefer branch/tag conditionals and metadata.

## Dynamic Pipelines

Dynamic upload is appropriate when the repo has many packages/services or build steps depend on generated metadata. Keep the bootstrap small:

```yaml
steps:
  - label: ":pipeline: Generate pipeline"
    key: "pipeline-upload"
    command: "scripts/buildkite/upload_pipeline.sh"
```

The uploaded pipeline must itself be versioned, readable, and multi-step. Validate every static YAML file involved. If the generator writes YAML from code, inspect the generator and run it in a dry-run mode when available.

## Conditions and Gates

- Use step-level `if` for branch, tag, pull request, commit message, or environment-based routing.
- Remember that Buildkite step conditionals are evaluated at pipeline upload time, not after earlier step results.
- Do not depend on one step's runtime result from a later static `if`; upload a dynamic step after checking the prior step outcome if that behavior is required.
- Production deploys should have at least one hard gate:
  - branch condition such as `build.branch == "main"`
  - tag condition such as `build.tag != null`
  - manual `block` step before the deploy
  - trigger to a protected downstream deploy pipeline

## Artifacts and Annotations

- Add `artifact_paths` for coverage reports, test reports, compiled packages, screenshots, logs, and generated release artifacts that users need after the job.
- Use `buildkite-agent annotate` for summarized test results, release notes, migration plans, or links to important artifacts.
- Do not upload secrets, raw environment dumps, private keys, unredacted logs, or full dependency caches as artifacts.

## Queues and Agents

- Add `agents` at the root when every step needs the same queue.
- Add step-level `agents` when only some steps need specialized runners, such as macOS, GPU, Docker-in-Docker, deployment networking, or signing credentials.
- Do not invent queue names. Use queue tags found in existing Buildkite config, repo docs, user input, or live pipeline settings.

## Anti-Patterns

- A single `make ci` or `scripts/ci.sh` command as the whole pipeline.
- Long shell blocks that install, lint, test, build, and deploy in one step.
- Deploy steps without branch/tag/manual protection.
- Inline secret values in YAML or scripts.
- Plugin use that hides critical behavior without comments or repo docs.
- Replacing existing CI semantics without mapping old checks to new Buildkite steps.
