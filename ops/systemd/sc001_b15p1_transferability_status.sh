#!/usr/bin/env bash
set -u

SERVICE="sc001-b15p1-transferability.service"
ROOT="/home/botmarket/sc001_data/SC001_B15P1_TRANSFERABILITY"
STATE="$ROOT/collector_state.json"
MANIFEST="$ROOT/collector_manifest.json"
CAP="$ROOT/source_capability_snapshot.json"
AUTH="$ROOT/collector_launch_authorization.json"

echo "===== SC001 B15-P1 NON-PRICE COLLECTOR ====="
printf "service active="
systemctl is-active "$SERVICE" 2>/dev/null || true
printf "service enabled="
systemctl is-enabled "$SERVICE" 2>/dev/null || true

python3 - "$STATE" "$MANIFEST" "$CAP" "$AUTH" <<'PY'
import json
import sys
from pathlib import Path

state, manifest, cap, auth = map(Path, sys.argv[1:])
print()
print("===== FILE GATES =====")
for name, path in (
    ("state", state),
    ("manifest", manifest),
    ("capability", cap),
    ("launch_authorization", auth),
):
    print(f"{name} = {'PRESENT' if path.exists() else 'MISSING'}")

print()
print("===== STATE =====")
if not state.exists():
    print("collector_state = MISSING")
else:
    obj=json.loads(state.read_text())
    for k in (
        "stage","version","status","process_epoch","last_heartbeat_ms",
        "last_scheduled_slot_ms","poll_count","invalid_poll_count",
        "missed_poll_slots","source_gap_count","process_restart_count",
        "last_fee_refresh_completed_ms","price_data_collected","pnl_calculated",
    ):
        print(f"{k} = {obj.get(k)}")
PY

echo
echo "===== RECENT LOG ====="
tail -n 20 "$ROOT/systemd.log" 2>/dev/null || true
