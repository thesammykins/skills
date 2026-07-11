---
name: anti-ai-slop
description: "Reviews and removes unsupported, non-idiomatic code and UI/design changes introduced on a branch. Use when implementing or reviewing a feature or fix before handoff."
---

# Anti-AI slop

## Rule

Judge the change, not its presumed author. Slop is task-added work with no evidence in the request, a verified constraint, or an established local/native pattern.

Keep the smallest correct change. Never trade correctness, security, accessibility, data-loss protection, or an explicit requirement for brevity.

## Work from evidence

- Read `AGENTS.md`, the task/spec, relevant source/tests/UI, and callers; search for existing helpers, components, tokens, and patterns.
- Prefer: no change, reuse, standard library/native features, installed dependencies, then minimum new code.
- Every file, dependency, abstraction, state, and UI element must serve requested behavior, a real invariant/trust boundary, a local/native pattern, or the smallest useful check/required diagnostic. If unclear, inspect siblings and run or render it; plausibility is not evidence.

## Review scope

Resolve the PR/task base, falling back to `main` then `master` with the assumption stated. Inspect the full working tree from its merge base plus untracked files:

```bash
base_ref=main # replace with the resolved base ref
base=$(git merge-base HEAD "$base_ref")
git diff "$base"
git status --short
```

Use narrower diffs only to isolate layers. Without a Git baseline, require an explicit before/after scope. Read full files and callers for context, but edit only the task scope unless correctness requires more.

## Code signals

Remove or simplify task-introduced:

- narrative comments/docstrings/logs or unactionable TODOs;
- speculative layers, config/compatibility paths, or one-use helpers;
- duplicate/unused/dead code, fake implementations, or placeholder data;
- proven-redundant internal casts, assertions, checks, retries, or catch-and-rethrow blocks;
- unnecessary, nonexistent, or repository-incompatible APIs and packages;
- local style drift or tests that add no behavioral protection;
- invisible characters or identifier homoglyphs in code/config, while preserving intentional localized content.

Verify required dependencies against authoritative docs and the manifest/lockfile, then run normal license/security checks. Preserve boundary validation, authorization, escaping, cleanup, useful error handling, and data-loss protection. Never weaken a failing test to make the branch green.

## Design signals

Render changed UI and compare adjacent surfaces, components/tokens, platform conventions, and brand references. Remove unsupported invented content/controls, fake data, duplicate components, flattened hierarchy, incomplete interactions, and generic decorative defaults.

This is not a trope blacklist. Preserve product-supported brand/cultural distinctiveness plus semantics, labels, keyboard/focus behavior, contrast, target sizes, text reflow, reduced motion, and required UI states.

## Finish

Simplify the narrowest shared path, remove only task-introduced fallout, and run the smallest relevant format, lint, build, test, static/security, and UI/accessibility checks. Re-read the complete diff; every line must map to the request, a verified constraint, or a local convention.

Report only a 1-3 sentence summary of cleanup, checks, and anything unverified. No bullets or emojis.
