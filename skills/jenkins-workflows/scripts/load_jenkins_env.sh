#!/usr/bin/env bash
# Source this file to load Jenkins API credentials for the current shell only.
set -euo pipefail

if [[ -n "${BASH_VERSION:-}" && "${BASH_SOURCE[0]}" == "$0" ]]; then
  printf 'This script must be sourced so exports affect your current shell:\n' >&2
  printf '  source "%s"\n' "$0" >&2
  exit 2
fi

export JENKINS_URL="${JENKINS_URL:-http://your-jenkins-host:8080}"
export JENKINS_USER_ID="${JENKINS_USER_ID:-$(op read 'op://your-vault/jenkins-api-key/username')}"
export JENKINS_API_TOKEN="${JENKINS_API_TOKEN:-$(op read 'op://your-vault/jenkins-api-key/credential')}"

printf 'Loaded Jenkins env for %s at %s\n' "$JENKINS_USER_ID" "$JENKINS_URL"
