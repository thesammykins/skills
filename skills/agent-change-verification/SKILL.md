---
name: agent-change-verification
description: Verify agent changes with risk-shaped evidence.
version: 0.4.0
author: Samantha Myers
license: MIT
platforms: [linux, macos, windows]
metadata:
  tags: [verification, testing, demos, matrices, evidence]
---

# Agent Change Verification

Verify the exact artifact an agent changed through evidence that can falsify its claims. The implementer’s summary, green CI, coverage, a screenshot, or an attestation can each support a narrow claim; none proves the whole change correct.

Load `references/verification-methods.md` before designing the checks. For any visual, animation, transition, scroll, drag, canvas/WebGL, or other time-dependent change, also load and follow `references/visual-motion-verification.md`. Use `templates/evidence-bundle.md` for normal/high-risk handoffs or whenever multiple surfaces are involved.

When running in Amp, load `harnesses/amp.md` to map these evidence requirements to available tools and executor constraints.

## When to Use

- An agent changed code, configuration, UI, automation, infrastructure, data behavior, or an external integration.
- A reviewer asks “how do we know this works?”
- The change crosses versions, clients, platforms, account/role states, runners, trust boundaries, or deployment stages.
- A visual/interaction change needs inspectable runtime evidence.

Don't use for: prose-only edits with no executable claim. This does not replace independent security review, migration review, or production approval where those are required.

## Inputs

- Outcome, acceptance criteria, non-goals, and must-not-change behavior.
- Complete diff plus generated, packaged, deployed, and remote artifacts.
- Risk/blast radius, invariants, and escalation boundaries.
- Supported compatibility dimensions and repository-required checks.
- Final revision/artifact identity and available test environment.

## Core Model: Claim → Risk → Oracle → Evidence

For every material claim, record:

1. **Claim:** observable behavior or invariant—not “refactored successfully.”
2. **Risk:** how the diff could violate it and who/what is affected.
3. **Oracle:** what distinguishes correct from plausible.
4. **Probe:** the cheapest check capable of making the oracle fail.
5. **Evidence:** reproducible output tied to the exact revision/artifact.
6. **Residual uncertainty:** what the probe cannot establish.

No material claim without an oracle; no PASS without evidence from the final artifact.

## Procedure

1. **Reconstruct the verification contract.** Read project instructions, request/spec, complete diff, status, generated files, dependency/lock changes, migrations, and external effects. Enumerate acceptance criteria, invariants, non-goals, and unauthorized scope. Done when every changed artifact and behavioral claim is accounted for.
2. **Map the blast radius.** Trace callers, consumers, trust boundaries, persistence, deployment path, and compatible versions with the host's code-search and repository tools. Identify security, money, auth, data-loss, migration, concurrency, accessibility, operational, and supply-chain risks. Done when each material risk has an owner and failure signal.
3. **Build the claim-evidence matrix.** Load `references/verification-methods.md`; select focused regression, property, contract, differential, replay, end-to-end, visual, accessibility, provenance, or live-observation probes because each can falsify a named claim. Avoid an unreasoned Cartesian matrix. Done when every criterion/invariant maps to at least one probe and every probe maps back to a risk.
4. **Establish artifact identity.** Capture source revision, dirty diff, build/package identity, relevant environment and parameters; digest releasable artifacts. For published artifacts, verify available SLSA/GitHub attestations against expected source, builder/workflow and parameters. Attestation proves provenance/integrity, not safety. Done when later evidence cannot be confused with a stale build.
5. **Run the cheapest deterministic gates.** Execute repository-required format, lint, type, schema, build, focused unit/integration/regression and security checks. Retain command, scope, exit status and output location. Done when failures are resolved or honestly block the verdict.
6. **Prove critical checks bite.** For bug fixes and high-value invariants, sabotage the changed behavior or temporarily restore the old behavior and confirm the regression fails; then restore and rerun. Use property/fuzz testing when the input space—not one example—is the risk. Done when the key check demonstrates fault-detection power.
7. **Exercise real boundaries.** Use actual clients, parsers, storage, provider sandboxes, package/install paths, or consumer contracts rather than mocks that bypass the change. Test positive, negative, unauthorized, invalid, dependency-failure, retry, duplicate/idempotency and recovery paths as implicated. Done when the observable system outcome matches the contract.
8. **Exercise and record the real user path.** Run setup → action → output consumption end-to-end. If visuals or behavior over time are involved, recording is mandatory: capture the final artifact using the project-native recorder, Playwright/app recording, or a documented platform recorder. For browser UI, retain a trace and inspect actions, DOM snapshots, console, network and errors. Done when the full recording belongs to the final revision, has been opened, and covers the changed interaction through its settled state.
9. **Cover the meaningful compatibility matrix.** Include only dimensions coupled to the diff: oldest/current version, client, platform, role/tenant, runner, data age, flag state, viewport/input, locale/timezone, or network condition. Use boundary and representative/pairwise cells; document exclusions. Done when each included cell has a reason and result.
10. **Inspect visual and temporal evidence frame-by-frame.** Follow `references/visual-motion-verification.md`: validate duration, dimensions and measured FPS; preserve the original recording; use `ffprobe`/`ffmpeg` or an equally timestamp-faithful existing decoder to extract overview samples and every decoded frame around suspicious transitions; open contact sheets and individual frames with an available media-inspection capability. Check jitter, stalls, flashes, layout shift, clipping, z-index/unstyled states, interrupted interactions, endpoint drift and reduced-motion behavior. A generated video or final screenshot is not proof until inspected. Done when findings cite recording path and exact timestamps/frame PTS, with capture limits stated.
11. **Verify accessibility when UI changed.** Combine automation with keyboard/focus, accessible-name/state, zoom/reflow, reduced-motion and error-recovery checks. Use WCAG 2.2/ACT expectations where relevant; never claim conformance from one scanner. Done when changed critical flows have both tool and human-observable evidence appropriate to risk.
12. **Independently read back side effects.** Treat implementer/subagent claims as untrusted: open files, query remote records, fetch URLs, inspect deployment revision, and verify messages/uploads through returned handles. Consequential effects still require authority. Done when each claimed external state has independent proof.
13. **Invalidate stale evidence.** After any behavior-affecting edit, rerun all probes whose assumptions or artifact identity changed. Visual changes require a new final recording and affected frame inspection. Done when the evidence bundle identifies the final revision/digest only.
14. **Issue a bounded verdict.** Fill `templates/evidence-bundle.md`: `PASS`, `PASS WITH RESIDUAL RISK`, `FAIL`, or `BLOCKED`. Include exact checks, matrix, artifacts, residual uncertainty and next owner. Never translate missing evidence into confidence.

## Safety Rules

- Use short-lived, least-privilege test credentials; never embed them in artifacts, traces, reports, or prompts.
- Do not mutate production unless explicitly approved, bounded, observable, and recoverable.
- Uploads, messages, deployments, purchases, signing, migrations, destructive actions, and permission changes require separate authority.
- Redact secrets and personal/customer data from screenshots, videos, HAR/trace files, logs and fixtures.
- High-risk changes require verifier independence: separate agent/reviewer plus human authority where policy requires it.
- Verification agents may not weaken tests, thresholds, validation, or permissions to obtain green output.

## Pitfalls

- “All tests pass” with no proof they reach the changed behavior.
- Trusting the implementing agent’s demo description without watching/opening it.
- Recording a demo but inspecting only the final frame, a sparse sample, or the extraction command's exit code.
- Trusting a nominal 60/120 FPS setting without measuring the recording or accounting for variable/duplicated frames.
- Testing source while shipping a different package, container, binary, workflow or configuration.
- Broad matrices with no risk rationale; narrow matrices that omit oldest supported/least-privileged boundary cases.
- Contract tests used as proof of persistence/business effects; attestations used as proof of secure behavior.
- Automated accessibility scans presented as conformance.
- Evidence captured before the final tweak.

## Verification

- [ ] Complete change/artifact inventory matches the final revision.
- [ ] Every material claim has risk, oracle, falsifying probe, evidence and residual uncertainty.
- [ ] Critical regression/invariant checks were shown to bite.
- [ ] Real boundaries and user/caller path were exercised.
- [ ] Visual/temporal changes have a final-revision recording, validated metadata, extracted-frame inspection and timestamped findings.
- [ ] Returned artifacts and external effects were independently read back.
- [ ] Risk-relevant compatibility, failure, security and accessibility cells are explicit.
- [ ] Release artifact identity/provenance was checked when applicable.
- [ ] Verdict uses only evidence from the final revision and names remaining uncertainty.
