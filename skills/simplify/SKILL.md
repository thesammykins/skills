---
name: simplify
description: Review task-scoped code for clarity once behavior is verified. Use for a requested simplification or one cleanup pass before human review; do not activate for every comment edit.
---
Review changes in the current branch, or in the scope the user specifies. Apply these criteria without changing behavior. Only touch code in that scope, and run the relevant existing checks after changes.

## Scope and completion

Review only the current task's changes. For branch-wide work, use the complete
committed, staged, unstaged, and relevant untracked scope described by
`anti-ai-slop`; a nonempty staged diff does not exclude the other states.
Perform one combined cleanup pass. Reuse criteria already checked by
`anti-ai-slop` on unchanged hunks, and recheck only material changes.
Preserve user-owned work and staging. Report checks and limitations in the
parent task's handoff rather than replacing its output contract.

## Word choice in code and comments

Use the repository's domain vocabulary and established API names. Prefer precise,
unambiguous names over shorter synonyms. Do not rename concepts solely because
a word is long, Latinate, compound, or technical. Change names only when the
current name is misleading or redundant and the benefit justifies the churn.
Keep one term per concept; preserve distinctions such as observed state versus
stored baseline when they encode different properties.

### Comments

State, in plain English, the constraint the code cannot show: why the **non-obvious** exists.

- ✅ If code is complex and the implementation is non-obvious, add a comment.
- ✅ If a function contains complex behaviors or side effects, add a doc comment.
- 🗑️ If a comment narrates change history from the conversation, delete it.
- 🗑️ If a comment restates code whose behavior is self-evident, delete it.

## Code structure

1. **Inverted pyramid.** Within a file, lead with the exported or significant functions and push helpers below them. Don't bury the lead.
2. **Related concepts over monoliths.** Break a large file into modules that each own one concept.
3. **Combine overlapping concepts.** If two types, functions, or constants overlap significantly, merge them. The fewer distinct concepts a reader must hold in their head, the better.
4. **Use shared code.** Common utilities (ex. file path parsing) may exist in the codebase already. Check for library or utility functions before inlining.
5. **Derivability.** If a value can be computed from values already in scope, don't pass or store it separately. Removing derivable state often simplifies signatures, types, and control flow in one move. Example: an `isDirty` parameter that is always `editorContent !== baseline` can be dropped.

## Overfitting

Code must stand on its own. If a change only makes sense to someone who watched it happen (this conversation, this PR), it is overfitted. Write for the reader who arrives with no history.

- If a name or comment needs the conversation to be understood, rewrite it against the codebase's own vocabulary.
- **No backwards compatibility with unshipped code.** Supporting an old signature, alias, or data shape that only existed earlier in the same branch is compatibility with something that was never deployed. Delete the old path and update its callers.

