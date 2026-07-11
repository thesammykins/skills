#!/usr/bin/env zsh

DEFAULT_OP_SERVICE_ACCOUNT_TOKEN_REF='op://your-vault/your-item/credential'
DEFAULT_CACHE_DIR="${OP_AGENT_CACHE_DIR:-${XDG_RUNTIME_DIR:-${TMPDIR:-$HOME/.cache}}/onepassword-agent}"
DEFAULT_CACHE_FILE="${OP_SERVICE_ACCOUNT_TOKEN_CACHE:-$DEFAULT_CACHE_DIR/op-service-account-token}"

if [[ "${ZSH_EVAL_CONTEXT:-}" != *:file ]]; then
  print -u2 "Source this script so it can export OP_SERVICE_ACCOUNT_TOKEN in the current shell:"
  print -u2 "  source \"$HOME/.agents/skills/onepassword-agent/scripts/load-token.zsh\""
  exit 2
fi

token_ref="${OP_SERVICE_ACCOUNT_TOKEN_REF:-$DEFAULT_OP_SERVICE_ACCOUNT_TOKEN_REF}"
timeout_seconds="${OP_SERVICE_ACCOUNT_TOKEN_TIMEOUT:-45}"
cache_file="$DEFAULT_CACHE_FILE"
use_cache=1
if [[ "${OP_AGENT_DISABLE_TOKEN_CACHE:-}" == "1" ]]; then
  use_cache=0
fi
force=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --token-ref)
      if [[ -z "${2:-}" ]]; then
        print -u2 "Missing value for --token-ref"
        return 2
      fi
      token_ref="$2"
      shift 2
      ;;
    --force)
      force=1
      shift
      ;;
    --no-cache)
      use_cache=0
      shift
      ;;
    --cache-file)
      if [[ -z "${2:-}" ]]; then
        print -u2 "Missing value for --cache-file"
        return 2
      fi
      cache_file="$2"
      shift 2
      ;;
    --clear-cache)
      rm -f "$cache_file"
      unset OP_SERVICE_ACCOUNT_TOKEN
      print -u2 "Cleared OP_SERVICE_ACCOUNT_TOKEN and local token cache."
      return 0
      ;;
    --timeout)
      if [[ -z "${2:-}" ]]; then
        print -u2 "Missing value for --timeout"
        return 2
      fi
      timeout_seconds="$2"
      shift 2
      ;;
    --help|-h)
      print "Usage: source load-token.zsh [--token-ref op://vault/item/field] [--force] [--timeout seconds] [--no-cache] [--cache-file path] [--clear-cache]"
      return 0
      ;;
    *)
      if [[ "$1" == --* ]]; then
        print -u2 "Unknown option: $1"
        return 2
      fi
      shift
      ;;
  esac
done

if [[ -n "${OP_SERVICE_ACCOUNT_TOKEN:-}" && "$force" -ne 1 ]]; then
  export OP_SERVICE_ACCOUNT_TOKEN
  export OP_SERVICE_ACCOUNT_TOKEN_REF="$token_ref"
  if [[ "$use_cache" -eq 1 ]]; then
    mkdir -p "${cache_file:h}"
    chmod 700 "${cache_file:h}" >/dev/null 2>&1 || true
    tmp_cache="$(mktemp "${cache_file}.XXXXXX")"
    print -r -- "$OP_SERVICE_ACCOUNT_TOKEN" >"$tmp_cache"
    chmod 600 "$tmp_cache"
    mv "$tmp_cache" "$cache_file"
    unset tmp_cache
  fi
  print -u2 "OP_SERVICE_ACCOUNT_TOKEN is already loaded."
  return 0
fi

if [[ "$use_cache" -eq 1 && "$force" -ne 1 && -r "$cache_file" ]]; then
  token="$(<"$cache_file")"
  if [[ -n "$token" ]]; then
    export OP_SERVICE_ACCOUNT_TOKEN="$token"
    export OP_SERVICE_ACCOUNT_TOKEN_REF="$token_ref"
    unset token
    print -u2 "OP_SERVICE_ACCOUNT_TOKEN loaded from local token cache."
    return 0
  fi
  unset token
fi

if ! command -v op >/dev/null 2>&1; then
  print -u2 "1Password CLI 'op' is required to bootstrap OP_SERVICE_ACCOUNT_TOKEN from a secret reference."
  return 1
fi

if [[ ! "$timeout_seconds" = <-> || "$timeout_seconds" -lt 1 ]]; then
  print -u2 "Timeout must be a positive integer number of seconds."
  return 2
fi

tmp_out="$(mktemp -t op-agent-token-out.XXXXXX)"
tmp_err="$(mktemp -t op-agent-token-err.XXXXXX)"
op read "$token_ref" >"$tmp_out" 2>"$tmp_err" &
op_pid=$!
elapsed=0

while kill -0 "$op_pid" >/dev/null 2>&1; do
  if (( elapsed >= timeout_seconds )); then
    kill "$op_pid" >/dev/null 2>&1
    wait "$op_pid" >/dev/null 2>&1
    rm -f "$tmp_out" "$tmp_err"
    print -u2 "Timed out waiting for 1Password CLI to read the service account token. Unlock/sign in to 1Password CLI or set OP_SERVICE_ACCOUNT_TOKEN manually."
    return 1
  fi
  sleep 1
  (( elapsed++ ))
done

wait "$op_pid"
op_status=$?
token="$(<"$tmp_out")"
op_error="$(<"$tmp_err")"
rm -f "$tmp_out" "$tmp_err"

if [[ "$op_status" -ne 0 ]]; then
  unset token
  if [[ -n "$op_error" ]]; then
    print -u2 "$op_error"
  fi
  unset op_error
  print -u2 "Failed to read OP_SERVICE_ACCOUNT_TOKEN from 1Password reference."
  return "$op_status"
fi
unset op_error

if [[ -z "$token" ]]; then
  unset token
  print -u2 "1Password returned an empty service account token."
  return 1
fi

export OP_SERVICE_ACCOUNT_TOKEN="$token"
export OP_SERVICE_ACCOUNT_TOKEN_REF="$token_ref"
if [[ "$use_cache" -eq 1 ]]; then
  mkdir -p "${cache_file:h}"
  chmod 700 "${cache_file:h}" >/dev/null 2>&1 || true
  tmp_cache="$(mktemp "${cache_file}.XXXXXX")"
  print -r -- "$token" >"$tmp_cache"
  chmod 600 "$tmp_cache"
  mv "$tmp_cache" "$cache_file"
  unset tmp_cache
fi
unset token
print -u2 "OP_SERVICE_ACCOUNT_TOKEN loaded from 1Password reference."
