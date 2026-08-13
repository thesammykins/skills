---
name: progressive-production-hardening
description: Tighten production behavior through observed safe stages.
version: 0.2.0
author: Samantha Myers (thesammykins), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [production, rollout, observability, compatibility, rollback]
    related_skills: [systematic-debugging, test-driven-development]
---

# Progressive Production Hardening

Introduce a risky production invariant through shadow decisions, repair, narrow cohorts, measured promotion, and cleanup. Use production as a bounded feedback loop—not as a substitute for tests or an excuse for unrestricted agent access.

Load `references/hardening-playbook.md` to select shadow, flag, canary/ring, expand-contract, protocol-compatibility, and backfill mechanics.

## When to Use

- Tightening auth, validation, compatibility, protocol, schema, or data requirements on existing traffic/data.
- Mixed versions, split-brain deployment, or historical records can violate the new invariant.
- A change needs warning/shadow observation before rejection or mutation.
- Exposure can be controlled by cohort, traffic, flag, revision, region, tenant, or event class.

Don't use for: routine no-risk deployments, emergency containment, or security flaws where continued permissive behavior is itself unacceptable.

## Inputs

- Intended invariant, current behavior, target behavior, and excluded behavior.
- Blast radius, trust/persistence boundaries, legacy-data and mixed-version risks.
- Existing rollout/flag/migration primitives—reuse them before adding machinery.
- Success/failure/unknown thresholds, minimum sample, observation windows and telemetry freshness.
- Owner, backup operator, authority boundary, rollback/roll-forward plan, and cleanup date.

## Procedure

1. **Write the rollout contract.** Define invariant, stages, cohorts, decision owner, success/failure/unknown thresholds, minimum sample, observation windows, telemetry freshness, rollback versus roll-forward, stop conditions, and cleanup. Done when promotion is a deterministic decision rather than “looks fine.”
2. **Map compatibility and irreversible state.** Trace old/new binaries, producers/consumers, persisted data, caches, flags and schema. Distinguish code rollback from data recovery. Done when every mixed state is supported, blocked, or explicitly sequenced away.
3. **Reuse the native mechanism.** Choose existing flag, deployment controller, migration framework, scheduler, telemetry stack and auth. Do not add a flag service or rollout platform for one change. Done when the smallest mechanism can constrain exposure and recover safely.
4. **Preflight outside production.** Test old/new paths, mixed versions, legacy fixtures, migration/backfill dry run, decision telemetry, dashboards/queries and recovery. Load `agent-change-verification` for material changes. Done when the rollout controls themselves have executable evidence.
5. **Deploy the shadow/tracer stage.** Evaluate the exact future rule at its decision point while preserving old behavior. Emit structured bounded reason codes, mode, outcome, cohort, revision and correlation—not sensitive payloads. Done when known synthetic allow/would-reject cases produce correct signals and telemetry freshness is measurable.
6. **Observe a bounded window.** Use read-only production access to quantify rates/distributions, classify failures, compare against baseline and inspect representative traces/events. “No data,” unknown categories, or stale telemetry pauses progression. Done when sample/window thresholds are met and every observed category has a disposition.
7. **Repair prerequisites separately.** Correct producers or run bounded, idempotent, checkpointed backfills with before/after invariant queries. Prefer expand → migrate → contract and roll-forward for data changes. Done when legacy cases are repaired, deliberately exempted, or still block enforcement.
8. **Enable the lowest-risk cohort.** Internal/test users first, then a small explicit cohort/canary. Change one exposure dimension per stage. Verify user-visible symptoms plus latency, errors, saturation, business/invariant signals and telemetry health. Done when stage thresholds hold for the full window.
9. **Promote, pause, or recover mechanically.** Promote only when all contract conditions pass; pause on inconclusive telemetry; disable/rollback/roll-forward on failure. Automated progression is allowed only for pre-authorized reversible stages. Done when the action and evidence are recorded.
10. **Repeat progressive cohorts.** Increase exposure with explicit pauses and analysis; rerun compatibility and real-path checks after behavior changes. Keep another authorized operator able to inspect and intervene. Done when full enforcement is reached or residual cohorts/exemptions are explicit.
11. **Soak and contract.** Keep recovery available through the soak/compatibility window. Then remove old paths, expired flags, temporary warnings and migration compatibility only when usage proves them dead. Done when runtime, code, schema, docs, tests and monitoring agree.
12. **Externalize the handoff.** Record current stage/revision, evidence, active flags/cohorts, dashboards/queries, data state, next decision time, exact recovery and cleanup owner.

## Safety Rules

- Least-privilege production access; read-only observation by default.
- Unattended agents never receive unrestricted production credentials or discretionary rollback/mutation authority.
- Auth, privacy, money, destructive data, permission and irreversible migration stages require human approval.
- Production telemetry contains no secrets, tokens, payload content, guessable URLs, or unnecessary identifiers.
- Unknown failure classes, stale telemetry, breached thresholds, failed state persistence, or unavailable recovery stop progression.
- Feature flags have owner, expiry, relevant on/off tests and removal task.

## Pitfalls

- Shadow logic differs from enforcement logic.
- Low warning volume is treated as success without checking traffic and telemetry health.
- Percentage rollout ignores tenant/role/data-age cohorts where risk actually clusters.
- Backfill, enforcement and broad rollout happen in one irreversible step.
- “Rollback” means old code, but new data is incompatible.
- Flags and warning logs remain as permanent sediment.

## Verification

- [ ] Rollout contract has deterministic promote/pause/recover rules.
- [ ] Mixed versions and persisted-data states are explicitly handled.
- [ ] Shadow evaluation shares the future decision point and has telemetry-health proof.
- [ ] Repairs are idempotent, checkpointed and measured before/after.
- [ ] Every cohort stage meets minimum sample/window and user-facing thresholds.
- [ ] Recovery remains viable until soak/compatibility windows close.
- [ ] Final cleanup removes old paths, expired flags and temporary noise.
- [ ] Handoff permits an authorized operator to inspect and intervene without chat context.
