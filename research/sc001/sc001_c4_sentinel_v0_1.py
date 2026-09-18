from __future__ import annotations

import argparse
import math
import statistics
from pathlib import Path

from sc001_selection_causal_utils_v0_1 import return_bps, robust_zscore
from sc001_selection_sentinel_common_v0_1 import (
    ASSETS, PERF_DAYS, DATA_ROOT, atomic_json, bars_by_close, build_asset_bars,
    date_ms, day_text, one_shot_guard, ordinary_ols_beta,
    require_global_parents, require_sentinel_identity,
)

CANDIDATE = "C4"
PREFLIGHT_PASS = "C4_SENTINEL_PREFLIGHT_PASS"
SURVIVE = "C4_SENTINEL_SURVIVE"
REJECT = "C4_REJECT_SENTINEL"
TARGETS = ("DOGE", "ORDI", "UNI", "XRP", "OP", "BCH")
BAR_MS = 30_000
TARGET_HORIZON_MS = 60_000
Z_THRESHOLD = 3.0
OUT_DIR = DATA_ROOT / "SC001_C1C6_SENTINELS" / CANDIDATE
PREFLIGHT = OUT_DIR / "c4_sentinel_preflight_v0_1.json"
REPORT = OUT_DIR / "c4_sentinel_report_v0_1.json"

VARIANTS = (
    ("C4-BTC-30", "BTC", 30_000),
    ("C4-BTC-60", "BTC", 60_000),
    ("C4-ETH-30", "ETH", 30_000),
    ("C4-ETH-60", "ETH", 60_000),
)


def price_at(maps, asset: str, t: int) -> float | None:
    b = maps[asset].get(t)
    return None if b is None else float(b.close)


def horizon_return(maps, asset: str, t: int, horizon: int) -> float | None:
    p0 = price_at(maps, asset, t - horizon)
    p1 = price_at(maps, asset, t)
    if p0 is None or p1 is None:
        return None
    return return_bps(p0, p1)


def history_returns(maps, asset: str, t: int, horizon: int) -> list[float] | None:
    n = (60 * 60_000) // horizon
    vals: list[float] = []
    end = t - horizon
    for _ in range(n):
        r = horizon_return(maps, asset, end, horizon)
        if r is None:
            return None
        vals.append(r)
        end -= horizon
    vals.reverse()
    return vals


def beta_history(maps, target: str, t: int) -> float | None:
    xs: list[float] = []
    ys: list[float] = []
    end = t - 60_000
    for _ in range(60):
        tr = horizon_return(maps, target, end, 60_000)
        br = horizon_return(maps, "BTC", end, 60_000)
        er = horizon_return(maps, "ETH", end, 60_000)
        if tr is not None and br is not None and er is not None:
            xs.append((br + er) / 2.0)
            ys.append(tr)
        end -= 60_000
    xs.reverse(); ys.reverse()
    return ordinary_ols_beta(xs, ys)


def point_z(maps, leader: str, t: int, impulse_horizon: int) -> tuple[float | None, float | None]:
    cur = horizon_return(maps, leader, t, impulse_horizon)
    hist = history_returns(maps, leader, t, impulse_horizon)
    if cur is None or hist is None:
        return None, None
    try:
        return float(cur), float(robust_zscore(cur, hist))
    except Exception:
        return float(cur), None


def variant_events(maps, leader: str, impulse_horizon: int) -> tuple[list[dict], list[dict]]:
    leader_events: list[dict] = []
    obs: list[dict] = []
    for day in PERF_DAYS:
        start = date_ms(day)
        end = start + 86_400_000
        first = start
        t = first
        # Same-day 60s target outcome only. Previous Z is recomputed causally
        # at t-horizon so day-boundary crossings can use allowed warm-up history
        # without carrying state across the July->September gap.
        while t <= end - TARGET_HORIZON_MS:
            cur, z = point_z(maps, leader, t, impulse_horizon)
            _prev_cur, prev_z = point_z(maps, leader, t - impulse_horizon, impulse_horizon)

            crossed = z is not None and prev_z is not None and abs(prev_z) < Z_THRESHOLD and abs(z) >= Z_THRESHOLD
            if crossed:
                direction = 1 if float(cur) > 0 else -1
                le = {
                    "date": day,
                    "decision_ts": t,
                    "leader": leader,
                    "impulse_horizon_ms": impulse_horizon,
                    "leader_return_bps": float(cur),
                    "leader_z": float(z),
                    "direction": direction,
                }
                leader_events.append(le)

                btc_future = horizon_return(maps, "BTC", t + TARGET_HORIZON_MS, TARGET_HORIZON_MS)
                eth_future = horizon_return(maps, "ETH", t + TARGET_HORIZON_MS, TARGET_HORIZON_MS)
                if btc_future is not None and eth_future is not None:
                    common_future = (btc_future + eth_future) / 2.0
                    for target in TARGETS:
                        tf = horizon_return(maps, target, t + TARGET_HORIZON_MS, TARGET_HORIZON_MS)
                        beta = beta_history(maps, target, t)
                        if tf is None or beta is None:
                            continue
                        raw_signed = direction * tf
                        residual = tf - beta * common_future
                        residual_signed = direction * residual
                        obs.append({
                            **le,
                            "target": target,
                            "target_beta_pre_event": beta,
                            "future_target_return_bps": tf,
                            "future_common_factor_return_bps": common_future,
                            "raw_signed_target_response_bps": raw_signed,
                            "signed_residual_response_bps": residual_signed,
                        })
            t += impulse_horizon

    return leader_events, obs


def variant_metrics(leader_events: list[dict], obs: list[dict]) -> dict:
    by_target = {a: [] for a in TARGETS}
    raw_by_target = {a: [] for a in TARGETS}
    for r in obs:
        by_target[r["target"]].append(float(r["signed_residual_response_bps"]))
        raw_by_target[r["target"]].append(float(r["raw_signed_target_response_bps"]))
    means = {a: (statistics.fmean(v) if v else None) for a, v in by_target.items()}
    raw_means = {a: (statistics.fmean(v) if v else None) for a, v in raw_by_target.items()}
    active = [a for a in TARGETS if by_target[a]]
    vals = [float(means[a]) for a in active]
    raw_vals = [float(raw_means[a]) for a in active]
    eq = statistics.fmean(vals) if vals else None
    med = statistics.median(vals) if vals else None
    raw_eq = statistics.fmean(raw_vals) if raw_vals else None
    pos = sum(1 for v in vals if v > 0)
    event_days = len({e["date"] for e in leader_events})
    gates = {
        "leader_event_days_gte15": event_days >= 15,
        "evaluable_targets_gte5": len(active) >= 5,
        "pooled_event_target_obs_gte100": len(obs) >= 100,
        "equal_weight_target_residual_mean_gte15": eq is not None and eq >= 15.0,
        "median_target_residual_mean_gte15": med is not None and med >= 15.0,
        "positive_target_means_gte4": pos >= 4,
    }
    survives = all(gates.values())
    common_beta_not_lead_lag = (
        not survives and raw_eq is not None and raw_eq > 0
        and (eq is None or eq < 15.0)
    )
    return {
        "leader_event_count": len(leader_events),
        "leader_event_days": event_days,
        "pooled_event_target_observations": len(obs),
        "evaluable_targets": active,
        "target_residual_mean_bps": means,
        "target_raw_mean_bps": raw_means,
        "equal_weight_target_residual_mean_bps": eq,
        "median_target_residual_mean_bps": med,
        "equal_weight_target_raw_mean_bps": raw_eq,
        "positive_target_count": pos,
        "gates": gates,
        "survives": survives,
        "common_beta_not_lead_lag": common_beta_not_lead_lag,
    }


def preflight() -> int:
    require_global_parents()
    require_sentinel_identity(CANDIDATE, Path(__file__))
    atomic_json(PREFLIGHT, {
        "stage": "SC001-C4-SENTINEL-PREFLIGHT-V0.1",
        "status": PREFLIGHT_PASS,
        "variant_count": 4,
        "variants": [{"id": v, "leader": l, "impulse_horizon_ms": h} for v,l,h in VARIANTS],
        "leader_history_minutes": 60,
        "leader_z_threshold": Z_THRESHOLD,
        "target_horizon_ms": TARGET_HORIZON_MS,
        "common_factor": "equal_weight_BTC_ETH_60s_return",
        "beta_estimation": "ordinary_OLS_prior_60_nonoverlapping_60s_returns",
        "sentinel_outcome_calculated": False,
        "protected_data_accessed": False,
        "promotional_alpha_accessed": False,
    })
    print(PREFLIGHT_PASS)
    print("variant_count = 4")
    return 0


def run() -> int:
    preflight()
    one_shot_guard(REPORT, {SURVIVE, REJECT})
    print("C4 loading 30s bars for 8 assets", flush=True)
    maps = {a: bars_by_close(build_asset_bars(a, BAR_MS, market="swap")) for a in ASSETS}

    variants = {}
    for vid, leader, horizon in VARIANTS:
        print(f"C4 {vid}", flush=True)
        les, obs = variant_events(maps, leader, horizon)
        variants[vid] = {
            "metrics": variant_metrics(les, obs),
            "leader_events": les,
            "observations": obs,
        }

    survivors = [v for v,_,_ in VARIANTS if variants[v]["metrics"]["survives"]]
    common_beta = [v for v,_,_ in VARIANTS if variants[v]["metrics"]["common_beta_not_lead_lag"]]
    status = SURVIVE if survivors else REJECT
    rep = {
        "stage": "SC001-C4-SENTINEL-V0.1",
        "status": status,
        "variants": variants,
        "surviving_variants": survivors,
        "common_beta_not_lead_lag_variants": common_beta,
        "selection_calibration_only": True,
        "sentinel_variant_budget_total": 11,
        "candidate_variant_count": 4,
        "protected_data_accessed": False,
        "promotional_alpha_accessed": False,
        "pnl_calculated": False,
    }
    atomic_json(REPORT, rep)
    print(status)
    for vid,_,_ in VARIANTS:
        m = variants[vid]["metrics"]
        print(vid, "events =", m["leader_event_count"], "obs =", m["pooled_event_target_observations"], "resid_eq =", m["equal_weight_target_residual_mean_bps"], "survives =", m["survives"])
    print("report =", REPORT)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["preflight", "run"])
    args = ap.parse_args()
    return preflight() if args.mode == "preflight" else run()


if __name__ == "__main__":
    raise SystemExit(main())
