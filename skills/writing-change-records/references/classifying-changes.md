# Classifying Changes

Classification chooses the lightest engineering record that lets a reviewer
and future maintainer judge the change correctly. It is not a label to include
in the output.

## Decision questions

Ask:

1. How much context is needed to understand why the result is correct?
2. Does the change establish or alter an invariant or design choice?
3. Which callers, users, data, services, or operators are in the blast radius?
4. How difficult is rollback or recovery?
5. Do compatibility or deployment order affect safety?
6. Is focused validation enough, or does acceptance depend on broader evidence?

Use the highest class indicated by the answers.

## Quick

All or nearly all of these are true:

- The defect or correction is narrow.
- Intended behaviour is already established.
- The change is local and low-risk.
- No architecture, compatibility, or operational decision needs review.
- One focused check can establish the result.

Typical records:

- Commit: a specific subject; a short body only if the failure mode is not
  obvious.
- PR: a specific title, one short problem/outcome explanation, and focused
  evidence.

Do not add architecture, trade-offs, risk, or non-goal sections merely to fill a
template.

## Standard

Typical signals:

- Bounded new behaviour or normal feature work.
- A meaningful local refactor.
- A non-trivial bug with understood blast radius.
- Several files or components implementing one coherent decision.
- A local approach choice that is not obvious from the code.

Typical records:

- Commit: subject plus a body covering the prior problem and why this approach
  is appropriate.
- PR: problem, outcome, meaningful evidence, and approach/trade-offs only when
  they affect review.

## Major/high-risk

Use this treatment when any of these materially affect acceptance:

- architecture or cross-service coordination;
- a public API, protocol, file format, or caller contract;
- schema migration, stored data, or irreversible mutation;
- authentication, authorization, security, privacy, or another trust boundary;
- concurrency, ordering, retries, idempotency, or distributed coordination;
- deployment order, compatibility window, feature-flag state, or rollback;
- broad user-visible behaviour or difficult recovery;
- significant performance, capacity, or cost consequences.

The record may need:

- problem and intended outcome;
- constraints and invariants;
- decision and why it satisfies them;
- alternatives actually considered and material trade-offs;
- blast radius and failure mode;
- old/new compatibility;
- migration, rollout, rollback, and observability;
- evidence proportionate to the cost of failure;
- the decisions reviewers should challenge.

Do not add every item automatically. Include it when omission would make the
change harder to judge or maintain.

## Risk modifiers

### Security and privacy

Preserve the trust boundary, expected failure behaviour, compatibility impact,
and evidence beyond the happy path. Do not expose exploit details in a public
record when repository policy requires private handling.

### Stored data and migrations

Preserve old/new reader and writer compatibility, operation order, partial
failure, rollback, and data validation where relevant.

### Public contracts

Preserve caller impact, versioning, deprecation, and transition behaviour.

### Concurrency and distributed systems

Preserve invariants, ordering, cancellation, timeout, retry, idempotency, race,
and recovery decisions that matter to correctness.

### Performance and capacity

Name the mechanism and observed measurement. Do not turn “improves performance”
into a claim without a relevant comparison.

### Generated or mechanical changes

Large generated diffs can have low conceptual complexity. Record what generated
the output, why regeneration was needed, and how determinism or correctness was
checked. Do not narrate generated files.

## Draft/exploratory overlay

Draft is independent of class. State:

- what is complete;
- what is intentionally incomplete;
- what feedback is useful now;
- what should wait;
- which validation gaps remain before merge readiness.

This keeps reviewers from treating intentional incompleteness as an accidental
defect.

## Scope failure

A record is not a substitute for a coherent change. Consider splitting when:

- refactoring and unrelated behaviour changes are mixed;
- multiple independent defects are bundled;
- cleanup crosses unrelated modules;
- a migration is coupled to unrelated feature work;
- no single engineering outcome accurately names the change.

Line count is only a cognitive-load signal. It is never the decision rule.
