from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import statistics
import subprocess
from datetime import datetime, timezone
from pathlib import Path

STAGE = "SC001-C7-S0-MULTI-ASSET-SPREAD-HEADROOM-V0.1"
SURVIVE = "C7_S0_SPREAD_HEADROOM_SURVIVE"
REJECT = "C7_S0_REJECT_SPREAD_HEADROOM"
DEFER = "C7_S0_DEFER_DATA_QUALITY"

FIXED_DATE = "2024-02-12"
DAY_START_SEC = 1707696000
DAY_END_SEC = 1707782400

INSTS = (
    "ETH-USDT-SWAP",
    "DOGE-USDT-SWAP",
    "ORDI-USDT-SWAP",
    "UNI-USDT-SWAP",
    "XRP-USDT-SWAP",
    "OP-USDT-SWAP",
    "BCH-USDT-SWAP",
)

SPREAD_HURDLE_BPS = 10.0
PERSISTENCE_SECONDS = 5

VALID_SECONDS_MIN = 80_000
ACTIVE_HOURS_REQUIRED = 24

P75_GATE_BPS = 10.0
HIGH_SPREAD_SHARE_MIN = 0.20
EPISODE_MIN = 100
EPISODE_HOURS_MIN = 12
UNIVERSE_ELIGIBLE_MIN = 2

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/sc001-c7-s0-multi-asset-spread-headroom-sentinel-v0.1.md"
REGISTRY = ROOT / "docs/research/sc001-contamination-registry-v0.14.json"
FREEZE = ROOT / "docs/research/sc001-c7-s0-implementation-freeze-v0.1.json"

DATA_ROOT = Path(
    os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))
).expanduser().resolve()

D1_REPORT = (
    DATA_ROOT / "SC001_C7_D1_V02_MULTI_ASSET_L2"
    / "sc001_c7_d1_v02_multi_asset_l2_integrity_report_v0_1.json"
)

OUT_DIR = DATA_ROOT / "SC001_C7_S0_SPREAD_HEADROOM"
STRATEGY_OUT = OUT_DIR / "c7_s0_strategy_evidence_v0_1.json"
FEATURE_OUT = OUT_DIR / "c7_s0_feature_block_evidence_v0_1.json"


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
    if fr.get("status") != "FROZEN_BEFORE_FIRST_C7_S0_SPREAD_OUTCOME":
        fail("C7-S0 freeze status mismatch")
    if fr.get("runner_git_blob_sha") != git_blob(Path(__file__).resolve()):
        fail("C7-S0 runner identity mismatch")
    if fr.get("protocol_git_blob_sha") != git_blob(PROTOCOL):
        fail("C7-S0 protocol identity mismatch")
    if fr.get("contamination_registry_git_blob_sha") != git_blob(REGISTRY):
        fail("C7-S0 registry identity mismatch")
    if tuple(fr.get("universe") or ()) != INSTS:
        fail("C7-S0 universe mismatch")
    if fr.get("fixed_date") != FIXED_DATE:
        fail("C7-S0 date mismatch")
    if float(fr.get("spread_hurdle_bps", -1)) != SPREAD_HURDLE_BPS:
        fail("C7-S0 spread hurdle mismatch")
    if int(fr.get("persistence_seconds", 0)) != PERSISTENCE_SECONDS:
        fail("C7-S0 persistence mismatch")
    if float(fr.get("p75_gate_bps", -1)) != P75_GATE_BPS:
        fail("C7-S0 p75 gate mismatch")
    if float(fr.get("high_spread_share_min", -1)) != HIGH_SPREAD_SHARE_MIN:
        fail("C7-S0 share gate mismatch")
    if int(fr.get("persistent_episode_min", 0)) != EPISODE_MIN:
        fail("C7-S0 episode gate mismatch")
    if int(fr.get("persistent_episode_hour_min", 0)) != EPISODE_HOURS_MIN:
        fail("C7-S0 episode-hour gate mismatch")
    if int(fr.get("eligible_asset_min", 0)) != UNIVERSE_ELIGIBLE_MIN:
        fail("C7-S0 universe gate mismatch")

    for k in (
        "maker_order_simulation_authorized",
        "fill_model_authorized",
        "queue_model_authorized",
        "adverse_selection_outcome_authorized",
        "pnl_authorized",
        "promotional_alpha_authorized",
    ):
        if fr.get(k) is not False:
            fail(f"C7-S0 firewall mismatch: {k}")
    return fr


def require_registry() -> dict:
    reg = load_json(REGISTRY)
    if str(reg.get("version")) != "0.14":
        fail("C7-S0 contamination registry version mismatch")
    row = reg.get("c7_spread_selection_calibration") or {}
    if row.get("classification") != "NONPROMOTIONAL_SELECTION_CALIBRATION":
        fail("C7-S0 calibration role mismatch")
    if tuple(row.get("universe") or ()) != INSTS:
        fail("C7-S0 registry universe mismatch")
    if row.get("target_utc_date") != FIXED_DATE:
        fail("C7-S0 registry date mismatch")
    return reg


def require_d1() -> dict:
    rep = load_json(D1_REPORT)
    if rep.get("status") != "C7_D1_V02_MULTI_ASSET_L2_INTEGRITY_PASS":
        fail("C7-D1 v0.2 parent not exact PASS")
    if int(rep.get("assets_passed", 0)) != len(INSTS):
        fail("C7-D1 v0.2 assets_passed mismatch")
    if tuple(rep.get("universe") or ()) != INSTS:
        fail("C7-D1 v0.2 universe mismatch")

    for k in (
        "quoted_spread_calculated",
        "c7_asset_eligibility_calculated",
        "maker_order_simulated",
        "fill_model_calculated",
        "queue_model_calculated",
        "adverse_selection_outcome_calculated",
        "pnl_calculated",
        "promotional_alpha_accessed",
    ):
        if rep.get(k) is not False:
            fail(f"C7-D1 parent firewall mismatch: {k}")
    return rep


def nearest_rank_percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    vals = sorted(values)
    idx = max(0, min(len(vals) - 1, math.ceil(q * len(vals)) - 1))
    return vals[idx]


def load_asset_series(path: Path) -> tuple[list[int], list[float], set[int]]:
    secs: list[int] = []
    spreads: list[float] = []
    hours: set[int] = set()

    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        expected = [
            "second_id",
            "l2_ts_ms",
            "best_bid",
            "best_ask",
            "best_bid_size",
            "best_ask_size",
        ]
        if list(r.fieldnames or []) != expected:
            fail(f"normalized header mismatch: {path.name}")

        prev_sec = None
        for row in r:
            sec = int(row["second_id"])
            if not (DAY_START_SEC <= sec < DAY_END_SEC):
                fail(f"normalized second outside fixed day: {path.name} {sec}")
            if prev_sec is not None and sec <= prev_sec:
                fail(f"normalized seconds not strictly increasing: {path.name}")
            prev_sec = sec

            bid = float(row["best_bid"])
            ask = float(row["best_ask"])
            bid_sz = float(row["best_bid_size"])
            ask_sz = float(row["best_ask_size"])

            if not (
                math.isfinite(bid) and bid > 0
                and math.isfinite(ask) and ask > bid
                and math.isfinite(bid_sz) and bid_sz > 0
                and math.isfinite(ask_sz) and ask_sz > 0
            ):
                fail(f"invalid normalized top-of-book: {path.name} {sec}")

            mid = 0.5 * (bid + ask)
            spread_bps = 10_000.0 * (ask - bid) / mid

            if not (math.isfinite(spread_bps) and spread_bps > 0):
                fail(f"invalid quoted spread: {path.name} {sec}")

            secs.append(sec)
            spreads.append(spread_bps)
            hours.add((sec - DAY_START_SEC) // 3600)

    return secs, spreads, hours


def count_persistent_episodes(
    secs: list[int],
    spreads: list[float],
) -> tuple[int, set[int]]:
    episodes = 0
    episode_hours: set[int] = set()

    armed = True
    high_run = 0
    prev_sec = None

    for sec, spread in zip(secs, spreads):
        consecutive = prev_sec is not None and sec == prev_sec + 1

        if spread < SPREAD_HURDLE_BPS:
            armed = True
            high_run = 0
        else:
            if consecutive:
                high_run += 1
            else:
                high_run = 1

            if armed and high_run == PERSISTENCE_SECONDS:
                start_sec = sec - (PERSISTENCE_SECONDS - 1)
                episodes += 1
                episode_hours.add((start_sec - DAY_START_SEC) // 3600)
                armed = False

        prev_sec = sec

    return episodes, episode_hours


def main() -> int:
    try:
        require_freeze()
        require_registry()
        d1 = require_d1()

        if STRATEGY_OUT.exists():
            old = load_json(STRATEGY_OUT)
            if old.get("status") in {SURVIVE, REJECT, DEFER}:
                fail(f"one-shot guard: terminal C7-S0 report exists: {old.get('status')}")

        assets_parent = d1.get("assets") or {}
        results: dict[str, dict] = {}

        for i, inst in enumerate(INSTS, start=1):
            print(f"C7-S0 [{i}/7] {inst}", flush=True)

            parent = assets_parent.get(inst)
            if not isinstance(parent, dict) or parent.get("integrity_pass") is not True:
                fail(f"C7-D1 parent asset invalid: {inst}")

            norm = (parent.get("normalization") or {}).get("normalized_file") or {}
            path = Path(str(norm.get("path", "")))

            if not path.exists():
                fail(f"normalized file missing: {inst} {path}")
            if path.stat().st_size != int(norm.get("bytes", -1)):
                fail(f"normalized byte mismatch: {inst}")
            if sha256_file(path) != norm.get("sha256"):
                fail(f"normalized SHA mismatch: {inst}")

            secs, spreads, hours = load_asset_series(path)

            p50 = nearest_rank_percentile(spreads, 0.50)
            p75 = nearest_rank_percentile(spreads, 0.75)
            p90 = nearest_rank_percentile(spreads, 0.90)

            high_count = sum(1 for x in spreads if x >= SPREAD_HURDLE_BPS)
            high_share = high_count / len(spreads) if spreads else 0.0

            episodes, episode_hours = count_persistent_episodes(secs, spreads)

            data_gate = (
                len(spreads) >= VALID_SECONDS_MIN
                and len(hours) == ACTIVE_HOURS_REQUIRED
            )

            structural_gates = {
                "p75_spread_gte10bps": p75 is not None and p75 >= P75_GATE_BPS,
                "share_spread_gte10bps_gte020": high_share >= HIGH_SPREAD_SHARE_MIN,
                "persistent_high_spread_episodes_gte100": episodes >= EPISODE_MIN,
                "persistent_episode_hours_gte12": len(episode_hours) >= EPISODE_HOURS_MIN,
            }

            eligible = data_gate and all(structural_gates.values())

            results[inst] = {
                "data_gate_pass": data_gate,
                "structural_eligible": eligible,
                "valid_sampled_seconds": len(spreads),
                "active_utc_hours": len(hours),
                "p50_quoted_spread_bps": p50,
                "p75_quoted_spread_bps": p75,
                "p90_quoted_spread_bps": p90,
                "seconds_spread_gte10bps": high_count,
                "share_spread_gte10bps": high_share,
                "persistent_high_spread_episode_count": episodes,
                "persistent_episode_utc_hours": len(episode_hours),
                "structural_gates": structural_gates,
                "failed_structural_gates": [
                    k for k, v in structural_gates.items() if not v
                ],
            }

            print(
                f"{inst}: data={data_gate} eligible={eligible} "
                f"p75={p75} share10={high_share} "
                f"episodes={episodes} hours={len(episode_hours)}",
                flush=True,
            )

        data_pass_count = sum(
            1 for x in results.values() if x["data_gate_pass"] is True
        )
        eligible_assets = [
            inst for inst, x in results.items()
            if x["structural_eligible"] is True
        ]

        if data_pass_count < 5:
            status = DEFER
        elif len(eligible_assets) >= UNIVERSE_ELIGIBLE_MIN:
            status = SURVIVE
        else:
            status = REJECT

        strategy = {
            "stage": STAGE,
            "version": "0.1",
            "status": status,
            "selection_calibration_only": True,
            "candidate": "C7",
            "mechanism": "spread-qualified non-BTC passive/hybrid maker universe",
            "fixed_date": FIXED_DATE,
            "universe": list(INSTS),
            "structural_architecture": {
                "entry": "maker",
                "exit": "taker_fail_safe",
                "maker_fee_reference_bps": 2.0,
                "taker_fee_reference_bps": 5.0,
                "adverse_model_reserve_bps": 3.0,
                "gross_quoted_spread_hurdle_bps": SPREAD_HURDLE_BPS,
            },
            "persistence_seconds": PERSISTENCE_SECONDS,
            "per_asset": results,
            "data_pass_asset_count": data_pass_count,
            "eligible_asset_count": len(eligible_assets),
            "eligible_assets": eligible_assets,
            "universe_survival_gate": f"eligible_assets >= {UNIVERSE_ELIGIBLE_MIN}",
            "maker_order_simulated": False,
            "fill_model_calculated": False,
            "queue_model_calculated": False,
            "adverse_selection_outcome_calculated": False,
            "pnl_calculated": False,
            "promotional_alpha_accessed": False,
        }

        feature = {
            "stage": "SC001-C7-S0-FEATURE-BLOCK-EVIDENCE-V0.1",
            "version": "0.1",
            "evidence_maturity": "SELECTION_CALIBRATION_ONLY",
            "strategy_status_reference": status,
            "blocks": {
                "C7-F1": {
                    "name": "quoted spread state",
                    "roles": ["R2", "R6"],
                    "measurement_validity": True,
                    "hurdle_bps": SPREAD_HURDLE_BPS,
                    "per_asset_p75_bps": {
                        inst: results[inst]["p75_quoted_spread_bps"]
                        for inst in INSTS
                    },
                    "per_asset_high_spread_share": {
                        inst: results[inst]["share_spread_gte10bps"]
                        for inst in INSTS
                    },
                },
                "C7-F2": {
                    "name": "persistent high-spread regime",
                    "roles": ["R2", "R4"],
                    "measurement_validity": True,
                    "persistence_seconds": PERSISTENCE_SECONDS,
                    "per_asset_episode_count": {
                        inst: results[inst]["persistent_high_spread_episode_count"]
                        for inst in INSTS
                    },
                    "per_asset_episode_hour_breadth": {
                        inst: results[inst]["persistent_episode_utc_hours"]
                        for inst in INSTS
                    },
                },
            },
            "works_global_claim_allowed": False,
            "execution_evidence_present": False,
            "promotional_alpha_accessed": False,
        }

        atomic_json(STRATEGY_OUT, strategy)
        atomic_json(FEATURE_OUT, feature)

        print(status)
        print("data_pass_asset_count =", data_pass_count, "/", len(INSTS))
        print("eligible_asset_count =", len(eligible_assets))
        print("eligible_assets =", ",".join(eligible_assets) if eligible_assets else "NONE")
        print("maker/fill/queue/adverse-selection/PnL = False")
        print("promotional alpha accessed = False")
        print("strategy_report =", STRATEGY_OUT)
        print("feature_report =", FEATURE_OUT)
        return 0

    except Exception as exc:
        print("C7_S0_IMPLEMENTATION_FAIL")
        print("error =", f"{type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
