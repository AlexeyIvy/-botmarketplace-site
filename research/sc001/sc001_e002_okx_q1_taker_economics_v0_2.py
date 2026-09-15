"""SC001-E002 OKX Q1 taker economics implementation adapter v0.2.

Pre-output implementation repair only. Loads the frozen v0.1 engine, updates
metadata/funding paths to the successful v0.3 preflight artifacts, and tightens
one execution-state edge case: after an entry is filled, an unfillable exit
keeps the scenario position open for the rest of the day instead of allowing
new entries. No signal, threshold, fee, latency, haircut, size, horizon, gate,
or Q2/Validation/Final rule is changed.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE / "sc001_e002_okx_q1_taker_economics.py"
MODULE_NAME = "sc001_e002_okx_q1_taker_economics_parent_v01"

spec = importlib.util.spec_from_file_location(MODULE_NAME, PARENT)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load parent taker-economics engine")
m = importlib.util.module_from_spec(spec)
sys.modules[MODULE_NAME] = m
spec.loader.exec_module(m)

# Parser/preflight v0.3 is the authoritative successful metadata/funding input.
m.VERSION = "0.2"
m.META_REPORT = (
    m.DATA_ROOT / "SC001_E002_OKX_Q1_EXECUTION_METADATA" /
    "sc001_e002_okx_q1_execution_metadata_preflight_v0_3.json"
)
m.FUNDING_FILE = (
    m.DATA_ROOT / "SC001_E002_OKX_Q1_EXECUTION_METADATA" /
    "sc001_e002_okx_q1_funding_rates_v0_3.json"
)

_parent_parent_state = m.parent_state


def parent_state_v02():
    q6, q9a, q9b, meta, funding = _parent_parent_state()
    if str(meta.get("version")) != "0.3":
        m.fail(f"expected successful metadata preflight version 0.3, got {meta.get('version')!r}")
    if str(funding.get("version")) != "0.3":
        m.fail(f"expected funding artifact version 0.3, got {funding.get('version')!r}")
    src = str(funding.get("source", ""))
    if "market-data-history" not in src or "module=3" not in src:
        m.fail(f"unexpected funding source identity: {src!r}")
    return q6, q9a, q9b, meta, funding


m.parent_state = parent_state_v02


def combined_script_sha() -> str:
    h = hashlib.sha256()
    h.update(PARENT.read_bytes())
    h.update(Path(__file__).resolve().read_bytes())
    return h.hexdigest()


m.script_sha = combined_script_sha


def simulate_day_v02(day: dict, candidates: dict[str, list[dict]], execs: dict,
                     funding: dict, day_dir: Path, impl_sha: str,
                     replay_stats: dict) -> dict:
    funding_events = m.funding_rows(funding, day["date"])
    csv_path = day_dir / "completed_trades.csv"
    rows_out = []
    summaries = []
    BLOCK_FOREVER = 10**30

    for qname, _ in m.THRESHOLDS:
        cands = candidates[qname]
        for lat in m.LATENCIES_MS:
            for haircut in m.HAIRCUTS:
                for target in m.TARGET_NOTIONALS:
                    open_until = -1
                    skipped = 0
                    unfilled = 0
                    completed_rows = []
                    for c in cands:
                        if int(c["decision_ts"]) < open_until:
                            skipped += 1
                            continue

                        ex = execs.get((qname, c["id"], lat), {})
                        en = ex.get("entry")
                        out = ex.get("exit")
                        if en is None:
                            unfilled += 1
                            continue

                        ef = en["sizes"][str(target)]["haircuts"][str(haircut)]
                        if not ef["filled"]:
                            # No entry fill means no position was opened.
                            unfilled += 1
                            continue

                        if out is None:
                            # Entry exists but no executable exit state: position remains open.
                            unfilled += 1
                            open_until = BLOCK_FOREVER
                            continue

                        xf = out["sizes"][str(target)]["haircuts"][str(haircut)]
                        if not xf["filled"]:
                            # Entry filled but the frozen exit cannot fully fill visible depth.
                            # The position is therefore not closed; block all later candidates.
                            unfilled += 1
                            open_until = BLOCK_FOREVER
                            continue

                        tr = m.trade_row(day, c, qname, lat, haircut, target, ex, funding_events)
                        if tr is None:
                            m.fail("completed trade unexpectedly missing")
                        completed_rows.append(tr)
                        rows_out.append(tr)
                        open_until = int(out["book_ts"])

                    sm = m.summarize_rows(completed_rows, len(cands), skipped, unfilled)
                    sm.update({
                        "date": day["date"],
                        "sample_type": day["sample_type"],
                        "event_class": day["event_class"],
                        "threshold_scenario": qname,
                        "latency_ms": lat,
                        "haircut": haircut,
                        "target_notional": target,
                    })
                    summaries.append(sm)

    if rows_out:
        header = list(rows_out[0].keys())
        tmp = csv_path.with_suffix(".csv.tmp")
        with tmp.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=header)
            w.writeheader()
            w.writerows(rows_out)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, csv_path)
    else:
        m.atomic_text(csv_path, "")

    report = {
        "stage": m.STAGE,
        "version": m.VERSION,
        "status": "PASS",
        "implementation_sha256": impl_sha,
        "date": day["date"],
        "sample_type": day["sample_type"],
        "event_class": day["event_class"],
        "replay_stats": replay_stats,
        "scenario_summaries": summaries,
        "completed_trades_csv": str(csv_path),
        "do_not_interpret_before_all_four_days_complete": True,
        "adapter_v0_2_exit_unfilled_blocks_future_entries": True,
    }
    m.atomic_json(day_dir / "day_report.json", report)
    return report


m.simulate_day = simulate_day_v02


if __name__ == "__main__":
    print("SC001 taker-economics implementation adapter v0.2")
    print("parent engine =", PARENT.name)
    print("metadata preflight =", m.META_REPORT.name)
    print("funding artifact =", m.FUNDING_FILE.name)
    print("exit-unfilled state rule = BLOCK FUTURE ENTRIES FOR DAY")
    m.main()
