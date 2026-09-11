"""SC001-DATA-Q004 OKX L2 range/schema qualification for Android/Pydroid.

Data-only stage. No strategy/P&L. No full L2 archive download.
Reads Q003-discovered trusted OKX archive URLs and requests only the first 8 MiB
of each archive using HTTP Range, then inspects a bounded decompressed prefix.
"""
from __future__ import annotations

import csv
import io
import json
import os
import shutil
import zlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

VERSION = "0.1"
STAGE = "SC001-DATA-Q004"

DOWNLOAD = Path("/storage/emulated/0/Download")
Q003_REPORT = DOWNLOAD / "SC001_DATA_Q003" / "sc001_data_q003_report.json"
OUTDIR = DOWNLOAD / "SC001_DATA_Q004"
REPORT = OUTDIR / "sc001_data_q004_report.json"
SUMMARY = OUTDIR / "sc001_data_q004_summary.md"
SCHEMA_COMPARE = OUTDIR / "sc001_data_q004_schema_compare.json"
FINAL_SAFETY = OUTDIR / "sc001_data_q004_final_safety.json"

FROZEN_DATES = ["2023-04-15", "2024-01-15", "2025-01-15", "2026-07-15"]
RANGE_BYTES = 8 * 1024 * 1024
MAX_DECOMPRESSED_BYTES = 64 * 1024 * 1024
NORMAL_PLANNED_NETWORK_BUDGET = 40 * 1024 * 1024
SESSION_DOWNLOAD_CAP_BYTES = 2_000_000_000
WORKSPACE_CAP_BYTES = 2_000_000_000
MIN_FREE_RESERVE_BYTES = 4_000_000_000
MAX_TEXT_SAMPLE_BYTES = 2 * 1024 * 1024
MAX_ROWS_PREVIEW = 8
TIMEOUT = 90
USER_AGENT = "BotMarketplace-SC001-DATA-Q004/0.1"
TRUSTED_HOST = "static.okx.com"

network_bytes_read = 0


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def dir_size(path: Path) -> int:
    total = 0
    if path.exists():
        for p in path.rglob("*"):
            if p.is_file():
                try:
                    total += p.stat().st_size
                except OSError:
                    pass
    return total


def free_bytes() -> int:
    return shutil.disk_usage(DOWNLOAD).free


def safety_check(extra_disk: int = 0, extra_network: int = 0):
    if extra_disk < 0 or extra_network < 0:
        raise ValueError("negative safety increment")
    if dir_size(OUTDIR) + extra_disk > WORKSPACE_CAP_BYTES:
        raise RuntimeError("Q004 workspace cap would be exceeded")
    if network_bytes_read + extra_network > SESSION_DOWNLOAD_CAP_BYTES:
        raise RuntimeError("Q004 session network cap would be exceeded")
    if free_bytes() - extra_disk < MIN_FREE_RESERVE_BYTES:
        raise RuntimeError("Q004 free-storage reserve protection triggered")


def atomic_text(path: Path, text: str):
    raw = text.encode("utf-8")
    safety_check(extra_disk=len(raw))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("wb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def atomic_json(path: Path, obj):
    atomic_text(path, json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def trusted_url(url: str) -> bool:
    try:
        u = urlparse(url)
        return u.scheme == "https" and (u.hostname or "").lower() == TRUSTED_HOST
    except Exception:
        return False


def load_q003_links():
    if not Q003_REPORT.exists():
        raise FileNotFoundError(f"Missing Q003 report: {Q003_REPORT}")
    obj = json.loads(Q003_REPORT.read_text(encoding="utf-8"))
    out = {}
    for d in obj.get("discoveries", []):
        date = d.get("date")
        links = d.get("links") or []
        if date not in FROZEN_DATES:
            continue
        good = [x for x in links if trusted_url(str(x.get("url", "")))]
        if len(good) == 1:
            out[date] = good[0]
        else:
            out[date] = {"error": f"expected exactly one trusted link, found {len(good)}"}
    return out


def fetch_range(url: str):
    global network_bytes_read
    if not trusted_url(url):
        return {"status": "UNTRUSTED_URL", "url": url}

    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Referer": "https://www.okx.com/historical-data",
            "Range": f"bytes=0-{RANGE_BYTES - 1}",
            "Accept-Encoding": "identity",
        },
    )
    try:
        with urlopen(req, timeout=TIMEOUT) as resp:
            status = int(getattr(resp, "status", 200))
            final_url = resp.geturl()
            headers = dict(resp.headers.items())
            content_range = headers.get("Content-Range") or headers.get("content-range")
            content_length = headers.get("Content-Length") or headers.get("content-length")

            if not trusted_url(final_url):
                return {"status": "UNTRUSTED_REDIRECT", "http_status": status, "final_url": final_url}

            if status != 206:
                # Critical safety rule: do not consume a 200/full-body response.
                return {
                    "status": "RANGE_UNSUPPORTED",
                    "http_status": status,
                    "content_range": content_range,
                    "content_length": content_length,
                    "final_url": final_url,
                    "bytes_read": 0,
                }

            if not content_range or not content_range.lower().startswith("bytes 0-"):
                return {
                    "status": "BAD_CONTENT_RANGE",
                    "http_status": status,
                    "content_range": content_range,
                    "final_url": final_url,
                    "bytes_read": 0,
                }

            safety_check(extra_network=RANGE_BYTES)
            raw = resp.read(RANGE_BYTES + 1)
            if len(raw) > RANGE_BYTES:
                raise RuntimeError("Range response exceeded frozen 8 MiB body cap")
            network_bytes_read += len(raw)
            return {
                "status": "PASS",
                "http_status": status,
                "content_range": content_range,
                "content_length": content_length,
                "content_type": headers.get("Content-Type") or headers.get("content-type"),
                "final_url": final_url,
                "bytes_read": len(raw),
                "raw": raw,
            }
    except HTTPError as e:
        return {"status": "HTTP_ERROR", "http_status": int(e.code), "reason": str(e)}
    except (URLError, TimeoutError, OSError, RuntimeError) as e:
        return {"status": "ERROR", "reason": repr(e)}


def decompress_gzip_prefix(raw: bytes):
    out = {"status": "FAIL", "bytes_out": 0, "eof": False}
    try:
        dec = zlib.decompressobj(16 + zlib.MAX_WBITS)
        data = dec.decompress(raw, MAX_DECOMPRESSED_BYTES)
        out.update({
            "status": "PASS",
            "bytes_out": len(data),
            "eof": bool(dec.eof),
            "data": data,
        })
    except Exception as e:
        out["reason"] = repr(e)
    return out


def parse_octal(field: bytes):
    s = field.rstrip(b"\0 ").lstrip(b" ")
    if not s:
        return 0
    try:
        return int(s, 8)
    except Exception:
        return None


def inspect_text_prefix(content: bytes):
    sample = content[:MAX_TEXT_SAMPLE_BYTES]
    text = sample.decode("utf-8", errors="replace")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return {"text_detected": False}

    first = lines[0]
    delimiter = None
    for cand in [",", "\t", "|"]:
        if first.count(cand) >= 2:
            delimiter = cand
            break

    out = {
        "text_detected": True,
        "line_count_in_prefix": len(lines),
        "first_line": first[:1000],
        "delimiter": delimiter,
    }
    if delimiter:
        try:
            reader = csv.reader(io.StringIO("\n".join(lines[:MAX_ROWS_PREVIEW + 1])), delimiter=delimiter)
            rows = list(reader)
            if rows:
                out["header_candidate"] = rows[0]
                out["rows_preview"] = rows[1:1 + MAX_ROWS_PREVIEW]
                out["column_count"] = len(rows[0])
        except Exception as e:
            out["csv_parse_error"] = repr(e)
    return out


def inspect_tar_prefix(data: bytes):
    result = {"status": "PASS", "members": [], "text_schemas": []}
    pos = 0
    seen = 0
    while pos + 512 <= len(data) and seen < 16:
        hdr = data[pos:pos + 512]
        if hdr == b"\0" * 512:
            break
        name = hdr[0:100].split(b"\0", 1)[0].decode("utf-8", errors="replace")
        size = parse_octal(hdr[124:136])
        typeflag = hdr[156:157].decode("ascii", errors="replace") or "0"
        if size is None:
            result["status"] = "REVIEW"
            result["reason"] = "unparseable tar size field"
            break
        content_start = pos + 512
        available = max(0, min(size, len(data) - content_start))
        member = {
            "name": name,
            "typeflag": typeflag,
            "declared_size": size,
            "available_prefix_bytes": available,
            "complete_in_prefix": available >= size,
        }
        if available > 0 and typeflag in ("0", "", "x", "g"):
            content = data[content_start:content_start + available]
            text_info = inspect_text_prefix(content)
            member["text"] = text_info
            if text_info.get("header_candidate"):
                result["text_schemas"].append({
                    "member": name,
                    "header": text_info.get("header_candidate"),
                    "column_count": text_info.get("column_count"),
                    "delimiter": text_info.get("delimiter"),
                })
        result["members"].append(member)
        seen += 1
        padded = ((size + 511) // 512) * 512
        next_pos = content_start + padded
        if next_pos <= pos or next_pos > len(data):
            break
        pos = next_pos
    return result


def normalize_header(header):
    return [str(x).strip().lower() for x in (header or [])]


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    safety_check()
    started = now_iso()
    free_start = free_bytes()

    links = load_q003_links()
    samples = []

    print("=" * 78)
    print("SC001-DATA-Q004 OKX L2 RANGE/SCHEMA QUALIFICATION v0.1")
    print("No strategy/P&L. No full archive download.")
    print(f"Range per frozen epoch: {RANGE_BYTES/(1024*1024):.0f} MiB")
    print("=" * 78)

    for date in FROZEN_DATES:
        print("Q004 sample:", date)
        link = links.get(date)
        rec = {"date": date, "link": link}
        if not link or "error" in link:
            rec["status"] = "MISSING_OR_AMBIGUOUS_Q003_LINK"
            samples.append(rec)
            continue

        fr = fetch_range(str(link.get("url")))
        raw = fr.pop("raw", None)
        rec["range"] = fr
        if fr.get("status") != "PASS" or raw is None:
            rec["status"] = fr.get("status", "FAIL")
            samples.append(rec)
            continue

        dec = decompress_gzip_prefix(raw)
        data = dec.pop("data", None)
        rec["gzip"] = dec
        if dec.get("status") != "PASS" or data is None:
            rec["status"] = "DECOMPRESS_FAIL"
            samples.append(rec)
            continue

        tar_info = inspect_tar_prefix(data)
        rec["tar"] = tar_info
        rec["status"] = "PASS" if tar_info.get("text_schemas") else "REVIEW"
        samples.append(rec)

    successful = [x for x in samples if x.get("status") == "PASS"]
    schema_rows = []
    for s in successful:
        schemas = s.get("tar", {}).get("text_schemas") or []
        first = schemas[0] if schemas else None
        schema_rows.append({
            "date": s["date"],
            "member": first.get("member") if first else None,
            "header": first.get("header") if first else None,
            "normalized_header": normalize_header(first.get("header") if first else []),
            "column_count": first.get("column_count") if first else None,
            "delimiter": first.get("delimiter") if first else None,
        })

    header_groups = {}
    for row in schema_rows:
        key = json.dumps(row.get("normalized_header") or [], separators=(",", ":"))
        header_groups.setdefault(key, []).append(row["date"])

    required_dates_ok = {x["date"] for x in successful}
    coherent = len(header_groups) == 1 and len(schema_rows) >= 3
    includes_required = "2025-01-15" in required_dates_ok and "2026-07-15" in required_dates_ok
    overall = "SCHEMA_COMPATIBLE_SCREEN" if coherent and includes_required else "NEEDS_REVIEW"

    schema_compare = {
        "stage": STAGE,
        "frozen_dates": FROZEN_DATES,
        "successful_dates": sorted(required_dates_ok),
        "schema_rows": schema_rows,
        "header_groups": header_groups,
        "coherent_exact_header": coherent,
        "includes_2025_and_2026": includes_required,
        "decision": overall,
    }

    report = {
        "stage": STAGE,
        "version": VERSION,
        "started_at_utc": started,
        "finished_at_utc": now_iso(),
        "strategy_pnl_calculated": False,
        "full_l2_archive_downloaded": False,
        "q003_report": str(Q003_REPORT),
        "frozen_dates": FROZEN_DATES,
        "safety": {
            "range_bytes_per_sample": RANGE_BYTES,
            "max_decompressed_prefix_bytes": MAX_DECOMPRESSED_BYTES,
            "normal_planned_network_budget": NORMAL_PLANNED_NETWORK_BUDGET,
            "session_download_cap_bytes": SESSION_DOWNLOAD_CAP_BYTES,
            "workspace_cap_bytes": WORKSPACE_CAP_BYTES,
            "minimum_free_reserve_bytes": MIN_FREE_RESERVE_BYTES,
            "network_bytes_read": network_bytes_read,
            "free_bytes_start": free_start,
        },
        "samples": samples,
        "schema_compare": schema_compare,
        "overall_status": overall,
    }

    atomic_json(SCHEMA_COMPARE, schema_compare)
    atomic_json(REPORT, report)

    lines = [
        "# SC001-DATA-Q004 — OKX L2 Range/Schema Qualification",
        "",
        f"- Overall: `{overall}`",
        "- Strategy/P&L calculated: **NO**",
        "- Full L2 archive downloaded: **NO**",
        f"- Network bytes actually read: {network_bytes_read:,}",
        f"- Frozen epochs passed: {len(successful)} / {len(FROZEN_DATES)}",
        "",
        "## Epochs",
    ]
    for s in samples:
        schemas = s.get("tar", {}).get("text_schemas") or []
        header = schemas[0].get("header") if schemas else None
        lines.append(f"- {s['date']}: **{s.get('status')}**; header={header}")
    lines += [
        "",
        "## Boundary",
        "Q004 qualifies archive schema only. It does not prove full-day completeness, maker queue position, or profitability.",
    ]
    atomic_text(SUMMARY, "\n".join(lines) + "\n")

    final_safety = {
        "stage": STAGE,
        "network_bytes_read": network_bytes_read,
        "workspace_bytes_after_outputs": dir_size(OUTDIR),
        "free_bytes_after_outputs": free_bytes(),
        "caps": {
            "session": SESSION_DOWNLOAD_CAP_BYTES,
            "workspace": WORKSPACE_CAP_BYTES,
            "reserve": MIN_FREE_RESERVE_BYTES,
            "range_per_sample": RANGE_BYTES,
            "decompressed_prefix": MAX_DECOMPRESSED_BYTES,
        },
    }
    atomic_json(FINAL_SAFETY, final_safety)

    print("\nQ004 COMPLETE")
    print("Overall:", overall)
    print("Network bytes read:", f"{network_bytes_read:,}")
    print("Results:", OUTDIR)
    print("Upload these files:")
    print("1) sc001_data_q004_report.json")
    print("2) sc001_data_q004_summary.md")
    print("3) sc001_data_q004_schema_compare.json")
    print("4) sc001_data_q004_final_safety.json")


if __name__ == "__main__":
    main()
