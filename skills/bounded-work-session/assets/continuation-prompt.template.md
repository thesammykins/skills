# Fresh-session continuation prompt template

```text
Continue `<task-id>: <task name>` in `<repository/worktree>`.

This is an execution task. Continue the authorised top-level outcome rather than performing another general readiness review.

Read:
- applicable AGENTS.md or CLAUDE.md
- relevant sections of `<canonical task source>`
- concise handoff at `<handoff path>`

Establish reality quickly:
1. Inspect branch, status, relevant diff, and recent commits.
2. Confirm `<expected commit>` is present or an ancestor. Accept compatible descendant commits.
3. Reuse `<recorded check>` if its relevant code, tests, dependencies, configuration, and environment are unchanged.
4. Resolve only material mismatches, then begin implementation.

Immediate next action:
`<one exact action>`

Connected work to continue after that checkpoint:
- `<next connected outcome>`
- `<next connected outcome>`

Local branch/worktree edits, staging, and coherent local commits are authorised. Do not push, merge, deploy, or publish unless separately requested.

Non-goals:
- `<real exclusion>`

Do not create session-state or another handoff unless a real boundary occurs. Do not spawn a reviewer or new thread solely for process. Continue through connected green checkpoints while context remains healthy.
```
