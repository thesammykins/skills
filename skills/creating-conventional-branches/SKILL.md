---
name: creating-conventional-branches
description: Creates and checks out Git branches that follow Conventional Branch naming. Use when asked to create a new branch from an issue, ticket, or task description.
---

# Creating Conventional Branches

Creates a new Git branch using the [Conventional Branch](https://conventional-branch.github.io/) pattern and verifies the result.

## Prerequisites

- Branch naming context (issue number, ticket number, or short task description)
- Clean git working directory, or explicit user approval to proceed with local changes

## Workflow

### 1. Preflight

Skip the `git status` call only when a coordinator preflighted **immediately before** invoking this skill **and no file-changing step has run since**. Otherwise:

```bash
git status --short --branch
```

- **None** — proceed (clean)
- **Only `??`** — proceed (untracked files survive `git checkout -b`)
- **Any `M A D R C`** — stop and ask the user before creating a branch
- **Any `U` / `AA` / `DD`** — stop; resolve before branching

### 2. Switch to the Up-to-Date Default Branch

Resolve the default branch via `origin/HEAD`, falling back to `main`:

```bash
git fetch origin
DEFAULT=$(git rev-parse --abbrev-ref origin/HEAD 2>/dev/null)
DEFAULT=${DEFAULT#origin/}
DEFAULT=${DEFAULT:-main}
git checkout "$DEFAULT"
git pull --ff-only
```

If `origin/HEAD` is unset, run `git remote set-head origin --auto` once before retrying.

If the user explicitly asks to branch from a different base, skip this step.

### 3. Gather Branch Inputs

Collect:
- **Issue or ticket number** (if available)
- **Short description** from the issue title or task summary
- **Type signal** from labels or request language (bug, feature, docs, etc.)

### 4. Select Branch Prefix

- `fix/` — bugs, defects
- `hotfix/` — critical or urgent production fixes
- `chore/` — docs, dependencies, tooling, maintenance
- `release/` — release branches
- `feat/` — everything else (default, including new features and enhancements)

### 5. Build the Description Slug

Lowercase, alphanumerics + hyphens only; 3–8 words.

### 6. Compose the Branch Name

Use one of these formats:

- With issue number: `<prefix>/<issue-number>-<description-slug>`
- Without issue number: `<prefix>/<description-slug>`

Examples:

```bash
feat/123-add-user-authentication
fix/456-resolve-login-timeout
chore/update-readme-links
```

### 7. Create

```bash
git checkout -b <branch-name>
```

If the branch already exists, check it out instead with `git checkout <branch-name>`.

## Notes

- Prefer issue number in the branch name when available.
- Usable directly or as a sub-step inside `addressing-github-issues`.
