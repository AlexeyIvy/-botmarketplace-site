"""SC001-DATA-Q007 — metadata-only OKX Q1 L2 preflight.

No archive bodies. No TFI/midquote features. No P&L. Q2/Validation/Final closed.
Android/Pydroid compatible; standard library only.
"""
from __future__ import annotations

import json
import os
import shutil
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

STAGE = "SC001-DATA-Q007-OKX-L2-Q1-PREFLIGHT"
VERSION = "0.1"
PROTOCOL_COMMIT = "448c29985811044b2717bdb592a5eb4810461bc5"
PARENT_STAGE = "SC001-DATA-Q006R-OKX-UTC-STITCH"

TRADE_MODULE = "4"
INST_TYPE = "SWAP"
INST_FAMILY = "BTC-USDT"
TARGET_INST = "BTC-USDT-SWAP"
DATES = (
    "2024-01-05",
    "2024-01-14",
    "2024-01-31",
    "2024-02-12",
    "2024-02-13",
)

DOWNLOAD = Path("/storage/emulated/0/Download")
PARENT_REPORT = (
    DOWNLOAD / "SC001_DATA_Q006R_OKX_UTC_STITCH" /
    "sc001_data_q006r_okx_utc_stitch_report.json"
)
OUTDIR = DOWNLOAD / "SC001_DATA_Q007_OKX_L2_Q1_PREFLIGHT"
REPORT = OUTDIR / "sc001_data_q007_okx_l2_q1_preflight_report.json"
SUMMARY = OUTDIR / "sc001_data_q007_okx_l2_q1_preflight_summary.md"
SAFETY = OUTDIR / "sc001_data_q007_okx_l2_q1_preflight_final_safety.json"

DOMAINS = ("https://www.okx.com", "https://us.okx.com")
DISCOVERY_PATH = "/priapi/v5/broker/public/trade-data/download-link"
REFERER = "https://www.okx.com/historical-data"
USER_AGENT = "BotMarketplace-SC001-Q007/0.1"
TIMEOUT = 60
RETRIES = 3

NETWORK_CAP_BYTES = 20_000_000
WORKSPACE_CAP_BYTES = 20_000_000
PER_RESPONSE_CAP_BYTES = 4_000_000
MIN_FREE_RESERVE_BYTES = 4_000_000_000
ALLOWED_STATIC_PREFIX = "static.okx."

network_bytes_read = 0


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def free_bytes() -> int:
    return shutil.disk_usage(DOWNLOAD).free


def safety_check(extra_workspace: int = 0) -> None:
    if network_bytes_read > NETWORK_CAP_BYTES:
        raise RuntimeError("Q007 network cap exceeded")
    if dir_size(OUTDIR) + max(0, extra_workspace) > WORKSPACE_CAP_BYTES:
        raise RuntimeError("Q007 workspace cap exceeded")
    if free_bytes() - max(0, extra_workspace) < MIN_FREE_RESERVE_BYTES:
        raise RuntimeError("Q007 free-space reserve violated")


def atomic_text(path: Path, text: str) -> None:
    raw = text.encode("utf-8")
    safety_check(len(raw))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("wb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def atomic_json(path: Path, obj) -> None:
    atomic_text(path, json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True))


def trusted_static(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme == "https" and (p.hostname or "").lower().startswith(ALLOWED_STATIC_PREFIX)
    except Exception:
        return False


def date_bounds(date_text: str) -> tuple[int, int]:
    d = datetime.strptime(date_text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    lo = int(d.timestamp() * 1000)
    hi = int((d + timedelta(days=1) - timedelta(milliseconds=1)).timestamp() * 1000)
    return lo, hi


def payload_for(date_text: str) -> dict:
    lo, hi = date_bounds(date_text)
    return {
        "module": TRADE_MODULE,
        "instType": INST_TYPE,
        "instQueryParam": {"instFamilyList": [INST_FAMILY]},
        "dateQuery": {
            "dateAggrType": "daily",
            "begin": str(lo),
            "end": str(hi),
        },
    }


def request_json(domain: str, payload: dict) -> tuple[object | None, dict]:
    global network_bytes_read
    url = domain + DISCOVERY_PATH + "?t=" + str(int(time.time() * 1000))
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json,*/*",
        "Content-Type": "application/json",
        "Referer": REFERER,
    }
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = Request(url, data=body, method="POST", headers=headers)
            with urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read(PER_RESPONSE_CAP_BYTES + 1)
                final = resp.geturl()
                status = int(getattr(resp, "status", 200))
            if len(raw) > PER_RESPONSE_CAP_BYTES:
                raise RuntimeError("Q007 metadata response cap exceeded")
            network_bytes_read += len(raw)
            safety_check()
            text = raw.decode("utf-8", errors="replace")
            obj = json.loads(text)
            return obj, {
                "status": status,
                "bytes_read": len(raw),
                "final_url": final,
                "json_ok": True,
                "preview": text[:500],
            }
        except HTTPError as e:
            raw = e.read(min(PER_RESPONSE_CAP_BYTES, 256_000))
            network_bytes_read += len(raw)
            safety_check()
            text = raw.decode("utf-8", errors="replace")
            obj = None
            try:
                obj = json.loads(text)
            except Exception:
                pass
            if e.code == 429 and attempt < RETRIES:
                time.sleep(1.5 * attempt)
                continue
            return obj, {
                "status": int(e.code),
                "bytes_read": len(raw),
                "http_error": True,
                "json_ok": obj is not None,
                "preview": text[:500],
            }
        except (URLError, TimeoutError, OSError, ValueError, RuntimeError) as e:
            last = repr(e)
            if attempt < RETRIES:
                time.sleep(1.5 * attempt)
                continue
    return None, {"status": None, "error": last or "request failed"}


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
            fn = g.get("filename") or g.get("fileName")
            url = g.get("url")
            out.append({
                "filename": fn,
                "url": url,
                "sizeMB_raw": g.get("sizeMB"),
                "trusted_url": trusted_static(str(url)) if url else False,
            })
    return out


def discover(date_text: str) -> dict:
    payload = payload_for(date_text)
    attempts = []
    for domain in DOMAINS:
        obj, meta = request_json(domain, payload)
        code = obj.get("code") if isinstance(obj, dict) else None
        links = extract_links(obj)
        attempts.append({
            "domain": domain,
            "code": code,
            "msg": obj.get("msg") if isinstance(obj, dict) else None,
            "meta": meta,
            "links": links,
        })
        if code == "0" and links:
            return {"status": "PASS", "payload": payload, "attempts": attempts, "links": links}
        time.sleep(0.8)
    return {"status": "NO_LINKS", "payload": payload, "attempts": attempts, "links": []}


def exact_candidate(links: list[dict], date_text: str) -> tuple[dict | None, str]:
    expected = f"{TARGET_INST}-L2orderbook-400lv-{date_text}.tar.gz"
    exact = [x for x in links if x.get("filename") == expected and x.get("trusted_url") is True]
    if len(exact) == 1:
        return exact[0], "EXACT_DATE_FILENAME"
    if len(exact) == 0:
        return None, "NO_EXACT_DATE_FILENAME"
    return None, "MULTIPLE_EXACT_DATE_FILENAMES"


def head_remote(url: str, expected_filename: str) -> dict:
    if not trusted_static(url):
        return {"status": "REJECTED_URL"}
    try:
        req = Request(url, method="HEAD", headers={"User-Agent": USER_AGENT, "Referer": REFERER})
        with urlopen(req, timeout=TIMEOUT) as resp:
            final = resp.geturl()
            size = resp.headers.get("Content-Length")
            ok = trusted_static(final) and expected_filename in final and size and size.isdigit()
            return {
                "status": "PASS" if ok else "REVIEW",
                "http_status": int(getattr(resp, "status", 200)),
                "final_url": final,
                "content_length": int(size) if size and size.isdigit() else None,
                "content_type": resp.headers.get("Content-Type"),
            }
    except Exception as e:
        return {"status": "ERROR", "error": repr(e)}


def verify_parent() -> dict:
    if not PARENT_REPORT.exists():
        raise RuntimeError(f"missing Q006R parent report: {PARENT_REPORT}")
    obj = json.loads(PARENT_REPORT.read_text(encoding="utf-8"))
    if obj.get("stage") != PARENT_STAGE or obj.get("overall_status") != "PASS":
        raise RuntimeError("Q006R parent is not PASS")
    if obj.get("q2_okx_accessed") is not False:
        raise RuntimeError("Q006R Q2 boundary mismatch")
    return {"path": str(PARENT_REPORT), "overall_status": obj.get("overall_status")}


def write_outputs(report: dict) -> None:
    atomic_json(REPORT, report)
    lines = [
        "# SC001-DATA-Q007 — OKX Q1 L2 metadata preflight",
        "",
        f"- Overall: `{report.get('overall_status')}`",
        "- Archive bodies downloaded: **NO**",
        "- Strategy/midquote/P&L calculated: **NO**",
        f"- Network bytes read: {report.get('network_bytes_read', 0)}",
        "",
        "## Exact-date L2 archives",
    ]
    total = 0
    for row in report.get("dates", []):
        head = row.get("head") or {}
        size = head.get("content_length")
        if isinstance(size, int):
            total += size
        lines.append(
            f"- {row.get('date')}: **{row.get('status')}**; "
            f"file={row.get('filename')}; bytes={size}"
        )
    lines += ["", f"Known compressed bytes total: {total}", "", "## Boundary",
              "Metadata/HEAD only. No L2 archive GET, no Q2, no Validation/Final."]
    atomic_text(SUMMARY, "\n".join(lines) + "\n")
    atomic_json(SAFETY, {
        "stage": STAGE,
        "network_bytes_read": network_bytes_read,
        "workspace_bytes_after_outputs": dir_size(OUTDIR),
        "free_bytes_after_outputs": free_bytes(),
        "archive_bodies_downloaded": False,
        "caps": {
            "network": NETWORK_CAP_BYTES,
            "workspace": WORKSPACE_CAP_BYTES,
            "per_response": PER_RESPONSE_CAP_BYTES,
            "reserve": MIN_FREE_RESERVE_BYTES,
        },
    })


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    safety_check()
    parent = verify_parent()
    report = {
        "stage": STAGE,
        "version": VERSION,
        "protocol_commit": PROTOCOL_COMMIT,
        "started_at_utc": now_iso(),
        "parent": parent,
        "scope": {"venue": "OKX", "instrument": TARGET_INST, "module": TRADE_MODULE, "dates": list(DATES)},
        "archive_bodies_downloaded": False,
        "strategy_features_calculated": False,
        "midquote_response_calculated": False,
        "strategy_pnl_calculated": False,
        "q2_okx_accessed": False,
        "validation_or_final_accessed": False,
        "dates": [],
    }
    try:
        for date_text in DATES:
            print(f"[{date_text}] L2 metadata...")
            rec = discover(date_text)
            candidate, mode = exact_candidate(rec.get("links", []), date_text)
            if candidate is None:
                row = {"date": date_text, "status": "REVIEW", "identity_mode": mode, "filename": None, "head": None}
            else:
                expected = candidate["filename"]
                head = head_remote(str(candidate["url"]), expected)
                size = head.get("content_length") if isinstance(head, dict) else None
                ok = head.get("status") == "PASS" and isinstance(size, int) and size > 0
                row = {
                    "date": date_text,
                    "status": "PASS" if ok else "REVIEW",
                    "identity_mode": mode,
                    "filename": expected,
                    "reported_sizeMB": candidate.get("sizeMB_raw"),
                    "url": candidate.get("url"),
                    "head": head,
                    "discovery_link_count": len(rec.get("links", [])),
                }
            report["dates"].append(row)
            report["network_bytes_read"] = network_bytes_read
            write_outputs(report)
            safety_check()
            time.sleep(0.8)

        report["overall_status"] = "PASS" if len(report["dates"]) == len(DATES) and all(x["status"] == "PASS" for x in report["dates"]) else "REVIEW"
        report["known_compressed_bytes_total"] = sum((x.get("head") or {}).get("content_length") or 0 for x in report["dates"])
        report["finished_at_utc"] = now_iso()
        report["network_bytes_read"] = network_bytes_read
        write_outputs(report)
        print(f"COMPLETE: {report['overall_status']} | L2 bodies=NO | total_known={report['known_compressed_bytes_total']}")
    except Exception as exc:
        report["overall_status"] = "ERROR"
        report["error"] = repr(exc)
        report["finished_at_utc"] = now_iso()
        report["network_bytes_read"] = network_bytes_read
        write_outputs(report)
        raise


if __name__ == "__main__":
    main()
