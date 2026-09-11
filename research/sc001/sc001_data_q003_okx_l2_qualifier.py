"""SC001-DATA-Q003 optimized OKX L2 qualification for Android/Pydroid.

Data engineering only. No strategy/P&L.
- Multi-date metadata discovery for OKX historical L2.
- Conditional single-day raw download ONLY for fixed 2025-01-15.
- Hard 2 GB session/workspace caps, 512 MB single-file cap, 4 GB free reserve.
- No archive extraction to disk; bounded streaming schema inspection only.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import shutil
import tarfile
import time
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

VERSION = "0.2"
STAGE = "SC001-DATA-Q003"

DOWNLOAD = Path("/storage/emulated/0/Download")
OUTDIR = DOWNLOAD / "SC001_DATA_Q003"
REPORT = OUTDIR / "sc001_data_q003_report.json"
SUMMARY = OUTDIR / "sc001_data_q003_summary.md"
SCHEMA_REPORT = OUTDIR / "sc001_data_q003_schema.json"

DISCOVERY_DATES = ["2023-04-15", "2024-01-15", "2025-01-15", "2026-07-15"]
PRIMARY_DOWNLOAD_DATE = "2025-01-15"
INST_TYPE = "SWAP"
INST_FAMILY = "BTC-USDT"
INST_ID = "BTC-USDT-SWAP"
L2_MODULE = "4"

DOMAINS = ["https://www.okx.com", "https://us.okx.com"]
DISCOVERY_PATH = "/priapi/v5/broker/public/trade-data/download-link"
INSTRUMENT_PATH = "/api/v5/public/instruments"

USER_AGENT = "BotMarketplace-SC001-DATA-Q003/0.2"
REFERER = "https://www.okx.com/historical-data"
TIMEOUT = 90
RETRIES = 3

# Hard safety: decimal bytes, intentionally stricter than GiB.
SESSION_DOWNLOAD_CAP_BYTES = 2_000_000_000
WORKSPACE_CAP_BYTES = 2_000_000_000
PER_FILE_CAP_BYTES = 512_000_000
MIN_FREE_RESERVE_BYTES = 4_000_000_000
MAX_METADATA_RESPONSE_BYTES = 4_000_000
MAX_DECOMPRESSED_INSPECTION_BYTES = 32_000_000
MAX_INSPECTION_LINES = 2_000

ALLOWED_STATIC_HOST_PREFIX = "static.okx."

downloaded_this_run = 0


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def dir_size(path: Path) -> int:
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


def free_bytes() -> int:
    return shutil.disk_usage(DOWNLOAD).free


def safety_check(extra_workspace_bytes: int = 0, extra_download_bytes: int = 0) -> None:
    global downloaded_this_run
    if extra_workspace_bytes < 0 or extra_download_bytes < 0:
        raise ValueError("safety byte increments must be non-negative")

    ws = dir_size(OUTDIR)
    if ws + extra_workspace_bytes > WORKSPACE_CAP_BYTES:
        raise RuntimeError(
            f"Workspace cap would be exceeded: {ws + extra_workspace_bytes:,} > "
            f"{WORKSPACE_CAP_BYTES:,} bytes"
        )

    if downloaded_this_run + extra_download_bytes > SESSION_DOWNLOAD_CAP_BYTES:
        raise RuntimeError(
            f"Session download cap would be exceeded: "
            f"{downloaded_this_run + extra_download_bytes:,} > "
            f"{SESSION_DOWNLOAD_CAP_BYTES:,} bytes"
        )

    free = free_bytes()
    reserve_cost = max(extra_workspace_bytes, extra_download_bytes)
    if free - reserve_cost < MIN_FREE_RESERVE_BYTES:
        raise RuntimeError(
            "Free-space reserve protection triggered: "
            f"free={free:,}, requested={reserve_cost:,}, "
            f"reserve={MIN_FREE_RESERVE_BYTES:,}"
        )


def atomic_text(path: Path, text: str) -> None:
    raw = text.encode("utf-8")
    safety_check(extra_workspace_bytes=len(raw))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("wb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    safety_check()


def atomic_json(path: Path, obj) -> None:
    atomic_text(path, json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def bounded_error_body(e: HTTPError, limit: int = 256_000) -> bytes:
    try:
        return e.read(limit)
    except Exception:
        return b""


def request_json(url: str, method: str = "GET", payload=None) -> tuple[object | None, dict]:
    global downloaded_this_run
    body = None
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json,*/*",
        "Referer": REFERER,
    }
    if payload is not None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"

    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = Request(url, data=body, method=method, headers=headers)
            with urlopen(req, timeout=TIMEOUT) as resp:
                advertised = resp.headers.get("Content-Length")
                if advertised and advertised.isdigit():
                    adv = int(advertised)
                    if adv > MAX_METADATA_RESPONSE_BYTES:
                        raise RuntimeError(
                            f"Metadata response too large: {adv:,} > {MAX_METADATA_RESPONSE_BYTES:,}"
                        )
                    safety_check(extra_download_bytes=adv)
                raw = resp.read(MAX_METADATA_RESPONSE_BYTES + 1)
                status = int(getattr(resp, "status", 200))
                final_url = resp.geturl()
                resp_headers = dict(resp.headers.items())

            if len(raw) > MAX_METADATA_RESPONSE_BYTES:
                raise RuntimeError("Metadata response exceeded cap")
            safety_check(extra_download_bytes=len(raw))
            downloaded_this_run += len(raw)
            text = raw.decode("utf-8", errors="replace")
            meta = {
                "status": status,
                "bytes": len(raw),
                "final_url": final_url,
                "headers": resp_headers,
                "preview": text[:600],
            }
            try:
                obj = json.loads(text)
                meta["json_ok"] = True
                return obj, meta
            except Exception:
                meta["json_ok"] = False
                return None, meta

        except HTTPError as e:
            raw = bounded_error_body(e)
            safety_check(extra_download_bytes=len(raw))
            downloaded_this_run += len(raw)
            text = raw.decode("utf-8", errors="replace")
            obj = None
            try:
                obj = json.loads(text)
            except Exception:
                pass
            return obj, {
                "status": int(e.code),
                "bytes": len(raw),
                "http_error": True,
                "preview": text[:600],
                "json_ok": obj is not None,
            }
        except (URLError, TimeoutError, OSError, RuntimeError) as e:
            last = repr(e)
            if attempt < RETRIES:
                time.sleep(attempt * 2)

    return None, {"status": None, "error": last or "request failed"}


def date_bounds(date_str: str) -> tuple[int, int]:
    d = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    start = int(d.timestamp() * 1000)
    end = int((d + timedelta(days=1) - timedelta(milliseconds=1)).timestamp() * 1000)
    return start, end


def build_discovery_payload(date_str: str) -> dict:
    begin, end = date_bounds(date_str)
    return {
        "module": L2_MODULE,
        "instType": INST_TYPE,
        "instQueryParam": {"instFamilyList": [INST_FAMILY]},
        "dateQuery": {
            "dateAggrType": "daily",
            "begin": str(begin),
            "end": str(end),
        },
    }


def parse_size_mb(value) -> int | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if value < 0:
            return None
        return int(float(value) * 1_000_000)
    s = str(value).strip().replace(",", "")
    try:
        return int(float(s) * 1_000_000)
    except Exception:
        pass
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(kb|mb|gb|b)?", s, re.I)
    if not m:
        return None
    n = float(m.group(1))
    unit = (m.group(2) or "mb").lower()
    mult = {"b": 1, "kb": 1_000, "mb": 1_000_000, "gb": 1_000_000_000}[unit]
    return int(n * mult)


def valid_static_okx_url(url: str) -> tuple[bool, str | None]:
    try:
        p = urlparse(url)
        host = (p.hostname or "").lower()
        ok = p.scheme == "https" and host.startswith(ALLOWED_STATIC_HOST_PREFIX)
        return ok, host
    except Exception:
        return False, None


def extract_links(obj) -> list[dict]:
    out = []
    if not isinstance(obj, dict):
        return out
    data = obj.get("data")
    if not isinstance(data, dict):
        return out
    details = data.get("details")
    if not isinstance(details, list):
        return out
    for detail in details:
        if not isinstance(detail, dict):
            continue
        groups = detail.get("groupDetails")
        if not isinstance(groups, list):
            continue
        for g in groups:
            if not isinstance(g, dict):
                continue
            url = g.get("url")
            filename = g.get("filename") or g.get("fileName")
            size_mb = g.get("sizeMB")
            valid, host = valid_static_okx_url(str(url)) if url else (False, None)
            out.append({
                "filename": filename,
                "url": url,
                "sizeMB_raw": size_mb,
                "reported_bytes": parse_size_mb(size_mb),
                "trusted_url": valid,
                "host": host,
            })
    return out


def discover_for_date(date_str: str) -> dict:
    payload = build_discovery_payload(date_str)
    attempts = []
    for domain in DOMAINS:
        url = domain + DISCOVERY_PATH + "?t=" + str(int(time.time() * 1000))
        obj, meta = request_json(url, method="POST", payload=payload)
        code = obj.get("code") if isinstance(obj, dict) else None
        links = extract_links(obj)
        rec = {
            "domain": domain,
            "url": url,
            "code": code,
            "msg": obj.get("msg") if isinstance(obj, dict) else None,
            "meta": meta,
            "links": links,
        }
        attempts.append(rec)
        if code == "0" and links:
            return {
                "date": date_str,
                "status": "PASS",
                "payload": payload,
                "selected_domain": domain,
                "attempts": attempts,
                "links": links,
            }
        time.sleep(0.6)
    return {
        "date": date_str,
        "status": "NO_LINKS",
        "payload": payload,
        "selected_domain": None,
        "attempts": attempts,
        "links": [],
    }


def instrument_metadata() -> dict:
    attempts = []
    params = urlencode({"instType": INST_TYPE, "instId": INST_ID})
    for domain in DOMAINS:
        url = domain + INSTRUMENT_PATH + "?" + params
        obj, meta = request_json(url)
        code = obj.get("code") if isinstance(obj, dict) else None
        data = obj.get("data") if isinstance(obj, dict) else None
        rec = {"domain": domain, "code": code, "meta": meta}
        attempts.append(rec)
        if code == "0" and isinstance(data, list) and data:
            wanted = {}
            for k in (
                "instId", "instType", "instFamily", "uly", "ctVal", "ctMult", "ctValCcy",
                "settleCcy", "tickSz", "lotSz", "minSz", "state", "listTime", "expTime"
            ):
                if k in data[0]:
                    wanted[k] = data[0].get(k)
            return {"status": "PASS", "domain": domain, "fields": wanted, "attempts": attempts}
    return {"status": "NO_DATA", "attempts": attempts}


def head_remote(url: str) -> dict:
    valid, host = valid_static_okx_url(url)
    if not valid:
        return {"status": "REJECTED_URL", "host": host}
    try:
        req = Request(url, method="HEAD", headers={"User-Agent": USER_AGENT, "Referer": REFERER})
        with urlopen(req, timeout=TIMEOUT) as resp:
            final = resp.geturl()
            final_valid, final_host = valid_static_okx_url(final)
            if not final_valid:
                return {"status": "REJECTED_REDIRECT", "final_url": final, "host": final_host}
            v = resp.headers.get("Content-Length")
            size = int(v) if v and v.isdigit() else None
            return {
                "status": "PASS",
                "http_status": int(getattr(resp, "status", 200)),
                "content_length": size,
                "content_type": resp.headers.get("Content-Type"),
                "final_url": final,
                "host": final_host,
            }
    except HTTPError as e:
        return {"status": "HTTP_ERROR", "http_status": int(e.code)}
    except Exception as e:
        return {"status": "ERROR", "error": repr(e)}


def safe_download(url: str, dest: Path, expected_bytes: int | None) -> dict:
    global downloaded_this_run

    valid, host = valid_static_okx_url(url)
    if not valid:
        return {"status": "SAFE_SKIP", "reason": "untrusted URL", "host": host}

    if expected_bytes is None:
        return {"status": "SAFE_SKIP", "reason": "remote size unknown"}
    if expected_bytes <= 0:
        return {"status": "SAFE_SKIP", "reason": "invalid remote size"}
    if expected_bytes > PER_FILE_CAP_BYTES:
        return {
            "status": "SAFE_SKIP",
            "reason": "file exceeds 512 MB cap",
            "expected_bytes": expected_bytes,
        }

    if dest.exists() and dest.is_file():
        local_size = dest.stat().st_size
        if 0 < local_size <= PER_FILE_CAP_BYTES:
            safety_check()
            return {
                "status": "PASS",
                "reused_local": True,
                "file": str(dest),
                "bytes": local_size,
                "sha256": sha256_file(dest),
                "expected_bytes": expected_bytes,
                "size_match": local_size == expected_bytes,
            }

    safety_check(extra_workspace_bytes=expected_bytes, extra_download_bytes=expected_bytes)
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    if part.exists():
        part.unlink()

    h = hashlib.sha256()
    total = 0
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*", "Referer": REFERER})
        with urlopen(req, timeout=TIMEOUT) as resp:
            final = resp.geturl()
            final_valid, final_host = valid_static_okx_url(final)
            if not final_valid:
                return {"status": "SAFE_SKIP", "reason": "untrusted redirect", "final_url": final}
            advertised = resp.headers.get("Content-Length")
            if advertised and advertised.isdigit():
                adv = int(advertised)
                if adv > PER_FILE_CAP_BYTES:
                    return {"status": "SAFE_SKIP", "reason": "advertised file exceeds cap", "bytes": adv}
                safety_check(extra_workspace_bytes=adv, extra_download_bytes=adv)

            with part.open("wb") as f:
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    next_total = total + len(chunk)
                    if next_total > PER_FILE_CAP_BYTES:
                        raise RuntimeError("stream crossed 512 MB per-file cap")
                    safety_check(
                        extra_workspace_bytes=len(chunk),
                        extra_download_bytes=len(chunk),
                    )
                    f.write(chunk)
                    h.update(chunk)
                    total = next_total
                    downloaded_this_run += len(chunk)
                    if total // (50 * 1024 * 1024) != (total - len(chunk)) // (50 * 1024 * 1024):
                        print(f"    L2 download: {total / (1024*1024):.1f} MB")
                f.flush()
                os.fsync(f.fileno())

        if total == 0:
            raise RuntimeError("empty download")
        size_match = bool(expected_bytes and total == expected_bytes)
        os.replace(part, dest)
        safety_check()
        return {
            "status": "PASS",
            "reused_local": False,
            "file": str(dest),
            "bytes": total,
            "sha256": h.hexdigest(),
            "expected_bytes": expected_bytes,
            "size_match": size_match,
        }
    except Exception as e:
        try:
            if part.exists():
                part.unlink()
        except OSError:
            pass
        return {"status": "FAIL", "error": repr(e), "partial_deleted": True, "bytes_before_fail": total}


def record_view(obj, acc: dict) -> None:
    if isinstance(obj, dict):
        candidates = [obj]
        if isinstance(obj.get("data"), list):
            candidates.extend(x for x in obj["data"] if isinstance(x, dict))
    elif isinstance(obj, list):
        candidates = [x for x in obj if isinstance(x, dict)]
    else:
        candidates = []

    for rec in candidates:
        keys = tuple(sorted(str(k) for k in rec.keys()))
        if len(acc["key_signatures"]) < 20 and keys not in acc["key_signatures"]:
            acc["key_signatures"].append(keys)

        action = rec.get("action")
        if action is not None:
            acc["actions"][str(action)] = acc["actions"].get(str(action), 0) + 1

        for field in ("seqId", "prevSeqId", "checksum"):
            if field in rec:
                acc["sequencing_fields"][field] = True

        if "asks" in rec and isinstance(rec.get("asks"), list):
            acc["asks_records"] += 1
            if rec["asks"] and acc["asks_preview"] is None:
                acc["asks_preview"] = rec["asks"][:2]
        if "bids" in rec and isinstance(rec.get("bids"), list):
            acc["bids_records"] += 1
            if rec["bids"] and acc["bids_preview"] is None:
                acc["bids_preview"] = rec["bids"][:2]

        for tfield in ("ts", "timestamp", "time"):
            if tfield in rec:
                try:
                    ts = int(rec[tfield])
                    acc["timestamp_field_counts"][tfield] = acc["timestamp_field_counts"].get(tfield, 0) + 1
                    acc["min_timestamp"] = ts if acc["min_timestamp"] is None else min(acc["min_timestamp"], ts)
                    acc["max_timestamp"] = ts if acc["max_timestamp"] is None else max(acc["max_timestamp"], ts)
                except Exception:
                    pass


def inspect_text_stream(stream, member_name: str) -> dict:
    acc = {
        "member": member_name,
        "lines_seen": 0,
        "json_ok": 0,
        "json_errors": 0,
        "bytes_decompressed_sampled": 0,
        "key_signatures": [],
        "actions": {},
        "sequencing_fields": {"seqId": False, "prevSeqId": False, "checksum": False},
        "asks_records": 0,
        "bids_records": 0,
        "asks_preview": None,
        "bids_preview": None,
        "timestamp_field_counts": {},
        "min_timestamp": None,
        "max_timestamp": None,
    }

    while acc["lines_seen"] < MAX_INSPECTION_LINES and acc["bytes_decompressed_sampled"] < MAX_DECOMPRESSED_INSPECTION_BYTES:
        line = stream.readline()
        if not line:
            break
        acc["lines_seen"] += 1
        acc["bytes_decompressed_sampled"] += len(line)
        if acc["bytes_decompressed_sampled"] > MAX_DECOMPRESSED_INSPECTION_BYTES:
            break
        try:
            if isinstance(line, bytes):
                text = line.decode("utf-8", errors="replace").strip()
            else:
                text = str(line).strip()
            if not text:
                continue
            obj = json.loads(text)
            acc["json_ok"] += 1
            record_view(obj, acc)
        except Exception:
            acc["json_errors"] += 1
    return acc


def inspect_archive(path: Path) -> dict:
    out = {
        "status": "RUNNING",
        "file": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "archive_type": None,
        "members": [],
        "sample": None,
    }
    lower = path.name.lower()

    try:
        if lower.endswith((".tar.gz", ".tgz")):
            out["archive_type"] = "tar.gz"
            with tarfile.open(path, "r:gz") as tf:
                members = [m for m in tf.getmembers() if m.isfile()]
                out["members"] = [m.name for m in members[:50]]
                if not members:
                    out.update({"status": "FAIL", "reason": "no file members"})
                    return out
                f = tf.extractfile(members[0])
                if f is None:
                    out.update({"status": "FAIL", "reason": "cannot open first member"})
                    return out
                out["sample"] = inspect_text_stream(f, members[0].name)

        elif lower.endswith(".zip"):
            out["archive_type"] = "zip"
            with zipfile.ZipFile(path, "r") as zf:
                bad = zf.testzip()
                if bad is not None:
                    out.update({"status": "FAIL", "reason": f"bad zip member {bad}"})
                    return out
                names = [n for n in zf.namelist() if not n.endswith("/")]
                out["members"] = names[:50]
                if not names:
                    out.update({"status": "FAIL", "reason": "no file members"})
                    return out
                with zf.open(names[0], "r") as f:
                    out["sample"] = inspect_text_stream(f, names[0])

        elif lower.endswith(".gz"):
            out["archive_type"] = "gzip"
            with gzip.open(path, "rb") as f:
                out["sample"] = inspect_text_stream(f, path.name)
        else:
            out.update({"status": "FAIL", "reason": "unsupported archive suffix"})
            return out

        sample = out.get("sample") or {}
        enough = sample.get("json_ok", 0) > 0 and (
            sample.get("asks_records", 0) > 0 or sample.get("bids_records", 0) > 0
        )
        out["status"] = "PASS" if enough else "REVIEW"
        return out

    except Exception as e:
        out.update({"status": "FAIL", "error": repr(e)})
        return out


def choose_primary_candidate(discovery: dict) -> tuple[dict | None, str | None]:
    links = discovery.get("links") or []
    trusted = [x for x in links if x.get("trusted_url") and x.get("url")]
    if len(trusted) != 1:
        return None, f"expected exactly 1 trusted candidate, found {len(trusted)}"
    return trusted[0], None


def write_summary(report: dict) -> None:
    lines = [
        "# SC001-DATA-Q003 — Optimized OKX L2 Qualification",
        "",
        f"- Overall: `{report['overall_status']}`",
        "- Strategy/P&L calculated: **NO**",
        "- Bulk/multi-year L2 download: **NO**",
        f"- Primary raw sample date: `{PRIMARY_DOWNLOAD_DATE} UTC`",
        "- Hard session cap: **2.00 GB**",
        "- Hard workspace cap: **2.00 GB**",
        "- Single archive cap: **512 MB**",
        "- Minimum free-space reserve: **4.00 GB**",
        "",
        "## Metadata discovery",
    ]
    for d in report["discoveries"]:
        sizes = [x.get("reported_bytes") for x in d.get("links", []) if x.get("reported_bytes") is not None]
        size_text = ", ".join(f"{x/1_000_000:.1f} MB" for x in sizes) if sizes else "unknown"
        lines.append(
            f"- {d['date']}: {d['status']}; trusted links={sum(1 for x in d.get('links', []) if x.get('trusted_url'))}; reported sizes={size_text}"
        )

    lines += ["", "## Current instrument metadata"]
    im = report.get("instrument_metadata", {})
    lines.append(f"- status: `{im.get('status')}`")
    if im.get("fields"):
        for k, v in im["fields"].items():
            lines.append(f"- {k}: `{v}`")

    lines += ["", "## Canonical sample"]
    lines.append(f"- decision: `{report.get('sample_decision', {}).get('status')}`")
    if report.get("sample_decision", {}).get("reason"):
        lines.append(f"- reason: {report['sample_decision']['reason']}")
    if report.get("download"):
        lines.append(f"- download: `{report['download'].get('status')}`")
        if report['download'].get('bytes') is not None:
            lines.append(f"- compressed bytes: {report['download']['bytes']:,}")
    if report.get("schema"):
        sample = (report["schema"].get("sample") or {})
        lines.append(f"- archive/schema inspection: `{report['schema'].get('status')}`")
        lines.append(f"- sampled JSON records: {sample.get('json_ok', 0)}")
        lines.append(f"- snapshot/update actions: {sample.get('actions', {})}")
        lines.append(f"- sequencing fields: {sample.get('sequencing_fields', {})}")
        lines.append(f"- asks records: {sample.get('asks_records', 0)}; bids records: {sample.get('bids_records', 0)}")

    lines += [
        "",
        "## Boundary",
        "Q003 is data qualification only. L2 does not by itself prove exact maker queue position or strategy profitability.",
        "Do not begin multi-year L2 download before this output is reviewed and a staged bulk calendar is frozen.",
    ]
    atomic_text(SUMMARY, "\n".join(lines) + "\n")


def main() -> None:
    global downloaded_this_run
    OUTDIR.mkdir(parents=True, exist_ok=True)
    safety_check()

    print("=" * 78)
    print("SC001-DATA-Q003 OPTIMIZED OKX L2 QUALIFICATION v0.2")
    print("Strategy/P&L: NO")
    print("Multi-year/bulk L2 download: NO")
    print("Primary raw sample date:", PRIMARY_DOWNLOAD_DATE)
    print("Session cap: 2.00 GB | Workspace cap: 2.00 GB | Per-file cap: 512 MB")
    print("Minimum free-space reserve: 4.00 GB")
    print("=" * 78)

    report = {
        "stage": STAGE,
        "version": VERSION,
        "started_at_utc": now_iso(),
        "strategy_pnl_calculated": False,
        "bulk_l2_downloaded": False,
        "discovery_dates": DISCOVERY_DATES,
        "primary_download_date": PRIMARY_DOWNLOAD_DATE,
        "instrument": {"instType": INST_TYPE, "instFamily": INST_FAMILY, "instId": INST_ID},
        "safety": {
            "session_download_cap_bytes": SESSION_DOWNLOAD_CAP_BYTES,
            "workspace_cap_bytes": WORKSPACE_CAP_BYTES,
            "per_file_cap_bytes": PER_FILE_CAP_BYTES,
            "minimum_free_reserve_bytes": MIN_FREE_RESERVE_BYTES,
            "max_decompressed_inspection_bytes": MAX_DECOMPRESSED_INSPECTION_BYTES,
            "free_bytes_start": free_bytes(),
        },
    }

    print("Fetching current OKX instrument metadata...")
    report["instrument_metadata"] = instrument_metadata()

    discoveries = []
    for d in DISCOVERY_DATES:
        print("Discovering L2 metadata:", d)
        rec = discover_for_date(d)
        discoveries.append(rec)
        print("  status:", rec["status"], "links:", len(rec.get("links", [])))
        time.sleep(0.8)
    report["discoveries"] = discoveries

    primary = next((x for x in discoveries if x["date"] == PRIMARY_DOWNLOAD_DATE), None)
    candidate = None
    reason = None
    if primary is None or primary.get("status") != "PASS":
        reason = "canonical date did not return L2 links"
    else:
        candidate, reason = choose_primary_candidate(primary)

    sample_decision = {"status": "PENDING", "reason": reason, "candidate": candidate}
    report["sample_decision"] = sample_decision

    if candidate is None:
        sample_decision["status"] = "SAFE_SKIP"
        report["download"] = None
        report["schema"] = None
        overall = "QUALIFIED_METADATA_ONLY" if any(x.get("status") == "PASS" for x in discoveries) else "REDESIGN"
    else:
        print("Canonical candidate:", candidate.get("filename"))
        head = head_remote(candidate["url"])
        sample_decision["head"] = head
        reported = candidate.get("reported_bytes")
        head_size = head.get("content_length") if head.get("status") == "PASS" else None
        known_sizes = [x for x in (reported, head_size) if isinstance(x, int) and x > 0]
        expected = max(known_sizes) if known_sizes else None
        sample_decision["effective_expected_bytes"] = expected

        if expected is None:
            sample_decision.update({"status": "SAFE_SKIP", "reason": "size unavailable from metadata/HEAD"})
            report["download"] = None
            report["schema"] = None
            overall = "QUALIFIED_METADATA_ONLY"
        elif expected > PER_FILE_CAP_BYTES:
            sample_decision.update({"status": "SAFE_SKIP", "reason": "canonical file exceeds 512 MB cap"})
            report["download"] = None
            report["schema"] = None
            overall = "QUALIFIED_METADATA_ONLY"
        else:
            sample_decision["status"] = "APPROVED_FOR_SINGLE_SAMPLE"
            name = str(candidate.get("filename") or f"okx_l2_{PRIMARY_DOWNLOAD_DATE}.bin")
            safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(name).name)
            dest = OUTDIR / safe_name
            print(f"Downloading ONE canonical L2 sample ({expected/1_000_000:.1f} MB expected)...")
            dl = safe_download(candidate["url"], dest, expected)
            report["download"] = dl
            if dl.get("status") == "PASS":
                print("Inspecting compressed archive in-place; no extraction to disk...")
                schema = inspect_archive(dest)
                report["schema"] = schema
                atomic_json(SCHEMA_REPORT, schema)
                overall = "QUALIFIED_SAMPLE" if schema.get("status") == "PASS" else "REDESIGN"
            else:
                report["schema"] = None
                overall = "QUALIFIED_METADATA_ONLY" if dl.get("status") == "SAFE_SKIP" else "REDESIGN"

    report["overall_status"] = overall
    report["finished_at_utc"] = now_iso()
    report["safety"]["downloaded_this_run_bytes"] = downloaded_this_run
    report["safety"]["free_bytes_end_before_reports"] = free_bytes()
    report["safety"]["workspace_bytes_before_reports"] = dir_size(OUTDIR)

    atomic_json(REPORT, report)
    write_summary(report)
    safety_check()

    final_safety = {
        "stage": STAGE,
        "workspace_bytes_after_main_outputs": dir_size(OUTDIR),
        "free_bytes_after_main_outputs": free_bytes(),
        "downloaded_this_run_bytes": downloaded_this_run,
        "caps": {
            "session": SESSION_DOWNLOAD_CAP_BYTES,
            "workspace": WORKSPACE_CAP_BYTES,
            "per_file": PER_FILE_CAP_BYTES,
            "reserve": MIN_FREE_RESERVE_BYTES,
        },
    }
    atomic_json(OUTDIR / "sc001_data_q003_final_safety.json", final_safety)
    safety_check()

    print("\n" + "=" * 78)
    print("SC001-DATA-Q003 COMPLETE")
    print("Overall:", overall)
    print("Network bytes this run:", f"{downloaded_this_run:,}")
    print("Workspace bytes:", f"{dir_size(OUTDIR):,}")
    print("Results:", OUTDIR)
    print("\nUpload these files to ChatGPT:")
    print("1) sc001_data_q003_report.json")
    print("2) sc001_data_q003_summary.md")
    print("3) sc001_data_q003_final_safety.json")
    if SCHEMA_REPORT.exists():
        print("4) sc001_data_q003_schema.json")


if __name__ == "__main__":
    main()
