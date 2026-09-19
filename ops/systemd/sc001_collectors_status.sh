#!/usr/bin/env bash
set -u

echo "===== SC001 SYSTEMD COLLECTORS ====="
for svc in sc001-b13c-liquidation.service sc001-b14a-p0.service; do
  printf "%-38s " "$svc"
  systemctl is-active "$svc" 2>/dev/null || true
  printf "  enabled="
  systemctl is-enabled "$svc" 2>/dev/null || true
done

echo
echo "===== B13-C STATE ====="
python3 - <<'PY'
import json
from pathlib import Path
p=Path("/home/botmarket/sc001_data/SC001_B13C_PROSPECTIVE_LIQUIDATIONS/collector_state.json")
if not p.exists():
    print("state: MISSING")
else:
    j=json.loads(p.read_text())
    for k in (
        "stage","status","connection_status","source_qualified_symbols",
        "last_heartbeat_ms","reconnect_count","cumulative_gap_ms",
        "process_restart_count","cumulative_process_gap_ms",
        "total_raw_messages","total_normalized_events","invalid_event_count"
    ):
        print(f"{k} = {j.get(k)}")
PY

echo
echo "===== B14-A P0 STATE ====="
python3 - <<'PY'
import json
from pathlib import Path
p=Path("/home/botmarket/sc001_data/SC001_B14A_P0_20260925/collector_state.json")
if not p.exists():
    print("state: MISSING")
else:
    j=json.loads(p.read_text())
    for k in (
        "stage","status","last_heartbeat_ms","subscription_ack",
        "process_restart_count","reconnect_count",
        "raw_trade_messages","normalized_trade_rows","invalid_trade_rows",
        "basis_calculated","convergence_calculated","pnl_calculated"
    ):
        print(f"{k} = {j.get(k)}")
PY

echo
echo "===== RECENT SYSTEMD LOGS ====="
echo "--- B13-C ---"
tail -n 12 /home/botmarket/sc001_data/SC001_B13C_PROSPECTIVE_LIQUIDATIONS/systemd.log 2>/dev/null || true
echo "--- B14-A ---"
tail -n 12 /home/botmarket/sc001_data/SC001_B14A_P0_20260925/systemd.log 2>/dev/null || true
