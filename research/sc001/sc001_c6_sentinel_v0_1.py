from __future__ import annotations

import argparse
import statistics
from pathlib import Path

from sc001_selection_causal_utils_v0_1 import return_bps
from sc001_selection_sentinel_common_v0_1 import (
    ASSETS, PERF_DAYS, DATA_ROOT, atomic_json, bars_by_close, build_asset_bars,
    date_ms, day_text, one_shot_guard, require_global_parents,
    require_sentinel_identity, trimmed_mean,
)

CANDIDATE = "C6"
PREFLIGHT_PASS = "C6_SENTINEL_PREFLIGHT_PASS"
SURVIVE = "C6_SENTINEL_SURVIVE"
REJECT = "C6_REJECT_SENTINEL"
WIDTH_MS = 5 * 60_000
HOLD_MS = 15 * 60_000
OUT_DIR = DATA_ROOT / "SC001_C1C6_SENTINELS" / CANDIDATE
PREFLIGHT = OUT_DIR / "c6_sentinel_preflight_v0_1.json"
REPORT = OUT_DIR / "c6_sentinel_report_v0_1.json"


def preflight() -> int:
    require_global_parents()
    require_sentinel_identity(CANDIDATE, Path(__file__))
    atomic_json(PREFLIGHT, {
        "stage": "SC001-C6-SENTINEL-PREFLIGHT-V0.1",
        "status": PREFLIGHT_PASS,
        "variant_count": 1,
        "variant": "5m_cross_sectional_equal_weight_residual_top1_bottom1_15m",
        "bar_ms": WIDTH_MS,
        "hold_ms": HOLD_MS,
        "decision_alignment": "UTC 15-minute boundaries",
        "sentinel_outcome_calculated": False,
        "protected_data_accessed": False,
        "promotional_alpha_accessed": False,
    })
    print(PREFLIGHT_PASS)
    print("variant_count = 1")
    return 0


def run() -> int:
    preflight()
    one_shot_guard(REPORT, {SURVIVE, REJECT})

    print("C6 loading 5m bars for 8 assets", flush=True)
    maps = {a: bars_by_close(build_asset_bars(a, WIDTH_MS, market="swap")) for a in ASSETS}
    rows: list[dict] = []

    for day in PERF_DAYS:
        start = date_ms(day)
        # exact non-overlapping 15-minute decision slots
        t = start + HOLD_MS
        while t <= start + 86_400_000 - HOLD_MS:
            if t % HOLD_MS != 0:
                t += HOLD_MS
                continue
            current_returns = {}
            all_ok = True
            for a in ASSETS:
                b0 = maps[a].get(t - WIDTH_MS)
                b1 = maps[a].get(t)
                if b0 is None or b1 is None:
                    all_ok = False
                    break
                current_returns[a] = return_bps(float(b0.close), float(b1.close))
            if not all_ok:
                t += HOLD_MS
                continue

            common = statistics.fmean(current_returns.values())
            residuals = {a: current_returns[a] - common for a in ASSETS}
            long_asset = min(ASSETS, key=lambda a: (residuals[a], a))
            short_asset = max(ASSETS, key=lambda a: (residuals[a], a))
            if long_asset == short_asset:
                t += HOLD_MS
                continue

            lb0 = maps[long_asset].get(t)
            lb1 = maps[long_asset].get(t + HOLD_MS)
            sb0 = maps[short_asset].get(t)
            sb1 = maps[short_asset].get(t + HOLD_MS)
            if None in (lb0, lb1, sb0, sb1):
                t += HOLD_MS
                continue

            long_ret = return_bps(float(lb0.close), float(lb1.close))
            short_ret = return_bps(float(sb0.close), float(sb1.close))
            spread = long_ret - short_ret
            rows.append({
                "date": day,
                "decision_ts": t,
                "common_market_5m_return_bps": common,
                "long_asset": long_asset,
                "short_asset": short_asset,
                "long_residual_bps": residuals[long_asset],
                "short_residual_bps": residuals[short_asset],
                "long_15m_return_bps": long_ret,
                "short_15m_return_bps": short_ret,
                "gross_spread_bps": spread,
            })
            t += HOLD_MS

    vals = [float(r["gross_spread_bps"]) for r in rows]
    med = statistics.median(vals) if vals else None
    trim = trimmed_mean(vals, 0.10)

    byday: dict[str, list[float]] = {}
    for r in rows:
        byday.setdefault(r["date"], []).append(float(r["gross_spread_bps"]))
    daymeans = {d: statistics.fmean(v) for d,v in byday.items()}
    eq_day_mean = statistics.fmean(daymeans.values()) if daymeans else None
    pos_day_share = sum(v > 0 for v in daymeans.values()) / len(daymeans) if daymeans else 0.0

    long_contrib = {a: 0.0 for a in ASSETS}
    short_contrib = {a: 0.0 for a in ASSETS}
    for r in rows:
        long_contrib[r["long_asset"]] += abs(float(r["long_15m_return_bps"]))
        short_contrib[r["short_asset"]] += abs(float(r["short_15m_return_bps"]))
    lden = sum(long_contrib.values())
    sden = sum(short_contrib.values())
    long_shares = {a: (long_contrib[a]/lden if lden > 0 else 0.0) for a in ASSETS}
    short_shares = {a: (short_contrib[a]/sden if sden > 0 else 0.0) for a in ASSETS}
    top_long = max(long_shares.values()) if long_shares else 1.0
    top_short = max(short_shares.values()) if short_shares else 1.0

    gates = {
        "opportunities_gte100": len(rows) >= 100,
        "opportunity_days_gte20": len(byday) >= 20,
        "trimmed_mean_gte30": trim is not None and trim >= 30.0,
        "median_spread_gte20": med is not None and med >= 20.0,
        "equal_weight_calendar_day_mean_gte30": eq_day_mean is not None and eq_day_mean >= 30.0,
        "positive_calendar_day_share_gte060": pos_day_share >= 0.60,
        "top_long_abs_contribution_share_lte035": top_long <= 0.35,
        "top_short_abs_contribution_share_lte035": top_short <= 0.35,
    }
    status = SURVIVE if all(gates.values()) else REJECT

    rep = {
        "stage": "SC001-C6-SENTINEL-V0.1",
        "status": status,
        "opportunity_count": len(rows),
        "opportunity_days": len(byday),
        "trimmed_mean_gross_spread_bps": trim,
        "median_opportunity_spread_bps": med,
        "equal_weight_calendar_day_mean_spread_bps": eq_day_mean,
        "positive_calendar_day_share": pos_day_share,
        "long_abs_contribution_share": long_shares,
        "short_abs_contribution_share": short_shares,
        "top_long_abs_contribution_share": top_long,
        "top_short_abs_contribution_share": top_short,
        "calendar_day_means_bps": daymeans,
        "gates": gates,
        "failed_gates": [k for k,v in gates.items() if not v],
        "opportunities": rows,
        "selection_calibration_only": True,
        "sentinel_variant_budget_total": 11,
        "candidate_variant_count": 1,
        "protected_data_accessed": False,
        "promotional_alpha_accessed": False,
        "pnl_calculated": False,
    }
    atomic_json(REPORT, rep)
    print(status)
    print("opportunities =", len(rows))
    print("opportunity_days =", len(byday))
    print("trimmed_mean_bps =", trim)
    print("median_bps =", med)
    print("equal_weight_day_mean_bps =", eq_day_mean)
    print("positive_day_share =", pos_day_share)
    print("top_long_share =", top_long, "top_short_share =", top_short)
    print("report =", REPORT)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["preflight", "run"])
    args = ap.parse_args()
    return preflight() if args.mode == "preflight" else run()


if __name__ == "__main__":
    raise SystemExit(main())
