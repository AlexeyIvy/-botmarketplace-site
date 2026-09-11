"""SC001-DATA-A001 — Binance USD-M BTCUSDT 1m DEV backbone acquisition.

No strategy/P&L. DEV only. Official monthly archives + official checksums.
Android/Pydroid, standard library only.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import shutil
import zipfile
from calendar import monthrange
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

STAGE = "SC001-DATA-A001"
VERSION = "0.1"

SYMBOL = "BTCUSDT"
INTERVAL = "1m"
START_MONTH = (2023, 4)
END_MONTH = (2024, 6)

SESSION_DOWNLOAD_CAP_BYTES = 2_000_000_000
WORKSPACE_CAP_BYTES = 2_000_000_000
PER_FILE_CAP_BYTES = 100_000_000
CHECKSUM_RESPONSE_CAP_BYTES = 1_000_000
MINIMUM_FREE_RESERVE_BYTES = 4_000_000_000
MIN_MONTH_COVERAGE = 0.995

WORKSPACE = Path("/storage/emulated/0/Download/SC001_DATA_A001_BINANCE_DEV_1M")
ARCHIVES = WORKSPACE / "archives"

BASE = (
    "https://data.binance.vision/data/futures/um/monthly/klines/"
    f"{SYMBOL}/{INTERVAL}"
)

QUALIFICATION_ONLY_DATES = {
    "2023-04-15",
    "2024-01-15",
    "2025-01-15",
    "2026-07-15",
}

network_bytes_read = 0


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, obj) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    os.replace(tmp, path)


def dir_size(path: Path) -> int:
    total = 0
    if not path.exists():
        return 0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except FileNotFoundError:
                pass
    return total


def free_bytes(path: Path) -> int:
    return shutil.disk_usage(path).free


def safety_check(extra_workspace_bytes: int = 0) -> None:
    if network_bytes_read > SESSION_DOWNLOAD_CAP_BYTES:
        raise RuntimeError("Session network cap exceeded")
    w = dir_size(WORKSPACE) + max(0, extra_workspace_bytes)
    if w > WORKSPACE_CAP_BYTES:
        raise RuntimeError("Workspace cap exceeded")
    if free_bytes(WORKSPACE) - max(0, extra_workspace_bytes) < MINIMUM_FREE_RESERVE_BYTES:
        raise RuntimeError("Minimum free-storage reserve would be violated")


def months_between(start, end):
    y, m = start
    ey, em = end
    while (y, m) <= (ey, em):
        yield y, m
        m += 1
        if m == 13:
            y += 1
            m = 1


def month_bounds_ms(year: int, month: int):
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    days = monthrange(year, month)[1]
    if month == 12:
        next_month = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        next_month = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    start_ms = int(start.timestamp() * 1000)
    end_exclusive_ms = int(next_month.timestamp() * 1000)
    expected_rows = days * 24 * 60
    return start_ms, end_exclusive_ms, expected_rows


def request_bytes(url: str, cap: int) -> bytes:
    global network_bytes_read
    req = Request(
        url,
        headers={"User-Agent": "BotMarketplace-SC001-DATA-A001/0.1"},
    )
    with urlopen(req, timeout=90) as resp:
        raw = resp.read(cap + 1)
    if len(raw) > cap:
        raise RuntimeError(f"Response exceeded cap: {url}")
    network_bytes_read += len(raw)
    safety_check()
    return raw


def parse_checksum(raw: bytes, expected_filename: str) -> str:
    text = raw.decode("utf-8", errors="strict").strip()
    candidates = []
    for line in text.splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        sha = parts[0].lower()
        filename = parts[-1].lstrip("*")
        if len(sha) == 64 and all(c in "0123456789abcdef" for c in sha):
            candidates.append((sha, filename))
    exact = [sha for sha, fn in candidates if fn == expected_filename]
    if len(exact) == 1:
        return exact[0]
    if len(candidates) == 1:
        return candidates[0][0]
    raise RuntimeError(
        f"Could not resolve unique checksum for {expected_filename}: {candidates[:5]}"
    )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def download_archive(url: str, dest: Path, expected_sha: str) -> dict:
    global network_bytes_read
    if dest.exists():
        size = dest.stat().st_size
        if size <= PER_FILE_CAP_BYTES and sha256_file(dest) == expected_sha:
            return {
                "status": "REUSED",
                "bytes": size,
                "sha256": expected_sha,
                "network_bytes": 0,
            }
        dest.unlink()

    part = dest.with_suffix(dest.suffix + ".part")
    if part.exists():
        part.unlink()

    req = Request(
        url,
        headers={"User-Agent": "BotMarketplace-SC001-DATA-A001/0.1"},
    )
    read_this = 0
    h = hashlib.sha256()
    try:
        with urlopen(req, timeout=120) as resp, part.open("wb") as out:
            cl = resp.headers.get("Content-Length")
            if cl:
                declared = int(cl)
                if declared > PER_FILE_CAP_BYTES:
                    raise RuntimeError(
                        f"Archive declared size {declared} > per-file cap {PER_FILE_CAP_BYTES}"
                    )
                safety_check(declared)
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                read_this += len(chunk)
                network_bytes_read += len(chunk)
                if read_this > PER_FILE_CAP_BYTES:
                    raise RuntimeError("Per-file download cap exceeded")
                if network_bytes_read > SESSION_DOWNLOAD_CAP_BYTES:
                    raise RuntimeError("Session network cap exceeded")
                safety_check(len(chunk))
                h.update(chunk)
                out.write(chunk)
            out.flush()
            os.fsync(out.fileno())
        got = h.hexdigest()
        if got != expected_sha:
            raise RuntimeError(
                f"Checksum mismatch for {dest.name}: expected {expected_sha}, got {got}"
            )
        os.replace(part, dest)
        return {
            "status": "DOWNLOADED",
            "bytes": read_this,
            "sha256": got,
            "network_bytes": read_this,
        }
    except Exception:
        if part.exists():
            part.unlink()
        raise


def parse_open_time(cell: str) -> int:
    s = cell.strip()
    if not s:
        raise ValueError("empty open_time")
    x = int(s)
    if x > 10_000_000_000_000:
        raise ValueError(f"unexpected timestamp scale: {x}")
    return x


def validate_month_zip(path: Path, year: int, month: int) -> dict:
    start_ms, end_excl_ms, expected_rows = month_bounds_ms(year, month)
    expected_last = end_excl_ms - 60_000

    with zipfile.ZipFile(path, "r") as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        if len(names) != 1:
            raise RuntimeError(f"Expected one data member, got {names}")
        member = names[0]

        rows = 0
        invalid_rows = 0
        out_of_month = 0
        misaligned = 0
        duplicate_timestamps = 0
        nonmonotonic = 0
        timestamps = set()
        first_ts = None
        last_ts = None
        prev_ts = None
        max_gap_minutes = 0
        gap_minutes_total = 0
        header_skipped = False

        with zf.open(member, "r") as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            reader = csv.reader(text)
            for row in reader:
                if not row:
                    continue
                if len(row) < 12:
                    invalid_rows += 1
                    continue
                try:
                    ts = parse_open_time(row[0])
                except Exception:
                    if rows == 0 and not header_skipped:
                        header_skipped = True
                        continue
                    invalid_rows += 1
                    continue

                rows += 1
                if first_ts is None:
                    first_ts = ts
                last_ts = ts

                if ts < start_ms or ts >= end_excl_ms:
                    out_of_month += 1
                if ts % 60_000 != 0:
                    misaligned += 1
                if ts in timestamps:
                    duplicate_timestamps += 1
                timestamps.add(ts)

                if prev_ts is not None:
                    if ts < prev_ts:
                        nonmonotonic += 1
                    delta = ts - prev_ts
                    if delta > 60_000:
                        missing = max(0, delta // 60_000 - 1)
                        gap_minutes_total += int(missing)
                        max_gap_minutes = max(max_gap_minutes, int(missing))
                prev_ts = ts

    unique_rows = len(timestamps)
    coverage = unique_rows / expected_rows if expected_rows else 0.0
    edge_start_ok = first_ts == start_ms
    edge_end_ok = last_ts == expected_last

    gates = {
        "coverage_ge_99_5pct": coverage >= MIN_MONTH_COVERAGE,
        "duplicates_zero": duplicate_timestamps == 0,
        "nonmonotonic_zero": nonmonotonic == 0,
        "invalid_rows_zero": invalid_rows == 0,
        "out_of_month_zero": out_of_month == 0,
        "minute_alignment": misaligned == 0,
        "first_minute_present": edge_start_ok,
        "last_minute_present": edge_end_ok,
    }
    status = "PASS" if all(gates.values()) else "REVIEW"

    return {
        "status": status,
        "member": member,
        "header_skipped": header_skipped,
        "rows": rows,
        "unique_rows": unique_rows,
        "expected_rows": expected_rows,
        "coverage": coverage,
        "first_ts": first_ts,
        "last_ts": last_ts,
        "expected_first_ts": start_ms,
        "expected_last_ts": expected_last,
        "invalid_rows": invalid_rows,
        "out_of_month": out_of_month,
        "misaligned_timestamps": misaligned,
        "duplicate_timestamps": duplicate_timestamps,
        "nonmonotonic_timestamps": nonmonotonic,
        "gap_minutes_total": gap_minutes_total,
        "max_gap_minutes": max_gap_minutes,
        "gates": gates,
    }


def iso_minute(ms: int | None) -> str | None:
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()


def main() -> None:
    global network_bytes_read

    WORKSPACE.mkdir(parents=True, exist_ok=True)
    ARCHIVES.mkdir(parents=True, exist_ok=True)
    safety_check()

    report = {
        "stage": STAGE,
        "version": VERSION,
        "started_at_utc": utc_now(),
        "strategy_pnl_calculated": False,
        "scope": {
            "venue": "Binance USD-M Futures",
            "symbol": SYMBOL,
            "interval": INTERVAL,
            "split": "DEV_ONLY",
            "start_month": f"{START_MONTH[0]:04d}-{START_MONTH[1]:02d}",
            "end_month": f"{END_MONTH[0]:04d}-{END_MONTH[1]:02d}",
            "qualification_only_dates_to_exclude_from_future_performance": sorted(
                QUALIFICATION_ONLY_DATES
            ),
        },
        "safety": {
            "session_download_cap_bytes": SESSION_DOWNLOAD_CAP_BYTES,
            "workspace_cap_bytes": WORKSPACE_CAP_BYTES,
            "per_file_cap_bytes": PER_FILE_CAP_BYTES,
            "minimum_free_reserve_bytes": MINIMUM_FREE_RESERVE_BYTES,
            "free_bytes_start": free_bytes(WORKSPACE),
        },
        "months": [],
    }

    previous_last = None
    cross_month_discontinuities = []

    try:
        for year, month in months_between(START_MONTH, END_MONTH):
            ym = f"{year:04d}-{month:02d}"
            filename = f"{SYMBOL}-{INTERVAL}-{ym}.zip"
            url = f"{BASE}/{filename}"
            checksum_url = f"{url}.CHECKSUM"

            print(f"[{ym}] checksum...")
            checksum_raw = request_bytes(checksum_url, CHECKSUM_RESPONSE_CAP_BYTES)
            expected_sha = parse_checksum(checksum_raw, filename)

            dest = ARCHIVES / filename
            print(f"[{ym}] archive...")
            dl = download_archive(url, dest, expected_sha)

            print(f"[{ym}] validate...")
            val = validate_month_zip(dest, year, month)
            val["first_iso_utc"] = iso_minute(val["first_ts"])
            val["last_iso_utc"] = iso_minute(val["last_ts"])

            if previous_last is not None and val["first_ts"] is not None:
                if val["first_ts"] != previous_last + 60_000:
                    cross_month_discontinuities.append(
                        {
                            "current_month": ym,
                            "previous_last_ts": previous_last,
                            "current_first_ts": val["first_ts"],
                            "gap_minutes": (
                                (val["first_ts"] - previous_last) // 60_000 - 1
                            ),
                        }
                    )
            previous_last = val["last_ts"]

            row = {
                "month": ym,
                "url": url,
                "checksum_url": checksum_url,
                "expected_sha256": expected_sha,
                "archive": dl,
                "validation": val,
                "status": (
                    "PASS"
                    if dl["sha256"] == expected_sha and val["status"] == "PASS"
                    else "REVIEW"
                ),
            }
            report["months"].append(row)
            atomic_json(WORKSPACE / "sc001_data_a001_report.json", report)
            safety_check()

        report["cross_month_discontinuities"] = cross_month_discontinuities
        report["network_bytes_read"] = network_bytes_read
        report["workspace_bytes_after_archives"] = dir_size(WORKSPACE)
        passed = sum(1 for x in report["months"] if x["status"] == "PASS")
        report["months_passed"] = passed
        report["months_total"] = len(report["months"])
        report["overall_status"] = (
            "PASS"
            if passed == len(report["months"])
            and not cross_month_discontinuities
            else "REVIEW"
        )
        report["finished_at_utc"] = utc_now()

    except Exception as exc:
        report["overall_status"] = "ERROR"
        report["error"] = repr(exc)
        report["network_bytes_read"] = network_bytes_read
        report["finished_at_utc"] = utc_now()
        atomic_json(WORKSPACE / "sc001_data_a001_report.json", report)
        raise
    finally:
        final_safety = {
            "stage": STAGE,
            "network_bytes_read": network_bytes_read,
            "workspace_bytes_after_outputs": dir_size(WORKSPACE),
            "free_bytes_after_outputs": free_bytes(WORKSPACE),
            "caps": {
                "session": SESSION_DOWNLOAD_CAP_BYTES,
                "workspace": WORKSPACE_CAP_BYTES,
                "per_file": PER_FILE_CAP_BYTES,
                "reserve": MINIMUM_FREE_RESERVE_BYTES,
            },
        }
        atomic_json(
            WORKSPACE / "sc001_data_a001_final_safety.json",
            final_safety,
        )

    atomic_json(WORKSPACE / "sc001_data_a001_report.json", report)

    manifest = {
        "stage": STAGE,
        "version": VERSION,
        "overall_status": report["overall_status"],
        "strategy_pnl_calculated": False,
        "archives_retained": True,
        "months": [
            {
                "month": x["month"],
                "filename": Path(x["url"]).name,
                "sha256": x["archive"]["sha256"],
                "bytes": x["archive"]["bytes"],
                "rows": x["validation"]["rows"],
                "expected_rows": x["validation"]["expected_rows"],
                "coverage": x["validation"]["coverage"],
                "first_ts": x["validation"]["first_ts"],
                "last_ts": x["validation"]["last_ts"],
                "status": x["status"],
            }
            for x in report["months"]
        ],
    }
    atomic_json(WORKSPACE / "sc001_data_a001_manifest.json", manifest)

    lines = [
        "# SC001-DATA-A001 — Binance BTCUSDT USD-M 1m DEV Backbone",
        "",
        f"- Overall: `{report['overall_status']}`",
        "- Strategy/P&L calculated: **NO**",
        "- Scope: DEV only, 2023-04 through 2024-06",
        f"- Months passed: {report.get('months_passed', 0)} / {report.get('months_total', 0)}",
        f"- Network bytes read this run: {network_bytes_read:,}",
        f"- Workspace bytes: {dir_size(WORKSPACE):,}",
        f"- Cross-month discontinuities: {len(report.get('cross_month_discontinuities', []))}",
        "",
        "## Month checks",
    ]
    for x in report["months"]:
        v = x["validation"]
        lines.append(
            f"- {x['month']}: **{x['status']}**; "
            f"rows={v['rows']:,}/{v['expected_rows']:,}; "
            f"coverage={v['coverage']:.6%}; "
            f"duplicates={v['duplicate_timestamps']}; "
            f"nonmonotonic={v['nonmonotonic_timestamps']}; "
            f"max_gap_min={v['max_gap_minutes']}"
        )
    lines += [
        "",
        "## Boundary",
        "This stage qualifies and retains official Binance monthly 1m archives for the DEV split.",
        "Validation and FINAL minute-level data remain unopened by this stage.",
        "Qualification-only dates may exist inside raw monthly archives but are frozen for exclusion from future performance evaluation.",
    ]
    (WORKSPACE / "sc001_data_a001_summary.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    final_safety = {
        "stage": STAGE,
        "network_bytes_read": network_bytes_read,
        "workspace_bytes_after_outputs": dir_size(WORKSPACE),
        "free_bytes_after_outputs": free_bytes(WORKSPACE),
        "caps": {
            "session": SESSION_DOWNLOAD_CAP_BYTES,
            "workspace": WORKSPACE_CAP_BYTES,
            "per_file": PER_FILE_CAP_BYTES,
            "reserve": MINIMUM_FREE_RESERVE_BYTES,
        },
    }
    atomic_json(
        WORKSPACE / "sc001_data_a001_final_safety.json",
        final_safety,
    )

    print("=" * 78)
    print("SC001-DATA-A001 complete")
    print("Overall:", report["overall_status"])
    print("Workspace:", WORKSPACE)
    print("No strategy/P&L calculated.")
    print("=" * 78)


if __name__ == "__main__":
    main()
