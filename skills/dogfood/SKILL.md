---
name: dogfood
description: Explores a web application to find reproducible functional, visual, accessibility, console, UX, and content defects. Use for exploratory QA or a structured dogfood pass.
version: 1.1.0
author: Samantha Myers
license: MIT
platforms: [linux, macos, windows]
metadata:
  tags: [qa, testing, browser, web, dogfood]
---

# Dogfood: Exploratory Web Application QA

Explore a web application as a user would, capture reproducible evidence, and return a structured defect report. This is exploratory QA, not a claim that the application is defect-free.

Load `references/issue-taxonomy.md` before classifying findings and use `templates/dogfood-report-template.md` for the report. When running in Amp, load `harnesses/amp.md` to select browser and media-inspection capabilities for the current executor.

## Inputs

1. **Target URL** — the entry point for testing.
2. **Scope** — targeted flows or “full site.”
3. **Test access and boundaries** — accounts, seeded data, actions that are prohibited, and environments that are safe to mutate.
4. **Output directory** (optional) — default `./dogfood-output`.

## Workflow

### 1. Plan

1. Create `{output_dir}/screenshots/` and reserve `{output_dir}/report.md`.
2. Read application and repository guidance. Identify the user roles, critical flows, unsafe actions, and the expected behavior for the requested scope.
3. Build a compact coverage plan: entry points, navigation, primary flows, forms, empty/error states, and relevant responsive or keyboard paths.

### 2. Explore

Use the host's browser automation capability when available. For each planned page or flow:

1. Navigate and inspect the rendered page and accessibility/DOM representation.
2. Record browser-console errors and failed requests after navigation and meaningful interactions.
3. Exercise links, buttons, forms, keyboard navigation, scrolling, valid/invalid input, empty submissions, and relevant edge cases.
4. Compare observed behavior with the stated expectation. Do not treat an unfamiliar implementation as a bug without an expectation or reproducible user harm.
5. Inspect representative visual states, including the changed/responsive states implicated by the scope.

If no browser capability is available, report the limitation and perform only the static or runnable checks that the environment supports; do not invent interaction evidence.

### 3. Collect evidence

For every finding, retain:

- URL and account/state used;
- minimal reproduction steps;
- expected and actual behavior;
- console/network evidence when relevant;
- an inspected screenshot or recording path when it materially demonstrates the defect;
- conditions that affect reproduction, such as viewport, browser, feature state, or timing.

Do not capture or report secrets, private customer data, or credentials. Use sanitized accounts and data where possible.

### 4. Categorize

De-duplicate manifestations of the same root defect. Classify severity and category using `references/issue-taxonomy.md`; sort findings by severity. Severity reflects user impact and reproducibility, not the amount of evidence collected.

### 5. Report

Write `{output_dir}/report.md` from `templates/dogfood-report-template.md`. Include the tested scope, environment, coverage, limitations, blockers, and every confirmed finding. A zero-finding report must say what was tested and what was not; it is not an “all clear” claim.

## Safety rules

- Do not test destructive, financial, production-data, or permission-changing flows without explicit authorization and a safe test account.
- Stop if the target redirects to an unapproved production environment or exposes sensitive data.
- Report security-sensitive observations discreetly; do not exploit a suspected vulnerability beyond the minimum needed to establish impact.
