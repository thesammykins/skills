---
name: write-feature-docs
description: Drafts accurate user documentation from a feature spec and verified codebase behavior. Use when asked to document a feature, turn a spec into docs, or prepare a documentation pull request.
---

# Write Feature Documentation

Create a complete, user-facing documentation draft grounded in the feature spec and verified product behavior. The draft explains what users can do and how; it does not expose internal implementation details.

## Inputs

- Logical feature slug and documentation repository or destination.
- `specs/<feature-slug>/PRODUCT.md` and optional `TECH.md`, if available.
- The implementation repository and revision to verify.
- Target audience, documentation format, style guide, navigation conventions, and screenshots if relevant.
- Whether the user wants a draft only or explicitly authorizes creating a branch or pull request.

## Workflow

1. Read repository instructions, the relevant spec files, and nearby documentation before drafting.
2. Treat `PRODUCT.md` as the primary source for user-facing behavior. Use `TECH.md` only to identify behavior to verify; keep internal architecture, private APIs, data models, feature-flag names, credentials, and operational details out of public documentation unless explicitly approved.
3. Verify material claims against the implementation or a runnable product. When evidence is incomplete, mark the claim for owner confirmation rather than inventing behavior.
4. Present a concise outline: intended audience, prerequisite/setup, primary flow, important states and limitations, examples, and proposed navigation location. Wait for confirmation when the product behavior or public framing is ambiguous.
5. Draft the documentation in the repository's existing format and style. Use direct, task-oriented language and realistic examples. Add screenshots only when they demonstrate a meaningful UI step, and inspect them before inclusion.
6. Run the documentation repository's validation and link checks. Review the rendered output when the repository provides a preview path.
7. If explicitly authorized, create a draft branch and pull request. Otherwise save the draft locally and report its path.

## Documentation contract

- Use the feature's logical slug in file names, metadata, and cross-references. Existing tickets or issues may be linked as context but do not replace the slug.
- State prerequisites, permissions, supported environments, and limitations that materially affect a user.
- Keep examples safe: no production secrets, customer data, private URLs, or destructive commands.
- Do not claim release availability, compatibility, or behavior that has not been confirmed for the target revision.
- Keep the doc aligned with the shipped behavior; update it when the checked-in product spec changes materially.

## Output

Report the source revision and specs consulted, drafted files, verified versus unverified claims, checks run, preview evidence, and any approval still required before publication.
