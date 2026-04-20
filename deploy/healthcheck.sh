#!/usr/bin/env bash
# healthcheck.sh — probe the API /readyz endpoint and alert on repeated failure.
#
# Triggered by systemd timer (botmarket-healthcheck.timer) every 30s.
# On two consecutive non-200 responses an alert is sent to $ALERT_WEBHOOK_URL
# (Telegram bot API or Slack-incoming-webhook compatible JSON POST).
#
# Consecutive-failure state is persisted at $STATE_FILE so the check is stateless
# between invocations.
#
# Environment:
#   READYZ_URL          URL to probe (default: http://127.0.0.1:4000/readyz)
#   ALERT_WEBHOOK_URL   Webhook to POST on alert (optional — skipped if unset)
#   ALERT_WEBHOOK_KIND  "telegram" (default) or "slack"
#   ALERT_CHAT_ID       Telegram chat id (required if kind=telegram)
#   STATE_FILE          Failure counter file (default: /var/lib/botmarket/healthcheck.state)
#   FAIL_THRESHOLD      Consecutive failures before alert (default: 2)

set -u

READYZ_URL="${READYZ_URL:-http://127.0.0.1:4000/readyz}"
ALERT_WEBHOOK_URL="${ALERT_WEBHOOK_URL:-}"
ALERT_WEBHOOK_KIND="${ALERT_WEBHOOK_KIND:-telegram}"
ALERT_CHAT_ID="${ALERT_CHAT_ID:-}"
STATE_FILE="${STATE_FILE:-/var/lib/botmarket/healthcheck.state}"
FAIL_THRESHOLD="${FAIL_THRESHOLD:-2}"

mkdir -p "$(dirname "$STATE_FILE")"
prev_fails=0
if [[ -r "$STATE_FILE" ]]; then
  prev_fails=$(cat "$STATE_FILE" 2>/dev/null || echo 0)
  [[ "$prev_fails" =~ ^[0-9]+$ ]] || prev_fails=0
fi

status=$(curl -s -o /tmp/healthcheck.body -w "%{http_code}" --max-time 5 "$READYZ_URL" 2>/dev/null)
[[ -z "$status" ]] && status="000"

if [[ "$status" == "200" ]]; then
  echo 0 > "$STATE_FILE"
  exit 0
fi

fails=$((prev_fails + 1))
echo "$fails" > "$STATE_FILE"

echo "healthcheck: $READYZ_URL returned $status (consecutive failures: $fails)" >&2

if (( fails < FAIL_THRESHOLD )); then
  exit 0
fi

# Only alert on the edge (first time we cross the threshold) to avoid spam.
if (( fails > FAIL_THRESHOLD )); then
  exit 0
fi

if [[ -z "$ALERT_WEBHOOK_URL" ]]; then
  echo "healthcheck: ALERT_WEBHOOK_URL not set — skipping alert" >&2
  exit 0
fi

host=$(hostname -f 2>/dev/null || hostname)
body=$(head -c 500 /tmp/healthcheck.body 2>/dev/null || echo "")
message="[botmarket] $host /readyz unhealthy (status=$status, consecutive=$fails). Body: $body"

case "$ALERT_WEBHOOK_KIND" in
  telegram)
    if [[ -z "$ALERT_CHAT_ID" ]]; then
      echo "healthcheck: ALERT_CHAT_ID required for telegram" >&2
      exit 1
    fi
    curl -s --max-time 5 -X POST "$ALERT_WEBHOOK_URL" \
      --data-urlencode "chat_id=$ALERT_CHAT_ID" \
      --data-urlencode "text=$message" >/dev/null || true
    ;;
  slack)
    payload=$(printf '{"text":%s}' "$(printf '%s' "$message" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')")
    curl -s --max-time 5 -X POST -H "Content-Type: application/json" \
      --data "$payload" "$ALERT_WEBHOOK_URL" >/dev/null || true
    ;;
  *)
    echo "healthcheck: unknown ALERT_WEBHOOK_KIND=$ALERT_WEBHOOK_KIND" >&2
    exit 1
    ;;
esac

exit 0
