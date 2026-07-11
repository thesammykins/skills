# Provenance policy

This public repository includes skills imported from an attested working Mac on 2026-07-11. `inventory.toml` is authoritative for each skill's content hash and provenance status.

Entries marked `unresolved` have no verified upstream repository or redistribution license recorded locally. They are retained to make the working environment recoverable and are published as-is without claiming authorship. Known copyright and license files inside those directories are preserved unchanged.

If an exact upstream source is found:

1. Compare the complete directory hash and content.
2. Confirm the upstream license permits the intended use.
3. Replace the vendored directory with a pinned `skills.toml` source.
4. Update `inventory.toml` to `verified-upstream`.

Do not silently rewrite, relicense, or remove an unresolved skill during provenance cleanup.
