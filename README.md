# Skills Repository

Public, installable Agent Skills for use across Amp, Claude Code, Codex, and
other harnesses that discover the shared `.agents/skills` convention.

## Install

Clone the repository, then install every checked-in skill globally:

```bash
python3 scripts/install-skills.py install
```

The installer copies complete skill directories into `~/.agents/skills`. It
only manages the named skills and never deletes unrelated skills or `.system`.
If an installed skill has local changes, installation stops rather than
overwriting it; inspect the difference and pass `--force` when replacement is
intentional.

Install one or more skills:

```bash
python3 scripts/install-skills.py install \
  --skill agent-change-verification \
  --skill dogfood
```

Install project-local skills into `./.agents/skills`:

```bash
python3 scripts/install-skills.py install --project
```

Use `--target PATH` for another harness-specific location. The installer copies
files only; it does not execute bundled scripts or install runtime dependencies.

### Install externally managed skills

Skills with maintained upstream equivalents are intentionally not vendored.
Preview the reviewed `npx skills` commands without downloading anything:

```bash
python3 scripts/install-skills.py external
```

Install those skills globally for every supported agent harness:

```bash
python3 scripts/install-skills.py external --apply
```

Pass `--project` for a project-local install, or repeat `--agent NAME` to target
specific harnesses. `external-skills.toml` groups skills by verified source and
pins the Node and `skills` CLI versions. It records the source revision that was
reviewed; the current CLI installs from the repository's default branch, so the
preview and explicit `--apply` boundary are intentional.

## Release artifacts

Each tagged GitHub release contains:

- `<name>.skill` for every skill, with `SKILL.md` at the archive root;
- `skills-bundle.zip`, containing the complete catalog and installer; and
- `SHA256SUMS` for artifact verification.

After extracting `skills-bundle.zip`, run the same install command from its
root. Individual `.skill` archives can be imported by tools that support that
format directly.

## Repository layout

- `skills/<name>/` — canonical packaged skill source.
- `inventory.toml` — catalog and current provenance status.
- `external-skills.toml` — reviewed skills installed from upstream with
  `npx skills`.
- `scripts/install-skills.py` — validation, deterministic packaging,
  installation, external install preview, and verification.
- `.github/workflows/check.yml` — pull-request and branch validation.
- `.github/workflows/release.yml` — immutable releases for existing `v*` tags.
- `PROVENANCE.md` — source and ownership boundaries.

The repository currently contains 37 packaged skills and 9 externally managed
skills. `.system` is intentionally absent because it is managed by Codex and is
installation-specific.

## Develop and verify

```bash
python3 scripts/install-skills.py check
python3 -m unittest discover -s tests -v
python3 scripts/install-skills.py package
(cd dist && sha256sum --check SHA256SUMS)
```

Packaging is deterministic: identical source trees produce byte-identical
archives. To verify a global installation against this checkout:

```bash
python3 scripts/install-skills.py verify
```
