from __future__ import annotations

import argparse
import math
import statistics
from pathlib import Path

from sc001_selection_causal_utils_v0_1 import return_bps, robust_zscore
from sc001_selection_sentinel_common_v0_1 import (
    ASSETS, PERF_BY_WINDOW, WARMUP_BY_WINDOW, DATA_ROOT,
    atomic_json, build_asset_bars, date_ms, day_text,
    one_shot_guard, require_global_parents, require_sentinel_identity,
)

CANDIDATE = "C5"
PREFLIGHT_PASS = "C5_SENTINEL_PREFLIGHT_PASS"
SURVIVE = "C5_SENTINEL_SURVIVE"
DEFER = "C5_DEFER_SAMPLE_INSUFFICIENT"
REJECT = "C5_REJECT_SENTINEL"
WIDTH_MS = 30_000
HORIZON_MS = 5 * 60_000
Z_THRESHOLD = 3.0
MIN_MOVE_BPS = 10.0
HISTORY_BARS = 120
OUT_DIR = DATA_ROOT / "SC001_C1C6_SENTINELS" / CANDIDATE
PREFLIGHT = OUT_DIR / "c5_sentinel_preflight_v0_1.json"
REPORT = OUT_DIR / "c5_sentinel_report_v0_1.json"


def run_asset(asset: str) -> list[dict]:
    all_bars = build_asset_bars(asset, WIDTH_MS, market="swap")
    events: list[dict] = []

    for window in ("JULY", "SEPTEMBER"):
        warm = WARMUP_BY_WINDOW[window]
        perf = PERF_BY_WINDOW[window]
        lo = date_ms(warm)
        hi = date_ms(perf[-1]) + 86_400_000
        bars = [b for b in all_bars if lo < b.close_ms <= hi]
        by_close = {b.close_ms: b for b in bars}
        prev_z: float | None = None
        next_allowed = -1

        for i, b in enumerate(bars):
            t = b.close_ms
            d = day_text(t - 1)
            if i < HISTORY_BARS:
                continue
            hist = bars[i-HISTORY_BARS:i]
            if [x.close_ms for x in hist] != [t - k*WIDTH_MS for k in range(HISTORY_BARS, 0, -1)]:
                prev_z = None
                continue
            vals = [float(x.signed_aggressive_notional) for x in hist]
            try:
                z = robust_zscore(float(b.signed_aggressive_notional), vals)
            except Exception:
                prev_z = None
                continue

            if d not in perf:
                prev_z = z
                continue
            if t > date_ms(d) + 86_400_000 - HORIZON_MS:
                prev_z = z
                continue
            if t < next_allowed:
                prev_z = z
                continue

            move = return_bps(float(b.open), float(b.close))
            flow_sign = 1 if b.signed_aggressive_notional > 0 else (-1 if b.signed_aggressive_notional < 0 else 0)
            move_sign = 1 if move > 0 else (-1 if move < 0 else 0)
            crossed = prev_z is not None and abs(prev_z) < Z_THRESHOLD and abs(z) >= Z_THRESHOLD

            if crossed and flow_sign != 0 and flow_sign == move_sign and abs(move) >= MIN_MOVE_BPS:
                future = by_close.get(t + HORIZON_MS)
                if future is not None:
                    reversal_direction = -flow_sign
                    response = reversal_direction * return_bps(float(b.close), float(future.close))
                    events.append({
                        "asset": asset,
                        "date": d,
                        "decision_ts": t,
                        "flow_z": z,
                        "signed_aggressive_notional": float(b.signed_aggressive_notional),
                        "concurrent_return_bps": move,
                        "event_direction": flow_sign,
                        "future_close": float(future.close),
                        "signed_reversal_bps": response,
                    })
                    next_allowed = t + HORIZON_MS

            prev_z = z

    return events


def metrics(events: list[dict]) -> dict:
    by_asset = {a: [] for a in ASSETS}
    for e in events:
        by_asset[e["asset"]].append(float(e["signed_reversal_bps"]))
    means = {a: (statistics.fmean(v) if v else None) for a, v in by_asset.items()}
    active = [a for a in ASSETS if by_asset[a]]
    active5 = [a for a in ASSETS if len(by_asset[a]) >= 5]
    vals = [float(means[a]) for a in active]
    eq = statistics.fmean(vals) if vals else None
    med = statistics.median(vals) if vals else None
    pos = sum(1 for v in vals if v > 0)
    days = len({e["date"] for e in events})
    positive_rule = pos >= 5 if len(active) == 8 else (len(active) > 0 and pos / len(active) >= 0.70)
    gates = {
        "pooled_nonoverlap_events_gte50": len(events) >= 50,
        "assets_with_gte5_events_gte5": len(active5) >= 5,
        "equal_weight_asset_mean_gte15": eq is not None and eq >= 15.0,
        "median_active_asset_mean_gte15": med is not None and med >= 15.0,
        "positive_breadth_rule": positive_rule,
        "event_days_gte15": days >= 15,
    }
    return {
        "pooled_events": len(events),
        "per_asset_count": {a: len(by_asset[a]) for a in ASSETS},
        "per_asset_mean_bps": means,
        "active_assets": active,
        "assets_with_gte5_events": active5,
        "equal_weight_asset_mean_bps": eq,
        "median_active_asset_mean_bps": med,
        "positive_active_asset_count": pos,
        "event_days": days,
        "gates": gates,
        "survives": all(gates.values()),
    }


def preflight() -> int:
    require_global_parents()
    require_sentinel_identity(CANDIDATE, Path(__file__))
    atomic_json(PREFLIGHT, {
        "stage": "SC001-C5-SENTINEL-PREFLIGHT-V0.1",
        "status": PREFLIGHT_PASS,
        "variant_count": 1,
        "variant": "30s_flow_z3_price_confirmed_exhaustion_to_5m_reversal",
        "history_bars": HISTORY_BARS,
        "flow_z_threshold": Z_THRESHOLD,
        "minimum_concurrent_move_bps": MIN_MOVE_BPS,
        "outcome_horizon_ms": HORIZON_MS,
        "sentinel_outcome_calculated": False,
        "protected_data_accessed": False,
        "promotional_alpha_accessed": False,
    })
    print(PREFLIGHT_PASS)
    print("variant_count = 1")
    return 0


def run() -> int:
    preflight()
    one_shot_guard(REPORT, {SURVIVE, DEFER, REJECT})
    events: list[dict] = []
    for i, asset in enumerate(ASSETS, 1):
        print(f"C5 [{i}/8] {asset}", flush=True)
        ev = run_asset(asset)
        events.extend(ev)
        print(f"C5 {asset}: events={len(ev)}", flush=True)

    m = metrics(events)
    if m["survives"]:
        status = SURVIVE
    elif 15 <= m["pooled_events"] <= 49 and len(m["active_assets"]) >= 4:
        status = DEFER
    else:
        status = REJECT

    rep = {
        "stage": "SC001-C5-SENTINEL-V0.1",
        "status": status,
        "metrics": m,
        "events": events,
        "selection_calibration_only": True,
        "sentinel_variant_budget_total": 11,
        "candidate_variant_count": 1,
        "l2_accessed": False,
        "protected_data_accessed": False,
        "promotional_alpha_accessed": False,
        "pnl_calculated": False,
    }
    atomic_json(REPORT, rep)
    print(status)
    print("pooled_events =", m["pooled_events"])
    print("equal_weight_asset_mean_bps =", m["equal_weight_asset_mean_bps"])
    print("median_active_asset_mean_bps =", m["median_active_asset_mean_bps"])
    print("event_days =", m["event_days"])
    print("report =", REPORT)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["preflight", "run"])
    args = ap.parse_args()
    return preflight() if args.mode == "preflight" else run()


if __name__ == "__main__":
    raise SystemExit(main())
