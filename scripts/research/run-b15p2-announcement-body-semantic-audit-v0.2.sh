#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

REPO="/var/lib/botmarket-github-control/repo"
STAGE="/home/botmarket/.local/share/botmarket/b15p2-semantic-audit-v0.2-stage"
DATA_ROOT="/home/botmarket/sc001_data"
OUT_DIR="$DATA_ROOT/SC001_B15P2_ANNOUNCEMENT_SEMANTIC_AUDIT"
OUT="$OUT_DIR/sc001_b15p2_announcement_body_semantic_audit_v0_1.json"
LOG="$OUT_DIR/networked_semantic_audit_v0_2.log"
EXIT_FILE="$OUT_DIR/networked_semantic_audit_v0_2.exit_code"
MARKER="$OUT_DIR/networked_semantic_audit_v0_2.launch.json"

SCRIPT_REL="research/sc001/sc001_b15p2_announcement_body_semantic_audit_v0_1_3.py"
PROTOCOL_REL="docs/research/sc001-b15p2-announcement-body-semantic-audit-protocol-v0.1.md"
FREEZE_REL="docs/research/sc001-b15p2-announcement-body-semantic-audit-implementation-freeze-v0.1.3.json"
SELFTEST_RESULT_REL="docs/research/sc001-b15p2-announcement-body-semantic-audit-v013-offline-selftest-result-v0.1.json"
SOURCE_RESULT_REL="docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_result.v0.1.1.json"
EVENT_FREEZE_REL="docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_event_set_freeze.v0.1.json"

EXPECTED_SCRIPT_SHA="8a5ba89168dcd7845a7f340027e552767b41836b3c10755df00a6f9b7a309e78"
EXPECTED_PROTOCOL_SHA="4209779876e3796feff16a8310af93324cd1927862874524fb90ebf95d51d84f"
EXPECTED_FREEZE_SHA="175381cdff6873310405ffdf2ae3a3b2630e87a5c6ca0ad3f422ba45a85ba3b1"
EXPECTED_SELFTEST_RESULT_SHA="71d1f9cdffc2f8b02699b2c5b305f20b985dc7494e0373ca64c1303a9dcb4123"
EXPECTED_SOURCE_RESULT_SHA="c28aeb2b1ac0a23fb0e4420ced943fd619dd0a60e3fdcf5820299579cb94206c"
EXPECTED_EVENT_FREEZE_SHA="81952c83e7397481035cc00354388dfe3470ad17993c6e80665a7d376be907ed"
EXPECTED_EVENT_SET_SHA="1063695ec003a0d6789270659822f50577e6a0f07059d88ac03a5be4288ed1a2"

SELFTEST_PASS="B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_V013_SELF_TEST_PASS"
PASS="B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_PASS"
REVIEW="B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_REVIEW"

die() {
  echo "B15P2_SEMANTIC_AUDIT_HOST_REVIEW"
  echo "reason=$1"
  echo "price_access_authorized=False"
  echo "basis_access_authorized=False"
  echo "returns_access_authorized=False"
  echo "pnl_access_authorized=False"
  exit 2
}

need_root() {
  [[ "${EUID:-$(id -u)}" -eq 0 ]] || die "wrapper_must_run_as_root"
}

check_tools() {
  local cmd
  for cmd in sha256sum awk install sudo python3 systemctl systemd-run date grep find wc chown chmod rm cat tail mv dirname env tee; do
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

contract_preflight() {
  [[ -d "$REPO" ]] || die "repo_missing"

  check_source "$SCRIPT_REL" "$EXPECTED_SCRIPT_SHA"
  check_source "$PROTOCOL_REL" "$EXPECTED_PROTOCOL_SHA"
  check_source "$FREEZE_REL" "$EXPECTED_FREEZE_SHA"
  check_source "$SELFTEST_RESULT_REL" "$EXPECTED_SELFTEST_RESULT_SHA"
  check_source "$SOURCE_RESULT_REL" "$EXPECTED_SOURCE_RESULT_SHA"
  check_source "$EVENT_FREEZE_REL" "$EXPECTED_EVENT_FREEZE_SHA"

  python3 -     "$REPO/$SELFTEST_RESULT_REL"     "$REPO/$FREEZE_REL"     "$REPO/$EVENT_FREEZE_REL"     "$REPO/$SOURCE_RESULT_REL"     "$EXPECTED_SCRIPT_SHA"     "$EXPECTED_PROTOCOL_SHA"     "$EXPECTED_EVENT_SET_SHA" <<'PY'
import json
import sys
from pathlib import Path

def load(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"PRECHECK_JSON_READ_FAILED:{Path(p).name}:{type(exc).__name__}:{exc}")

def require(cond, code):
    if not cond:
        raise SystemExit(f"PRECHECK_FAILED:{code}")

st=load(sys.argv[1])
fr=load(sys.argv[2])
ef=load(sys.argv[3])
src=load(sys.argv[4])
script_sha=sys.argv[5]
protocol_sha=sys.argv[6]
event_set_sha=sys.argv[7]

require(st.get("schema")=="sc001.b15p2_announcement_body_semantic_audit_v013_offline_selftest_result.v0.1","SELFTEST_SCHEMA")
require(st.get("status")=="B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_V013_SELF_TEST_PASS","SELFTEST_STATUS")
execution=st.get("execution") or {}
require(execution.get("exit_code")==0,"SELFTEST_EXIT_CODE")
require(execution.get("package_integrity_ok") is True,"SELFTEST_PACKAGE_INTEGRITY")
require(execution.get("stderr_empty") is True,"SELFTEST_STDERR")
require((st.get("implementation") or {}).get("sha256")==script_sha,"SELFTEST_SCRIPT_SHA")
for key in ("network_calls","real_announcement_body_access","price_access","basis_access","returns_access","pnl_access"):
    require((st.get("boundary") or {}).get(key) is False,f"SELFTEST_{key.upper()}")
require(st.get("networked_execution_authorized") is False,"SELFTEST_NETWORK_AUTH")
require(st.get("binding_consequence")=="PREPARE_ASYNC_NETWORKED_94_PAGE_SEMANTIC_AUDIT_BOUNDARY","SELFTEST_CONSEQUENCE")

require(fr.get("schema")=="sc001.b15p2_announcement_body_semantic_audit_implementation_freeze.v0.1.3","FREEZE_SCHEMA")
require((fr.get("entrypoint") or {}).get("sha256")==script_sha,"FREEZE_SCRIPT_SHA")
require((fr.get("protocol") or {}).get("sha256")==protocol_sha,"FREEZE_PROTOCOL_SHA")
require((fr.get("frozen_input") or {}).get("event_set_sha256")==event_set_sha,"FREEZE_EVENT_SET_SHA")
require((fr.get("frozen_input") or {}).get("event_count")==94,"FREEZE_EVENT_COUNT")
require((fr.get("frozen_input") or {}).get("unique_announcement_url_count")==94,"FREEZE_URL_COUNT")
require((fr.get("semantic_invariants") or {}).get("classify_text_unchanged_from_v0_1_2") is True,"FREEZE_CLASSIFIER_INVARIANT")
require((fr.get("semantic_invariants") or {}).get("article_region_unchanged_from_v0_1_2") is True,"FREEZE_ARTICLE_REGION_INVARIANT")
require((fr.get("semantic_invariants") or {}).get("frozen_input_validation_unchanged_from_v0_1_2") is True,"FREEZE_INPUT_VALIDATION_INVARIANT")
for key in ("price_access_authorized","external_reference_price_access_authorized","index_value_access_authorized","basis_access_authorized","return_access_authorized","pnl_authorized","event_outcome_ranking_authorized"):
    require(fr.get(key) is False,f"FREEZE_{key.upper()}")

require(ef.get("status")=="B15P2_EXACT_ADMITTED_EVENT_SET_FROZEN","EVENT_FREEZE_STATUS")
require(ef.get("event_count")==94,"EVENT_FREEZE_COUNT")
require(ef.get("event_set_sha256")==event_set_sha,"EVENT_FREEZE_DIGEST")
require((ef.get("source_result") or {}).get("sha256")=="c28aeb2b1ac0a23fb0e4420ced943fd619dd0a60e3fdcf5820299579cb94206c","EVENT_FREEZE_SOURCE_SHA")
for key in ("price_accessed","basis_calculated","pnl_calculated","event_ranked_by_outcome"):
    require((ef.get("firewalls") or {}).get(key) is False,f"EVENT_FREEZE_{key.upper()}")

require(src.get("status")=="B15P2_BYBIT_DELISTING_SOURCE_CENSUS_PASS","SOURCE_STATUS")
require(src.get("admitted_event_count")==94,"SOURCE_EVENT_COUNT")
require(src.get("announcement_match_coverage")==1.0,"SOURCE_COVERAGE")
require(src.get("source_integrity_issue_count")==0,"SOURCE_INTEGRITY")
events=src.get("events")
require(isinstance(events,list) and len(events)==94,"SOURCE_EVENTS")
urls=[]
for i,e in enumerate(events):
    require(isinstance(e,dict),f"EVENT_{i}_OBJECT")
    au=e.get("announcement_urls")
    require(isinstance(au,list) and len(au)==1,f"EVENT_{i}_ONE_URL")
    urls.append(au[0])
require(len(set(urls))==94,"UNIQUE_URL_COUNT")
require(all(u.startswith("https://announcements.bybit.com/") for u in urls),"URL_HOST")
for key in ("price_accessed","basis_calculated","pnl_calculated","event_ranked_by_outcome","settlement_semantics_interpreted"):
    require(src.get(key) is False,f"SOURCE_{key.upper()}")

print("B15P2_SEMANTIC_AUDIT_NETWORK_V02_PREFLIGHT_PASS")
print("frozen_events=94")
print("unique_announcement_urls=94")
print("network_calls_performed=False")
print("price/basis/returns/PnL/index-values= CLOSED")
PY
}

show_status() {
  need_root
  check_tools
  echo "wrapper_version=0.2"

  if [[ -f "$MARKER" ]]; then
    local unit
    unit="$(python3 - "$MARKER" <<'PY'
import json,sys
from pathlib import Path
print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["unit"])
PY
)"
    echo "unit=$unit"
    local active_state sub_state
    active_state="$(systemctl show "$unit" -p ActiveState --value 2>/dev/null || true)"
    sub_state="$(systemctl show "$unit" -p SubState --value 2>/dev/null || true)"
    echo "systemd_active_state=${active_state:-UNKNOWN}"
    echo "systemd_sub_state=${sub_state:-UNKNOWN}"
    case "$active_state" in
      active|activating|reloading)
        echo "execution_state=RUNNING"
        ;;
      *)
        echo "execution_state=NOT_RUNNING"
        systemctl show "$unit" -p Result -p ExecMainCode -p ExecMainStatus --no-pager 2>/dev/null || true
        ;;
    esac
  else
    echo "launch_marker=ABSENT"
  fi

  if [[ -f "$EXIT_FILE" ]]; then
    echo "exit_code=$(cat "$EXIT_FILE")"
  else
    echo "exit_code=PENDING_OR_ABSENT"
  fi

  if [[ -f "$OUT" ]]; then
    python3 - "$OUT" "$PASS" "$REVIEW" "$EXPECTED_EVENT_SET_SHA" <<'PY'
import json,sys
from pathlib import Path
obj=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
PASS=sys.argv[2]
REVIEW=sys.argv[3]
event_set_sha=sys.argv[4]
status=obj.get("status")
assert status in {PASS,REVIEW}
if obj.get("frozen_event_set_sha256") is not None:
    assert obj.get("frozen_event_set_sha256")==event_set_sha
fw=obj.get("firewalls") or {}
for key,value in fw.items():
    if key.endswith(("accessed","calculated")) or key=="event_ranked_by_outcome":
        assert value is False,(key,value)
print("result_status =",status)
print("page_fetch_success =",obj.get("page_fetch_success_count"))
print("page_fetch_errors =",obj.get("page_fetch_error_count"))
print("exact_time_matches =",obj.get("exact_time_match_count"))
print("automatic_close_explicit =",obj.get("automatic_close_explicit_count"))
print("active_order_cancel_explicit =",obj.get("active_order_auto_cancel_explicit_count"))
print("trading_stop_explicit =",obj.get("trading_stop_explicit_count"))
print("basis_counts =",json.dumps(obj.get("closing_price_basis_counts"),sort_keys=True))
print("window_minute_counts =",json.dumps(obj.get("closing_price_window_minute_counts"),sort_keys=True))
print("funding_mentioned =",obj.get("funding_mentioned_count"))
print("revision_wording =",obj.get("revision_wording_count"))
print("unresolved_count =",len(obj.get("unresolved_symbols") or []))
print("time_mismatch_or_unresolved_count =",len(obj.get("time_mismatch_or_unresolved_symbols") or []))
print("error_type =",obj.get("error_type"))
print("error_message =",obj.get("error_message"))
print("price/basis/returns/PnL/index-values = CLOSED")
print("result_path =",sys.argv[1])
PY
  else
    echo "result_status=PENDING_OR_REVIEW"
  fi

  if [[ -f "$LOG" ]]; then
    local started done errors last_line
    started="$(grep -c '^EVENT_START ' "$LOG" 2>/dev/null || true)"
    done="$(grep -c '^EVENT_DONE ' "$LOG" 2>/dev/null || true)"
    errors="$(grep -c '^EVENT_ERROR ' "$LOG" 2>/dev/null || true)"
    last_line="$(grep -E '^(EVENT_START|EVENT_DONE|EVENT_ERROR|FETCH_RETRY) ' "$LOG" 2>/dev/null | tail -n 1 || true)"
    echo "progress_started=$started/94"
    echo "progress_done=$done/94"
    echo "progress_errors=$errors"
    [[ -n "$last_line" ]] && echo "last_progress=$last_line"
    echo "--- persistent log tail ---"
    tail -n 40 "$LOG"
  else
    echo "persistent_log=ABSENT"
  fi
}

preflight_only() {
  need_root
  check_tools
  contract_preflight
}

launch() {
  need_root
  check_tools
  contract_preflight

  [[ ! -e "$MARKER" ]] || die "one_shot_launch_marker_exists"
  [[ ! -e "$OUT" ]] || die "existing_result_forbidden"
  [[ ! -e "$EXIT_FILE" ]] || die "existing_exit_file_forbidden"
  [[ ! -e "$LOG" ]] || die "existing_log_forbidden"

  rm -rf "$STAGE"
  install -d -m 0750 -o botmarket -g botmarket "$STAGE"

  local files=(
    "$SCRIPT_REL"
    "$PROTOCOL_REL"
    "$FREEZE_REL"
    "$SELFTEST_RESULT_REL"
    "$SOURCE_RESULT_REL"
    "$EVENT_FREEZE_REL"
  )
  local shas=(
    "$EXPECTED_SCRIPT_SHA"
    "$EXPECTED_PROTOCOL_SHA"
    "$EXPECTED_FREEZE_SHA"
    "$EXPECTED_SELFTEST_RESULT_SHA"
    "$EXPECTED_SOURCE_RESULT_SHA"
    "$EXPECTED_EVENT_FREEZE_SHA"
  )

  local i rel expected src dst actual
  for i in "${!files[@]}"; do
    rel="${files[$i]}"
    expected="${shas[$i]}"
    src="$REPO/$rel"
    dst="$STAGE/$rel"
    install -d -m 0750 -o botmarket -g botmarket "$(dirname "$dst")"
    install -m 0640 -o botmarket -g botmarket "$src" "$dst"
    actual="$(sha256sum "$dst" | awk '{print $1}')"
    [[ "$actual" == "$expected" ]] || die "staged_sha_mismatch:$rel"
    sudo -u botmarket -H test -r "$dst" || die "staged_file_not_readable:$rel"
  done

  [[ -z "$(find "$STAGE" -type l -print -quit)" ]] || die "staging_symlink_detected"
  local stage_count
  stage_count="$(find "$STAGE" -type f | wc -l | awk '{print $1}')"
  [[ "$stage_count" == "6" ]] || die "unexpected_staging_file_count:$stage_count"

  local staged_script="$STAGE/$SCRIPT_REL"
  local selftest_out
  if selftest_out="$(
    sudo -u botmarket -H env -i       HOME=/home/botmarket       PATH=/usr/bin:/bin       B15P2_REPO_ROOT="$STAGE"       SC001_DATA_ROOT="$DATA_ROOT"       /usr/bin/python3 "$staged_script" --mode self-test 2>&1
  )"; then
    :
  else
    printf '%s
' "$selftest_out"
    die "staged_selftest_failed"
  fi
  printf '%s
' "$selftest_out"
  printf '%s
' "$selftest_out" | grep -qx "$SELFTEST_PASS" || die "staged_selftest_pass_token_missing"

  install -d -m 0750 -o botmarket -g botmarket "$OUT_DIR"
  : > "$LOG"
  chown botmarket:botmarket "$LOG"
  chmod 0640 "$LOG"

  local helper="$STAGE/run-live-semantic-v0.2.sh"
  cat > "$helper" <<EOF
#!/usr/bin/env bash
set -Eeuo pipefail
umask 027
set +e
env -i \
  HOME=/home/botmarket \
  PATH=/usr/bin:/bin \
  B15P2_REPO_ROOT="$STAGE" \
  SC001_DATA_ROOT="$DATA_ROOT" \
  /usr/bin/python3 "$staged_script" --mode live 2>&1 | /usr/bin/tee -a "$LOG"
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
  unit="sc001-b15p2-semantic-audit-v02-$(date -u +%Y%m%dT%H%M%SZ)"

  local marker_tmp="$MARKER.tmp"
  cat > "$marker_tmp" <<EOF
{
  "schema": "sc001.b15p2_semantic_audit_launch_marker.v0.2",
  "unit": "$unit",
  "script_sha256": "$EXPECTED_SCRIPT_SHA",
  "protocol_sha256": "$EXPECTED_PROTOCOL_SHA",
  "source_result_sha256": "$EXPECTED_SOURCE_RESULT_SHA",
  "event_set_sha256": "$EXPECTED_EVENT_SET_SHA",
  "frozen_event_count": 94,
  "execution_mode": "ASYNC_SYSTEMD_NO_BLOCK",
  "runtime_bound_seconds": 7200,
  "progress_semantics_exposed": false,
  "launched_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "price_access_authorized": false,
  "external_reference_price_access_authorized": false,
  "index_value_access_authorized": false,
  "basis_access_authorized": false,
  "returns_access_authorized": false,
  "pnl_authorized": false
}
EOF
  mv "$marker_tmp" "$MARKER"
  chown botmarket:botmarket "$MARKER"
  chmod 0640 "$MARKER"

  set +e
  systemd-run \
      --no-block \
      --unit="$unit" \
      --description="SC001 B15-P2 frozen 94-page announcement semantic audit v0.2" \
      --property=Type=oneshot \
      --property=TimeoutStartSec=7200 \
      --property=RuntimeMaxSec=7200 \
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
    show_status || true
    die "async_systemd_launch_failed"
  fi

  echo "B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_ASYNC_LAUNCHED"
  echo "unit=$unit"
  echo "termux_prompt_can_return=True"
  echo "status_command=sudo bash $REPO/scripts/research/run-b15p2-announcement-body-semantic-audit-v0.2.sh --status"
  echo "price/basis/returns/PnL/index-values = CLOSED"

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
