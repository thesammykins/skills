# Amp adapter

Read product and technical specs from the current worktree first. If they are absent but a linked Amp thread contains the approval or decision record, read that thread's full content before using it as spec context.

- Review the actual checked-out diff and files; treat optional `spec_context.md`, `pr_diff.txt`, `pr_description.md`, and `review.json` as harness-provided conveniences, not required inputs.
- Return findings in the review format provided by the current Amp workflow. If none is provided, return a compact spec-alignment section in the thread.
- Do not publish review comments or alter remote pull-request state without explicit authorization.
