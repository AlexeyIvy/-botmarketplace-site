"""SC001-DATA-Q008 — full-day OKX L2 replay pilot.

Data engineering only. One fixed 2024-01-05 archive. No E002 feature,
midquote response, execution P&L, Q2, Validation or Final access.
Android/Pydroid compatible; standard library only.
"""
from __future__ import annotations

import bisect
import hashlib
import json
import math
import os
import shutil
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

STAGE = "SC001-DATA-Q008-OKX-L2-FULL-DAY-PILOT"
VERSION = "0.1"
PROTOCOL_COMMIT = "ada4a6d2ef95fca1bb40f37553d6d630afa00579"
PARENT_STAGE = "SC001-DATA-Q007-OKX-L2-Q1-PREFLIGHT"
PILOT_DATE = "2024-01-05"
EXPECTED_FILENAME = "BTC-USDT-SWAP-L2orderbook-400lv-2024-01-05.tar.gz"
EXPECTED_BYTES = 500_060_536
EXPECTED_INST = "BTC-USDT-SWAP"

DOWNLOAD = Path("/storage/emulated/0/Download")
PARENT_REPORT = DOWNLOAD / "SC001_DATA_Q007_OKX_L2_Q1_PREFLIGHT" / "sc001_data_q007_okx_l2_q1_preflight_report.json"
WORKSPACE = DOWNLOAD / "SC001_DATA_Q008_OKX_L2_PILOT"
ARCHIVE = WORKSPACE / EXPECTED_FILENAME
REPORT = WORKSPACE / "sc001_data_q008_okx_l2_pilot_report.json"
SUMMARY = WORKSPACE / "sc001_data_q008_okx_l2_pilot_summary.md"
SAFETY = WORKSPACE / "sc001_data_q008_okx_l2_pilot_final_safety.json"

SESSION_DOWNLOAD_CAP_BYTES = 700_000_000
WORKSPACE_CAP_BYTES = 700_000_000
PER_FILE_CAP_BYTES = 650_000_000
MIN_FREE_RESERVE_BYTES = 4_000_000_000
MAX_LINE_BYTES = 5_000_000
TRUSTED_HOST = "static.okx.com"
USER_AGENT = "BotMarketplace-SC001-Q008/0.1"
REFERER = "https://www.okx.com/historical-data"
TIMEOUT = 120

network_bytes_read = 0


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def free_bytes() -> int:
    return shutil.disk_usage(DOWNLOAD).free


def safety_check(extra_workspace: int = 0, extra_network: int = 0):
    if network_bytes_read + max(0, extra_network) > SESSION_DOWNLOAD_CAP_BYTES:
        raise RuntimeError("Q008 session network cap would be exceeded")
    if dir_size(WORKSPACE) + max(0, extra_workspace) > WORKSPACE_CAP_BYTES:
        raise RuntimeError("Q008 workspace cap would be exceeded")
    if free_bytes() - max(0, extra_workspace) < MIN_FREE_RESERVE_BYTES:
        raise RuntimeError("Q008 free-space reserve would be violated")


def atomic_json(path: Path, obj):
    raw = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True, default=str).encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("wb") as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


def atomic_text(path: Path, text: str):
    raw = text.encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("wb") as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


def valid_url(url: str) -> bool:
    p = urlparse(url)
    return p.scheme == "https" and (p.hostname or "").lower() == TRUSTED_HOST and Path(p.path).name == EXPECTED_FILENAME


def verify_parent():
    if not PARENT_REPORT.exists():
        raise RuntimeError(f"missing Q007 report: {PARENT_REPORT}")
    obj = json.loads(PARENT_REPORT.read_text(encoding="utf-8"))
    if obj.get("stage") != PARENT_STAGE or obj.get("overall_status") != "PASS":
        raise RuntimeError("Q007 parent is not PASS")
    if obj.get("archive_bodies_downloaded") is not False:
        raise RuntimeError("Q007 archive-body boundary mismatch")
    if obj.get("q2_okx_accessed") is not False or obj.get("validation_or_final_accessed") is not False:
        raise RuntimeError("Q007 firewall mismatch")
    row = next((x for x in (obj.get("dates") or []) if x.get("date") == PILOT_DATE), None)
    if row is None or row.get("status") != "PASS":
        raise RuntimeError("Q007 pilot date missing/non-PASS")
    if row.get("filename") != EXPECTED_FILENAME:
        raise RuntimeError("Q007 pilot filename mismatch")
    head = row.get("head") or {}
    if head.get("content_length") != EXPECTED_BYTES:
        raise RuntimeError("Q007 pilot size mismatch")
    url = str(row.get("url") or "")
    if not valid_url(url):
        raise RuntimeError("Q007 pilot URL not trusted/exact")
    return {"path": str(PARENT_REPORT), "url": url, "bytes": EXPECTED_BYTES, "filename": EXPECTED_FILENAME}


def head_remote(url: str):
    req = Request(url, method="HEAD", headers={"User-Agent": USER_AGENT, "Referer": REFERER})
    with urlopen(req, timeout=TIMEOUT) as resp:
        final = resp.geturl()
        cl = resp.headers.get("Content-Length")
        size = int(cl) if cl and cl.isdigit() else None
        ok = int(getattr(resp, "status", 200)) == 200 and valid_url(final) and size == EXPECTED_BYTES
        return {"status": "PASS" if ok else "REVIEW", "http_status": int(getattr(resp, "status", 200)), "final_url": final, "content_length": size, "content_type": resp.headers.get("Content-Type")}


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_resumable(url: str):
    global network_bytes_read
    if EXPECTED_BYTES > PER_FILE_CAP_BYTES:
        raise RuntimeError("Q008 frozen file exceeds per-file cap")
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    part = ARCHIVE.with_suffix(ARCHIVE.suffix + ".part")
    if ARCHIVE.exists():
        if ARCHIVE.stat().st_size != EXPECTED_BYTES:
            raise RuntimeError("existing final archive has wrong size")
        return {"status": "REUSED", "bytes": EXPECTED_BYTES, "network_bytes": 0, "sha256": hash_file(ARCHIVE)}

    start = part.stat().st_size if part.exists() else 0
    if start < 0 or start > EXPECTED_BYTES:
        part.unlink(missing_ok=True); start = 0
    remaining = EXPECTED_BYTES - start
    safety_check(extra_workspace=remaining, extra_network=remaining)

    headers = {"User-Agent": USER_AGENT, "Referer": REFERER}
    if start:
        headers["Range"] = f"bytes={start}-"
    req = Request(url, headers=headers)
    mode = "ab" if start else "wb"
    with urlopen(req, timeout=TIMEOUT) as resp, part.open(mode) as out:
        status = int(getattr(resp, "status", 200))
        if start:
            if status != 206:
                raise RuntimeError("server did not honor resume Range")
            cr = resp.headers.get("Content-Range", "")
            if not cr.startswith(f"bytes {start}-"):
                raise RuntimeError("unexpected Content-Range on resume")
        else:
            if status != 200:
                raise RuntimeError("unexpected initial GET status")
        if not valid_url(resp.geturl()):
            raise RuntimeError("Q008 download URL identity changed")
        got = start
        next_print = ((got // 50_000_000) + 1) * 50_000_000
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            got += len(chunk)
            network_bytes_read += len(chunk)
            if got > EXPECTED_BYTES or network_bytes_read > SESSION_DOWNLOAD_CAP_BYTES:
                raise RuntimeError("Q008 download size/network cap exceeded")
            out.write(chunk)
            if got >= next_print:
                print(f"downloaded {got:,} / {EXPECTED_BYTES:,}")
                next_print += 50_000_000
        out.flush(); os.fsync(out.fileno())
    if part.stat().st_size != EXPECTED_BYTES:
        raise RuntimeError(f"incomplete Q008 archive: {part.stat().st_size} != {EXPECTED_BYTES}")
    os.replace(part, ARCHIVE)
    return {"status": "DOWNLOADED" if start == 0 else "RESUMED", "resumed_from_bytes": start, "bytes": EXPECTED_BYTES, "network_bytes": EXPECTED_BYTES - start, "sha256": hash_file(ARCHIVE)}


def parse_level(x):
    if not isinstance(x, list) or len(x) != 3:
        raise ValueError("level shape")
    px = float(x[0]); sz = float(x[1]); orders_f = float(x[2])
    if not (math.isfinite(px) and math.isfinite(sz) and math.isfinite(orders_f)):
        raise ValueError("nonfinite level")
    orders = int(round(orders_f))
    if px <= 0 or sz < 0 or orders < 0 or abs(orders_f - orders) > 1e-9:
        raise ValueError("invalid level")
    return px, sz, orders


def book_apply(book, prices, levels, stats):
    for px, sz, orders in levels:
        if sz == 0:
            stats["zero_size_deletions"] += 1
            if orders != 0:
                stats["zero_size_nonzero_orders"] += 1
            if px not in book:
                stats["delete_missing_level"] += 1
            else:
                del book[px]
                i = bisect.bisect_left(prices, px)
                if i < len(prices) and prices[i] == px:
                    prices.pop(i)
        else:
            if px not in book:
                bisect.insort(prices, px)
            book[px] = (sz, orders)


def replay_full_archive(path: Path):
    start_ms = int(datetime.fromisoformat(PILOT_DATE).replace(tzinfo=timezone.utc).timestamp() * 1000)
    end_ms = start_ms + 86_400_000
    required = {"instId", "action", "ts", "asks", "bids"}
    stats = {
        "status": "RUNNING", "regular_members": 0, "member_names": [], "member_declared_bytes": [],
        "records_parsed": 0, "invalid_json_lines": 0, "missing_required_keys": 0,
        "wrong_instrument": 0, "invalid_action": 0, "nonmonotonic_timestamps": 0,
        "malformed_levels": 0, "crossed_book_states": 0, "empty_book_states": 0,
        "snapshots": 0, "updates": 0, "resync_snapshots_after_first": 0,
        "zero_size_deletions": 0, "zero_size_nonzero_orders": 0, "delete_missing_level": 0,
        "first_action": None, "first_ts": None, "last_ts": None, "out_of_target_day": 0,
        "minute_buckets_observed": 0, "max_ask_levels": 0, "max_bid_levels": 0,
        "max_interrecord_gap_ms": 0, "uncompressed_line_bytes": 0,
    }
    asks = {}; bids = {}; ask_prices = []; bid_prices = []
    minute_buckets = set(); last_ts = None; first_record = True

    with tarfile.open(path, mode="r|gz") as tf:
        for member in tf:
            if not member.isfile():
                continue
            stats["regular_members"] += 1
            stats["member_names"].append(member.name)
            stats["member_declared_bytes"].append(member.size)
            if stats["regular_members"] > 1:
                # Still consume nothing from unexpected extra data members; verdict will be REVIEW.
                continue
            f = tf.extractfile(member)
            if f is None:
                raise RuntimeError("could not stream regular tar member")
            for raw in f:
                stats["uncompressed_line_bytes"] += len(raw)
                if len(raw) > MAX_LINE_BYTES:
                    stats["invalid_json_lines"] += 1
                    continue
                if not raw.strip():
                    continue
                try:
                    rec = json.loads(raw)
                except Exception:
                    stats["invalid_json_lines"] += 1
                    continue
                if not isinstance(rec, dict):
                    stats["invalid_json_lines"] += 1
                    continue
                stats["records_parsed"] += 1
                if not required.issubset(rec):
                    stats["missing_required_keys"] += 1
                    continue
                if rec.get("instId") != EXPECTED_INST:
                    stats["wrong_instrument"] += 1
                action = rec.get("action")
                if action not in {"snapshot", "update"}:
                    stats["invalid_action"] += 1
                    continue
                try:
                    ts = int(rec.get("ts"))
                except Exception:
                    stats["nonmonotonic_timestamps"] += 1
                    continue
                if stats["first_ts"] is None:
                    stats["first_ts"] = ts
                stats["last_ts"] = ts
                if last_ts is not None:
                    if ts < last_ts:
                        stats["nonmonotonic_timestamps"] += 1
                    else:
                        stats["max_interrecord_gap_ms"] = max(stats["max_interrecord_gap_ms"], ts - last_ts)
                last_ts = ts
                if start_ms <= ts < end_ms:
                    minute_buckets.add((ts - start_ms) // 60_000)
                else:
                    stats["out_of_target_day"] += 1
                if first_record:
                    stats["first_action"] = action; first_record = False
                elif action == "snapshot":
                    stats["resync_snapshots_after_first"] += 1
                asks_raw = rec.get("asks"); bids_raw = rec.get("bids")
                if not isinstance(asks_raw, list) or not isinstance(bids_raw, list):
                    stats["malformed_levels"] += 1; continue
                try:
                    pa = [parse_level(x) for x in asks_raw]
                    pb = [parse_level(x) for x in bids_raw]
                except Exception:
                    stats["malformed_levels"] += 1; continue
                if action == "snapshot":
                    stats["snapshots"] += 1
                    asks.clear(); bids.clear(); ask_prices.clear(); bid_prices.clear()
                else:
                    stats["updates"] += 1
                book_apply(asks, ask_prices, pa, stats)
                book_apply(bids, bid_prices, pb, stats)
                stats["max_ask_levels"] = max(stats["max_ask_levels"], len(ask_prices))
                stats["max_bid_levels"] = max(stats["max_bid_levels"], len(bid_prices))
                if not ask_prices or not bid_prices:
                    stats["empty_book_states"] += 1
                elif bid_prices[-1] >= ask_prices[0]:
                    stats["crossed_book_states"] += 1

    stats["minute_buckets_observed"] = len(minute_buckets)
    stats["first_ts_utc"] = datetime.fromtimestamp(stats["first_ts"] / 1000, tz=timezone.utc).isoformat() if stats["first_ts"] is not None else None
    stats["last_ts_utc"] = datetime.fromtimestamp(stats["last_ts"] / 1000, tz=timezone.utc).isoformat() if stats["last_ts"] is not None else None
    boundary_ok = (
        stats["first_ts"] is not None and stats["last_ts"] is not None
        and start_ms <= stats["first_ts"] < end_ms and start_ms <= stats["last_ts"] < end_ms
        and stats["out_of_target_day"] == 0 and stats["minute_buckets_observed"] == 1440
    )
    replay_ok = (
        stats["regular_members"] == 1 and stats["records_parsed"] > 0
        and stats["first_action"] == "snapshot" and stats["snapshots"] >= 1 and stats["updates"] >= 1
        and stats["invalid_json_lines"] == 0 and stats["missing_required_keys"] == 0
        and stats["wrong_instrument"] == 0 and stats["invalid_action"] == 0
        and stats["nonmonotonic_timestamps"] == 0 and stats["malformed_levels"] == 0
        and stats["crossed_book_states"] == 0 and stats["empty_book_states"] == 0
        and stats["zero_size_nonzero_orders"] == 0 and stats["delete_missing_level"] == 0
    )
    stats["boundary_ok"] = boundary_ok
    stats["replay_ok"] = replay_ok
    stats["status"] = "FULL_DAY_PASS" if replay_ok and boundary_ok else ("BOUNDARY_REVIEW" if replay_ok else "REVIEW")
    return stats


def write_outputs(report):
    atomic_json(REPORT, report)
    r = report.get("replay") or {}
    lines = [
        "# SC001-DATA-Q008 — OKX L2 Full-Day Replay Pilot",
        "",
        f"- Overall: `{report.get('overall_status')}`",
        f"- Pilot date: `{PILOT_DATE}`",
        f"- Archive bytes: {report.get('archive', {}).get('bytes')}",
        f"- Records parsed: {r.get('records_parsed')}",
        f"- Snapshots / updates: {r.get('snapshots')} / {r.get('updates')}",
        f"- First / last UTC: {r.get('first_ts_utc')} / {r.get('last_ts_utc')}",
        f"- UTC minutes: {r.get('minute_buckets_observed')}/1440",
        f"- Out-of-target records: {r.get('out_of_target_day')}",
        f"- Crossed / empty states: {r.get('crossed_book_states')} / {r.get('empty_book_states')}",
        f"- Delete-missing-level: {r.get('delete_missing_level')}",
        "",
        "## Boundary",
        "Data engineering only. No TFI, no midquote-response alpha, no execution P&L, no Q2 OKX, no formal Validation/Final.",
    ]
    atomic_text(SUMMARY, "\n".join(lines) + "\n")
    atomic_json(SAFETY, {
        "stage": STAGE,
        "network_bytes_read": network_bytes_read,
        "workspace_bytes_after_outputs": dir_size(WORKSPACE),
        "free_bytes_after_outputs": free_bytes(),
        "caps": {"session_download": SESSION_DOWNLOAD_CAP_BYTES, "workspace": WORKSPACE_CAP_BYTES, "per_file": PER_FILE_CAP_BYTES, "reserve": MIN_FREE_RESERVE_BYTES},
        "strategy_features_calculated": False,
        "midquote_response_calculated": False,
        "strategy_pnl_calculated": False,
        "execution_profitability_calculated": False,
        "q2_okx_accessed": False,
        "validation_or_final_accessed": False,
    })


def main():
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    safety_check()
    parent = verify_parent()
    report = {
        "stage": STAGE, "version": VERSION, "protocol_commit": PROTOCOL_COMMIT,
        "started_at_utc": now_iso(), "parent": parent,
        "strategy_features_calculated": False, "midquote_response_calculated": False,
        "strategy_pnl_calculated": False, "execution_profitability_calculated": False,
        "q2_okx_accessed": False, "validation_or_final_accessed": False,
    }
    try:
        head = head_remote(parent["url"])
        report["live_head"] = head
        if head.get("status") != "PASS":
            raise RuntimeError("Q008 live HEAD no longer matches frozen Q007 identity")
        print("Downloading/reusing fixed 2024-01-05 L2 archive...")
        archive = download_resumable(parent["url"])
        report["archive"] = archive
        write_outputs(report)
        print("Full streaming semantic replay; this can take a while...")
        replay = replay_full_archive(ARCHIVE)
        report["replay"] = replay
        report["overall_status"] = replay["status"]
        report["finished_at_utc"] = now_iso()
        write_outputs(report)
        print("COMPLETE:", report["overall_status"])
        print("Results:", WORKSPACE)
    except Exception as exc:
        report["overall_status"] = "ERROR"
        report["error"] = repr(exc)
        report["finished_at_utc"] = now_iso()
        write_outputs(report)
        raise


if __name__ == "__main__":
    main()
