# Handoff, resume, and evidence reuse

## 1. Prefer the existing system of record

Use the current issue, execution plan, specification checklist, branch, commits, and tests as the durable record. Add a separate handoff file only when those artefacts do not provide enough cross-session recovery.

## 2. Concise handoff contents

A handoff should contain only information the next agent cannot cheaply derive:

- requested outcome and current status
- branch/worktree and relevant commits
- intentional uncommitted paths
- completed connected outcomes
- exact checks run and their results
- evidence that can be reused and the inputs it covers
- blockers, deviations, or material risks
- one exact next action
- relevant canonical paths

Do not reproduce the full specification, repository inventory, transcript, or every file read.

## 3. Continuation prompt

A continuation prompt should:

- state that this is an execution task, review, or investigation
- identify the requested top-level outcome
- name the relevant task source and handoff
- grant the same local commit authority that already applies
- name the immediate next action
- identify real non-goals
- say whether prior evidence may be reused

Do not freeze an exact HEAD unless exact equality is a real safety invariant. Prefer “confirm this commit is an ancestor and inspect relevant intervening changes”.

Do not include blanket “do not commit” wording unless the user or project policy requires it.

## 4. Resume fast path

Before editing:

1. Read applicable guidance and the relevant task source.
2. Read the concise handoff.
3. Inspect branch, status, relevant diff, and recent commits.
4. Accept expected descendants when relevant paths and requirements remain compatible.
5. Check whether prior evidence remains fresh.
6. Resolve only material mismatches.
7. Continue implementation.

Do not rerun every prior test or reread every specification section just because the session is new.

## 5. Evidence freshness

Prior evidence is reusable when:

- the command and observed result are recorded
- relevant code, tests, dependencies, configuration, and environment are unchanged
- the result proves the current claim
- no later contradictory result exists

Mark the evidence as reused. Rerun when relevant inputs changed, the result is incomplete or stale, the environment changed materially, or fresh execution is explicitly requested.

## 6. Mismatch handling

Do not treat any mismatch as an automatic stop.

Continue after reconciling harmless changes such as:

- documentation-only descendant commits
- unrelated dirty paths outside the task
- expected generated output
- timestamp or count changes that do not affect the claim

Stop before mutation only when the mismatch affects requirements, relevant implementation, data safety, authority, or the validity of evidence.

## 7. Review loop prevention

- A clean review should lead to implementation, merge preparation, or completion.
- A review finding should lead to a fix and at most one focused re-review.
- Do not create a second reviewer to confirm an identical no-go or no-findings review.
- Do not create a handoff whose next action is another equivalent review unless new evidence will become available.
