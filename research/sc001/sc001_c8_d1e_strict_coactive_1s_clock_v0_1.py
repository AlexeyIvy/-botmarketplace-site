from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import math
import os
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

STAGE = "SC001-C8-D1E-STRICT-COACTIVE-1S-CLOCK-V0.1"
PASS = "C8_D1E_STRICT_COACTIVE_1S_PASS"
REVIEW = "C8_D1E_STRICT_COACTIVE_1S_REVIEW"

FIXED_DATE = "2025-01-15"
DAY_START_US = 1736899200000 * 1000
DAY_END_US = 1736985600000 * 1000
DAY_START_SEC = DAY_START_US // 1_000_000
TOTAL_SECONDS = 86_400

OKX_INST = "BTC-USDT-SWAP"
OKX_D = "BTC-USDT-SWAP-trades-2025-01-15.zip"
OKX_D1 = "BTC-USDT-SWAP-trades-2025-01-16.zip"
OKX_HEADER = ["instrument_name", "trade_id", "side", "price", "size", "created_time"]

BYBIT_FILE = "BTCUSDT2025-01-15.csv.gz"

JOINT_SECOND_MIN = 50_000
JOINT_HOUR_MIN = 24
MIN_JOINT_SECONDS_PER_HOUR = 600
P99_SKEW_MAX_MS = 1000.0

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/sc001-c8-d1e-strict-coactive-1s-clock-qualification-protocol-v0.1.md"
REGISTRY = ROOT / "docs/research/sc001-contamination-registry-v0.11.json"
FREEZE = ROOT / "docs/research/sc001-c8-d1e-implementation-freeze-v0.1.json"

DATA_ROOT = Path(
    os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))
).expanduser().resolve()

ARCHIVE_DIR = DATA_ROOT / "SC001_C8_D1_HISTORICAL_CLOCK" / "archives"
PARENT = (
    DATA_ROOT / "SC001_C8_D1_V02_HISTORICAL_CLOCK"
    / "sc001_c8_d1_v02_historical_clock_integrity_report_v0_1.json"
)

OUT_DIR = DATA_ROOT / "SC001_C8_D1E_STRICT_COACTIVE_1S"
OUT = OUT_DIR / "sc001_c8_d1e_strict_coactive_1s_report_v0_1.json"


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing JSON: {path}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        fail(f"JSON object expected: {path}")
    return obj


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
    if fr.get("status") != "FROZEN_BEFORE_C8_D1E_RUN":
        fail("D1E freeze status mismatch")
    if fr.get("runner_git_blob_sha") != git_blob(Path(__file__).resolve()):
        fail("D1E runner identity mismatch")
    if fr.get("protocol_git_blob_sha") != git_blob(PROTOCOL):
        fail("D1E protocol identity mismatch")
    if fr.get("contamination_registry_git_blob_sha") != git_blob(REGISTRY):
        fail("D1E registry identity mismatch")
    if fr.get("fixed_date") != FIXED_DATE:
        fail("D1E fixed date mismatch")
    if int(fr.get("joint_coactive_second_min", 0)) != JOINT_SECOND_MIN:
        fail("D1E joint-second gate mismatch")
    if int(fr.get("minimum_joint_seconds_per_hour", 0)) != MIN_JOINT_SECONDS_PER_HOUR:
        fail("D1E hourly gate mismatch")
    if float(fr.get("p99_last_event_skew_max_ms", -1)) != P99_SKEW_MAX_MS:
        fail("D1E skew gate mismatch")
    for k in (
        "cross_venue_price_comparison_authorized",
        "cross_venue_return_authorized",
        "dislocation_authorized",
        "lag_authorized",
        "leader_selection_authorized",
        "strategy_signal_authorized",
        "pnl_authorized",
        "promotional_alpha_authorized",
    ):
        if fr.get(k) is not False:
            fail(f"D1E firewall mismatch: {k}")
    return fr


def require_registry() -> dict:
    reg = load_json(REGISTRY)
    if str(reg.get("version")) != "0.11":
        fail("registry version mismatch")
    row = reg.get("c8_d1_v02_engineering_clock_calibration") or {}
    if row.get("classification") != "NONPROMOTIONAL_ENGINEERING_CLOCK_CALIBRATION":
        fail("engineering calibration role mismatch")
    return reg


def parent_archive_map() -> dict[str, dict]:
    rep = load_json(PARENT)
    if rep.get("status") != "C8_D1_V02_HISTORICAL_CLOCK_INTEGRITY_REVIEW":
        fail("D1 v0.2 parent status mismatch")
    if rep.get("cross_venue_price_compared") is not False:
        fail("parent cross-venue price firewall mismatch")
    if rep.get("cross_venue_return_calculated") is not False:
        fail("parent return firewall mismatch")
    if rep.get("dislocation_calculated") is not False:
        fail("parent dislocation firewall mismatch")
    if rep.get("lag_calculated") is not False:
        fail("parent lag firewall mismatch")

    rows: dict[str, dict] = {}
    for a in ((rep.get("okx") or {}).get("archives") or []):
        if isinstance(a, dict) and isinstance(a.get("filename"), str):
            rows[a["filename"]] = a
    b = ((rep.get("bybit") or {}).get("archive") or {})
    if isinstance(b, dict) and isinstance(b.get("filename"), str):
        rows[b["filename"]] = b

    expected = {OKX_D, OKX_D1, BYBIT_FILE}
    if set(rows) != expected:
        fail(f"parent archive set mismatch: {sorted(rows)}")
    return rows


def verify_local(path: Path, meta: dict) -> None:
    if not path.exists():
        fail(f"missing local archive: {path}")
    if path.stat().st_size != int(meta.get("bytes", -1)):
        fail(f"archive byte mismatch: {path.name}")
    if sha256_file(path) != meta.get("sha256"):
        fail(f"archive SHA mismatch: {path.name}")


def normalize_okx_ts_us(text: str) -> tuple[int, str]:
    v = int(str(text).strip())
    a = abs(v)
    if a >= 10**17:
        return v // 1000, "nanoseconds"
    if a >= 10**14:
        return v, "microseconds"
    if a >= 10**11:
        return v * 1000, "milliseconds"
    if a >= 10**9:
        return v * 1_000_000, "seconds"
    fail(f"unresolved OKX timestamp scale: {text}")


def scan_okx(path: Path, expected_filename: str, state: dict) -> dict:
    expected_member = expected_filename[:-4] + ".csv"
    source = {
        "filename": expected_filename,
        "invalid_rows": 0,
        "timestamp_reversals": 0,
        "trade_id_nonmonotonic": 0,
        "timestamp_scales": set(),
    }

    with zipfile.ZipFile(path, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            fail(f"ZIP CRC failure {expected_filename}: {bad}")
        members = [x for x in zf.infolist() if not x.is_dir()]
        if len(members) != 1:
            fail(f"ZIP member count mismatch: {expected_filename}")
        if Path(members[0].filename).name != expected_member:
            fail(f"ZIP member identity mismatch: {expected_filename}")

        with zf.open(members[0], "r") as raw:
            r = csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline=""))
            header = next(r, None)
            if header != OKX_HEADER:
                fail(f"OKX header mismatch: {expected_filename}")

            prev_source_ts = None
            prev_source_id = None

            for row in r:
                if not row:
                    continue
                if len(row) != 6:
                    source["invalid_rows"] += 1
                    continue
                try:
                    if row[0] != OKX_INST:
                        raise ValueError("instrument")
                    tid = int(row[1])
                    if row[2] not in {"buy", "sell"}:
                        raise ValueError("side")
                    price = float(row[3])
                    size = float(row[4])
                    ts, scale = normalize_okx_ts_us(row[5])
                    if not (
                        math.isfinite(price) and price > 0
                        and math.isfinite(size) and size > 0
                    ):
                        raise ValueError("price/size")
                except Exception:
                    source["invalid_rows"] += 1
                    continue

                source["timestamp_scales"].add(scale)

                if prev_source_ts is not None and ts < prev_source_ts:
                    source["timestamp_reversals"] += 1
                if prev_source_id is not None and tid <= prev_source_id:
                    source["trade_id_nonmonotonic"] += 1
                prev_source_ts = ts
                prev_source_id = tid

                if DAY_START_US <= ts < DAY_END_US:
                    if state["prev_ts"] is not None and ts < state["prev_ts"]:
                        state["timestamp_reversals"] += 1
                    if state["prev_id"] is not None:
                        d = tid - state["prev_id"]
                        if d <= 0:
                            state["trade_id_nonmonotonic"] += 1
                        elif d != 1:
                            state["trade_id_gap_count"] += 1

                    sec = ts // 1_000_000
                    state["last_ts_by_second"][sec] = ts
                    state["minutes"].add((ts - DAY_START_US) // 60_000_000)
                    state["sides"].add(row[2])
                    state["prev_ts"] = ts
                    state["prev_id"] = tid
                    state["admitted_rows"] += 1

    source["timestamp_scales"] = sorted(source["timestamp_scales"])
    return source


def parse_okx(d: Path, d1: Path) -> dict:
    state = {
        "last_ts_by_second": {},
        "minutes": set(),
        "sides": set(),
        "prev_ts": None,
        "prev_id": None,
        "timestamp_reversals": 0,
        "trade_id_nonmonotonic": 0,
        "trade_id_gap_count": 0,
        "admitted_rows": 0,
    }
    a = scan_okx(d, OKX_D, state)
    b = scan_okx(d1, OKX_D1, state)
    return {
        "last_ts_by_second": state["last_ts_by_second"],
        "admitted_rows": state["admitted_rows"],
        "minute_buckets": len(state["minutes"]),
        "buy_and_sell": state["sides"] == {"buy", "sell"},
        "timestamp_reversals": state["timestamp_reversals"],
        "trade_id_nonmonotonic": state["trade_id_nonmonotonic"],
        "trade_id_gap_count": state["trade_id_gap_count"],
        "sources": [a, b],
    }


def parse_bybit(path: Path) -> dict:
    last_ts_by_second = {}
    invalid = out_of_day = reversals = 0
    prev_ts = None

    with gzip.open(path, "rt", encoding="utf-8", errors="strict", newline="") as f:
        r = csv.reader(f)
        header = next(r, None)
        if not header or len(header) < 5:
            fail("Bybit header missing")
        low = [str(x).strip().lower() for x in header]
        if low[:5] != ["timestamp", "symbol", "side", "size", "price"]:
            fail(f"Bybit header semantics mismatch: {header[:5]}")

        for row in r:
            if not row:
                continue
            if len(row) < 5:
                invalid += 1
                continue
            try:
                ts = int(round(float(row[0]) * 1_000_000))
                if row[1].strip() != "BTCUSDT":
                    raise ValueError("symbol")
                if row[2].strip() not in {"Buy", "Sell"}:
                    raise ValueError("side")
                size = float(row[3])
                price = float(row[4])
                if not (
                    math.isfinite(size) and size > 0
                    and math.isfinite(price) and price > 0
                ):
                    raise ValueError("price/size")
            except Exception:
                invalid += 1
                continue

            if not (DAY_START_US <= ts < DAY_END_US):
                out_of_day += 1
                continue

            if prev_ts is not None and ts < prev_ts:
                reversals += 1
            prev_ts = ts

            sec = ts // 1_000_000
            last_ts_by_second[sec] = ts

    return {
        "last_ts_by_second": last_ts_by_second,
        "invalid_rows": invalid,
        "out_of_day_rows": out_of_day,
        "timestamp_reversals": reversals,
    }


def nearest_percentile(values: list[int], q: float) -> int | None:
    if not values:
        return None
    vals = sorted(values)
    i = max(0, min(len(vals)-1, int(math.ceil(q * len(vals))) - 1))
    return vals[i]


def main() -> int:
    try:
        require_freeze()
        require_registry()
        metas = parent_archive_map()

        paths = {
            OKX_D: ARCHIVE_DIR / OKX_D,
            OKX_D1: ARCHIVE_DIR / OKX_D1,
            BYBIT_FILE: ARCHIVE_DIR / BYBIT_FILE,
        }
        for fn, p in paths.items():
            verify_local(p, metas[fn])

        print("C8-D1E parse/stitch OKX timestamps", flush=True)
        okx = parse_okx(paths[OKX_D], paths[OKX_D1])
        print("C8-D1E parse Bybit timestamps", flush=True)
        bybit = parse_bybit(paths[BYBIT_FILE])

        okx_secs = set(okx["last_ts_by_second"])
        bybit_secs = set(bybit["last_ts_by_second"])
        joint_secs = sorted(okx_secs & bybit_secs)

        hourly = [0] * 24
        skews_us = []

        for sec in joint_secs:
            hour = (sec - DAY_START_SEC) // 3600
            if 0 <= hour < 24:
                hourly[hour] += 1
            skews_us.append(
                abs(
                    okx["last_ts_by_second"][sec]
                    - bybit["last_ts_by_second"][sec]
                )
            )

        okx_hours = {
            (s - DAY_START_SEC) // 3600
            for s in okx_secs
            if 0 <= (s - DAY_START_SEC) // 3600 < 24
        }
        bybit_hours = {
            (s - DAY_START_SEC) // 3600
            for s in bybit_secs
            if 0 <= (s - DAY_START_SEC) // 3600 < 24
        }
        joint_hours = {i for i, n in enumerate(hourly) if n > 0}

        p50_skew = nearest_percentile(skews_us, 0.50)
        p99_skew = nearest_percentile(skews_us, 0.99)

        gates = {
            "okx_source_integrity": (
                okx["timestamp_reversals"] == 0
                and okx["trade_id_nonmonotonic"] == 0
                and okx["trade_id_gap_count"] == 0
                and okx["minute_buckets"] == 1440
                and okx["buy_and_sell"] is True
                and all(
                    s["invalid_rows"] == 0
                    and s["timestamp_reversals"] == 0
                    and s["trade_id_nonmonotonic"] == 0
                    and len(s["timestamp_scales"]) == 1
                    for s in okx["sources"]
                )
            ),
            "bybit_source_integrity": (
                bybit["invalid_rows"] == 0
                and bybit["out_of_day_rows"] == 0
                and bybit["timestamp_reversals"] == 0
            ),
            "okx_active_hours_24": len(okx_hours) == 24,
            "bybit_active_hours_24": len(bybit_hours) == 24,
            "joint_coactive_seconds_gte50000": len(joint_secs) >= JOINT_SECOND_MIN,
            "joint_coactive_hours_24": len(joint_hours) == JOINT_HOUR_MIN,
            "min_joint_seconds_per_hour_gte600": min(hourly) >= MIN_JOINT_SECONDS_PER_HOUR,
            "p99_last_event_skew_lte1000ms": (
                p99_skew is not None and p99_skew / 1000.0 <= P99_SKEW_MAX_MS
            ),
        }

        status = PASS if all(gates.values()) else REVIEW

        report = {
            "stage": STAGE,
            "version": "0.1",
            "status": status,
            "fixed_date": FIXED_DATE,
            "representation": "STRICT_COACTIVE_1S_NO_CARRY_FORWARD",
            "okx_admitted_rows": okx["admitted_rows"],
            "okx_active_seconds": len(okx_secs),
            "bybit_active_seconds": len(bybit_secs),
            "joint_coactive_seconds": len(joint_secs),
            "joint_coactive_share_of_day": len(joint_secs) / TOTAL_SECONDS,
            "joint_active_seconds_per_hour": hourly,
            "okx_active_hours": len(okx_hours),
            "bybit_active_hours": len(bybit_hours),
            "joint_active_hours": len(joint_hours),
            "minimum_joint_active_seconds_in_hour": min(hourly),
            "median_last_event_skew_ms": (
                p50_skew / 1000.0 if p50_skew is not None else None
            ),
            "p99_last_event_skew_ms": (
                p99_skew / 1000.0 if p99_skew is not None else None
            ),
            "gates": gates,
            "failed_gates": [k for k, v in gates.items() if not v],
            "historical_trade_bodies_opened": True,
            "cross_venue_price_compared": False,
            "cross_venue_return_calculated": False,
            "dislocation_calculated": False,
            "lag_calculated": False,
            "leader_selected": False,
            "strategy_signal_calculated": False,
            "pnl_calculated": False,
            "promotional_alpha_accessed": False,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        atomic_json(OUT, report)

        print(status)
        print("okx_active_seconds =", len(okx_secs))
        print("bybit_active_seconds =", len(bybit_secs))
        print("joint_coactive_seconds =", len(joint_secs))
        print("joint_coactive_share_of_day =", report["joint_coactive_share_of_day"])
        print("minimum_joint_active_seconds_in_hour =", min(hourly))
        print("median_last_event_skew_ms =", report["median_last_event_skew_ms"])
        print("p99_last_event_skew_ms =", report["p99_last_event_skew_ms"])
        print("failed_gates =", report["failed_gates"])
        print("cross-venue price/return/dislocation/lag = False")
        print("leader/signal/PnL = False")
        print("promotional alpha accessed = False")
        print("report =", OUT)

        return 0 if status == PASS else 2

    except Exception as exc:
        print(REVIEW)
        print("error =", f"{type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
