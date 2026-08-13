# Mechanical enforcement and evaluation

Prompt guidance alone cannot guarantee productive autonomy. Use harness controls to detect process loops without forcing premature stops.

## Recommended measurements

Track per task or session:

- orientation and repository-discovery tool calls
- implementation or mutation tool calls
- verification tool calls
- review-only tool calls
- repeated commands with unchanged inputs
- files changed
- coherent commits created
- acceptance criteria completed
- handoff and session-state artefacts created
- subagents or new threads spawned
- total tokens, latency, retries, and approval interruptions

Optimise for completed verified outcomes, not minimum tokens in isolation.

## Anti-loop controls

Warn when:

- a task produces multiple handoffs without an intervening implementation commit
- two review sessions return materially identical findings
- the same expensive check is rerun without relevant input changes
- a continuation prompt removes local commit authority granted by global or project guidance
- exact-HEAD mismatch blocks on a harmless descendant
- process artefacts outnumber product or test artefacts
- a dirty-tree review repeats without an authorised recovery action

Do not automatically close a session solely because of a file, subsystem, commit, turn, or token count.

## Optional hard controls

Use hard limits only for real safety or platform constraints:

- destructive or external action approval
- credential and permission boundaries
- protected branches and required CI
- data migration dry-run and rollback gates
- maximum retries for an unchanged failing action
- actual model or harness context limits

## Trial evaluation

Run the next-thread trial in `NEXT_THREAD_TRIAL.md`. Compare:

- verified product outcomes per session
- commits per implementation session
- duplicated review or test work
- handoff count
- repository cleanliness at end
- whether the same session continued through connected checkpoints
