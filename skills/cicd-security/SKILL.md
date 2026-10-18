---
name: cicd-security
description: CI/CD security hardening for supply chain, secrets, runners, and artifacts. Triggers on "CI/CD security", "pipeline hardening", "supply chain security", "secure CI", "runner isolation".
license: MIT
---

# CI/CD Security Agent

DevSecOps-focused agent for securing CI/CD pipelines, with emphasis on supply chain protections, secrets handling, runner isolation, and artifact integrity.

---

## PHASE 0: Context Gathering (MANDATORY)

<context_gathering>
**Execute these commands IN PARALLEL to establish ground truth:**

```bash
git status
ls
```

**Capture these data points:**
1. CI/CD system in use (e.g., GitHub Actions, GitLab CI, Jenkins)
2. Artifact storage and signing approach (if any)
3. Runner model (hosted vs. self-hosted) and isolation controls
</context_gathering>

---

## PHASE 1: Analysis & Strategy (BLOCKING)

<analysis>
**Analyze the context and determine the mode/strategy.**

### 1.1 Decision Logic

| Condition | Mode/Strategy |
|-----------|---------------|
| No secrets management or plaintext secrets found | Secrets hardening first |
| Self-hosted runners without isolation | Runner isolation first |
| No artifact signing/verification | Supply chain integrity first |
| Mixed issues | Triage by highest-impact risk |

### 1.2 MANDATORY OUTPUT

**You MUST output this block before proceeding. NO EXCEPTIONS.**

```
ANALYSIS RESULT
===============
Detected Context: [...]
Selected Strategy: [...]
Plan:
  1. Step 1
  2. Step 2
```
</analysis>

---

## PHASE 2: Execution (Atomic & Safe)

<execution>
### 2.1 Step-by-Step Instructions

1. **Threat model the pipeline**:
   - Identify trust boundaries (source, build, test, deploy, artifact store).
   - Identify credentials used at each stage.

2. **Apply controls by priority**:
   - Enforce least privilege for CI identities.
   - Protect secrets with managed secret stores and short-lived tokens.
   - Isolate runners (ephemeral, sandboxed, minimal network access).
   - Verify dependencies and artifacts (signing, provenance).

### 2.2 Critical Rules

- Never store secrets in repo, logs, or build artifacts.
- Never grant broad write permissions to CI tokens.
- Always verify artifact integrity before deploy.
</execution>

---

## PHASE 3: Verification

<verification>
**Verify the work before finishing.**

```bash
# Example checks (adapt to CI system)
git status
```

**Final Report:**
Output a summary of actions taken and any next steps for the user.
</verification>

---

<best_practices>
- Enforce least-privilege access and role separation for CI/CD identities and tokens.
- Use managed secrets storage and avoid plaintext secrets in pipeline configs or logs.
- Isolate runners (ephemeral, sandboxed, minimal permissions) to limit lateral movement.
- Verify supply chain integrity with artifact signing and provenance validation.
- Apply security controls at every pipeline stage (source, build, test, deploy).
</best_practices>

<anti_patterns>
1. Storing secrets in repository files, pipeline logs, or build artifacts.
2. Using long-lived, overly privileged CI tokens or shared credentials.
3. Running builds on shared, non-isolated runners with broad network access.
4. Deploying artifacts without signature/provenance verification.
5. Treating pipeline security as an afterthought (no controls per stage).
</anti_patterns>

**Sources:**
- https://cheatsheetseries.owasp.org/cheatsheets/CI_CD_Security_Cheat_Sheet.html
- https://owasp.org/www-project-top-10-ci-cd-security-risks
- https://www.reversinglabs.com/blog/8-cicd-security-best-practices-software-pipeline
- https://www.wiz.io/academy/application-security/ci-cd-security-best-practices
