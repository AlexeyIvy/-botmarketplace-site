#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

REPO="/var/lib/botmarket-github-control/repo"
STAGE="/home/botmarket/.local/share/botmarket/b15p2-dual-schema-semantic-v0.2-stage"
DATA_ROOT="/home/botmarket/sc001_data"
OUT_DIR="$DATA_ROOT/SC001_B15P2_ANNOUNCEMENT_SEMANTIC_AUDIT"

OUT="$OUT_DIR/sc001_b15p2_announcement_body_semantic_audit_v0_1_7.json"
SMOKE="$OUT_DIR/sc001_b15p2_announcement_body_dual_schema_smoke_v0_1_7.json"
LOG="$OUT_DIR/networked_semantic_audit_v0_1_7.log"

INBOX_DIR="$REPO/docs/research/runtime-inbox"
INBOX_RESULT_REL="docs/research/runtime-inbox/sc001-b15p2-semantic-audit-v0.1.7-latest.json"
INBOX_RESULT="$REPO/$INBOX_RESULT_REL"
INBOX_SMOKE_REL="docs/research/runtime-inbox/sc001-b15p2-dual-schema-smoke-v0.1.7-latest.json"
INBOX_SMOKE="$REPO/$INBOX_SMOKE_REL"
INBOX_LOG_REL="docs/research/runtime-inbox/sc001-b15p2-semantic-audit-v0.1.7-latest.log"
INBOX_LOG="$REPO/$INBOX_LOG_REL"
INBOX_META_REL="docs/research/runtime-inbox/sc001-b15p2-semantic-audit-v0.1.7-latest.meta.json"
INBOX_META="$REPO/$INBOX_META_REL"
INBOX_DIAG_REL="docs/research/runtime-inbox/sc001-b15p2-dual-schema-semantic-v0.1.7-prelaunch-diagnostic.json"
INBOX_DIAG="$REPO/$INBOX_DIAG_REL"

SCRIPT_REL="research/sc001/sc001_b15p2_announcement_body_semantic_audit_v0_1_7.py"
PROTOCOL_REL="docs/research/sc001-b15p2-announcement-body-semantic-audit-protocol-v0.1.md"
IMPLEMENTATION_FREEZE_REL="docs/research/sc001-b15p2-announcement-body-semantic-audit-implementation-freeze-v0.1.7.json"
DUAL_ROUTING_REL="docs/research/sc001-b15p2-hydration-dual-schema-routing-freeze-v0.1.json"
ART_CENSUS_RESULT_REL="docs/research/sc001-b15p2-art-generation-schema-census-result-v0.1.json"
SOURCE_REL="docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_result.v0.1.1.json"
EVENT_FREEZE_REL="docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_event_set_freeze.v0.1.json"

EXPECTED_SCRIPT_SHA="f83e34263fe8716c235a76be1c94ee2049c38a4c3fdc8a064f1d99ed327ef4cc"
EXPECTED_PROTOCOL_SHA="4209779876e3796feff16a8310af93324cd1927862874524fb90ebf95d51d84f"
EXPECTED_IMPLEMENTATION_FREEZE_SHA="4e5707ad33a48234fe8a48f8920e75754e1812b7a30f0a36be1428199ee02c14"
EXPECTED_DUAL_ROUTING_SHA="5a58a4289aa73b6a510a8cdaade586c56433da20b35472b526e43174789c929f"
EXPECTED_ART_CENSUS_RESULT_SHA="44c7494b7ab125a83ce895ea93646af3ffae34d7a8c188e2e6415487d1bc3712"
EXPECTED_SOURCE_SHA="c28aeb2b1ac0a23fb0e4420ced943fd619dd0a60e3fdcf5820299579cb94206c"
EXPECTED_EVENT_FREEZE_SHA="81952c83e7397481035cc00354388dfe3470ad17993c6e80665a7d376be907ed"
EXPECTED_EVENT_SET_SHA="1063695ec003a0d6789270659822f50577e6a0f07059d88ac03a5be4288ed1a2"

SELFTEST_PASS="B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_V017_SELF_TEST_PASS"
SMOKE_PASS="B15P2_ANNOUNCEMENT_BODY_DUAL_SCHEMA_SMOKE_V017_PASS"
PASS="B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_PASS"
REVIEW="B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_REVIEW"

die() {
  echo "B15P2_DUAL_SCHEMA_SEMANTIC_HOST_REVIEW"
  echo "reason=$1"
  echo "price/index-values/basis/returns/PnL=CLOSED"
  exit 2
}

need_root() {
  [[ "${EUID:-$(id -u)}" -eq 0 ]] || die "wrapper_must_run_as_root"
}

check_tools() {
  local cmd
  for cmd in sha256sum awk install sudo python3 curl grep find wc chown chmod rm cat tail mv dirname env test stat timeout; do
    command -v "$cmd" >/dev/null 2>&1 || die "required_command_missing:$cmd"
  done
}

check_source() {
  local rel="$1" expected="$2" src="$REPO/$1"
  [[ -f "$src" && ! -L "$src" ]] || die "source_missing_or_symlink:$rel"
  local actual
  actual="$(sha256sum "$src" | awk '{print $1}')"
  [[ "$actual" == "$expected" ]] || die "source_sha_mismatch:$rel"
}

contract_preflight() {
  need_root
  check_tools
  [[ -d "$REPO" ]] || die "repo_missing"

  check_source "$SCRIPT_REL" "$EXPECTED_SCRIPT_SHA"
  check_source "$PROTOCOL_REL" "$EXPECTED_PROTOCOL_SHA"
  check_source "$IMPLEMENTATION_FREEZE_REL" "$EXPECTED_IMPLEMENTATION_FREEZE_SHA"
  check_source "$DUAL_ROUTING_REL" "$EXPECTED_DUAL_ROUTING_SHA"
  check_source "$ART_CENSUS_RESULT_REL" "$EXPECTED_ART_CENSUS_RESULT_SHA"
  check_source "$SOURCE_REL" "$EXPECTED_SOURCE_SHA"
  check_source "$EVENT_FREEZE_REL" "$EXPECTED_EVENT_FREEZE_SHA"

  python3 -     "$REPO/$IMPLEMENTATION_FREEZE_REL"     "$REPO/$DUAL_ROUTING_REL"     "$REPO/$ART_CENSUS_RESULT_REL"     "$REPO/$SOURCE_REL"     "$REPO/$EVENT_FREEZE_REL"     "$EXPECTED_SCRIPT_SHA" "$EXPECTED_PROTOCOL_SHA" "$EXPECTED_EVENT_SET_SHA" <<'PY'
import json,re,sys,urllib.parse
from pathlib import Path

def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))

def req(cond,code):
    if not cond:
        raise SystemExit(f"PRECHECK_FAILED:{code}")

impl=load(sys.argv[1])
route=load(sys.argv[2])
census=load(sys.argv[3])
src=load(sys.argv[4])
ef=load(sys.argv[5])
script_sha,protocol_sha,event_sha=sys.argv[6:9]

req(impl.get("schema")=="sc001.b15p2_announcement_body_semantic_audit_implementation_freeze.v0.1.7","IMPL_SCHEMA")
req((impl.get("entrypoint") or {}).get("sha256")==script_sha,"IMPL_SCRIPT_SHA")
req((impl.get("protocol") or {}).get("sha256")==protocol_sha,"IMPL_PROTOCOL_SHA")
req((impl.get("protocol") or {}).get("changed") is False,"IMPL_PROTOCOL_CHANGED")
dual_ref=impl.get("dual_schema_routing") or {}
req(dual_ref.get("path")=="docs/research/sc001-b15p2-hydration-dual-schema-routing-freeze-v0.1.json","IMPL_ROUTE_PATH")
req(dual_ref.get("sha256")=="5a58a4289aa73b6a510a8cdaade586c56433da20b35472b526e43174789c929f","IMPL_ROUTE_SHA")
census_ref=impl.get("schema_b_census") or {}
req(census_ref.get("path")=="docs/research/sc001-b15p2-art-generation-schema-census-result-v0.1.json","IMPL_CENSUS_PATH")
req(census_ref.get("sha256")=="44c7494b7ab125a83ce895ea93646af3ffae34d7a8c188e2e6415487d1bc3712","IMPL_CENSUS_SHA")
sinv=impl.get("semantic_invariants") or {}
for k in (
    "classify_text_unchanged_from_v0_1_6",
    "parse_announcement_time_unchanged_from_v0_1_6",
    "frozen_input_validation_unchanged_from_v0_1_6",
    "curl_transport_unchanged_from_v0_1_6",
    "extract_hydration_article_unchanged_from_v0_1_6",
    "dual_schema_routing_unchanged",
    "event_set_unchanged",
):
    req(sinv.get(k) is True,f"IMPL_{k}")
stfix=impl.get("selftest_change") or {}
req(stfix.get("stage")=="NO_CROSS_SCHEMA_FALLBACK","IMPL_SELFTEST_STAGE")
req(stfix.get("new_expected_fail_closed_error")=="SCHEMA_B_RAW_HTML_TOO_SHORT","IMPL_SELFTEST_EXPECTATION")

for k in (
    "price_access_authorized","external_reference_price_access_authorized",
    "index_value_access_authorized","basis_access_authorized",
    "returns_access_authorized","pnl_access_authorized",
    "event_outcome_ranking_authorized",
):
    req(impl.get(k) is False,f"IMPL_{k.upper()}")

req(route.get("schema")=="sc001.b15p2_hydration_dual_schema_routing_freeze.v0.1","ROUTE_SCHEMA")
req(route.get("status")=="FROZEN_BEFORE_DUAL_SCHEMA_SEMANTIC_RERUN","ROUTE_STATUS")
entries=route.get("routing") or []
req(isinstance(entries,list) and len(entries)==2,"ROUTE_ENTRIES")
by_id={x.get("schema_id"):x for x in entries if isinstance(x,dict)}
a=by_id.get("BLT_RICHTEXT") or {}
b=by_id.get("DOUBLE_DASH_ART_HTML") or {}
req(a.get("observed_frozen_event_count")==76,"ROUTE_A_COUNT")
req(a.get("primary_body_path")=="$.props.pageProps.articleDetail.content.json.children","ROUTE_A_PATH")
req(b.get("observed_frozen_event_count")==18,"ROUTE_B_COUNT")
req(b.get("primary_body_path")=="$.props.pageProps.articleDetail.content_html","ROUTE_B_PATH")
req(b.get("minimum_required_html_tag_count")==2,"ROUTE_B_MIN_HTML_TAGS")
req(b.get("observed_html_tag_count_all_18")==31,"ROUTE_B_OBSERVED_HTML_TAGS")
req(b.get("unique_content_sha256_count")==18,"ROUTE_B_UNIQUE_SHA_COUNT")
rules=route.get("routing_rules") or []
rules_text="\n".join(str(x) for x in rules)
req("frozen official announcement URL generation" in rules_text,"ROUTING_SOURCE")
req("do not fall back" in rules_text.lower(),"ROUTING_NO_FALLBACK")
req("semantic classification success" in rules_text.lower(),"ROUTING_NO_SEMANTIC")
req("price or outcome data" in rules_text.lower(),"ROUTING_NO_OUTCOME")

req(census.get("schema")=="sc001.b15p2_art_generation_schema_census_result.v0.1","CENSUS_SCHEMA")
req(census.get("status")=="B15P2_ART_GENERATION_SCHEMA_CENSUS_PASS","CENSUS_STATUS")
selected=census.get("selected_schema_b_body") or {}
req(selected.get("identity")=="__NEXT_DATA__::$.props.pageProps.articleDetail.content_html","CENSUS_BODY")
req(selected.get("coverage_event_count")==18,"CENSUS_COVERAGE_COUNT")
req(selected.get("coverage_fraction")==1.0,"CENSUS_COVERAGE_FRACTION")
req(selected.get("html_tag_count_all_18")==31,"CENSUS_HTML_TAG_COUNT")

req(src.get("status")=="B15P2_BYBIT_DELISTING_SOURCE_CENSUS_PASS","SOURCE_STATUS")
req(src.get("admitted_event_count")==94,"SOURCE_COUNT")
req(ef.get("status")=="B15P2_EXACT_ADMITTED_EVENT_SET_FROZEN","EVENT_FREEZE_STATUS")
req(ef.get("event_count")==94,"EVENT_FREEZE_COUNT")
req(ef.get("event_set_sha256")==event_sha,"EVENT_SET_SHA")

blt=re.compile(r"-blt[0-9a-f]+/?$",re.I)
art=re.compile(r"--art[0-9a-f]+/?$",re.I)
counts={"BLT":0,"ART":0}
urls=set()
for e in src.get("events") or []:
    au=e.get("announcement_urls")
    req(isinstance(au,list) and len(au)==1,f"URL_COUNT:{e.get('symbol')}")
    u=au[0]
    p=urllib.parse.urlparse(u)
    req(p.scheme=="https" and p.hostname=="announcements.bybit.com",f"URL_POLICY:{e.get('symbol')}")
    a=bool(blt.search(p.path)); b=bool(art.search(p.path))
    req(a != b,f"URL_GENERATION:{e.get('symbol')}")
    counts["BLT" if a else "ART"]+=1
    urls.add(u)
req(counts=={"BLT":76,"ART":18},f"PARTITION:{counts}")
req(len(urls)==94,"URL_UNIQUENESS")

for k in ("price_accessed","basis_calculated","pnl_calculated","event_ranked_by_outcome","settlement_semantics_interpreted"):
    req(src.get(k) is False,f"SOURCE_{k.upper()}")

print("B15P2_DUAL_SCHEMA_SEMANTIC_HOST_PREFLIGHT_PASS")
print("partition=BLT:76,ART:18")
print("frozen_events=94")
print("price/index-values/basis/returns/PnL=CLOSED")
PY
}

publish_prelaunch_diagnostic() {
  local phase="$1" code="$2" exit_code="$3" detail="$4"
  ensure_inbox_dir
  local tmp="$INBOX_DIAG.tmp"
  python3 - "$phase" "$code" "$exit_code" "$detail"     "$EXPECTED_SCRIPT_SHA" "$EXPECTED_IMPLEMENTATION_FREEZE_SHA" <<'PY' > "$tmp"
import datetime,json,sys
phase,code,exit_code,detail,script_sha,freeze_sha=sys.argv[1:7]
try:
    rc=int(exit_code)
except Exception:
    rc=None
print(json.dumps({
  "schema":"sc001.b15p2_dual_schema_prelaunch_diagnostic.v0.1",
  "published_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
  "phase":phase,
  "code":code,
  "exit_code":rc,
  "detail":detail[:20000],
  "implementation_sha256":script_sha,
  "implementation_freeze_sha256":freeze_sha,
  "network_started":False,
  "price_access_authorized":False,
  "external_reference_price_access_authorized":False,
  "index_value_access_authorized":False,
  "basis_access_authorized":False,
  "returns_access_authorized":False,
  "pnl_access_authorized":False
},indent=2,sort_keys=True))
PY
  chown botmarket-github:botmarket-github "$tmp"
  chmod 0640 "$tmp"
  mv "$tmp" "$INBOX_DIAG"
  echo "runtime_inbox_prelaunch_diagnostic=$INBOX_DIAG_REL"
}

ensure_inbox_dir() {
  install -d -m 0750 -o botmarket-github -g botmarket-github "$INBOX_DIR"
}

copy_exact() {
  local src="$1" dst="$2" max_bytes="$3"
  [[ -f "$src" && ! -L "$src" ]] || return 1
  local size src_sha tmp dst_sha
  size="$(stat -c '%s' "$src")"
  [[ "$size" -gt 0 && "$size" -le "$max_bytes" ]] || die "inbox_size_rejected:$src:$size"
  src_sha="$(sha256sum "$src" | awk '{print $1}')"
  tmp="$dst.tmp"
  install -m 0640 -o botmarket-github -g botmarket-github "$src" "$tmp"
  dst_sha="$(sha256sum "$tmp" | awk '{print $1}')"
  [[ "$src_sha" == "$dst_sha" ]] || die "inbox_copy_sha_mismatch:$src"
  mv "$tmp" "$dst"
  printf '%s' "$src_sha"
}

validate_smoke() {
  [[ -f "$SMOKE" ]] || die "smoke_missing"
  python3 - "$SMOKE" <<'PY'
import json,sys,urllib.parse
from pathlib import Path
o=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
def req(cond,code):
    if not cond:
        raise SystemExit(f"SMOKE_VALIDATION_FAILED:{code}")

req(o.get("schema")=="sc001.b15p2_announcement_body_dual_schema_smoke.v0.1.7","SCHEMA")
req(o.get("status") in {
    "B15P2_ANNOUNCEMENT_BODY_DUAL_SCHEMA_SMOKE_V017_PASS",
    "B15P2_ANNOUNCEMENT_BODY_DUAL_SCHEMA_SMOKE_V017_REVIEW",
},"STATUS")
req(o.get("article_body_text_persisted") is False,"ARTICLE_TEXT")
req(o.get("semantic_classification_performed") is False,"SEMANTIC")
for k in ("price_accessed","external_reference_price_accessed","index_value_accessed","basis_accessed","returns_accessed","pnl_accessed"):
    req(o.get(k) is False,k.upper())

rows=o.get("events")
req(isinstance(rows,list) and len(rows)<=4,"ROWS")
if o.get("status")=="B15P2_ANNOUNCEMENT_BODY_DUAL_SCHEMA_SMOKE_V017_PASS":
    req(len(rows)==4,"PASS_ROWS")
    req(sum(1 for r in rows if r.get("schema")=="BLT_RICHTEXT")==2,"A_COUNT")
    req(sum(1 for r in rows if r.get("schema")=="DOUBLE_DASH_ART_HTML")==2,"B_COUNT")
    for r in rows:
        req(isinstance(r.get("body_length"),int) and r["body_length"]>=120,"BODY_LENGTH")
        if r.get("schema")=="BLT_RICHTEXT":
            req(r.get("body_path")=="$.props.pageProps.articleDetail.content.json.children","A_PATH")
            req(r.get("secondary_match") is True,"A_SECONDARY")
        elif r.get("schema")=="DOUBLE_DASH_ART_HTML":
            req(r.get("body_path")=="$.props.pageProps.articleDetail.content_html","B_PATH")
            req(r.get("secondary_present") is None,"B_SECONDARY")
            req(isinstance(r.get("raw_body_html_tag_count"),int) and r["raw_body_html_tag_count"]>=2,"B_HTML_TAGS")
        else:
            req(False,"UNKNOWN_SCHEMA")
PY
}

validate_terminal() {
  [[ -f "$OUT" ]] || die "terminal_result_missing"
  python3 - "$OUT" "$EXPECTED_EVENT_SET_SHA" <<'PY'
import json,sys
from pathlib import Path
o=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
event_sha=sys.argv[2]
def req(cond,code):
    if not cond:
        raise SystemExit(f"RESULT_VALIDATION_FAILED:{code}")

req(o.get("schema")=="sc001.b15p2_announcement_body_semantic_audit_result.v0.1","SCHEMA")
req(o.get("status") in {
    "B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_PASS",
    "B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_REVIEW",
},"STATUS")
if o.get("frozen_event_set_sha256") is not None:
    req(o.get("frozen_event_set_sha256")==event_sha,"EVENT_SET_SHA")

fw=o.get("firewalls") or {}
for k,v in fw.items():
    if k.endswith(("accessed","calculated")) or k=="event_ranked_by_outcome":
        req(v is False,f"FIREWALL_{k}")

ex=o.get("body_extraction")
if ex is not None:
    req(ex.get("source")=="__NEXT_DATA__","SOURCE")
    req(ex.get("routing_source")=="frozen requested announcement URL","ROUTING_SOURCE")
    req((ex.get("schema_a") or {}).get("body_path")=="$.props.pageProps.articleDetail.content.json.children","A_PATH")
    req((ex.get("schema_b") or {}).get("body_path")=="$.props.pageProps.articleDetail.content_html","B_PATH")
    req(ex.get("adaptive_fallback_paths") is False,"NO_FALLBACK")

for r in o.get("events") or []:
    req(r.get("body_source")=="NEXT_DATA_DUAL_SCHEMA","BODY_SOURCE")
    schema=r.get("hydration_schema")
    if schema=="BLT_RICHTEXT":
        req(r.get("hydration_body_path")=="$.props.pageProps.articleDetail.content.json.children","ROW_A_PATH")
        if r.get("hydration_secondary_present") is True:
            req(r.get("hydration_secondary_match") is True,"ROW_A_SECONDARY")
    elif schema=="DOUBLE_DASH_ART_HTML":
        req(r.get("hydration_body_path")=="$.props.pageProps.articleDetail.content_html","ROW_B_PATH")
        req(isinstance(r.get("hydration_raw_body_html_tag_count"),int) and r["hydration_raw_body_html_tag_count"]>=2,"ROW_B_HTML_TAGS")
    else:
        req(False,"ROW_UNKNOWN_SCHEMA")

if o.get("status")=="B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_PASS":
    req(o.get("event_count_expected")==94,"PASS_EXPECTED")
    req(o.get("page_fetch_success_count")==94,"PASS_SUCCESS")
    req(o.get("page_fetch_error_count")==0,"PASS_ERRORS")
    req(o.get("exact_time_match_count")==94,"PASS_TIME")
    req(len(o.get("unresolved_symbols") or [])==0,"PASS_UNRESOLVED")
    req(len(o.get("time_mismatch_or_unresolved_symbols") or [])==0,"PASS_TIME_UNRESOLVED")
    req(o.get("hydration_schema_counts")=={"BLT_RICHTEXT":76,"DOUBLE_DASH_ART_HTML":18},"PASS_SCHEMA_COUNTS")

print(o.get("status"))
PY
}

publish_artifacts() {
  ensure_inbox_dir
  local smoke_sha="" result_sha="" log_sha="" status=""

  if [[ -f "$SMOKE" ]]; then
    validate_smoke
    smoke_sha="$(copy_exact "$SMOKE" "$INBOX_SMOKE" 524288)"
  fi
  if [[ -f "$OUT" ]]; then
    status="$(validate_terminal)"
    result_sha="$(copy_exact "$OUT" "$INBOX_RESULT" 2097152)"
  fi
  if [[ -f "$LOG" ]]; then
    log_sha="$(copy_exact "$LOG" "$INBOX_LOG" 1048576)"
  fi

  local tmp="$INBOX_META.tmp"
  python3 - "$status" "$smoke_sha" "$result_sha" "$log_sha" > "$tmp" <<'PY'
import datetime,json,sys
status,smoke_sha,result_sha,log_sha=sys.argv[1:5]
print(json.dumps({
  "schema":"sc001.b15p2_dual_schema_semantic_publish_meta.v0.2",
  "published_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
  "terminal_status":status or None,
  "smoke_relative_path":"docs/research/runtime-inbox/sc001-b15p2-dual-schema-smoke-v0.1.7-latest.json" if smoke_sha else None,
  "smoke_sha256":smoke_sha or None,
  "result_relative_path":"docs/research/runtime-inbox/sc001-b15p2-semantic-audit-v0.1.7-latest.json" if result_sha else None,
  "result_sha256":result_sha or None,
  "log_relative_path":"docs/research/runtime-inbox/sc001-b15p2-semantic-audit-v0.1.7-latest.log" if log_sha else None,
  "log_sha256":log_sha or None,
  "content_mutated":False
},indent=2,sort_keys=True))
PY
  chown botmarket-github:botmarket-github "$tmp"
  chmod 0640 "$tmp"
  mv "$tmp" "$INBOX_META"

  [[ -z "$smoke_sha" ]] || echo "runtime_inbox_smoke=$INBOX_SMOKE_REL"
  [[ -z "$result_sha" ]] || echo "runtime_inbox_result=$INBOX_RESULT_REL"
  [[ -z "$log_sha" ]] || echo "runtime_inbox_log=$INBOX_LOG_REL"
  echo "runtime_inbox_meta=$INBOX_META_REL"
}

show_summary() {
  if [[ -f "$OUT" ]]; then
    python3 - "$OUT" <<'PY'
import json,sys
from pathlib import Path
o=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print("result_status =",o.get("status"))
print("page_fetch_success =",o.get("page_fetch_success_count"))
print("page_fetch_errors =",o.get("page_fetch_error_count"))
print("exact_time_matches =",o.get("exact_time_match_count"))
print("automatic_close_explicit =",o.get("automatic_close_explicit_count"))
print("active_order_cancel_explicit =",o.get("active_order_auto_cancel_explicit_count"))
print("trading_stop_explicit =",o.get("trading_stop_explicit_count"))
print("schema_counts =",json.dumps(o.get("hydration_schema_counts"),sort_keys=True))
print("basis_counts =",json.dumps(o.get("closing_price_basis_counts"),sort_keys=True))
print("window_minute_counts =",json.dumps(o.get("closing_price_window_minute_counts"),sort_keys=True))
print("funding_mentioned =",o.get("funding_mentioned_count"))
print("revision_wording =",o.get("revision_wording_count"))
print("unresolved_count =",len(o.get("unresolved_symbols") or []))
print("time_mismatch_or_unresolved_count =",len(o.get("time_mismatch_or_unresolved_symbols") or []))
PY
  fi
}

run_all() {
  need_root
  check_tools
  local preflight_out preflight_rc
  set +e
  preflight_out="$(contract_preflight 2>&1)"
  preflight_rc="$?"
  set -e
  if [[ "$preflight_rc" -ne 0 ]]; then
    publish_prelaunch_diagnostic "PREFLIGHT" "CONTRACT_PREFLIGHT_FAILED" "$preflight_rc" "$preflight_out" || true
    printf '%s\n' "$preflight_out"
    die "contract_preflight_failed"
  fi
  printf '%s\n' "$preflight_out"

  [[ ! -e "$OUT" ]] || die "existing_terminal_result_forbidden"
  [[ ! -e "$SMOKE" ]] || die "existing_smoke_forbidden"
  [[ ! -e "$LOG" ]] || die "existing_log_forbidden"

  rm -rf "$STAGE"
  install -d -m 0750 -o root -g botmarket "$STAGE"

  stage_one() {
    local rel="$1" expected="$2" src="$REPO/$1" dst="$STAGE/$1" actual
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
  stage_one "$IMPLEMENTATION_FREEZE_REL" "$EXPECTED_IMPLEMENTATION_FREEZE_SHA"
  stage_one "$DUAL_ROUTING_REL" "$EXPECTED_DUAL_ROUTING_SHA"
  stage_one "$ART_CENSUS_RESULT_REL" "$EXPECTED_ART_CENSUS_RESULT_SHA"
  stage_one "$SOURCE_REL" "$EXPECTED_SOURCE_SHA"
  stage_one "$EVENT_FREEZE_REL" "$EXPECTED_EVENT_FREEZE_SHA"

  [[ -z "$(find "$STAGE" -type l -print -quit)" ]] || die "staging_symlink_detected"
  local stage_count
  stage_count="$(find "$STAGE" -type f | wc -l | awk '{print $1}')"
  [[ "$stage_count" == "7" ]] || die "unexpected_staging_file_count:$stage_count"

  local staged_script="$STAGE/$SCRIPT_REL"
  local selftest_out selftest_rc
  set +e
  selftest_out="$(
    sudo -u botmarket -H env -i       HOME=/home/botmarket       PATH=/usr/bin:/bin       B15P2_REPO_ROOT="$STAGE"       SC001_DATA_ROOT="$DATA_ROOT"       /usr/bin/python3 "$staged_script" --mode self-test 2>&1
  )"
  selftest_rc="$?"
  set -e

  if [[ "$selftest_rc" -ne 0 ]]; then
    publish_prelaunch_diagnostic "SELF_TEST" "SELF_TEST_EXIT_NONZERO" "$selftest_rc" "$selftest_out" || true
    printf '%s\n' "$selftest_out"
    die "staged_selftest_failed"
  fi

  if ! printf '%s\n' "$selftest_out" | grep -qx "$SELFTEST_PASS"; then
    publish_prelaunch_diagnostic "SELF_TEST" "SELF_TEST_PASS_TOKEN_MISSING" "0" "$selftest_out" || true
    printf '%s\n' "$selftest_out"
    die "selftest_pass_token_missing"
  fi

  echo "$SELFTEST_PASS"

  install -d -m 0750 -o botmarket -g botmarket "$OUT_DIR"
  : > "$LOG"
  chown botmarket:botmarket "$LOG"
  chmod 0640 "$LOG"

  echo "dual_schema_smoke=START"
  set +e
  sudo -u botmarket -H env -i     HOME=/home/botmarket     PATH=/usr/bin:/bin     B15P2_REPO_ROOT="$STAGE"     SC001_DATA_ROOT="$DATA_ROOT"     timeout 180     /usr/bin/python3 "$staged_script" --mode dual-schema-smoke >> "$LOG" 2>&1
  local smoke_rc="$?"
  set -e

  validate_smoke || {
    publish_artifacts || true
    tail -n 30 "$LOG" || true
    die "dual_schema_smoke_validation_failed"
  }

  if [[ "$smoke_rc" -ne 0 ]]; then
    publish_artifacts || true
    tail -n 30 "$LOG" || true
    die "dual_schema_smoke_failed:$smoke_rc"
  fi

  grep -qx "$SMOKE_PASS" "$LOG" || die "smoke_pass_token_missing"
  echo "dual_schema_smoke=PASS"

  echo "full_94_semantic_audit=START"
  set +e
  sudo -u botmarket -H env -i     HOME=/home/botmarket     PATH=/usr/bin:/bin     B15P2_REPO_ROOT="$STAGE"     SC001_DATA_ROOT="$DATA_ROOT"     timeout 4200     /usr/bin/python3 "$staged_script" --mode live >> "$LOG" 2>&1
  local live_rc="$?"
  set -e

  validate_terminal
  publish_artifacts
  show_summary

  if [[ "$live_rc" -ne 0 ]]; then
    echo "full_94_semantic_audit=REVIEW_OR_FAILURE"
    echo "live_exit_code=$live_rc"
    exit "$live_rc"
  fi

  grep -qx "$PASS" "$LOG" || die "terminal_pass_token_missing"
  echo "B15P2_DUAL_SCHEMA_SEMANTIC_AUDIT_V02_HOST_PASS"
  echo "price/index-values/basis/returns/PnL=CLOSED"
}

case "${1:-}" in
  --run)
    run_all
    ;;
  --preflight)
    contract_preflight
    ;;
  --status)
    show_summary
    publish_artifacts
    ;;
  *)
    echo "Usage:"
    echo "  sudo bash $0 --run"
    echo "  sudo bash $0 --preflight"
    echo "  sudo bash $0 --status"
    exit 2
    ;;
esac
