# Skills Repository

This repository is a personal mirror of the global agent skills installed under `~/.agents/skills`.

## Repository contents

- `skills/` contains one directory for every skill currently present in `~/.agents/skills`, except `.system`.
- The repository currently mirrors 42 non-system skill directories.
- The files under `skills/` are the skill snapshot itself; this repository does not replace or modify the source projects that originally provided those skills.
- `.system` is intentionally excluded because it is managed by Codex and is installation-specific.
- Skills that normally come from `npx skills` remain in the snapshot when they are installed locally. Their names and refresh guidance are listed in `NPIX_INSTALL_NOTES.md`.
- Skills installed only in other locations, such as Hermes-specific directories outside `~/.agents/skills`, are not part of this repository.

`inventory.toml` records the expected skill directories. `PROVENANCE.md` describes the snapshot's ownership boundaries.

## Using the snapshot

To reproduce this installation elsewhere, copy the directories under `skills/` into that account's `~/.agents/skills/` directory. Do not copy `.system`; let the destination tool manage its own system skills. For npx-managed skills, use the installer instructions in `NPIX_INSTALL_NOTES.md` when refreshing them.

## Synchronization

A synchronization updates the repository to match the local directory:

1. Add new non-system directories from `~/.agents/skills`.
2. Copy changed skill files.
3. Remove directories no longer present locally.
4. Update `inventory.toml` and `NPIX_INSTALL_NOTES.md`.
5. Verify that `skills/` and the local non-system skill tree match byte-for-byte.

`PROVENANCE.md` documents the source and ownership boundaries.
