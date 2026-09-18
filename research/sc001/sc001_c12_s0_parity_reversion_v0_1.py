from __future__ import annotations

import csv
import io
import json
import math
import os
import statistics
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

STAGE = "SC001-C12-S0-H1-PARITY-REVERSION-V0.1"
SURVIVE = "C12_S0_PARITY_REVERSION_SURVIVE"
REJECT = "C12_S0_REJECT_PARITY_REVERSION"
DEFER = "C12_S0_DEFER_DATA_QUALITY"

INST = "USDC-USDT"

TARGET_START_US = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp() * 1_000_000)
TARGET_END_US = int(datetime(2025, 7, 1, tzinfo=timezone.utc).timestamp() * 1_000_000)
SUPPORT_END_US = TARGET_END_US + 30 * 60 * 1_000_000

ENTRY_BPS = 30.0
REARM_BAND_BPS = 10.0
MAX_HOLD_US = 30 * 60 * 1_000_000

TARGET_DAY_MIN = 175
MONTH_COUNT_REQUIRED = 6

EPISODE_MIN = 12
EPISODE_DAY_MIN = 6
EPISODE_MONTH_MIN = 6
SUCCESS_SHARE_MIN = 0.60
MEDIAN_REVERSION_MIN_BPS = 15.0
P75_REVERSION_MIN_BPS = 20.0

HEADER = [
    "instrument_name",
    "trade_id",
    "side",
    "price",
    "size",
    "created_time",
]

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/sc001-c12-s0-parity-reversion-sentinel-v0.1.md"
REGISTRY = ROOT / "docs/research/sc001-contamination-registry-v0.17.json"
FREEZE = ROOT / "docs/research/sc001-c12-s0-implementation-freeze-v0.1.json"

DATA_ROOT = Path(
    os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))
).expanduser().resolve()

D3_ROOT = DATA_ROOT / "SC001_C12_D3_H1_BODY_INTEGRITY"
D3_REPORT = D3_ROOT / "sc001_c12_d3_h1_body_integrity_report_v0_1.json"

OUT_DIR = DATA_ROOT / "SC001_C12_S0_PARITY_REVERSION"
STRATEGY_OUT = OUT_DIR / "c12_s0_strategy_evidence_v0_1.json"
FEATURE_OUT = OUT_DIR / "c12_s0_feature_block_evidence_v0_1.json"


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
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require_freeze() -> dict:
    fr = load_json(FREEZE)

    if fr.get("status") != "FROZEN_BEFORE_FIRST_C12_S0_OUTCOME":
        fail("C12-S0 freeze status mismatch")
    if fr.get("runner_git_blob_sha") != git_blob(Path(__file__).resolve()):
        fail("C12-S0 runner identity mismatch")
    if fr.get("protocol_git_blob_sha") != git_blob(PROTOCOL):
        fail("C12-S0 protocol identity mismatch")
    if fr.get("contamination_registry_git_blob_sha") != git_blob(REGISTRY):
        fail("C12-S0 registry identity mismatch")

    expected = {
        "entry_threshold_bps": ENTRY_BPS,
        "parity_rearm_exit_band_bps": REARM_BAND_BPS,
        "max_hold_minutes": 30,
        "target_day_min": TARGET_DAY_MIN,
        "episode_min": EPISODE_MIN,
        "episode_day_min": EPISODE_DAY_MIN,
        "episode_month_min": EPISODE_MONTH_MIN,
        "success_share_min": SUCCESS_SHARE_MIN,
        "median_reversion_min_bps": MEDIAN_REVERSION_MIN_BPS,
        "p75_reversion_min_bps": P75_REVERSION_MIN_BPS,
    }
    for k, v in expected.items():
        if fr.get(k) != v:
            fail(f"C12-S0 freeze mismatch {k}: {fr.get(k)!r} != {v!r}")

    for k in (
        "maker_order_simulation_authorized",
        "fill_model_authorized",
        "queue_model_authorized",
        "pnl_authorized",
        "promotional_alpha_authorized",
    ):
        if fr.get(k) is not False:
            fail(f"C12-S0 firewall mismatch: {k}")

    return fr


def require_registry() -> dict:
    reg = load_json(REGISTRY)
    if str(reg.get("version")) != "0.17":
        fail("contamination registry version mismatch")

    row = reg.get("c12_s0_h1_parity_calibration") or {}
    if row.get("classification") != "NONPROMOTIONAL_SELECTION_CALIBRATION":
        fail("C12-S0 calibration role mismatch")
    if row.get("historical_trade_body_access_authorized") is not True:
        fail("C12-S0 body access not authorized")
    if row.get("peg_deviation_authorized") is not True:
        fail("C12-S0 peg deviation not authorized")
    if row.get("reversion_outcome_authorized") is not True:
        fail("C12-S0 reversion outcome not authorized")

    if float(row.get("entry_threshold_bps", -1)) != ENTRY_BPS:
        fail("C12-S0 registry entry threshold mismatch")
    if float(row.get("parity_rearm_exit_band_bps", -1)) != REARM_BAND_BPS:
        fail("C12-S0 registry parity band mismatch")
    if int(row.get("max_hold_minutes", 0)) != 30:
        fail("C12-S0 registry max-hold mismatch")

    return reg


def require_d3() -> dict:
    rep = load_json(D3_REPORT)
    if rep.get("status") != "C12_D3_H1_BODY_INTEGRITY_PASS":
        fail("C12-D3 parent not exact PASS")
    if int(rep.get("archive_count", 0)) != 182:
        fail("C12-D3 archive count mismatch")

    for k in (
        "peg_deviation_calculated",
        "parity_episode_calculated",
        "reversion_outcome_calculated",
        "strategy_signal_calculated",
        "fill_model_calculated",
        "pnl_calculated",
        "promotional_alpha_accessed",
    ):
        if rep.get(k) is not False:
            fail(f"C12-D3 parent firewall mismatch: {k}")

    return rep


def norm_ts(text: str) -> int:
    v = int(str(text).strip())
    a = abs(v)

    if a >= 10**17:
        return v // 1000
    if a >= 10**14:
        return v
    if a >= 10**11:
        return v * 1000
    if a >= 10**9:
        return v * 1_000_000

    fail(f"unresolved timestamp scale: {text}")


def nearest_rank(values: list[float], q: float) -> float | None:
    if not values:
        return None

    vals = sorted(values)
    idx = max(0, min(len(vals) - 1, math.ceil(q * len(vals)) - 1))
    return vals[idx]


def iter_trades(archives: list[dict]):
    prev_global_ts = None
    prev_global_id = None

    for i, meta in enumerate(archives, start=1):
        ds = str(meta.get("date"))
        filename = str(meta.get("filename"))
        expected_bytes = int(meta.get("bytes", -1))
        expected_sha = str(meta.get("sha256"))

        path = D3_ROOT / "archives" / filename

        if not path.exists():
            fail(f"missing C12-D3 archive: {filename}")
        if path.stat().st_size != expected_bytes:
            fail(f"archive byte mismatch: {filename}")
        if sha256_file(path) != expected_sha:
            fail(f"archive SHA mismatch: {filename}")

        if i == 1 or i % 20 == 0 or i == len(archives):
            print(
                f"C12-S0 source [{i}/{len(archives)}] {ds}",
                flush=True,
            )

        with zipfile.ZipFile(path, "r") as zf:
            bad = zf.testzip()
            if bad is not None:
                fail(f"ZIP CRC failure {filename}: {bad}")

            members = [x for x in zf.infolist() if not x.is_dir()]
            if len(members) != 1:
                fail(f"ZIP member count mismatch: {filename}")

            with zf.open(members[0], "r") as raw:
                r = csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline=""))

                if next(r, None) != HEADER:
                    fail(f"header mismatch: {filename}")

                for row in r:
                    if not row:
                        continue

                    if len(row) != 6:
                        fail(f"row length mismatch: {filename}")
                    if row[0] != INST:
                        fail(f"instrument mismatch: {filename}")
                    if row[2] not in {"buy", "sell"}:
                        fail(f"side mismatch: {filename}")

                    tid = int(row[1])
                    price = float(row[3])
                    size = float(row[4])
                    ts = norm_ts(row[5])

                    if not (
                        math.isfinite(price) and price > 0
                        and math.isfinite(size) and size > 0
                    ):
                        fail(f"invalid price/size: {filename}")

                    if ts < TARGET_START_US:
                        continue
                    if ts > SUPPORT_END_US:
                        return

                    if prev_global_ts is not None and ts < prev_global_ts:
                        fail(
                            f"global timestamp reversal at {filename}: "
                            f"{ts} < {prev_global_ts}"
                        )
                    if prev_global_id is not None and tid <= prev_global_id:
                        fail(
                            f"global trade id nonmonotonic at {filename}: "
                            f"{tid} <= {prev_global_id}"
                        )

                    prev_global_ts = ts
                    prev_global_id = tid

                    yield ts, tid, price


def target_day_key(ts_us: int) -> str:
    dt = datetime.fromtimestamp(ts_us / 1_000_000, tz=timezone.utc)
    return dt.date().isoformat()


def target_month_key(ts_us: int) -> str:
    dt = datetime.fromtimestamp(ts_us / 1_000_000, tz=timezone.utc)
    return f"{dt.year:04d}-{dt.month:02d}"


def main() -> int:
    try:
        require_freeze()
        require_registry()
        d3 = require_d3()

        if STRATEGY_OUT.exists():
            old = load_json(STRATEGY_OUT)
            if old.get("status") in {SURVIVE, REJECT, DEFER}:
                fail(
                    "one-shot guard: terminal C12-S0 report already exists: "
                    + str(old.get("status"))
                )

        archives = d3.get("archives") or []
        if len(archives) != 182:
            fail(f"C12-D3 archive list count mismatch: {len(archives)}")

        target_days: set[str] = set()
        target_months: set[str] = set()

        armed = False
        active = None
        episodes: list[dict] = []
        last_trade = None

        for ts, tid, price in iter_trades(archives):
            in_target = TARGET_START_US <= ts < TARGET_END_US

            if in_target:
                target_days.add(target_day_key(ts))
                target_months.add(target_month_key(ts))

            deviation = 10_000.0 * math.log(price / 1.0)
            abs_dev = abs(deviation)

            # Resolve active episode before considering any new arm/entry state.
            if active is not None:
                deadline = int(active["deadline_ts_us"])

                if ts <= deadline and abs_dev <= REARM_BAND_BPS:
                    sign = int(active["sign"])
                    gross = sign * 10_000.0 * math.log(
                        float(active["entry_price"]) / price
                    )

                    active["exit_ts_us"] = ts
                    active["exit_price"] = price
                    active["exit_deviation_bps"] = deviation
                    active["success_within_30m"] = True
                    active["gross_reversion_bps"] = gross
                    active["hold_seconds"] = (
                        ts - int(active["entry_ts_us"])
                    ) / 1_000_000.0
                    active["evaluable"] = True
                    episodes.append(active)

                    active = None
                    armed = True

                elif ts > deadline:
                    # Close at the last trade at/before the frozen deadline.
                    if last_trade is None:
                        active["evaluable"] = False
                        active["unevaluable_reason"] = "no_deadline_prior_trade"
                        episodes.append(active)
                    else:
                        last_ts, _last_id, last_price = last_trade
                        stale = deadline - last_ts

                        if stale < 0 or stale > 60 * 1_000_000:
                            active["evaluable"] = False
                            active["unevaluable_reason"] = (
                                "deadline_anchor_stale_gt60s"
                            )
                            active["deadline_staleness_ms"] = stale / 1000.0
                            episodes.append(active)
                        else:
                            exit_dev = 10_000.0 * math.log(last_price / 1.0)
                            sign = int(active["sign"])
                            gross = sign * 10_000.0 * math.log(
                                float(active["entry_price"]) / last_price
                            )

                            active["exit_ts_us"] = last_ts
                            active["exit_price"] = last_price
                            active["exit_deviation_bps"] = exit_dev
                            active["success_within_30m"] = False
                            active["gross_reversion_bps"] = gross
                            active["hold_seconds"] = (
                                last_ts - int(active["entry_ts_us"])
                            ) / 1_000_000.0
                            active["deadline_staleness_ms"] = stale / 1000.0
                            active["evaluable"] = True
                            episodes.append(active)

                    active = None
                    armed = False

            # New state transitions are allowed only for target-window trades.
            if active is None and in_target:
                if abs_dev <= REARM_BAND_BPS:
                    armed = True

                elif armed and abs_dev >= ENTRY_BPS:
                    active = {
                        "entry_ts_us": ts,
                        "entry_time_utc": datetime.fromtimestamp(
                            ts / 1_000_000,
                            tz=timezone.utc,
                        ).isoformat(),
                        "entry_trade_id": tid,
                        "entry_price": price,
                        "entry_deviation_bps": deviation,
                        "entry_abs_deviation_bps": abs_dev,
                        "sign": 1 if deviation > 0 else -1,
                        "entry_utc_date": target_day_key(ts),
                        "entry_utc_month": target_month_key(ts),
                        "deadline_ts_us": ts + MAX_HOLD_US,
                    }
                    armed = False

            last_trade = (ts, tid, price)

        # Final unresolved episode may use the last available support trade.
        if active is not None:
            deadline = int(active["deadline_ts_us"])

            if last_trade is None:
                active["evaluable"] = False
                active["unevaluable_reason"] = "no_final_support_trade"
            else:
                last_ts, _last_id, last_price = last_trade
                stale = deadline - last_ts

                if last_ts <= deadline and 0 <= stale <= 60 * 1_000_000:
                    exit_dev = 10_000.0 * math.log(last_price / 1.0)
                    sign = int(active["sign"])
                    gross = sign * 10_000.0 * math.log(
                        float(active["entry_price"]) / last_price
                    )

                    active["exit_ts_us"] = last_ts
                    active["exit_price"] = last_price
                    active["exit_deviation_bps"] = exit_dev
                    active["success_within_30m"] = False
                    active["gross_reversion_bps"] = gross
                    active["hold_seconds"] = (
                        last_ts - int(active["entry_ts_us"])
                    ) / 1_000_000.0
                    active["deadline_staleness_ms"] = stale / 1000.0
                    active["evaluable"] = True
                else:
                    active["evaluable"] = False
                    active["unevaluable_reason"] = "final_deadline_not_covered"

            episodes.append(active)

        evaluable = [e for e in episodes if e.get("evaluable") is True]
        successes = [e for e in evaluable if e.get("success_within_30m") is True]
        gross = [float(e["gross_reversion_bps"]) for e in evaluable]

        episode_days = {str(e["entry_utc_date"]) for e in evaluable}
        episode_months = {str(e["entry_utc_month"]) for e in evaluable}

        data_gates = {
            "target_days_with_trades_gte175": len(target_days) >= TARGET_DAY_MIN,
            "all_six_target_months_present": len(target_months) == MONTH_COUNT_REQUIRED,
        }

        success_share = (
            len(successes) / len(evaluable)
            if evaluable else None
        )
        median_gross = statistics.median(gross) if gross else None
        p75_gross = nearest_rank(gross, 0.75) if gross else None

        reversion_gates = {
            "evaluable_episodes_gte12": len(evaluable) >= EPISODE_MIN,
            "episode_dates_gte6": len(episode_days) >= EPISODE_DAY_MIN,
            "episode_months_eq6": len(episode_months) == EPISODE_MONTH_MIN,
            "success_share_gte060": (
                success_share is not None and success_share >= SUCCESS_SHARE_MIN
            ),
            "median_gross_reversion_gte15bps": (
                median_gross is not None
                and median_gross >= MEDIAN_REVERSION_MIN_BPS
            ),
            "p75_gross_reversion_gte20bps": (
                p75_gross is not None
                and p75_gross >= P75_REVERSION_MIN_BPS
            ),
        }

        if not all(data_gates.values()):
            status = DEFER
        elif all(reversion_gates.values()):
            status = SURVIVE
        else:
            status = REJECT

        strategy = {
            "stage": STAGE,
            "version": "0.1",
            "status": status,
            "selection_calibration_only": True,
            "candidate": "C12",
            "mechanism": "USDC-USDT stablecoin parity dislocation reversion",
            "target_window": "2025-01-01_to_2025-06-30",
            "source_support_window": "2025-01-01_to_2025-07-01_plus_30m_available_from_Jul1_archive",
            "parity_anchor": 1.0,
            "entry_threshold_bps": ENTRY_BPS,
            "rearm_exit_band_bps": REARM_BAND_BPS,
            "max_hold_minutes": 30,
            "structural_reference": {
                "fill_count": 2,
                "fee_reference_bps": 10.0,
                "spread_slippage_model_reserve_bps": 5.0,
                "structural_burden_bps": 15.0,
            },
            "target_days_with_trades": len(target_days),
            "target_months_with_trades": len(target_months),
            "episode_count_total": len(episodes),
            "evaluable_episode_count": len(evaluable),
            "successful_reversion_episode_count": len(successes),
            "episode_utc_date_count": len(episode_days),
            "episode_utc_month_count": len(episode_months),
            "success_share_within_30m": success_share,
            "median_gross_reversion_bps": median_gross,
            "p75_gross_reversion_bps": p75_gross,
            "data_gates": data_gates,
            "reversion_gates": reversion_gates,
            "failed_data_gates": [k for k, v in data_gates.items() if not v],
            "failed_reversion_gates": [
                k for k, v in reversion_gates.items() if not v
            ],
            "episodes": episodes,
            "maker_order_simulated": False,
            "fill_model_calculated": False,
            "queue_model_calculated": False,
            "pnl_calculated": False,
            "promotional_alpha_accessed": False,
        }

        feature = {
            "stage": "SC001-C12-S0-FEATURE-BLOCK-EVIDENCE-V0.1",
            "version": "0.1",
            "evidence_maturity": "SELECTION_CALIBRATION_ONLY",
            "strategy_status_reference": status,
            "blocks": {
                "C12-F1": {
                    "name": "direct stablecoin cross-parity deviation",
                    "roles": ["R2", "R6"],
                    "measurement_validity": True,
                    "formula": "10000*ln(USDCUSDT_trade_price/1.0)",
                    "entry_threshold_bps": ENTRY_BPS,
                    "parity_band_bps": REARM_BAND_BPS,
                },
                "C12-F2": {
                    "name": "30-minute parity reversion episode",
                    "roles": ["R1", "R2"],
                    "measurement_validity": True,
                    "evaluable_episode_count": len(evaluable),
                    "success_share_within_30m": success_share,
                    "median_gross_reversion_bps": median_gross,
                    "p75_gross_reversion_bps": p75_gross,
                },
            },
            "works_global_claim_allowed": False,
            "execution_evidence_present": False,
            "promotional_alpha_accessed": False,
        }

        atomic_json(STRATEGY_OUT, strategy)
        atomic_json(FEATURE_OUT, feature)

        print(status)
        print("target_days_with_trades =", len(target_days), "/ 181")
        print("target_months_with_trades =", len(target_months), "/ 6")
        print("episode_count_total =", len(episodes))
        print("evaluable_episode_count =", len(evaluable))
        print("successful_reversion_episode_count =", len(successes))
        print("episode_utc_date_count =", len(episode_days))
        print("episode_utc_month_count =", len(episode_months))
        print("success_share_within_30m =", success_share)
        print("median_gross_reversion_bps =", median_gross)
        print("p75_gross_reversion_bps =", p75_gross)
        print("failed_data_gates =", strategy["failed_data_gates"])
        print("failed_reversion_gates =", strategy["failed_reversion_gates"])
        print("fill/queue/PnL/promotional alpha = False")
        print("strategy_report =", STRATEGY_OUT)
        print("feature_report =", FEATURE_OUT)
        return 0

    except Exception as exc:
        print("C12_S0_IMPLEMENTATION_FAIL")
        print("error =", f"{type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
