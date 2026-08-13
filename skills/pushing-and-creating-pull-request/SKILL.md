---
name: pushing-and-creating-pull-request
description: Pushes the current branch and creates a GitHub pull request with a structured description. Use when asked to push, create a PR, or open a pull request.
---

# Pushing and Creating a Pull Request

Pushes the current branch to the remote and creates a pull request with a well-structured description synthesized from commit history.

## Prerequisites

- At least one commit on the current branch ahead of the base branch

## Workflow

### 1. Preflight

Always run preflight here — state changes between when a coordinator started and when this skill pushes.

```bash
git status --short --branch
```

- **None** — proceed (clean)
- **Only `??`** — warn the user; they will not be pushed. Proceed only with approval
- **Any `M A D R C`** — stop; commit (via `creating-conventional-commits`) or stash before pushing
- **Any `U` / `AA` / `DD`** — stop; resolve before pushing

Resolve the default branch and confirm the current branch is not it:

```bash
DEFAULT=$(git rev-parse --abbrev-ref origin/HEAD 2>/dev/null)
DEFAULT=${DEFAULT#origin/}
DEFAULT=${DEFAULT:-main}
CURRENT=$(git symbolic-ref --short HEAD)
[ "$CURRENT" != "$DEFAULT" ] || { echo "Refusing to push from default branch ($CURRENT)"; exit 1; }
```

If `origin/HEAD` is unset (e.g., on manually-added remotes or after a default-branch rename), run `git remote set-head origin --auto` once before retrying — the silent `main` fallback may otherwise produce a wrong-base PR.

### 2. Gather Commit History

Reuse `$DEFAULT` from step 1 to collect commits ahead of the base branch:

```bash
BASE="origin/$DEFAULT"
git log "$BASE"..HEAD --reverse --format="%h %s%n%n%b"
```

For PRs targeting a non-default base, the caller should specify it explicitly via `gh pr create --base <branch>` in step 6.

Parse each commit for:
- **Type** (`feat`, `fix`, `docs`, etc.) from the conventional commit prefix
- **Description** from the subject line
- **Body** for additional context
- **Issue references** (e.g., `Closes #N`, `Fixes #N`, `Refs #N`)

### 3. Fetch Referenced Issue Context

For each issue number referenced in commits or the branch name:

```bash
gh issue view ISSUE_NUMBER --json title,body,labels
```

Use the issue title and body to understand the motivation and reason for the change.

### 4. Determine PR Title

- **Single commit**: Use the commit subject line as the PR title.
- **Multiple commits**: Synthesize a title that captures the overall change, using conventional commit format (e.g., `feat: add findings service with pagination`).

The title should match the primary conventional commit type of the work.

### 5. Compose PR Description

Structure:

```markdown
A 2–3 sentence paragraph explaining what changed and why, drawing motivation from the referenced issue.

- One bullet per logical change (single commit → derive from body/diff; multiple commits → one bullet per commit, prefix stripped)
- Group related commits

Closes #N
```

Rules:
- Never insert newlines inside a paragraph or bullet — each is one unwrapped line. GitHub renders mid-paragraph newlines as literal breaks.
- Use `Closes`/`Fixes` for fully resolved issues, `Refs` otherwise. Place at end of body, collected from all commits and the branch name.

### 6. Push and Create the PR

Pipe the body via heredoc to `--body-file -` to avoid shell-escaping pitfalls with backticks, quotes, and `$`:

```bash
git push -u origin HEAD
gh pr create --title "<title>" --body-file - <<'EOF'
<body>
EOF
```

For non-default base branches, add `--base <branch>`. Capture the PR URL printed by `gh pr create` and return it to the user.
