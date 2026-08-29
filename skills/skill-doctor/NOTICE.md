# Attribution and provenance

This `skill-doctor` fork is adapted from
[Warp's `warpdotdev/common-skills` implementation](https://github.com/warpdotdev/common-skills/tree/main/.agents/skills/skill-doctor),
copyright (c) 2026 Denver Technologies, Inc. The upstream work is licensed
under the [MIT License](https://github.com/warpdotdev/common-skills/blob/main/LICENSE);
the complete upstream license text is bundled verbatim in [`LICENSE`](LICENSE).

The published fork was imported from the user's Amp User Skills repository at
[`https://ampcode.com/git/@sammykins/-/skills`](https://ampcode.com/git/@sammykins/-/skills),
adapted commit `365cc485bbf33c7ecdab860c6a73087bedfc654b`.
Its upstream baseline matches `warpdotdev/common-skills` commit
[`f589e224907eda566c13755529f59db563090d14`](https://github.com/warpdotdev/common-skills/commit/f589e224907eda566c13755529f59db563090d14)
for the files in `.agents/skills/skill-doctor` before the Amp modifications.

The fork adds:

- authenticated Amp thread discovery and export;
- Amp personal and workspace skill discovery;
- explicit corpus selection, exclusion accounting, and complete-corpus sampling;
- Amp fixtures and collector regression tests;
- Amp Portal delivery for generated HTML reports; and
- evidence-backed remediation of authoritative project, user, and workspace
  skill sources, subject to scope, permissions, and normal publication approval.

Warp, Claude Code, and Codex collection and reporting remain supported. Warp
and Denver Technologies, Inc. do not endorse, sponsor, or maintain this fork.

At publication time, the upstream repository and the complete upstream skill
tree were checked for `LICENSE`, `LICENCE`, `NOTICE`, `COPYING`, copyright,
SPDX, attribution, trademark, and per-file licensing markers. The root MIT
License was the only explicit legal notice found; no additional per-file terms
were present.
