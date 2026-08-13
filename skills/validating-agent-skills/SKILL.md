---
name: validating-agent-skills
description: Audits an Agent Skills catalog for malformed metadata, duplicate names, broken local references, oversized instructions, unmanaged provenance, generated artifacts, and risky commands. Use when maintaining, reviewing, installing, or pruning a skills directory.
---

# Validating Agent Skills

Run the bundled validator before and after catalog maintenance. It is read-only
and uses only the Python standard library.

## Workflow

1. Resolve the catalog root. For this installation it is `~/.agents/skills`.
2. Run the validator and save machine-readable evidence when useful:

   ```bash
   python3 scripts/validate_catalog.py ~/.agents/skills
   python3 scripts/validate_catalog.py ~/.agents/skills --format json > skill-audit.json
   ```

3. Treat errors as structural defects. Review warnings in context; a warning is
   not automatically a reason to remove a skill.
4. For third-party skills, update or reinstall from the recorded source rather
   than locally patching upstream content.
5. Re-run the validator after changes and compare counts and findings.

## Checks

The validator reports:

- invalid or missing frontmatter names and descriptions;
- directory/name mismatches and duplicate skill names;
- `SKILL.md` files over the progressive-disclosure line budget;
- missing relative Markdown links;
- nested repositories, dependency trees, archives, bytecode, and host metadata;
- potentially risky shell patterns that require human review;
- MCP server declarations without an `includeTools` filter;
- whether each direct skill is installer-managed, system-managed, nested, or local.

## Boundaries

- Do not delete, rename, update, or install anything during validation.
- Do not classify a skill as unused without real activation telemetry.
- Do not treat all broad descriptions as defects; routers are intentionally broad
  when they clearly delegate to specialist skills.
- Do not modify installer-managed skills directly. Use their installer or source
  repository so provenance remains accurate.
