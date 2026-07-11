---
name: deliver-baseline
description: 'Always-on delivery baseline for SWE/DevOps work (code review, quality gates, testing, CI/CD security, release discipline). Triggers: "baseline", "delivery baseline", "quality standard", "engineering standard", "devops standard".'
license: MIT
---

# Delivery Baseline Agent

Sets the 2026 engineering-quality floor for software delivery by enforcing code review standards, quality gates, testing strategy, CI/CD security, and release discipline.

---

## PHASE 0: Context Gathering (MANDATORY)

<context_gathering>
**Execute these commands IN PARALLEL to establish ground truth:**

```bash
ls -la
rg -n --glob "**/*" "(README|CONTRIBUTING|CODEOWNERS|SECURITY|CHANGELOG)" || true
rg -n --glob ".github/workflows/*.yml" "(permissions:|secrets:|uses:|runs-on:)" || true
rg -n --glob "{**/sonar*.yml,**/sonar-project.properties,**/sonar-project.properties}" "." || true
rg -n --glob "{.gitlab-ci.yml,**/Jenkinsfile,azure-pipelines.yml,.circleci/config.yml,**/buildkite/*.yml}" "." || true
```

**Capture these data points:**
1. Existing engineering standards (README/CONTRIBUTING/CODEOWNERS)
2. CI/CD platform(s) and workflow locations
3. Quality gate tooling signals (e.g., SonarQube)
4. Release/rollback documentation or checklists
</context_gathering>

---

## PHASE 1: Analysis & Strategy (BLOCKING)

<analysis>
**Analyze the context and determine the mode/strategy.**

### 1.1 Decision Logic

| Condition | Mode/Strategy |
|-----------|---------------|
| Existing standards present | Align to existing policies + fill gaps |
| No standards found | Establish minimum delivery baseline |
| CI/CD detected | Enforce pipeline security + quality gates |
| Release workflow present | Enforce release checklist + rollback plan |

### 1.2 MANDATORY OUTPUT

**You MUST output this block before proceeding. NO EXCEPTIONS.**

```
ANALYSIS RESULT
===============
Detected Context: [...]
Selected Strategy: [...]
Plan:
  1. Confirm baseline scope and existing policies
  2. Apply quality gate + review standards
  3. Apply test/CI security checks
  4. Confirm release/rollback discipline
```
</analysis>

---

## PHASE 2: Execution (Atomic & Safe)

<execution>
### 2.1 Step-by-Step Instructions

1. **Baseline Alignment**
   - Use existing CONTRIBUTING/CODEOWNERS/SECURITY docs if present.
   - If absent, define a minimal baseline: review, tests, static analysis, release checks.

2. **Code Review Standards**
   - Require peer review for all non-trivial changes.
   - Review for correctness, readability, maintainability, and risk.

3. **Quality Gates**
   - Enforce automated checks (build + tests + static analysis) before merge.
   - Require quality gate pass for new/changed code.

4. **Testing Strategy**
   - Require tests for new behavior and bug fixes.
   - Prefer fast unit tests + targeted integration/E2E where risk is higher.

5. **CI/CD Security**
   - Lock down pipeline permissions and secrets.
   - Pin dependencies and validate artifact integrity when releasing.

6. **Release Discipline**
   - Require a rollout plan, monitoring, and a rollback plan for releases.

### 2.2 Critical Rules

- Never bypass required tests or quality gates without explicit approval.
- Never allow unreviewed pipeline config changes.
- Always require a rollback plan for production releases.
</execution>

---

## PHASE 3: Verification

<verification>
**Verify the work before finishing.**

```bash
rg -n --glob ".github/workflows/*.yml" "(permissions:|secrets:|uses:|runs-on:)" || true
rg -n --glob "**/*" "(CODEOWNERS|CONTRIBUTING|SECURITY|CHANGELOG)" || true
```

**Final Report:**
Summarize baseline applied, checks enforced, and any required follow-up.
</verification>

---

<best_practices>
- Use peer code review to protect long-term code health and balance developer velocity with quality. [Sources]
- Enforce automated quality gates (tests + static analysis) in CI/CD so only high-quality code progresses. [Sources]
- Integrate CI/CD security controls to reduce pipeline and supply-chain risk. [Sources]
- Generate and verify provenance for released artifacts to improve integrity. [Sources]
- Maintain a release checklist with explicit rollback planning. [Sources]

Sources:
- https://google.github.io/eng-practices/review/
- https://google.github.io/eng-practices/review/reviewer/standard.html
- https://docs.sonarsource.com/sonarqube-server/quality-standards-administration/managing-quality-gates/introduction-to-quality-gates
- https://cheatsheetseries.owasp.org/cheatsheets/CI_CD_Security_Cheat_Sheet.html
- https://slsa.dev/spec/v1.0/requirements
- https://launchdarkly.com/blog/release-management-checklist/
</best_practices>

<anti_patterns>
1. **Bypassing tests or gates to merge faster**: short-term speed creates long-term risk and regressions. [Sources]
2. **Unreviewed pipeline changes**: undermines CI/CD integrity and increases supply-chain risk. [Sources]
3. **Releases without rollback plans**: increases outage duration and customer impact. [Sources]

Sources:
- https://google.github.io/eng-practices/review/reviewer/standard.html
- https://cheatsheetseries.owasp.org/cheatsheets/CI_CD_Security_Cheat_Sheet.html
- https://launchdarkly.com/blog/release-management-checklist/
</anti_patterns>
