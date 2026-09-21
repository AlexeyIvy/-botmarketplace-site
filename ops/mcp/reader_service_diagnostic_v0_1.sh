#!/usr/bin/env bash
set -uo pipefail

SERVICE="botmarket-reader-mcp.service"
PORT="8765"
APP="/opt/botmarket-research/app/reader_server.py"
PY="/opt/botmarket-research/venv/bin/python"

echo "========== BOTMARKET READER MCP DIAGNOSTIC v0.1 =========="
date -u

echo
echo "=== A. SYSTEMD STATE ==="
sudo systemctl show "$SERVICE" \
  -p ActiveState -p SubState -p MainPID -p ExecMainCode -p ExecMainStatus \
  -p NRestarts -p Result --no-pager || true

PID="$(systemctl show -p MainPID --value "$SERVICE" 2>/dev/null || true)"
echo "main_pid=$PID"

echo
echo "=== B. JOURNAL ==="
sudo journalctl -u "$SERVICE" -n 120 --no-pager -o short-iso || true

echo
echo "=== C. HOST SOCKETS ==="
sudo ss -lntp || true

echo
echo "=== D. PORT-SPECIFIC SOCKET ==="
sudo ss -lntp | grep -E "(:$PORT[[:space:]]|:$PORT$)" || echo "NO_HOST_LISTENER_$PORT"

echo
echo "=== E. HTTP PROBE ==="
if command -v curl >/dev/null 2>&1; then
  curl --max-time 3 -sS -D - \
    -o /tmp/botmarket_reader_probe_body.$$ \
    "http://127.0.0.1:$PORT/mcp" || true
  rm -f /tmp/botmarket_reader_probe_body.$$
else
  echo "curl not installed"
fi

echo
echo "=== F. PROCESS / NETWORK NAMESPACE ==="
if [ -n "$PID" ] && [ "$PID" != "0" ] && [ -d "/proc/$PID" ]; then
  sudo ps -o pid,ppid,user,group,stat,etime,wchan:32,cmd -p "$PID" || true
  echo -n "init_netns = "; sudo readlink /proc/1/ns/net || true
  echo -n "svc_netns  = "; sudo readlink "/proc/$PID/ns/net" || true

  if command -v nsenter >/dev/null 2>&1; then
    echo "--- sockets visible inside service netns ---"
    sudo nsenter -t "$PID" -n ss -lntp || true
  fi

  echo "--- process fd summary ---"
  sudo ls -l "/proc/$PID/fd" 2>/dev/null | head -80 || true
else
  echo "service process is not alive"
fi

echo
echo "=== G. READER SOURCE STARTUP TAIL ==="
tail -40 "$APP" || true

echo
echo "=== H. UNIT EFFECTIVE CONTENT ==="
sudo systemctl cat "$SERVICE" --no-pager || true

echo
echo "=== I. BARE USER LOOPBACK BIND TEST (PORT 8766) ==="
sudo -u botmarket-mcp "$PY" - <<'PY'
import socket
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
s.bind(("127.0.0.1",8766))
s.listen(1)
print("PASS_BARE_BIND_127_0_0_1_8766")
s.close()
PY
BARE_RC=$?
echo "bare_bind_rc=$BARE_RC"

echo
echo "=== J. SYSTEMD IP POLICY BIND TEST (PORT 8767) ==="
TMP_UNIT="botmarket-mcp-bindtest-$(date +%s)"
if sudo systemd-run \
    --quiet \
    --wait \
    --collect \
    --unit="$TMP_UNIT" \
    --uid=botmarket-mcp \
    --property=IPAddressDeny=any \
    --property=IPAddressAllow=localhost \
    --property='RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6' \
    "$PY" -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",8767));s.listen(1);print("PASS_SYSTEMD_IP_POLICY_BIND_8767")'
then
    echo "systemd_ip_policy_bind_rc=0"
else
    echo "systemd_ip_policy_bind_rc=NONZERO"
fi

echo
echo "=== K. DIRECT MCP START TEST OUTSIDE SYSTEMD ==="
echo "Temporarily stopping Reader service for an isolated 8-second direct test."
sudo systemctl stop "$SERVICE" || true

DIRECT_LOG="/tmp/botmarket-reader-direct-test.$$.log"
sudo -u botmarket-mcp env \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  timeout 8s "$PY" "$APP" >"$DIRECT_LOG" 2>&1 &
DIRECT_WRAPPER_PID=$!

DIRECT_LISTEN=FAIL
for _ in $(seq 1 40); do
    if ss -lnt 2>/dev/null | grep -Eq "127\.0\.0\.1:$PORT([[:space:]]|$)"; then
        DIRECT_LISTEN=PASS
        break
    fi
    sleep 0.25
done

if [ "$DIRECT_LISTEN" = "PASS" ]; then
    echo "PASS_DIRECT_MCP_LISTENER_$PORT"
else
    echo "FAIL_DIRECT_MCP_NO_LISTENER_$PORT"
fi

echo "--- direct MCP output ---"
cat "$DIRECT_LOG" || true

wait "$DIRECT_WRAPPER_PID" 2>/dev/null || true
rm -f "$DIRECT_LOG"

echo
echo "=== L. RESTORE SERVICE ==="
sudo systemctl start "$SERVICE" || true
sleep 2
sudo systemctl show "$SERVICE" -p ActiveState -p SubState -p MainPID -p NRestarts -p Result --no-pager || true

echo
echo "=== M. DIAGNOSTIC SUMMARY ==="
if [ "$BARE_RC" -eq 0 ]; then
    echo "bare_bind=PASS"
else
    echo "bare_bind=FAIL"
fi
echo "direct_mcp_listener=$DIRECT_LISTEN"

if [ "$BARE_RC" -ne 0 ]; then
    echo "LIKELY_CLASS=OS_OR_USER_SOCKET_BIND"
elif [ "$DIRECT_LISTEN" = "FAIL" ]; then
    echo "LIKELY_CLASS=MCP_APPLICATION_STARTUP"
else
    echo "LIKELY_CLASS=SYSTEMD_SANDBOX_OR_UNIT_POLICY"
fi

echo "========== DIAGNOSTIC COMPLETE =========="
