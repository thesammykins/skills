---
name: addressing-github-issues
description: Implements a GitHub issue up to the point of human review. Fetches issue context, creates a working branch, implements the change, and commits. Stops before push/PR so a human can review or amend. Use when given an issue number to work on.
---

# Addressing GitHub Issues

Coordinates the path from issue → branch → implementation → commits, leaving the branch ready for a human to review (and then push/open a PR separately).

## Workflow

### 1. Preflight

```bash
git status --short --branch
```

- **None** — proceed (clean)
- **Only `??`** — proceed; the commits step will handle them
- **Any `M A D R C`** — stop and ask the user (commit, stash, or discard)
- **Any `U` / `AA` / `DD`** — stop (merge conflict)

Each sub-skill runs its own preflight at the moment it executes; do not instruct them to skip it (state changes during implementation).

### 2. Fetch the Issue

Start with the minimum context:

```bash
gh issue view ISSUE_NUMBER --json title,body,labels,assignees
```

Fetch comments when the body, labels, or assignees suggest they add value — for example: ongoing discussion, open questions, clarifications from maintainers, reproduction details, design decisions, or implementation hints not captured in the body.

```bash
gh issue view ISSUE_NUMBER --json comments
```

Extract the request, acceptance criteria, and labels.

### 3. Create the Working Branch

Use the `creating-conventional-branches` skill with the issue number, title, and labels.

### 4. Implement the Solution

Implement the change following project conventions and AGENTS.md. Verify the implementation against the acceptance criteria from step 2 (run tests, exercise the behaviour) before moving on.

### 5. Commit with Conventional Commits

Use the `creating-conventional-commits` skill. Include `Closes #ISSUE_NUMBER` (or `Fixes #ISSUE_NUMBER`) in the footer of the commit that resolves the issue.

## Done when

- The working branch contains one or more conventional commits implementing the issue.
- Acceptance criteria are demonstrably met.
- Nothing has been pushed; the branch is ready for human review before invoking `pushing-and-creating-pull-request`.
