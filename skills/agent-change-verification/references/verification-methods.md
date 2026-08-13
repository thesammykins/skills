# Verification Method Selection

Use this reference after listing the change's claims and risks. Select methods because they can falsify a claim, not because they are available.

## Evidence strength

1. **Claim** — implementer says it works. Not evidence.
2. **Static evidence** — diff, typecheck, lint, schema validation. Shows structural properties, not runtime behavior.
3. **Focused executable evidence** — a regression, property, contract, security, or integration check reaches the changed boundary.
4. **Real-path evidence** — an end-to-end run exercises the same interfaces and packaging a user or system consumes.
5. **Independent evidence** — another actor/tool reads artifacts back, checks the deployed target, or verifies provenance against expectations.
6. **Operational evidence** — bounded live observation proves the final revision behaves within defined thresholds.

Use the lowest level that can disprove each claim; high-risk claims usually need several independent levels.

## Risk-to-method map

| Change shape | Minimum useful evidence | Add when risk warrants |
|---|---|---|
| Pure function/business rule | focused examples at boundaries | property-based test for broad input space; mutation/sabotage check that the test bites |
| Bug fix | red reproduction, root-cause fix, regression test | restore old behavior temporarily and prove regression goes red |
| Parser/serializer | valid/invalid examples, round trip | fuzz/property testing, corpus replay, resource limits |
| API/schema/event | producer/consumer checks | consumer-driven contract verification, old/new version compatibility matrix |
| Database migration | forward migration on production-like copy | invariants/counts, old+new app compatibility, rollback or roll-forward rehearsal |
| Auth/permissions | positive and negative role matrix | OWASP ASVS requirement IDs, tenant-isolation and confused-deputy probes, independent review |
| CLI | command exit/status/stdout/stderr and filesystem effects | old/current CLI versions, shell/platform matrix, install/package path |
| Web UI | real interaction and DOM assertions | recording plus trace, console/network review, screenshots for key states, responsive/keyboard/reduced-motion checks |
| Motion | final-revision recording and endpoints | validate measured FPS; extract timestamped decoded frames around transitions; inspect jitter, stalls, flashes, layout shift and interruption paths |
| Async/concurrency | deterministic state-transition test | stress/repetition, injected delay, idempotency/retry/duplicate-delivery probes |
| External integration | sandbox/test-provider round trip | callback signature/replay tests, provider read-back, teardown proof |
| Build/release artifact | digest and final package smoke test | SLSA/GitHub attestation verification against source, builder, workflow and parameters |
| Infrastructure/config | syntax/plan/dry-run plus diff | canary, health thresholds, rollback rehearsal, live read-back |
| Automation/cron | foreground sample and deterministic decision tests | duplicate, empty, failure, recovery, delivery and monitor-health paths |

## Test quality probes

A passing test is useful only if it could fail for the defect or invariant.

- **Sabotage:** temporarily restore the old behavior or invert the changed branch; the new regression must fail.
- **Property:** express a rule over a generated input domain when examples cannot cover the state space. Prefer installed property-testing tools; do not add one for a single trivial example.
- **Contract:** test the actual client/producer and replay its minimal expectations against the real provider. Contract tests verify compatibility, not business side effects.
- **Differential:** compare old/new implementation, versions, providers, or datasets on the same corpus.
- **Metamorphic:** transform input in a way that should preserve or predictably change output.
- **Replay:** use sanitized production payloads, HAR files, traces, queue messages, or failure corpora.
- **Stress/repetition:** raise the reproduction rate of timing, race, leak, or retry defects; retain seed and iteration count.

## Matrix design

Do not take the Cartesian product blindly. Add a dimension only when the diff can interact with it.

1. List dimensions: version, platform, client, runner, role, account state, feature flag, locale/timezone, viewport/input, network condition, persisted-data age.
2. Mark the risk mechanism for each dimension.
3. Use pairwise or representative cells for independent dimensions.
4. Require explicit boundary cells: oldest supported version, current version, least-privileged role, empty/maximum/invalid input, offline/retry where relevant.
5. Record exclusions and why they cannot affect this change.

## Browser evidence

When Playwright is already present, prefer:

- trace retained on failure or first retry;
- recording is mandatory where visual or temporal claims exist; screenshots support key states but cannot prove a transition;
- trace inspection of action snapshots, console, errors, network, and metadata;
- device/viewport, locale, timezone, permissions, color scheme and offline emulation only when implicated.

Do not upload traces containing secrets or personal data. Playwright's hosted trace viewer processes traces in-browser, but local inspection is still preferable for sensitive artifacts.

For visual, animation, transition, scroll, drag, canvas/WebGL, or time-dependent interaction changes, load `references/visual-motion-verification.md`. The required pattern is record → validate media metadata → watch → extract timestamped frames → inspect contact sheets and suspicious frames → correlate with trace/runtime evidence → recapture after fixes. A video that was produced but not inspected is only an artifact, not evidence.

## Accessibility evidence

Automated tools cannot establish accessibility alone. For affected UI, combine relevant automation with human checks:

- keyboard order, focus visibility and focus restoration;
- accessible names/roles/states;
- zoom/reflow and responsive layout;
- reduced motion and animation interruption;
- error identification and recovery;
- screen-reader spot check for changed critical flows when risk warrants.

Use WCAG 2.2 criteria or ACT rules as explicit expectations; do not claim conformance from an automated scan.

## Artifact identity and provenance

Verification evidence must identify what it verified:

- source revision or diff;
- artifact path and cryptographic digest where release artifacts exist;
- build/run environment and relevant parameters;
- command and exit status;
- timestamp for volatile/live evidence.

For released binaries/packages, verify provenance or GitHub artifact attestations when available. Attestation proves origin/integrity, not that the code is safe or behavior is correct.

## Primary resources

- Playwright traces and recording: https://playwright.dev/docs/trace-viewer, https://playwright.dev/docs/videos and https://playwright.dev/docs/test-use-options
- FFmpeg frame extraction and filters: https://ffmpeg.org/ffmpeg.html and https://ffmpeg.org/ffmpeg-filters.html
- SLSA artifact verification: https://slsa.dev/spec/v1.2/verifying-artifacts
- GitHub artifact attestations: https://docs.github.com/en/actions/concepts/security/artifact-attestations
- OWASP ASVS: https://owasp.org/www-project-application-security-verification-standard/
- NIST SSDF: https://csrc.nist.gov/pubs/sp/800/218/final
- W3C accessibility evaluation: https://www.w3.org/WAI/test-evaluate/
- Hypothesis/property testing: https://hypothesis.readthedocs.io/en/latest/
- Pact contract testing: https://docs.pact.io/getting_started/how_pact_works
