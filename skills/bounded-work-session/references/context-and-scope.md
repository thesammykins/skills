# Context, scope, and repository state

## 1. Lightweight focus contract

For genuinely long or resumed work, keep a compact focus record:

- requested top-level outcome
- immediate next checkpoint
- relevant canonical source
- likely write surface
- explicit non-goals
- success evidence
- current blocker, if any

This may live in the current plan, issue, work-state file, or concise working notes. Do not create a new repository artefact solely to restate information already durable elsewhere.

## 2. Context management by symptoms

Do not enforce universal limits such as five documents, twelve files, two subsystems, or four commits. Those limits may stop a healthy task or encourage artificial splitting.

Prefer targeted retrieval:

1. Read applicable guidance and relevant task sections.
2. Search for named symbols, errors, routes, schemas, configuration, and tests.
3. Read targeted files and ranges.
4. Trace callers and persistence far enough to establish the causal path.
5. Summarise large outputs before loading more.
6. Avoid repeatedly rereading unchanged material.

Context is unhealthy when the agent loses the objective, cannot explain the current diff, repeats completed work, or needs repeated full reloads to continue.

## 3. Read radius and write radius

The read radius can be broad during investigation. The write radius should follow the smallest complete causal closure.

Suggested labels:

- `focused`: one component plus directly related tests
- `connected`: adjacent modules linked by observed calls, data, configuration, or contracts
- `cross-cutting`: shared contracts or multiple services/packages
- `system-data`: migrations, bulk data, permissions, infrastructure, or destructive state

Labels describe risk. They do not create mandatory session boundaries.

## 4. Expanding scope

When new evidence implicates another path:

1. Explain the observed connection.
2. Confirm the additional path is required for a complete fix.
3. Extend the working write surface.
4. Add appropriate verification.
5. Continue unless the work becomes unrelated or crosses a new risk or authority boundary.

Do not stop merely because the initial file list changed. Initial file lists are hypotheses, not contracts.

## 5. Dirty-tree recovery

Repeatedly preserving a large mixed tree creates compounding cost and makes atomic review impossible.

Use this order:

1. Continue in an existing clean task branch or worktree.
2. Create a clean worktree from the last known-good commit.
3. Selectively commit a coherent existing workstream when local commits are authorised.
4. Establish a reviewed baseline commit when the repository is unborn and the current state is intended to be retained.
5. Ask once when ownership of the existing dirty state cannot be determined safely.

After recovery, keep separate workstreams on separate branches or worktrees. Do not use handoffs as a substitute for repository hygiene.
