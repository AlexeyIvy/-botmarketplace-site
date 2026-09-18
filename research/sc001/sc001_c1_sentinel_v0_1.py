from __future__ import annotations

import argparse
import bisect
import math
import statistics
from collections import deque
from pathlib import Path

from sc001_selection_sentinel_common_v0_1 import (
    ASSETS, PERF_BY_WINDOW, WARMUP_BY_WINDOW, DATA_ROOT, ROOT,
    atomic_json, bars_by_close, build_asset_bars, date_ms, day_text, fail,
    latest_signal_ms_for_horizon, load_json, one_shot_guard,
    require_global_parents, require_sentinel_identity,
)

CANDIDATE = "C1"
PREFLIGHT_PASS = "C1_SENTINEL_PREFLIGHT_PASS"
SURVIVE = "C1_SENTINEL_SURVIVE"
DEFER = "C1_DEFER_SAMPLE_INSUFFICIENT"
REJECT = "C1_REJECT_SENTINEL"

GRID_MS = 10_000
LOOKBACK_POINTS = 2160
MIN_VALID_POINTS = 2052
TRIGGER_BPS = 50.0
EXIT_BPS = 10.0
MAX_HOLD_MS = 30 * 60_000
OUT_DIR = DATA_ROOT / "SC001_C1C6_SENTINELS" / CANDIDATE
PREFLIGHT = OUT_DIR / "c1_sentinel_preflight_v0_1.json"
REPORT = OUT_DIR / "c1_sentinel_report_v0_1.json"


def basis_bps(spot: float, perp: float) -> float:
    return 10_000.0 * (perp / spot - 1.0)


def rolling_state(pair_basis: dict[int, float], start: int, end: int):
    q: deque[float | None] = deque()
    ordered: list[float] = []
    out: dict[int, tuple[float | None, float | None]] = {}
    t = start + GRID_MS
    while t <= end:
        cur = pair_basis.get(t)
        baseline = None
        dis = None
        if len(q) == LOOKBACK_POINTS and len(ordered) >= MIN_VALID_POINTS and cur is not None:
            baseline = statistics.median(ordered)
            dis = cur - baseline
        out[t] = (baseline, dis)
        q.append(cur)
        if cur is not None:
            bisect.insort(ordered, cur)
        if len(q) > LOOKBACK_POINTS:
            old = q.popleft()
            if old is not None:
                i = bisect.bisect_left(ordered, old)
                if i >= len(ordered):
                    fail("rolling median state corruption")
                ordered.pop(i)
        t += GRID_MS
    return out


def run_asset(asset: str) -> list[dict]:
    spot_all = bars_by_close(build_asset_bars(asset, GRID_MS, market="spot"))
    perp_all = bars_by_close(build_asset_bars(asset, GRID_MS, market="swap"))
    events: list[dict] = []

    for window in ("JULY", "SEPTEMBER"):
        warm = WARMUP_BY_WINDOW[window]
        perf = PERF_BY_WINDOW[window]
        start = date_ms(warm)
        end = date_ms(perf[-1]) + 86_400_000
        pair_basis: dict[int, float] = {}
        t = start + GRID_MS
        while t <= end:
            sb = spot_all.get(t)
            pb = perp_all.get(t)
            if sb is not None and pb is not None:
                pair_basis[t] = basis_bps(float(sb.vwap), float(pb.vwap))
            t += GRID_MS

        state = rolling_state(pair_basis, start, end)
        prev_dis = None
        prev_eligible = False
        for t in sorted(state):
            baseline, dis = state[t]
            eligible = baseline is not None and dis is not None
            d = day_text(t)
            if d not in perf:
                prev_dis = dis
                prev_eligible = eligible
                continue
            if t > latest_signal_ms_for_horizon(d, MAX_HOLD_MS):
                prev_dis = dis
                prev_eligible = eligible
                continue

            crossed = (
                prev_eligible and eligible and prev_dis is not None
                and float(prev_dis) < TRIGGER_BPS and float(dis) >= TRIGGER_BPS
            )
            if crossed:
                frozen = float(baseline)
                trig_basis = float(pair_basis[t])
                trig_dis = float(dis)
                exit_t = None
                exit_dis = None
                exit_reason = None
                last_valid = None
                ft = t + GRID_MS
                while ft <= t + MAX_HOLD_MS:
                    b = pair_basis.get(ft)
                    if b is not None:
                        cur_dis = float(b) - frozen
                        last_valid = (ft, cur_dis)
                        if cur_dis <= EXIT_BPS:
                            exit_t, exit_dis, exit_reason = ft, cur_dis, "convergence"
                            break
                    ft += GRID_MS
                if exit_t is None and last_valid is not None:
                    exit_t, exit_dis = last_valid
                    exit_reason = "time"
                if exit_t is not None and exit_dis is not None:
                    events.append({
                        "asset": asset,
                        "date": d,
                        "trigger_ts": t,
                        "trigger_basis_bps": trig_basis,
                        "frozen_baseline_bps": frozen,
                        "trigger_dislocation_bps": trig_dis,
                        "exit_ts": exit_t,
                        "exit_dislocation_bps": exit_dis,
                        "exit_reason": exit_reason,
                        "idealized_contraction_bps": trig_dis - exit_dis,
                    })
            prev_dis = dis
            prev_eligible = eligible

    return events


def preflight() -> int:
    require_global_parents()
    require_sentinel_identity(CANDIDATE, Path(__file__))
    rep = {
        "stage": "SC001-C1-SENTINEL-PREFLIGHT-V0.1",
        "status": PREFLIGHT_PASS,
        "variant_count": 1,
        "variant": "strict_legacy_E006_mechanism_multiasset",
        "grid_ms": GRID_MS,
        "baseline_points": LOOKBACK_POINTS,
        "baseline_min_valid_points": MIN_VALID_POINTS,
        "trigger_bps": TRIGGER_BPS,
        "exit_bps": EXIT_BPS,
        "max_hold_ms": MAX_HOLD_MS,
        "sentinel_outcome_calculated": False,
        "protected_data_accessed": False,
        "promotional_alpha_accessed": False,
    }
    atomic_json(PREFLIGHT, rep)
    print(PREFLIGHT_PASS)
    print("variant_count = 1")
    print("sentinel outcome calculated = False")
    return 0


def run() -> int:
    preflight()
    one_shot_guard(REPORT, {SURVIVE, DEFER, REJECT})
    per_asset: dict[str, list[dict]] = {}
    all_events: list[dict] = []
    for i, asset in enumerate(ASSETS, 1):
        print(f"C1 [{i}/8] {asset}", flush=True)
        ev = run_asset(asset)
        per_asset[asset] = ev
        all_events.extend(ev)
        print(f"C1 {asset}: measured_triggers={len(ev)}", flush=True)

    counts = {a: len(per_asset[a]) for a in ASSETS}
    active = [a for a in ASSETS if counts[a] >= 3]
    means = {
        a: (statistics.fmean([x["idealized_contraction_bps"] for x in per_asset[a]]) if per_asset[a] else None)
        for a in ASSETS
    }
    active_means = [float(means[a]) for a in active if means[a] is not None]
    eq = statistics.fmean(active_means) if active_means else None
    med = statistics.median(active_means) if active_means else None
    pos = sum(1 for v in active_means if v > 0)
    pooled = len(all_events)

    gates = {
        "eligible_pairs_gte4": len(ASSETS) >= 4,
        "pairs_with_gte3_triggers_gte4": len(active) >= 4,
        "pooled_triggers_gte40": pooled >= 40,
        "equal_weight_active_pair_mean_gte30": eq is not None and eq >= 30.0,
        "median_active_pair_mean_gte30": med is not None and med >= 30.0,
        "positive_active_pairs_gte_three_quarters": bool(active) and pos / len(active) >= 0.75,
    }

    if all(gates.values()):
        status = SURVIVE
    elif 10 <= pooled < 40 and len(active) >= 3:
        status = DEFER
    else:
        status = REJECT

    rep = {
        "stage": "SC001-C1-SENTINEL-V0.1",
        "status": status,
        "variant": "strict_legacy_E006_mechanism_multiasset",
        "eligible_pairs": list(ASSETS),
        "per_pair_trigger_count": counts,
        "active_pairs_gte3_triggers": active,
        "per_pair_mean_contraction_bps": means,
        "pooled_measured_triggers": pooled,
        "equal_weight_active_pair_mean_contraction_bps": eq,
        "median_active_pair_mean_contraction_bps": med,
        "positive_active_pair_count": pos,
        "calendar_days_with_trigger": len({e["date"] for e in all_events}),
        "events": all_events,
        "gates": gates,
        "failed_gates": [k for k, v in gates.items() if not v],
        "selection_calibration_only": True,
        "sentinel_variant_budget_total": 11,
        "candidate_variant_count": 1,
        "protected_data_accessed": False,
        "promotional_alpha_accessed": False,
        "pnl_calculated": False,
    }
    atomic_json(REPORT, rep)
    print(status)
    print("pooled_measured_triggers =", pooled)
    print("active_pairs_gte3 =", len(active))
    print("equal_weight_mean_contraction_bps =", eq)
    print("median_active_pair_mean_contraction_bps =", med)
    print("positive_active_pairs =", pos)
    print("report =", REPORT)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["preflight", "run"])
    args = ap.parse_args()
    return preflight() if args.mode == "preflight" else run()


if __name__ == "__main__":
    raise SystemExit(main())
