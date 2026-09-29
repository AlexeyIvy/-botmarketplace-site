#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

TUNNEL_ID="${1:-${TUNNEL_ID:-}}"
[[ -n "$TUNNEL_ID" ]] || {
  echo "Usage: sudo bash $0 tunnel_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  exit 2
}
[[ "$TUNNEL_ID" =~ ^tunnel_[0-9a-f]{32}$ ]] || {
  echo "[FAIL] Invalid tunnel id: $TUNNEL_ID" >&2
  exit 1
}

BIN="${BM_TUNNEL_BIN:-/opt/botmarket-research/bin/tunnel-client-runtime}"
SRC_ENV="${BM_TUNNEL_SOURCE_ENV:-/etc/botmarket-research/runner-tunnel.env}"

ENV_DIR="/etc/botmarket-research"
ENV_FILE="$ENV_DIR/test-executor-tunnel.env"
UNIT="/etc/systemd/system/botmarket-test-executor-tunnel.service"
SERVICE="botmarket-test-executor-tunnel.service"

MCP_URL="${BM_TEST_EXECUTOR_MCP_URL:-http://127.0.0.1:8769/mcp}"
HEALTH_ADDR="${BM_TEST_EXECUTOR_TUNNEL_HEALTH_ADDR:-127.0.0.1:8083}"

TUNNEL_USER="botmarket-tunnel"
TUNNEL_GROUP="botmarket-tunnel"
TUNNEL_HOME="/var/lib/botmarket-tunnel"

TS="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/root/botmarket-test-executor-tunnel-backups/$TS"

log(){ printf '\n[%s] %s\n' "$1" "$2"; }
die(){ echo "[FAIL] $*" >&2; exit 1; }

[[ "${EUID:-$(id -u)}" -eq 0 ]] || die "Run as root"

log STEP "Preflight"
for c in systemctl journalctl curl ss grep sed install id getent chown chmod cp rm mktemp seq; do
  command -v "$c" >/dev/null || die "$c missing"
done
[[ -x "$BIN" ]] || die "Tunnel client not found: $BIN"
id "$TUNNEL_USER" >/dev/null 2>&1 || die "Tunnel user not found"
getent group "$TUNNEL_GROUP" >/dev/null || die "Tunnel group not found"
systemctl is-active --quiet botmarket-test-executor.service || die "Test Executor MCP is not active"

API_KEY_SOURCE=""
if [[ -n "${CONTROL_PLANE_API_KEY:-}" ]]; then
  API_KEY_SOURCE="environment"
elif [[ -r "$SRC_ENV" ]] && grep -q '^CONTROL_PLANE_API_KEY=.' "$SRC_ENV"; then
  API_KEY_SOURCE="existing-env"
else
  die "No CONTROL_PLANE_API_KEY available. Export it or restore $SRC_ENV."
fi

install -d -m0700 "$BACKUP"
[[ -f "$ENV_FILE" ]] && cp -a "$ENV_FILE" "$BACKUP/test-executor-tunnel.env.bak"
[[ -f "$UNIT" ]] && cp -a "$UNIT" "$BACKUP/botmarket-test-executor-tunnel.service.bak"

if systemctl is-active --quiet "$SERVICE" 2>/dev/null; then
  systemctl stop "$SERVICE"
fi
sleep 1

if ss -ltnH | awk '{print $4}' | grep -Eq '(^|:)8083$'; then
  ss -ltnp | grep ':8083' || true
  die "Health port 8083 is occupied"
fi

if [[ "$API_KEY_SOURCE" == "existing-env" ]]; then
  grep '^CONTROL_PLANE_API_KEY=' "$SRC_ENV" > "$ENV_FILE"
else
  cat > "$ENV_FILE" <<EOF
CONTROL_PLANE_API_KEY=$CONTROL_PLANE_API_KEY
EOF
fi

set_env() {
  local key="$1" value="$2" file="$3"
  if grep -q "^${key}=" "$file"; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$file"
  else
    printf '%s=%s\n' "$key" "$value" >> "$file"
  fi
}

set_env CONTROL_PLANE_TUNNEL_ID "$TUNNEL_ID" "$ENV_FILE"
set_env MCP_SERVER_URL "$MCP_URL" "$ENV_FILE"
set_env HEALTH_LISTEN_ADDR "$HEALTH_ADDR" "$ENV_FILE"

chown root:"$TUNNEL_GROUP" "$ENV_FILE"
chmod 0640 "$ENV_FILE"

log STEP "Verify local Test Executor MCP"
set +e
TMP="$(mktemp)"
HTTP_CODE="$(curl -sS -N --max-time 2 -o "$TMP" -w '%{http_code}'   -H 'Accept: application/json, text/event-stream' "$MCP_URL" 2>/dev/null)"
RC=$?
set -e
rm -f "$TMP"
if [[ "$HTTP_CODE" != "200" && $RC -ne 0 ]]; then
  die "Local Test Executor MCP is not reachable: HTTP=$HTTP_CODE curl_rc=$RC"
fi

log STEP "Install dedicated tunnel service"
cat > "$UNIT" <<EOF
[Unit]
Description=BotMarketplace OpenAI Tunnel - Test Executor MCP
After=network-online.target botmarket-test-executor.service
Wants=network-online.target
Requires=botmarket-test-executor.service

[Service]
Type=simple
User=$TUNNEL_USER
Group=$TUNNEL_GROUP
WorkingDirectory=$TUNNEL_HOME
Environment=HOME=$TUNNEL_HOME
EnvironmentFile=$ENV_FILE
ExecStart=$BIN run
Restart=on-failure
RestartSec=3
TimeoutStopSec=20
KillMode=control-group
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
ProtectKernelLogs=true
RestrictSUIDSGID=true
LockPersonality=true
CapabilityBoundingSet=
AmbientCapabilities=
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
ReadWritePaths=$TUNNEL_HOME
ReadOnlyPaths=$ENV_FILE $BIN

[Install]
WantedBy=multi-user.target
EOF

chmod 0644 "$UNIT"
systemctl daemon-reload
systemctl enable "$SERVICE" >/dev/null
systemctl restart "$SERVICE"
sleep 2

if ! systemctl is-active --quiet "$SERVICE"; then
  systemctl --no-pager --full status "$SERVICE" || true
  journalctl -u "$SERVICE" -n100 --no-pager || true
  die "Test Executor tunnel failed to start"
fi

log STEP "Wait for health listener"
FOUND=0
for _ in $(seq 1 30); do
  if ss -ltnH | awk '{print $4}' | grep -Eq '(^|:)8083$'; then
    FOUND=1
    break
  fi
  sleep 1
done
[[ "$FOUND" -eq 1 ]] || {
  journalctl -u "$SERVICE" -n100 --no-pager || true
  systemctl stop "$SERVICE" || true
  die "Health listener 8083 did not appear"
}

log STEP "Wait for tunnel readiness"
READY=0
LAST_CODE=""
for _ in $(seq 1 45); do
  set +e
  LAST_CODE="$(curl -sS --max-time 4 -o /tmp/bm-test-ready.$$ -w '%{http_code}'     http://127.0.0.1:8083/readyz 2>/dev/null)"
  RC=$?
  set -e
  if [[ $RC -eq 0 && "$LAST_CODE" == "200" ]]; then
    READY=1
    break
  fi
  sleep 1
done
rm -f /tmp/bm-test-ready.$$ 2>/dev/null || true

if [[ "$READY" -ne 1 ]]; then
  echo "READY_HTTP_CODE=${LAST_CODE:-NONE}"
  curl -sS --max-time 5 'http://127.0.0.1:8083/health?details=true' 2>/dev/null || true
  journalctl -u "$SERVICE" -n120 --no-pager || true
  systemctl stop "$SERVICE" || true
  die "Tunnel did not become READY"
fi

echo
echo "=== BOTMARKETPLACE TEST EXECUTOR TUNNEL INSTALLED ==="
echo "Tunnel ID: $TUNNEL_ID"
echo "Local MCP: $MCP_URL"
echo "Health: http://127.0.0.1:8083"
echo "Test Executor tunnel: READY"
echo "Research Runner: NOT MODIFIED"
echo "GitHub Control: NOT MODIFIED"
