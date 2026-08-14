---
name: create-pr
description: Creates a focused pull request for the current branch after reviewing the diff and running relevant checks. Use when asked to open, create, submit, or prepare a pull request.
---

# Create a Pull Request

Prepare and create a reviewable pull request for the current branch. Creating a PR is an external action: do it only when the user explicitly asks.

## Before creating the PR

1. Read repository instructions and the pull-request template, if present.
2. Determine the base branch from repository configuration, an existing PR, or the user's request. Do not assume `main` or `master`.
3. Update the branch only when necessary and safe. Do not merge, rebase, reset, or force-push without explicit approval when it could discard or rewrite work.
4. Review the complete change:

   ```bash
   git status --short
   git log <base>..HEAD --oneline
   git diff --check <base>...HEAD
   git diff --stat <base>...HEAD
   git diff <base>...HEAD
   ```

5. Run the repository-required format, lint, type, build, and relevant test checks. For bug fixes, add a regression test unless impractical and state why. Do not claim checks passed when they were skipped or unavailable.
6. Confirm that the branch contains only the requested work, no secrets, and no generated or unrelated files.

## Write the title and body

Load `writing-change-records` to draft the title and body from the final
base-to-head change, linked context, and observed verification evidence. That
skill owns the writing contract; this skill owns the branch checks and remote
PR operation.

Follow the repository template when available. Do not fall back to generic
headings or use command lists as the explanation of correctness. Never require
or create external tracking solely for the PR.

Use a logical feature slug in branch names, paths, and spec references.

## Create or update

First determine whether the current branch already has a PR:

```bash
gh pr view --json number,url 2>/dev/null
```

Create a draft by default unless the user asks for ready-for-review:

```bash
gh pr create --draft --title "<title>" --body-file <body-file>
```

For an existing PR, update only the fields that are stale:

```bash
gh pr edit --title "<title>" --body-file <body-file>
```

Read the returned URL and PR metadata back after the command. Report the URL, base branch, verification results, and remaining risks. Do not assign reviewers, apply labels, mark ready, merge, or change release state unless the user asks.

## Boundaries

- Do not bypass failing checks by weakening tests, suppressing errors, or excluding files.
- Do not include co-author trailers or attribution not explicitly requested or supported by the actual contributors.
- Keep a PR focused on one logical outcome; split unrelated work rather than hiding it in a broad description.
