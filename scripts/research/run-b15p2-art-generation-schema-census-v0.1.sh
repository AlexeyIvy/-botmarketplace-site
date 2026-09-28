#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

REPO="/var/lib/botmarket-github-control/repo"
STAGE="/home/botmarket/.local/share/botmarket/b15p2-art-schema-census-v0.1-stage"
DATA_ROOT="/home/botmarket/sc001_data"
OUT_DIR="$DATA_ROOT/SC001_B15P2_ART_GENERATION_SCHEMA_CENSUS"
OUT="$OUT_DIR/art_generation_schema_census_v0_1.json"
LOG="$OUT_DIR/art_generation_schema_census_v0_1.log"

INBOX_DIR="$REPO/docs/research/runtime-inbox"
INBOX_RESULT_REL="docs/research/runtime-inbox/sc001-b15p2-art-generation-schema-census-v0.1-latest.json"
INBOX_RESULT="$REPO/$INBOX_RESULT_REL"
INBOX_LOG_REL="docs/research/runtime-inbox/sc001-b15p2-art-generation-schema-census-v0.1-latest.log"
INBOX_LOG="$REPO/$INBOX_LOG_REL"
INBOX_META_REL="docs/research/runtime-inbox/sc001-b15p2-art-generation-schema-census-v0.1-latest.meta.json"
INBOX_META="$REPO/$INBOX_META_REL"

SCRIPT_REL="scripts/research/probe-b15p2-art-generation-schema-census-v0.1.py"
SOURCE_REL="docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_result.v0.1.1.json"
FREEZE_REL="docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_event_set_freeze.v0.1.json"

EXPECTED_SCRIPT_SHA="7ee2057a3c66e0b4a3f08b0f23a16df295abc3a4e7fcf88a71e29543b2f06de0"
EXPECTED_SOURCE_SHA="c28aeb2b1ac0a23fb0e4420ced943fd619dd0a60e3fdcf5820299579cb94206c"
EXPECTED_FREEZE_SHA="81952c83e7397481035cc00354388dfe3470ad17993c6e80665a7d376be907ed"
EXPECTED_EVENT_SET_SHA="1063695ec003a0d6789270659822f50577e6a0f07059d88ac03a5be4288ed1a2"

SELFTEST_PASS="B15P2_ART_GENERATION_SCHEMA_CENSUS_V01_SELF_TEST_PASS"
COMPLETE="B15P2_ART_GENERATION_SCHEMA_CENSUS_V01_COMPLETE"
REVIEW="B15P2_ART_GENERATION_SCHEMA_CENSUS_V01_REVIEW"

die() {
  echo "B15P2_ART_SCHEMA_CENSUS_HOST_REVIEW"
  echo "reason=$1"
  echo "semantic_classification_performed=False"
  echo "price/index-values/basis/returns/PnL=CLOSED"
  exit 2
}

need_root() {
  [[ "${EUID:-$(id -u)}" -eq 0 ]] || die "wrapper_must_run_as_root"
}

check_tools() {
  local cmd
  for cmd in sha256sum awk install sudo python3 curl grep find wc chown chmod rm cat tail mv dirname env tee test stat; do
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
  check_source "$SOURCE_REL" "$EXPECTED_SOURCE_SHA"
  check_source "$FREEZE_REL" "$EXPECTED_FREEZE_SHA"

  python3 - "$REPO/$SOURCE_REL" "$REPO/$FREEZE_REL" "$EXPECTED_EVENT_SET_SHA" <<'PY'
import json,re,sys,urllib.parse
from pathlib import Path

src=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
fr=json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
event_sha=sys.argv[3]

def req(cond,code):
    if not cond:
        raise SystemExit(f"PRECHECK_FAILED:{code}")

req(src.get("status")=="B15P2_BYBIT_DELISTING_SOURCE_CENSUS_PASS","SOURCE_STATUS")
req(src.get("admitted_event_count")==94,"SOURCE_COUNT")
req(src.get("announcement_match_coverage")==1.0,"SOURCE_COVERAGE")
req(src.get("source_integrity_issue_count")==0,"SOURCE_INTEGRITY")
req(fr.get("status")=="B15P2_EXACT_ADMITTED_EVENT_SET_FROZEN","FREEZE_STATUS")
req(fr.get("event_count")==94,"FREEZE_COUNT")
req(fr.get("event_set_sha256")==event_sha,"EVENT_SET_SHA")

pat=re.compile(r"--art[0-9a-f]+/?$",re.I)
selected=[]
for e in src.get("events") or []:
    urls=e.get("announcement_urls")
    req(isinstance(urls,list) and len(urls)==1,f"URL_COUNT:{e.get('symbol')}")
    u=urls[0]
    p=urllib.parse.urlparse(u)
    req(p.scheme=="https" and p.hostname=="announcements.bybit.com",f"URL_POLICY:{e.get('symbol')}")
    if pat.search(p.path):
        selected.append((e.get("symbol"),u))

req(len(selected)==18,f"ART_EVENT_COUNT:{len(selected)}")
req(len({u for _,u in selected})==18,"ART_URL_UNIQUENESS")

for key in ("price_accessed","basis_calculated","pnl_calculated","event_ranked_by_outcome","settlement_semantics_interpreted"):
    req(src.get(key) is False,f"SOURCE_{key.upper()}")

print("B15P2_ART_SCHEMA_CENSUS_HOST_PREFLIGHT_PASS")
print("frozen_events=94")
print("selected_art_generation_events=18")
print("selection_rule=FROZEN_URL_DOUBLE_DASH_ART")
print("semantic_classification_performed=False")
print("price/index-values/basis/returns/PnL=CLOSED")
PY
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

validate_result() {
  [[ -f "$OUT" ]] || die "result_missing"
  python3 - "$OUT" <<'PY'
import json,re,sys,urllib.parse
from pathlib import Path

o=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
def req(cond,code):
    if not cond:
        raise SystemExit(f"RESULT_VALIDATION_FAILED:{code}")

req(o.get("schema")=="sc001.b15p2_art_generation_schema_census.v0.1","SCHEMA")
req(o.get("status") in {
    "B15P2_ART_GENERATION_SCHEMA_CENSUS_V01_COMPLETE",
    "B15P2_ART_GENERATION_SCHEMA_CENSUS_V01_REVIEW",
},"STATUS")

req(o.get("article_body_text_persisted") is False,"ARTICLE_TEXT")
req(o.get("semantic_classification_performed") is False,"SEMANTIC")
for k in ("price_accessed","external_reference_price_accessed","index_value_accessed","basis_accessed","returns_accessed","pnl_accessed"):
    req(o.get(k) is False,k.upper())

rows=o.get("events")
req(isinstance(rows,list) and len(rows)<=18,"EVENT_ROWS")
pat=re.compile(r"--art[0-9a-f]+/?$",re.I)
for i,r in enumerate(rows):
    u=r.get("requested_url") or ""
    p=urllib.parse.urlparse(u)
    req(p.scheme=="https" and p.hostname=="announcements.bybit.com",f"URL_POLICY_{i}")
    req(bool(pat.search(p.path)),f"URL_GENERATION_{i}")

if o.get("status")=="B15P2_ART_GENERATION_SCHEMA_CENSUS_V01_COMPLETE":
    sel=o.get("selection") or {}
    req(sel.get("expected_event_count")==18,"EXPECTED_COUNT")
    req(sel.get("selected_event_count")==18,"SELECTED_COUNT")
    req(sel.get("selection_uses_semantic_or_price_outcomes") is False,"SELECTION_OUTCOME")
    req(len(rows)==18,"COMPLETE_ROWS")
    req(isinstance(o.get("consensus"),dict),"CONSENSUS")

print(o.get("status"))
PY
}

publish_result() {
  validate_result >/dev/null
  ensure_inbox_dir

  local result_sha log_sha status
  result_sha="$(copy_exact "$OUT" "$INBOX_RESULT" 2097152)"
  log_sha=""
  if [[ -f "$LOG" ]]; then
    log_sha="$(copy_exact "$LOG" "$INBOX_LOG" 524288)"
  fi
  status="$(python3 - "$OUT" <<'PY'
import json,sys
from pathlib import Path
print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")).get("status") or "")
PY
)"

  local tmp="$INBOX_META.tmp"
  python3 - "$status" "$result_sha" "$log_sha" > "$tmp" <<'PY'
import datetime,json,sys
status,result_sha,log_sha=sys.argv[1:4]
print(json.dumps({
  "schema":"sc001.b15p2_art_generation_schema_census_publish_meta.v0.1",
  "published_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
  "status":status,
  "result_relative_path":"docs/research/runtime-inbox/sc001-b15p2-art-generation-schema-census-v0.1-latest.json",
  "result_sha256":result_sha,
  "log_relative_path":"docs/research/runtime-inbox/sc001-b15p2-art-generation-schema-census-v0.1-latest.log" if log_sha else None,
  "log_sha256":log_sha or None,
  "content_mutated":False
},indent=2,sort_keys=True))
PY
  chown botmarket-github:botmarket-github "$tmp"
  chmod 0640 "$tmp"
  mv "$tmp" "$INBOX_META"

  echo "runtime_inbox_result=$INBOX_RESULT_REL"
  echo "runtime_inbox_result_sha256=$result_sha"
  [[ -z "$log_sha" ]] || echo "runtime_inbox_log=$INBOX_LOG_REL"
  echo "runtime_inbox_meta=$INBOX_META_REL"
}

show_status() {
  need_root
  check_tools
  if [[ -f "$OUT" ]]; then
    python3 - "$OUT" <<'PY'
import json,sys
from pathlib import Path
o=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print("result_status =",o.get("status"))
print("events =",len(o.get("events") or []))
c=o.get("consensus") or {}
print("exact_title_identities =",json.dumps([
    {"identity":x.get("identity"),"event_count":x.get("event_count")}
    for x in (c.get("exact_title_identities") or [])[:10]
],sort_keys=True))
print("common_candidates =",c.get("common_candidate_count"))
print("common_high_confidence =",c.get("common_high_confidence_candidate_count"))
for x in (c.get("common_candidates") or [])[:12]:
    print(
        "COMMON_CANDIDATE",
        "identity="+str(x.get("identity")),
        "events="+str(x.get("event_count")),
        "title_coupled="+str(x.get("title_document_event_count")),
        "min_score="+str(x.get("min_score")),
        "min_chars="+str(x.get("min_chars")),
        "max_chars="+str(x.get("max_chars")),
    )
PY
    publish_result
  else
    echo "result_status=ABSENT"
  fi

  if [[ -f "$LOG" ]]; then
    echo "--- log tail ---"
    tail -n 30 "$LOG"
  fi
}

run_census() {
  need_root
  check_tools
  contract_preflight

  [[ ! -e "$OUT" ]] || die "existing_result_forbidden"
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
  stage_one "$SOURCE_REL" "$EXPECTED_SOURCE_SHA"
  stage_one "$FREEZE_REL" "$EXPECTED_FREEZE_SHA"

  [[ -z "$(find "$STAGE" -type l -print -quit)" ]] || die "staging_symlink_detected"
  local stage_count
  stage_count="$(find "$STAGE" -type f | wc -l | awk '{print $1}')"
  [[ "$stage_count" == "3" ]] || die "unexpected_staging_file_count:$stage_count"

  local staged_script="$STAGE/$SCRIPT_REL"
  local selftest_out
  if selftest_out="$(
    sudo -u botmarket -H env -i       HOME=/home/botmarket       PATH=/usr/bin:/bin       B15P2_REPO_ROOT="$STAGE"       /usr/bin/python3 "$staged_script" --mode self-test 2>&1
  )"; then
    :
  else
    printf '%s\n' "$selftest_out"
    die "staged_selftest_failed"
  fi
  printf '%s\n' "$selftest_out"
  printf '%s\n' "$selftest_out" | grep -qx "$SELFTEST_PASS" || die "selftest_pass_token_missing"

  install -d -m 0750 -o botmarket -g botmarket "$OUT_DIR"
  : > "$LOG"
  chown botmarket:botmarket "$LOG"
  chmod 0640 "$LOG"

  set +e
  sudo -u botmarket -H env -i     HOME=/home/botmarket     PATH=/usr/bin:/bin     B15P2_REPO_ROOT="$STAGE"     /usr/bin/python3 "$staged_script" --mode live 2>&1 | /usr/bin/tee -a "$LOG"
  local pipe_status=("${PIPESTATUS[@]}")
  set -e

  local python_rc="${pipe_status[0]:-125}"
  local tee_rc="${pipe_status[1]:-125}"

  [[ "$tee_rc" -eq 0 ]] || die "tee_failed:$tee_rc"

  validate_result
  publish_result

  if [[ "$python_rc" -ne 0 ]]; then
    die "census_review_or_failure:$python_rc"
  fi

  grep -qx "$COMPLETE" "$LOG" || die "complete_token_missing"

  echo "B15P2_ART_GENERATION_SCHEMA_CENSUS_V01_HOST_PASS"
  echo "selected_events=18"
  echo "runtime_inbox_result=$INBOX_RESULT_REL"
  echo "semantic_classification_performed=False"
  echo "price/index-values/basis/returns/PnL=CLOSED"
}

case "${1:-}" in
  --run)
    run_census
    ;;
  --status)
    show_status
    ;;
  --preflight)
    contract_preflight
    ;;
  *)
    echo "Usage:"
    echo "  sudo bash $0 --run"
    echo "  sudo bash $0 --status"
    echo "  sudo bash $0 --preflight"
    exit 2
    ;;
esac
