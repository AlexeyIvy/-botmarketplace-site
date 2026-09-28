#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

REPO="/var/lib/botmarket-github-control/repo"
STAGE="/home/botmarket/.local/share/botmarket/b15p2-semantic-audit-v0.4.1-stage"
RUNTIME_DIR="/home/botmarket/.local/share/botmarket/b15p2-semantic-audit-v0.4.1-runtime"
DATA_ROOT="/home/botmarket/sc001_data"
OUT_DIR="$DATA_ROOT/SC001_B15P2_ANNOUNCEMENT_SEMANTIC_AUDIT"

OUT="$OUT_DIR/sc001_b15p2_announcement_body_semantic_audit_v0_1_5.json"
SMOKE_OUT="$OUT_DIR/sc001_b15p2_announcement_body_hydration_smoke_v0_1_5.json"
LOG="$OUT_DIR/networked_semantic_audit_v0_4_1.log"
EXIT_FILE="$OUT_DIR/networked_semantic_audit_v0_4_1.exit_code"
MARKER="$OUT_DIR/networked_semantic_audit_v0_4_1.launch.json"

INBOX_DIR="$REPO/docs/research/runtime-inbox"
INBOX_RESULT_REL="docs/research/runtime-inbox/sc001-b15p2-semantic-audit-v0.1.5-latest.json"
INBOX_RESULT="$REPO/$INBOX_RESULT_REL"
INBOX_SMOKE_REL="docs/research/runtime-inbox/sc001-b15p2-hydration-smoke-v0.1.5-latest.json"
INBOX_SMOKE="$REPO/$INBOX_SMOKE_REL"
INBOX_LOG_REL="docs/research/runtime-inbox/sc001-b15p2-semantic-audit-v0.1.5-latest.log"
INBOX_LOG="$REPO/$INBOX_LOG_REL"
INBOX_META_REL="docs/research/runtime-inbox/sc001-b15p2-semantic-audit-v0.1.5-latest.meta.json"
INBOX_META="$REPO/$INBOX_META_REL"
INBOX_PROGRESS_REL="docs/research/runtime-inbox/sc001-b15p2-semantic-audit-v0.1.5-progress.json"
INBOX_PROGRESS="$REPO/$INBOX_PROGRESS_REL"

SCRIPT_REL="research/sc001/sc001_b15p2_announcement_body_semantic_audit_v0_1_5.py"
PROTOCOL_REL="docs/research/sc001-b15p2-announcement-body-semantic-audit-protocol-v0.1.md"
FREEZE_REL="docs/research/sc001-b15p2-announcement-body-semantic-audit-implementation-freeze-v0.1.5.json"
SOURCE_RESULT_REL="docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_result.v0.1.1.json"
EVENT_FREEZE_REL="docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_event_set_freeze.v0.1.json"
SELECTION_REL="docs/research/sc001-b15p2-hydration-body-selection-freeze-v0.1.json"
MAPPER_RESULT_REL="docs/research/sc001-b15p2-generic-hydration-mapper-v04-result-v0.1.json"
HELPER_REL="scripts/research/run-b15p2-semantic-live-helper-v0.1.sh"

EXPECTED_SCRIPT_SHA="70cc8164fa1cffc8f8bde749a7e3c67744974b0eeb4c8e21b6e1d10621e8094d"
EXPECTED_PROTOCOL_SHA="4209779876e3796feff16a8310af93324cd1927862874524fb90ebf95d51d84f"
EXPECTED_FREEZE_SHA="ba373094d153dba028e39ce3cc20b1377a23af009a869bffc2a8b0a8b61a6b47"
EXPECTED_SOURCE_RESULT_SHA="c28aeb2b1ac0a23fb0e4420ced943fd619dd0a60e3fdcf5820299579cb94206c"
EXPECTED_EVENT_FREEZE_SHA="81952c83e7397481035cc00354388dfe3470ad17993c6e80665a7d376be907ed"
EXPECTED_SELECTION_SHA="ba2ccfa336a70e0592a9e4ce1742161e518060ceb5da090b37c666bc34c2c033"
EXPECTED_MAPPER_RESULT_SHA="3cd9216f0974d9b2e33886dfe59955946bc541b2fb9b4ae871332f4bffeccb38"
EXPECTED_HELPER_SHA="ce3d20648a6c835295ae3c2e49d1d5f22a9f12860ccaaf5cf363d7fb68317ca1"
EXPECTED_EVENT_SET_SHA="1063695ec003a0d6789270659822f50577e6a0f07059d88ac03a5be4288ed1a2"

SELFTEST_PASS="B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_V015_SELF_TEST_PASS"
SMOKE_PASS="B15P2_ANNOUNCEMENT_BODY_HYDRATION_SMOKE_V015_PASS"
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
  for cmd in sha256sum awk install sudo python3 curl systemctl systemd-run date grep find wc chown chmod rm cat tail mv dirname env tee test sort head cut stat; do
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
  check_source "$SOURCE_RESULT_REL" "$EXPECTED_SOURCE_RESULT_SHA"
  check_source "$EVENT_FREEZE_REL" "$EXPECTED_EVENT_FREEZE_SHA"
  check_source "$SELECTION_REL" "$EXPECTED_SELECTION_SHA"
  check_source "$MAPPER_RESULT_REL" "$EXPECTED_MAPPER_RESULT_SHA"
  check_source "$HELPER_REL" "$EXPECTED_HELPER_SHA"

  python3 -     "$REPO/$FREEZE_REL"     "$REPO/$EVENT_FREEZE_REL"     "$REPO/$SOURCE_RESULT_REL"     "$REPO/$SELECTION_REL"     "$REPO/$MAPPER_RESULT_REL"     "$EXPECTED_SCRIPT_SHA"     "$EXPECTED_PROTOCOL_SHA"     "$EXPECTED_EVENT_SET_SHA" <<'PY'
import json,sys
from pathlib import Path

def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))

def req(cond,code):
    if not cond:
        raise SystemExit(f"PRECHECK_FAILED:{code}")

fr=load(sys.argv[1])
ef=load(sys.argv[2])
src=load(sys.argv[3])
sel=load(sys.argv[4])
mapper=load(sys.argv[5])
script_sha=sys.argv[6]
protocol_sha=sys.argv[7]
event_set_sha=sys.argv[8]

req(fr.get("schema")=="sc001.b15p2_announcement_body_semantic_audit_implementation_freeze.v0.1.5","FREEZE_SCHEMA")
req((fr.get("entrypoint") or {}).get("sha256")==script_sha,"FREEZE_SCRIPT_SHA")
req((fr.get("protocol") or {}).get("sha256")==protocol_sha,"FREEZE_PROTOCOL_SHA")
req((fr.get("protocol") or {}).get("changed") is False,"FREEZE_PROTOCOL_CHANGED")
sinv=fr.get("semantic_invariants") or {}
for k in (
    "classify_text_unchanged_from_v0_1_4",
    "parse_announcement_time_unchanged_from_v0_1_4",
    "frozen_input_validation_unchanged_from_v0_1_4",
    "curl_transport_unchanged_from_v0_1_4",
    "pass_review_rules_unchanged",
    "event_set_unchanged",
):
    req(sinv.get(k) is True,f"SEMANTIC_INVARIANT_{k}")

hydr=fr.get("hydration_extraction") or {}
req(hydr.get("source")=="__NEXT_DATA__","HYDRATION_SOURCE")
req(hydr.get("one_exact_next_data_script_required") is True,"HYDRATION_NEXT_DATA_COUNT")
req(hydr.get("exact_title_equality_required") is True,"HYDRATION_TITLE")
req(hydr.get("primary_body_type")=="list","HYDRATION_BODY_TYPE")
req(hydr.get("minimum_normalized_body_chars")==120,"HYDRATION_MIN_BODY")
req(hydr.get("secondary_consistency_fail_closed_if_present_and_mismatched") is True,"HYDRATION_SECONDARY")
for k in ("price_access_authorized","external_reference_price_access_authorized","index_value_access_authorized","basis_access_authorized","returns_access_authorized","pnl_access_authorized","event_outcome_ranking_authorized"):
    req(fr.get(k) is False,f"FREEZE_{k.upper()}")

req(sel.get("schema")=="sc001.b15p2_hydration_body_selection_freeze.v0.1","SELECTION_SCHEMA")
req(sel.get("status")=="FROZEN_BEFORE_FINAL_HYDRATION_EXTRACTION","SELECTION_STATUS")
req(sel.get("script_role")=="__NEXT_DATA__","SELECTION_ROLE")
req(sel.get("exact_title_path")=="$.props.pageProps.articleDetail.title","SELECTION_TITLE_PATH")
req(sel.get("primary_body_path")=="$.props.pageProps.articleDetail.content.json.children","SELECTION_PRIMARY_PATH")
req(sel.get("secondary_consistency_path")=="$.props.pageProps.articleDetail.entry.entryKey.children","SELECTION_SECONDARY_PATH")
req(sel.get("semantic_rules_changed") is False,"SELECTION_SEMANTIC_CHANGED")
req(sel.get("frozen_event_set_changed") is False,"SELECTION_EVENT_SET_CHANGED")

req(mapper.get("schema")=="sc001.b15p2_generic_hydration_mapper_v04_result.v0.1","MAPPER_SCHEMA")
req(mapper.get("status")=="B15P2_GENERIC_HYDRATION_MAPPER_V04_PASS","MAPPER_STATUS")
req(mapper.get("exact_title_identity")=="__NEXT_DATA__::$.props.pageProps.articleDetail.title","MAPPER_TITLE")
req(mapper.get("selected_primary_body_identity")=="__NEXT_DATA__::$.props.pageProps.articleDetail.content.json.children","MAPPER_PRIMARY")
req(mapper.get("secondary_consistency_identity")=="__NEXT_DATA__::$.props.pageProps.articleDetail.entry.entryKey.children","MAPPER_SECONDARY")
req(mapper.get("article_body_text_persisted") is False,"MAPPER_BODY_TEXT")
req(mapper.get("semantic_classification_performed") is False,"MAPPER_SEMANTIC")

req(ef.get("status")=="B15P2_EXACT_ADMITTED_EVENT_SET_FROZEN","EVENT_FREEZE_STATUS")
req(ef.get("event_count")==94,"EVENT_FREEZE_COUNT")
req(ef.get("event_set_sha256")==event_set_sha,"EVENT_SET_SHA")

req(src.get("status")=="B15P2_BYBIT_DELISTING_SOURCE_CENSUS_PASS","SOURCE_STATUS")
req(src.get("admitted_event_count")==94,"SOURCE_COUNT")
req(src.get("announcement_match_coverage")==1.0,"SOURCE_COVERAGE")
req(src.get("source_integrity_issue_count")==0,"SOURCE_INTEGRITY")
events=src.get("events")
req(isinstance(events,list) and len(events)==94,"SOURCE_EVENTS")
urls=[]
symbols=[]
for i,e in enumerate(events):
    req(isinstance(e,dict),f"EVENT_{i}_OBJECT")
    au=e.get("announcement_urls")
    req(isinstance(au,list) and len(au)==1,f"EVENT_{i}_URL")
    urls.append(au[0])
    symbols.append(e.get("symbol"))
req(len(set(urls))==94,"UNIQUE_URLS")
req(all(u.startswith("https://announcements.bybit.com/") for u in urls),"URL_HOST")
req(symbols.count("DOGUSDT")==1 and symbols.count("TONUSDT")==1,"SMOKE_IDENTITIES")

for obj,label,keys in (
    (sel,"SELECTION",("price_access_authorized","external_reference_price_access_authorized","index_value_access_authorized","basis_access_authorized","returns_access_authorized","pnl_access_authorized")),
    (mapper,"MAPPER",("price_accessed","external_reference_price_accessed","index_value_accessed","basis_accessed","returns_accessed","pnl_accessed")),
):
    for k in keys:
        req(obj.get(k) is False,f"{label}_{k.upper()}")

for k in ("price_accessed","basis_calculated","pnl_calculated","event_ranked_by_outcome","settlement_semantics_interpreted"):
    req(src.get(k) is False,f"SOURCE_{k.upper()}")

print("B15P2_SEMANTIC_AUDIT_NETWORK_V04_PREFLIGHT_PASS")
print("frozen_events=94")
print("unique_announcement_urls=94")
print("hydration_smoke_gate=DOGUSDT,TONUSDT")
print("primary_body_path=$.props.pageProps.articleDetail.content.json.children")
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
def req(cond,code):
    if not cond:
        raise SystemExit(f"SMOKE_PRECHECK_FAILED:{code}")

req(obj.get("schema")=="sc001.b15p2_announcement_body_hydration_smoke.v0.1.5","SCHEMA")
req(obj.get("status")=="B15P2_ANNOUNCEMENT_BODY_HYDRATION_SMOKE_V015_PASS","STATUS")
tr=obj.get("transport") or {}
req(tr.get("client")=="curl","CLIENT")
req(tr.get("address_family")=="IPv4","FAMILY")
req(tr.get("http_version")=="HTTP/1.1","HTTP")
req(tr.get("proxy") is False,"PROXY")
ex=obj.get("body_extraction") or {}
req(ex.get("source")=="__NEXT_DATA__","SOURCE")
req(ex.get("exact_title_path")=="$.props.pageProps.articleDetail.title","TITLE_PATH")
req(ex.get("primary_body_path")=="$.props.pageProps.articleDetail.content.json.children","PRIMARY_PATH")
req(ex.get("secondary_consistency_path")=="$.props.pageProps.articleDetail.entry.entryKey.children","SECONDARY_PATH")
req(ex.get("adaptive_fallback_paths") is False,"ADAPTIVE_FALLBACK")

rows=obj.get("events")
req(isinstance(rows,list) and len(rows)==2,"EVENT_COUNT")
req([r.get("symbol") for r in rows]==["DOGUSDT","TONUSDT"],"EVENT_ORDER")
for i,r in enumerate(rows):
    req(r.get("title_path")==ex.get("exact_title_path"),f"TITLE_PATH_{i}")
    req(r.get("primary_body_path")==ex.get("primary_body_path"),f"PRIMARY_PATH_{i}")
    req(r.get("secondary_consistency_path")==ex.get("secondary_consistency_path"),f"SECONDARY_PATH_{i}")
    req(isinstance(r.get("primary_body_length"),int) and r["primary_body_length"]>=120,f"BODY_LENGTH_{i}")
    req(isinstance(r.get("primary_text_leaf_count"),int) and r["primary_text_leaf_count"]>0,f"LEAF_COUNT_{i}")
    req(r.get("secondary_present") is True,f"SECONDARY_PRESENT_{i}")
    req(r.get("secondary_match") is True,f"SECONDARY_MATCH_{i}")
    final=r.get("final_url") or ""
    p=urllib.parse.urlparse(final)
    req(p.scheme=="https" and p.hostname=="announcements.bybit.com",f"FINAL_URL_{i}")
    for key in ("raw_html_sha256","primary_body_sha256","secondary_body_sha256","article_region_sha256"):
        v=r.get(key)
        req(isinstance(v,str) and len(v)==64 and all(c in "0123456789abcdef" for c in v),f"{key}_{i}")
    req(r.get("primary_body_sha256")==r.get("secondary_body_sha256"),f"BODY_HASH_MATCH_{i}")

req(obj.get("article_body_text_persisted") is False,"ARTICLE_TEXT")
req(obj.get("semantic_classification_performed") is False,"SEMANTIC")
for k in ("price_accessed","external_reference_price_accessed","index_value_accessed","basis_accessed","returns_accessed","pnl_accessed"):
    req(obj.get(k) is False,k.upper())

print("B15P2_HYDRATION_SMOKE_RESULT_VALIDATED")
PY
}

ensure_inbox_dir() {
  install -d -m 0750 -o botmarket-github -g botmarket-github "$INBOX_DIR"
}

copy_exact_to_inbox() {
  local src="$1"
  local dst="$2"
  local max_bytes="$3"
  [[ -f "$src" && ! -L "$src" ]] || return 1
  local size src_sha tmp dst_sha
  size="$(stat -c '%s' "$src")"
  [[ "$size" -gt 0 && "$size" -le "$max_bytes" ]] || die "runtime_inbox_size_rejected:$src:$size"
  src_sha="$(sha256sum "$src" | awk '{print $1}')"
  ensure_inbox_dir
  tmp="$dst.tmp"
  install -m 0640 -o botmarket-github -g botmarket-github "$src" "$tmp"
  dst_sha="$(sha256sum "$tmp" | awk '{print $1}')"
  [[ "$dst_sha" == "$src_sha" ]] || die "runtime_inbox_sha_mismatch:$src"
  mv "$tmp" "$dst"
  echo "$src_sha"
}

publish_smoke_if_present() {
  [[ -f "$SMOKE_OUT" ]] || return 0

  if ! python3 - "$SMOKE_OUT" <<'PY'
import json,sys
from pathlib import Path
obj=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
def req(cond,code):
    if not cond:
        raise SystemExit(f"PUBLISH_SMOKE_FAILED:{code}")

req(obj.get("schema")=="sc001.b15p2_announcement_body_hydration_smoke.v0.1.5","SCHEMA")
req(obj.get("status") in {
    "B15P2_ANNOUNCEMENT_BODY_HYDRATION_SMOKE_V015_PASS",
    "B15P2_ANNOUNCEMENT_BODY_HYDRATION_SMOKE_V015_REVIEW",
},"STATUS")
req(obj.get("article_body_text_persisted") is False,"ARTICLE_TEXT")
req(obj.get("semantic_classification_performed") is False,"SEMANTIC")
for k in ("price_accessed","external_reference_price_accessed","index_value_accessed","basis_accessed","returns_accessed","pnl_accessed"):
    req(obj.get(k) is False,k.upper())
rows=obj.get("events")
req(isinstance(rows,list),"EVENTS")
req(len(rows)<=2,"EVENT_COUNT")
req(all(r.get("symbol") in {"DOGUSDT","TONUSDT"} for r in rows),"SYMBOLS")
PY
  then
    echo "runtime_inbox_smoke=NOT_PUBLISHED_VALIDATION_FAILED"
    return 0
  fi

  local sha
  sha="$(copy_exact_to_inbox "$SMOKE_OUT" "$INBOX_SMOKE" 524288)"
  echo "runtime_inbox_smoke=$INBOX_SMOKE_REL"
  echo "runtime_inbox_smoke_sha256=$sha"
}

validate_terminal_result() {
  [[ -f "$OUT" ]] || return 1
  python3 - "$OUT" "$PASS" "$REVIEW" "$EXPECTED_EVENT_SET_SHA" <<'PY'
import json,sys
from pathlib import Path
obj=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
PASS,REVIEW,event_sha=sys.argv[2],sys.argv[3],sys.argv[4]
status=obj.get("status")
assert status in {PASS,REVIEW}

fw=obj.get("firewalls") or {}
for k,v in fw.items():
    if k.endswith(("accessed","calculated")) or k=="event_ranked_by_outcome":
        assert v is False,(k,v)

if obj.get("frozen_event_set_sha256") is not None:
    assert obj.get("frozen_event_set_sha256")==event_sha

ex=obj.get("body_extraction")
if ex is not None:
    assert ex.get("source")=="__NEXT_DATA__"
    assert ex.get("exact_title_path")=="$.props.pageProps.articleDetail.title"
    assert ex.get("primary_body_path")=="$.props.pageProps.articleDetail.content.json.children"
    assert ex.get("secondary_consistency_path")=="$.props.pageProps.articleDetail.entry.entryKey.children"
    assert ex.get("adaptive_fallback_paths") is False
else:
    assert status==REVIEW
    assert obj.get("error_type")

for row in obj.get("events") or []:
    assert row.get("body_source")=="NEXT_DATA_HYDRATION"
    assert row.get("hydration_primary_body_path")=="$.props.pageProps.articleDetail.content.json.children"
    if row.get("hydration_secondary_present") is True:
        assert row.get("hydration_secondary_match") is True

print(status)
PY
}

publish_progress_meta() {
  ensure_inbox_dir

  local unit="" active_state="ABSENT" sub_state="ABSENT"
  local service_result="ABSENT" exec_main_code="ABSENT" exec_main_status="ABSENT"
  if [[ -f "$MARKER" ]]; then
    unit="$(python3 - "$MARKER" <<'PY'
import json,sys
from pathlib import Path
print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")).get("unit") or "")
PY
)"
    if [[ -n "$unit" ]]; then
      active_state="$(systemctl show "$unit" -p ActiveState --value 2>/dev/null || true)"
      sub_state="$(systemctl show "$unit" -p SubState --value 2>/dev/null || true)"
      service_result="$(systemctl show "$unit" -p Result --value 2>/dev/null || true)"
      exec_main_code="$(systemctl show "$unit" -p ExecMainCode --value 2>/dev/null || true)"
      exec_main_status="$(systemctl show "$unit" -p ExecMainStatus --value 2>/dev/null || true)"
      [[ -n "$active_state" ]] || active_state="UNKNOWN"
      [[ -n "$sub_state" ]] || sub_state="UNKNOWN"
      [[ -n "$service_result" ]] || service_result="UNKNOWN"
      [[ -n "$exec_main_code" ]] || exec_main_code="UNKNOWN"
      [[ -n "$exec_main_status" ]] || exec_main_status="UNKNOWN"
    fi
  fi

  local started=0 done=0 errors=0 retries=0 last_progress=""
  if [[ -f "$LOG" ]]; then
    started="$(grep -c '^EVENT_START ' "$LOG" 2>/dev/null || true)"
    done="$(grep -c '^EVENT_DONE ' "$LOG" 2>/dev/null || true)"
    errors="$(grep -c '^EVENT_ERROR ' "$LOG" 2>/dev/null || true)"
    retries="$(grep -c '^FETCH_RETRY ' "$LOG" 2>/dev/null || true)"
    last_progress="$(grep -E '^(EVENT_START|EVENT_DONE|EVENT_ERROR|FETCH_RETRY) ' "$LOG" 2>/dev/null | tail -n 1 || true)"
  fi

  local exit_code="" terminal_status="" smoke_status=""
  if [[ -f "$EXIT_FILE" ]]; then
    exit_code="$(cat "$EXIT_FILE" 2>/dev/null || true)"
  fi
  if [[ -f "$OUT" ]]; then
    terminal_status="$(python3 - "$OUT" <<'PY'
import json,sys
from pathlib import Path
try:
    print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")).get("status") or "")
except Exception:
    print("INVALID")
PY
)"
  fi
  if [[ -f "$SMOKE_OUT" ]]; then
    smoke_status="$(python3 - "$SMOKE_OUT" <<'PY'
import json,sys
from pathlib import Path
try:
    print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")).get("status") or "")
except Exception:
    print("INVALID")
PY
)"
  fi

  local tmp="$INBOX_PROGRESS.tmp"
  python3 -     "$unit" "$active_state" "$sub_state" "$service_result" "$exec_main_code" "$exec_main_status"     "$started" "$done" "$errors" "$retries" "$last_progress" "$exit_code" "$terminal_status" "$smoke_status" > "$tmp" <<'PY'
import json,sys,datetime
(
 unit,active_state,sub_state,service_result,exec_main_code,exec_main_status,
 started,done,errors,retries,last_progress,exit_code,terminal_status,smoke_status
)=sys.argv[1:15]
print(json.dumps({
  "schema":"sc001.b15p2_semantic_audit_progress.v0.1",
  "published_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
  "unit":unit or None,
  "systemd":{
    "active_state":active_state,
    "sub_state":sub_state,
    "result":service_result,
    "exec_main_code":exec_main_code,
    "exec_main_status":exec_main_status,
  },
  "progress":{
    "expected_events":94,
    "started":int(started or 0),
    "done":int(done or 0),
    "errors":int(errors or 0),
    "retries":int(retries or 0),
    "last_progress":last_progress or None,
  },
  "exit_code":exit_code or None,
  "terminal_status":terminal_status or None,
  "smoke_status":smoke_status or None,
  "price_access_authorized":False,
  "external_reference_price_access_authorized":False,
  "index_value_access_authorized":False,
  "basis_access_authorized":False,
  "returns_access_authorized":False,
  "pnl_access_authorized":False,
},indent=2,sort_keys=True))
PY
  chown botmarket-github:botmarket-github "$tmp"
  chmod 0640 "$tmp"
  mv "$tmp" "$INBOX_PROGRESS"
  echo "runtime_inbox_progress=$INBOX_PROGRESS_REL"
}

publish_terminal_if_present() {
  [[ -f "$OUT" ]] || return 0
  local status
  if ! status="$(validate_terminal_result)"; then
    echo "runtime_inbox_result=NOT_PUBLISHED_VALIDATION_FAILED"
    return 0
  fi

  local result_sha log_sha
  result_sha="$(copy_exact_to_inbox "$OUT" "$INBOX_RESULT" 2097152)"
  echo "runtime_inbox_result=$INBOX_RESULT_REL"
  echo "runtime_inbox_result_sha256=$result_sha"

  log_sha=""
  if [[ -f "$LOG" ]]; then
    log_sha="$(copy_exact_to_inbox "$LOG" "$INBOX_LOG" 1048576)"
    echo "runtime_inbox_log=$INBOX_LOG_REL"
    echo "runtime_inbox_log_sha256=$log_sha"
  fi

  ensure_inbox_dir
  local meta_tmp="$INBOX_META.tmp"
  python3 - "$status" "$result_sha" "$log_sha" > "$meta_tmp" <<'PY'
import json,sys,datetime
status,result_sha,log_sha=sys.argv[1:4]
print(json.dumps({
  "schema":"sc001.semantic_runtime_result_publish_meta.v0.1",
  "published_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
  "result_status":status,
  "result_relative_path":"docs/research/runtime-inbox/sc001-b15p2-semantic-audit-v0.1.5-latest.json",
  "result_sha256":result_sha,
  "log_relative_path":"docs/research/runtime-inbox/sc001-b15p2-semantic-audit-v0.1.5-latest.log" if log_sha else None,
  "log_sha256":log_sha or None,
  "content_mutated":False
},indent=2,sort_keys=True))
PY
  chown botmarket-github:botmarket-github "$meta_tmp"
  chmod 0640 "$meta_tmp"
  mv "$meta_tmp" "$INBOX_META"
  echo "runtime_inbox_meta=$INBOX_META_REL"
}

show_status() {
  need_root
  check_tools
  echo "wrapper_version=0.4.1"

  if [[ -f "$SMOKE_OUT" ]]; then
    python3 - "$SMOKE_OUT" <<'PY'
import json,sys
from pathlib import Path
o=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print("smoke_status =",o.get("status"))
for r in o.get("events") or []:
    print(r.get("symbol"),"body_len="+str(r.get("primary_body_length")),"leaves="+str(r.get("primary_text_leaf_count")),"secondary_match="+str(r.get("secondary_match")))
PY
  else
    echo "smoke_status=ABSENT"
  fi

  if [[ -f "$MARKER" ]]; then
    local unit active_state sub_state
    unit="$(python3 - "$MARKER" <<'PY'
import json,sys
from pathlib import Path
print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["unit"])
PY
)"
    echo "unit=$unit"
    active_state="$(systemctl show "$unit" -p ActiveState --value 2>/dev/null || true)"
    sub_state="$(systemctl show "$unit" -p SubState --value 2>/dev/null || true)"
    [[ -n "$active_state" ]] || active_state=UNKNOWN
    [[ -n "$sub_state" ]] || sub_state=UNKNOWN
    echo "systemd_active_state=$active_state"
    echo "systemd_sub_state=$sub_state"
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
    python3 - "$OUT" <<'PY'
import json,sys
from pathlib import Path
obj=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print("result_status =",obj.get("status"))
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
PY
  else
    echo "result_status=PENDING_OR_ABSENT"
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
    [[ -z "$last_line" ]] || echo "last_progress=$last_line"
    echo "--- persistent log tail ---"
    tail -n 30 "$LOG"
  else
    echo "persistent_log=ABSENT"
  fi

  publish_smoke_if_present
  publish_terminal_if_present
  publish_progress_meta
}

preflight_only() {
  need_root
  check_tools
  contract_preflight
}

launch() {
  need_root
  check_tools

  [[ ! -e "$MARKER" ]] || die "one_shot_launch_marker_exists"
  [[ ! -e "$OUT" ]] || die "existing_result_forbidden"
  [[ ! -e "$EXIT_FILE" ]] || die "existing_exit_file_forbidden"
  [[ ! -e "$LOG" ]] || die "existing_log_forbidden"

  contract_preflight

  if [[ -f "$SMOKE_OUT" ]]; then
    if ! validate_smoke_result >/dev/null 2>&1; then
      die "preexisting_smoke_invalid"
    fi
    publish_smoke_if_present
    rm -f "$SMOKE_OUT"
  fi

  rm -rf "$STAGE" "$RUNTIME_DIR"
  install -d -m 0750 -o root -g botmarket "$STAGE"
  install -d -m 0750 -o root -g botmarket "$RUNTIME_DIR"

  stage_one() {
    local rel="$1"
    local expected="$2"
    local src="$REPO/$rel"
    local dst="$STAGE/$rel"
    local actual
    install -d -m 0750 -o root -g botmarket "$(dirname "$dst")"
    install -m 0440 -o root -g botmarket "$src" "$dst"
    actual="$(sha256sum "$dst" | awk '{print $1}')"
    [[ "$actual" == "$expected" ]] || die "staged_sha_mismatch:$rel"
    sudo -u botmarket -H test -r "$dst" || die "staged_not_readable:$rel"
    if sudo -u botmarket -H test -w "$dst"; then
      die "staged_unexpectedly_writable:$rel"
    fi
  }

  stage_one "$SCRIPT_REL" "$EXPECTED_SCRIPT_SHA"
  stage_one "$PROTOCOL_REL" "$EXPECTED_PROTOCOL_SHA"
  stage_one "$FREEZE_REL" "$EXPECTED_FREEZE_SHA"
  stage_one "$SOURCE_RESULT_REL" "$EXPECTED_SOURCE_RESULT_SHA"
  stage_one "$EVENT_FREEZE_REL" "$EXPECTED_EVENT_FREEZE_SHA"
  stage_one "$SELECTION_REL" "$EXPECTED_SELECTION_SHA"
  stage_one "$MAPPER_RESULT_REL" "$EXPECTED_MAPPER_RESULT_SHA"

  [[ -z "$(find "$STAGE" -type l -print -quit)" ]] || die "staging_symlink_detected"
  local stage_count
  stage_count="$(find "$STAGE" -type f | wc -l | awk '{print $1}')"
  [[ "$stage_count" == "7" ]] || die "unexpected_staging_file_count:$stage_count"

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

  echo "B15P2_HYDRATION_SMOKE_START"
  set +e
  sudo -u botmarket -H env -i     HOME=/home/botmarket     PATH=/usr/bin:/bin     B15P2_REPO_ROOT="$STAGE"     SC001_DATA_ROOT="$DATA_ROOT"     /usr/bin/python3 "$staged_script" --mode hydration-smoke 2>&1 | /usr/bin/tee -a "$LOG"
  local smoke_rc="$?"
  set -e

  if [[ "$smoke_rc" -ne 0 ]]; then
    echo "B15P2_HYDRATION_SMOKE_FAILED"
    echo "smoke_exit_code=$smoke_rc"
    publish_smoke_if_present || true
    if [[ -f "$LOG" ]]; then
      copy_exact_to_inbox "$LOG" "$INBOX_LOG" 1048576 >/dev/null || true
    fi
    die "hydration_smoke_failed_full_94_not_started"
  fi

  grep -qx "$SMOKE_PASS" "$LOG" || die "hydration_smoke_pass_token_missing"
  validate_smoke_result
  publish_smoke_if_present
  echo "B15P2_HYDRATION_SMOKE_GATE_PASS"

  local helper="$RUNTIME_DIR/run-b15p2-semantic-live-helper-v0.1.sh"
  install -m 0550 -o root -g botmarket "$REPO/$HELPER_REL" "$helper"
  local helper_sha
  helper_sha="$(sha256sum "$helper" | awk '{print $1}')"
  [[ "$helper_sha" == "$EXPECTED_HELPER_SHA" ]] || die "runtime_helper_sha_mismatch"
  sudo -u botmarket -H test -r "$helper" || die "runtime_helper_not_readable"
  sudo -u botmarket -H test -x "$helper" || die "runtime_helper_not_executable"
  if sudo -u botmarket -H test -w "$helper"; then
    die "runtime_helper_unexpectedly_writable"
  fi

  local unit
  unit="sc001-b15p2-semantic-audit-v041-$(date -u +%Y%m%dT%H%M%SZ)"

  set +e
  systemd-run     --no-block     --unit="$unit"     --description="SC001 B15-P2 frozen 94-page semantic audit v0.4.1 static helper recovery"     --property=Type=exec     --property=TimeoutStartSec=30     --property=RuntimeMaxSec=4200     --property=User=botmarket     --property=Group=botmarket     --property=UMask=0027     --property=NoNewPrivileges=yes     --property=PrivateTmp=yes     --property=PrivateDevices=yes     --property=ProtectSystem=strict     --property=ProtectKernelTunables=yes     --property=ProtectKernelModules=yes     --property=ProtectControlGroups=yes     --property=RestrictSUIDSGID=yes     --property=LockPersonality=yes     --property="RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6"     --property="ReadOnlyPaths=$STAGE $RUNTIME_DIR"     --property="ReadWritePaths=$OUT_DIR"     --setenv="B15P2_STAGE=$STAGE"     --setenv="B15P2_DATA_ROOT=$DATA_ROOT"     --setenv="B15P2_SCRIPT=$staged_script"     --setenv="B15P2_LOG=$LOG"     --setenv="B15P2_EXIT_FILE=$EXIT_FILE"     "$helper"
  local systemd_rc="$?"
  set -e

  if [[ "$systemd_rc" -ne 0 ]]; then
    die "async_systemd_launch_failed"
  fi

  local marker_tmp="$MARKER.tmp"
  cat > "$marker_tmp" <<EOF
{
  "schema": "sc001.b15p2_semantic_audit_launch_marker.v0.4.1",
  "unit": "$unit",
  "script_sha256": "$EXPECTED_SCRIPT_SHA",
  "protocol_sha256": "$EXPECTED_PROTOCOL_SHA",
  "selection_sha256": "$EXPECTED_SELECTION_SHA",
  "mapper_result_sha256": "$EXPECTED_MAPPER_RESULT_SHA",
  "source_result_sha256": "$EXPECTED_SOURCE_RESULT_SHA",
  "event_set_sha256": "$EXPECTED_EVENT_SET_SHA",
  "frozen_event_count": 94,
  "execution_mode": "ASYNC_SYSTEMD_TYPE_EXEC_STATIC_HELPER_AFTER_REQUIRED_HYDRATION_SMOKE",
  "transport": "curl_ipv4_http11_browser_ua",
  "body_source": "NEXT_DATA_HYDRATION",
  "hydration_smoke_status": "PASS",
  "runtime_bound_seconds": 4200,
  "live_helper_sha256": "$EXPECTED_HELPER_SHA",
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

  echo "B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_V041_ASYNC_LAUNCHED"
  echo "unit=$unit"
  echo "hydration_smoke=PASS"
  echo "termux_prompt_can_return=True"
  echo "status_command=sudo bash $REPO/scripts/research/run-b15p2-announcement-body-semantic-audit-v0.4.1.sh --status"
  echo "large_output_handoff=RUNTIME_INBOX_ON_STATUS"
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
