# Writing Pull Requests

A pull request is a compact engineering argument for the base-to-head change.
It should reduce context reconstruction for today's reviewer and preserve
material decisions for a future maintainer.

## Title

Describe the whole outcome in repository style:

```text
Retry transient storage failures
Reject expired device enrollment tokens
Preserve filters when returning to search
```

Avoid generic categories, branch names, ticket-only titles, and claims broader
than the actual change:

```text
Fix bug
Refactor
PROJ-1842
Various improvements
```

## Description content

Every merge-ready PR should make these facts recoverable when relevant:

1. **Problem:** what behaviour, constraint, or need caused the change?
2. **Outcome:** what is observably or structurally different now?
3. **Decision:** why was a non-obvious approach chosen?
4. **Evidence:** what observation supports acceptance?
5. **Consequence:** what material risk, compatibility, rollout, or recovery fact
   must a reviewer understand?

These are questions, not mandatory headings. Use repository-required headings
first and omit optional empty sections where allowed.

## Quick fix

Use a title, a short problem/outcome explanation, and focused evidence. No
ceremonial headings are needed.

```markdown
## Treat equal expiry timestamps as stale

Entries expiring exactly at the current timestamp remained valid for one extra
refresh cycle. Treat equality as expired so cache behaviour matches the
documented boundary.

A regression test covers the equality case.
```

The test is worth one line because it names the exact boundary it protects.
Passing local CI goes without saying.

## Standard change

A standard PR normally needs problem, outcome, meaningful evidence, and only
the approach context a reviewer must judge.

```markdown
## Retry transient storage failures

Idempotent storage writes fail immediately on transient 503 responses. Apply
the shared retry policy to this path so its timeout and backoff behaviour stays
aligned with other storage operations; permanent errors still return
immediately.

A new regression covers a 503 followed by success and sees exactly one
persisted write, so the retry can't double-write.
```

An `Approach` heading would add no value here because the decision already fits
in the main explanation.

## Major/high-risk change

Use enough structure to make system consequences reviewable. A useful shape is:

```markdown
## Accept previous signing keys during rotation

<problem and intended outcome>

### Constraints

<security and compatibility invariants>

### Decision

<chosen design and why it satisfies those constraints>

### Trade-offs

<material alternatives, shortcomings, or costs actually considered>

### Compatibility and rollout

<old/new behaviour, deployment order, migration, observation, rollback>

### Evidence

<tests, experiments, rehearsal, benchmarks, security checks, or live evidence,
each connected to the claim it supports>

### Review focus

<the highest-risk decisions reviewers should challenge>
```

This is a prompt set, not a fixed template. Remove sections that contribute no
information and add repository-required fields.

For major/high-risk work, state invariants concretely. “Maintains backward
compatibility” is weaker than “old readers can consume rows written by the new
writer throughout the rolling deployment.” State rollback preconditions rather
than writing “easy to roll back.”

## Draft/exploratory PRs

Draft is a workflow state, not a size class. Tell reviewers what attention is
valuable now:

```markdown
Draft: feedback requested on retry ownership and the storage boundary.

The API shape and failure tests are intentionally incomplete. Please focus on
whether retry belongs in the storage adapter or its caller; naming and final
error mapping can wait until that decision is settled.
```

Do not represent a draft as merge-ready or hide known validation gaps.

## Evidence that explains rather than performs

Weak:

```markdown
### Testing

- Ran unit tests
- Ran lint
- Ran git diff
```

Better, and only when the test proves something a reviewer would ask about:

```markdown
The new reconnect regression fails on the old code with the stale state and
passes once abandoned connections clear it.
```

Local CI passing is a precondition for opening the PR, so never list lint,
formatting, type checks or suite runs.

## Conditional information

Include only when it affects review:

- **Approach:** a decision not obvious from code.
- **Trade-offs:** a real cost or rejected alternative, not manufactured
  sophistication.
- **Rollout/migration:** order, compatibility window, data transformation,
  flags, operator action, observation, rollback.
- **Review focus:** a decision or risk deserving concentrated attention.
- **Non-goals:** scope boundaries important to a major change.
- **Demonstration:** visual or interactive evidence easier to judge than prose.
- **Related work:** issues, incidents, designs, or dependent changes that reduce
  search cost.

Do not narrate files, list every commit, repeat the ticket, or generate a long
summary from diff hunks. The code and hosting UI already expose those facts.

## Before finalizing

Re-read the base-to-head result after review changes. Remove claims about code
that was dropped, add decisions that became part of acceptance, and keep links
supplemental to a self-contained explanation.
