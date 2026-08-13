---
name: creating-conventional-commits
description: Creates Git commits that follow the Conventional Commits 1.0.0 specification as work progresses. Use when asked to commit changes during implementation or before opening a pull request.
---

# Creating Conventional Commits

Creates Git commits that follow the [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) specification.

## Prerequisites

- A clear logical unit of work ready to commit
- Known list of files to include in the commit

## Workflow

### 1. Preflight

Always run preflight here — state changes between when a coordinator started and when this skill commits.

```bash
git status --short --branch
```

- **None** — nothing to commit; stop
- **Any `M A D R C`** — proceed to §2
- **Any `??`** — proceed to §2; intended untracked files are staged there
- **Any `U` / `AA` / `DD`** — stop; resolve before committing

### 2. Identify the Logical Change Set

Pick the files for one logical commit; split unrelated edits into separate commits.

```bash
git diff HEAD -- <files>
```

For untracked files (`??`), stage only the intended ones — never `git add .`:

```bash
git add <intended untracked files only>
```

### 3. Choose the Commit Type

Use the standard Conventional Commits types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`. Pick by intent (new behavior, bug fix, docs-only, formatting-only, internal restructure, test-only, tooling/maintenance).

### 4. Compose the Commit Message

Follow this structure:

```text
<type>[optional scope][!]: <short imperative summary>

[optional body]

[optional footer(s)]
```

Guidelines:
- Keep the summary concise and specific (typically under 72 characters).
- Use an optional scope when it improves clarity, for example `fix(auth): handle token refresh`.
- Use `!` for breaking changes and explain the break in the body or footer.
- Add issue references in footers when relevant: `Closes #123`, `Fixes #123`, or `Refs #123`.

### 5. Commit and Verify

Pass intended files directly to `git commit` to avoid pulling in unrelated staged changes. Use multiple `-m` flags for body and footers.

```bash
git commit <files> -m "fix(auth): handle expired refresh token" \
  -m "Rejects malformed refresh payloads before token verification." \
  -m "Fixes #123"
git log -1 --format="%h %s"
```

### 6. Continue During Ongoing Work

Commit each logical step as work progresses; do not batch.

## Notes

- Usable directly or as a sub-step inside `addressing-github-issues`.
