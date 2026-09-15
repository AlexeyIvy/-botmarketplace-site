"""Read-only SC001-E002 postmortem diagnostics.

Reads only the terminal taker-economics report and its already-written completed
trade CSVs. Does not rerun market data, does not alter verdicts, and does not
access Q2 / Validation / Final.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

DATA_ROOT = Path.home() / "sc001_data"
WORKSPACE = DATA_ROOT / "SC001_E002_OKX_Q1_TAKER_ECONOMICS"
REPORT = WORKSPACE / "sc001_e002_okx_q1_taker_economics_report.json"
DAY_ROOT = WORKSPACE / "days"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sid(q, lat, haircut, size):
    return f"{q}|{lat}|{haircut}|{size}"


def index_pooled(report):
    out = {}
    for x in report.get("pooled_scenarios", []):
        out[sid(x["threshold_scenario"], x["latency_ms"], x["haircut"], x["target_notional"])] = x
    return out


def show(label, row):
    keys = [
        "completed_trade_count", "completion_rate", "long_count", "short_count",
        "mean_gross_midquote_edge_bps", "mean_pre_fee_executable_edge_bps",
        "mean_spread_depth_cost_bps", "mean_fee_cost_bps", "mean_funding_cost_bps",
        "mean_net_edge_bps", "median_net_edge_bps", "positive_daily_mean_net_days",
        "median_daily_mean_net_edge_bps", "mean_break_even_round_trip_fee_bps",
        "entry_wait_p50_ms", "entry_wait_p95_ms", "entry_wait_p99_ms",
        "exit_wait_p50_ms", "exit_wait_p95_ms", "exit_wait_p99_ms",
    ]
    print(f"\n=== {label} ===")
    for k in keys:
        print(f"{k} = {row.get(k)}")


def tie_diagnostic():
    seen = {}
    for day_dir in sorted(DAY_ROOT.iterdir() if DAY_ROOT.exists() else []):
        csv_path = day_dir / "completed_trades.csv"
        if not csv_path.exists() or csv_path.stat().st_size == 0:
            continue
        with csv_path.open("r", encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                key = (r["date"], r["threshold_scenario"], r["decision_ts"])
                if key in seen:
                    continue
                try:
                    tfi = abs(float(r["tfi"]))
                    thr = float(r["causal_threshold"])
                except Exception:
                    continue
                seen[key] = (tfi, thr)
    by_q = defaultdict(lambda: [0, 0])
    for (_, q, _), (tfi, thr) in seen.items():
        by_q[q][1] += 1
        if abs(tfi - thr) <= 1e-12:
            by_q[q][0] += 1
    print("\n=== COMPLETED-TRADE THRESHOLD-TIE DIAGNOSTIC ===")
    print("NOTE: deduplicated completed trades only; not all raw candidates.")
    for q in ("q90", "q95", "q97.5"):
        ties, total = by_q[q]
        frac = ties / total if total else None
        print(f"{q}: ties={ties} total={total} fraction={frac}")


def main():
    if not REPORT.exists():
        raise SystemExit(f"missing terminal report: {REPORT}")
    report = load_json(REPORT)
    print("E002_POSTMORTEM_READ_ONLY")
    print("terminal_verdict =", report.get("verdict"))
    print("Q2/Validation/Final = CLOSED")

    p = index_pooled(report)

    print("\n##### THRESHOLD COMPARISON: 10k / 100ms / 0% #####")
    for q in ("q90", "q95", "q97.5"):
        show(q, p[sid(q, 100, 0.0, 10000)])

    print("\n##### SIZE COMPARISON: q95 / 100ms / 0% #####")
    for size in (1000, 10000, 50000):
        show(f"SIZE_{size}", p[sid("q95", 100, 0.0, size)])

    print("\n##### LATENCY COMPARISON: q95 / 10k / 0% #####")
    for lat in (100, 250, 500):
        show(f"LAT_{lat}", p[sid("q95", lat, 0.0, 10000)])

    print("\n##### DEPTH HAIRCUT COMPARISON: q95 / 10k / 100ms #####")
    for h in (0.0, 0.25, 0.5):
        show(f"HAIRCUT_{h}", p[sid("q95", 100, h, 10000)])

    tie_diagnostic()
    print("\nPOSTMORTEM_COMPLETE_NO_VERDICT_CHANGE")


if __name__ == "__main__":
    main()
