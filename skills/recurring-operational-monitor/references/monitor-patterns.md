# Operational Monitor Patterns

## Monitor contract

```markdown
Name / owner:
User-visible or operational symptom:
Source and query:
Event key / grouping key:
Cadence and lookback:
Pending duration / tolerance:
Severity and destination:
Required human action / runbook:
Recovery notification:
Checkpoint and last-good state:
Monitor-health signal:
Expiry or review date:
```

An alert without an action or owner is dashboard data, not a page.

## Source-specific patterns

### Online service

Prefer high-level user symptoms: error rate, latency distribution, availability, or material business loss. Use lower-level causes for diagnosis unless they independently require action. Include traffic volume so a ratio is interpretable.

### Batch/cron job

Monitor last successful completion, not merely process invocation. Allow at least enough time for normal duration and transient retry; if one missed run cannot be tolerated, increase execution frequency rather than paging on every single failure.

### Queue/backlog/inbox

Monitor age of oldest actionable item plus count over threshold. Define actionable state precisely and exclude resolved/waiting/non-owned items. Fingerprint by stable item ID plus condition transition.

### Logs

Prefer structured reason codes/counters over text heuristics. If text matching is unavoidable, pin source/service/revision and test false-positive examples. A raw “error” count is rarely actionable without rate, traffic, severity and context.

### Post-deployment watch

Bind to deployment revision and a fixed soak window. Compare candidate behavior with baseline where possible. Stop or downgrade automatically at the end; do not leave temporary high-frequency watches forever.

### Capacity

Alert early enough for a human to act before exhaustion. Use trend/time-to-exhaustion when available rather than a static percentage alone.

## Alert routing

- **Page:** active or imminent user harm requiring prompt action.
- **Ticket/task:** action needed but not urgent.
- **Dashboard/report:** useful context with no immediate action.
- **Silent state update:** normal/no-match tick.

Group related events, inhibit dependent noise when an upstream symptom explains it, and use cooldown/repeat intervals deliberately. Preserve the full affected set behind one compact notification.

## State machine

Use explicit states rather than “send if query non-empty”:

`UNKNOWN → HEALTHY → PENDING → FIRING → RECOVERED → HEALTHY`

- UNKNOWN: source or parser has not produced a trustworthy sample.
- PENDING: symptom exists but has not crossed duration/count threshold.
- FIRING: threshold crossed; one notification per fingerprint/group.
- RECOVERED: optional one-time resolution notification.

Source failures move to UNKNOWN and may trigger a separate monitor-health condition; they never overwrite the last good checkpoint.

## Polling windows

Use overlap plus deduplication to avoid gaps:

- query `[last_success - overlap, now - ingestion_delay]`;
- checkpoint only after successful evaluation and state write;
- fingerprint stable source ID + rule version + transition;
- retain enough fingerprints to cover the maximum lookback/retry period.

Do not use timestamps alone as event identity when late or reordered delivery is possible.

## Verification scenarios

Before scheduling, exercise:

1. normal/empty result → no alert;
2. pending blip → no page before tolerance;
3. sustained/new symptom → one alert;
4. repeated same sample → no duplicate;
5. multiple related events → grouped notification;
6. recovery → one recovery if requested;
7. source timeout/auth/parser error → monitor-health behavior, last-good preserved;
8. late event/window overlap → detected once;
9. delivery test → observed on actual destination;
10. restart/state reload → no forgotten checkpoint or duplicate storm.

## Primary resources

- Google SRE monitoring, black-box/white-box and human interruption: https://sre.google/sre-book/monitoring-distributed-systems/
- Prometheus alerting principles and metamonitoring: https://prometheus.io/docs/practices/alerting/
- Alertmanager grouping, inhibition and silences: https://prometheus.io/docs/alerting/latest/alertmanager/
- OpenTelemetry signal selection: https://opentelemetry.io/docs/concepts/signals/
- Host scheduler and delivery behavior: consult the selected harness adapter before creating a job.
