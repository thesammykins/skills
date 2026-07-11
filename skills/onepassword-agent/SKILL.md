---
name: onepassword-agent
description: Safely interact with 1Password from agent workflows using a service account token and the 1Password SDK. Use when Codex needs to load OP_SERVICE_ACCOUNT_TOKEN, resolve 1Password secret references, inject credentials into commands, upload secrets to CI/CD tools, use SSH keys without printing them, or read/write items in an agent-scoped vault without exposing secret values.
---

# 1Password Agent

Use this skill to move secrets between 1Password and tools without showing raw values to the model or terminal output. Default token source: `op://your-vault/your-item/credential` (set `OP_SERVICE_ACCOUNT_TOKEN_REF` to override).

## Bootstrap Once

At the start of a new agent/session that will use 1Password, run this once:

```zsh
source "$HOME/.agents/skills/onepassword-agent/scripts/load-token.zsh"
```

This is the only normal use of `source`. It loads `OP_SERVICE_ACCOUNT_TOKEN` into the current shell and writes a `0600` local cache so later fresh tool shells can reuse the token without another `op read` or Touch ID prompt.

After bootstrapping, do not source `load-token.zsh` again for routine work. Use the Node helper for every 1Password interaction:

```bash
node "$HOME/.agents/skills/onepassword-agent/scripts/op-agent.mjs" vaults
```

If the helper says both the environment token and local cache are missing, ask before bootstrapping again because that can trigger Touch ID or a 1Password approval prompt. Use `--token-ref` or `OP_SERVICE_ACCOUNT_TOKEN_REF` only when the token moves from the default reference. Never ask the user to paste the token into chat.

## Rules

- Use full `op://vault/item/field` secret references for secret values.
- Prefer IDs for item management: vault ID, item ID, section ID, and field ID.
- Do not print tokens, passwords, private keys, API keys, TOTP seeds, or resolved secret values.
- Do not call `op read` for the service account token after `OP_SERVICE_ACCOUNT_TOKEN` is already set.
- Do not source `load-token.zsh` before each operation. Source it once to bootstrap, then use `node .../op-agent.mjs` for all further operations.
- Prefer the helper's env/cache reuse over repeated `source load-token.zsh` calls.
- Prefer `run`, `pipe`, or `secret-file` so secrets go directly to the target tool.
- Use `pipe` for CI secret upload commands that read from stdin.
- Use `secret-file` for commands that require a private key or certificate path; it writes a `0600` temp file and deletes it after the command exits.
- Confirm destructive operations like archive/delete unless the user explicitly requested the exact action.
- Read `references/onepassword-sdk-notes.md` when you need SDK field/category constraints.

## Helper

Run the helper with Node:

```bash
node "$HOME/.agents/skills/onepassword-agent/scripts/op-agent.mjs" --help
```

Core commands:

- `vaults`: list accessible vaults.
- `items --vault-id <id>`: list active items in a vault.
- `item --vault-id <id> --item-id <id>`: show redacted item metadata.
- `validate --ref 'op://...'`: validate secret reference syntax.
- `run --env NAME=op://... -- <command>`: inject resolved refs as environment variables.
- `pipe --ref op://... -- <command>`: send one resolved secret to command stdin.
- `secret-file --ref op://... --env NAME -- <command>`: pass a temp file path in `NAME`.
- `set-field --vault-id <id> --item-id <id> --field-id <id> --value-ref op://...`: update an existing field from a safe source.
- `create-login --vault-id <id> --title <title> --username-ref op://... --password-ref op://...`: create a login item without literal secrets.
- `archive --vault-id <id> --item-id <id>`: archive an item.

## Common Patterns

Upload a private key to GitHub Actions without printing it:

```bash
node "$HOME/.agents/skills/onepassword-agent/scripts/op-agent.mjs" pipe \
  --ref 'op://Jarvis Vault/Deploy SSH/private key?ssh-format=openssh' \
  -- gh secret set DEPLOY_KEY --repo owner/repo --body-file -
```

Use an SSH key through a temp file:

```bash
node "$HOME/.agents/skills/onepassword-agent/scripts/op-agent.mjs" secret-file \
  --ref 'op://Jarvis Vault/Deploy SSH/private key?ssh-format=openssh' \
  --env SSH_KEY_PATH \
  -- sh -c 'ssh -i "$SSH_KEY_PATH" user@host'
```

Run a command with injected API credentials:

```bash
node "$HOME/.agents/skills/onepassword-agent/scripts/op-agent.mjs" run \
  --env API_TOKEN='op://Jarvis Vault/Example API/token' \
  -- sh -c 'curl -H "Authorization: Bearer $API_TOKEN" https://example.invalid'
```

Use `sh -c` when the child command needs shell expansion of injected environment variables.

## Resources

- `scripts/load-token.zsh`: source once to export `OP_SERVICE_ACCOUNT_TOKEN` and seed the local token cache.
- `scripts/op-agent.mjs`: run with `node` for every subsequent redacted read, env injection, stdin piping, temp-file use, and item write.
- `references/onepassword-sdk-notes.md`: compact SDK notes and constraints.
