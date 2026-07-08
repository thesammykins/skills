# Skills

Curated agent skills for Samantha's Macs.

This repo has two jobs:

1. Store first-party or locally customized skills.
2. Declare upstream skill sources that should be installed into `$HOME/.agents/skills`.

It is not a dump of every installed skill. If an upstream skill is used as-is, keep it in `skills.toml` and install it from the source repo. Vendor a third-party skill here only after making local changes, and record the upstream source in the manifest.

## Install

```bash
python3 scripts/install-skills.py --profile core --dry-run
python3 scripts/install-skills.py --profile core,apple
```

Profiles:

- `core`: local custom skills that are useful on every Mac.
- `apple`: Swift/iOS/macOS skills installed from upstream.
- `agent-dev`: agent-development skills from this repo.

`new-mac` calls this installer from its profile-driven setup flow.

## Validate

```bash
python3 scripts/install-skills.py --check
```

## Policy

- Local custom skills live at the repo root, for example `convert-prompt/`.
- Upstream skills stay upstream unless customized.
- Installs target `$HOME/.agents/skills` by default.
- The Codex system `skill-installer` is used for GitHub-backed upstream skills.
- Official Codex plugin skills stay in the Codex plugin cache; this repo does not vendor them.
