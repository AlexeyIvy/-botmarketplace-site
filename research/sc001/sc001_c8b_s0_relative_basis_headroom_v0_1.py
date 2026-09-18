from __future__ import annotations

import bisect
import csv
import hashlib
import json
import math
import os
import statistics
import subprocess
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

STAGE = "SC001-C8B-S0-CROSS-VENUE-RELATIVE-BASIS-HEADROOM-V0.1"
SURVIVE = "C8B_S0_HEADROOM_SURVIVE"
REJECT = "C8B_S0_REJECT_HEADROOM"
DEFER = "C8B_S0_DEFER_SAMPLE"

FIXED_DATE = "2025-01-20"
DAY_START_SEC = 1737331200
DAY_END_SEC = 1737417600

LOOKBACK_SECONDS = 300
MIN_BASELINE_OBS = 120
HEADROOM_BPS = 30.0
MAX_GATE_BPS = 40.0

COACTIVE_MIN = 50_000
ELIGIBLE_MIN = 40_000
ELIGIBLE_HOURS_MIN = 24
EPISODE_MIN = 10
EPISODE_HOURS_MIN = 6

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/sc001-c8b-s0-cross-venue-relative-basis-headroom-sentinel-v0.1.md"
REGISTRY = ROOT / "docs/research/sc001-contamination-registry-v0.12.json"
FREEZE = ROOT / "docs/research/sc001-c8b-s0-implementation-freeze-v0.1.json"

DATA_ROOT = Path(
    os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))
).expanduser().resolve()

D3_REPORT = (
    DATA_ROOT / "SC001_C8_D3_PRICE_CALIBRATION"
    / "sc001_c8_d3_price_body_integrity_report_v0_1.json"
)

STRATEGY_OUT_DIR = DATA_ROOT / "SC001_C8B_S0_HEADROOM"
STRATEGY_OUT = STRATEGY_OUT_DIR / "c8b_s0_strategy_evidence_v0_1.json"
FEATURE_OUT = STRATEGY_OUT_DIR / "c8b_s0_feature_block_evidence_v0_1.json"


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing JSON: {path}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        fail(f"JSON object expected: {path}")
    return obj


def atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def git_blob(path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(ROOT), "hash-object", str(path.relative_to(ROOT))],
        text=True,
    ).strip()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require_freeze() -> dict:
    fr = load_json(FREEZE)
    if fr.get("status") != "FROZEN_BEFORE_FIRST_C8B_S0_PRICE_OUTCOME":
        fail("C8B-S0 freeze status mismatch")
    if fr.get("runner_git_blob_sha") != git_blob(Path(__file__).resolve()):
        fail("C8B-S0 runner identity mismatch")
    if fr.get("protocol_git_blob_sha") != git_blob(PROTOCOL):
        fail("C8B-S0 protocol identity mismatch")
    if fr.get("contamination_registry_git_blob_sha") != git_blob(REGISTRY):
        fail("C8B-S0 registry identity mismatch")
    if fr.get("fixed_date") != FIXED_DATE:
        fail("C8B-S0 fixed date mismatch")
    if fr.get("representation") != "STRICT_COACTIVE_1S_NO_CARRY_FORWARD":
        fail("C8B-S0 representation mismatch")
    if int(fr.get("lookback_seconds", 0)) != LOOKBACK_SECONDS:
        fail("C8B-S0 lookback mismatch")
    if int(fr.get("minimum_prior_coactive_observations", 0)) != MIN_BASELINE_OBS:
        fail("C8B-S0 baseline sample mismatch")
    if float(fr.get("headroom_hurdle_bps", -1)) != HEADROOM_BPS:
        fail("C8B-S0 headroom hurdle mismatch")
    if int(fr.get("persistence_seconds", 0)) != 2:
        fail("C8B-S0 persistence mismatch")
    if fr.get("cross_venue_price_comparison_authorized") is not True:
        fail("C8B-S0 price comparison not authorized")
    for k in (
        "convergence_outcome_authorized",
        "cross_venue_return_authorized",
        "lag_authorized",
        "leader_selection_authorized",
        "strategy_pnl_authorized",
        "promotional_alpha_authorized",
    ):
        if fr.get(k) is not False:
            fail(f"C8B-S0 firewall mismatch: {k}")
    return fr


def require_registry() -> dict:
    reg = load_json(REGISTRY)
    if str(reg.get("version")) != "0.12":
        fail("contamination registry version mismatch")
    row = reg.get("c8_price_selection_calibration") or {}
    if row.get("classification") != "NONPROMOTIONAL_SELECTION_CALIBRATION":
        fail("C8B-S0 calibration role mismatch")
    if row.get("candidate") != "C8B":
        fail("C8B-S0 candidate registry mismatch")
    if row.get("target_utc_date") != FIXED_DATE:
        fail("C8B-S0 registry date mismatch")
    if row.get("qualified_temporal_representation") != "STRICT_COACTIVE_1S_NO_CARRY_FORWARD":
        fail("C8B-S0 registry representation mismatch")
    return reg


def require_d3() -> tuple[dict, Path, Path]:
    rep = load_json(D3_REPORT)
    if rep.get("status") != "C8_D3_PRICE_BODY_INTEGRITY_PASS":
        fail("C8-D3 parent not exact PASS")
    if rep.get("fixed_date") != FIXED_DATE:
        fail("C8-D3 parent date mismatch")
    if rep.get("failed_gates") != []:
        fail("C8-D3 parent failed_gates not empty")
    for k in (
        "cross_venue_price_compared",
        "cross_venue_return_calculated",
        "rolling_cross_venue_baseline_calculated",
        "raw_spread_calculated",
        "dislocation_calculated",
        "convergence_outcome_calculated",
        "strategy_signal_calculated",
        "pnl_calculated",
        "promotional_alpha_accessed",
    ):
        if rep.get(k) is not False:
            fail(f"C8-D3 parent firewall mismatch: {k}")

    okx_meta = ((rep.get("okx") or {}).get("normalized_file") or {})
    bybit_meta = ((rep.get("bybit") or {}).get("normalized_file") or {})

    okx_path = Path(str(okx_meta.get("path", "")))
    bybit_path = Path(str(bybit_meta.get("path", "")))

    for label, meta, path in (
        ("OKX", okx_meta, okx_path),
        ("Bybit", bybit_meta, bybit_path),
    ):
        if not path.exists():
            fail(f"{label} normalized file missing: {path}")
        if path.stat().st_size != int(meta.get("bytes", -1)):
            fail(f"{label} normalized byte mismatch")
        if sha256_file(path) != meta.get("sha256"):
            fail(f"{label} normalized SHA mismatch")

    return rep, okx_path, bybit_path


def load_norm(path: Path) -> dict[int, float]:
    out: dict[int, float] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        expected = ["second_id", "last_trade_ts_us", "last_trade_price"]
        if list(r.fieldnames or []) != expected:
            fail(f"normalized header mismatch: {path.name}")

        prev_sec = None
        for row in r:
            sec = int(row["second_id"])
            ts_us = int(row["last_trade_ts_us"])
            price = float(row["last_trade_price"])

            if not (DAY_START_SEC <= sec < DAY_END_SEC):
                fail(f"normalized second outside fixed day: {path.name} {sec}")
            if ts_us // 1_000_000 != sec:
                fail(f"normalized timestamp/second mismatch: {path.name} {sec}")
            if not (math.isfinite(price) and price > 0):
                fail(f"normalized price invalid: {path.name} {sec}")
            if prev_sec is not None and sec <= prev_sec:
                fail(f"normalized seconds not strictly increasing: {path.name}")
            prev_sec = sec
            out[sec] = price

    return out


def median_sorted(vals: list[float]) -> float:
    n = len(vals)
    if n == 0:
        raise ValueError("empty median")
    m = n // 2
    if n % 2:
        return vals[m]
    return 0.5 * (vals[m - 1] + vals[m])


def nearest_rank_percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    vals = sorted(values)
    idx = max(0, min(len(vals) - 1, math.ceil(q * len(vals)) - 1))
    return vals[idx]


def build_dislocations(
    okx: dict[int, float],
    bybit: dict[int, float],
) -> tuple[dict[int, float], dict[int, float], int]:
    coactive_secs = sorted(set(okx) & set(bybit))

    raw: dict[int, float] = {}
    for sec in coactive_secs:
        raw[sec] = 10_000.0 * math.log(okx[sec] / bybit[sec])

    eligible: dict[int, float] = {}
    baselines: dict[int, float] = {}

    window = deque()  # (sec, raw_spread)
    sorted_vals: list[float] = []

    for sec in coactive_secs:
        cutoff = sec - LOOKBACK_SECONDS

        while window and window[0][0] < cutoff:
            old_sec, old_val = window.popleft()
            pos = bisect.bisect_left(sorted_vals, old_val)
            if pos >= len(sorted_vals) or sorted_vals[pos] != old_val:
                fail(f"rolling median removal mismatch at {old_sec}")
            sorted_vals.pop(pos)

        if len(sorted_vals) >= MIN_BASELINE_OBS:
            baseline = median_sorted(sorted_vals)
            baselines[sec] = baseline
            eligible[sec] = raw[sec] - baseline

        val = raw[sec]
        bisect.insort(sorted_vals, val)
        window.append((sec, val))

    return eligible, baselines, len(coactive_secs)


def count_episodes(disloc: dict[int, float]) -> tuple[int, list[int]]:
    secs = sorted(disloc)
    armed = True
    episodes = 0
    episode_secs: list[int] = []

    for sec in secs:
        v = disloc[sec]
        av = abs(v)

        if av < HEADROOM_BPS:
            armed = True
            continue

        if not armed:
            continue

        nxt = sec + 1
        nv = disloc.get(nxt)
        if nv is None:
            continue
        if abs(nv) < HEADROOM_BPS:
            continue

        same_sign = (v > 0 and nv > 0) or (v < 0 and nv < 0)
        if not same_sign:
            continue

        episodes += 1
        episode_secs.append(sec)
        armed = False

    return episodes, episode_secs


def main() -> int:
    try:
        require_freeze()
        require_registry()
        _d3, okx_path, bybit_path = require_d3()

        if STRATEGY_OUT.exists():
            old = load_json(STRATEGY_OUT)
            if old.get("status") in {SURVIVE, REJECT, DEFER}:
                fail(f"one-shot guard: terminal C8B-S0 report already exists: {old.get('status')}")

        print("C8B-S0 load OKX normalized 1s prices", flush=True)
        okx = load_norm(okx_path)
        print("C8B-S0 load Bybit normalized 1s prices", flush=True)
        bybit = load_norm(bybit_path)

        print("C8B-S0 calculate strict-coactive raw spread and causal baseline", flush=True)
        disloc, baselines, coactive_count = build_dislocations(okx, bybit)

        abs_vals = [abs(v) for v in disloc.values()]
        p99_abs = nearest_rank_percentile(abs_vals, 0.99)
        max_abs = max(abs_vals) if abs_vals else None

        eligible_hours = {
            datetime.fromtimestamp(sec, tz=timezone.utc).hour
            for sec in disloc
        }

        episodes, episode_secs = count_episodes(disloc)
        episode_hours = {
            datetime.fromtimestamp(sec, tz=timezone.utc).hour
            for sec in episode_secs
        }

        sample_gates = {
            "strict_coactive_seconds_gte50000": coactive_count >= COACTIVE_MIN,
            "baseline_eligible_seconds_gte40000": len(disloc) >= ELIGIBLE_MIN,
            "baseline_eligible_utc_hours_eq24": len(eligible_hours) == ELIGIBLE_HOURS_MIN,
        }

        headroom_gates = {
            "persistent_episodes_gte10": episodes >= EPISODE_MIN,
            "episode_hours_gte6": len(episode_hours) >= EPISODE_HOURS_MIN,
            "p99_abs_dislocation_gte30bps": p99_abs is not None and p99_abs >= HEADROOM_BPS,
            "max_abs_dislocation_gte40bps": max_abs is not None and max_abs >= MAX_GATE_BPS,
        }

        if not all(sample_gates.values()):
            status = DEFER
        elif all(headroom_gates.values()):
            status = SURVIVE
        else:
            status = REJECT

        strategy_report = {
            "stage": STAGE,
            "version": "0.1",
            "status": status,
            "selection_calibration_only": True,
            "candidate": "C8B",
            "mechanism": "paired cross-venue transient relative-basis convergence",
            "fixed_date": FIXED_DATE,
            "representation": "STRICT_COACTIVE_1S_NO_CARRY_FORWARD",
            "within_second_statistic": "chronologically_last_trade_inside_active_second",
            "raw_spread_formula": "10000*ln(OKX_last_price/BYBIT_last_price)",
            "baseline": {
                "wall_clock_lookback_seconds": LOOKBACK_SECONDS,
                "minimum_prior_coactive_observations": MIN_BASELINE_OBS,
                "statistic": "median",
                "current_second_excluded": True,
            },
            "structural_architecture": {
                "execution_family": "T3_paired",
                "structural_fill_count": 4,
                "fee_reference_bps_per_fill": 5.0,
                "four_fill_fee_reference_floor_bps": 20.0,
                "gross_headroom_hurdle_bps": HEADROOM_BPS,
            },
            "strict_coactive_seconds": coactive_count,
            "baseline_eligible_seconds": len(disloc),
            "baseline_eligible_utc_hours": len(eligible_hours),
            "persistent_episode_count": episodes,
            "persistent_episode_utc_hours": len(episode_hours),
            "p99_abs_dislocation_bps": p99_abs,
            "max_abs_dislocation_bps": max_abs,
            "sample_gates": sample_gates,
            "headroom_gates": headroom_gates,
            "failed_sample_gates": [k for k, v in sample_gates.items() if not v],
            "failed_headroom_gates": [k for k, v in headroom_gates.items() if not v],
            "convergence_outcome_calculated": False,
            "cross_venue_return_calculated": False,
            "lag_calculated": False,
            "leader_selected": False,
            "strategy_pnl_calculated": False,
            "promotional_alpha_accessed": False,
        }

        feature_report = {
            "stage": "SC001-C8B-S0-FEATURE-BLOCK-EVIDENCE-V0.1",
            "version": "0.1",
            "evidence_maturity": "SELECTION_CALIBRATION_ONLY",
            "strategy_status_reference": status,
            "blocks": {
                "C8B-F1": {
                    "name": "cross-venue raw basis",
                    "roles": ["R6", "R2"],
                    "measurement_validity": True,
                    "formula": "10000*ln(OKX_last_price/BYBIT_last_price)",
                    "strict_coactive_seconds": coactive_count,
                },
                "C8B-F2": {
                    "name": "causal local cross-venue basis median",
                    "roles": ["R6"],
                    "measurement_validity": True,
                    "lookback_seconds": LOOKBACK_SECONDS,
                    "minimum_prior_coactive_observations": MIN_BASELINE_OBS,
                    "baseline_eligible_seconds": len(baselines),
                },
                "C8B-F3": {
                    "name": "transient relative-basis deviation",
                    "roles": ["R1", "R2"],
                    "measurement_validity": True,
                    "p99_abs_dislocation_bps": p99_abs,
                    "max_abs_dislocation_bps": max_abs,
                    "persistent_episode_count": episodes,
                    "persistent_episode_utc_hours": len(episode_hours),
                    "economic_headroom_hurdle_bps": HEADROOM_BPS,
                },
            },
            "works_global_claim_allowed": False,
            "convergence_evidence_present": False,
            "execution_evidence_present": False,
            "promotional_alpha_accessed": False,
        }

        atomic_json(STRATEGY_OUT, strategy_report)
        atomic_json(FEATURE_OUT, feature_report)

        print(status)
        print("strict_coactive_seconds =", coactive_count)
        print("baseline_eligible_seconds =", len(disloc))
        print("baseline_eligible_utc_hours =", len(eligible_hours))
        print("persistent_episode_count =", episodes)
        print("persistent_episode_utc_hours =", len(episode_hours))
        print("p99_abs_dislocation_bps =", p99_abs)
        print("max_abs_dislocation_bps =", max_abs)
        print("failed_sample_gates =", strategy_report["failed_sample_gates"])
        print("failed_headroom_gates =", strategy_report["failed_headroom_gates"])
        print("convergence/return/lag/PnL = False")
        print("promotional alpha accessed = False")
        print("strategy_report =", STRATEGY_OUT)
        print("feature_report =", FEATURE_OUT)
        return 0

    except Exception as exc:
        print("C8B_S0_IMPLEMENTATION_FAIL")
        print("error =", f"{type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
