---
name: project-skill-manager
description: Keeps language, framework, platform, and SDK skills project-local. Use when a repository task needs stack-specific guidance that is not already installed in the project's `.agents/skills`.
---

# Project Skill Manager

Keep the user-global skill catalog general. Add specialist skills only to the
repository that needs them.

1. Resolve the project root with `git rev-parse --show-toplevel`; use the current
   directory only when it is intentionally the project root.
2. Read the repository guidance and inspect its manifests and lockfiles. Add a
   specialist skill only when it will materially improve the current task.
3. Reuse a matching skill in `<project>/.agents/skills` before installing one.
4. Prefer an exact match from
   `~/.agents/project-skills-library`. From the project root, run:

   ```bash
   npx skills add ~/.agents/project-skills-library/<skill> --agent codex --yes
   ```

5. If the local library has no match, use `npx skills find <language-or-sdk>`,
   review the source, then install the chosen skill with `npx skills add` from
   the project root.
6. Never pass `--global` or `-g`. Never install an entire source when one skill
   is enough.
7. Verify `<project>/.agents/skills/<skill>/SKILL.md` exists and report the
   project file change. Do not commit it unless the user asked for a commit.

If there is no real project root, use the specialist guidance without making it
global, or ask where it should live when persistence matters.
