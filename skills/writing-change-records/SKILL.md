---
name: writing-change-records
description: Drafts evidence-grounded Git commit messages and PR titles/descriptions, scaling context to change risk. Use when composing or revising commit or PR text.
---

# Writing Change Records

Write the engineering record that the diff cannot preserve by itself.

This skill owns commit and pull-request wording. It consumes inspected change
context and existing evidence; it does not design or run verification, check an
implementation against a spec, write review comments, commit changes, or manage
remote PRs.

## Prepare from the final change

Before writing:

1. Read repository instructions, contribution guidance, and any PR template.
2. Inspect the complete relevant diff. For a PR, also inspect every commit and
   the base-to-head result. Read surrounding code when the diff does not reveal
   the behavioural contract.
3. Check recent history for local subject prefixes, tense, line length,
   trailers, and merge conventions. Repository convention beats generic Git
   style.
4. Recover the linked issue, incident, specification, or decision context when
   available. Do not require the reader to open those links to understand the
   record.
5. Gather validation already performed and its result. This skill communicates
   evidence; it does not invent evidence or replace a verification workflow.

Reconstruct these facts:

- What was wrong, missing, or unnecessarily difficult before this change?
- What outcome does the change establish?
- Which constraint or decision would not be recoverable from the diff?
- What observed evidence supports the outcome?
- What risk, compatibility, migration, or recovery fact affects acceptance?

Do not infer motivation from filenames, changed symbols, or a ticket title when
better evidence exists. Mark a material unknown outside the proposed message
instead of filling it with plausible prose.

## Scale the record

Classify by review burden and consequence, never line count alone:

- **Quick:** established intent, narrow correction, low blast radius, no
  meaningful design decision. State what is being corrected and the relevant
  mechanism or outcome without ceremonial sections.
- **Standard:** bounded feature, refactor, or bug fix that needs some context or
  contains a non-obvious local decision.
- **Major/high-risk:** a material invariant, public contract, stored-data
  format, trust boundary, concurrency rule, deployment order, rollback path,
  or broad/hard-to-recover behaviour changes.

Risk overrides size. A six-line authorization change may need major/high-risk
treatment; a generated thousand-line refresh may need only its source,
purpose, and determinism check.

Draft/exploratory is a separate overlay. State what is incomplete and what
feedback is useful now.

Read [classifying changes](references/classifying-changes.md) when the class is
unclear or risk modifiers are present.

## Preserve reasoning, not activity

The record should let a future engineer recover the problem, outcome, and
material reasoning without replaying the author's work session.

Prefer:

> Entries expiring exactly at the current timestamp remained valid for one
> refresh cycle. Treat equality as expired so cache behaviour matches the
> documented boundary.

Avoid:

> Updated the comparison, added tests, and ran `git diff`.

Do not narrate files, commits, tool calls, or agent activity. `git diff` proves
only that a diff was inspected. A test command without the behaviour it checked
is reproducibility metadata, not an explanation of correctness.

Name evidence as **claim → observation**:

> The equality boundary is covered by a regression test; the cache suite passes
> with `expiresAt == now` treated as stale (`go test ./internal/cache/...`).

Include an exact command when it helps reproduction, but never substitute a
command list for what the checks established. Never claim tests, CI, manual
checks, screenshots, benchmarks, or rollout results that were not observed.

## Write the commit message

Read [writing commit messages](references/writing-commit-messages.md) for
target-specific guidance and examples.

- Keep each commit to one logical change. If the message needs to reconcile
  unrelated purposes, the commit likely needs splitting.
- Make the subject stand alone in history and describe the applied outcome.
- Use the repository's conventional prefix and grammar. Otherwise prefer a
  concise imperative subject, no trailing period, then a blank line before any
  body.
- Omit the body when the subject fully explains an obvious, low-risk change.
- Use a body to explain the prior problem, why this outcome or approach is
  appropriate, and non-obvious consequences or exclusions.
- Include evidence, issue references, and trailers only when useful or required
  by repository convention.

A commit message explains that commit's logical step. Do not paste the PR body
into every commit.

## Write the pull request

Read [writing pull requests](references/writing-pull-requests.md) for
target-specific guidance and examples.

- Make the title describe the whole behavioural or engineering outcome, not
  the branch name or work category.
- Explain the problem and resulting behaviour before implementation detail.
- Add approach or trade-off context only when a reviewer must judge it.
- For major/high-risk work, preserve the engineering rationale: problem, core
  decisions, constraints and invariants, material trade-offs, compatibility,
  rollout/rollback, observed evidence, and review focus.
- Adapt to the repository template. Keep required fields, but do not create
  empty headings or ceremonial `N/A` sections where omission is allowed.
- Describe the base-to-head outcome. Do not turn the body into a commit log or
  file inventory.
- Update the description after material review changes so it matches the final
  code and decisions.

## Keep it proportional

Use the shortest record that preserves the reasoning needed for this change.

- A typo or obvious boundary correction may need only a precise commit subject
  or a two-sentence PR description.
- A standard change usually needs problem, outcome, any non-obvious decision,
  and meaningful evidence.
- A major/high-risk change needs enough context to evaluate system
  consequences, but every section must still earn its place.

More prose cannot repair incoherent scope. If a change combines independently
reviewable decisions, surface the scope problem instead of hiding it under a
long summary.

## Output

Return ready-to-use text in the repository's format. Do not put the internal
classification or drafting rationale into the message. Put unresolved facts,
assumptions, or suggested splits in a separate `Notes` section after the record;
omit it when there are none.

When asked only to draft or revise text, do not commit, push, or create/update a
PR. Those are separate actions.

## Final filter

Before returning the message, confirm:

- The title or subject distinguishes this change in history.
- A future engineer can recover what problem existed and why this outcome was
  chosen.
- The prose adds information that is not obvious from the diff.
- Detail is proportional to risk and review burden.
- Material decisions, trade-offs, and operational consequences are present;
  hypothetical ones are absent.
- Validation says what was established, not merely which commands ran.
- Every factual claim is supported by inspected context.
- The text describes the final change rather than the work session.

For the historical and empirical basis behind these rules, read
[research basis](references/research-basis.md).
