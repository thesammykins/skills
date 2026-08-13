# Skills

Curated, shareable skills for Samantha's Macs.

The repository vendors only `happy-path-use-case-design`, which is maintained locally from the Hermes source. The `.system` directory is managed by Codex and is intentionally excluded. Other skills installed under `~/.agents/skills` by `npx skills` are intentionally not copied here; see [`NPIX_INSTALL_NOTES.md`](NPIX_INSTALL_NOTES.md) for the install association.

## Use

Install the vendored skill with the repository's setup tooling or copy `skills/happy-path-use-case-design` into `~/.agents/skills/`. Install the remaining listed skills with `npx skills@1.5.16`.

## Ownership

- `skills/<name>/`: locally maintained, vendored content.
- `NPIX_INSTALL_NOTES.md`: npx-managed skills intentionally omitted from this repository.
- `inventory.toml`: desired-state catalog and provenance.
- `PROVENANCE.md`: provenance policy.
