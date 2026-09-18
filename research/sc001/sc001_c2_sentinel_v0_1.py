from __future__ import annotations

import argparse
import statistics
from pathlib import Path

from sc001_selection_causal_utils_v0_1 import return_bps
from sc001_selection_sentinel_common_v0_1 import (
    ASSETS, PERF_BY_WINDOW, WARMUP_BY_WINDOW, DATA_ROOT,
    atomic_json, build_asset_bars, date_ms, day_text,
    one_shot_guard, require_global_parents, require_sentinel_identity,
)

CANDIDATE = "C2"
PREFLIGHT_PASS = "C2_SENTINEL_PREFLIGHT_PASS"
SURVIVE = "C2_SENTINEL_SURVIVE"
REJECT = "C2_REJECT_SENTINEL"
WIDTH_MS = 60_000
HORIZON_MS = 10 * 60_000
THRESHOLD_BPS = 30.0
OUT_DIR = DATA_ROOT / "SC001_C1C6_SENTINELS" / CANDIDATE
PREFLIGHT = OUT_DIR / "c2_sentinel_preflight_v0_1.json"
REPORT = OUT_DIR / "c2_sentinel_report_v0_1.json"


def reference(last5, variant: str) -> float:
    if variant == "C2-A":
        vol = sum(float(b.volume) for b in last5)
        return sum(float(b.notional) for b in last5) / vol
    if variant == "C2-B":
        return statistics.median(float(b.vwap) for b in last5)
    raise RuntimeError(f"bad variant {variant}")


def run_variant(asset: str, variant: str) -> list[dict]:
    all_bars = build_asset_bars(asset, WIDTH_MS, market="swap")
    events: list[dict] = []

    for window in ("JULY", "SEPTEMBER"):
        warm = WARMUP_BY_WINDOW[window]
        perf = PERF_BY_WINDOW[window]
        lo = date_ms(warm)
        hi = date_ms(perf[-1]) + 86_400_000
        bars = [b for b in all_bars if lo < b.close_ms <= hi]
        by_close = {b.close_ms: b for b in bars}
        next_allowed = -1

        for i, b in enumerate(bars):
            t = b.close_ms
            d = day_text(t - 1)
            if d not in perf or i < 4:
                continue
            if t > date_ms(d) + 86_400_000 - HORIZON_MS:
                continue
            if t < next_allowed:
                continue
            last5 = bars[i-4:i+1]
            # Require an actual contiguous 5-minute reference window.
            if [x.close_ms for x in last5] != [t - 4*WIDTH_MS, t - 3*WIDTH_MS, t - 2*WIDTH_MS, t - WIDTH_MS, t]:
                continue
            ref = reference(last5, variant)
            dev = return_bps(ref, float(b.vwap))
            if abs(dev) < THRESHOLD_BPS:
                continue
            future = by_close.get(t + HORIZON_MS)
            if future is None:
                continue
            direction = -1 if dev > 0 else 1
            response = direction * return_bps(float(b.vwap), float(future.vwap))
            events.append({
                "asset": asset,
                "date": d,
                "decision_ts": t,
                "variant": variant,
                "reference_price": ref,
                "current_vwap": float(b.vwap),
                "deviation_bps": dev,
                "direction": direction,
                "future_vwap": float(future.vwap),
                "signed_reversion_bps": response,
            })
            next_allowed = t + HORIZON_MS

    return events


def variant_metrics(events: list[dict]) -> dict:
    by_asset = {a: [] for a in ASSETS}
    for e in events:
        by_asset[e["asset"]].append(float(e["signed_reversion_bps"]))
    means = {a: (statistics.fmean(v) if v else None) for a, v in by_asset.items()}
    active10 = [a for a in ASSETS if len(by_asset[a]) >= 10]
    active_means = [v for v in means.values() if v is not None]
    eq = statistics.fmean(active_means) if active_means else None
    med = statistics.median(active_means) if active_means else None
    pos = sum(1 for v in active_means if v > 0)
    days = len({e["date"] for e in events})
    gates = {
        "pooled_opportunities_gte100": len(events) >= 100,
        "assets_with_gte10_opportunities_gte6": len(active10) >= 6,
        "equal_weight_asset_mean_gte15": eq is not None and eq >= 15.0,
        "median_asset_mean_gte15": med is not None and med >= 15.0,
        "positive_assets_gte5": pos >= 5,
        "active_calendar_days_gte18": days >= 18,
    }
    return {
        "pooled_opportunities": len(events),
        "per_asset_count": {a: len(by_asset[a]) for a in ASSETS},
        "per_asset_mean_bps": means,
        "assets_with_gte10": active10,
        "equal_weight_asset_mean_bps": eq,
        "median_asset_mean_bps": med,
        "positive_asset_count": pos,
        "active_calendar_days": days,
        "gates": gates,
        "survives": all(gates.values()),
    }


def preflight() -> int:
    require_global_parents()
    require_sentinel_identity(CANDIDATE, Path(__file__))
    rep = {
        "stage": "SC001-C2-SENTINEL-PREFLIGHT-V0.1",
        "status": PREFLIGHT_PASS,
        "variants": ["C2-A", "C2-B"],
        "variant_count": 2,
        "threshold_bps": THRESHOLD_BPS,
        "outcome_horizon_ms": HORIZON_MS,
        "sentinel_outcome_calculated": False,
        "protected_data_accessed": False,
        "promotional_alpha_accessed": False,
    }
    atomic_json(PREFLIGHT, rep)
    print(PREFLIGHT_PASS)
    print("variant_count = 2")
    return 0


def run() -> int:
    preflight()
    one_shot_guard(REPORT, {SURVIVE, REJECT})
    variants = {}
    for variant in ("C2-A", "C2-B"):
        ev: list[dict] = []
        for i, asset in enumerate(ASSETS, 1):
            print(f"{variant} [{i}/8] {asset}", flush=True)
            ev.extend(run_variant(asset, variant))
        variants[variant] = {"metrics": variant_metrics(ev), "events": ev}

    survivors = [v for v in ("C2-A", "C2-B") if variants[v]["metrics"]["survives"]]
    status = SURVIVE if survivors else REJECT
    selected_if_both = "C2-A" if len(survivors) == 2 else (survivors[0] if survivors else None)

    rep = {
        "stage": "SC001-C2-SENTINEL-V0.1",
        "status": status,
        "variants": variants,
        "surviving_variants": survivors,
        "predeclared_simpler_choice_if_both_survive": "C2-A",
        "selection_variant": selected_if_both,
        "selection_calibration_only": True,
        "sentinel_variant_budget_total": 11,
        "candidate_variant_count": 2,
        "protected_data_accessed": False,
        "promotional_alpha_accessed": False,
        "pnl_calculated": False,
    }
    atomic_json(REPORT, rep)
    print(status)
    for v in ("C2-A", "C2-B"):
        m = variants[v]["metrics"]
        print(v, "opportunities =", m["pooled_opportunities"], "eq_mean =", m["equal_weight_asset_mean_bps"], "survives =", m["survives"])
    print("report =", REPORT)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["preflight", "run"])
    args = ap.parse_args()
    return preflight() if args.mode == "preflight" else run()


if __name__ == "__main__":
    raise SystemExit(main())
