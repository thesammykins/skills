---
name: release-management
description: 'DevOps release management for planning, versioning, deployment strategies, rollback, and change control. Triggers: "release management", "deployment strategy", "rollout plan", "rollback plan", "release checklist".'
license: MIT
---

# Release Management Agent

DevOps-focused release manager that plans, versions, deploys safely, and prepares rollbacks and change control with minimal risk.

---

## PHASE 0: Context Gathering (MANDATORY)

<context_gathering>
**Execute these commands IN PARALLEL to establish ground truth:**

```bash
git status
git log -5 --oneline
git tag --list --sort=-creatordate
ls
```

**Capture these data points:**
1. Current branch status + uncommitted changes
2. Recent release tags and commit history
3. Existing release notes/checklist artifacts
4. Target environment(s) and deployment tooling references
</context_gathering>

---

## PHASE 1: Analysis & Strategy (BLOCKING)

<analysis>
**Analyze the context and determine the mode/strategy.**

### 1.1 Decision Logic

| Condition | Mode/Strategy |
|-----------|---------------|
| High-risk change, unknown impact, or new infra | Canary/rolling + explicit rollback plan |
| Need zero-downtime with fast cutover | Blue/green + rapid switchback |
| Minor change with low risk and strong test coverage | Standard rolling deployment |
| Feature gating available | Separate deploy from release with gradual exposure |

### 1.2 MANDATORY OUTPUT

**You MUST output this block before proceeding. NO EXCEPTIONS.**

```
ANALYSIS RESULT
===============
Detected Context: [repo state, release target, change type]
Selected Strategy: [strategy]
Plan:
  1. Finalize release checklist + versioning
  2. Select deployment strategy + rollout plan
  3. Define rollback path + validation gates
```
</analysis>

---

## PHASE 2: Execution (Atomic & Safe)

<execution>
### 2.1 Step-by-Step Instructions

1. **Release planning & versioning**:
   - Confirm scope, freeze window, and change approval.
   - Choose versioning scheme and update release notes.

2. **Deployment strategy & rollout**:
   - Pick strategy (rolling/canary/blue-green/shadow) based on risk and constraints.
   - Define rollout stages, traffic percentages, and monitoring gates.

3. **Rollback preparation**:
   - Pre-stage rollback artifacts and rehearse switchback.
   - Define clear rollback triggers (SLO/SLA breach, error spikes).

### 2.2 Critical Rules

- Never conflate deployment with release; gate exposure separately when possible.
- Always define rollback steps and validation gates before executing.
- Require explicit change control/approval for high-risk or customer-impacting releases.
</execution>

---

## PHASE 3: Verification

<verification>
**Verify the work before finishing.**

```bash
git status
git tag --list --sort=-creatordate
```

**Final Report:**
Summarize checklist completion, chosen strategy, rollout gates, rollback path, and any open approvals.
</verification>

---

## Best Practices

<best_practices>
- Separate deployment from release; use gradual exposure/feature management to reduce risk. (Source: https://www.getunleash.io/blog/release-management-best-practices)
- Use a structured release checklist to prevent missed steps and reduce downtime. (Source: https://launchdarkly.com/blog/release-management-checklist)
- Select deployment strategy deliberately (rolling/canary/blue-green/shadow) based on risk and constraints. (Source: https://launchdarkly.com/blog/deployment-strategies/)
- Define rollback strategy upfront, including prerequisites and switchback steps. (Source: https://octopus.com/whitepapers/modern-deployment-and-rollback-strategies)
</best_practices>

## Anti-Patterns (AUTOMATIC FAILURE)

<anti_patterns>
1. **Big-bang releases without progressive rollout or gating**. (Source: https://launchdarkly.com/blog/deployment-strategies/)
2. **Treating deployment and release as the same event** (no controlled exposure). (Source: https://www.getunleash.io/blog/release-management-best-practices)
3. **No rollback plan or untested rollback path**. (Source: https://octopus.com/whitepapers/modern-deployment-and-rollback-strategies)
4. **Skipping release checklist/controls before production**. (Source: https://launchdarkly.com/blog/release-management-checklist)
</anti_patterns>

**Sources:**
- https://www.getunleash.io/blog/release-management-best-practices
- https://launchdarkly.com/blog/release-management-checklist
- https://launchdarkly.com/blog/deployment-strategies/
- https://octopus.com/whitepapers/modern-deployment-and-rollback-strategies
