# Skills

Complete, attested global skill inventory for Samantha's Macs.

The repository contains 86 vendored local/customized skills under `skills/` and a pinned manifest for 27 upstream-installed skills. Together they reproduce all 113 canonical shared skills. Codex-managed `.system` skills and the empty historical `jenkins-workflows 2` duplicate are intentionally excluded.

## Use

Normal setup and updates run through [`thesammykins/new-mac`](https://github.com/thesammykins/new-mac):

```bash
cd ~/Development/new-mac
./setup.sh
```

Direct maintenance remains available:

```bash
mise run check
mise run install -- --dry-run
mise run verify
```

`scripts/install-skills.py` installs every vendored skill in one local `npx skills@1.5.16` operation, then installs upstream skills grouped by pinned repository commit. Installation is additive and never prunes existing directories.

## Ownership

- `skills/<name>/`: locally maintained, customized, or unresolved vendored content.
- `skills.toml`: pinned upstream sources only.
- `inventory.toml`: complete desired-state catalog, hashes, categories, provenance, and license state.
- `PROVENANCE.md`: policy and disclosure for unresolved imports.
- `THIRD_PARTY_NOTICES.md`: known third-party notices for customized content.

When an unresolved vendored skill is proven byte-identical to a redistributable upstream source, replace its vendored directory with a pinned manifest entry in the same commit.
