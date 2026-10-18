---
name: done
description: When we finish a feature. Use when the user says work is done, asks to merge a worktree back to main/master, or clean up a worktree.
---

Review remaining uncommitted code. If all changes are related and can fit into an atomic commit, create a single commit. If work should be broken into multiple atomic commits, do so and commit all.

If we're on a worktree or branch, rebase onto main/master and resolve conflicts.

Run the repository's local CI (lint, typecheck, tests, build). Fix failures before continuing; never push red.

Fast-forward main/master to the finished work and push it to origin. Open a PR only if the user asks for one. Don't create version tags; releases are tagged only on request.

If work on this feature was tied to a GitHub issue or taskboard ticket, mark that issue as completed if available tooling allows.

Finally, clean up the worktree.

