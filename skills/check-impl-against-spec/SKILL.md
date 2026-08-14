---
name: check-impl-against-spec
description: Compare an implementation against its approved product and technical specs, identifying material drift. Use during code review or before finishing spec-driven work.
---

# Check implementation against spec

Use this skill when approved product or technical specs can be located from the current worktree, a supplied path, or linked decision context. If the specification is unavailable, state that comparison is blocked rather than inventing commitments.

## Goal

Determine whether the implementation materially matches the approved spec. This supplements normal code review; it does not replace defect, security, or test review.

## Inputs

- Product and technical specs, normally `specs/<feature-slug>/PRODUCT.md` and optional `TECH.md`, or explicitly supplied equivalent documents.
- The implementation diff and checked-out files.
- Optional pull-request description, review artifacts, and linked decision context.

## Process

1. Read the available spec context and extract the concrete commitments it makes:
   - required behaviors (from the product spec)
   - required files or subsystems to change (from the tech spec)
   - stated constraints
   - required follow-up steps, validation, or migrations
2. Compare those commitments against the actual implementation diff and checked-out files.
3. Treat small implementation-level adjustments as acceptable when they preserve the spec's intent. Do not flag harmless differences in naming, structure, or low-level technique.
4. Flag a mismatch only when it is material, such as:
   - required behavior in the product spec is missing
   - the implementation contradicts a spec decision
   - the change introduces significant unplanned scope
   - a required validation, migration, or compatibility step from the tech spec is absent

## Outputs

- Use the host review format when one exists. Otherwise return a compact spec-alignment section with each material mismatch, the exact spec commitment, implementation evidence, impact, and recommended correction.
- Put broad spec-drift concerns in the review summary; attach line-level findings only when they map to changed lines.
- Treat material spec drift as an important concern.
- If the implementation matches closely enough, record no finding merely to announce alignment.

## Boundaries

- Do not require literal one-to-one implementation of the spec when the PR achieves the same outcome safely.
- Do not speculate about spec details that are not actually present in the supplied context.
- Do not publish comments, create work items, or alter remote state unless explicitly authorized.

When running in Amp, load `harnesses/amp.md` for current-thread and review-artifact handling.
