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
