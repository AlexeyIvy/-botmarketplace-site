#!/usr/bin/env bash
set -euo pipefail
BIN_DIR="/opt/botmarket-research/bin"
CFG_DIR="/etc/botmarket-research/tunnel"
ID_FILE="${CFG_DIR}/tunnel-id"
KEY_FILE="${CFG_DIR}/runtime-api-key"
PROFILE="${CFG_DIR}/runtime.yaml"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
UNIT_SRC="${SCRIPT_DIR}/botmarket-openai-tunnel.service"
READY_SRC="${SCRIPT_DIR}/tunnel_readiness_v0_1.sh"
echo "========== OPENAI SECURE MCP TUNNEL — SERVICE INSTALL =========="
echo "script_dir = ${SCRIPT_DIR}"
test -f "$UNIT_SRC"
test -f "$READY_SRC"
echo
echo "=== 1. PRECONDITIONS ==="
test -x "${BIN_DIR}/tunnel-client"
test -x "${BIN_DIR}/tunnel-client-runtime"
sudo test -r "$ID_FILE"
sudo test -r "$KEY_FILE"
sudo systemctl is-active --quiet botmarket-reader-mcp.service
sudo -u botmarket-mcp /opt/botmarket-research/venv/bin/python /opt/botmarket-research/app/reader_readiness.py
echo "PASS: Reader MCP ready"
if ss -lnt 2>/dev/null | grep -Eq '(^|[[:space:]])(127\.0\.0\.1:8080|0\.0\.0\.0:8080|\[::\]:8080)([[:space:]]|$)'; then
  echo "FAIL: health port 8080 already in use"
  ss -lntp | grep ':8080' || true
  exit 121
fi
echo "PASS: health port 8080 free"
echo
echo "=== 2. BUILD ROOT-OWNED RUNTIME PROFILE ==="
TUNNEL_ID="$(sudo cat "$ID_FILE")"
if [[ ! "$TUNNEL_ID" =~ ^tunnel_[0-9a-f]{32}$ ]]; then
  echo "FAIL: invalid stored tunnel id"
  exit 122
fi
TMP_PROFILE="$(mktemp)"
trap 'rm -f "$TMP_PROFILE"' EXIT
cat >"$TMP_PROFILE" <<EOF
config_version: 1
control_plane:
  base_url: https://api.openai.com
  tunnel_id: ${TUNNEL_ID}
  api_key: file:${KEY_FILE}
  max_inflight_requests: 4
  poll_channels:
    - main
log:
  level: info
  format: json
health:
  listen_addr: 127.0.0.1:8080
  url_file: /run/botmarket-tunnel/health-url
admin_ui:
  open_browser: false
  log_buffer_events: 500
process:
  pid_file: /run/botmarket-tunnel/tunnel-client.pid
mcp:
  server_urls:
    - channel: main
      url: http://127.0.0.1:8765/mcp
  startup_wait_timeout: 30s
  connection_max_ttl: 10m
  max_concurrent_requests: 2
cloudflared:
  managed: false
EOF
sudo install -o root -g botmarket-tunnel -m 0440 "$TMP_PROFILE" "$PROFILE"
echo "PASS: runtime profile installed"
echo
echo "=== 3. PROFILE DOCTOR ==="
sudo -u botmarket-tunnel "${BIN_DIR}/tunnel-client" doctor --profile-file "$PROFILE" --explain
echo "PASS: profile doctor"
echo
echo "=== 4. INSTALL READINESS + SYSTEMD UNIT ==="
sudo install -o root -g root -m 0555 "$READY_SRC" "${BIN_DIR}/tunnel-readiness"
sudo install -o root -g root -m 0644 "$UNIT_SRC" /etc/systemd/system/botmarket-openai-tunnel.service
sudo systemctl daemon-reload
echo "PASS: service files installed"
echo
echo "=== 5. START SERVICE WITH READINESS GATE ==="
sudo systemctl enable --now botmarket-openai-tunnel.service
echo
echo "=== 6. VERIFY SERVICE ==="
sudo systemctl is-active --quiet botmarket-openai-tunnel.service
sudo systemctl show botmarket-openai-tunnel.service -p ActiveState -p SubState -p MainPID -p NRestarts -p Result --no-pager
echo
echo "=== 7. VERIFY HEALTH / READY ==="
curl -fsS http://127.0.0.1:8080/healthz
echo
curl -fsS http://127.0.0.1:8080/readyz
echo
echo
echo "=== 8. FULL CLIENT STRUCTURED HEALTH ==="
sudo -u botmarket-tunnel "${BIN_DIR}/tunnel-client" health --url-file /run/botmarket-tunnel/health-url || true
echo
echo "=== 9. VERIFY NO PUBLIC HEALTH LISTENER ==="
sudo ss -lntp | grep '127.0.0.1:8080'
if sudo ss -lnt | grep -Eq '(^|[[:space:]])(0\.0\.0\.0:8080|\[::\]:8080)([[:space:]]|$)'; then
  echo "SECURITY_FAIL: tunnel health endpoint is public"
  exit 123
else
  echo "PASS: tunnel health is loopback-only"
fi
echo
echo "=== 10. VERIFY SECRET SEPARATION ==="
if sudo -u botmarket-mcp test -r "$KEY_FILE" 2>/dev/null; then
  echo "SECURITY_FAIL: Reader can read tunnel key"
  exit 124
else
  echo "PASS: Reader cannot read tunnel key"
fi
echo
echo "=== 11. RECENT TUNNEL LOGS ==="
sudo journalctl -u botmarket-openai-tunnel.service -n 50 --no-pager
echo
echo "========== OPENAI SECURE MCP TUNNEL SERVICE PASS =========="
