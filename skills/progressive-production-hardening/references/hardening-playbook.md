# Progressive Hardening Playbook

This reference converts a risky invariant into explicit rollout stages. Use native deployment/flag facilities already present; do not add a flag platform merely to follow the playbook.

## Select the mechanism

| Need | Prefer | Notes |
|---|---|---|
| Observe what enforcement would reject | shadow/tracer decision at the exact enforcement point | Must share decision logic with future enforcement or results drift |
| Change one feature independently of deployment | short-lived feature/release flag | Give owner and expiry; flags add test states and carrying cost |
| Compare application revisions | canary/ring/blue-green deployment | Validate stable and candidate under comparable traffic |
| Change persistent schema | expand → migrate/backfill → contract | Old and new binaries must coexist during the compatibility window |
| Change producer/consumer protocol | tolerant reader + version/contract checks | Verify oldest supported and current participants |
| Correct historical data | bounded idempotent backfill | Counts, checkpoints, dry-run/sample, retry and roll-forward plan |

## Stage contract

Before stage 0, record:

```markdown
Invariant:
Owner / backup operator:
Affected surfaces and cohorts:
Current permissive behavior:
Target behavior:
Stage sequence:
Success metrics and thresholds:
Failure/unknown thresholds:
Minimum sample and observation window:
Telemetry freshness check:
Rollback vs roll-forward action:
Data mutation implications:
Flag/toggle expiry:
```

## Canonical stages

0. **Preflight:** compatibility tests, dry-run/backfill rehearsal, dashboards/queries, rollback and authority ready.
1. **Shadow:** evaluate the new rule but preserve old behavior; emit structured reason codes and correlation IDs.
2. **Repair:** classify shadow failures; fix producers or historical data; repeat until remaining failures are understood.
3. **Internal cohort:** operators/test accounts; verify black-box behavior and telemetry.
4. **Low-risk cohort/canary:** small explicit percentage, tenant group, region, or event class.
5. **Progressive cohorts:** increase one dimension at a time with pauses and analysis.
6. **Full enforcement:** retain kill switch/rollback during the soak window.
7. **Contract:** remove old path, temporary telemetry and expired flags only after compatibility/rollback windows close.

Not every rollout needs every stage. Removing a stage requires an explicit reason tied to risk.

## Promotion logic

Promote only when all are true:

- minimum sample and observation time reached;
- user-visible error, latency, saturation and business/invariant signals stay within threshold;
- telemetry is fresh and complete enough to decide;
- no unknown failure category remains;
- rollback/kill path is still viable;
- stage-specific manual checks pass.

Pause on inconclusive telemetry. Roll back or disable on failure thresholds. Never interpret “no data” as success.

## Telemetry design

Prefer structured events at the decision point:

```text
hardening_rule=<stable name>
mode=shadow|enforce
outcome=allow|would_reject|reject|error
reason=<bounded enum>
cohort=<non-sensitive rollout cohort>
revision=<source/deploy revision>
trace_id=<correlation id when available>
```

Use metrics for rates/distributions, traces for request paths, and sampled logs/events for explanations. Preserve correlation across them when existing OpenTelemetry facilities allow it.

Do not log raw tokens, attachment URLs, payloads, or customer content. Hashing identifiers is not automatically anonymous; retain only what the decision requires.

## Data-change rule

Code rollback cannot undo a destructive or incompatible data mutation. For migrations/backfills, prefer roll-forward and require:

- expand-before-contract schema;
- idempotency and checkpointing;
- before/after invariant queries;
- production-like rehearsal;
- old/new application compatibility during rollout;
- a separate authorization boundary for destructive cleanup.

## Flag lifecycle

Feature flags are inventory:

- owner, purpose, creation date and expiry;
- stable default and failure behavior;
- observability showing evaluated variant;
- tests for relevant on/off states;
- removal task created with the flag;
- delete decision logic after full rollout.

## Primary resources

- Feature Toggle categories and carrying cost: https://martinfowler.com/articles/feature-toggles.html
- Argo Rollouts analysis and dry-run metrics: https://argo-rollouts.readthedocs.io/en/stable/features/analysis/
- Kubernetes rollout status/history/rollback: https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
- OpenTelemetry signals: https://opentelemetry.io/docs/concepts/signals/
- Google SRE monitoring principles: https://sre.google/sre-book/monitoring-distributed-systems/
