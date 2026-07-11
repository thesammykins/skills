---
name: gh-cli
description: Official GitHub CLI (gh) automation for PRs, Issues, Actions, and Repos.
license: MIT
---

# gh-cli Agent

Expert GitHub automation using the official `gh` CLI tool.
Enforces machine-readable outputs (`--json`) and safe, atomic operations for Pull Requests, Issues, Repositories, and Actions.

---

## PHASE 0: Context Gathering (MANDATORY)

<context_gathering>
**Execute these commands IN PARALLEL to establish ground truth:**

```bash
# Verify installation and check version
gh --version || echo "NOT_INSTALLED"

# Check authentication status
gh auth status || echo "NOT_AUTHENTICATED"

# Check current repo context (if applicable)
gh repo view --json name,owner,url || echo "NO_REPO_CONTEXT"
```

**Capture these data points:**
1. Is `gh` installed? (If "NOT_INSTALLED", STOP and ask user to install it: `brew install gh` or equivalent).
2. Is the user authenticated? (If "NOT_AUTHENTICATED", STOP and ask user to run `gh auth login`).
3. Are we inside a git repository? (Required for context-dependent commands like `pr create`).
</context_gathering>

---

## PHASE 1: Analysis & Strategy (BLOCKING)

<analysis>
**Analyze the user request and determine the GitHub operation strategy.**

### 1.1 Decision Logic

| Condition | Strategy |
|-----------|----------|
| User wants to **read** data (list PRs, view issue) | **Read-Only**: Use `list`/`view` with `--json` flag. Parse output strictly. |
| User wants to **modify** state (create PR, merge) | **Transactional**: Check prerequisites -> Execute -> Verify. |
| User wants to **checkout** code | **Context-Switch**: Verify clean working directory -> `gh pr checkout`. |
| User wants to **run/watch** CI/CD | **Observability**: `gh run list` -> `gh run watch`. |

### 1.2 MANDATORY OUTPUT

**You MUST output this block before proceeding. NO EXCEPTIONS.**

```text
ANALYSIS RESULT
===============
Target Repo: [owner/repo]
Operation: [Read | Write | Context-Switch | CI]
Command Chain:
  1. [Validation Step]
  2. [Primary Action]
  3. [Verification Step]
Required Scopes: [e.g. repo, read:org]
```
</analysis>

---

## PHASE 2: Execution (Atomic & Safe)

<execution>
### 2.1 Core Patterns

#### Pattern A: Reading Data (JSON is MANDATORY)
**NEVER** parse the default tabular text output. It is intended for humans, not agents.
```bash
# Correct: Get specific fields as JSON
gh pr list --json number,title,url,state

# Correct: View specific issue details
gh issue view 123 --json body,comments
```

#### Pattern B: Creating Pull Requests
```bash
# 1. Push current branch
git push -u origin HEAD

# 2. Create PR with explicit title/body
gh pr create --title "feat: new feature" --body "Detailed description..." --web
# Note: --web is optional, usually we want non-interactive:
gh pr create --title "..." --body "..." --base main
```

#### Pattern C: GitHub Actions
```bash
# List recent runs
gh run list --limit 5 --json databaseId,status,conclusion,workflowName

# Watch a run
gh run watch <run-id> --exit-status
```

### 2.2 Step-by-Step Instructions

1. **Pre-Flight Check**:
   - Ensure `gh` is authenticated.
   - For write operations, ensure local git state is clean/synced if necessary.

2. **Action Execution**:
   - Construct the `gh` command with appropriate flags.
   - **ALWAYS** use double quotes for string arguments (`--body "..."`).
   - Capture output (stdout/stderr).

3. **Error Handling**:
   - If `gh` returns exit code 1, check stderr.
   - Common errors: "GraphQL: Resource not accessible by integration" (Permissions/Token issue).

### 2.3 Critical Rules

- **JSON Only**: ALWAYS use `--json <fields>` when retrieving information.
- **No Interactive Mode**: Avoid commands that prompt for input. Use flags (e.g., `--yes`, `--public`, `--fill`) or pass inputs explicitly.
- **Token Scope**: If a permission error occurs, warn the user they might need to refresh their token (`gh auth refresh -s <scope>`).
</execution>

---

## PHASE 3: Verification

<verification>
**Verify the work before finishing.**

```bash
# Example: Verify PR creation
gh pr view <pr-number> --json state,url

# Example: Verify Issue closure
gh issue view <issue-number> --json state
```

**Final Report:**
Output a summary of the action, including relevant URLs (PR link, Issue link, Run link).
</verification>

---

## Anti-Patterns (AUTOMATIC FAILURE)

<anti_patterns>
1. **Parsing Text Output**: Attempting to regex scrape `gh pr list` default output. **ALWAYS USE --json**.
2. **Interactive Prompts**: Running `gh pr create` without flags, causing the process to hang waiting for user input.
3. **Blind Execution**: Creating a PR without first pushing the branch (unless using `--head`).
4. **Ignoring Auth**: Running commands assuming auth exists. Always check `gh auth status` first (in Phase 0).
5. **Over-fetching**: Requesting all JSON fields when only `url` is needed. Be specific with `--json`.
</anti_patterns>
