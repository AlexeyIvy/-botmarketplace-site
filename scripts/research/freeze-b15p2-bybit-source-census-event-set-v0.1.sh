#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

REPO="/var/lib/botmarket-github-control/repo"
SRC="/home/botmarket/sc001_data/SC001_B15P2_BYBIT_DELISTING_SOURCE_CENSUS/sc001_b15p2_bybit_delisting_source_census_v0_1_1.json"
ART_REL="docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z"
DST="$REPO/$ART_REL/source_census_result.v0.1.1.json"
FREEZE="$REPO/$ART_REL/source_census_event_set_freeze.v0.1.json"

die() {
  echo "B15P2_SOURCE_CENSUS_EVENT_SET_FREEZE_REVIEW"
  echo "reason=$1"
  exit 2
}

need_root() {
  [[ "${EUID:-$(id -u)}" -eq 0 ]] || die "wrapper_must_run_as_root"
}

check_tools() {
  local cmd
  for cmd in python3 sha256sum install stat git chown chmod dirname find; do
    command -v "$cmd" >/dev/null 2>&1 || die "required_command_missing:$cmd"
  done
}

validate_source() {
  [[ -d "$REPO/.git" ]] || die "repo_missing"
  [[ -f "$SRC" ]] || die "source_result_missing"
  [[ ! -L "$SRC" ]] || die "source_result_symlink_forbidden"
  [[ -z "$(git -C "$REPO" status --porcelain=v1 --untracked-files=all)" ]] || die "github_control_repo_not_clean"

  python3 - "$SRC" <<'PY'
import json
import math
import re
import sys
from pathlib import Path

p=Path(sys.argv[1])
obj=json.loads(p.read_text(encoding="utf-8"))

def require(cond, code):
    if not cond:
        raise SystemExit(f"FREEZE_PRECHECK_FAILED:{code}")

expected_top={
    "stage","version","window","announcement_source","instrument_source",
    "status","closed_in_scope_count","admitted_event_count","unmatched_symbols",
    "announcement_match_coverage","delivery_months","lead_hours",
    "source_integrity_issue_count","source_integrity_issues","gates","events",
    "price_accessed","basis_calculated","pnl_calculated","event_ranked_by_outcome",
    "settlement_semantics_interpreted","next_state"
}
require(set(obj)==expected_top,"TOP_LEVEL_SCHEMA")
require(obj["stage"]=="SC001-B15P2-BYBIT-DELISTING-SOURCE-CENSUS-V0.1.1","STAGE")
require(obj["version"]=="0.1.1","VERSION")
require(obj["status"]=="B15P2_BYBIT_DELISTING_SOURCE_CENSUS_PASS","STATUS")

window=obj["window"]
require(isinstance(window,dict),"WINDOW_OBJECT")
require(window.get("start_ms")==1767225600000,"WINDOW_START")
require(window.get("end_exclusive_ms")==1790467200000,"WINDOW_END")

ann=obj["announcement_source"]
require(isinstance(ann,dict),"ANNOUNCEMENT_SOURCE_OBJECT")
require(ann.get("endpoint")=="/v5/announcements/index","ANNOUNCEMENT_ENDPOINT")
require(ann.get("locale")=="en-US","ANNOUNCEMENT_LOCALE")
require(ann.get("type")=="delistings","ANNOUNCEMENT_TYPE")
require(ann.get("retrieved_count")==479,"ANNOUNCEMENT_COUNT")
require(ann.get("derivative_relevant_count")==271,"DERIVATIVE_RELEVANT_COUNT")
require(ann.get("missing_publish_time_count")==32,"MISSING_PUBLISHTIME_COUNT")
require(ann.get("invalid_publish_time_count")==0,"INVALID_PUBLISHTIME_COUNT")
require(ann.get("date_timestamp_is_never_publish_fallback") is True,"DATE_TIMESTAMP_FIREWALL")

inst=obj["instrument_source"]
require(isinstance(inst,dict),"INSTRUMENT_SOURCE_OBJECT")
require(inst.get("endpoint")=="/v5/market/instruments-info","INSTRUMENT_ENDPOINT")
require(inst.get("category")=="linear","INSTRUMENT_CATEGORY")
require(inst.get("status")=="Closed","INSTRUMENT_STATUS")
require(inst.get("in_scope_count")==94,"INSTRUMENT_COUNT")

require(obj["closed_in_scope_count"]==94,"CLOSED_COUNT")
require(obj["admitted_event_count"]==94,"ADMITTED_COUNT")
require(obj["unmatched_symbols"]==[],"UNMATCHED_SYMBOLS")
require(obj["announcement_match_coverage"]==1.0,"COVERAGE")
require(obj["delivery_months"]==[
    "2026-01","2026-02","2026-03","2026-04","2026-05",
    "2026-06","2026-07","2026-08","2026-09"
],"DELIVERY_MONTHS")
require(obj["source_integrity_issue_count"]==0,"SOURCE_INTEGRITY_COUNT")
require(obj["source_integrity_issues"]==[],"SOURCE_INTEGRITY_ISSUES")

gates=obj["gates"]
expected_gate_keys={
    "closed_perpetuals_ge5","admitted_events_ge5",
    "announcement_match_coverage_ge80pct","all_admitted_positive_lead",
    "delivery_months_ge3","matched_source_timestamp_integrity"
}
require(set(gates)==expected_gate_keys,"GATE_SCHEMA")
require(all(gates.values()),"GATES_NOT_ALL_TRUE")

for k in ("price_accessed","basis_calculated","pnl_calculated","event_ranked_by_outcome","settlement_semantics_interpreted"):
    require(obj[k] is False,f"FIREWALL_{k.upper()}")

require(obj["next_state"]=="FREEZE_ADMITTED_EVENT_SET_AND_RUN_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT","NEXT_STATE")

lead=obj["lead_hours"]
for k in ("min","p25","median","p75","max"):
    require(isinstance(lead.get(k),(int,float)) and math.isfinite(float(lead[k])),f"LEAD_{k.upper()}")
require(0 < lead["min"] <= lead["p25"] <= lead["median"] <= lead["p75"] <= lead["max"],"LEAD_ORDER")

events=obj["events"]
require(isinstance(events,list) and len(events)==94,"EVENT_COUNT")
seen=set()
for i,e in enumerate(events):
    require(isinstance(e,dict),f"EVENT_{i}_OBJECT")
    expected_event_keys={
        "venue","symbol","delivery_ms","delivery_utc","first_notice_ms",
        "last_pre_event_notice_ms","notice_count","pre_launch_match_count",
        "post_delivery_match_count","lead_hours","announcement_urls","delivery_month"
    }
    require(set(e)==expected_event_keys,f"EVENT_{i}_SCHEMA")
    require(e["venue"]=="BYBIT",f"EVENT_{i}_VENUE")
    require(isinstance(e["symbol"],str) and e["symbol"].endswith("USDT"),f"EVENT_{i}_SYMBOL")
    require(re.fullmatch(r"[A-Z0-9]+USDT",e["symbol"]) is not None,f"EVENT_{i}_SYMBOL_FORMAT")
    require(window["start_ms"] <= e["delivery_ms"] < window["end_exclusive_ms"],f"EVENT_{i}_DELIVERY_WINDOW")
    require(e["first_notice_ms"] < e["delivery_ms"],f"EVENT_{i}_FIRST_NOTICE_CAUSAL")
    require(e["last_pre_event_notice_ms"] < e["delivery_ms"],f"EVENT_{i}_LAST_NOTICE_CAUSAL")
    require(e["first_notice_ms"] <= e["last_pre_event_notice_ms"],f"EVENT_{i}_NOTICE_ORDER")
    require(isinstance(e["notice_count"],int) and e["notice_count"]>=1,f"EVENT_{i}_NOTICE_COUNT")
    require(isinstance(e["lead_hours"],(int,float)) and e["lead_hours"]>0,f"EVENT_{i}_LEAD")
    expected_lead=(e["delivery_ms"]-e["first_notice_ms"])/3_600_000.0
    require(abs(float(e["lead_hours"])-expected_lead)<1e-9,f"EVENT_{i}_LEAD_RECALC")
    require(isinstance(e["announcement_urls"],list) and len(e["announcement_urls"])==e["notice_count"],f"EVENT_{i}_URL_COUNT")
    for u in e["announcement_urls"]:
        require(isinstance(u,str) and u.startswith("https://announcements.bybit.com/"),f"EVENT_{i}_URL_DOMAIN")
    key=(e["symbol"],e["delivery_ms"])
    require(key not in seen,f"EVENT_{i}_DUPLICATE_IDENTITY")
    seen.add(key)

print("B15P2_SOURCE_CENSUS_EVENT_SET_FREEZE_PREFLIGHT_PASS")
print("events=94")
print("coverage=1.0")
print("source_integrity_issues=0")
print("price/basis/PnL= CLOSED")
PY
}

promote() {
  validate_source
  [[ ! -e "$DST" ]] || die "destination_result_already_exists"
  [[ ! -e "$FREEZE" ]] || die "destination_freeze_already_exists"

  install -d -m 0750 -o botmarket-github -g botmarket-github "$(dirname "$DST")"
  install -m 0640 -o botmarket-github -g botmarket-github "$SRC" "$DST"

  local src_sha dst_sha
  src_sha="$(sha256sum "$SRC" | awk '{print $1}')"
  dst_sha="$(sha256sum "$DST" | awk '{print $1}')"
  [[ "$src_sha" == "$dst_sha" ]] || die "promoted_result_sha_mismatch"

  python3 - "$DST" "$FREEZE" "$dst_sha" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

result_path=Path(sys.argv[1])
freeze_path=Path(sys.argv[2])
result_sha=sys.argv[3]
obj=json.loads(result_path.read_text(encoding="utf-8"))

core=[]
for e in sorted(obj["events"],key=lambda x:(x["delivery_ms"],x["symbol"])):
    core.append({
        "venue":e["venue"],
        "symbol":e["symbol"],
        "delivery_ms":e["delivery_ms"],
        "first_notice_ms":e["first_notice_ms"],
        "last_pre_event_notice_ms":e["last_pre_event_notice_ms"],
        "notice_count":e["notice_count"],
        "lead_hours":e["lead_hours"],
        "announcement_urls":e["announcement_urls"],
    })

canonical=json.dumps(core,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
event_digest=hashlib.sha256(canonical).hexdigest()

freeze={
    "schema":"sc001.b15p2_bybit_source_census_event_set_freeze.v0.1",
    "date":"2026-09-27",
    "status":"B15P2_EXACT_ADMITTED_EVENT_SET_FROZEN",
    "source_result":{
        "path":"docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_result.v0.1.1.json",
        "sha256":result_sha,
    },
    "event_identity":"BYBIT x EXACT_USDT_PERPETUAL_SYMBOL x DELIVERY_TIME",
    "event_count":len(core),
    "event_set_sha256":event_digest,
    "coverage":obj["announcement_match_coverage"],
    "delivery_months":obj["delivery_months"],
    "source_integrity_issue_count":obj["source_integrity_issue_count"],
    "firewalls":{
        "price_accessed":False,
        "basis_calculated":False,
        "pnl_calculated":False,
        "event_ranked_by_outcome":False,
    },
    "next_state":"ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_ONLY",
}
freeze_path.write_text(json.dumps(freeze,indent=2,sort_keys=True)+"\n",encoding="utf-8")
PY

  chown botmarket-github:botmarket-github "$FREEZE"
  chmod 0640 "$FREEZE"

  echo "B15P2_SOURCE_CENSUS_EVENT_SET_FREEZE_PROMOTION_PASS"
  echo "source_result_sha256=$dst_sha"
  echo "artifact_root=$ART_REL"
  echo "network_calls_performed=False"
  echo "price/basis/PnL=CLOSED"
}

case "${1:-}" in
  --preflight)
    need_root
    check_tools
    validate_source
    ;;
  --promote)
    need_root
    check_tools
    promote
    ;;
  *)
    echo "Usage:"
    echo "  sudo bash $0 --preflight"
    echo "  sudo bash $0 --promote"
    exit 2
    ;;
esac
