---
name: project-skills
description: Detects a repository's languages, platforms, delivery targets, and tooling; recommends the smallest project-local set of Agent Skills from recorded upstream sources; and audits global skill provenance. Use when setting up skills for a project, deciding whether a skill belongs globally or locally, or reviewing ~/.agents/skills without deleting anything.
---

# Project Skills

Keep global skills limited to agent capabilities and cross-project workflows.
Put language, framework, platform, infrastructure, CI provider, and delivery
skills in the projects that need them.

This skill is the policy and detection layer. Agent Plugins provides the
portable package format but intentionally leaves installation, scope,
enablement, dependencies, and trust decisions to clients.

## Project setup workflow

1. Establish the repository root and read its guidance files.
2. Inspect concrete project evidence before recommending anything:
   - language and package manifests;
   - Xcode, Gradle, CI, deployment, and infrastructure configuration;
   - checked-in `.agents/skills`, `skills-lock.json`, and Agent Plugin manifests;
   - the user's requested build and delivery targets.
3. Read `references/project-profiles.json` and select only profiles supported by
   that evidence.
4. Separate required skills from optional workflow skills. A language does not
   imply every platform or delivery capability: Swift does not by itself imply
   App Store Connect, and TypeScript does not imply Cloudflare.
   Each profile records a source root and, at most, one preferred entry skill;
   it does not snapshot the source's full inventory.
5. Present the proposed source repositories, exact skill names, destination,
   and reason for each profile before installing anything.
6. Ask before network-backed installation or writing project files.
7. Install project-locally. Do not add `--global`, and do not remove a global
   copy as part of project setup.
8. Verify the installed `SKILL.md` files, lock/manifest changes, and `git diff`.

## Installation policy

Prefer an upstream Agent Plugin when one exists and the active client supports
it. Otherwise install Agent Skills directly from the recorded root repository.
For repositories supported by the `skills` CLI, the non-global shape is:

```bash
npx --yes skills add <owner/repo> --skill <skill-name> --yes
```

Use `--copy` only when the project intends to check the skill content into
source control. Never invent a repository from a matching public skill name;
verify the root through a lockfile, manifest, exact source match, or upstream
documentation.

Before proposing an installation, verify the skill names currently exposed by
the recorded root. Install only the subset supported by repository evidence or
the requested task, and retain the resulting project lockfile.

Agent Plugins 1.0.0 has no portable plugin dependency or setup-hook mechanism.
Represent related source repositories as one project profile, not as undeclared
runtime dependencies. Client-specific extensions require a separate trust and
portability review.

## Scope decision

Classify a skill by what activates it:

| Activation condition | Default scope |
|---|---|
| The agent is doing normal cross-project work | Global candidate |
| A language, framework, platform, provider, or build tool is present | Project |
| A release channel such as App Store Connect is actually used | Project, opt-in |
| The client supplies it under `.system` | System-managed |
| Its purpose or origin is unclear | Audit; do not move or delete |

Global candidates include review, planning, debugging process, Git workflow,
browser/computer operation, and skill-management capabilities that remain useful
regardless of the repository's implementation stack. A broadly applicable
development topic is not automatically agent-specific.

## Global provenance audit

Run the bundled read-only audit:

```bash
python3 scripts/audit_global_skills.py
python3 scripts/audit_global_skills.py --format json
```

The audit uses, in descending confidence:

1. client-managed `.system` placement;
2. the current `~/.agents/.skill-lock.json`;
3. exact directory matches against recorded local source checkouts;
4. historical `~/.agents*.bak*/.skill-lock.json` records;
5. `unresolved` when none of the above establishes provenance.

Treat `unresolved` as a queue for human audit, not proof that a skill was
hand-authored. Historical name-only matches are candidates until current
content or installer metadata confirms them. Never delete, overwrite, update,
or relocate a skill during an audit. Report source confidence separately from
the recommended scope.

## Maintaining the catalogue

- Add a profile only after confirming its root source and activation evidence.
- Link to upstream roots; do not vendor unchanged third-party skills.
- Record locally modified forks as `derived`, with both local and upstream roots.
- Keep profile recommendations minimal and capability-driven.
- Re-run the audit and tests after catalogue changes.
- Preserve unresolved records until evidence resolves them.
