#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

REPO="/var/lib/botmarket-github-control/repo"
STAGE="/home/botmarket/.local/share/botmarket/b15p2-bybit-source-census-v0.1.2-stage"
DATA_ROOT="/home/botmarket/sc001_data"
OUT_DIR="$DATA_ROOT/SC001_B15P2_BYBIT_DELISTING_SOURCE_CENSUS"
OUT="$OUT_DIR/sc001_b15p2_bybit_delisting_source_census_v0_1_1.json"
LOG="$OUT_DIR/networked_source_census_v0_1_2.log"
EXIT_FILE="$OUT_DIR/networked_source_census_v0_1_2.exit_code"
MARKER="$OUT_DIR/networked_source_census_v0_1_2.launch.json"

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

  echo "wrapper_version=0.1.2"

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

  python3 - "$REPO/$SELFTEST_RESULT_REL" <<'PY'
import json, sys
from pathlib import Path
obj=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert obj.get("status") == "B15P2_BYBIT_DELISTING_SOURCE_CENSUS_V011_SELF_TEST_PASS"
execution=obj.get("execution") or {}
assert execution.get("exit_code") == 0
assert execution.get("package_integrity_ok") is True
boundary=obj.get("boundary") or {}
for key in (
    "network_calls",
    "real_announcement_access",
    "real_instrument_access",
    "price_access",
    "external_reference_price_access",
    "basis_access",
    "pnl_access",
):
    assert boundary.get(key) is False, key
assert obj.get("binding_consequence") == "PREPARE_NETWORKED_SOURCE_ONLY_WRAPPER_V0_1_2_AGAINST_EXACT_V011_IMPLEMENTATION"
print("offline_selftest_prerequisite = PASS")
PY

  [[ ! -e "$MARKER" ]] || die "v012_one_shot_launch_marker_exists"
  [[ ! -e "$OUT" ]] || die "existing_canonical_result_forbidden"
  [[ ! -e "$EXIT_FILE" ]] || die "v012_existing_exit_file_forbidden"
  [[ ! -e "$LOG" ]] || die "v012_existing_log_forbidden"

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

  local helper="$STAGE/run-live-v0.1.2.sh"
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
  unit="sc001-b15p2-bybit-source-census-v012-$(date -u +%Y%m%dT%H%M%SZ)"

  local marker_tmp="$MARKER.tmp"
  cat > "$marker_tmp" <<EOF
{
  "schema": "sc001.b15p2_networked_source_census_launch_marker.v0.1.2",
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
      --description="SC001 B15-P2 Bybit source-only delisting census v0.1.2 wrapper" \
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

case "${1:-}" in
  --launch)
    launch
    ;;
  --status)
    show_status
    ;;
  *)
    echo "Usage:"
    echo "  sudo bash $0 --launch"
    echo "  sudo bash $0 --status"
    exit 2
    ;;
esac
