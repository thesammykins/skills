---
name: agent-change-verification
description: Verify agent changes with risk-shaped evidence.
version: 0.5.0
author: Samantha Myers
license: MIT
platforms: [linux, macos, windows]
metadata:
  tags: [verification, testing, demos, matrices, evidence]
---

# Agent Change Verification

Verify the exact artifact an agent changed through evidence that can falsify its claims. The implementer’s summary, green CI, coverage, a screenshot, or an attestation can each support a narrow claim; none proves the whole change correct.

Start with the lightweight path below. Load `references/verification-methods.md`
when choosing additional checks for a material risk or an unfamiliar boundary.
Load `references/visual-motion-verification.md` for visual or temporal claims;
static appearance and behavior over time require different evidence.
Use `templates/evidence-bundle.md` for high-risk or complex handoffs where the
structure helps; ordinary changes need only a concise evidence summary.

When running in Amp, load `harnesses/amp.md` to map these evidence requirements to available tools and executor constraints.

## When to Use

- An agent changed code, configuration, UI, automation, infrastructure, data behavior, or an external integration.
- A reviewer asks “how do we know this works?”
- The change crosses versions, clients, platforms, account/role states, runners, trust boundaries, or deployment stages.
- A visual/interaction change needs inspectable runtime evidence.

Don't use for: prose-only edits with no executable claim. This does not replace independent security review, migration review, or production approval where those are required.

## Lightweight path (default)

1. State the observable outcome and what must remain unchanged. Derive expected
   results from the request/spec, a reproduced failure, a known fixture, or an
   independent reference. Resolve material ambiguity before encoding assumptions.
2. Inspect the scoped diff and relevant existing checks. Choose the cheapest
   reliable check that could expose a defect at the changed boundary.
3. Run applicable repository-required checks and exercise the changed behavior.
   For a trivial reversible edit, focused inspection or an existing check may be
   sufficient; do not manufacture a new test or framework to demonstrate activity.
4. Report what was checked, the result, and remaining uncertainty. Reuse evidence
   while its relevant inputs remain unchanged; stop verifying when the stated
   outcome is supported and required checks pass.

Use the extended procedure only for implicated risks: business rules, parsers,
permissions, persistence, concurrency, external contracts, deployment, or complex
user interactions. Select applicable steps, not all steps automatically. A simple
change does not require a matrix, recording, artifact digest, or formal bundle.

## Exploration, verification, and regression protection

- Temporary probes help discover behavior; they need not become committed tests.
- Verification establishes the current outcome through execution or inspection.
- Durable tests protect meaningful behavior during future changes. Reuse or extend
  an existing test before adding another. For a reproduced behavioral bug, retain
  a regression test when practical; explain a meaningful gap or an alternative
  check when automation is impractical or adds no lasting protection.
- Test-first suits a clear contract. Explore first when the shape is uncertain,
  then test the stabilized contract before treating it as protected behavior.
- Derive assertions independently of the implementation. Do not calculate the
  expected result with the same logic under test or bless the current output just
  because it passes. Mocks must not bypass the property or boundary being checked.
- Retain focused tests for business rules, parsers, auth, data loss, state changes,
  and concurrency risks. Coverage, test count, and assertion count are not goals.
- Never weaken an existing test to obtain green output. Change an expectation only
  for an authorized contract change and explain why the old expectation is obsolete.

## Inputs

- Outcome, acceptance criteria, non-goals, and must-not-change behavior.
- Complete diff plus generated, packaged, deployed, and remote artifacts.
- Risk/blast radius, invariants, and escalation boundaries.
- Supported compatibility dimensions and repository-required checks.
- Final revision/artifact identity and available test environment.

## Core Model: Claim → Risk → Oracle → Evidence

For every material claim, identify the following; write only the detail needed
for a reviewer to assess the evidence:

1. **Claim:** observable behavior or invariant—not “refactored successfully.”
2. **Risk:** how the diff could violate it and who/what is affected.
3. **Oracle:** what distinguishes correct from plausible.
4. **Probe:** the cheapest check capable of making the oracle fail.
5. **Evidence:** reproducible output tied to the exact revision/artifact.
6. **Residual uncertainty:** what the probe cannot establish.

No material claim without an oracle; no PASS without evidence from the final artifact.

## Extended procedure (select applicable steps)

1. **Reconstruct the verification contract.** Read project instructions, request/spec, complete diff, status, generated files, dependency/lock changes, migrations, and external effects. Enumerate acceptance criteria, invariants, non-goals, and unauthorized scope. Done when every changed artifact and behavioral claim is accounted for.
2. **Map the blast radius.** Trace callers, consumers, trust boundaries, persistence, deployment path, and compatible versions with the host's code-search and repository tools. Identify security, money, auth, data-loss, migration, concurrency, accessibility, operational, and supply-chain risks. Done when each material risk has an owner and failure signal.
3. **Build the claim-evidence matrix.** Load `references/verification-methods.md`; select focused regression, property, contract, differential, replay, end-to-end, visual, accessibility, provenance, or live-observation probes because each can falsify a named claim. Avoid an unreasoned Cartesian matrix. Done when every criterion/invariant maps to at least one probe and every probe maps back to a risk.
4. **Establish artifact identity.** Capture source revision, dirty diff, build/package identity, relevant environment and parameters; digest releasable artifacts. For published artifacts, verify available SLSA/GitHub attestations against expected source, builder/workflow and parameters. Attestation proves provenance/integrity, not safety. Done when later evidence cannot be confused with a stale build.
5. **Run the cheapest deterministic gates.** Execute repository-required format, lint, type, schema, build, focused unit/integration/regression and security checks. Retain command, scope, exit status and output location. Done when failures are resolved or honestly block the verdict.
6. **Prove critical checks bite.** For a retained regression or high-value invariant, use the observed pre-fix failure when available. Otherwise confirm fault detection with a bounded old-behavior or mutation check in an isolated fixture/worktree, then restore and rerun. Do not disturb unrelated work or repeat an already demonstrated failure. Use property/fuzz testing when the input space—not one example—is the risk. Done when the key check demonstrates fault-detection power.
7. **Exercise real boundaries.** Use actual clients, parsers, storage, provider sandboxes, package/install paths, or consumer contracts rather than mocks that bypass the change. Test positive, negative, unauthorized, invalid, dependency-failure, retry, duplicate/idempotency and recovery paths as implicated. Done when the observable system outcome matches the contract.
8. **Exercise the real user path.** Run the affected setup → action → output consumption path when the claim crosses user or integration boundaries. Static layout, styling, and visual-state claims need inspected screenshots of the final artifact and relevant interaction checks. Animation, scrolling, drag, transitions, or timing claims need an inspected final-artifact recording. Retain browser traces when useful to investigate behavior or required by the repository. State any missing runtime evidence rather than substituting unit-test success.
9. **Cover the meaningful compatibility matrix.** Include only dimensions coupled to the diff: oldest/current version, client, platform, role/tenant, runner, data age, flag state, viewport/input, locale/timezone, or network condition. Use boundary and representative/pairwise cells; document exclusions. Done when each included cell has a reason and result.
10. **Inspect temporal evidence when implicated.** Follow `references/visual-motion-verification.md`: validate duration, dimensions and measured FPS; preserve the original recording; use `ffprobe`/`ffmpeg` or an equally timestamp-faithful existing decoder to extract overview samples and every decoded frame around suspicious transitions; open contact sheets and individual frames with an available media-inspection capability. Check jitter, stalls, flashes, layout shift, clipping, z-index/unstyled states, interrupted interactions, endpoint drift and reduced-motion behavior. A generated video or final screenshot is not proof until inspected. Done when findings cite recording path and exact timestamps/frame PTS, with capture limits stated.
11. **Verify accessibility when UI changed.** Combine automation with keyboard/focus, accessible-name/state, zoom/reflow, reduced-motion and error-recovery checks. Use WCAG 2.2/ACT expectations where relevant; never claim conformance from one scanner. Done when changed critical flows have both tool and human-observable evidence appropriate to risk.
12. **Independently read back side effects.** Treat implementer/subagent claims as untrusted: open files, query remote records, fetch URLs, inspect deployment revision, and verify messages/uploads through returned handles. Consequential effects still require authority. Done when each claimed external state has independent proof.
13. **Invalidate stale evidence.** After any behavior-affecting edit, rerun all probes whose assumptions or artifact identity changed. Refresh affected screenshots for static visual changes; refresh recordings and affected frame inspection for temporal changes. Done when the evidence bundle identifies the final revision/digest only.
14. **Issue a bounded verdict.** Use `templates/evidence-bundle.md` when risk or complexity warrants it; otherwise summarize the applicable evidence inline. Verdicts are `PASS`, `PASS WITH RESIDUAL RISK`, `FAIL`, or `BLOCKED`. Include exact checks, matrix, artifacts, residual uncertainty and next owner. Never translate missing evidence into confidence.

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

Apply only the items implicated by the change; do not turn this into a mandatory
full checklist for the lightweight path.

- [ ] Complete change/artifact inventory matches the final revision.
- [ ] Every material claim has risk, oracle, falsifying probe, evidence and residual uncertainty.
- [ ] Critical regression/invariant checks were shown to bite.
- [ ] Real boundaries and user/caller path were exercised.
- [ ] Static visual claims have inspected final-artifact screenshots and relevant interaction checks; temporal claims have recording and affected frame inspection.
- [ ] Returned artifacts and external effects were independently read back.
- [ ] Risk-relevant compatibility, failure, security and accessibility cells are explicit.
- [ ] Release artifact identity/provenance was checked when applicable.
- [ ] Verdict uses only evidence from the final revision and names remaining uncertainty.
