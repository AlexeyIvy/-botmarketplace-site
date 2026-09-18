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

CANDIDATE = "C3"
PREFLIGHT_PASS = "C3_SENTINEL_PREFLIGHT_PASS"
SURVIVE = "C3_SENTINEL_SURVIVE"
REJECT = "C3_REJECT_SENTINEL"
OUT_DIR = DATA_ROOT / "SC001_C1C6_SENTINELS" / CANDIDATE
PREFLIGHT = OUT_DIR / "c3_sentinel_preflight_v0_1.json"
REPORT = OUT_DIR / "c3_sentinel_report_v0_1.json"

VARIANTS = {
    "C3-A": {"width_ms": 5 * 60_000, "horizon_ms": 10 * 60_000},
    "C3-B": {"width_ms": 10 * 60_000, "horizon_ms": 20 * 60_000},
}


def true_range(bar, prev_close: float) -> float:
    return max(
        float(bar.high) - float(bar.low),
        abs(float(bar.high) - prev_close),
        abs(float(bar.low) - prev_close),
    )


def run_variant(asset: str, variant: str) -> list[dict]:
    cfg = VARIANTS[variant]
    width = cfg["width_ms"]
    horizon = cfg["horizon_ms"]
    all_bars = build_asset_bars(asset, width, market="swap")
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
            if d not in perf or i < 13:
                continue
            if t > date_ms(d) + 86_400_000 - horizon:
                continue
            if t < next_allowed:
                continue

            needed = bars[i-13:i+1]
            if [x.close_ms for x in needed] != [t - k*width for k in range(13, -1, -1)]:
                continue

            prev6 = bars[i-6:i]
            prior12 = bars[i-12:i]
            prev_close_for_current = float(bars[i-1].close)
            tr_current = true_range(b, prev_close_for_current)

            trs = []
            ok = True
            for j in range(i-12, i):
                if j <= 0:
                    ok = False
                    break
                trs.append(true_range(bars[j], float(bars[j-1].close)))
            if not ok or len(trs) != 12:
                continue

            med_tr = statistics.median(trs)
            if med_tr <= 0 or tr_current < 1.5 * med_tr:
                continue

            up = float(b.close) > max(float(x.high) for x in prev6)
            dn = float(b.close) < min(float(x.low) for x in prev6)
            if up == dn:
                continue
            direction = 1 if up else -1

            future = by_close.get(t + horizon)
            if future is None:
                continue
            response = direction * return_bps(float(b.close), float(future.close))
            events.append({
                "asset": asset,
                "date": d,
                "variant": variant,
                "decision_ts": t,
                "direction": direction,
                "bar_close": float(b.close),
                "true_range": tr_current,
                "prior12_median_true_range": med_tr,
                "expansion_ratio": tr_current / med_tr,
                "future_close": float(future.close),
                "signed_continuation_bps": response,
            })
            next_allowed = t + horizon

    return events


def metrics(events: list[dict]) -> dict:
    by_asset = {a: [] for a in ASSETS}
    for e in events:
        by_asset[e["asset"]].append(float(e["signed_continuation_bps"]))
    means = {a: (statistics.fmean(v) if v else None) for a, v in by_asset.items()}
    active = [a for a in ASSETS if by_asset[a]]
    active_means = [float(means[a]) for a in active]
    eq = statistics.fmean(active_means) if active_means else None
    med = statistics.median(active_means) if active_means else None
    pos = sum(1 for v in active_means if v > 0)
    days = len({e["date"] for e in events})
    gates = {
        "pooled_nonoverlap_events_gte60": len(events) >= 60,
        "active_assets_gte6": len(active) >= 6,
        "equal_weight_asset_mean_gte15": eq is not None and eq >= 15.0,
        "median_asset_mean_gte15": med is not None and med >= 15.0,
        "positive_assets_gte5": pos >= 5,
        "active_calendar_days_gte15": days >= 15,
    }
    return {
        "pooled_events": len(events),
        "per_asset_count": {a: len(by_asset[a]) for a in ASSETS},
        "per_asset_mean_bps": means,
        "active_assets": active,
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
    atomic_json(PREFLIGHT, {
        "stage": "SC001-C3-SENTINEL-PREFLIGHT-V0.1",
        "status": PREFLIGHT_PASS,
        "variants": VARIANTS,
        "variant_count": 2,
        "prior_breakout_bars": 6,
        "prior_tr_median_bars": 12,
        "expansion_ratio_threshold": 1.5,
        "sentinel_outcome_calculated": False,
        "protected_data_accessed": False,
        "promotional_alpha_accessed": False,
    })
    print(PREFLIGHT_PASS)
    print("variant_count = 2")
    return 0


def run() -> int:
    preflight()
    one_shot_guard(REPORT, {SURVIVE, REJECT})
    variants = {}
    for variant in ("C3-A", "C3-B"):
        ev: list[dict] = []
        for i, asset in enumerate(ASSETS, 1):
            print(f"{variant} [{i}/8] {asset}", flush=True)
            ev.extend(run_variant(asset, variant))
        variants[variant] = {"metrics": metrics(ev), "events": ev}

    survivors = [v for v in ("C3-A", "C3-B") if variants[v]["metrics"]["survives"]]
    status = SURVIVE if survivors else REJECT
    rep = {
        "stage": "SC001-C3-SENTINEL-V0.1",
        "status": status,
        "variants": variants,
        "surviving_variants": survivors,
        "selection_calibration_only": True,
        "sentinel_variant_budget_total": 11,
        "candidate_variant_count": 2,
        "protected_data_accessed": False,
        "promotional_alpha_accessed": False,
        "pnl_calculated": False,
    }
    atomic_json(REPORT, rep)
    print(status)
    for v in ("C3-A", "C3-B"):
        m = variants[v]["metrics"]
        print(v, "events =", m["pooled_events"], "eq_mean =", m["equal_weight_asset_mean_bps"], "survives =", m["survives"])
    print("report =", REPORT)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["preflight", "run"])
    args = ap.parse_args()
    return preflight() if args.mode == "preflight" else run()


if __name__ == "__main__":
    raise SystemExit(main())
