"""SC001-DATA-Q004R semantic OKX L2 replay qualification for Android/Pydroid.

Research-only. No strategy/P&L. No full archive download.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import time
import zlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

VERSION = "0.1"
STAGE = "SC001-DATA-Q004R"

DOWNLOAD = Path("/storage/emulated/0/Download")
Q003_REPORT = DOWNLOAD / "SC001_DATA_Q003" / "sc001_data_q003_report.json"
OUTDIR = DOWNLOAD / "SC001_DATA_Q004R"
REPORT = OUTDIR / "sc001_data_q004r_report.json"
SUMMARY = OUTDIR / "sc001_data_q004r_summary.md"
COMPARE = OUTDIR / "sc001_data_q004r_semantic_compare.json"
FINAL_SAFETY = OUTDIR / "sc001_data_q004r_final_safety.json"

FROZEN_DATES = ["2023-04-15", "2024-01-15", "2025-01-15", "2026-07-15"]
RANGE_BYTES = 8 * 1024 * 1024
MAX_DECOMPRESSED_PREFIX_BYTES = 64 * 1024 * 1024
NORMAL_PLANNED_NETWORK_BUDGET = 40 * 1024 * 1024
SESSION_DOWNLOAD_CAP_BYTES = 2_000_000_000
WORKSPACE_CAP_BYTES = 2_000_000_000
MIN_FREE_RESERVE_BYTES = 4_000_000_000
MIN_COMPLETE_RECORDS = 100
TIMEOUT = 90
RETRIES = 3
USER_AGENT = "BotMarketplace-SC001-DATA-Q004R/0.1"
TRUSTED_HOSTS = {"static.okx.com"}

network_bytes_read = 0


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def dir_size(path):
    total = 0
    if not path.exists():
        return 0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except OSError:
                pass
    return total


def free_bytes():
    return shutil.disk_usage(DOWNLOAD).free


def safety_check(extra_bytes=0):
    global network_bytes_read
    if network_bytes_read + extra_bytes > SESSION_DOWNLOAD_CAP_BYTES:
        raise RuntimeError("2 GB session cap would be exceeded")
    if dir_size(OUTDIR) + extra_bytes > WORKSPACE_CAP_BYTES:
        raise RuntimeError("2 GB workspace cap would be exceeded")
    if free_bytes() - extra_bytes < MIN_FREE_RESERVE_BYTES:
        raise RuntimeError("4 GB free-storage reserve protection triggered")


def atomic_text(path, text):
    raw = text.encode("utf-8")
    safety_check(len(raw))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("wb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def atomic_json(path, obj):
    atomic_text(path, json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def validate_url(url):
    p = urlparse(url)
    host = (p.hostname or "").lower()
    return p.scheme == "https" and host in TRUSTED_HOSTS, host


def fetch_range(url):
    global network_bytes_read
    trusted, host = validate_url(url)
    if not trusted:
        return b"", {"status": "FAIL", "reason": "untrusted URL", "host": host}
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            safety_check(RANGE_BYTES)
            req = Request(url, headers={
                "User-Agent": USER_AGENT,
                "Accept": "*/*",
                "Range": f"bytes=0-{RANGE_BYTES - 1}",
                "Referer": "https://www.okx.com/historical-data",
            })
            with urlopen(req, timeout=TIMEOUT) as resp:
                status = int(getattr(resp, "status", 200))
                headers = dict(resp.headers.items())
                final_url = resp.geturl()
                if status != 206:
                    return b"", {
                        "status": "SAFE_SKIP",
                        "reason": "server ignored HTTP Range",
                        "http_status": status,
                        "content_length": headers.get("Content-Length"),
                        "content_range": headers.get("Content-Range"),
                        "final_url": final_url,
                    }
                cr = headers.get("Content-Range", "")
                cl = headers.get("Content-Length", "")
                if not cr.startswith("bytes 0-"):
                    return b"", {"status": "SAFE_SKIP", "reason": "unexpected Content-Range", "content_range": cr}
                if cl and cl.isdigit() and int(cl) > RANGE_BYTES:
                    return b"", {"status": "SAFE_SKIP", "reason": "range response too large", "content_length": cl}
                raw = resp.read(RANGE_BYTES + 1)
            if len(raw) > RANGE_BYTES:
                return b"", {"status": "SAFE_SKIP", "reason": "range body exceeded 8 MiB cap"}
            safety_check(len(raw))
            network_bytes_read += len(raw)
            return raw, {
                "status": "PASS",
                "http_status": status,
                "content_range": cr,
                "content_length": cl,
                "bytes_read": len(raw),
                "final_url": final_url,
                "sha256_prefix": hashlib.sha256(raw).hexdigest(),
            }
        except (HTTPError, URLError, TimeoutError, OSError, RuntimeError) as e:
            last = repr(e)
            if attempt < RETRIES:
                time.sleep(attempt * 2)
    return b"", {"status": "FAIL", "reason": last}


def decompress_gzip_prefix(raw):
    if not raw.startswith(b"\x1f\x8b"):
        return b"", {"status": "FAIL", "reason": "gzip magic not found"}
    try:
        d = zlib.decompressobj(16 + zlib.MAX_WBITS)
        out = d.decompress(raw, MAX_DECOMPRESSED_PREFIX_BYTES + 1)
        if len(out) > MAX_DECOMPRESSED_PREFIX_BYTES:
            out = out[:MAX_DECOMPRESSED_PREFIX_BYTES]
        return out, {"status": "PASS", "bytes_out": len(out), "eof": bool(d.eof)}
    except zlib.error as e:
        return b"", {"status": "FAIL", "reason": repr(e)}


def parse_tar_first_member_prefix(data):
    if len(data) < 512:
        return b"", {"status": "FAIL", "reason": "not enough bytes for tar header"}
    hdr = data[:512]
    name = hdr[:100].split(b"\0", 1)[0].decode("utf-8", errors="replace")
    size_raw = hdr[124:136].split(b"\0", 1)[0].strip() or b"0"
    try:
        declared_size = int(size_raw, 8)
    except ValueError:
        return b"", {"status": "FAIL", "reason": "invalid tar size", "name": name}
    available = max(0, min(declared_size, len(data) - 512))
    return data[512:512 + available], {
        "status": "PASS",
        "name": name,
        "declared_size": declared_size,
        "available_prefix_bytes": available,
        "complete_in_prefix": available >= declared_size,
    }


def as_number(x):
    if isinstance(x, bool):
        raise ValueError("bool is not numeric")
    v = float(x)
    if not math.isfinite(v):
        raise ValueError("non-finite number")
    return v


def parse_level(level):
    if not isinstance(level, list) or len(level) != 3:
        raise ValueError("level must be [price,size,orders]")
    px = as_number(level[0])
    sz = as_number(level[1])
    orders_f = as_number(level[2])
    orders = int(round(orders_f))
    if abs(orders_f - orders) > 1e-9:
        raise ValueError("orders not integer-like")
    if px <= 0 or sz < 0 or orders < 0:
        raise ValueError("invalid level domain")
    return px, sz, orders


def semantic_replay(payload, expected_inst="BTC-USDT-SWAP"):
    text = payload.decode("utf-8", errors="replace")
    lines = text.splitlines()
    if payload and not payload.endswith((b"\n", b"\r")) and lines:
        lines = lines[:-1]

    out = {
        "status": "RUNNING",
        "complete_lines_considered": len(lines),
        "records_parsed": 0,
        "invalid_json_lines": 0,
        "missing_required_keys": 0,
        "wrong_instrument": 0,
        "invalid_action": 0,
        "nonmonotonic_timestamps": 0,
        "malformed_levels": 0,
        "crossed_book_states": 0,
        "empty_book_states": 0,
        "snapshots": 0,
        "updates": 0,
        "zero_size_deletions": 0,
        "zero_size_nonzero_orders": 0,
        "delete_missing_level": 0,
        "resync_snapshots_after_first": 0,
        "first_action": None,
        "first_ts": None,
        "last_ts": None,
        "key_sets": [],
        "extra_keys_seen": [],
        "max_ask_levels": 0,
        "max_bid_levels": 0,
        "final_best_ask": None,
        "final_best_bid": None,
    }
    required = {"instId", "action", "ts", "asks", "bids"}
    asks_book, bids_book = {}, {}
    last_ts = None
    first_record = True
    key_sets = set()
    extras = set()

    for line in lines:
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except Exception:
            out["invalid_json_lines"] += 1
            continue
        if not isinstance(rec, dict):
            out["invalid_json_lines"] += 1
            continue
        out["records_parsed"] += 1
        key_sets.add(tuple(sorted(rec.keys())))
        missing = required - set(rec.keys())
        if missing:
            out["missing_required_keys"] += 1
            continue
        extras.update(set(rec.keys()) - required)
        if rec.get("instId") != expected_inst:
            out["wrong_instrument"] += 1
        action = rec.get("action")
        if action not in ("snapshot", "update"):
            out["invalid_action"] += 1
            continue
        try:
            ts = int(rec.get("ts"))
        except Exception:
            out["nonmonotonic_timestamps"] += 1
            continue
        if out["first_ts"] is None:
            out["first_ts"] = ts
        if last_ts is not None and ts < last_ts:
            out["nonmonotonic_timestamps"] += 1
        last_ts = ts
        out["last_ts"] = ts
        if first_record:
            out["first_action"] = action
            first_record = False
        elif action == "snapshot":
            out["resync_snapshots_after_first"] += 1

        asks_raw, bids_raw = rec.get("asks"), rec.get("bids")
        if not isinstance(asks_raw, list) or not isinstance(bids_raw, list):
            out["malformed_levels"] += 1
            continue
        try:
            pa = [parse_level(x) for x in asks_raw]
            pb = [parse_level(x) for x in bids_raw]
        except Exception:
            out["malformed_levels"] += 1
            continue

        if action == "snapshot":
            out["snapshots"] += 1
            asks_book, bids_book = {}, {}
        else:
            out["updates"] += 1

        for book, levels in ((asks_book, pa), (bids_book, pb)):
            for px, sz, orders in levels:
                if sz == 0:
                    out["zero_size_deletions"] += 1
                    if orders != 0:
                        out["zero_size_nonzero_orders"] += 1
                    if px not in book:
                        out["delete_missing_level"] += 1
                    book.pop(px, None)
                else:
                    book[px] = (sz, orders)

        out["max_ask_levels"] = max(out["max_ask_levels"], len(asks_book))
        out["max_bid_levels"] = max(out["max_bid_levels"], len(bids_book))
        if not asks_book or not bids_book:
            out["empty_book_states"] += 1
            continue
        if max(bids_book) >= min(asks_book):
            out["crossed_book_states"] += 1

    out["key_sets"] = [list(x) for x in sorted(key_sets)]
    out["extra_keys_seen"] = sorted(extras)
    if asks_book:
        out["final_best_ask"] = min(asks_book)
    if bids_book:
        out["final_best_bid"] = max(bids_book)

    ok = (
        out["records_parsed"] >= MIN_COMPLETE_RECORDS
        and out["first_action"] == "snapshot"
        and out["invalid_json_lines"] == 0
        and out["missing_required_keys"] == 0
        and out["wrong_instrument"] == 0
        and out["invalid_action"] == 0
        and out["nonmonotonic_timestamps"] == 0
        and out["malformed_levels"] == 0
        and out["crossed_book_states"] == 0
        and out["empty_book_states"] == 0
        and out["snapshots"] >= 1
        and out["updates"] >= 1
    )
    out["status"] = "PASS" if ok else "REVIEW"
    return out


def q003_links(q003):
    found = {}
    for d in q003.get("discoveries", []):
        date = d.get("date")
        links = d.get("links") or []
        if date in FROZEN_DATES and len(links) == 1:
            found[date] = links[0]
    return found


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("SC001-DATA-Q004R — SEMANTIC OKX L2 REPLAY QUALIFICATION v0.1")
    print("No strategy/P&L. No full archive download.")
    print("=" * 78)

    if not Q003_REPORT.exists():
        raise FileNotFoundError(f"Required Q003 report missing: {Q003_REPORT}")
    q003 = json.loads(Q003_REPORT.read_text(encoding="utf-8"))
    links = q003_links(q003)
    samples = []
    started = now_iso()
    free_start = free_bytes()

    for date in FROZEN_DATES:
        print(f"\n[{date}] semantic replay")
        link = links.get(date)
        if not link:
            samples.append({"date": date, "status": "FAIL", "reason": "missing unique Q003 link"})
            continue
        raw, rmeta = fetch_range(str(link.get("url")))
        sample = {"date": date, "link": link, "range": rmeta}
        if rmeta.get("status") != "PASS":
            sample["status"] = "FAIL"
            samples.append(sample)
            continue
        dec, gmeta = decompress_gzip_prefix(raw)
        sample["gzip"] = gmeta
        if gmeta.get("status") != "PASS":
            sample["status"] = "FAIL"
            samples.append(sample)
            continue
        payload, tmeta = parse_tar_first_member_prefix(dec)
        sample["tar"] = tmeta
        if tmeta.get("status") != "PASS":
            sample["status"] = "FAIL"
            samples.append(sample)
            continue
        replay = semantic_replay(payload)
        sample["replay"] = replay
        sample["status"] = replay.get("status")
        samples.append(sample)
        print("  status:", sample["status"], "records:", replay.get("records_parsed"), "crossed:", replay.get("crossed_book_states"))

    passed = [s for s in samples if s.get("status") == "PASS"]
    signatures = []
    for s in passed:
        r = s.get("replay") or {}
        signatures.append({
            "date": s.get("date"),
            "first_action": r.get("first_action"),
            "key_sets": r.get("key_sets"),
            "extra_keys_seen": r.get("extra_keys_seen"),
            "level_shape": 3,
            "instrument": "BTC-USDT-SWAP",
        })
    cores = {
        json.dumps({k: v for k, v in x.items() if k != "date"}, sort_keys=True)
        for x in signatures
    }
    coherent = len(passed) == len(FROZEN_DATES) and len(cores) == 1
    overall = "PASS" if coherent else "NEEDS_REVIEW"

    compare = {
        "stage": STAGE,
        "frozen_dates": FROZEN_DATES,
        "passed_dates": [s.get("date") for s in passed],
        "semantic_signatures": signatures,
        "coherent_semantic_schema": coherent,
        "replay_boundary": "Price-level replay supports spread/depth/imbalance and conservative taker execution; it does not prove exact maker queue position or MBO priority.",
    }
    report = {
        "stage": STAGE,
        "version": VERSION,
        "started_at_utc": started,
        "finished_at_utc": now_iso(),
        "strategy_pnl_calculated": False,
        "full_l2_archive_downloaded": False,
        "frozen_dates": FROZEN_DATES,
        "safety": {
            "range_bytes_per_sample": RANGE_BYTES,
            "max_decompressed_prefix_bytes": MAX_DECOMPRESSED_PREFIX_BYTES,
            "normal_planned_network_budget": NORMAL_PLANNED_NETWORK_BUDGET,
            "session_download_cap_bytes": SESSION_DOWNLOAD_CAP_BYTES,
            "workspace_cap_bytes": WORKSPACE_CAP_BYTES,
            "minimum_free_reserve_bytes": MIN_FREE_RESERVE_BYTES,
            "network_bytes_read": network_bytes_read,
            "free_bytes_start": free_start,
        },
        "samples": samples,
        "compare": compare,
        "overall_status": overall,
    }

    atomic_json(REPORT, report)
    atomic_json(COMPARE, compare)
    lines = [
        "# SC001-DATA-Q004R — Semantic OKX L2 Replay Qualification",
        "",
        f"- Overall: `{overall}`",
        "- Strategy/P&L calculated: **NO**",
        "- Full L2 archive downloaded: **NO**",
        f"- Network bytes read: {network_bytes_read:,}",
        f"- Frozen epochs passed: {len(passed)} / {len(FROZEN_DATES)}",
        f"- Semantic schema coherent: **{coherent}**",
        "",
        "## Epoch replay",
    ]
    for s in samples:
        r = s.get("replay") or {}
        lines.append(
            f"- {s.get('date')}: **{s.get('status')}**; records={r.get('records_parsed')}; snapshots={r.get('snapshots')}; updates={r.get('updates')}; nonmonotonic_ts={r.get('nonmonotonic_timestamps')}; malformed_levels={r.get('malformed_levels')}; crossed={r.get('crossed_book_states')}; empty_book={r.get('empty_book_states')}"
        )
    lines += [
        "",
        "## Boundary",
        "PASS means deterministic price-level replay on the frozen sampled prefixes. It does not prove exact maker queue position, MBO priority, or profitability.",
    ]
    atomic_text(SUMMARY, "\n".join(lines) + "\n")
    atomic_json(FINAL_SAFETY, {
        "stage": STAGE,
        "network_bytes_read": network_bytes_read,
        "workspace_bytes_after_outputs": dir_size(OUTDIR),
        "free_bytes_after_outputs": free_bytes(),
        "caps": {
            "session": SESSION_DOWNLOAD_CAP_BYTES,
            "workspace": WORKSPACE_CAP_BYTES,
            "reserve": MIN_FREE_RESERVE_BYTES,
            "range_per_sample": RANGE_BYTES,
            "decompressed_prefix": MAX_DECOMPRESSED_PREFIX_BYTES,
        },
    })

    print("\n" + "=" * 78)
    print("SC001-DATA-Q004R COMPLETE")
    print("Overall:", overall)
    print("Semantic schema coherent:", coherent)
    print("Network bytes read:", f"{network_bytes_read:,}")
    print("Results:", OUTDIR)
    print("Upload these 4 files to ChatGPT:")
    print("1) sc001_data_q004r_report.json")
    print("2) sc001_data_q004r_summary.md")
    print("3) sc001_data_q004r_semantic_compare.json")
    print("4) sc001_data_q004r_final_safety.json")


if __name__ == "__main__":
    main()
