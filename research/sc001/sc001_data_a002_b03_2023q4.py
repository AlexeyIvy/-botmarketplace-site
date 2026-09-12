"""SC001-DATA-A002-B03 — frozen Binance BTCUSDT aggTrades 2023-Q4.

Data qualification only. No strategy features, no P&L, no VALIDATION/FINAL.
Android/Pydroid; standard library only.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import shutil
import zipfile
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from urllib.request import Request, urlopen

STAGE = "SC001-DATA-A002-B03"
VERSION = "0.1"
BATCH_ID = "2023-Q4"
SYMBOL = "BTCUSDT"
DATASET = "aggTrades"

FROZEN_CALENDAR_SHA256 = "e6bd2ddfee7d1ea8fbac89f9ae1aa3e038bbac83e0d624c98af14588bf0cbb7b"
PREFLIGHT_STAGE = "SC001-DATA-A002-PREFLIGHT"
PREFLIGHT_PATH = Path(
    "/storage/emulated/0/Download/SC001_DATA_A002_PREFLIGHT/"
    "sc001_data_a002_preflight_report.json"
)

WORKSPACE = Path("/storage/emulated/0/Download/SC001_DATA_A002_B03_2023Q4")
ARCHIVES = WORKSPACE / "archives"

SESSION_DOWNLOAD_CAP_BYTES = 200_000_000
WORKSPACE_CAP_BYTES = 200_000_000
PER_FILE_CAP_BYTES = 256_000_000
MINIMUM_FREE_RESERVE_BYTES = 4_000_000_000
MAX_UNCOMPRESSED_MEMBER_BYTES = 2_000_000_000
SMALL_RESPONSE_CAP_BYTES = 1_000_000

EXPECTED_BATCH_COMPRESSED_BYTES = 91_449_749
EXPECTED_DAYS = 5

BASE = (
    "https://data.binance.vision/data/futures/um/daily/aggTrades/"
    f"{SYMBOL}"
)

EXPECTED = [
    (
        "2023-10-06", "EVENT", "NFP", 16_322_789,
        "56203d777eef00b4f2a4b010ab5783c10375c0d12d6379855c518e2f995a0d04",
    ),
    (
        "2023-10-25", "ORDINARY_WEEKDAY", None, 30_292_155,
        "33d1b6cf278277ed96bdc541f0311e9103c0d9bfb8371ac5f6df4a0f62fb617b",
    ),
    (
        "2023-12-03", "ORDINARY_WEEKEND", None, 10_141_775,
        "28e84940fdb14a6aba6e0a92203617f5823414c00066b5578c42240e45f3c0a0",
    ),
    (
        "2023-12-12", "EVENT", "CPI", 16_718_495,
        "4afc4d7355251ad997c5475b348ca54cd4534fc989fce0050fe5262594250690",
    ),
    (
        "2023-12-13", "EVENT", "FOMC", 17_974_535,
        "5390f437ae1afee0e4c17454b1254356a41d5757118bf7de589e50eb74ea48e5",
    ),
]

HEADER = [
    "agg_trade_id",
    "price",
    "quantity",
    "first_trade_id",
    "last_trade_id",
    "transact_time",
    "is_buyer_maker",
]

network_bytes_read = 0


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except FileNotFoundError:
                pass
    return total


def free_bytes(path: Path) -> int:
    return shutil.disk_usage(path).free


def atomic_json(path: Path, obj) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    os.replace(tmp, path)


def safety_check(extra_workspace_bytes: int = 0) -> None:
    extra = max(0, extra_workspace_bytes)
    if network_bytes_read > SESSION_DOWNLOAD_CAP_BYTES:
        raise RuntimeError("session network cap exceeded")
    if dir_size(WORKSPACE) + extra > WORKSPACE_CAP_BYTES:
        raise RuntimeError("workspace cap exceeded")
    if free_bytes(WORKSPACE) - extra < MINIMUM_FREE_RESERVE_BYTES:
        raise RuntimeError("minimum free-space reserve would be violated")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_small(url: str) -> bytes:
    global network_bytes_read
    req = Request(
        url,
        headers={"User-Agent": "BotMarketplace-SC001-A002-B03/0.1"},
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(SMALL_RESPONSE_CAP_BYTES + 1)
        final_url = resp.geturl()
        status = resp.status
    if status != 200 or final_url != url:
        raise RuntimeError(f"small-response identity failure: {url}")
    if len(raw) > SMALL_RESPONSE_CAP_BYTES:
        raise RuntimeError(f"small response cap exceeded: {url}")
    network_bytes_read += len(raw)
    safety_check()
    return raw


def parse_checksum(raw: bytes, expected_filename: str) -> str:
    candidates = []
    for line in raw.decode("utf-8", errors="strict").splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        sha = parts[0].lower()
        fn = parts[-1].lstrip("*")
        if len(sha) == 64 and all(c in "0123456789abcdef" for c in sha):
            candidates.append((sha, fn))
    exact = [sha for sha, fn in candidates if fn == expected_filename]
    if len(exact) == 1:
        return exact[0]
    if len(candidates) == 1:
        return candidates[0][0]
    raise RuntimeError(f"could not resolve checksum for {expected_filename}")


def head_content_length(url: str) -> int:
    req = Request(
        url,
        method="HEAD",
        headers={"User-Agent": "BotMarketplace-SC001-A002-B03/0.1"},
    )
    with urlopen(req, timeout=60) as resp:
        if resp.status != 200 or resp.geturl() != url:
            raise RuntimeError(f"HEAD identity failure: {url}")
        value = resp.headers.get("Content-Length")
    if value is None:
        raise RuntimeError(f"missing Content-Length: {url}")
    return int(value)


def download_archive(url: str, dest: Path, expected_bytes: int, expected_sha: str) -> dict:
    global network_bytes_read

    if expected_bytes > PER_FILE_CAP_BYTES:
        raise RuntimeError("per-file cap exceeded before download")

    if dest.exists():
        if dest.stat().st_size == expected_bytes and sha256_file(dest) == expected_sha:
            return {
                "status": "REUSED",
                "bytes": expected_bytes,
                "sha256": expected_sha,
                "network_bytes": 0,
            }
        dest.unlink()

    part = dest.with_suffix(dest.suffix + ".part")
    if part.exists():
        part.unlink()

    safety_check(expected_bytes)
    got = 0
    h = hashlib.sha256()

    req = Request(
        url,
        headers={"User-Agent": "BotMarketplace-SC001-A002-B03/0.1"},
    )

    try:
        with urlopen(req, timeout=120) as resp, part.open("wb") as out:
            if resp.status != 200 or resp.geturl() != url:
                raise RuntimeError(f"GET identity failure: {url}")
            cl = resp.headers.get("Content-Length")
            if cl is not None and int(cl) != expected_bytes:
                raise RuntimeError("Content-Length changed after preflight")

            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                got += len(chunk)
                network_bytes_read += len(chunk)
                if got > expected_bytes or got > PER_FILE_CAP_BYTES:
                    raise RuntimeError("download size/per-file cap exceeded")
                if network_bytes_read > SESSION_DOWNLOAD_CAP_BYTES:
                    raise RuntimeError("session download cap exceeded")
                h.update(chunk)
                out.write(chunk)

            out.flush()
            os.fsync(out.fileno())

        digest = h.hexdigest()
        if got != expected_bytes:
            raise RuntimeError(f"download size mismatch: got={got}, expected={expected_bytes}")
        if digest != expected_sha:
            raise RuntimeError("download SHA256 mismatch")

        os.replace(part, dest)
        return {
            "status": "DOWNLOADED",
            "bytes": got,
            "sha256": digest,
            "network_bytes": got,
        }
    except Exception:
        if part.exists():
            part.unlink()
        raise


def positive_decimal(text: str) -> Decimal:
    value = Decimal(text.strip())
    if not value.is_finite() or value <= 0:
        raise ValueError("non-positive/non-finite decimal")
    return value


def validate_zip(path: Path, date_text: str) -> dict:
    start = datetime.fromisoformat(date_text).replace(tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    day_lo = int(start.timestamp() * 1000)
    day_hi = int(end.timestamp() * 1000)
    expected_member = f"{SYMBOL}-aggTrades-{date_text}.csv"

    with zipfile.ZipFile(path, "r") as zf:
        bad_crc = zf.testzip()
        if bad_crc is not None:
            raise RuntimeError(f"ZIP CRC failure: {bad_crc}")

        infos = [x for x in zf.infolist() if not x.is_dir()]
        if len(infos) != 1:
            raise RuntimeError(f"expected one data member, got {len(infos)}")
        info = infos[0]
        if Path(info.filename).name != expected_member:
            raise RuntimeError(f"ZIP member mismatch: {info.filename}")
        if info.file_size > MAX_UNCOMPRESSED_MEMBER_BYTES:
            raise RuntimeError("uncompressed member cap exceeded")

        rows = 0
        invalid_rows = 0
        out_of_day = 0
        timestamp_backwards = 0
        same_ms_adjacent = 0
        agg_id_duplicate_or_backwards = 0
        agg_id_gap_count = 0
        underlying_overlap_or_backwards = 0
        underlying_gap_count_diagnostic = 0
        maker_true_rows = 0
        maker_false_rows = 0

        first_agg_id = None
        last_agg_id = None
        first_underlying_id = None
        last_underlying_id = None
        first_ts = None
        last_ts = None

        previous_agg_id = None
        previous_underlying_last = None
        previous_ts = None
        minute_buckets = set()
        header_mode = None
        first_nonempty_seen = False

        with zf.open(info, "r") as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            reader = csv.reader(text)

            for row in reader:
                if not row:
                    continue

                if not first_nonempty_seen:
                    try:
                        int(row[0].strip())
                    except Exception:
                        normalized = [x.strip().lower() for x in row]
                        if normalized != HEADER:
                            raise RuntimeError(f"unexpected CSV header: {row[:10]}")
                        header_mode = "HEADER_PRESENT"
                        first_nonempty_seen = True
                        continue
                    header_mode = "NO_HEADER"
                    first_nonempty_seen = True

                if len(row) != 7:
                    invalid_rows += 1
                    continue

                try:
                    agg_id = int(row[0].strip())
                    positive_decimal(row[1])
                    positive_decimal(row[2])
                    first_trade_id = int(row[3].strip())
                    last_trade_id = int(row[4].strip())
                    ts = int(row[5].strip())
                    maker = row[6].strip().lower()
                    if first_trade_id > last_trade_id:
                        raise ValueError("first_trade_id > last_trade_id")
                    if maker not in {"true", "false"}:
                        raise ValueError("invalid maker flag")
                except Exception:
                    invalid_rows += 1
                    continue

                rows += 1
                if first_agg_id is None:
                    first_agg_id = agg_id
                    first_underlying_id = first_trade_id
                    first_ts = ts
                last_agg_id = agg_id
                last_underlying_id = last_trade_id
                last_ts = ts

                if day_lo <= ts < day_hi:
                    minute_buckets.add((ts - day_lo) // 60_000)
                else:
                    out_of_day += 1

                if previous_ts is not None:
                    if ts < previous_ts:
                        timestamp_backwards += 1
                    elif ts == previous_ts:
                        same_ms_adjacent += 1

                if previous_agg_id is not None:
                    delta = agg_id - previous_agg_id
                    if delta <= 0:
                        agg_id_duplicate_or_backwards += 1
                    elif delta != 1:
                        agg_id_gap_count += 1

                if previous_underlying_last is not None:
                    if first_trade_id <= previous_underlying_last:
                        underlying_overlap_or_backwards += 1
                    elif first_trade_id != previous_underlying_last + 1:
                        underlying_gap_count_diagnostic += 1

                if maker == "true":
                    maker_true_rows += 1
                else:
                    maker_false_rows += 1

                previous_agg_id = agg_id
                previous_underlying_last = last_trade_id
                previous_ts = ts

    gates = {
        "rows_positive": rows > 0,
        "invalid_rows_zero": invalid_rows == 0,
        "all_rows_inside_target_utc_day": out_of_day == 0,
        "timestamps_monotonic_nondecreasing": timestamp_backwards == 0,
        "agg_trade_ids_strict_contiguous": (
            agg_id_duplicate_or_backwards == 0 and agg_id_gap_count == 0
        ),
        "underlying_trade_ranges_nonoverlapping": underlying_overlap_or_backwards == 0,
        "all_1440_minutes_observed": len(minute_buckets) == 1440,
        "both_maker_flags_observed": maker_true_rows > 0 and maker_false_rows > 0,
    }

    status = "PASS" if all(gates.values()) else "REVIEW"

    def iso_ms(ms):
        if ms is None:
            return None
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()

    return {
        "status": status,
        "member": info.filename,
        "compressed_size": info.compress_size,
        "uncompressed_size": info.file_size,
        "header_mode": header_mode,
        "rows": rows,
        "invalid_rows": invalid_rows,
        "out_of_day_rows": out_of_day,
        "timestamp_backwards": timestamp_backwards,
        "same_ms_adjacent": same_ms_adjacent,
        "agg_id_duplicate_or_backwards": agg_id_duplicate_or_backwards,
        "agg_id_gap_count": agg_id_gap_count,
        "underlying_overlap_or_backwards": underlying_overlap_or_backwards,
        "underlying_gap_count_diagnostic": underlying_gap_count_diagnostic,
        "minute_buckets_observed": len(minute_buckets),
        "maker_true_rows": maker_true_rows,
        "maker_false_rows": maker_false_rows,
        "first_agg_trade_id": first_agg_id,
        "last_agg_trade_id": last_agg_id,
        "first_underlying_trade_id": first_underlying_id,
        "last_underlying_trade_id": last_underlying_id,
        "first_ts": first_ts,
        "last_ts": last_ts,
        "first_ts_utc": iso_ms(first_ts),
        "last_ts_utc": iso_ms(last_ts),
        "gates": gates,
    }


def verify_preflight() -> dict:
    if not PREFLIGHT_PATH.exists():
        raise RuntimeError(f"missing preflight report: {PREFLIGHT_PATH}")

    obj = json.loads(PREFLIGHT_PATH.read_text(encoding="utf-8"))
    scope = obj.get("scope") or {}

    if obj.get("stage") != PREFLIGHT_STAGE:
        raise RuntimeError("preflight stage mismatch")
    if obj.get("overall_status") != "PASS":
        raise RuntimeError("preflight is not PASS")
    if obj.get("strategy_pnl_calculated") is not False:
        raise RuntimeError("preflight P&L boundary mismatch")
    if obj.get("archive_bodies_downloaded") is not False:
        raise RuntimeError("preflight body-download boundary mismatch")
    if scope.get("frozen_calendar_sha256") != FROZEN_CALENDAR_SHA256:
        raise RuntimeError("preflight calendar SHA mismatch")
    if scope.get("split") != "DEV_ONLY":
        raise RuntimeError("preflight split mismatch")
    if obj.get("days_total") != 25 or obj.get("days_passed") != 25:
        raise RuntimeError("preflight count mismatch")

    by_date = {x["date"]: x for x in obj.get("days", [])}
    if len(by_date) != 25:
        raise RuntimeError("preflight unique-day mismatch")

    for date_text, _, _, expected_bytes, expected_sha in EXPECTED:
        row = by_date.get(date_text)
        if row is None or row.get("status") != "PASS":
            raise RuntimeError(f"preflight missing/non-PASS day: {date_text}")
        if row.get("expected_sha256") != expected_sha:
            raise RuntimeError(f"preflight SHA identity mismatch: {date_text}")
        live_meta = row.get("archive_metadata") or {}
        if live_meta.get("content_length") != expected_bytes:
            raise RuntimeError(f"preflight size identity mismatch: {date_text}")

    return {
        "path": str(PREFLIGHT_PATH),
        "frozen_calendar_sha256": scope["frozen_calendar_sha256"],
        "days_verified": [x[0] for x in EXPECTED],
    }


def write_outputs(report: dict) -> None:
    atomic_json(WORKSPACE / "sc001_data_a002_b03_report.json", report)

    manifest = {
        "stage": STAGE,
        "version": VERSION,
        "batch_id": BATCH_ID,
        "overall_status": report.get("overall_status"),
        "strategy_pnl_calculated": False,
        "strategy_features_calculated": False,
        "archives_retained": True,
        "files": [],
    }

    for row in report.get("days", []):
        val = row["validation"]
        manifest["files"].append(
            {
                "date": row["date"],
                "sample_type": row["sample_type"],
                "event_class": row["event_class"],
                "filename": row["filename"],
                "bytes": row["archive"]["bytes"],
                "sha256": row["archive"]["sha256"],
                "rows": val["rows"],
                "first_agg_trade_id": val["first_agg_trade_id"],
                "last_agg_trade_id": val["last_agg_trade_id"],
                "first_ts": val["first_ts"],
                "last_ts": val["last_ts"],
                "minute_buckets_observed": val["minute_buckets_observed"],
                "status": row["status"],
            }
        )

    atomic_json(WORKSPACE / "sc001_data_a002_b03_manifest.json", manifest)

    lines = [
        "# SC001-DATA-A002-B03 — Binance BTCUSDT aggTrades 2023-Q4",
        "",
        f"- Overall: `{report.get('overall_status')}`",
        "- Strategy/P&L calculated: **NO**",
        "- Strategy features calculated: **NO**",
        f"- Days passed: {report.get('days_passed', 0)} / {EXPECTED_DAYS}",
        f"- Network bytes read: {report.get('network_bytes_read', 0)}",
        "",
        "## Day checks",
    ]
    for row in report.get("days", []):
        val = row["validation"]
        tag = row["sample_type"]
        if row["event_class"]:
            tag += "/" + row["event_class"]
        lines.append(
            f"- {row['date']} [{tag}]: **{row['status']}**; "
            f"rows={val['rows']}; minutes={val['minute_buckets_observed']}/1440; "
            f"agg_id_gaps={val['agg_id_gap_count']}; "
            f"timestamp_backwards={val['timestamp_backwards']}; "
            f"invalid_rows={val['invalid_rows']}; out_of_day={val['out_of_day_rows']}; "
            f"underlying_gap_diag={val['underlying_gap_count_diagnostic']}"
        )
    lines += [
        "",
        "## Boundary",
        "Data qualification only. No strategy/P&L, no strategy features, no VALIDATION/FINAL, no maker-queue inference, and no L2 execution model.",
        "B03 completes DEV-DISCOVERY acquisition. STOP before B04/B05; next step is hypothesis design/freeze.",
    ]
    (WORKSPACE / "sc001_data_a002_b03_summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    atomic_json(
        WORKSPACE / "sc001_data_a002_b03_final_safety.json",
        {
            "stage": STAGE,
            "network_bytes_read": report.get("network_bytes_read", 0),
            "workspace_bytes_after_outputs": dir_size(WORKSPACE),
            "free_bytes_after_outputs": free_bytes(WORKSPACE),
            "caps": {
                "session_download": SESSION_DOWNLOAD_CAP_BYTES,
                "workspace": WORKSPACE_CAP_BYTES,
                "per_file": PER_FILE_CAP_BYTES,
                "reserve": MINIMUM_FREE_RESERVE_BYTES,
                "max_uncompressed_member": MAX_UNCOMPRESSED_MEMBER_BYTES,
            },
        },
    )


def main() -> None:
    global network_bytes_read

    WORKSPACE.mkdir(parents=True, exist_ok=True)
    ARCHIVES.mkdir(parents=True, exist_ok=True)
    safety_check()
    preflight = verify_preflight()

    report = {
        "stage": STAGE,
        "version": VERSION,
        "batch_id": BATCH_ID,
        "started_at_utc": utc_now(),
        "strategy_pnl_calculated": False,
        "strategy_features_calculated": False,
        "validation_or_final_accessed": False,
        "scope": {
            "venue": "Binance USD-M Futures",
            "symbol": SYMBOL,
            "dataset": DATASET,
            "split": "DEV_DISCOVERY_ONLY",
            "batch": BATCH_ID,
            "dates": [x[0] for x in EXPECTED],
            "frozen_calendar_sha256": FROZEN_CALENDAR_SHA256,
            "expected_compressed_bytes": EXPECTED_BATCH_COMPRESSED_BYTES,
        },
        "preflight_verification": preflight,
        "safety": {
            "session_download_cap_bytes": SESSION_DOWNLOAD_CAP_BYTES,
            "workspace_cap_bytes": WORKSPACE_CAP_BYTES,
            "per_file_cap_bytes": PER_FILE_CAP_BYTES,
            "minimum_free_reserve_bytes": MINIMUM_FREE_RESERVE_BYTES,
            "free_bytes_start": free_bytes(WORKSPACE),
        },
        "days": [],
    }

    previous_selected_last_agg = None
    previous_selected_last_underlying = None
    cross_order_violations = []

    try:
        for date_text, sample_type, event_class, expected_bytes, expected_sha in EXPECTED:
            filename = f"{SYMBOL}-aggTrades-{date_text}.zip"
            url = f"{BASE}/{filename}"
            checksum_url = url + ".CHECKSUM"

            print(f"[{date_text}] live checksum...")
            live_sha = parse_checksum(read_small(checksum_url), filename)
            if live_sha != expected_sha:
                raise RuntimeError(f"live checksum changed: {date_text}")

            print(f"[{date_text}] live HEAD...")
            live_bytes = head_content_length(url)
            if live_bytes != expected_bytes:
                raise RuntimeError(f"live Content-Length changed: {date_text}")

            print(f"[{date_text}] download/reuse...")
            dest = ARCHIVES / filename
            archive = download_archive(url, dest, expected_bytes, expected_sha)

            print(f"[{date_text}] validate...")
            validation = validate_zip(dest, date_text)

            if previous_selected_last_agg is not None:
                if validation["first_agg_trade_id"] <= previous_selected_last_agg:
                    cross_order_violations.append(
                        {
                            "date": date_text,
                            "kind": "agg_trade_id_not_forward",
                            "previous_last": previous_selected_last_agg,
                            "current_first": validation["first_agg_trade_id"],
                        }
                    )
                if validation["first_underlying_trade_id"] <= previous_selected_last_underlying:
                    cross_order_violations.append(
                        {
                            "date": date_text,
                            "kind": "underlying_trade_id_not_forward",
                            "previous_last": previous_selected_last_underlying,
                            "current_first": validation["first_underlying_trade_id"],
                        }
                    )

            previous_selected_last_agg = validation["last_agg_trade_id"]
            previous_selected_last_underlying = validation["last_underlying_trade_id"]

            row_status = (
                "PASS"
                if archive["sha256"] == expected_sha
                and archive["bytes"] == expected_bytes
                and validation["status"] == "PASS"
                else "REVIEW"
            )

            report["days"].append(
                {
                    "date": date_text,
                    "sample_type": sample_type,
                    "event_class": event_class,
                    "filename": filename,
                    "url": url,
                    "checksum_url": checksum_url,
                    "frozen_expected_bytes": expected_bytes,
                    "frozen_expected_sha256": expected_sha,
                    "live_checksum_sha256": live_sha,
                    "live_head_bytes": live_bytes,
                    "archive": archive,
                    "validation": validation,
                    "status": row_status,
                }
            )

            report["days_passed_so_far"] = sum(
                1 for x in report["days"] if x["status"] == "PASS"
            )
            report["network_bytes_read"] = network_bytes_read
            write_outputs(report)
            safety_check()

        report["cross_selected_day_order_violations"] = cross_order_violations
        report["days_total"] = len(report["days"])
        report["days_passed"] = sum(
            1 for x in report["days"] if x["status"] == "PASS"
        )
        report["network_bytes_read"] = network_bytes_read
        report["overall_status"] = (
            "PASS"
            if report["days_total"] == EXPECTED_DAYS
            and report["days_passed"] == EXPECTED_DAYS
            and not cross_order_violations
            else "REVIEW"
        )
        report["finished_at_utc"] = utc_now()
        write_outputs(report)

    except Exception as exc:
        report["overall_status"] = "ERROR"
        report["error"] = repr(exc)
        report["network_bytes_read"] = network_bytes_read
        report["finished_at_utc"] = utc_now()
        write_outputs(report)
        raise

    report["workspace_bytes_after_outputs"] = dir_size(WORKSPACE)
    write_outputs(report)

    print(
        f"COMPLETE: {report['overall_status']} "
        f"{report['days_passed']}/{report['days_total']} | "
        f"network={network_bytes_read} | P&L=NO | FEATURES=NO | STOP_AFTER_B03=YES"
    )


if __name__ == "__main__":
    main()
