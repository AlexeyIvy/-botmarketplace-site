#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

REPO="/var/lib/botmarket-github-control/repo"
STAGE="/home/botmarket/.local/share/botmarket/b15p2-semantic-audit-v0.3-stage"
DATA_ROOT="/home/botmarket/sc001_data"
OUT_DIR="$DATA_ROOT/SC001_B15P2_ANNOUNCEMENT_SEMANTIC_AUDIT"
OUT="$OUT_DIR/sc001_b15p2_announcement_body_semantic_audit_v0_1_4.json"
SMOKE_OUT="$OUT_DIR/sc001_b15p2_announcement_body_transport_smoke_v0_1_4.json"
LOG="$OUT_DIR/networked_semantic_audit_v0_3.log"
EXIT_FILE="$OUT_DIR/networked_semantic_audit_v0_3.exit_code"
MARKER="$OUT_DIR/networked_semantic_audit_v0_3.launch.json"

SCRIPT_REL="research/sc001/sc001_b15p2_announcement_body_semantic_audit_v0_1_4.py"
PROTOCOL_REL="docs/research/sc001-b15p2-announcement-body-semantic-audit-protocol-v0.1.md"
FREEZE_REL="docs/research/sc001-b15p2-announcement-body-semantic-audit-implementation-freeze-v0.1.4.json"
SELFTEST_RESULT_REL="docs/research/sc001-b15p2-announcement-body-semantic-audit-v014-offline-selftest-result-v0.1.json"
SOURCE_RESULT_REL="docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_result.v0.1.1.json"
EVENT_FREEZE_REL="docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_event_set_freeze.v0.1.json"
TRANSPORT_RESULT_REL="docs/research/sc001-b15p2-announcement-html-transport-probe-v03-result-v0.1.json"

EXPECTED_SCRIPT_SHA="ca96be6b0cb8cae3a37fedb1a22fa2b426f5286ca3decdf7c272bf7cd29feceb"
EXPECTED_PROTOCOL_SHA="4209779876e3796feff16a8310af93324cd1927862874524fb90ebf95d51d84f"
EXPECTED_FREEZE_SHA="ff30f3a599b76995dad57ed8ab145597487cc0c6e14487f96e20908119f029cc"
EXPECTED_SELFTEST_RESULT_SHA="8fa053319833cbb78be66a9dc4dc8b9ea89be417ffd8bb8703616dbb30447687"
EXPECTED_SOURCE_RESULT_SHA="c28aeb2b1ac0a23fb0e4420ced943fd619dd0a60e3fdcf5820299579cb94206c"
EXPECTED_EVENT_FREEZE_SHA="81952c83e7397481035cc00354388dfe3470ad17993c6e80665a7d376be907ed"
EXPECTED_TRANSPORT_RESULT_SHA="97498ed8f60ab119d5a547a449d1e449366c4226d55442ed8d7abb0d1ba39e6f"
EXPECTED_EVENT_SET_SHA="1063695ec003a0d6789270659822f50577e6a0f07059d88ac03a5be4288ed1a2"

SELFTEST_PASS="B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_V014_SELF_TEST_PASS"
SMOKE_PASS="B15P2_ANNOUNCEMENT_BODY_TRANSPORT_SMOKE_V014_PASS"
PASS="B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_PASS"
REVIEW="B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_REVIEW"

die() {
  echo "B15P2_SEMANTIC_AUDIT_HOST_REVIEW"
  echo "reason=$1"
  echo "price_access_authorized=False"
  echo "external_reference_price_access_authorized=False"
  echo "index_value_access_authorized=False"
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
  for cmd in sha256sum awk install sudo python3 curl systemctl systemd-run date grep find wc chown chmod rm cat tail mv dirname env tee test; do
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
  check_source "$TRANSPORT_RESULT_REL" "$EXPECTED_TRANSPORT_RESULT_SHA"

  python3 -     "$REPO/$SELFTEST_RESULT_REL"     "$REPO/$FREEZE_REL"     "$REPO/$EVENT_FREEZE_REL"     "$REPO/$SOURCE_RESULT_REL"     "$REPO/$TRANSPORT_RESULT_REL"     "$EXPECTED_SCRIPT_SHA"     "$EXPECTED_PROTOCOL_SHA"     "$EXPECTED_EVENT_SET_SHA" <<'PY'
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
tr_result=load(sys.argv[5])
script_sha=sys.argv[6]
protocol_sha=sys.argv[7]
event_set_sha=sys.argv[8]

require(st.get("schema")=="sc001.b15p2_announcement_body_semantic_audit_v014_offline_selftest_result.v0.1","SELFTEST_SCHEMA")
require(st.get("status")=="B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_V014_SELF_TEST_PASS","SELFTEST_STATUS")
execution=st.get("execution") or {}
require(execution.get("exit_code")==0,"SELFTEST_EXIT_CODE")
require(execution.get("package_integrity_ok") is True,"SELFTEST_PACKAGE_INTEGRITY")
require(execution.get("stderr_empty") is True,"SELFTEST_STDERR")
require((st.get("implementation") or {}).get("sha256")==script_sha,"SELFTEST_SCRIPT_SHA")
for key in ("network_calls","real_announcement_body_access","price_access","basis_access","returns_access","pnl_access"):
    require((st.get("boundary") or {}).get(key) is False,f"SELFTEST_{key.upper()}")
require(st.get("networked_execution_authorized") is False,"SELFTEST_NETWORK_AUTH")
require(st.get("binding_consequence")=="FREEZE_NETWORKED_BOUNDARY_WITH_AUTOMATIC_TWO_PAGE_SMOKE_THEN_94","SELFTEST_CONSEQUENCE")

require(tr_result.get("schema")=="sc001.b15p2_announcement_html_transport_probe_v03_result.v0.1","TRANSPORT_RESULT_SCHEMA")
require(tr_result.get("status")=="B15P2_ANNOUNCEMENT_HTML_TRANSPORT_PROBE_COMPLETE","TRANSPORT_RESULT_STATUS")
require(tr_result.get("observed_pattern")=="CURL_HTML_WORKS_URLLIB_HTML_FAILS","TRANSPORT_OBSERVED_PATTERN")
minimal=tr_result.get("minimal_transport_fix") or {}
require(minimal.get("client")=="curl","TRANSPORT_RESULT_CLIENT")
require(minimal.get("address_family")=="IPv4","TRANSPORT_RESULT_FAMILY")
require(minimal.get("http_version")=="HTTP/1.1","TRANSPORT_RESULT_HTTP")
require(minimal.get("user_agent")=="browser-like","TRANSPORT_RESULT_UA")
require(tr_result.get("semantic_classification_performed") is False,"TRANSPORT_RESULT_NO_SEMANTICS")
for key in ("price_accessed","external_reference_price_accessed","index_value_accessed","basis_accessed","returns_accessed","pnl_accessed"):
    require(tr_result.get(key) is False,f"TRANSPORT_RESULT_{key.upper()}")

require(fr.get("schema")=="sc001.b15p2_announcement_body_semantic_audit_implementation_freeze.v0.1.4","FREEZE_SCHEMA")
require((fr.get("entrypoint") or {}).get("sha256")==script_sha,"FREEZE_SCRIPT_SHA")
require((fr.get("protocol") or {}).get("sha256")==protocol_sha,"FREEZE_PROTOCOL_SHA")
require((fr.get("protocol") or {}).get("changed") is False,"FREEZE_PROTOCOL_CHANGED")
sinv=fr.get("semantic_invariants") or {}
require(sinv.get("classify_text_unchanged_from_v0_1_3") is True,"FREEZE_CLASSIFIER_INVARIANT")
require(sinv.get("article_region_unchanged_from_v0_1_3") is True,"FREEZE_ARTICLE_REGION_INVARIANT")
require(sinv.get("frozen_input_validation_unchanged_from_v0_1_3") is True,"FREEZE_INPUT_VALIDATION_INVARIANT")
require(sinv.get("event_set_unchanged") is True,"FREEZE_EVENT_SET_INVARIANT")
require(sinv.get("pass_review_rules_unchanged") is True,"FREEZE_PASS_REVIEW_INVARIANT")

transport=fr.get("acquisition_transport") or {}
require(transport.get("client")=="curl","TRANSPORT_CLIENT")
require(transport.get("address_family")=="IPv4","TRANSPORT_FAMILY")
require(transport.get("http_version")=="HTTP/1.1","TRANSPORT_HTTP")
require(transport.get("user_agent")=="browser-like","TRANSPORT_UA")
require(transport.get("proxy") is False,"TRANSPORT_PROXY")
require(transport.get("https_only") is True,"TRANSPORT_HTTPS")
require(transport.get("same_host_redirects_only") is True,"TRANSPORT_REDIRECT")
require(transport.get("connect_timeout_seconds")==5,"TRANSPORT_CONNECT_TIMEOUT")
require(transport.get("total_timeout_seconds")==15,"TRANSPORT_TOTAL_TIMEOUT")
require(transport.get("attempts_per_url")==2,"TRANSPORT_ATTEMPTS")
require(transport.get("max_html_bytes")==2000000,"TRANSPORT_BODY_CAP")

smoke=fr.get("mandatory_network_smoke_before_full_94") or {}
require(smoke.get("event_symbols")==["DOGUSDT","TONUSDT"],"SMOKE_EVENTS")
require(smoke.get("semantic_classification_performed") is False,"SMOKE_NO_SEMANTICS")
require(smoke.get("full_94_may_start_only_after_smoke_pass") is True,"SMOKE_GATE")

fin=fr.get("frozen_input") or {}
require(fin.get("event_set_sha256")==event_set_sha,"FREEZE_EVENT_SET_SHA")
require(fin.get("event_count")==94,"FREEZE_EVENT_COUNT")
require(fin.get("unique_announcement_url_count")==94,"FREEZE_URL_COUNT")
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
symbols=[]
for i,e in enumerate(events):
    require(isinstance(e,dict),f"EVENT_{i}_OBJECT")
    au=e.get("announcement_urls")
    require(isinstance(au,list) and len(au)==1,f"EVENT_{i}_ONE_URL")
    urls.append(au[0])
    symbols.append(e.get("symbol"))
require(len(set(urls))==94,"UNIQUE_URL_COUNT")
require(all(u.startswith("https://announcements.bybit.com/") for u in urls),"URL_HOST")
require(symbols.count("DOGUSDT")==1,"DOG_EVENT_COUNT")
require(symbols.count("TONUSDT")==1,"TON_EVENT_COUNT")
for key in ("price_accessed","basis_calculated","pnl_calculated","event_ranked_by_outcome","settlement_semantics_interpreted"):
    require(src.get(key) is False,f"SOURCE_{key.upper()}")

print("B15P2_SEMANTIC_AUDIT_NETWORK_V03_PREFLIGHT_PASS")
print("frozen_events=94")
print("unique_announcement_urls=94")
print("smoke_gate=DOGUSDT,TONUSDT")
print("network_calls_performed=False")
print("price/basis/returns/PnL/index-values=CLOSED")
PY
}

validate_smoke_result() {
  [[ -f "$SMOKE_OUT" ]] || die "smoke_result_missing"
  python3 - "$SMOKE_OUT" <<'PY'
import json,sys,urllib.parse
from pathlib import Path

obj=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
def require(cond,code):
    if not cond:
        raise SystemExit(f"SMOKE_PRECHECK_FAILED:{code}")

require(obj.get("schema")=="sc001.b15p2_announcement_body_transport_smoke.v0.1.4","SCHEMA")
require(obj.get("status")=="B15P2_ANNOUNCEMENT_BODY_TRANSPORT_SMOKE_V014_PASS","STATUS")
tr=obj.get("transport") or {}
require(tr.get("client")=="curl","CLIENT")
require(tr.get("address_family")=="IPv4","FAMILY")
require(tr.get("http_version")=="HTTP/1.1","HTTP")
require(tr.get("user_agent")=="browser-like","UA")
require(tr.get("proxy") is False,"PROXY")
require(tr.get("same_host_redirects_only") is True,"REDIRECT")

rows=obj.get("events")
require(isinstance(rows,list) and len(rows)==2,"EVENT_COUNT")
require([r.get("symbol") for r in rows]==["DOGUSDT","TONUSDT"],"EVENT_ORDER")
for i,r in enumerate(rows):
    require(r.get("exact_title_present") is True,f"TITLE_{i}")
    require(isinstance(r.get("raw_html_bytes"),int) and 0<r["raw_html_bytes"]<=2000000,f"BODY_SIZE_{i}")
    require(isinstance(r.get("article_region_length"),int) and r["article_region_length"]>=120,f"REGION_LENGTH_{i}")
    final=r.get("final_url") or ""
    p=urllib.parse.urlparse(final)
    require(p.scheme=="https" and p.hostname=="announcements.bybit.com",f"FINAL_URL_{i}")
    for key in ("raw_html_sha256","normalized_text_sha256","article_region_sha256"):
        v=r.get(key)
        require(isinstance(v,str) and len(v)==64 and all(c in "0123456789abcdef" for c in v),f"{key}_{i}")

require(obj.get("semantic_classification_performed") is False,"NO_SEMANTICS")
for key in ("price_accessed","external_reference_price_accessed","index_value_accessed","basis_accessed","returns_accessed","pnl_accessed"):
    require(obj.get(key) is False,key.upper())
print("B15P2_TRANSPORT_SMOKE_RESULT_VALIDATED")
PY
}

show_status() {
  need_root
  check_tools
  echo "wrapper_version=0.3"

  if [[ -f "$SMOKE_OUT" ]]; then
    python3 - "$SMOKE_OUT" <<'PY'
import json,sys
from pathlib import Path
try:
    o=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print("smoke_status =",o.get("status"))
    print("smoke_events =",len(o.get("events") or []))
except Exception as exc:
    print("smoke_status = INVALID",type(exc).__name__,exc)
PY
  else
    echo "smoke_status=ABSENT"
  fi

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
tr=obj.get("acquisition_transport") or {}
assert tr.get("client")=="curl"
assert tr.get("address_family")=="IPv4"
assert tr.get("http_version")=="HTTP/1.1"
assert tr.get("proxy") is False
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
print("price/basis/returns/PnL/index-values=CLOSED")
print("result_path =",sys.argv[1])
PY
  else
    echo "result_status=PENDING_OR_REVIEW"
  fi

  if [[ -f "$LOG" ]]; then
    local started done errors retries last_line
    started="$(grep -c '^EVENT_START ' "$LOG" 2>/dev/null || true)"
    done="$(grep -c '^EVENT_DONE ' "$LOG" 2>/dev/null || true)"
    errors="$(grep -c '^EVENT_ERROR ' "$LOG" 2>/dev/null || true)"
    retries="$(grep -c '^FETCH_RETRY ' "$LOG" 2>/dev/null || true)"
    last_line="$(grep -E '^(EVENT_START|EVENT_DONE|EVENT_ERROR|FETCH_RETRY) ' "$LOG" 2>/dev/null | tail -n 1 || true)"
    echo "progress_started=$started/94"
    echo "progress_done=$done/94"
    echo "progress_errors=$errors"
    echo "progress_retries=$retries"
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
  [[ ! -e "$SMOKE_OUT" ]] || die "existing_smoke_result_forbidden"
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
    printf '%s\n' "$selftest_out"
    die "staged_selftest_failed"
  fi
  printf '%s\n' "$selftest_out"
  printf '%s\n' "$selftest_out" | grep -qx "$SELFTEST_PASS" || die "staged_selftest_pass_token_missing"

  install -d -m 0750 -o botmarket -g botmarket "$OUT_DIR"
  : > "$LOG"
  chown botmarket:botmarket "$LOG"
  chmod 0640 "$LOG"

  echo "B15P2_TRANSPORT_SMOKE_START"
  set +e
  sudo -u botmarket -H env -i     HOME=/home/botmarket     PATH=/usr/bin:/bin     B15P2_REPO_ROOT="$STAGE"     SC001_DATA_ROOT="$DATA_ROOT"     /usr/bin/python3 "$staged_script" --mode transport-smoke 2>&1 | /usr/bin/tee -a "$LOG"
  local smoke_rc="${PIPESTATUS[0]}"
  set -e

  if [[ "$smoke_rc" -ne 0 ]]; then
    echo "B15P2_TRANSPORT_SMOKE_FAILED"
    echo "smoke_exit_code=$smoke_rc"
    die "transport_smoke_failed_full_94_not_started"
  fi

  grep -qx "$SMOKE_PASS" "$LOG" || die "transport_smoke_pass_token_missing"
  validate_smoke_result
  echo "B15P2_TRANSPORT_SMOKE_GATE_PASS"

  local helper="$STAGE/run-live-semantic-v0.3.sh"
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
  unit="sc001-b15p2-semantic-audit-v03-$(date -u +%Y%m%dT%H%M%SZ)"

  local marker_tmp="$MARKER.tmp"
  cat > "$marker_tmp" <<EOF
{
  "schema": "sc001.b15p2_semantic_audit_launch_marker.v0.3",
  "unit": "$unit",
  "script_sha256": "$EXPECTED_SCRIPT_SHA",
  "protocol_sha256": "$EXPECTED_PROTOCOL_SHA",
  "source_result_sha256": "$EXPECTED_SOURCE_RESULT_SHA",
  "event_set_sha256": "$EXPECTED_EVENT_SET_SHA",
  "frozen_event_count": 94,
  "execution_mode": "ASYNC_SYSTEMD_NO_BLOCK_AFTER_REQUIRED_TWO_PAGE_SMOKE",
  "transport": "curl_ipv4_http11_browser_ua",
  "transport_smoke_status": "PASS",
  "runtime_bound_seconds": 4200,
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
  systemd-run       --no-block       --unit="$unit"       --description="SC001 B15-P2 frozen 94-page semantic audit v0.3 curl transport"       --property=Type=oneshot       --property=TimeoutStartSec=4200       --property=RuntimeMaxSec=4200       --property=User=botmarket       --property=Group=botmarket       --property=NoNewPrivileges=yes       --property=PrivateTmp=yes       --property=PrivateDevices=yes       --property=ProtectSystem=strict       --property=ProtectKernelTunables=yes       --property=ProtectKernelModules=yes       --property=ProtectControlGroups=yes       --property=RestrictSUIDSGID=yes       --property=LockPersonality=yes       --property="RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6"       --property="ReadWritePaths=$OUT_DIR"       "$helper"
  local systemd_rc="$?"
  set -e

  if [[ "$systemd_rc" -ne 0 ]]; then
    show_status || true
    die "async_systemd_launch_failed"
  fi

  echo "B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_V03_ASYNC_LAUNCHED"
  echo "unit=$unit"
  echo "transport_smoke=PASS"
  echo "termux_prompt_can_return=True"
  echo "status_command=sudo bash $REPO/scripts/research/run-b15p2-announcement-body-semantic-audit-v0.3.sh --status"
  echo "price/basis/returns/PnL/index-values=CLOSED"
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
