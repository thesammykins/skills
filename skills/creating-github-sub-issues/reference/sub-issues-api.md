# Sub-Issues REST API Reference

Endpoints used by the `creating-github-sub-issues` skill, plus related endpoints needed only for inspection or cleanup.

## Add Sub-Issue

```
POST /repos/{owner}/{repo}/issues/{issue_number}/sub_issues
```

Request body:

```json
{
  "sub_issue_id": 123456789,
  "replace_parent": false
}
```

- `sub_issue_id` (required): The numeric **ID** of the issue (not the issue number). Must be passed as an integer.
- `replace_parent` (optional): If `true`, replaces the sub-issue's current parent.

## List Sub-Issues

```bash
gh api repos/OWNER/REPO/issues/PARENT/sub_issues
```

## Remove Sub-Issue

```
DELETE /repos/{owner}/{repo}/issues/{issue_number}/sub_issues/{sub_issue_id}
```

## Get Parent Issue

```bash
gh api repos/OWNER/REPO/issues/CHILD/parent
```

## Constraints

- Sub-issues must belong to the same repository owner as the parent.
- Up to 100 sub-issues per parent issue.
- Up to 8 levels of nested sub-issues.
- Issue IDs are different from issue numbers; resolve the ID via `gh api repos/OWNER/REPO/issues/N --jq '.id'`.
- The deprecated `[tasklist]` markdown syntax does not create proper parent-child relationships.
