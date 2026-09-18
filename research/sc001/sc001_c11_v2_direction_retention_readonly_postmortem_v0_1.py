from __future__ import annotations

import json, os, statistics, subprocess
from pathlib import Path

STAGE="SC001-C11-V2-DIRECTION-RETENTION-READONLY-POSTMORTEM-V0.1"
PASS="C11_V2_DIRECTION_RETENTION_READONLY_POSTMORTEM_PASS"

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/"docs/research/sc001-c11-v2-direction-retention-readonly-postmortem-protocol-v0.1.md"
FREEZE=ROOT/"docs/research/sc001-c11-v2-direction-retention-readonly-postmortem-implementation-freeze-v0.1.json"
RESULT_DOC=ROOT/"docs/research/sc001-c11-v2-selection-stage-ab-result-v1.1.md"

DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
PARENT=DATA_ROOT/"SC001_C11_V2_SELECTION_AB"/"sc001_c11_v2_selection_stage_ab_report_v1_1.json"
OUT_DIR=DATA_ROOT/"SC001_C11_V2_POSTMORTEM"
OUT=OUT_DIR/"sc001_c11_v2_direction_retention_readonly_postmortem_v0_1.json"

def fail(m): raise RuntimeError(m)

def load_json(p):
    x=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(x,dict): fail(f"JSON object expected: {p}")
    return x

def atomic_json(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    t=Path(str(p)+".tmp")
    with t.open("w",encoding="utf-8") as f:
        json.dump(o,f,ensure_ascii=False,indent=2,sort_keys=True)
        f.write("\n"); f.flush(); os.fsync(f.fileno())
    os.replace(t,p)

def git_blob(p):
    return subprocess.check_output(["git","-C",str(ROOT),"hash-object",str(p.relative_to(ROOT))],text=True).strip()

def require():
    fr=load_json(FREEZE)
    if fr.get("status")!="FROZEN_BEFORE_C11_V2_READONLY_POSTMORTEM":
        fail("freeze status mismatch")
    checks={
        "runner_git_blob_sha":git_blob(Path(__file__).resolve()),
        "protocol_git_blob_sha":git_blob(PROTOCOL),
        "result_doc_git_blob_sha":git_blob(RESULT_DOC),
    }
    for k,v in checks.items():
        if fr.get(k)!=v: fail(f"freeze identity mismatch: {k}")

    p=load_json(PARENT)
    if p.get("status")!="C11_V2_SC_REJECT_DIRECTION_RETENTION":
        fail("parent status mismatch")
    if p.get("confirmation_outcome_accessed") is not False: fail("confirmation firewall mismatch")
    if p.get("execution_model_calculated") is not False: fail("execution firewall mismatch")
    if p.get("pnl_calculated") is not False: fail("pnl firewall mismatch")
    if int(p.get("scheduled_events",0))!=24: fail("scheduled count mismatch")
    return p

def med(vals):
    return statistics.median(vals) if vals else None

def main():
    try:
        p=require()
        rows=p.get("events") or []
        if len(rows)!=24: fail("event rows mismatch")

        valid=[r for r in rows if r.get("anchor_valid") is True]
        actionable=[r for r in rows if r.get("signal_state") in {"LONG","SHORT"}]
        large=[r for r in valid if (r.get("abs_residual_move_1s_to_60s_bps") or 0)>=20.0]

        captured=[r for r in large if r.get("signed_continuation_bps") is not None and r["signed_continuation_bps"]>=20.0]
        same_small=[r for r in large if r.get("signed_continuation_bps") is not None and 0<r["signed_continuation_bps"]<20.0]
        wrong=[r for r in large if r.get("signed_continuation_bps") is not None and r["signed_continuation_bps"]<=0.0]

        if len(wrong)>len(same_small):
            structure="FAILURE_CONCENTRATED_IN_WRONG_SIGN"
        elif len(same_small)>len(wrong):
            structure="FAILURE_CONCENTRATED_IN_TOO_SMALL_SAME_SIGN_MOVE"
        else:
            structure="MIXED_DIRECTION_CAPTURE_FAILURE"

        fam={}
        for kind in ("CPI","EMPLOYMENT"):
            g=[r for r in actionable if r.get("kind")==kind]
            signed=[r["signed_continuation_bps"] for r in g if r.get("signed_continuation_bps") is not None]
            fam[kind]={
                "actionable":len(g),
                "median_signed_continuation_bps":med(signed),
                "positive_signed_count":sum(1 for v in signed if v>0),
                "signed_gte20bps_count":sum(1 for v in signed if v>=20),
            }

        impulses=[abs(r["first_impulse_bps"]) for r in actionable if r.get("first_impulse_bps") is not None]
        signed=[r["signed_continuation_bps"] for r in actionable if r.get("signed_continuation_bps") is not None]

        out={
            "stage":STAGE,
            "version":"0.1",
            "status":PASS,
            "parent_terminal_state":p["status"],
            "classification":"RESIDUAL_HEADROOM_EXISTS_DIRECTION_CAPTURE_WEAK",
            "failure_structure":structure,
            "scheduled_events":24,
            "data_valid_events":len(valid),
            "actionable_events":len(actionable),
            "positive_signed_share":sum(1 for v in signed if v>0)/24.0,
            "median_abs_first_impulse_bps":med(impulses),
            "large_residual_events_gte20bps":len(large),
            "large_residual_capture": {
                "signed_gte20bps":len(captured),
                "same_sign_but_lt20bps":len(same_small),
                "wrong_or_zero_sign":len(wrong),
                "capture_share_among_large_residual":len(captured)/len(large) if large else None,
            },
            "family_descriptives":fam,
            "stage_a_median_abs_residual_bps":p["stage_a"]["median_abs_residual_bps"],
            "stage_b_median_signed_continuation_bps":p["stage_b"]["median_signed_continuation_bps"],
            "stage_b_positive_signed_count":p["stage_b"]["positive_signed_count_diagnostic"],
            "stage_b_signed_gte20bps_count":p["stage_b"]["events_signed_continuation_gte20bps"],
            "worst_signed_continuation_bps":p["stage_b"]["worst_signed_continuation_bps_diagnostic"],
            "best_signed_continuation_bps":p["stage_b"]["best_signed_continuation_bps_diagnostic"],
            "schema_counts":p.get("schema_counts"),
            "alternative_window_tested":False,
            "reversal_rule_scored":False,
            "alternative_threshold_tested":False,
            "alternative_horizon_tested":False,
            "macro_surprise_used":False,
            "execution_model_calculated":False,
            "pnl_calculated":False,
            "confirmation_outcome_accessed":False,
        }
        atomic_json(OUT,out)

        print(PASS)
        print("classification =",out["classification"])
        print("failure_structure =",out["failure_structure"])
        print("positive_signed_share =",out["positive_signed_share"])
        print("median_abs_first_impulse_bps =",out["median_abs_first_impulse_bps"])
        print("large_residual_capture =",out["large_residual_capture"])
        print("family_descriptives =",out["family_descriptives"])
        print("alternative/reversal/execution/PnL/Confirmation = False")
        print("report =",OUT)
        return 0
    except Exception as exc:
        print("C11_V2_READONLY_POSTMORTEM_IMPLEMENTATION_FAIL")
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2

if __name__=="__main__":
    raise SystemExit(main())
