#!/bin/bash
set -euo pipefail

# Only run in Claude Code web sessions
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# === GitHub token (sync — needed immediately) ===
SECRETS_FILE="${CLAUDE_PROJECT_DIR}/.claude/secrets"
if [ -f "$SECRETS_FILE" ]; then
  # shellcheck source=/dev/null
  source "$SECRETS_FILE"
fi

if [ -n "${GITHUB_TOKEN:-}" ]; then
  echo "export GITHUB_TOKEN='${GITHUB_TOKEN}'" >> "$CLAUDE_ENV_FILE"
fi

# === Async: pnpm install runs in background while session starts ===
echo '{"async": true, "asyncTimeout": 300000}'

cd "${CLAUDE_PROJECT_DIR}"
pnpm install
