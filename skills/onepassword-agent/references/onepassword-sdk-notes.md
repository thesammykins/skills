# 1Password SDK Notes

## Token Loading

- Default token reference: `op://your-vault/your-item/credential` (set `OP_SERVICE_ACCOUNT_TOKEN_REF` to override).
- Source `scripts/load-token.zsh` once as the explicit auth/bootstrap action for a new agent/session. It can call `op read` and may trigger Touch ID or a 1Password approval prompt.
- After that first source, run `node scripts/op-agent.mjs ...` for all 1Password interactions. Do not source the loader before each helper command.
- The loader writes a local `0600` token cache by default under `${OP_AGENT_CACHE_DIR:-${XDG_RUNTIME_DIR:-${TMPDIR:-$HOME/.cache}}/onepassword-agent}/op-service-account-token` so later fresh tool shells can reuse the service account token without another Touch ID prompt.
- The helper reads `OP_SERVICE_ACCOUNT_TOKEN` first and then the local cache. It only calls `op read` when explicitly run with `--bootstrap-token`.
- Clear the cache with `source scripts/load-token.zsh --clear-cache`. Disable cache for one bootstrap with `--no-cache` or set `OP_AGENT_DISABLE_TOKEN_CACHE=1` for the JS helper.
- The loader times out after 45 seconds by default. Use `--timeout seconds` or `OP_SERVICE_ACCOUNT_TOKEN_TIMEOUT` if 1Password CLI needs longer.
- Child processes cannot mutate the parent shell. The helper expects `OP_SERVICE_ACCOUNT_TOKEN` to be set already; explicit `--bootstrap-token` is only for one-off fallback use and can trigger 1Password CLI auth.
- In non-persistent shells, group related 1Password operations into one compound shell command after sourcing the loader, or expect a new auth prompt for each fresh shell.
- Do not print the token or ask the user to paste it into chat.

## Secret References

- Use `op://vault/item/field` for simple fields.
- Use `op://vault/item/section/field` for section fields.
- Quote refs containing spaces.
- If a vault, item, section, or field contains unsupported characters, use its 26-character ID.
- Use `?attribute=otp` for TOTP codes.
- Use `?ssh-format=openssh` for SSH private keys when a command expects OpenSSH format.

## SDK Operations

- JS client creation uses `sdk.createClient({ auth: process.env.OP_SERVICE_ACCOUNT_TOKEN, integrationName, integrationVersion })`.
- Resolve one secret with `client.secrets.resolve(ref)`.
- Validate syntax with `sdk.Secrets.validateSecretReference(ref)`.
- List vaults with `client.vaults.list()`.
- List item overviews with `client.items.list(vaultId)`.
- Get an item with `client.items.get(vaultId, itemId)`.
- Create an item with `client.items.create(params)`.
- Update an item by fetching it, changing fields, and calling `client.items.put(updatedItem)`.
- Archive with `client.items.archive(vaultId, itemId)`.

## Item Management Constraints

- Item management operations require IDs for vaults, items, sections, and fields.
- Supported field types include `Text`, `Concealed`, `Totp`, `Url`, `Email`, `Date`, `MonthYear`, `CreditCardNumber`, `SSHKey`, and file/document types.
- Built-in Login field IDs are `username` and `password`.
- Custom fields generally need a section ID.
- If an item contains unsupported field types, update/delete can fail.
- Service account needs read permissions for read operations and read/write permissions for create/update/archive operations.

## Safe Transfer Patterns

- For CI uploads, pipe the secret to a command that reads stdin, such as `gh secret set NAME --body-file -`.
- For SSH keys, use the helper's `secret-file` command so the key exists only in a temporary `0600` file that is removed afterward.
- For shell expansion of injected env vars, run through `sh -c 'command using "$VAR"'`.
- Redaction only catches exact secret values in stdout/stderr. Avoid commands that intentionally transform or print secrets.
