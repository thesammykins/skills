---
name: hardening-github-actions
description: Audits and hardens GitHub Actions workflows, composite actions, and Dependabot configuration with zizmor, then adds an ongoing zizmor-action workflow. Use when asked to secure, audit, or remediate GitHub Actions using zizmor.
---

# Hardening GitHub Actions

Hardens a repository's GitHub Actions surface with `zizmor` by fixing each concern independently before adding continuous auditing.

## Core Principles

- Treat composite actions, workflows, Dependabot, and the ongoing audit workflow as separate concerns.
- Fix existing findings first. Add the `zizmor-action` workflow only after local `zizmor` audits pass, so the new workflow starts green.
- Prefer one PR for small repositories, but use logical commits for each concern: composite action fixes, workflow fixes, Dependabot fixes, and the new audit workflow.
- Prefer `zizmor` autofixes for mechanical changes, but review every diff. Use unsafe autofixes only after understanding the generated change.
- Suppress findings only when the behavior is intentional, narrowly scoped, and documented inline with a concrete reason.

## Workflow

### 1. Confirm zizmor Options

Confirm `zizmor` is available and inspect the installed CLI options:

```bash
zizmor --version
zizmor --help
```

Use the installed help output as the source of truth. Important options commonly used during this workflow include:

- `--collect=actions` for `action.yml` / `action.yaml` composite action definitions.
- `--collect=workflows` for `.github/workflows/*`.
- `--collect=dependabot` for `.github/dependabot.yml`.
- `--strict-collection` to fail on syntax or schema collection problems.
- `--fix=safe`, `--fix=unsafe-only`, or `--fix=all` for available autofixes.
- `--persona=auditor` or `--persona=pedantic` for broader review.
- `--min-severity` and `--min-confidence` to triage noisy repositories.
- `--format sarif` or `--format github` for CI and reporting contexts.

### 2. Inventory the Actions Surface

Use one file listing command, then read only the files that exist:

```bash
rg --files --hidden -g 'action.y*ml' -g '.github/workflows/*.y*ml' -g '.github/dependabot.y*ml'
```

Identify whether the repo has:

- Root or nested composite actions (`action.yml` / `action.yaml`).
- GitHub workflows under `.github/workflows/`.
- Dependabot configuration at `.github/dependabot.yml`.

### 3. Audit and Fix Composite Actions First

Run an action-only audit:

```bash
zizmor --collect=actions --strict-collection .
```

For mechanical findings, try safe autofixes first:

```bash
zizmor --fix=safe --collect=actions .
```

If `zizmor` reports held-back unsafe fixes, inspect the findings and decide whether `--fix=all` is appropriate:

```bash
zizmor --fix=all --collect=actions .
```

Common composite action fixes:

- Move GitHub expressions out of shell `run:` blocks and into step-level `env:` values, then reference and quote shell variables (`"$INPUT_VERSION"`) inside the script.
- Validate any value that influences a shell command, filesystem path, URL, cache key, or downloaded artifact. For versions, use a strict expected format such as semver instead of accepting arbitrary text.
- Avoid writing attacker-controlled values to `$GITHUB_ENV`, `$GITHUB_OUTPUT`, or `$GITHUB_PATH`.
- If writing to `$GITHUB_PATH` is intentional, ensure the path is derived from trusted runner locations and validated inputs, then add a narrow inline ignore such as:

```yaml
# zizmor: ignore[github-env] install-dir is computed from trusted runner paths and validated semver
```

Verify the action concern is clean before committing:

```bash
zizmor --collect=actions --strict-collection .
```

Create a conventional commit for only the composite action changes.

### 4. Audit and Fix Workflows Second

Run a workflow-only audit:

```bash
zizmor --collect=workflows --strict-collection .
```

Common workflow fixes:

- Add least-privilege `permissions:`. Prefer top-level `permissions: {}` plus job-level permissions when jobs need different scopes, or top-level `contents: read` for simple read-only workflows.
- Set `persist-credentials: false` on every `actions/checkout` step unless a later step explicitly needs the checked-out token.
- Pin third-party actions to immutable commit SHAs when the repository policy expects supply-chain hardening. Keep a comment with the human-readable version when useful.
- Avoid untrusted `pull_request_target` patterns, inline shell interpolation, and overly broad tokens.

Verify the workflow concern is clean:

```bash
zizmor --collect=workflows --strict-collection .
```

Create a conventional commit for only the workflow changes.

### 5. Audit and Fix Dependabot Separately

If `.github/dependabot.yml` exists, run:

```bash
zizmor --collect=dependabot --strict-collection .
```

Common Dependabot fixes:

- Add a small update cooldown under each relevant `updates` entry, usually:

```yaml
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
    cooldown:
      default-days: 7
```

- Preserve existing ecosystem entries, registries, labels, reviewers, and grouping choices unless they are directly related to the finding.
- If broader Dependabot configuration is requested, use the `configuring-dependabot` skill.

Verify the Dependabot concern is clean:

```bash
zizmor --collect=dependabot --strict-collection .
```

Create a conventional commit for only the Dependabot changes.

### 6. Run a Full Audit Before Adding CI

Once the separate concerns are fixed, run the full audit:

```bash
zizmor --strict-collection .
zizmor --persona=auditor .
```

Resolve any remaining actionable findings in the appropriate concern and commit them with that concern. Do not add the ongoing workflow while known actionable findings remain unless the user explicitly wants to establish a baseline with existing code-scanning alerts or console findings.

### 7. Add the Ongoing zizmor Workflow Last

Create `.github/workflows/zizmor.yml` only after local audits are clean.

Baseline workflow:

```yaml
name: Run zizmor

on:
  pull_request:
    paths:
      - .github/**
  push:
    branches: [main]
    paths:
      - .github/**

permissions: {}

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  zizmor:
    name: Run zizmor
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write # Required for zizmor-action to upload SARIF to GitHub code scanning.
    steps:
      - name: Checkout repository
        uses: actions/checkout@<pinned-sha>
        with:
          persist-credentials: false

      - name: Run zizmor
        uses: zizmorcore/zizmor-action@<pinned-sha>
```

Adapt the workflow to the repository:

- Choose the trigger paths from the action inventory in step 2:
  - For a typical application repository whose audited files are all under `.github/`, keep the `.github/**` path filters so unrelated changes do not run `zizmor`.
  - If the repository's primary product is a GitHub Action, including a composite action, remove both `paths` filters so all pull requests and default-branch pushes run `zizmor`.
  - If the repository contains nested action manifests outside `.github/` but is not primarily an action repository, add `'**/action.yml'` and `'**/action.yaml'` to both `paths` lists.
  - If this workflow will be a required status check, remove both `paths` filters; GitHub can leave path-filtered required workflows pending on unrelated pull requests and block merging.
- Replace `<pinned-sha>` with immutable commit SHAs. If the repo does not pin actions elsewhere and the user prefers version tags, follow existing policy but note the trade-off.
- Keep `permissions: {}` at the workflow level and grant only the job permissions required.
- Keep the top-level `concurrency` block so repeated pushes cancel stale runs and `zizmor` does not report `concurrency-limits` on the newly added workflow.
- By default, `zizmor-action` uploads SARIF to GitHub code scanning, which requires `security-events: write`; keep the inline comment on that permission so `zizmor` does not report `undocumented-permissions` on the newly added workflow.
- For private or internal repositories using the default Advanced Security mode, add `actions: read`; `contents: read` is already present in the baseline.
- If the repo cannot use GitHub Advanced Security/code scanning, remove `security-events: write` and set `advanced-security: false` on the `zizmor-action` step.
- Include `pull_request` and default-branch `push` triggers unless the project has a different CI trigger policy; adapt only their path filters using the rules above.

Verify the new workflow and then run the full audit again:

```bash
zizmor --collect=workflows --strict-collection .
zizmor --persona=auditor --collect=workflows .
zizmor --strict-collection .
zizmor --persona=auditor .
```

Create a separate conventional commit for the new `zizmor-action` workflow.

### 8. Final Verification

Before finishing:

```bash
zizmor --strict-collection .
zizmor --persona=auditor .
```

In the final response, summarize:

- The separate concerns fixed and their commits.
- The local `zizmor` commands that pass.
- Any inline ignores and why they are safe.
- Any policy decisions, especially action SHA pinning or code scanning permissions.

## Done When

- Composite action, workflow, and Dependabot findings have been handled in separate logical commits.
- The ongoing `zizmor-action` workflow is added in its own final commit.
- `zizmor --strict-collection .` and `zizmor --persona=auditor .` pass locally.
- Any remaining suppressions are narrow, inline, and justified.
