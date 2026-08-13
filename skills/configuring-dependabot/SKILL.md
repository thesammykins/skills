---
name: configuring-dependabot
description: Creates or updates a .github/dependabot.yml file for a repository. Discovers package ecosystems in use, then writes a configuration with sensible schedules, grouping, and PR limits per the Dependabot options reference. Use when asked to add, enable, or update Dependabot configuration.
---

# Configuring Dependabot

Produces a `.github/dependabot.yml` that enables version updates for every package ecosystem the repository actually uses, with grouping and scheduling chosen to minimise PR noise.

Authoritative reference: <https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference>.

## Workflow

### 1. Check for an Existing Configuration

```bash
ls .github/dependabot.yml 2>/dev/null
```

If `.github/dependabot.yml` exists, read it — treat the task as an *update*, preserving deliberate user customisations (top-level `registries:` and per-update `registries: [...]` references, `target-branch`, `ignore`/`allow`, `reviewers`/`assignees`/`labels`, custom `commit-message`).

### 2. Discover Package Ecosystems

Scan the repository (one `rg --files` is enough) and map manifest files to their `package-ecosystem` value. Only enable an ecosystem if its manifest is actually present.

- `bun` — `bun.lock`
- `npm` — `package.json` with `package-lock.json`, `npm-shrinkwrap.json`, `pnpm-lock.yaml`, or `yarn.lock` (or `package.json` alone if the repo is not Bun-based)
- `bundler` — `Gemfile`
- `cargo` — `Cargo.toml`
- `composer` — `composer.json`
- `mix` — `mix.exs`
- `maven` — `pom.xml`
- `gradle` — `build.gradle`, `build.gradle.kts`, `settings.gradle*`
- `nuget` — `*.csproj`, `*.fsproj`, `*.vbproj`, `packages.config`
- `dotnet-sdk` — `global.json`
- `gomod` — `go.mod`
- `pip` — `requirements*.txt`, `setup.py`, `setup.cfg`, `Pipfile`, `pyproject.toml` (poetry), `*.in` (pip-compile)
- `uv` — `pyproject.toml` with `[tool.uv]` or `uv.lock`
- `pub` — `pubspec.yaml`
- `swift` — `Package.swift`
- `elm` — `elm.json`
- `julia` — `Project.toml`
- `conda` — `environment.yml`, `meta.yaml`
- `docker` — `Dockerfile*`, plus Kubernetes manifests or Helm `values.yaml` files that reference image tags
- `docker-compose` — `docker-compose*.y[a]ml`, `compose*.y[a]ml`
- `helm` — `Chart.yaml`
- `terraform` — `*.tf`, `*.tf.json`
- `opentofu` — `*.tofu` or Terraform tree managed by OpenTofu
- `nix` — `flake.lock`
- `devcontainers` — `.devcontainer/devcontainer.json` or `.devcontainer.json`
- `github-actions` — `.github/workflows/*.y[a]ml`, root `action.y[a]ml`
- `gitsubmodule` — `.gitmodules`
- `pre-commit` — `.pre-commit-config.yaml`
- `bazel` — `MODULE.bazel`, `WORKSPACE*`
- `vcpkg` — `vcpkg.json`
- `rust-toolchain` — `rust-toolchain*`

Detection notes:
- Choose **one** JS ecosystem per project from its lockfile; never emit both `bun` and `npm` for the same package set.
- `nix` requires a `flake.lock` — Dependabot updates the lockfile, not pinned refs in `flake.nix`.
- `github-actions` only updates external `uses: owner/repo@ref` references in `.github/workflows/*` and root `action.y[a]ml`. Local `./...` actions and `docker://` references are not updated.
- `helm` already updates Docker images referenced inside the chart — do not add a separate `docker` entry for the same chart directory unless non-chart manifests live there too.

For each ecosystem, also note the *locations* of its manifests so you can pick `directory: "/"` (single root) or `directories: [...]` (multiple sub-projects).

### 3. Decide Per-Ecosystem Strategy

For every ecosystem found, decide the four key settings before writing YAML.

**`directory` vs `directories` vs multiple entries:**

Think in terms of **cohorts** — sets of manifests that share a dependency profile (same framework family, same vendor mix, same upgrade cadence). The shape of the YAML follows the cohort structure, not the ecosystem.

- **One manifest, or a build tool that aggregates from root** (Maven reactor, Gradle multi-project, Cargo workspace, single Go module): one entry, `directory: "/"`.
- **Independent sub-projects with the same dependency profile** (e.g. three Dockerfiles all running Alpine + Python, npm workspaces sharing the same React/Vite stack, Terraform stacks all on the same providers): one entry, `directories: [...]`, with `group-by: dependency-name` on shared groups so a single PR updates a dep everywhere.
- **Independent sub-projects with distinct dependency profiles** (e.g. a standalone Lambda alongside Spring Boot services, a CLI alongside a Next.js app, a legacy Python 2 service alongside modern uv-based ones): **one entry per cohort**, each with `directories: [...]` listing only that cohort's paths and `groups` tailored to its actual dependencies. This prevents one cohort's families from being silently masked by another's union and keeps each block's groups auditable against its own manifests.
- **Totally heterogeneous sub-projects** (every directory is its own world): one entry per directory.
- For `github-actions`, always use `directory: "/"` (Dependabot scans `.github/workflows/` automatically).

To identify cohorts, after enumerating dependencies per manifest (see Step 3 `groups` below), cluster manifests whose dependency sets overlap heavily — shared parent POM, shared framework, shared vendor — into the same cohort. Manifests with disjoint stacks belong in separate cohorts. Multiple `updates` entries for the same ecosystem are allowed provided their directories don't overlap within a target-branch.

**`schedule.interval`:** default to `weekly`. Use `daily` only if the user asks. Use `monthly` only when the repo is clearly low-touch or the user explicitly wants lower churn (avoid for security-sensitive ecosystems).

**`open-pull-requests-limit`:** default `5` (matches GitHub's own default and keeps noise down). Raise to `10` only when the user wants faster update throughput; omit the key entirely if you have no reason to deviate.

**`cooldown`:** always set a small cooldown so freshly-released versions get a chance to settle before Dependabot opens a PR. Use `default-days` only — it is the one cooldown key accepted by every package ecosystem:

```yaml
cooldown:
  default-days: 7
```

Raise `default-days` (e.g. `14`) for risk-averse projects. `cooldown` applies only to version updates, not security updates, so it never delays vulnerability fixes.

Do not emit `semver-major-days`, `semver-minor-days`, or `semver-patch-days`. They are only accepted by SemVer-aware ecosystems and fail validation on the others (`bazel`, `devcontainers`, `docker`, `docker-compose`, `github-actions`, `gitsubmodule`, `helm`, `terraform`) with `The property '#/updates/N/cooldown/semver-*-days' is not supported for the package ecosystem '<name>'`. Only add them if the user explicitly asks for per-bump-type cooldowns, and then only on SemVer ecosystems.

**`groups`:** the goal is to bundle dependencies that **must move in lockstep** (same vendor's coordinated release train, framework + its plugins, packages that share an internal API) into one PR so reviewers see a coherent change. Derive groups from the actual manifests — never from memory or assumption.

A group must justify itself by **lockstep risk**, not by shared namespace. Two packages under `hashicorp/*` that are unrelated do not need a group. One package alone under a namespace never needs a group — it would be a group of one, which adds noise (extra group name in the PR title, extra block in the YAML) without bundling anything. Concretely:

- **Minimum 2 distinct packages** in the group, counted by package name (not version). `actions/checkout@v5` and `actions/checkout@v6` are one package.
- **Coordinated release or shared API** — Spring Boot starters, AWS SDK v2 modules, OpenTelemetry SDK + instrumentation, React + React DOM, a monorepo's own `@scope/*` packages, a vendor's CLI + matching action. If two packages under the same namespace release independently and have no shared surface (e.g. `slackapi/slack-github-action` vs a hypothetical unrelated `slackapi/*` action), do not group them.
- **When in doubt, leave it out** — let Dependabot open separate PRs. A missing group costs one extra PR; a wrong group hides unrelated changes behind one title.

Before naming any group, **enumerate dependencies from every manifest of that ecosystem**, not just the one at the repo root. Skipping sub-project manifests is the most common source of missed groups (e.g. a non-aggregating root `pom.xml` whose sibling modules inherit from `spring-boot-starter-parent`, or a workspace where each package has its own dependencies). For each manifest:

- Read the file and list every direct dependency (runtime, dev, test, build).
- Inspect **inherited and indirect declarations** that imply a family but may not appear as a normal dependency:
  - Maven: `<parent>` (e.g. `spring-boot-starter-parent`), `<dependencyManagement>` BOM imports, `<build><plugins>`, `<pluginManagement>`.
  - Gradle: `plugins { ... }` block, `platform(...)` / BOM imports, `buildscript` classpath.
  - npm/bun: `peerDependencies`, `devDependencies`, workspace package manifests, framework presets in `eslint`/`babel`/`vite` config.
  - Python: `[tool.poetry.group.*]`, optional-dependency extras, `[build-system].requires`.
  - Cargo: workspace member `Cargo.toml` files, `[build-dependencies]`, `[dev-dependencies]`.
  - Go: indirect modules in `go.mod` that share an org prefix (e.g. `k8s.io/*`, `go.opentelemetry.io/*`).
  - GitHub Actions: every `uses:` line across all workflow files.
- Aggregate the union across manifests, then identify clusters by shared name prefix, organisation, or known framework family. A cluster found in *any* manifest warrants a group, even if absent from the root.

Dependabot assigns each dependency to the **first** matching group, so order groups narrowest → broadest:
1. Framework/family groups first, one per cluster you identified **that has 2+ distinct packages with lockstep risk**.
2. Drop any cluster that resolves to a single package — leave it ungrouped.

`reference/family-groups.md` shows illustrative patterns for common ecosystems (Spring, React, AWS SDK, etc.) — use it for shape and naming inspiration, not as an exhaustive list. Most repos will have project-specific clusters not covered there; invent group names and patterns to fit what is in the manifests.

Leave `major` updates ungrouped so breaking changes are reviewed individually. When the same dependency lives in multiple `directories`, set `group-by: dependency-name` on the relevant group so a single PR updates it everywhere.

### 4. Compose `dependabot.yml`

Write to `.github/dependabot.yml`. Required top-level keys: `version: 2` and `updates:`.

Order each `updates` entry consistently for readability. If there are justified family groups, place them narrowest → broadest:

```yaml
- package-ecosystem: "<ecosystem>"
  directory: "/"            # or directories: [...]
  schedule:
    interval: "weekly"
  open-pull-requests-limit: 5
  cooldown:
    default-days: 7
  groups:
    spring-boot:
      patterns: ["org.springframework*"]
```

Only add optional keys (`labels`, `assignees`, `reviewers`, `commit-message`, `versioning-strategy`, `target-branch`, `ignore`, `allow`, `registries`, `milestone`, `rebase-strategy`, `vendor`, `exclude-paths`, `pull-request-branch-name`, `insecure-external-code-execution`, `multi-ecosystem-groups`) when the user asks or the existing file already uses them — do not invent policy. Skip `enable-beta-ecosystems` (currently has no effect per the GitHub docs).

When updating an existing file, preserve order and comments where possible; only change what the task requires.

### 5. Validate

Confirm:
- `version: 2` is present.
- Every `updates` entry has `package-ecosystem`, `directory`/`directories`, and `schedule.interval`.
- Each ecosystem listed actually has a matching manifest in the repo.
- No two entries for the same ecosystem and target-branch overlap on directories.
- `package-ecosystem` values are spelled exactly as in the reference list above (e.g. `gomod`, not `go`; `gitsubmodule`, not `git-submodule`).
- Family `groups` are ordered narrowest → broadest in each entry (first match wins).
- For every ecosystem with `directories: [...]`, you read each listed manifest (including parent/BOM/plugin sections) and the family groups reflect the union of clusters across them.
- Where sub-projects have distinct dependency profiles, they are split into separate `updates` entries (cohorts), and each cohort's `groups` only references families actually present in its own manifests (no dead patterns, no missed families).
- Every named family group has **at least 2 distinct packages** matching its patterns in the actual manifests, and those packages share a lockstep release/API relationship. Single-package "groups" (e.g. one action under a namespace) have been removed so the dependency remains ungrouped.
- `cooldown` blocks use `default-days` only, unless the user explicitly asked for per-bump-type cooldowns on a SemVer-aware ecosystem.

## Done when

- `.github/dependabot.yml` exists and parses as YAML.
- Every detected ecosystem the user wants managed is configured with directory, schedule, PR limit, and any justified grouping.
- Custom user settings from any pre-existing file are preserved.
