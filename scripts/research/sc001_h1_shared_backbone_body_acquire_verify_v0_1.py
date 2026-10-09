#!/usr/bin/env python3
"""Acquire and verify the frozen SC001 H1 Binance USD-M 1m shared bodyset.

Repository preparation only. Network use is impossible unless all of these are
explicitly supplied by a later authorized run:
  * --apply
  * --ack-resource-id with the frozen RESOURCE_ID
  * SC001_NETWORK_PROFILE=public_research
  * SC001_DATA_ROOT pointing at the shared data root

The implementation reads timestamps and schema for integrity only. It computes
no returns, signals, alpha, PnL, or strategy outcomes.
"""

from __future__ import annotations

import argparse
import calendar
import csv
import hashlib
import io
import json
import math
import os
import re
from pathlib import Path, PurePosixPath
import shutil
import sys
import time
from typing import Iterable, Mapping, Sequence
import urllib.error
import urllib.request
import zipfile


PUBLIC_PREFIX = "https://data.binance.vision/"
EXPECTED_SYMBOLS = (
    "0GUSDT",
    "1000000BOBUSDT",
    "1000000MOGUSDT",
    "1000BONKUSDT",
    "1000CATUSDT",
    "1000CHEEMSUSDT",
    "1000FLOKIUSDT",
    "1000LUNCUSDT",
    "1000PEPEUSDT",
    "1000RATSUSDT",
    "1000SATSUSDT",
    "1000SHIBUSDT",
)
EXPECTED_MONTHS = (
    "2025-09", "2025-10", "2025-11", "2025-12",
    "2026-01", "2026-02", "2026-03", "2026-04",
    "2026-05", "2026-06", "2026-07", "2026-08", "2026-09",
)
EXPECTED_HEADER = (
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_volume", "count", "taker_buy_volume",
    "taker_buy_quote_volume", "ignore",
)
DATASET_KEY: dict[str, object] = {
    "source_provider": "Binance",
    "source_host": "data.binance.vision",
    "endpoint_class": "public archive objects",
    "market_type": "USD-M futures",
    "instrument_or_frozen_universe_identifier": {
        "kind": "ordered_symbol_list",
        "symbols": list(EXPECTED_SYMBOLS),
    },
    "data_kind": "kline",
    "granularity": "1m",
    "archive_class": "monthly ZIP plus SHA256 checksum sidecar",
    "UTC_start": "2025-09-01T00:00:00Z",
    "UTC_end_exclusive": "2026-10-01T00:00:00Z",
    "exact_source_identity_rule": (
        "data/futures/um/monthly/klines/{symbol}/1m/"
        "{symbol}-1m-{YYYY-MM}.zip and exact .CHECKSUM sidecar basename"
    ),
    "source_semantic_version": (
        "Binance public data monthly USD-M kline archive schema v1"
    ),
}


def canonical_dataset_key_bytes(dataset_key: Mapping[str, object]) -> bytes:
    return json.dumps(
        dataset_key,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def resource_id_for(dataset_key: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_dataset_key_bytes(dataset_key)).hexdigest()


RESOURCE_ID = resource_id_for(DATASET_KEY)
CHUNK_BYTES = 1024 * 1024


def cache_relative_path(source_basename: str) -> Path:
    if not source_basename or Path(source_basename).name != source_basename:
        raise ContractError("source basename must not contain path components")
    return Path("_raw_cache") / "binance" / RESOURCE_ID / source_basename


class ContractError(RuntimeError):
    """The frozen contract is invalid or a resource gate failed."""


class BudgetExceeded(ContractError):
    """A prospective request, byte, object, or disk budget was exceeded."""


class IntegrityFailure(ContractError):
    """Body integrity failed with an exact machine-readable report."""

    def __init__(
        self,
        archive_id: str,
        code: str,
        *,
        day_utc: str | None = None,
        detail: str = "",
    ) -> None:
        self.report = {
            "archive_id": archive_id,
            "day_utc": day_utc,
            "code": code,
            "detail": detail,
        }
        super().__init__(json.dumps(self.report, sort_keys=True))


class Budget:
    def __init__(self, max_requests: int, max_bytes: int) -> None:
        if max_requests < 0 or max_bytes < 0:
            raise ValueError("budgets must be non-negative")
        self.max_requests = max_requests
        self.max_bytes = max_bytes
        self.requests = 0
        self.bytes = 0

    def consume_request(self) -> None:
        if self.requests + 1 > self.max_requests:
            raise BudgetExceeded("request budget exhausted")
        self.requests += 1

    def consume_bytes(self, count: int) -> None:
        if count < 0 or self.bytes + count > self.max_bytes:
            raise BudgetExceeded("network byte budget exhausted")
        self.bytes += count


def load_and_validate_freeze(path: Path) -> dict:
    freeze = json.loads(path.read_text(encoding="utf-8"))
    frozen_key = freeze.get("dataset_key")
    if not isinstance(frozen_key, Mapping):
        raise ContractError("DATASET_KEY must be a structured mapping")
    if frozen_key != DATASET_KEY:
        raise ContractError("DATASET_KEY mismatch")
    computed_resource_id = resource_id_for(frozen_key)
    if computed_resource_id != RESOURCE_ID:
        raise ContractError("implementation RESOURCE_ID recomputation mismatch")
    if freeze.get("resource_id") != computed_resource_id:
        raise ContractError("freeze RESOURCE_ID is not SHA256(canonical DATASET_KEY)")
    if tuple(freeze.get("frozen_universe", ())) != EXPECTED_SYMBOLS:
        raise ContractError("frozen universe mismatch")
    interval = freeze.get("frozen_interval", {})
    if tuple(interval.get("months", ())) != EXPECTED_MONTHS:
        raise ContractError("frozen month sequence mismatch")
    if interval.get("start_utc") != "2025-09-01T00:00:00Z":
        raise ContractError("frozen start mismatch")
    if interval.get("end_exclusive_utc") != "2026-10-01T00:00:00Z":
        raise ContractError("frozen end mismatch")
    if interval.get("timestamp_unit") != "milliseconds":
        raise ContractError("timestamp unit mismatch")
    manifest = freeze.get("ordered_archive_manifest", ())
    if len(manifest) != 156:
        raise ContractError("manifest must contain exactly 156 archives")
    expected_pairs = [(symbol, month) for symbol in EXPECTED_SYMBOLS for month in EXPECTED_MONTHS]
    actual_pairs = [(item.get("symbol"), item.get("month_utc")) for item in manifest]
    if actual_pairs != expected_pairs:
        raise ContractError("manifest ordering or membership mismatch")
    if [item.get("ordinal") for item in manifest] != list(range(1, 157)):
        raise ContractError("manifest ordinals mismatch")
    for item in manifest:
        symbol = item["symbol"]
        month = item["month_utc"]
        stem = f"{symbol}-1m-{month}"
        relative = f"data/futures/um/monthly/klines/{symbol}/1m/{stem}.zip"
        if item.get("archive_id") != stem or item.get("csv_member") != f"{stem}.csv":
            raise ContractError(f"archive identity mismatch: {stem}")
        archive = item.get("archive", {})
        sidecar = item.get("checksum_sidecar", {})
        if archive.get("url") != PUBLIC_PREFIX + relative:
            raise ContractError(f"archive URL mismatch: {stem}")
        if sidecar.get("url") != PUBLIC_PREFIX + relative + ".CHECKSUM":
            raise ContractError(f"checksum URL mismatch: {stem}")
        expected_archive_cache = cache_relative_path(f"{stem}.zip").as_posix()
        expected_sidecar_cache = cache_relative_path(f"{stem}.zip.CHECKSUM").as_posix()
        if archive.get("cache_relative_path") != expected_archive_cache:
            raise ContractError(f"RESOURCE_ID-bound archive cache mismatch: {stem}")
        if sidecar.get("cache_relative_path") != expected_sidecar_cache:
            raise ContractError(f"RESOURCE_ID-bound sidecar cache mismatch: {stem}")
    return freeze


def parse_checksum_sidecar(text: str, expected_filename: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) != 1:
        raise ContractError("checksum sidecar must contain exactly one non-empty line")
    parts = lines[0].split()
    if len(parts) != 2:
        raise ContractError("checksum sidecar must be '<sha256> <filename>'")
    digest, identity = parts
    identity = identity.lstrip("*")
    if identity != expected_filename:
        raise ContractError(
            f"checksum identity mismatch: expected {expected_filename}, got {identity}"
        )
    if len(digest) != 64 or any(ch not in "0123456789abcdefABCDEF" for ch in digest):
        raise ContractError("checksum is not a SHA-256 hex digest")
    return digest.lower()


def _content_range_start(content_range: str | None) -> int | None:
    if content_range is None:
        return None
    match = re.fullmatch(r"bytes (\\d+)-(\\d+)/(\\d+|\\*)", content_range.strip())
    if match is None:
        return None
    start, end = (int(value) for value in match.group(1, 2))
    if end < start:
        return None
    total = match.group(3)
    if total != "*" and end >= int(total):
        return None
    return start


def validate_resume_response(existing_bytes: int, status: int, content_range: str | None) -> str:
    range_start = _content_range_start(content_range)
    if existing_bytes == 0:
        if status == 200:
            return "wb"
        if status == 206 and range_start == 0:
            return "wb"
        raise ContractError(
            "initial response must be HTTP 200 or HTTP 206 with Content-Range starting at byte 0"
        )
    if status != 206 or range_start != existing_bytes:
        raise ContractError(
            "resume response mismatch; refusing restart or append to the frozen .part"
        )
    return "ab"

def _month_bounds_ms(month: str) -> tuple[int, int]:
    import datetime as dt

    year, month_number = (int(value) for value in month.split("-"))
    start = dt.datetime(year, month_number, 1, tzinfo=dt.timezone.utc)
    if month_number == 12:
        end = dt.datetime(year + 1, 1, 1, tzinfo=dt.timezone.utc)
    else:
        end = dt.datetime(year, month_number + 1, 1, tzinfo=dt.timezone.utc)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)


def _day_utc(timestamp_ms: int) -> str:
    import datetime as dt

    return dt.datetime.fromtimestamp(timestamp_ms / 1000, tz=dt.timezone.utc).date().isoformat()


def validate_timestamp_sequence(
    open_times_ms: Iterable[int],
    start_ms: int,
    end_exclusive_ms: int,
    archive_id: str,
) -> int:
    expected_rows = (end_exclusive_ms - start_ms) // 60_000
    previous: int | None = None
    count = 0
    day_counts: dict[str, int] = {}
    for current in open_times_ms:
        day = _day_utc(current)
        if previous is None:
            if current != start_ms:
                raise IntegrityFailure(
                    archive_id, "MONTH_START_MISMATCH", day_utc=day,
                    detail=f"expected {start_ms}, got {current}",
                )
        else:
            if current == previous:
                raise IntegrityFailure(
                    archive_id, "DUPLICATE_OPEN_TIME", day_utc=day,
                    detail=f"duplicate {current}",
                )
            if current < previous:
                raise IntegrityFailure(
                    archive_id, "NON_MONOTONIC_OPEN_TIME", day_utc=day,
                    detail=f"previous {previous}, got {current}",
                )
            if current - previous != 60_000:
                raise IntegrityFailure(
                    archive_id, "ONE_MINUTE_GAP", day_utc=day,
                    detail=f"previous {previous}, got {current}",
                )
        day_counts[day] = day_counts.get(day, 0) + 1
        previous = current
        count += 1
    if count != expected_rows:
        failing_day = _day_utc(start_ms if previous is None else previous)
        raise IntegrityFailure(
            archive_id, "MONTH_ROW_COUNT_MISMATCH", day_utc=failing_day,
            detail=f"expected {expected_rows}, got {count}",
        )
    if previous is None or previous + 60_000 != end_exclusive_ms:
        failing_day = _day_utc(start_ms if previous is None else previous)
        raise IntegrityFailure(
            archive_id, "MONTH_END_MISMATCH", day_utc=failing_day,
            detail=f"expected final+60000={end_exclusive_ms}",
        )
    for day, bars in sorted(day_counts.items()):
        if bars != 1440:
            raise IntegrityFailure(
                archive_id, "UTC_DAY_BAR_COUNT_MISMATCH", day_utc=day,
                detail=f"expected 1440, got {bars}",
            )
    return count


def _safe_single_member(zf: zipfile.ZipFile, expected_member: str, archive_id: str) -> zipfile.ZipInfo:
    infos = zf.infolist()
    if len(infos) != 1:
        raise IntegrityFailure(
            archive_id, "ZIP_MEMBER_COUNT_MISMATCH",
            detail=f"expected 1 member, got {len(infos)}",
        )
    info = infos[0]
    pure = PurePosixPath(info.filename)
    unsafe = (
        info.is_dir()
        or pure.is_absolute()
        or ".." in pure.parts
        or "\\" in info.filename
        or len(pure.parts) != 1
        or info.filename != expected_member
    )
    if unsafe:
        raise IntegrityFailure(
            archive_id, "ZIP_MEMBER_IDENTITY_OR_PATH_UNSAFE",
            detail=f"expected {expected_member}, got {info.filename}",
        )
    return info


def validate_kline_row(
    row: Sequence[str],
    archive_id: str,
    row_number: int,
) -> int:
    if len(row) != len(EXPECTED_HEADER):
        raise IntegrityFailure(
            archive_id,
            "CSV_SCHEMA_COLUMN_COUNT",
            detail=f"data row {row_number}: expected 12, got {len(row)}",
        )

    integer_values: dict[str, int] = {}
    for index, name in ((0, "open_time"), (6, "close_time"), (8, "count")):
        try:
            integer_values[name] = int(row[index])
        except (TypeError, ValueError) as exc:
            raise IntegrityFailure(
                archive_id,
                "INTEGER_FIELD_INVALID",
                detail=f"data row {row_number}: {name}",
            ) from exc

    open_time = integer_values["open_time"]
    day = _day_utc(open_time)
    numeric_values: list[float] = []
    for index, name in enumerate(EXPECTED_HEADER):
        try:
            value = float(row[index])
        except (TypeError, ValueError) as exc:
            raise IntegrityFailure(
                archive_id,
                "NUMERIC_FIELD_INVALID",
                day_utc=day,
                detail=f"data row {row_number}: {name}",
            ) from exc
        if not math.isfinite(value):
            raise IntegrityFailure(
                archive_id,
                "NONFINITE_NUMERIC_FIELD",
                day_utc=day,
                detail=f"data row {row_number}: {name}",
            )
        numeric_values.append(value)

    open_value, high, low, close = numeric_values[1:5]
    if any(value <= 0 for value in (open_value, high, low, close)):
        raise IntegrityFailure(
            archive_id,
            "OHLC_NON_POSITIVE",
            day_utc=day,
            detail=f"data row {row_number}",
        )
    if high < max(open_value, close, low) or low > min(open_value, close, high):
        raise IntegrityFailure(
            archive_id,
            "OHLC_RELATION_INVALID",
            day_utc=day,
            detail=f"data row {row_number}",
        )
    for index, name in (
        (5, "volume"),
        (7, "quote_volume"),
        (9, "taker_buy_volume"),
        (10, "taker_buy_quote_volume"),
    ):
        if numeric_values[index] < 0:
            raise IntegrityFailure(
                archive_id,
                "NEGATIVE_VOLUME",
                day_utc=day,
                detail=f"data row {row_number}: {name}",
            )
    if integer_values["count"] < 0:
        raise IntegrityFailure(
            archive_id,
            "NEGATIVE_TRADE_COUNT",
            day_utc=day,
            detail=f"data row {row_number}",
        )
    if integer_values["close_time"] != open_time + 59_999:
        raise IntegrityFailure(
            archive_id,
            "CLOSE_TIME_MISMATCH",
            day_utc=day,
            detail=(
                f"data row {row_number}: expected {open_time + 59_999}, "
                f"got {integer_values['close_time']}"
            ),
        )
    return open_time


def validate_zip_body(zip_path: Path, entry: Mapping[str, object]) -> dict:
    archive_id = str(entry["archive_id"])
    expected_member = str(entry["csv_member"])
    month = str(entry["month_utc"])
    start_ms, end_ms = _month_bounds_ms(month)
    try:
        zf = zipfile.ZipFile(zip_path, "r")
    except (OSError, zipfile.BadZipFile) as exc:
        raise IntegrityFailure(archive_id, "BAD_ZIP", detail=str(exc)) from exc
    with zf:
        info = _safe_single_member(zf, expected_member, archive_id)
        if info.file_size <= 0:
            raise IntegrityFailure(archive_id, "EMPTY_CSV_MEMBER")
        with zf.open(info, "r") as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            reader = csv.reader(text)
            try:
                first = next(reader)
            except StopIteration as exc:
                raise IntegrityFailure(archive_id, "EMPTY_CSV") from exc
            if tuple(first) == EXPECTED_HEADER:
                rows: Iterable[Sequence[str]] = reader
            else:
                rows = _prepend(first, reader)

            def timestamps() -> Iterable[int]:
                for row_number, row in enumerate(rows, start=1):
                    yield validate_kline_row(row, archive_id, row_number)

            rows_validated = validate_timestamp_sequence(
                timestamps(), start_ms, end_ms, archive_id
            )
    return {
        "archive_id": archive_id,
        "month_utc": month,
        "rows_validated": rows_validated,
        "status": "BODY_INTEGRITY_PASS",
    }


def _prepend(first: Sequence[str], rest: Iterable[Sequence[str]]) -> Iterable[Sequence[str]]:
    yield first
    yield from rest


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def quarantine(path: Path, data_root: Path, reason: Mapping[str, object]) -> Path:
    quarantine_root = data_root / "quarantine" / RESOURCE_ID
    quarantine_root.mkdir(parents=True, exist_ok=True)
    destination = quarantine_root / (path.name + ".quarantine")
    counter = 1
    while destination.exists():
        destination = quarantine_root / (path.name + f".quarantine.{counter}")
        counter += 1
    if path.exists():
        os.replace(path, destination)
    reason_path = destination.with_name(destination.name + ".reason.json")
    reason_path.write_text(json.dumps(dict(reason), sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return destination


def _download_to_part(
    url: str,
    part_path: Path,
    *,
    budget: Budget,
    max_object_bytes: int,
    max_attempts: int,
    timeout_seconds: int,
    backoff_seconds: Sequence[int],
) -> Path:
    if not url.startswith(PUBLIC_PREFIX):
        raise ContractError("non-frozen source URL rejected")
    part_path.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for attempt in range(max_attempts):
        existing = part_path.stat().st_size if part_path.exists() else 0
        if existing > max_object_bytes:
            raise BudgetExceeded(f"existing .part exceeds object cap: {part_path}")
        headers = {"User-Agent": "SC001-H1-bodyset-v0.1"}
        if existing:
            headers["Range"] = f"bytes={existing}-"
        budget.consume_request()
        request = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                status = int(getattr(response, "status", response.getcode()))
                mode = validate_resume_response(
                    existing, status, response.headers.get("Content-Range")
                )
                content_length = response.headers.get("Content-Length")
                if content_length is not None and existing + int(content_length) > max_object_bytes:
                    raise BudgetExceeded(f"object cap exceeded before read: {url}")
                with part_path.open(mode) as output:
                    while True:
                        chunk = response.read(CHUNK_BYTES)
                        if not chunk:
                            break
                        if output.tell() + len(chunk) > max_object_bytes:
                            raise BudgetExceeded(f"object cap exceeded during read: {url}")
                        budget.consume_bytes(len(chunk))
                        output.write(chunk)
                return part_path
        except (urllib.error.URLError, TimeoutError, OSError, ContractError) as exc:
            last_error = exc
            if isinstance(exc, (BudgetExceeded, ContractError)) and not isinstance(
                exc, urllib.error.URLError
            ):
                raise
            if attempt + 1 == max_attempts:
                break
            delay = backoff_seconds[min(attempt, len(backoff_seconds) - 1)]
            time.sleep(delay)
    raise ContractError(f"bounded download attempts exhausted for {url}: {last_error}")


def _check_disk_gate(data_root: Path, minimum_free_bytes: int) -> None:
    data_root.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(data_root).free
    if free < minimum_free_bytes:
        raise BudgetExceeded(
            f"free disk gate failed: need {minimum_free_bytes}, found {free}"
        )


def _read_or_fetch_sidecar(
    entry: Mapping[str, object],
    data_root: Path,
    budget: Budget,
    acquisition: Mapping[str, object],
) -> tuple[Path, str]:
    sidecar = entry["checksum_sidecar"]
    if not isinstance(sidecar, Mapping):
        raise ContractError("checksum sidecar contract malformed")
    final_path = data_root / str(sidecar["cache_relative_path"])
    expected_filename = Path(str(entry["archive"]["cache_relative_path"])).name
    if final_path.exists():
        digest = parse_checksum_sidecar(
            final_path.read_text(encoding="utf-8"), expected_filename
        )
        return final_path, digest
    part_path = final_path.with_name(final_path.name + ".part")
    _download_to_part(
        str(sidecar["url"]),
        part_path,
        budget=budget,
        max_object_bytes=int(sidecar["max_bytes"]),
        max_attempts=int(acquisition["max_attempts_per_object"]),
        timeout_seconds=int(acquisition["request_timeout_seconds"]),
        backoff_seconds=tuple(acquisition["retry_backoff_seconds"]),
    )
    try:
        digest = parse_checksum_sidecar(
            part_path.read_text(encoding="utf-8"), expected_filename
        )
    except Exception as exc:
        quarantine(
            part_path, data_root,
            {"archive_id": entry["archive_id"], "code": "CHECKSUM_IDENTITY_FAILURE", "detail": str(exc)},
        )
        raise
    final_path.parent.mkdir(parents=True, exist_ok=True)
    os.replace(part_path, final_path)
    return final_path, digest


def acquire_and_verify_entry(
    entry: Mapping[str, object],
    data_root: Path,
    budget: Budget,
    acquisition: Mapping[str, object],
) -> dict:
    archive = entry["archive"]
    if not isinstance(archive, Mapping):
        raise ContractError("archive contract malformed")
    _, expected_digest = _read_or_fetch_sidecar(entry, data_root, budget, acquisition)
    final_path = data_root / str(archive["cache_relative_path"])
    candidate = final_path
    if not final_path.exists():
        candidate = final_path.with_name(final_path.name + ".part")
        _download_to_part(
            str(archive["url"]),
            candidate,
            budget=budget,
            max_object_bytes=int(archive["max_bytes"]),
            max_attempts=int(acquisition["max_attempts_per_object"]),
            timeout_seconds=int(acquisition["request_timeout_seconds"]),
            backoff_seconds=tuple(acquisition["retry_backoff_seconds"]),
        )
    actual_digest = sha256_file(candidate)
    if actual_digest != expected_digest:
        destination = quarantine(
            candidate, data_root,
            {
                "archive_id": entry["archive_id"],
                "code": "SHA256_MISMATCH",
                "expected": expected_digest,
                "actual": actual_digest,
            },
        )
        raise IntegrityFailure(
            str(entry["archive_id"]), "SHA256_MISMATCH",
            detail=f"quarantined={destination}",
        )
    try:
        integrity = validate_zip_body(candidate, entry)
    except IntegrityFailure as exc:
        destination = quarantine(candidate, data_root, exc.report)
        exc.report["quarantined"] = str(destination)
        raise
    if candidate != final_path:
        final_path.parent.mkdir(parents=True, exist_ok=True)
        os.replace(candidate, final_path)
    integrity["sha256"] = actual_digest
    integrity["cache_path"] = str(final_path)
    return integrity


def acquire_bodyset(freeze: Mapping[str, object], data_root: Path) -> dict:
    acquisition = freeze["prospective_acquisition_budget"]
    if not isinstance(acquisition, Mapping):
        raise ContractError("acquisition budget malformed")
    _check_disk_gate(data_root, int(acquisition["minimum_free_disk_bytes_before_start"]))
    budget = Budget(
        int(acquisition["max_requests"]),
        int(acquisition["max_network_bytes"]),
    )
    results = []
    for entry in freeze["ordered_archive_manifest"]:
        results.append(acquire_and_verify_entry(entry, data_root, budget, acquisition))
    if len(results) != 156:
        raise ContractError("fail closed: full frozen bodyset was not accepted")
    return {
        "schema": "sc001.h1_shared_backbone_bodyset_acquisition_receipt.v0.1",
        "dataset_key": DATASET_KEY,
        "resource_id": RESOURCE_ID,
        "status": "FULL_BODYSET_INTEGRITY_PASS",
        "accepted_archives": len(results),
        "requests": budget.requests,
        "network_bytes": budget.bytes,
        "results": results,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--freeze",
        type=Path,
        default=Path("docs/research/sc001-h1-shared-backbone-bodyset-freeze-v0.1.json"),
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--ack-resource-id")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    freeze = load_and_validate_freeze(args.freeze)
    if not args.apply:
        print(json.dumps({
            "status": "PLAN_ONLY_NO_NETWORK",
            "dataset_key": DATASET_KEY,
            "resource_id": RESOURCE_ID,
            "archive_count": 156,
        }, sort_keys=True))
        return 0
    if args.ack_resource_id != RESOURCE_ID:
        raise ContractError("exact --ack-resource-id is required")
    if os.environ.get("SC001_NETWORK_PROFILE") != "public_research":
        raise ContractError("SC001_NETWORK_PROFILE must equal public_research")
    root_value = os.environ.get("SC001_DATA_ROOT")
    if not root_value:
        raise ContractError("SC001_DATA_ROOT is required")
    data_root = Path(root_value).expanduser().resolve()
    receipt = acquire_bodyset(freeze, data_root)
    receipt_path = data_root / "receipts" / (RESOURCE_ID + ".json")
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = receipt_path.with_name(receipt_path.name + ".part")
    temporary.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, receipt_path)
    print(json.dumps({
        "status": receipt["status"],
        "receipt_path": str(receipt_path),
        "accepted_archives": receipt["accepted_archives"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
