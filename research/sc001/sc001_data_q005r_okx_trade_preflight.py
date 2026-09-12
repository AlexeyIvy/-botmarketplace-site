"""SC001-DATA-Q005R — repaired metadata-only OKX trade preflight.

Exact-date identity repair only. No archive bodies, no features, no P&L,
no formal Validation/Final. Standard library only; Android/Pydroid compatible.
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

STAGE = "SC001-DATA-Q005R-OKX-TRADE-PREFLIGHT"
VERSION = "0.1"
PARENT_STAGE = "SC001-DATA-Q005-OKX-TRADE-PREFLIGHT"
TRADE_MODULE = "1"
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
    DOWNLOAD / "SC001_DATA_Q005_OKX_TRADE_PREFLIGHT" /
    "sc001_data_q005_okx_trade_preflight_report.json"
)
OUTDIR = DOWNLOAD / "SC001_DATA_Q005R_OKX_TRADE_PREFLIGHT"
REPORT = OUTDIR / "sc001_data_q005r_okx_trade_preflight_report.json"
SUMMARY = OUTDIR / "sc001_data_q005r_okx_trade_preflight_summary.md"
SAFETY = OUTDIR / "sc001_data_q005r_okx_trade_preflight_final_safety.json"

DOMAINS = ("https://www.okx.com", "https://us.okx.com")
DISCOVERY_PATH = "/priapi/v5/broker/public/trade-data/download-link"
REFERER = "https://www.okx.com/historical-data"
USER_AGENT = "BotMarketplace-SC001-Q005R/0.1"
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
        raise RuntimeError("Q005R network cap exceeded")
    if dir_size(OUTDIR) + max(0, extra_workspace) > WORKSPACE_CAP_BYTES:
        raise RuntimeError("Q005R workspace cap exceeded")
    if free_bytes() - max(0, extra_workspace) < MIN_FREE_RESERVE_BYTES:
        raise RuntimeError("Q005R minimum free-space reserve violated")


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
        host = (p.hostname or "").lower()
        return p.scheme == "https" and host.startswith(ALLOWED_STATIC_PREFIX)
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
                raise RuntimeError("Q005R metadata response cap exceeded")
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
        rec = {
            "domain": domain,
            "code": code,
            "msg": obj.get("msg") if isinstance(obj, dict) else None,
            "meta": meta,
            "links": links,
        }
        attempts.append(rec)
        if code == "0" and links:
            return {
                "status": "PASS",
                "date": date_text,
                "payload": payload,
                "selected_domain": domain,
                "attempts": attempts,
                "links": links,
            }
        time.sleep(0.8)
    return {
        "status": "NO_LINKS",
        "date": date_text,
        "payload": payload,
        "selected_domain": None,
        "attempts": attempts,
        "links": [],
    }


def exact_candidate(links: list[dict], date_text: str) -> tuple[dict | None, str]:
    expected = f"{TARGET_INST}-trades-{date_text}.zip"
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
            if not trusted_static(final):
                return {"status": "REJECTED_REDIRECT", "final_url": final}
            name_ok = expected_filename in final
            cl = resp.headers.get("Content-Length")
            size = int(cl) if cl and cl.isdigit() else None
            return {
                "status": "PASS" if name_ok and isinstance(size, int) and size > 0 else "REVIEW",
                "http_status": int(getattr(resp, "status", 200)),
                "content_length": size,
                "content_type": resp.headers.get("Content-Type"),
                "final_url": final,
                "filename_identity_ok": name_ok,
            }
    except Exception as e:
        return {"status": "ERROR", "error": repr(e)}


def verify_parent() -> dict:
    if not PARENT_REPORT.exists():
        raise RuntimeError(f"missing parent Q005 report: {PARENT_REPORT}")
    obj = json.loads(PARENT_REPORT.read_text(encoding="utf-8"))
    if obj.get("stage") != PARENT_STAGE:
        raise RuntimeError("Q005 parent stage mismatch")
    if obj.get("overall_status") != "REDESIGN":
        raise RuntimeError("Q005 parent status is not REDESIGN")
    if obj.get("archive_bodies_downloaded") is not False:
        raise RuntimeError("Q005 parent archive-body boundary mismatch")
    probes = obj.get("module_probe") or []
    m1 = next((x for x in probes if x.get("module") == TRADE_MODULE), None)
    if m1 is None:
        raise RuntimeError("Q005 parent missing module-1 evidence")
    expected = f"{TARGET_INST}-trades-2024-01-05.zip"
    if not any(x.get("filename") == expected and x.get("trusted_url") is True for x in (m1.get("links") or [])):
        raise RuntimeError("Q005 parent lacks exact 2024-01-05 trade archive evidence")
    return {
        "path": str(PARENT_REPORT),
        "parent_status": obj.get("overall_status"),
        "trade_module": TRADE_MODULE,
        "anchor_filename": expected,
    }


def write_outputs(report: dict) -> None:
    atomic_json(REPORT, report)
    lines = [
        "# SC001-DATA-Q005R — OKX tick-trade preflight repair",
        "",
        f"- Overall: `{report.get('overall_status')}`",
        f"- Frozen trade module: `{TRADE_MODULE}`",
        "- Archive bodies downloaded: **NO**",
        "- Strategy features/P&L: **NO**",
        f"- Network bytes read: {report.get('network_bytes_read', 0)}",
        "",
        "## Exact-date checks",
    ]
    for row in report.get("dates", []):
        head = row.get("head") or {}
        lines.append(
            f"- {row.get('date')}: **{row.get('status')}**; "
            f"identity={row.get('identity_mode')}; file={row.get('filename')}; "
            f"bytes={head.get('content_length')}"
        )
    lines += [
        "",
        "## Boundary",
        "Metadata/HEAD qualification only. No archive GET, no E002 metric, no P&L, no formal Validation/Final.",
    ]
    atomic_text(SUMMARY, "\n".join(lines) + "\n")
    atomic_json(SAFETY, {
        "stage": STAGE,
        "network_bytes_read": network_bytes_read,
        "workspace_bytes_after_outputs": dir_size(OUTDIR),
        "free_bytes_after_outputs": free_bytes(),
        "caps": {
            "network": NETWORK_CAP_BYTES,
            "workspace": WORKSPACE_CAP_BYTES,
            "per_response": PER_RESPONSE_CAP_BYTES,
            "reserve": MIN_FREE_RESERVE_BYTES,
        },
        "archive_bodies_downloaded": False,
    })


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    safety_check()
    parent = verify_parent()
    report = {
        "stage": STAGE,
        "version": VERSION,
        "started_at_utc": now_iso(),
        "parent_verification": parent,
        "scope": {
            "venue": "OKX",
            "instType": INST_TYPE,
            "instFamily": INST_FAMILY,
            "targetInst": TARGET_INST,
            "tradeModule": TRADE_MODULE,
            "dates": list(DATES),
        },
        "archive_bodies_downloaded": False,
        "strategy_features_calculated": False,
        "strategy_pnl_calculated": False,
        "validation_or_final_accessed": False,
        "dates": [],
    }
    try:
        for date_text in DATES:
            print(f"[{date_text}] exact-date trade metadata...")
            rec = discover(date_text)
            cand, mode = exact_candidate(rec.get("links", []), date_text)
            expected_filename = f"{TARGET_INST}-trades-{date_text}.zip"
            if cand is None:
                row = {
                    "date": date_text,
                    "status": "REVIEW",
                    "identity_mode": mode,
                    "filename": None,
                    "url": None,
                    "head": None,
                    "discovery": rec,
                }
            else:
                head = head_remote(str(cand["url"]), expected_filename)
                ok = head.get("status") == "PASS"
                row = {
                    "date": date_text,
                    "status": "PASS" if ok else "REVIEW",
                    "identity_mode": mode,
                    "filename": cand.get("filename"),
                    "url": cand.get("url"),
                    "reported_sizeMB": cand.get("sizeMB_raw"),
                    "head": head,
                    "discovery_link_count": len(rec.get("links", [])),
                }
            report["dates"].append(row)
            report["network_bytes_read"] = network_bytes_read
            write_outputs(report)
            safety_check()
            time.sleep(1.0)

        report["overall_status"] = (
            "PASS"
            if len(report["dates"]) == len(DATES)
            and all(x.get("status") == "PASS" for x in report["dates"])
            else "REVIEW"
        )
        report["finished_at_utc"] = now_iso()
        report["network_bytes_read"] = network_bytes_read
        write_outputs(report)
        print(f"COMPLETE: {report['overall_status']} | module=1 | network={network_bytes_read} | archive_body=NO | P&L=NO")
    except Exception as exc:
        report["overall_status"] = "ERROR"
        report["error"] = repr(exc)
        report["finished_at_utc"] = now_iso()
        report["network_bytes_read"] = network_bytes_read
        write_outputs(report)
        raise


if __name__ == "__main__":
    main()
