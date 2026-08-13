---
name: bounded-work-session
description: Keep genuinely long, resumed, parallel, or high-risk work productive and recoverable without forcing artificial thread boundaries. Use when a task is already crossing sessions, context reliability is at risk, parallel agents need coordination, external or data state needs durable recovery, or the user explicitly requests a formal handoff. Do not use for ordinary non-trivial implementation, focused reviews, or work that can continue safely in the current session.
---

# Bounded Work Session

The objective is sustained delivery with recoverable state. A milestone is a checkpoint, not an automatic reason to stop.

## Operating defaults

1. Continue the authorised top-level objective in the current session while context is reliable.
2. Work through as many connected, independently verifiable checkpoints as the objective requires.
3. Commit coherent green progress when local commits are authorised by the applicable guidance.
4. Create durable session state only when work is likely to cross an actual session boundary or carries meaningful state risk.
5. Create a handoff only when a new session is genuinely required, the user asks to stop, or a concrete blocker prevents useful continuation.
6. Do not automatically spawn a new thread, subagent, or reviewer. Use them only when they provide distinct value.

## Fast start

For a new long-running task:

1. Read applicable guidance and the relevant canonical task sections.
2. Inspect branch, worktree, status, and the directly relevant code path.
3. State the requested outcome, first checkpoint, likely write surface, and success evidence.
4. Begin implementation. Do not create governance artefacts before work unless they are needed for recovery or risk control.

For resumed work:

1. Read applicable guidance, the canonical task source, and the latest concise handoff if one exists.
2. Inspect current branch, status, relevant diff, and recent commits.
3. Accept expected descendant commits when they do not invalidate the task. Exact HEAD equality is required only when the handoff explicitly marks it as a safety invariant.
4. Reuse prior verification when relevant inputs have not changed.
5. Continue implementation after resolving only material mismatches.

## Connected checkpoint loop

Repeat while the objective remains authorised and context is healthy:

1. Choose the next connected product or engineering outcome.
2. Trace only the code and contracts needed for that outcome.
3. Implement it.
4. Run the narrowest useful check and verify the postcondition.
5. Inspect the scoped diff.
6. Commit coherent green progress.
7. Continue to the next connected checkpoint without creating a new session merely because the checkpoint completed.

## Scope and blast radius

Read broadly enough to find the real root cause. Write narrowly enough to keep the change reviewable.

When evidence expands the causal path:

- state the newly implicated path and why it matters
- extend the write surface to the smallest complete causal closure
- add verification for the wider impact
- continue in the same session unless the new work is materially unrelated, high-risk, or context is no longer reliable

Do not require a state-file edit before every newly implicated code edit. Keep the boundary explicit in the working notes or session state when one exists.

## Context health

Do not use fixed file, subsystem, commit, or token counts as automatic stop rules. Stop at a safe checkpoint only when there is evidence of degradation, such as:

- repeated rereading is required to remember the objective or current state
- the agent cannot explain changed files, remaining work, or checks already run
- conversation or tool output has been compacted or truncated in a way that loses task state
- the implementation path is repeatedly changing without progress
- several unrelated objectives are competing in the same context
- a new permission, credential, destructive-action, or rollback boundary is required

If context remains clear, continue.

## Review policy

- Independent review is appropriate before merge or release, for high-risk changes, or when the user requests it.
- Do not require review before every handoff or checkpoint.
- Do not review a review.
- One review is enough unless findings caused material changes.
- A clean review returns control to implementation or completion.
- Review existing evidence before rerunning checks.

## Git-state recovery

A large mixed dirty tree is a repository-state problem, not a reason for endless read-only reconciliation.

- Prefer a dedicated branch or worktree for new work.
- If no clean base exists, resolve the repository once by creating a reviewed baseline or selectively committing coherent closures.
- Local commits are allowed when the applicable guidance authorises implementation and does not prohibit them.
- Do not generate continuation prompts that revoke already granted local commit authority.
- Do not carry the same ambiguous staged, unstaged, and untracked state through repeated review-only sessions.

## Evidence reuse

A prior check can be reused when all are true:

- the exact command and result are recorded
- relevant source, tests, dependencies, build configuration, and environment have not materially changed
- the evidence is sufficient for the current claim
- no later failure contradicts it

Record reused evidence as reused, not rerun. Rerun only when inputs changed, the result is incomplete, or the user requests fresh execution.

## Real stop conditions

Create a handoff and stop only when one applies:

- the requested objective is complete
- the user asks to pause or switch work
- a concrete external blocker prevents further useful progress
- context health has materially degraded
- the next work is genuinely unrelated to the authorised objective
- the next action crosses a new destructive, credential, data, or external-state boundary
- project or harness policy imposes a real limit

A same-thread request to continue is valid when the objective remains authorised and context is healthy.

## Handoff and continuation

When a real boundary exists:

1. Finish or safely unwind the current atomic operation.
2. Commit complete scoped work when authorised.
3. Record observed repository state, completed outcomes, evidence, blockers, and one exact next action.
4. Keep the handoff concise and delta-focused. Use the existing issue, plan, or task tracker when it is already the system of record.
5. Create a standalone handoff file only when durable cross-session recovery needs it.
6. Provide a continuation prompt only when a new session is actually needed.
7. Do not automatically create a new thread or subagent unless the user requested continued execution and the capability adds value.

## References

Read only what is needed:

- Scope, context, and dirty-tree recovery: `references/context-and-scope.md`
- Session continuation and stop decisions: `references/session-lifecycle.md`
- Handoff, resume, and evidence reuse: `references/handoff-and-resume.md`
- Harness metrics and mechanical controls: `references/enforcement.md`

## Optional helpers

- `python3 scripts/capture_git_state.py`
- `python3 scripts/session_guard.py check <session-state.json>`
- `python3 scripts/session_guard.py scope <session-state.json>`
- `python3 scripts/validate_skill.py .`

The helpers support recovery and scope checks. They do not decide that a session must end.
