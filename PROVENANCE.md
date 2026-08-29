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

## `skill-doctor`

`skills/skill-doctor` is an Amp-compatible fork of Warp's
[`warpdotdev/common-skills` `skill-doctor`](https://github.com/warpdotdev/common-skills/tree/main/.agents/skills/skill-doctor),
copyright (c) 2026 Denver Technologies, Inc. The imported adapter is from the
user's [Amp User Skills repository](https://ampcode.com/git/@sammykins/-/skills)
at commit `365cc485bbf33c7ecdab860c6a73087bedfc654b`.
The upstream baseline was checked at `f589e224907eda566c13755529f59db563090d14`.

The fork adds authenticated Amp conversation collection, Amp skill discovery,
bounded-corpus accounting and fixtures, Amp Portal report delivery, and
evidence-backed remediation of authoritative skill sources. Existing Warp,
Claude Code, and Codex support is retained. Warp and Denver Technologies, Inc.
do not endorse or maintain this fork.

The upstream repository and complete skill tree were checked for additional
license, notice, copyright, SPDX, attribution, trademark, and per-file terms.
No terms beyond the root MIT License were found. The upstream MIT text is
preserved verbatim in `skills/skill-doctor/LICENSE`; detailed adaptation notes
are in `skills/skill-doctor/NOTICE.md`.
