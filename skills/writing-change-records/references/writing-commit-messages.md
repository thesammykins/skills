# Writing Commit Messages

A commit message is a durable explanation of one logical change. It should make
history searchable and preserve intent that cannot be recovered reliably from
the patch.

## Follow local history

Before choosing style, inspect repository guidance and recent commits in the
area being changed. Match established conventions for:

- prefixes or scopes;
- capitalization and imperative mood;
- subject length;
- body wrapping;
- issue references and trailers;
- whether commits are preserved, rebased, or squash-merged.

Do not introduce Conventional Commit prefixes or another taxonomy unless the
repository already uses or requests it.

When no convention exists, use the durable Git defaults:

- concise imperative subject;
- no trailing period;
- blank line before a body;
- body paragraphs focused on what and why rather than a patch walkthrough.

About 50 characters is a useful subject target, not a reason to remove essential
meaning. A clear standalone subject matters more than an arbitrary count.

## Subject

The subject should complete: “If applied, this commit will …”

Good:

```text
Treat equal expiry timestamps as stale
Preserve filters when returning to search
storage: apply shared retries to idempotent writes
```

Weak:

```text
Fix bug
Updates
Address review feedback
Change cache.ts and cache.test.ts
```

Name the behavioural or engineering outcome, not the work category, filenames,
or author activity.

## Body

Add a body only when it preserves useful context. Depending on the change, it
may explain:

1. the problem or status quo before the commit;
2. the outcome established by the commit;
3. why this approach fits the relevant constraint;
4. a non-obvious consequence, limitation, or excluded case;
5. an issue, benchmark, test result, or trailer required by convention.

Do not narrate each edit. The reader can inspect the patch for implementation
mechanics. Mention a mechanism when it is itself the important decision.

Keep external links supplemental. Summarize the context needed to understand
the commit because tickets and chat threads can disappear or become
inaccessible.

## Quick example

The subject is enough when it names the complete obvious correction:

```text
Correct the timeout default to 30 seconds
```

A short body is useful when the failure mode is not obvious:

```text
Clear stale connection state after failed reconnect

A reconnect that fails before negotiation leaves the previous connected state
visible. Clear it when abandoning the new connection so consumers do not treat
a dead session as active.
```

## Standard example

```text
Apply shared retries to idempotent storage writes

Storage writes currently fail immediately on transient 503 responses even
though callers can safely retry them. Use the shared retry policy so this path
has the same timeout and backoff behaviour as other storage operations.

Permanent failures still return without retrying.
```

The body records the prior behaviour, relevant property, decision, and limit.
It does not list changed helpers or test files.

## Major/high-risk example

```text
Accept previous signing keys during rotation

Replacing the active signing key currently invalidates every session issued by
the prior key, which makes rotation require a coordinated cutover.

Keep the previous key generation valid for one maximum session lifetime. New
sessions use only the active key; verification accepts the active and previous
generations. This preserves mixed-version operation without extending the
lifetime of an individual session.

Keys older than the compatibility window remain rejected, so rollback must
restore the immediately previous generation rather than an arbitrary key.
```

For a high-risk change, preserve the invariant and compatibility decision. If a
single commit spans several independently useful decisions, split it rather than
turning its body into a design document.

## Commits within a PR

Each commit explains its own logical step; the PR explains the base-to-head
outcome and cross-commit decision. Therefore:

- do not paste the PR description into every commit;
- do not use `WIP`, `fixup`, or review-conversation subjects in history meant
  to be retained;
- do not claim the whole feature is complete in an intermediate commit;
- preserve a progression that can be reviewed or reverted coherently when the
  repository retains individual commits.

If the repository squash-merges, write the final squash message as the durable
record the resulting history will actually retain.

## Evidence and trailers

Commit bodies do not need a ritual test list. Include evidence when it explains
the decision, quantifies a claim, records a regression, or is required locally.

Weak:

```text
Tests pass.
Ran git diff.
```

Useful when material:

```text
The new index reduced the representative lookup from 180 ms to 24 ms at the
95th percentile; write latency was unchanged within the benchmark variance.
```

Add issue-closing, sign-off, co-author, review, or test trailers only when they
are factually correct and repository convention calls for them. Never invent
attribution.
