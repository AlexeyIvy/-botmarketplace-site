#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

REPO="/var/lib/botmarket-github-control/repo"
STAGE="/home/botmarket/.local/share/botmarket/b15p2-bybit-source-census-v0.1.3-stage"
DATA_ROOT="/home/botmarket/sc001_data"
OUT_DIR="$DATA_ROOT/SC001_B15P2_BYBIT_DELISTING_SOURCE_CENSUS"
OUT="$OUT_DIR/sc001_b15p2_bybit_delisting_source_census_v0_1_1.json"
LOG="$OUT_DIR/networked_source_census_v0_1_3.log"
EXIT_FILE="$OUT_DIR/networked_source_census_v0_1_3.exit_code"
MARKER="$OUT_DIR/networked_source_census_v0_1_3.launch.json"

SCRIPT_REL="research/sc001/sc001_b15p2_bybit_delisting_source_census_v0_1_1.py"
PROTOCOL_REL="docs/research/sc001-b15p2-bybit-delisting-source-only-event-census-protocol-v0.1.md"
FREEZE_REL="docs/research/sc001-b15p2-bybit-delisting-source-census-implementation-freeze-v0.1.1.json"
SELFTEST_RESULT_REL="docs/research/sc001-b15p2-bybit-delisting-source-census-v011-offline-selftest-result-v0.1.json"
EXPECTED_SCRIPT_SHA="7da36641ed71e0195320f0cc7cc389d629d4f843a646f64c41c1739fc0cd6b35"
EXPECTED_PROTOCOL_SHA="ea577e42252b13fc5153256f3cc87c90d4518384cfd97254e4ddba06bbe611e2"
EXPECTED_FREEZE_SHA="693484fd882c3983c92a667793119df1815b6ca80672c672597e5f1c9ff0ec86"
EXPECTED_SELFTEST_RESULT_SHA="7cf4c91389be71415343d38b98520be7006c38907dafd908552eb1a47763efcd"

PASS="B15P2_BYBIT_DELISTING_SOURCE_CENSUS_PASS"
DEFER="B15P2_BYBIT_DELISTING_SOURCE_CENSUS_DEFER"
REVIEW="B15P2_BYBIT_DELISTING_SOURCE_CENSUS_REVIEW"
SELFTEST_PASS="B15P2_BYBIT_DELISTING_SOURCE_CENSUS_V011_SELF_TEST_PASS"

die() {
  echo "B15P2_NETWORKED_SOURCE_CENSUS_REVIEW"
  echo "reason=$1"
  echo "price_access_authorized=False"
  echo "basis_access_authorized=False"
  echo "pnl_authorized=False"
  exit 2
}

need_root() {
  [[ "${EUID:-$(id -u)}" -eq 0 ]] || die "wrapper_must_run_as_root"
}

check_tools() {
  local cmd
  for cmd in sha256sum awk stat install sudo python3 systemctl systemd-run date grep find wc chown chmod rm cat tail mv dirname env tee; do
    command -v "$cmd" >/dev/null 2>&1 || die "required_command_missing:$cmd"
  done
}

check_source() {
  local rel="$1"
  local expected="$2"
  local src="$REPO/$rel"
  [[ -f "$src" ]] || die "source_missing:$rel"
  [[ ! -L "$src" ]] || die "source_symlink_forbidden:$rel"
  local actual
  actual="$(sha256sum "$src" | awk '{print $1}')"
  [[ "$actual" == "$expected" ]] || die "source_sha_mismatch:$rel"
}

show_status() {
  need_root
  check_tools

  echo "wrapper_version=0.1.3"

  if [[ ! -f "$MARKER" ]]; then
    echo "launch_marker=ABSENT"
  else
    local unit
    unit="$(python3 - "$MARKER" <<'PY'
import json, sys
from pathlib import Path
obj=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(obj["unit"])
PY
)"
    echo "unit=$unit"
    if systemctl is-active --quiet "$unit"; then
      echo "execution_state=RUNNING"
    else
      echo "execution_state=NOT_RUNNING"
      systemctl show "$unit" -p Result -p ExecMainCode -p ExecMainStatus --no-pager 2>/dev/null || true
    fi
  fi

  if [[ -f "$EXIT_FILE" ]]; then
    echo "exit_code=$(cat "$EXIT_FILE")"
  else
    echo "exit_code=PENDING_OR_ABSENT"
  fi

  if [[ -f "$OUT" ]]; then
    python3 - "$OUT" "$PASS" "$DEFER" "$REVIEW" <<'PY'
import json, sys
from pathlib import Path
p=Path(sys.argv[1])
PASS=sys.argv[2]
DEFER=sys.argv[3]
obj=json.loads(p.read_text(encoding="utf-8"))
REVIEW=sys.argv[4]
assert obj.get("status") in {PASS, DEFER, REVIEW}
assert obj.get("price_accessed") is False
assert obj.get("basis_calculated") is False
assert obj.get("pnl_calculated") is False
assert obj.get("event_ranked_by_outcome") is False
print("result_status =", obj.get("status"))
print("closed_in_scope =", obj.get("closed_in_scope_count"))
print("admitted_events =", obj.get("admitted_event_count"))
print("coverage =", obj.get("announcement_match_coverage"))
print("delivery_months =", obj.get("delivery_months"))
print("lead_hours =", json.dumps(obj.get("lead_hours"), sort_keys=True))
print("gates =", json.dumps(obj.get("gates"), sort_keys=True))
print("source_integrity_issue_count =", obj.get("source_integrity_issue_count"))
print("error_type =", obj.get("error_type"))
print("error_message =", obj.get("error_message"))
print("price/basis/PnL = CLOSED")
print("result_path =", p)
PY
  else
    echo "result_status=PENDING_OR_REVIEW"
  fi

  if [[ -f "$LOG" ]]; then
    echo "--- persistent log tail ---"
    tail -n 60 "$LOG"
  else
    echo "persistent_log=ABSENT"
  fi
}

launch() {
  need_root
  check_tools

  [[ -d "$REPO" ]] || die "repo_missing"

  check_source "$SCRIPT_REL" "$EXPECTED_SCRIPT_SHA"
  check_source "$PROTOCOL_REL" "$EXPECTED_PROTOCOL_SHA"
  check_source "$FREEZE_REL" "$EXPECTED_FREEZE_SHA"
  check_source "$SELFTEST_RESULT_REL" "$EXPECTED_SELFTEST_RESULT_SHA"

  python3 - \
    "$REPO/$SELFTEST_RESULT_REL" \
    "$REPO/$FREEZE_REL" \
    "$EXPECTED_SCRIPT_SHA" \
    "$EXPECTED_PROTOCOL_SHA" <<'PY'
import json
import sys
from pathlib import Path

def load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"PRECHECK_JSON_READ_FAILED:{Path(path).name}:{type(exc).__name__}:{exc}")

def require(cond, code):
    if not cond:
        raise SystemExit(f"PRECHECK_FAILED:{code}")

st=load(sys.argv[1])
fr=load(sys.argv[2])
expected_script_sha=sys.argv[3]
expected_protocol_sha=sys.argv[4]

require(st.get("schema")=="sc001.b15p2_bybit_delisting_source_census_v011_offline_selftest_result.v0.1","SELFTEST_SCHEMA")
require(st.get("status")=="B15P2_BYBIT_DELISTING_SOURCE_CENSUS_V011_SELF_TEST_PASS","SELFTEST_STATUS")
execution=st.get("execution")
require(isinstance(execution,dict),"SELFTEST_EXECUTION_OBJECT")
require(execution.get("exit_code")==0,"SELFTEST_EXIT_CODE")
require(execution.get("package_integrity_ok") is True,"SELFTEST_PACKAGE_INTEGRITY")
require(execution.get("stderr_empty") is True,"SELFTEST_STDERR_EMPTY")
impl=st.get("implementation")
require(isinstance(impl,dict),"SELFTEST_IMPLEMENTATION_OBJECT")
require(impl.get("path")=="research/sc001/sc001_b15p2_bybit_delisting_source_census_v0_1_1.py","SELFTEST_IMPLEMENTATION_PATH")
require(impl.get("sha256")==expected_script_sha,"SELFTEST_IMPLEMENTATION_SHA")
boundary=st.get("boundary")
require(isinstance(boundary,dict),"SELFTEST_BOUNDARY_OBJECT")
for key in ("network_calls","real_announcement_access","real_instrument_access","price_access","basis_access","pnl_access"):
    require(key in boundary,f"SELFTEST_BOUNDARY_MISSING_{key.upper()}")
    require(boundary.get(key) is False,f"SELFTEST_BOUNDARY_{key.upper()}_NOT_FALSE")
require(st.get("networked_execution_authorized") is False,"SELFTEST_NETWORK_EXECUTION_NOT_FALSE")
require(st.get("binding_consequence")=="PREPARE_NETWORKED_SOURCE_ONLY_WRAPPER_V0_1_2_AGAINST_EXACT_V011_IMPLEMENTATION","SELFTEST_BINDING_CONSEQUENCE")

require(fr.get("schema")=="sc001.b15p2_bybit_delisting_source_census_implementation_freeze.v0.1.1","FREEZE_SCHEMA")
require(fr.get("status")=="FROZEN_PARSER_RESILIENCE_CORRECTION_BEFORE_RETRY","FREEZE_STATUS")
entry=fr.get("entrypoint")
require(isinstance(entry,dict),"FREEZE_ENTRYPOINT_OBJECT")
require(entry.get("path")=="research/sc001/sc001_b15p2_bybit_delisting_source_census_v0_1_1.py","FREEZE_ENTRYPOINT_PATH")
require(entry.get("sha256")==expected_script_sha,"FREEZE_ENTRYPOINT_SHA")
protocol=fr.get("protocol")
require(isinstance(protocol,dict),"FREEZE_PROTOCOL_OBJECT")
require(protocol.get("path")=="docs/research/sc001-b15p2-bybit-delisting-source-only-event-census-protocol-v0.1.md","FREEZE_PROTOCOL_PATH")
require(protocol.get("sha256")==expected_protocol_sha,"FREEZE_PROTOCOL_SHA")
require(protocol.get("changed") is False,"FREEZE_PROTOCOL_CHANGED")
for key in ("source_scope_changed","census_window_changed","gates_changed"):
    require(fr.get(key) is False,f"FREEZE_{key.upper()}_NOT_FALSE")
for key in ("price_access_authorized","external_reference_access_authorized","basis_access_authorized","pnl_authorized","event_outcome_ranking_authorized"):
    require(key in fr,f"FREEZE_MISSING_{key.upper()}")
    require(fr.get(key) is False,f"FREEZE_{key.upper()}_NOT_FALSE")
require(fr.get("expected_selftest_pass")=="B15P2_BYBIT_DELISTING_SOURCE_CENSUS_V011_SELF_TEST_PASS","FREEZE_EXPECTED_SELFTEST_PASS")

print("offline_contract_preflight = PASS")
print("price/basis/PnL/external-reference/outcome-ranking = CLOSED")
PY

  [[ ! -e "$MARKER" ]] || die "v013_one_shot_launch_marker_exists"
  [[ ! -e "$OUT" ]] || die "existing_canonical_result_forbidden"
  [[ ! -e "$EXIT_FILE" ]] || die "v013_existing_exit_file_forbidden"
  [[ ! -e "$LOG" ]] || die "v013_existing_log_forbidden"

  rm -rf "$STAGE"
  install -d -m 0750 -o botmarket -g botmarket "$STAGE"

  local files=("$SCRIPT_REL" "$PROTOCOL_REL" "$FREEZE_REL" "$SELFTEST_RESULT_REL")
  local shas=("$EXPECTED_SCRIPT_SHA" "$EXPECTED_PROTOCOL_SHA" "$EXPECTED_FREEZE_SHA" "$EXPECTED_SELFTEST_RESULT_SHA")
  local i rel expected src dst actual

  for i in "${!files[@]}"; do
    rel="${files[$i]}"
    expected="${shas[$i]}"
    src="$REPO/$rel"
    [[ -f "$src" ]] || die "stage_source_missing:$rel"
    [[ ! -L "$src" ]] || die "stage_source_symlink_forbidden:$rel"
    dst="$STAGE/$rel"
    install -d -m 0750 -o botmarket -g botmarket "$(dirname "$dst")"
    install -m 0640 -o botmarket -g botmarket "$src" "$dst"
    actual="$(sha256sum "$dst" | awk '{print $1}')"
    [[ "$actual" == "$expected" ]] || die "staged_sha_mismatch:$rel"
    sudo -u botmarket -H test -r "$dst" || die "staged_file_not_readable:$rel"
  done

  [[ -z "$(find "$STAGE" -type l -print -quit)" ]] || die "staging_symlink_detected"

  local staged_script="$STAGE/$SCRIPT_REL"
  local selftest_out
  if selftest_out="$(
    sudo -u botmarket -H env -i \
      HOME=/home/botmarket \
      PATH=/usr/bin:/bin \
      SC001_DATA_ROOT="$DATA_ROOT" \
      /usr/bin/python3 "$staged_script" --mode self-test 2>&1
  )"; then
    :
  else
    die "staged_selftest_failed"
  fi
  printf '%s\n' "$selftest_out"
  printf '%s\n' "$selftest_out" | grep -qx "$SELFTEST_PASS" || die "staged_selftest_pass_token_missing"

  install -d -m 0750 -o botmarket -g botmarket "$OUT_DIR"
  : > "$LOG"
  chown botmarket:botmarket "$LOG"
  chmod 0640 "$LOG"

  local helper="$STAGE/run-live-v0.1.3.sh"
  cat > "$helper" <<EOF
#!/usr/bin/env bash
set -Eeuo pipefail
umask 027
set +e
SC001_DATA_ROOT="$DATA_ROOT" /usr/bin/python3 "$staged_script" --mode live 2>&1 | /usr/bin/tee -a "$LOG"
rc="\${PIPESTATUS[0]}"
set -e
tmp="$EXIT_FILE.tmp"
printf '%s\\n' "\$rc" > "\$tmp"
mv "\$tmp" "$EXIT_FILE"
exit "\$rc"
EOF
  chown botmarket:botmarket "$helper"
  chmod 0750 "$helper"

  local unit
  unit="sc001-b15p2-bybit-source-census-v013-$(date -u +%Y%m%dT%H%M%SZ)"

  local marker_tmp="$MARKER.tmp"
  cat > "$marker_tmp" <<EOF
{
  "schema": "sc001.b15p2_networked_source_census_launch_marker.v0.1.3",
  "unit": "$unit",
  "script_sha256": "$EXPECTED_SCRIPT_SHA",
  "protocol_sha256": "$EXPECTED_PROTOCOL_SHA",
  "launched_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "observability_fix": "PRESERVE_LOG_EXIT_MARKER_AND_MIRROR_STDOUT_STDERR",
  "price_access_authorized": false,
  "basis_access_authorized": false,
  "pnl_authorized": false
}
EOF
  mv "$marker_tmp" "$MARKER"
  chown botmarket:botmarket "$MARKER"
  chmod 0640 "$MARKER"

  set +e
  systemd-run \
      --wait \
      --unit="$unit" \
      --description="SC001 B15-P2 Bybit source-only delisting census v0.1.3 wrapper" \
      --property=Type=oneshot \
      --property=TimeoutStartSec=900 \
      --property=RuntimeMaxSec=900 \
      --property=User=botmarket \
      --property=Group=botmarket \
      --property=NoNewPrivileges=yes \
      --property=PrivateTmp=yes \
      --property=PrivateDevices=yes \
      --property=ProtectSystem=strict \
      --property=ProtectKernelTunables=yes \
      --property=ProtectKernelModules=yes \
      --property=ProtectControlGroups=yes \
      --property=RestrictSUIDSGID=yes \
      --property=LockPersonality=yes \
      --property="RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6" \
      --property="ReadWritePaths=$OUT_DIR" \
      "$helper"
  local systemd_rc="$?"
  set -e

  if [[ "$systemd_rc" -ne 0 ]]; then
    echo "B15P2_NETWORKED_SOURCE_CENSUS_UNIT_FAILED"
    echo "systemd_run_rc=$systemd_rc"
    show_status || true
    die "networked_unit_failed_diagnostics_preserved"
  fi

  echo "B15P2_NETWORKED_SOURCE_CENSUS_UNIT_COMPLETED"
  show_status
}

preflight_only() {
  need_root
  check_tools
  [[ -d "$REPO" ]] || die "repo_missing"
  check_source "$SCRIPT_REL" "$EXPECTED_SCRIPT_SHA"
  check_source "$PROTOCOL_REL" "$EXPECTED_PROTOCOL_SHA"
  check_source "$FREEZE_REL" "$EXPECTED_FREEZE_SHA"
  check_source "$SELFTEST_RESULT_REL" "$EXPECTED_SELFTEST_RESULT_SHA"

  python3 - \
    "$REPO/$SELFTEST_RESULT_REL" \
    "$REPO/$FREEZE_REL" \
    "$EXPECTED_SCRIPT_SHA" \
    "$EXPECTED_PROTOCOL_SHA" <<'PY'
import json
import sys
from pathlib import Path

def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))

def require(cond, code):
    if not cond:
        raise SystemExit(f"PRECHECK_FAILED:{code}")

st=load(sys.argv[1])
fr=load(sys.argv[2])
script_sha=sys.argv[3]
protocol_sha=sys.argv[4]

require(st.get("schema")=="sc001.b15p2_bybit_delisting_source_census_v011_offline_selftest_result.v0.1","SELFTEST_SCHEMA")
require(st.get("status")=="B15P2_BYBIT_DELISTING_SOURCE_CENSUS_V011_SELF_TEST_PASS","SELFTEST_STATUS")
require((st.get("execution") or {}).get("exit_code")==0,"SELFTEST_EXIT")
require((st.get("execution") or {}).get("package_integrity_ok") is True,"SELFTEST_INTEGRITY")
require((st.get("execution") or {}).get("stderr_empty") is True,"SELFTEST_STDERR")
require((st.get("implementation") or {}).get("sha256")==script_sha,"SELFTEST_SCRIPT_SHA")
for key in ("network_calls","real_announcement_access","real_instrument_access","price_access","basis_access","pnl_access"):
    require((st.get("boundary") or {}).get(key) is False,f"SELFTEST_{key.upper()}")
require(st.get("networked_execution_authorized") is False,"SELFTEST_NETWORK_EXECUTION")
require((fr.get("entrypoint") or {}).get("sha256")==script_sha,"FREEZE_SCRIPT_SHA")
require((fr.get("protocol") or {}).get("sha256")==protocol_sha,"FREEZE_PROTOCOL_SHA")
for key in ("price_access_authorized","external_reference_access_authorized","basis_access_authorized","pnl_authorized","event_outcome_ranking_authorized"):
    require(fr.get(key) is False,f"FREEZE_{key.upper()}")
print("B15P2_NETWORKED_SOURCE_CENSUS_V013_PREFLIGHT_PASS")
print("network_calls_performed=False")
print("price/basis/PnL/external-reference/outcome-ranking=CLOSED")
PY
}

case "${1:-}" in
  --preflight)
    preflight_only
    ;;
  --launch)
    launch
    ;;
  --status)
    show_status
    ;;
  *)
    echo "Usage:"
    echo "  sudo bash $0 --preflight"
    echo "  sudo bash $0 --launch"
    echo "  sudo bash $0 --status"
    exit 2
    ;;
esac
