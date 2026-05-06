---
name: maestro
description: Build, run, and debug Maestro UI automation for Android, iOS, and Web. Use when Codex needs to install or verify Maestro, create or refactor Maestro flow YAML files, organize a `.maestro` workspace, record flows, run tests locally or in CI, configure tags/hooks/workspace config, or diagnose flaky Maestro selectors and flow logic.
---

# Maestro

Use this skill to work with Maestro from first setup through flow debugging.

Start by verifying current Maestro docs and the local environment. Maestro evolves quickly, and this skill should not be used from memory alone.

## Ground Truth First

Before changing flows or suggesting commands:

1. Read the current Maestro docs for the feature you need.
2. Inspect the local repo for existing Maestro files:
   - `.maestro/`
   - `maestro/`
   - `config.yaml`
   - `*.yaml` flow files
3. Verify local tooling and target state:
   - `maestro --version`
   - `maestro test --help`
   - Confirm an iOS Simulator, Android Emulator, or Web target is available
   - Confirm the app under test is installed or runnable

If the repo already has Maestro flows, preserve its naming, folder structure, and selector conventions.

## Default Workflow

### 1. Pick the smallest workable flow shape

Prefer short, linear flows that cover one job well.

- Keep one primary user journey per flow.
- Extract repeated setup or repeated UI sequences into subflows with `runFlow`.
- Avoid conditional logic unless the UI truly branches at runtime.
- Prefer separate platform-specific subflows over large mixed-condition files.

Maestro documentation explicitly discourages overusing conditions because it increases test complexity. Follow that guidance.

### 2. Write stable flow files

Use the standard flow shape:

```yaml
appId: com.example.app
name: Login
tags:
  - smoke
env:
  USERNAME: user@example.com

---
- launchApp
- tapOn: "Username"
- inputText: ${USERNAME}
- assertVisible: "Home"
```

Keep configuration above `---` and commands below it.

Use:

- `appId` for the app under test
- `name` for readable reporting
- `tags` for selective execution
- `env` for portable parameters

### 3. Prefer resilient selectors

Choose selectors in this order:

1. Stable accessibility id or element id
2. Stable visible text
3. Structured selectors that combine attributes or hierarchy
4. Coordinates only as a last resort

Avoid selectors tied to volatile copy, animation timing, or layout position when a stronger identifier exists.

When a selector is flaky:

- Inspect the current view hierarchy
- Tighten the selector with `id`, `text`, `below`, `childOf`, or `index` only if needed
- Replace brittle waits with stronger assertions around the actual UI state

### 4. Keep synchronization explicit

Do not paper over race conditions with arbitrary sleeps.

Prefer:

- `assertVisible`
- `assertNotVisible`
- `extendedWaitUntil`
- `scrollUntilVisible`
- `waitForAnimationToEnd`

Use retry-style logic only when the UI is genuinely nondeterministic and simpler assertions are not enough.

### 5. Reuse flows with parameters

Use `env` and subflows instead of duplicating near-identical files.

- Put stable defaults in the flow header
- Override values from the parent flow or CLI when needed
- Keep subflows focused on one reusable chunk, such as login, permissions, or onboarding dismissal

### 6. Run the narrowest command that answers the question

Prefer running one flow or one tagged subset before broader suites.

Typical commands:

```bash
maestro test .maestro/login.yaml
maestro test .maestro --include-tags smoke
maestro studio
maestro record
```

Check current CLI help before suggesting flags or output options.

## Debugging Rules

When a flow fails:

1. Reproduce the failure with the smallest possible flow.
2. Confirm the target device and app state.
3. Inspect the selector or screen state before changing logic.
4. Fix the root cause:
   - wrong selector
   - wrong screen state
   - missing permission/setup step
   - unstable timing
   - platform-specific UI difference
5. Re-run the same flow after each fix.

Do not add complexity before proving the simple path fails.

## Workspace and CI Guidance

Use workspace-level configuration only when it reduces repetition.

- Keep shared hooks or defaults in workspace config
- Keep test-specific behavior in the individual flow
- Use tags for CI slicing instead of cloning suites

Current Maestro docs note that Maestro Studio does not currently support `config.yaml` for local runs. Do not assume a Studio run is honoring workspace config unless you have verified it.

If the task involves hooks, tags, workspace config, or JavaScript, read [flow-patterns.md](./references/flow-patterns.md) first.

## Output Expectations

When using this skill, deliver:

- the flow or flow changes
- the exact commands used to verify them
- any assumptions about simulator/emulator/app state
- any remaining flake risk or platform caveats
