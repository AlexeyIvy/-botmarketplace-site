#!/bin/bash
set -euo pipefail

# Only run in Claude Code web sessions
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# === GitHub token ===
SECRETS_FILE="${CLAUDE_PROJECT_DIR}/.claude/secrets"
if [ -f "$SECRETS_FILE" ]; then
  # shellcheck source=/dev/null
  source "$SECRETS_FILE"
fi

if [ -n "${GITHUB_TOKEN:-}" ]; then
  echo "export GITHUB_TOKEN='${GITHUB_TOKEN}'" >> "$CLAUDE_ENV_FILE"
fi

# === pnpm dependencies ===
cd "${CLAUDE_PROJECT_DIR}"
pnpm install
