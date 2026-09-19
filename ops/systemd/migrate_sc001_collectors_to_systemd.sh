#!/usr/bin/env bash
set -euo pipefail

REPO="/home/botmarket/botmarketplace-site"
DATA="/home/botmarket/sc001_data"
OPS="$DATA/SC001_COLLECTOR_RESILIENCE"
EVENTS="$OPS/operational_events.jsonl"

if [[ "$(id -un)" != "botmarket" ]]; then
  echo "Run as botmarket." >&2
  exit 2
fi

mkdir -p "$OPS"
cd "$REPO"

echo "===== SELF-TEST B13-C v0.3 ====="
SC001_DATA_ROOT="$DATA" python3 -u research/sc001/sc001_b13c_bybit_prospective_liquidation_collector_v0_3.py --mode self-test

echo "===== SELF-TEST B14-A P0 v0.3 ====="
SC001_DATA_ROOT="$DATA" python3 -u research/sc001/sc001_b14a_p0_prospective_trade_collector_v0_3.py --mode self-test

echo "===== INSTALL/VERIFY SYSTEMD ====="
sudo install -m 0644 ops/systemd/sc001-b13c-liquidation.service /etc/systemd/system/sc001-b13c-liquidation.service
sudo install -m 0644 ops/systemd/sc001-b14a-p0.service /etc/systemd/system/sc001-b14a-p0.service
sudo systemctl daemon-reload
sudo systemd-analyze verify /etc/systemd/system/sc001-b13c-liquidation.service /etc/systemd/system/sc001-b14a-p0.service
sudo systemctl enable sc001-b13c-liquidation.service sc001-b14a-p0.service

STOP_MS="$(date +%s%3N)"
python3 - "$EVENTS" "$STOP_MS" <<'PY'
import json, sys
from datetime import datetime, timezone
from pathlib import Path
path=Path(sys.argv[1]); ts=int(sys.argv[2])
rec={"event":"PLANNED_SYSTEMD_MIGRATION_STOP","ts_ms":ts,"ts_utc":datetime.fromtimestamp(ts/1000,tz=timezone.utc).isoformat()}
path.parent.mkdir(parents=True,exist_ok=True)
with path.open("a",encoding="utf-8") as f:
    f.write(json.dumps(rec,separators=(",",":"))+"\n")
print(json.dumps(rec))
PY

echo "===== STOP OLD TMUX COLLECTORS ====="
for s in b13ccol b14ap0; do
  if tmux has-session -t "$s" 2>/dev/null; then
    tmux send-keys -t "$s" C-c
  fi
done

for _ in $(seq 1 20); do
  alive=0
  tmux has-session -t b13ccol 2>/dev/null && alive=1 || true
  tmux has-session -t b14ap0 2>/dev/null && alive=1 || true
  [[ "$alive" -eq 0 ]] && break
  sleep 1
done

for s in b13ccol b14ap0; do
  if tmux has-session -t "$s" 2>/dev/null; then
    echo "tmux $s did not exit gracefully; killing session after timeout"
    tmux kill-session -t "$s"
  fi
done

echo "===== START SYSTEMD COLLECTORS ====="
sudo systemctl start sc001-b13c-liquidation.service || true
sudo systemctl start sc001-b14a-p0.service || true

sleep 5

B13="$(systemctl is-active sc001-b13c-liquidation.service 2>/dev/null || true)"
B14="$(systemctl is-active sc001-b14a-p0.service 2>/dev/null || true)"
START_MS="$(date +%s%3N)"

python3 - "$EVENTS" "$STOP_MS" "$START_MS" "$B13" "$B14" <<'PY'
import json, sys
from datetime import datetime, timezone
from pathlib import Path
path=Path(sys.argv[1])
start=int(sys.argv[2]); end=int(sys.argv[3])
rec={
    "event":"PLANNED_SYSTEMD_MIGRATION_GAP",
    "start_ms":start,
    "end_ms":end,
    "duration_ms":max(0,end-start),
    "start_utc":datetime.fromtimestamp(start/1000,tz=timezone.utc).isoformat(),
    "end_utc":datetime.fromtimestamp(end/1000,tz=timezone.utc).isoformat(),
    "b13c_systemd_state":sys.argv[4],
    "b14a_systemd_state":sys.argv[5],
}
path.parent.mkdir(parents=True,exist_ok=True)
with path.open("a",encoding="utf-8") as f:
    f.write(json.dumps(rec,separators=(",",":"))+"\n")
print(json.dumps(rec,indent=2))
PY

echo "===== FINAL SERVICE STATUS ====="
systemctl --no-pager --full status sc001-b13c-liquidation.service 2>&1 | sed -n '1,14p' || true
echo
systemctl --no-pager --full status sc001-b14a-p0.service 2>&1 | sed -n '1,14p' || true

if [[ "$B13" != "active" || "$B14" != "active" ]]; then
  echo "Migration review required: one or both services are not active." >&2
  echo "--- B13-C recent systemd log ---" >&2
  tail -n 30 "$DATA/SC001_B13C_PROSPECTIVE_LIQUIDATIONS/systemd.log" 2>/dev/null >&2 || true
  echo "--- B14-A recent systemd log ---" >&2
  tail -n 30 "$DATA/SC001_B14A_P0_20260925/systemd.log" 2>/dev/null >&2 || true
  exit 3
fi

echo
echo "SC001_COLLECTOR_SYSTEMD_MIGRATION_PASS"
