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
INSTALLER_BUILD="v0.1.4-permission-safe"

on_error() {
  rc=$?
  line=$1
  echo
  echo "===== TUNNEL INSTALL FAILURE rc=$rc line=$line =====" >&2
  sudo systemctl status botmarket-openai-tunnel.service --no-pager -l 2>/dev/null || true
  sudo journalctl -u botmarket-openai-tunnel.service -n 120 --no-pager 2>/dev/null || true
  echo "--- local health ---" >&2
  curl -sS --max-time 2 http://127.0.0.1:8080/healthz 2>/dev/null || true
  echo >&2
  curl -sS --max-time 2 http://127.0.0.1:8080/readyz 2>/dev/null || true
  echo >&2
  exit "$rc"
}
trap 'on_error $LINENO' ERR
echo "========== OPENAI SECURE MCP TUNNEL — SERVICE INSTALL =========="
echo "script_dir = ${SCRIPT_DIR}"
echo "installer_build = ${INSTALLER_BUILD}"

echo
echo "=== 0. STOP STALE SERVICE / RESTART LOOP ==="
sudo systemctl stop botmarket-openai-tunnel.service 2>/dev/null || true
sudo systemctl reset-failed botmarket-openai-tunnel.service 2>/dev/null || true
echo "PASS: stale service stopped/reset"

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
process:
  pid_file: /run/botmarket-tunnel/tunnel-client.pid
mcp:
  server_urls:
    - channel: main
      url: http://127.0.0.1:8765/mcp
  startup_wait_timeout: 30s
  connection_max_ttl: 10m
  max_concurrent_requests: 2
EOF
sudo install -o root -g botmarket-tunnel -m 0440 "$TMP_PROFILE" "$PROFILE"
echo "PASS: runtime profile installed"

echo
echo "=== 2B. VERIFY v0.0.14 PROFILE SCHEMA ==="
if sudo grep -Eq '^[[:space:]]*(show_details:|cloudflared:|admin_ui:)' "$PROFILE"; then
  echo "FAIL: unsupported v0.0.14 profile field detected"
  sudo sed -n '1,220p' "$PROFILE" | sed '/api_key:/s#file:.*#file:[REDACTED]#'
  exit 124
else
  echo "PASS: profile contains no unsupported v0.0.14 fields"
fi

echo
echo "=== 2C. EFFECTIVE v0.0.14 RUNTIME PROFILE ==="
sudo sed -n '1,220p' "$PROFILE" | sed '/api_key:/s#file:.*#file:[REDACTED]#'

echo
echo "=== 3. PROFILE DOCTOR ==="
sudo -u botmarket-tunnel "${BIN_DIR}/tunnel-client" doctor --profile-file "$PROFILE" --explain
echo "PASS: profile doctor"

echo
echo "=== 4. RUNTIME-ONLY PREFLIGHT (EXACT PRODUCTION BINARY) ==="
PREFLIGHT_DIR="$(mktemp -d)"
PREFLIGHT_LOG="$PREFLIGHT_DIR/runtime.log"
PREFLIGHT_URL="$PREFLIGHT_DIR/health-url"
PREFLIGHT_PID="$PREFLIGHT_DIR/pid"
chmod 0770 "$PREFLIGHT_DIR"
sudo chgrp botmarket-tunnel "$PREFLIGHT_DIR"

sudo -u botmarket-tunnel   timeout 25s "${BIN_DIR}/tunnel-client-runtime" run     --profile-file "$PROFILE"     --health.listen-addr=127.0.0.1:0     --health.url-file="$PREFLIGHT_URL"     --pid.file="$PREFLIGHT_PID"     >"$PREFLIGHT_LOG" 2>&1 &
PREFLIGHT_WRAPPER=$!

PREFLIGHT_BASE=""
for _ in $(seq 1 60); do
  if [ -s "$PREFLIGHT_URL" ]; then
    PREFLIGHT_BASE="$(sudo -u botmarket-tunnel cat "$PREFLIGHT_URL")"
    break
  fi
  if ! kill -0 "$PREFLIGHT_WRAPPER" 2>/dev/null; then
    break
  fi
  sleep 0.25
done

if [ -z "$PREFLIGHT_BASE" ]; then
  echo "FAIL: runtime-only binary exited before publishing health URL"
  sudo ls -ld "$PREFLIGHT_DIR" || true
  sudo ls -la "$PREFLIGHT_DIR" || true
  cat "$PREFLIGHT_LOG" || true
  wait "$PREFLIGHT_WRAPPER" 2>/dev/null || true
  rm -rf "$PREFLIGHT_DIR"
  exit 126
fi

echo "runtime_preflight_base = $PREFLIGHT_BASE"

PREFLIGHT_READY=0
for _ in $(seq 1 80); do
  if curl -fsS --max-time 2 "$PREFLIGHT_BASE/readyz" >"$PREFLIGHT_DIR/ready.txt" 2>/dev/null; then
    PREFLIGHT_READY=1
    break
  fi
  sleep 0.25
done

if [ "$PREFLIGHT_READY" -ne 1 ]; then
  echo "FAIL: exact runtime binary did not become ready"
  echo "--- /readyz ---"
  curl -sS --max-time 2 "$PREFLIGHT_BASE/readyz" || true

  echo
  echo "--- runtime log ---"
  cat "$PREFLIGHT_LOG" || true
  kill "$PREFLIGHT_WRAPPER" 2>/dev/null || true
  wait "$PREFLIGHT_WRAPPER" 2>/dev/null || true
  rm -rf "$PREFLIGHT_DIR"
  exit 127
fi

cat "$PREFLIGHT_DIR/ready.txt"
echo
echo "PASS: exact production runtime accepted profile and reached ready"

kill "$PREFLIGHT_WRAPPER" 2>/dev/null || true
wait "$PREFLIGHT_WRAPPER" 2>/dev/null || true
rm -rf "$PREFLIGHT_DIR"

echo
echo "=== 5. INSTALL READINESS + SYSTEMD UNIT ==="
sudo install -o root -g root -m 0555 "$READY_SRC" "${BIN_DIR}/tunnel-readiness"
sudo install -o root -g root -m 0644 "$UNIT_SRC" /etc/systemd/system/botmarket-openai-tunnel.service
sudo systemctl daemon-reload
echo "PASS: service files installed"
echo
echo "=== 6. START SERVICE WITH READINESS GATE ==="
sudo systemctl enable --now botmarket-openai-tunnel.service
echo
echo "=== 7. VERIFY SERVICE ==="
sudo systemctl is-active --quiet botmarket-openai-tunnel.service
sudo systemctl show botmarket-openai-tunnel.service -p ActiveState -p SubState -p MainPID -p NRestarts -p Result --no-pager
echo
echo "=== 8. VERIFY HEALTH / READY ==="
curl -fsS http://127.0.0.1:8080/healthz
echo
curl -fsS http://127.0.0.1:8080/readyz
echo
echo
echo "=== 9. FULL CLIENT STRUCTURED HEALTH ==="
sudo -u botmarket-tunnel "${BIN_DIR}/tunnel-client" health --url-file /run/botmarket-tunnel/health-url || true
echo
echo "=== 10. VERIFY NO PUBLIC HEALTH LISTENER ==="
sudo ss -lntp | grep '127.0.0.1:8080'
if sudo ss -lnt | grep -Eq '(^|[[:space:]])(0\.0\.0\.0:8080|\[::\]:8080)([[:space:]]|$)'; then
  echo "SECURITY_FAIL: tunnel health endpoint is public"
  exit 123
else
  echo "PASS: tunnel health is loopback-only"
fi
echo
echo "=== 11. VERIFY SECRET SEPARATION ==="
if sudo -u botmarket-mcp test -r "$KEY_FILE" 2>/dev/null; then
  echo "SECURITY_FAIL: Reader can read tunnel key"
  exit 124
else
  echo "PASS: Reader cannot read tunnel key"
fi
echo
echo "=== 12. RECENT TUNNEL LOGS ==="
sudo journalctl -u botmarket-openai-tunnel.service -n 50 --no-pager
echo
echo "========== OPENAI SECURE MCP TUNNEL SERVICE PASS =========="
