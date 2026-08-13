# Session lifecycle

## 1. Start

Use the lightest setup that preserves correctness:

1. Inspect applicable guidance, branch, worktree, and status.
2. Read the relevant canonical task sections.
3. Identify the requested top-level outcome and first checkpoint.
4. Identify success evidence.
5. Begin implementation.

Create `session-state.json` only when work is expected to cross sessions, coordinates parallel agents, or needs durable state recovery.

## 2. Continue

After a green checkpoint:

1. Commit coherent progress when authorised.
2. Confirm the next step remains connected to the requested outcome.
3. Check that the current objective, diff, and evidence are still clear.
4. Continue in the same session.

A completed checkpoint, milestone, or commit is not itself a stop condition.

## 3. Context-health review

Run this review at material transitions or when symptoms appear, not after every command.

Continue when the agent can state:

- the requested outcome
- what has been completed
- what changed and why
- the next action
- which checks ran or were reused
- the remaining material risks

Stop at a safe checkpoint when those answers are no longer reliable, output loss or compaction affected task state, or the next work crosses a new authority or risk boundary.

## 4. Failure handling

A failing check normally triggers diagnosis and correction in the same session.

- Read the actual failure.
- Distinguish product failure from test assumption, environment, or harness failure.
- Retry transient environment failures only after correcting the cause or execution environment.
- Do not create a handoff after every failed attempt.
- Hand off only when a concrete blocker prevents useful progress or context reliability is degraded.

## 5. Closing

When a real boundary exists:

1. Finish or unwind the atomic operation.
2. Verify and commit complete scoped work when authorised.
3. Inspect the final relevant diff and status.
4. Update the existing issue, plan, or durable task record.
5. Create a concise handoff only when another session is required.
6. Include one exact next action and the evidence that may be reused.
7. Do not automatically spawn a new thread, subagent, or review.

## 6. Same-thread continuation

A user instruction such as “continue”, “do it”, or “move to the next connected step” authorises continued work when:

- it stays within the original requested outcome
- context is healthy
- no new external or destructive authority is required

Do not require the user to explicitly override the skill.
