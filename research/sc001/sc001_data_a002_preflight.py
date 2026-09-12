"""SC001-DATA-A002-PREFLIGHT — Binance USD-M BTCUSDT aggTrades DEV preflight.

No strategy/P&L. No aggTrades archives downloaded.
Reads the frozen local micro-calendar manifest and checks only official checksum
files plus archive metadata (HEAD or a one-byte Range fallback).
Android/Pydroid, standard library only.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

STAGE = "SC001-DATA-A002-PREFLIGHT"
VERSION = "0.1"
SYMBOL = "BTCUSDT"
SPLIT = "DEV"
EXPECTED_DEV_DAYS = 25
FROZEN_CALENDAR_SHA256 = "e6bd2ddfee7d1ea8fbac89f9ae1aa3e038bbac83e0d624c98af14588bf0cbb7b"
CALENDAR_MANIFEST = Path("/storage/emulated/0/Download/SC001_MICRO_CALENDAR_V0_1/sc001_micro_calendar_manifest_v0_1.json")
WORKSPACE = Path("/storage/emulated/0/Download/SC001_DATA_A002_PREFLIGHT")
BASE = f"https://data.binance.vision/data/futures/um/daily/aggTrades/{SYMBOL}"
SESSION_NETWORK_CAP_BYTES = 50_000_000
WORKSPACE_CAP_BYTES = 50_000_000
PER_RESPONSE_CAP_BYTES = 1_000_000
MINIMUM_FREE_RESERVE_BYTES = 4_000_000_000
LATER_SINGLE_ARCHIVE_CAP_BYTES = 256_000_000
LATER_QUARTER_BATCH_CAP_BYTES = 1_000_000_000
LATER_SESSION_DOWNLOAD_CAP_BYTES = 2_000_000_000
network_bytes_read = 0


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def dir_size(path):
    if not path.exists():
        return 0
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def free_bytes(path):
    return shutil.disk_usage(path).free


def safety_check():
    if network_bytes_read > SESSION_NETWORK_CAP_BYTES:
        raise RuntimeError("Preflight network cap exceeded")
    if dir_size(WORKSPACE) > WORKSPACE_CAP_BYTES:
        raise RuntimeError("Preflight workspace cap exceeded")
    if free_bytes(WORKSPACE) < MINIMUM_FREE_RESERVE_BYTES:
        raise RuntimeError("Minimum free-storage reserve violated")


def atomic_json(path, obj):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def request_small(url):
    global network_bytes_read
    req = Request(url, headers={"User-Agent": "BotMarketplace-SC001-DATA-A002-PREFLIGHT/0.1", "Accept-Encoding": "identity"})
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(PER_RESPONSE_CAP_BYTES + 1)
        meta = {"http_status": getattr(resp, "status", None), "final_url": resp.geturl(), "bytes_read": len(raw)}
    if len(raw) > PER_RESPONSE_CAP_BYTES:
        raise RuntimeError(f"Response exceeded cap: {url}")
    network_bytes_read += len(raw)
    safety_check()
    return raw, meta


def parse_checksum(raw, expected_filename):
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
    raise RuntimeError(f"Could not resolve unique checksum for {expected_filename}: {candidates[:5]}")


def metadata_probe(url):
    global network_bytes_read
    head_error = None
    try:
        req = Request(url, method="HEAD", headers={"User-Agent": "BotMarketplace-SC001-DATA-A002-PREFLIGHT/0.1", "Accept-Encoding": "identity"})
        with urlopen(req, timeout=60) as resp:
            headers = dict(resp.headers.items())
            status = getattr(resp, "status", None)
            final_url = resp.geturl()
        cl = headers.get("Content-Length")
        if cl is not None:
            return {"status": "PASS", "method": "HEAD", "http_status": status, "final_url": final_url,
                    "content_length": int(cl), "etag": headers.get("ETag"),
                    "last_modified": headers.get("Last-Modified"), "content_type": headers.get("Content-Type"),
                    "body_bytes_read": 0}
        head_error = "HEAD returned no Content-Length"
    except Exception as exc:
        head_error = repr(exc)

    req = Request(url, headers={"User-Agent": "BotMarketplace-SC001-DATA-A002-PREFLIGHT/0.1", "Accept-Encoding": "identity", "Range": "bytes=0-0"})
    with urlopen(req, timeout=60) as resp:
        status = getattr(resp, "status", None)
        headers = dict(resp.headers.items())
        final_url = resp.geturl()
        if status != 206:
            cl = headers.get("Content-Length")
            return {"status": "REVIEW", "method": "RANGE_FALLBACK", "http_status": status,
                    "final_url": final_url, "content_length": int(cl) if cl and cl.isdigit() else None,
                    "content_range": headers.get("Content-Range"), "body_bytes_read": 0,
                    "head_error": head_error, "reason": "Range ignored; body intentionally not read"}
        raw = resp.read(2)
        if len(raw) > 1:
            raise RuntimeError("Range response exceeded one-byte body expectation")
        network_bytes_read += len(raw)
        safety_check()
    cr = headers.get("Content-Range", "")
    total = None
    if "/" in cr:
        tail = cr.rsplit("/", 1)[1].strip()
        if tail.isdigit():
            total = int(tail)
    return {"status": "PASS" if total is not None else "REVIEW", "method": "RANGE_FALLBACK",
            "http_status": status, "final_url": final_url, "content_length": total, "content_range": cr,
            "etag": headers.get("ETag"), "last_modified": headers.get("Last-Modified"),
            "content_type": headers.get("Content-Type"), "body_bytes_read": len(raw), "head_error": head_error}


def load_frozen_dev_dates():
    if not CALENDAR_MANIFEST.exists():
        raise RuntimeError(f"Frozen calendar manifest not found: {CALENDAR_MANIFEST}")
    got_sha = sha256_file(CALENDAR_MANIFEST)
    if got_sha != FROZEN_CALENDAR_SHA256:
        raise RuntimeError(f"Frozen calendar manifest SHA256 mismatch: expected {FROZEN_CALENDAR_SHA256}, got {got_sha}")
    manifest = json.loads(CALENDAR_MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("stage") != "SC001-MICRO-CALENDAR-v0.1" or manifest.get("status") != "PASS":
        raise RuntimeError("Frozen calendar stage/status mismatch")
    rows = [x for x in manifest.get("selected_samples", []) if x.get("split") == SPLIT]
    if len(rows) != EXPECTED_DEV_DAYS:
        raise RuntimeError(f"Expected {EXPECTED_DEV_DAYS} DEV rows, found {len(rows)}")
    dates = [x.get("date") for x in rows]
    if len(set(dates)) != EXPECTED_DEV_DAYS or any(not d for d in dates):
        raise RuntimeError("DEV date list is missing/duplicated")
    return sorted(rows, key=lambda x: x["date"])


def main():
    global network_bytes_read
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    safety_check()
    dev_rows = load_frozen_dev_dates()
    report = {"stage": STAGE, "version": VERSION, "started_at_utc": utc_now(),
              "strategy_pnl_calculated": False, "archive_bodies_downloaded": False,
              "scope": {"venue": "Binance USD-M Futures", "symbol": SYMBOL, "dataset": "aggTrades",
                        "split": "DEV_ONLY", "dev_days_expected": EXPECTED_DEV_DAYS,
                        "frozen_calendar_sha256": FROZEN_CALENDAR_SHA256},
              "safety": {"preflight_network_cap_bytes": SESSION_NETWORK_CAP_BYTES,
                         "preflight_workspace_cap_bytes": WORKSPACE_CAP_BYTES,
                         "preflight_per_response_cap_bytes": PER_RESPONSE_CAP_BYTES,
                         "minimum_free_reserve_bytes": MINIMUM_FREE_RESERVE_BYTES,
                         "later_single_archive_cap_bytes": LATER_SINGLE_ARCHIVE_CAP_BYTES,
                         "later_quarter_batch_cap_bytes": LATER_QUARTER_BATCH_CAP_BYTES,
                         "later_session_download_cap_bytes": LATER_SESSION_DOWNLOAD_CAP_BYTES,
                         "free_bytes_start": free_bytes(WORKSPACE)}, "days": []}
    groups = defaultdict(list)
    try:
        for row in dev_rows:
            date = row["date"]
            quarter = row.get("quarter")
            if not quarter:
                raise RuntimeError(f"Missing quarter for {date}")
            filename = f"{SYMBOL}-aggTrades-{date}.zip"
            url = f"{BASE}/{filename}"
            checksum_url = f"{url}.CHECKSUM"
            print(f"[{date}] checksum...")
            checksum_raw, checksum_meta = request_small(checksum_url)
            expected_sha = parse_checksum(checksum_raw, filename)
            print(f"[{date}] metadata...")
            meta = metadata_probe(url)
            size = meta.get("content_length")
            single_cap_ok = isinstance(size, int) and 0 < size <= LATER_SINGLE_ARCHIVE_CAP_BYTES
            status = "PASS" if meta.get("status") == "PASS" and single_cap_ok and len(expected_sha) == 64 else "REVIEW"
            out = {"date": date, "quarter": quarter, "sample_type": row.get("sample_type"),
                   "event_class": row.get("event_class"), "filename": filename, "url": url,
                   "checksum_url": checksum_url, "expected_sha256": expected_sha,
                   "checksum_response": checksum_meta, "archive_metadata": meta,
                   "later_single_archive_cap_ok": single_cap_ok, "status": status}
            report["days"].append(out)
            groups[quarter].append(out)
            atomic_json(WORKSPACE / "sc001_data_a002_preflight_report.json", report)

        batch_plan = []
        for quarter in sorted(groups):
            items = sorted(groups[quarter], key=lambda x: x["date"])
            sizes = [x["archive_metadata"].get("content_length") for x in items]
            known = all(isinstance(x, int) and x > 0 for x in sizes)
            total = sum(sizes) if known else None
            batch_plan.append({"batch_id": quarter, "dates": [x["date"] for x in items],
                               "sample_types": [x.get("event_class") or x.get("sample_type") for x in items],
                               "files": [x["filename"] for x in items], "expected_compressed_bytes": total,
                               "file_count": len(items),
                               "later_quarter_batch_cap_ok": known and total <= LATER_QUARTER_BATCH_CAP_BYTES,
                               "all_days_pass": all(x["status"] == "PASS" for x in items)})
        all_sizes = [x["archive_metadata"].get("content_length") for x in report["days"]]
        total_known = all(isinstance(x, int) and x > 0 for x in all_sizes)
        grand_total = sum(all_sizes) if total_known else None
        report["batch_plan"] = batch_plan
        report["total_expected_compressed_bytes_all_dev"] = grand_total
        report["network_bytes_read"] = network_bytes_read
        report["days_passed"] = sum(1 for x in report["days"] if x["status"] == "PASS")
        report["days_total"] = len(report["days"])
        all_batches_safe = all(b["all_days_pass"] and b["later_quarter_batch_cap_ok"] and b["file_count"] == 5 for b in batch_plan)
        report["overall_status"] = "PASS" if report["days_passed"] == EXPECTED_DEV_DAYS and all_batches_safe and len(batch_plan) == 5 and total_known else "REVIEW"
        report["finished_at_utc"] = utc_now()
        atomic_json(WORKSPACE / "sc001_data_a002_preflight_report.json", report)
        atomic_json(WORKSPACE / "sc001_data_a002_preflight_batch_plan.json",
                    {"stage": STAGE, "frozen_calendar_sha256": FROZEN_CALENDAR_SHA256,
                     "batches": batch_plan, "total_expected_compressed_bytes_all_dev": grand_total,
                     "overall_status": report["overall_status"]})
        lines = ["# SC001-DATA-A002-PREFLIGHT", "", f"- Overall: `{report['overall_status']}`",
                 "- Strategy/P&L calculated: **NO**", "- aggTrades archive bodies downloaded: **NO**",
                 f"- DEV dates checked: {report['days_passed']} / {report['days_total']}",
                 f"- Frozen calendar SHA256: `{FROZEN_CALENDAR_SHA256}`",
                 f"- Expected compressed bytes, all DEV: {grand_total}",
                 f"- Network bytes actually read: {network_bytes_read}", "", "## Quarter batches"]
        for b in batch_plan:
            lines.append(f"- {b['batch_id']}: files={b['file_count']}; bytes={b['expected_compressed_bytes']}; cap_ok={b['later_quarter_batch_cap_ok']}; all_days_pass={b['all_days_pass']}")
        lines += ["", "## Boundary", "PASS authorizes a later staged download only. It does not authorize strategy/P&L, VALIDATION/FINAL access, or raw-trade/L2 substitution."]
        (WORKSPACE / "sc001_data_a002_preflight_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        atomic_json(WORKSPACE / "sc001_data_a002_preflight_final_safety.json",
                    {"stage": STAGE, "network_bytes_read": network_bytes_read,
                     "workspace_bytes_after_outputs": dir_size(WORKSPACE),
                     "free_bytes_after_outputs": free_bytes(WORKSPACE),
                     "caps": {"preflight_network": SESSION_NETWORK_CAP_BYTES,
                              "preflight_workspace": WORKSPACE_CAP_BYTES,
                              "preflight_per_response": PER_RESPONSE_CAP_BYTES,
                              "reserve": MINIMUM_FREE_RESERVE_BYTES,
                              "later_single_archive": LATER_SINGLE_ARCHIVE_CAP_BYTES,
                              "later_quarter_batch": LATER_QUARTER_BATCH_CAP_BYTES,
                              "later_session": LATER_SESSION_DOWNLOAD_CAP_BYTES}})
        print("Overall:", report["overall_status"])
        print("Expected compressed bytes, all DEV:", grand_total)
        print("Output:", WORKSPACE)
    except Exception as exc:
        report["overall_status"] = "ERROR"
        report["error"] = repr(exc)
        report["network_bytes_read"] = network_bytes_read
        report["finished_at_utc"] = utc_now()
        atomic_json(WORKSPACE / "sc001_data_a002_preflight_report.json", report)
        raise


if __name__ == "__main__":
    main()
