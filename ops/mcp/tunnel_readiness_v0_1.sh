#!/usr/bin/env bash
set -euo pipefail
BASE="http://127.0.0.1:8080"
DEADLINE=$((SECONDS + 45))
LAST=""
while [ "$SECONDS" -lt "$DEADLINE" ]; do
  if BODY="$(curl -fsS --max-time 2 "${BASE}/readyz" 2>/dev/null)"; then
    printf 'OPENAI_TUNNEL_READY url=%s/readyz body=%s\n' "$BASE" "$BODY"
    exit 0
  fi
  LAST="$(curl -sS --max-time 2 "${BASE}/readyz" 2>/dev/null || true)"
  sleep 0.5
done
echo "OPENAI_TUNNEL_NOT_READY last_readyz=${LAST}" >&2
curl -sS --max-time 2 "${BASE}/healthz" 2>/dev/null || true
echo >&2
exit 1
