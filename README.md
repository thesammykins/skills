# Skills

This repository is a checked-in snapshot of Samantha's global agent skills. It mirrors the directories currently present in `~/.agents/skills`, except for `.system`.

## What is included

- Every current non-system skill directory is copied under `skills/<name>/`.
- This includes `happy-path-use-case-design` and skills installed locally by `npx skills`.
- `.system` is deliberately excluded because Codex manages it and it is not part of this shareable skill set.
- The repository does not include Hermes-only skills or any directory that is not present in the local `~/.agents/skills` snapshot.

The repository currently contains 42 skill directories. The authoritative list is `inventory.toml`; the files in `skills/` are the actual skill content.

## How to use this repository

To install the snapshot into another account's global skills directory, copy the directories under `skills/` into `~/.agents/skills/`. Do not copy `.system` from another installation.

Skills whose normal installation is managed by `npx skills` are still checked in here because the goal is to preserve the current local snapshot. `NPIX_INSTALL_NOTES.md` lists those skills and explains that they should be refreshed with `npx skills@1.5.16` when you want the installer-managed version.

## How it is maintained

1. Compare the repository with the current `~/.agents/skills` directory.
2. Copy every non-system skill directory into `skills/`.
3. Remove repository directories that no longer exist locally.
4. Update `inventory.toml` and the npx notes.
5. Verify that the repository and local non-system skill trees match byte-for-byte.

`PROVENANCE.md` documents the source and ownership boundaries.
