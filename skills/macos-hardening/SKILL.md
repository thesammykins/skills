---
name: macos-hardening
description: 'macOS administration hardening for baselines, compliance, patching, and configuration management. Triggers on: "macOS hardening", "macOS security baseline", "mSCP", "macOS compliance", "macOS admin".'
license: MIT
---

# macOS Hardening Agent

Specialized agent for macOS security baselines, compliance mapping, patching strategy, and configuration management workflows (MDM-driven).

---

## PHASE 0: Context Gathering (MANDATORY)

<context_gathering>
**Execute these commands IN PARALLEL to establish ground truth:**

```bash
sw_vers
profiles status -type enrollment
profiles list
system_profiler SPHardwareDataType
```

**Capture these data points:**
1. macOS version and build
2. MDM enrollment status
3. Installed configuration profiles
4. Hardware model/architecture
</context_gathering>

---

## PHASE 1: Analysis & Strategy (BLOCKING)

<analysis>
**Analyze the context and determine the mode/strategy.**

### 1.1 Decision Logic

| Condition | Mode/Strategy |
|-----------|---------------|
| MDM enrolled | Use mSCP outputs (baseline + profile) and deploy via MDM |
| Not MDM enrolled | Provide a minimal, manual hardening checklist and recommend MDM onboarding |
| Regulated environment (e.g., NIST 800-53 mapping requested) | Generate mSCP baseline for target framework |
| Patch gap > 30 days | Prioritize patching plan before configuration changes |

### 1.2 MANDATORY OUTPUT

**You MUST output this block before proceeding. NO EXCEPTIONS.**

```
ANALYSIS RESULT
===============
Detected Context: [...]
Selected Strategy: [...]
Plan:
  1. Baseline selection (mSCP or minimal)
  2. Deployment path (MDM/manual)
  3. Validation & reporting
```
</analysis>

---

## PHASE 2: Execution (Atomic & Safe)

<execution>
### 2.1 Step-by-Step Instructions

1. **Baseline Selection**:
   - Choose mSCP baseline aligned to target framework and OS version.
   - Generate baseline guidance/config profiles as needed.

2. **Deployment**:
   - If MDM: import configuration profiles and deploy to test group first.
   - If manual: provide a minimal, auditable checklist with rollback notes.

3. **Patching**:
   - Document current patch level.
   - Execute staged update plan before enforcing stricter controls.

### 2.2 Critical Rules

- Never apply configuration changes fleet-wide without a staged pilot.
- Always validate compliance/health after each change batch.
</execution>

---

## PHASE 3: Verification

<verification>
**Verify the work before finishing.**

```bash
profiles status -type enrollment
profiles list
softwareupdate --list
```

**Final Report:**
Summarize baseline used, deployment method, patch status, and any gaps.
</verification>

---

## Best Practices

<best_practices>
- Use mSCP to generate baselines, guidance, and MDM profiles aligned to compliance frameworks (e.g., NIST 800-53); deploy via existing management tools rather than ad‑hoc scripts.
- Keep guidance current with each macOS release; mSCP is updated per major macOS versions and recognized by Apple.
- Prefer programmatic, repeatable baselines and generate evidence (guidance + compliance scripts) for auditability.
</best_practices>

## Anti-Patterns (AUTOMATIC FAILURE)

<anti_patterns>
1. **Bypassing managed configuration**: Applying one-off local tweaks that cannot be audited or reproduced instead of using mSCP outputs and management tooling.
2. **Ignoring update cadence**: Enforcing hardening controls without ensuring macOS is updated to a supported, current baseline.
3. **Skipping staged rollout**: Pushing sweeping profile changes to all devices without pilot validation.
</anti_patterns>

## Sources
- https://pages.nist.gov/macos_security/welcome/introduction/
- https://pages.nist.gov/macos_security/
- https://csrc.nist.gov/pubs/sp/800/219/r1/final
- https://support.apple.com/guide/certifications/macos-security-compliance-project-apc322685bb2/web
