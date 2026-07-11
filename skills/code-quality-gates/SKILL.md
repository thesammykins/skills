---
name: code-quality-gates
description: Quality gates, code review standards, static analysis policy, and merge criteria enforcement.
license: MIT
---

# Code Quality Gates Agent

Ensures rigorous quality gates via structured reviews, static analysis policy, and merge criteria.

---

## PHASE 0: Context Gathering (MANDATORY)

<context_gathering>
**Execute these commands IN PARALLEL to establish ground truth:**

```bash
git status
git diff
git log -5 --oneline
```

**Capture these data points:**
1. Current branch status and uncommitted changes
2. Scope and size of changes (diff size)
3. Recent commit context and cadence
</context_gathering>

---

## PHASE 1: Analysis & Strategy (BLOCKING)

<analysis>
**Analyze the context and determine the mode/strategy.**

### 1.1 Decision Logic

| Condition | Mode/Strategy |
|-----------|---------------|
| Large or risky change set | Deep review + stricter gate thresholds |
| Small, isolated change | Standard review + baseline gates |
| Missing tests or low coverage | Block merge until tests added |

### 1.2 MANDATORY OUTPUT

**You MUST output this block before proceeding. NO EXCEPTIONS.**

```
ANALYSIS RESULT
===============
Detected Context: [...]
Selected Strategy: [...]
Plan:
  1. Confirm review scope and risk level
  2. Apply quality gate checklist
  3. Enforce static analysis policy
  4. Verify tests and merge criteria
```
</analysis>

---

## PHASE 2: Execution (Atomic & Safe)

<execution>
### 2.1 Step-by-Step Instructions

1. **Review Scope & Risk**:
   - Identify impacted modules and interfaces.
   - Confirm reviewers have domain context.

2. **Apply Review Checklist**:
   - Read every changed line.
   - Verify correctness, tests, and maintainability.
   - Check for readability and design consistency.

3. **Static Analysis Policy**:
   - Require clean static analysis (no new critical issues).
   - Triage findings and block merge on high severity.

4. **Merge Criteria**:
   - Tests must pass.
   - Review approvals complete.
   - Quality gate thresholds met.

### 2.2 Critical Rules

- Never merge without passing tests and required approvals.
- Never waive high-severity static analysis issues without documented exception.
- Never approve without understanding the change.
</execution>

---

## PHASE 3: Verification

<verification>
**Verify the work before finishing.**

```bash
git status
```

**Final Report:**
Summarize checks performed, exceptions (if any), and next steps.
</verification>

---

<best_practices>
- Read every changed line and validate correctness and tests (Google eng-practices).
- Keep reviews timely with defined expectations/SLAs (Repo Racers process guidance).
- Use automated checks (static analysis/linters) so humans focus on logic and design (Repo Racers reviewer guidance).
- Enforce explicit merge criteria: tests pass, reviews complete, quality gate thresholds met (SonarQube quality gates).
</best_practices>

<anti_patterns>
1. **Rubber-stamp reviews**: Approving without understanding changes undermines code health (Google eng-practices).
2. **Ignoring static analysis findings**: Allowing critical issues to merge defeats quality gates (SonarQube quality gates).
3. **Slow or absent reviews**: Stale PRs increase merge risk and bottleneck delivery (Repo Racers process guidance).
</anti_patterns>

Sources:
- https://google.github.io/eng-practices/review/reviewer/standard.html
- https://reporacers.com/playbook/code_reviews/process_guidance/process_guidance
- https://reporacers.com/playbook/code_reviews/process_guidance/reviewer_guidance
- https://docs.sonarsource.com/sonarqube-server/quality-standards-administration/managing-quality-gates/introduction-to-quality-gates
