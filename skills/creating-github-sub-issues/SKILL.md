---
name: creating-github-sub-issues
description: Creates GitHub issues with parent-child relationships using the gh CLI and REST API. Use when asked to create issues with sub-issues, parent issues, or issue hierarchies.
---

# Creating GitHub Issues with Sub-Issues

Creates GitHub issues with proper parent-child relationships visible in the GitHub UI sidebar.

## Workflow

### 1. Create the Parent Issue

```bash
gh issue create \
  --title "Parent Issue Title" \
  --body "Description of the parent issue..."
```

Note the issue URL returned (e.g., `https://github.com/owner/repo/issues/27`). Keep the parent body focused on scope/context; do not append sub-issue IDs or checklists.

### 2. Create Sub-Issues

Create each sub-issue with only its own description:

```bash
gh issue create \
  --title "Sub-issue title" \
  --body "Description..."
```

### 3. Link Sub-Issues to Parent

Get the issue ID (not issue number) for each sub-issue:

```bash
gh api repos/OWNER/REPO/issues/ISSUE_NUMBER --jq '.id'
```

Add sub-issues to the parent using the REST API with JSON input:

```bash
issue_id=$(gh api repos/OWNER/REPO/issues/28 --jq '.id')
gh api repos/OWNER/REPO/issues/27/sub_issues -X POST --input - <<< "{\"sub_issue_id\": $issue_id}"
```

The `sub_issue_id` must be passed as an integer, not a string.

### 4. Batch Add Multiple Sub-Issues

```bash
for issue_num in 28 29 30 31; do
  issue_id=$(gh api repos/OWNER/REPO/issues/$issue_num --jq '.id')
  gh api repos/OWNER/REPO/issues/27/sub_issues -X POST --input - <<< "{\"sub_issue_id\": $issue_id}"
done
```

## Done when

- Every `POST .../sub_issues` returned 2xx (the response body includes the linked sub-issue).
- For batches of 3+ children or any suspected failure, run one verification call:

  ```bash
  gh api repos/OWNER/REPO/issues/PARENT/sub_issues --jq '[.[].number]'
  ```

  Confirm it lists every expected child number. Skip this check for ≤2 children — the per-call 2xx is sufficient.

## Notes

- Do not add `Parent issue: #...` in sub-issue bodies — GitHub already shows the parent in the UI when the API relationship exists.
- Do not maintain sub-issue checklists or ID lists in the parent body — linked sub-issues are already shown in the parent.
- For inspection, removal, or other endpoints (List / Remove / Get Parent), see [`reference/sub-issues-api.md`](reference/sub-issues-api.md).
