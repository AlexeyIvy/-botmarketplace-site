from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import statistics
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

STAGE = "SC001-C9-S1-SCHEDULED-POST-FUNDING-RELATIVE-NORMALIZATION-V0.1"
SURVIVE = "C9_S1_SENTINEL_SURVIVE"
REJECT = "C9_S1_REJECT_SENTINEL"
DEFER = "C9_S1_DEFER_SAMPLE_OR_SIGN_BREADTH"

ASSETS = ("BTC", "ETH", "DOGE", "ORDI", "UNI", "XRP", "OP", "BCH")
SWAPS = tuple(f"{s}-USDT-SWAP" for s in ASSETS)

SEP_START_MS = 1725148800000  # 2024-09-01T00:00:00Z
OCT_START_MS = 1727740800000  # 2024-10-01T00:00:00Z

BAR_MS = 15 * 60 * 1000
HORIZON_MS = 30 * 60 * 1000

POOL_MIN = 500
ASSET_MIN = 60
POS_SIGN_MIN = 20
NEG_SIGN_MIN = 20
DAY_MIN = 25

SCREEN_HURDLE_BPS = 30.0
MEDIAN_HURDLE_BPS = 20.0
POSITIVE_ASSET_MIN = 6
POSITIVE_DAY_SHARE_MIN = 0.60

DATA_ROOT = Path(
    os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))
).expanduser().resolve()

D1_REPORT = (
    DATA_ROOT
    / "SC001_C9_D1_V03_FUNDING_ARCHIVE"
    / "sc001_c9_d1_v03_funding_archive_integrity_report_v0_1.json"
)
D2_REPORT = (
    DATA_ROOT
    / "SC001_C9_D2_MARK_INDEX_15M"
    / "sc001_c9_d2_mark_index_15m_integrity_report_v0_1.json"
)

ARCHIVE_ROOT = DATA_ROOT / "SC001_C9_D1_FUNDING_ARCHIVE" / "archives"
OUT_DIR = DATA_ROOT / "SC001_C9_S1_SENTINEL"
STRATEGY_OUT = OUT_DIR / "c9_s1_strategy_evidence_v0_1.json"
FEATURE_OUT = OUT_DIR / "c9_s1_feature_block_evidence_v0_1.json"


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing required JSON: {path}")
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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def finite_decimal(text: str) -> Decimal:
    try:
        x = Decimal(str(text).strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError(f"invalid decimal {text!r}") from exc
    if not x.is_finite():
        raise ValueError(f"nonfinite decimal {text!r}")
    return x


def require_parents() -> tuple[dict, dict]:
    d1 = load_json(D1_REPORT)
    if d1.get("status") != "C9_D1_V03_FUNDING_ARCHIVE_INTEGRITY_PASS":
        fail("D1 parent not exact PASS")
    if int(d1.get("assets_passed", 0)) != 8:
        fail("D1 assets_passed mismatch")
    if d1.get("october_funding_body_accessed_by_v03") is not False:
        fail("D1 v0.3 October-access firewall mismatch")
    if d1.get("prior_october_funding_contamination_known") is not True:
        fail("D1 prior October contamination acknowledgement missing")
    if d1.get("october_funding_clean_c9_confirmation_eligible") is not False:
        fail("D1 October funding confirmation eligibility mismatch")

    d2 = load_json(D2_REPORT)
    if d2.get("status") != "C9_D2_MARK_INDEX_15M_INTEGRITY_PASS":
        fail("D2 parent not exact PASS")
    if int(d2.get("assets_passed", 0)) != 8:
        fail("D2 assets_passed mismatch")
    if d2.get("october_utc_mark_index_accessed") is not False:
        fail("D2 October mark/index firewall mismatch")

    return d1, d2


def exact_sep_zip(inst: str) -> Path:
    asset = inst.split("-")[0]
    return ARCHIVE_ROOT / asset / f"{inst}-fundingrates-2024-09.zip"


def parse_funding_rows(path: Path, inst: str) -> list[tuple[int, float]]:
    import zipfile
    import io

    if path.name != f"{inst}-fundingrates-2024-09.zip":
        fail(f"refusing non-September funding body: {path.name}")
    if not path.exists():
        fail(f"missing funding archive: {path}")

    out: list[tuple[int, float]] = []
    with zipfile.ZipFile(path, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            fail(f"ZIP CRC failure: {path.name} {bad}")

        for info in [x for x in zf.infolist() if not x.is_dir()]:
            if not info.filename.lower().endswith(".csv"):
                fail(f"non-CSV member in funding ZIP: {info.filename}")
            with zf.open(info, "r") as raw:
                reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline=""))
                for fields in reader:
                    if not fields or len(fields) < 3:
                        continue
                    if fields[0] != inst:
                        continue
                    try:
                        rate = float(finite_decimal(fields[1]))
                        ts = int(fields[2].strip())
                    except Exception as exc:
                        raise RuntimeError(
                            f"malformed target funding row {path.name}: {fields!r}"
                        ) from exc
                    if SEP_START_MS <= ts < OCT_START_MS:
                        out.append((ts, rate))

    by_ts: dict[int, float] = {}
    for ts, rate in out:
        prev = by_ts.get(ts)
        if prev is not None and not math.isclose(prev, rate, rel_tol=0, abs_tol=0):
            fail(f"conflicting duplicate funding rate {inst} at {ts}")
        by_ts[ts] = rate

    return sorted(by_ts.items())


def load_mark_index_csv(path: Path) -> dict[int, tuple[float, float]]:
    if not path.exists():
        fail(f"missing normalized D2 file: {path}")

    out: dict[int, tuple[float, float]] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        expected = {
            "ts_ms",
            "mark_open","mark_high","mark_low","mark_close",
            "index_open","index_high","index_low","index_close",
            "confirmed",
        }
        if set(r.fieldnames or []) != expected:
            fail(f"normalized D2 header mismatch: {path.name}")

        for row in r:
            ts = int(row["ts_ms"])
            if row["confirmed"] != "1":
                fail(f"unconfirmed normalized row: {path.name} {ts}")
            mc = float(row["mark_close"])
            ic = float(row["index_close"])
            if not (math.isfinite(mc) and math.isfinite(ic) and mc > 0 and ic > 0):
                fail(f"invalid normalized close: {path.name} {ts}")
            out[ts] = (mc, ic)

    return out


def premium_bps(mark: float, index: float) -> float:
    return 10_000.0 * (mark / index - 1.0)


def trimmed_mean(values: list[float], frac: float = 0.10) -> float | None:
    if not values:
        return None
    vals = sorted(values)
    k = int(math.floor(len(vals) * frac))
    core = vals[k:len(vals)-k] if k > 0 else vals
    return statistics.fmean(core) if core else None


def main() -> int:
    try:
        d1, d2 = require_parents()

        if STRATEGY_OUT.exists():
            old = load_json(STRATEGY_OUT)
            if old.get("status") in {SURVIVE, REJECT, DEFER}:
                fail(f"one-shot guard: terminal S1 report already exists: {old.get('status')}")

        events: list[dict] = []
        by_asset: dict[str, list[float]] = {a: [] for a in ASSETS}
        sign_counts = {"positive": 0, "negative": 0}
        event_counts: dict[str, int] = {}

        for i, inst in enumerate(SWAPS, start=1):
            asset = inst.split("-")[0]
            print(f"C9-S1 [{i}/8] {inst}", flush=True)

            d1_asset = (d1.get("assets") or {}).get(inst)
            if not isinstance(d1_asset, dict) or d1_asset.get("integrity_pass") is not True:
                fail(f"D1 asset integrity missing: {inst}")

            funding_path = exact_sep_zip(inst)
            if funding_path.stat().st_size != int(d1_asset["archive_bytes"]):
                fail(f"D1 archive byte mismatch: {inst}")
            if sha256_file(funding_path) != d1_asset["archive_sha256"]:
                fail(f"D1 archive SHA mismatch: {inst}")

            d2_asset = (d2.get("assets") or {}).get(inst)
            if not isinstance(d2_asset, dict) or d2_asset.get("integrity_pass") is not True:
                fail(f"D2 asset integrity missing: {inst}")
            norm = d2_asset.get("normalized_file") or {}
            norm_path = Path(str(norm.get("path", "")))
            if not norm_path.exists():
                fail(f"D2 normalized file missing: {inst}")
            if norm_path.stat().st_size != int(norm["bytes"]):
                fail(f"D2 normalized byte mismatch: {inst}")
            if sha256_file(norm_path) != norm["sha256"]:
                fail(f"D2 normalized SHA mismatch: {inst}")

            funding = parse_funding_rows(funding_path, inst)
            series = load_mark_index_csv(norm_path)

            local_count = 0
            for ts, rate in funding:
                if rate == 0:
                    continue

                pre_ts = ts - BAR_MS
                post_ts = ts + BAR_MS

                pre = series.get(pre_ts)
                post = series.get(post_ts)
                if pre is None or post is None:
                    fail(f"missing causal pre/post bar for {inst} funding {ts}")

                pre_p = premium_bps(pre[0], pre[1])
                post_p = premium_bps(post[0], post[1])
                sgn = 1 if rate > 0 else -1
                resp = -sgn * (post_p - pre_p)

                day = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")

                events.append({
                    "asset": asset,
                    "funding_time_ms": ts,
                    "date": day,
                    "funding_sign": sgn,
                    "pre_premium_bps": pre_p,
                    "post_premium_bps": post_p,
                    "signed_normalization_bps": resp,
                })

                by_asset[asset].append(resp)
                sign_counts["positive" if sgn > 0 else "negative"] += 1
                local_count += 1

            event_counts[asset] = local_count
            print(f"C9-S1 {inst}: events={local_count}", flush=True)

        vals = [float(e["signed_normalization_bps"]) for e in events]
        pooled_trim = trimmed_mean(vals, 0.10)
        pooled_median = statistics.median(vals) if vals else None

        asset_means = {
            a: (statistics.fmean(v) if v else None)
            for a, v in by_asset.items()
        }
        active_asset_means = [v for v in asset_means.values() if v is not None]
        eq_asset_mean = (
            statistics.fmean(active_asset_means) if active_asset_means else None
        )
        med_asset_mean = (
            statistics.median(active_asset_means) if active_asset_means else None
        )
        positive_asset_count = sum(
            1 for v in active_asset_means if v > 0
        )

        by_day: dict[str, list[float]] = {}
        for e in events:
            by_day.setdefault(str(e["date"]), []).append(
                float(e["signed_normalization_bps"])
            )
        day_means = {d: statistics.fmean(v) for d, v in by_day.items()}
        eq_day_mean = (
            statistics.fmean(day_means.values()) if day_means else None
        )
        positive_day_share = (
            sum(1 for v in day_means.values() if v > 0) / len(day_means)
            if day_means else 0.0
        )

        sample_gates = {
            "pooled_events_gte500": len(events) >= POOL_MIN,
            "each_asset_events_gte60": all(event_counts.get(a, 0) >= ASSET_MIN for a in ASSETS),
            "calendar_days_gte25": len(day_means) >= DAY_MIN,
            "positive_funding_obs_gte20": sign_counts["positive"] >= POS_SIGN_MIN,
            "negative_funding_obs_gte20": sign_counts["negative"] >= NEG_SIGN_MIN,
        }

        econ_gates = {
            "trimmed_mean_gte30": pooled_trim is not None and pooled_trim >= SCREEN_HURDLE_BPS,
            "pooled_median_gte20": pooled_median is not None and pooled_median >= MEDIAN_HURDLE_BPS,
            "equal_weight_asset_mean_gte30": eq_asset_mean is not None and eq_asset_mean >= SCREEN_HURDLE_BPS,
            "median_asset_mean_gte20": med_asset_mean is not None and med_asset_mean >= MEDIAN_HURDLE_BPS,
            "positive_asset_count_gte6": positive_asset_count >= POSITIVE_ASSET_MIN,
            "equal_weight_day_mean_gte30": eq_day_mean is not None and eq_day_mean >= SCREEN_HURDLE_BPS,
            "positive_day_share_gte060": positive_day_share >= POSITIVE_DAY_SHARE_MIN,
        }

        if not all(sample_gates.values()):
            status = DEFER
        elif all(econ_gates.values()):
            status = SURVIVE
        else:
            status = REJECT

        strategy_report = {
            "stage": STAGE,
            "version": "0.1",
            "status": status,
            "selection_calibration_only": True,
            "variant_count": 1,
            "mechanism": "scheduled post-funding mark/index relative normalization",
            "execution_archetype": "T3_PAIRED_RELATIVE_VALUE_PROXY",
            "structural_fill_count": 4,
            "fee_reference_bps_per_fill": 5.0,
            "screening_gross_hurdle_bps": 30.0,
            "event_count": len(events),
            "funding_sign_counts": sign_counts,
            "per_asset_event_count": event_counts,
            "per_asset_mean_signed_normalization_bps": asset_means,
            "pooled_trimmed_mean_signed_normalization_bps": pooled_trim,
            "pooled_median_signed_normalization_bps": pooled_median,
            "equal_weight_asset_mean_bps": eq_asset_mean,
            "median_asset_mean_bps": med_asset_mean,
            "positive_asset_count": positive_asset_count,
            "calendar_day_count": len(day_means),
            "calendar_day_means_bps": day_means,
            "equal_weight_calendar_day_mean_bps": eq_day_mean,
            "positive_calendar_day_share": positive_day_share,
            "sample_gates": sample_gates,
            "economic_gates": econ_gates,
            "failed_sample_gates": [k for k, v in sample_gates.items() if not v],
            "failed_economic_gates": [k for k, v in econ_gates.items() if not v],
            "events": events,
            "promotional_alpha_accessed": False,
            "net_pnl_calculated": False,
            "october_funding_body_opened_by_s1": False,
            "october_utc_mark_index_opened_by_s1": False,
            "prior_october_funding_contamination_known": True,
        }

        feature_report = {
            "stage": "SC001-C9-S1-FEATURE-BLOCK-EVIDENCE-V0.1",
            "version": "0.1",
            "evidence_maturity": "SELECTION_CALIBRATION_ONLY",
            "blocks": {
                "C9-F1": {
                    "name": "funding sign state",
                    "primitive": "P8",
                    "roles": ["R2", "R1_event_direction_input"],
                    "measurement_validity": True,
                    "positive_observations": sign_counts["positive"],
                    "negative_observations": sign_counts["negative"],
                    "magnitude_threshold_used": False,
                },
                "C9-F2": {
                    "name": "scheduled funding clock",
                    "primitive": "P11",
                    "roles": ["R2"],
                    "measurement_validity": True,
                    "event_count": len(events),
                    "calendar_day_count": len(day_means),
                },
                "C9-F3": {
                    "name": "mark/index premium",
                    "primitive": "P8_P7",
                    "roles": ["R6", "R2"],
                    "measurement_validity": True,
                    "directional_response_metric": "signed_normalization_bps",
                    "pooled_trimmed_mean_bps": pooled_trim,
                    "pooled_median_bps": pooled_median,
                    "equal_weight_asset_mean_bps": eq_asset_mean,
                    "median_asset_mean_bps": med_asset_mean,
                    "positive_asset_count": positive_asset_count,
                    "equal_weight_day_mean_bps": eq_day_mean,
                    "positive_day_share": positive_day_share,
                    "economic_magnitude_hurdle_bps": 30.0,
                },
                "RB008": {
                    "name": "causal reference semantics",
                    "roles": ["R6"],
                    "measurement_validity": True,
                    "used_as_reference_only": True,
                },
            },
            "strategy_status_reference": status,
            "works_global_claim_allowed": False,
            "promotional_alpha_accessed": False,
        }

        atomic_json(STRATEGY_OUT, strategy_report)
        atomic_json(FEATURE_OUT, feature_report)

        print(status)
        print("event_count =", len(events))
        print("funding_sign_counts =", sign_counts)
        print("pooled_trimmed_mean_bps =", pooled_trim)
        print("pooled_median_bps =", pooled_median)
        print("equal_weight_asset_mean_bps =", eq_asset_mean)
        print("median_asset_mean_bps =", med_asset_mean)
        print("positive_asset_count =", positive_asset_count)
        print("calendar_day_count =", len(day_means))
        print("equal_weight_calendar_day_mean_bps =", eq_day_mean)
        print("positive_calendar_day_share =", positive_day_share)
        print("failed_sample_gates =", strategy_report["failed_sample_gates"])
        print("failed_economic_gates =", strategy_report["failed_economic_gates"])
        print("strategy_report =", STRATEGY_OUT)
        print("feature_report =", FEATURE_OUT)
        return 0

    except Exception as exc:
        print("C9_S1_IMPLEMENTATION_FAIL")
        print("error =", f"{type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
