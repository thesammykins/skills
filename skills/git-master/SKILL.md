---
name: git-master
description: Git workflow skill for commits, rebases, history search, and branch cleanup. Use for commit, rebase, squash, blame, or history questions.
---

# Git Master

Use this skill for safe git operations, commit preparation, history lookups, and branch cleanup.

## Principles
- Prefer safe, reversible operations.
- Follow the repository's existing commit style.
- Keep commits atomic when the user asks for commits, but do not force arbitrary split counts.
- Never rewrite published history without explicit approval.
- Never use destructive commands unless the user clearly asks for them.

## Workflow
1. Run a short preflight: inspect `git status`, relevant diffs, recent commit messages, and branch/upstream context.
2. Determine the mode: commit, history search, or history cleanup.
3. Choose the smallest safe set of git commands that solves the request.
4. Summarize the result and any risk before finishing.

## Commit mode
- Review staged and unstaged changes.
- Follow recent commit message style from the repo.
- Prefer one commit per independently understandable change.
- Keep related tests with the behavior they verify when practical.

## Rebase and cleanup mode
- Confirm whether the branch is local-only, shared, or already pushed.
- Before rewriting history, explicitly check whether the rewrite affects only local commits or commits already published to a remote.
- Avoid rebasing `main` or `master` unless the user explicitly requests it.
- If cleanup would require force push, warn clearly before suggesting the next step.

## History search mode
- Use targeted commands such as `git blame`, `git log -S`, `git log -- <path>`, and `git show`.
- Answer who changed it, when it changed, and the likely reason based on commit context.

## Quick reference
- Preflight: `git status`, `git diff`, `git log --oneline -5`, `git branch -vv`
- History: `git blame <path>`, `git log -S "pattern" -- <path>`, `git show <commit>`
