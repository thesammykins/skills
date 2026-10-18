# Provenance

The `skills/` tree began as a snapshot of non-system directories from a local
`~/.agents/skills` installation. The checked-in tree is now the source of truth
for packaging and installation, but that does not establish authorship or an
upstream source for each skill.

`inventory.toml` records the current provenance and license status for packaged
skills. `external-skills.toml` records verified upstream repositories and the
revisions reviewed before those skills were removed from the vendored catalog.
The external installer previews its commands by default and leaves network
installation to an explicit `--apply` invocation.

`.system` is managed by Codex and is intentionally excluded. Project-specific
and harness-managed skills outside this repository are not installed or pruned.

## Unverified imports

Eleven skills marked `provenance = "unverified-import"` in `inventory.toml`
(alt-text, cicd-security, copywriting, deslop, free-disk-space, open-pencil,
pdf, project-skill-manager, screenshot, security-threat-model, transcribe) were
copied from the installed set on 2026-10-19 so every Mac gets them. Several
came from third-party collections; their upstream source and license still
need confirming. Where a `LICENSE.txt` ships with a skill, it is kept as-is.

Skills listed under `[[ignored]]` in `skills.toml` are installed on a Mac but
deliberately not published here: tool-managed ones, and personal ones kept in a private repository.
