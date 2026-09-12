"""SC001-DATA-Q005 — metadata-only OKX historical tick-trade preflight.

No archive bodies. No signal/features. No P&L. No Validation/Final.
Standard library only; Android/Pydroid compatible.
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

STAGE = "SC001-DATA-Q005-OKX-TRADE-PREFLIGHT"
VERSION = "0.1"
INST_TYPE = "SWAP"
INST_FAMILY = "BTC-USDT"
TARGET_INST = "BTC-USDT-SWAP"
MODULE_CANDIDATES = ("1", "2", "3", "4", "5")
PROBE_DATE = "2024-01-05"
DATES = (
    "2024-01-05",
    "2024-01-14",
    "2024-01-31",
    "2024-02-12",
    "2024-02-13",
)

DOWNLOAD = Path("/storage/emulated/0/Download")
OUTDIR = DOWNLOAD / "SC001_DATA_Q005_OKX_TRADE_PREFLIGHT"
REPORT = OUTDIR / "sc001_data_q005_okx_trade_preflight_report.json"
SUMMARY = OUTDIR / "sc001_data_q005_okx_trade_preflight_summary.md"
SAFETY = OUTDIR / "sc001_data_q005_okx_trade_preflight_final_safety.json"

DOMAINS = ("https://www.okx.com", "https://us.okx.com")
DISCOVERY_PATH = "/priapi/v5/broker/public/trade-data/download-link"
REFERER = "https://www.okx.com/historical-data"
USER_AGENT = "BotMarketplace-SC001-Q005/0.1"
TIMEOUT = 60
RETRIES = 2

NETWORK_CAP_BYTES = 20_000_000
WORKSPACE_CAP_BYTES = 20_000_000
PER_RESPONSE_CAP_BYTES = 4_000_000
MIN_FREE_RESERVE_BYTES = 4_000_000_000
ALLOWED_STATIC_PREFIX = "static.okx."

network_bytes_read = 0

FORBIDDEN_FILENAME_TOKENS = (
    "orderbook", "order-book", "books", "book-", "depth", "l2",
    "funding", "fund-rate", "fundingrate", "candle", "kline",
    "borrow", "interest",
)
TRADE_FILENAME_TOKENS = ("trade", "trades", "traderecord")


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
        raise RuntimeError("Q005 network cap exceeded")
    if dir_size(OUTDIR) + max(0, extra_workspace) > WORKSPACE_CAP_BYTES:
        raise RuntimeError("Q005 workspace cap exceeded")
    if free_bytes() - max(0, extra_workspace) < MIN_FREE_RESERVE_BYTES:
        raise RuntimeError("Q005 free-space reserve violated")


def atomic_json(path: Path, obj) -> None:
    raw = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    safety_check(len(raw))
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(raw)
    os.replace(tmp, path)


def atomic_text(path: Path, text: str) -> None:
    raw = text.encode("utf-8")
    safety_check(len(raw))
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(raw)
    os.replace(tmp, path)


def date_bounds(date_text: str) -> tuple[int, int]:
    d = datetime.strptime(date_text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    begin = int(d.timestamp() * 1000)
    end = int((d + timedelta(days=1) - timedelta(milliseconds=1)).timestamp() * 1000)
    return begin, end


def build_payload(module: str, date_text: str) -> dict:
    begin, end = date_bounds(date_text)
    return {
        "module": module,
        "instType": INST_TYPE,
        "instQueryParam": {"instFamilyList": [INST_FAMILY]},
        "dateQuery": {
            "dateAggrType": "daily",
            "begin": str(begin),
            "end": str(end),
        },
    }


def request_json(url: str, payload: dict) -> tuple[object | None, dict]:
    global network_bytes_read
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json,*/*",
        "Content-Type": "application/json",
        "Referer": REFERER,
    }
    last_error = None
    for attempt in range(RETRIES):
        try:
            req = Request(url, data=body, method="POST", headers=headers)
            with urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read(PER_RESPONSE_CAP_BYTES + 1)
                status = int(getattr(resp, "status", 200))
                final_url = resp.geturl()
            if len(raw) > PER_RESPONSE_CAP_BYTES:
                raise RuntimeError("metadata response cap exceeded")
            network_bytes_read += len(raw)
            safety_check()
            text = raw.decode("utf-8", errors="replace")
            try:
                obj = json.loads(text)
            except Exception:
                obj = None
            return obj, {
                "status": status,
                "bytes_read": len(raw),
                "final_url": final_url,
                "json_ok": obj is not None,
                "preview": text[:500],
            }
        except HTTPError as e:
            raw = e.read(min(PER_RESPONSE_CAP_BYTES, 256_000))
            network_bytes_read += len(raw)
            safety_check()
            text = raw.decode("utf-8", errors="replace")
            try:
                obj = json.loads(text)
            except Exception:
                obj = None
            return obj, {
                "status": int(e.code),
                "bytes_read": len(raw),
                "http_error": True,
                "preview": text[:500],
                "json_ok": obj is not None,
            }
        except (URLError, TimeoutError, OSError, RuntimeError) as e:
            last_error = repr(e)
            if attempt + 1 < RETRIES:
                time.sleep(1.0 + attempt)
    return None, {"status": None, "error": last_error or "request failed"}


def trusted_static(url: str) -> tuple[bool, str | None]:
    try:
        p = urlparse(url)
        host = (p.hostname or "").lower()
        return p.scheme == "https" and host.startswith(ALLOWED_STATIC_PREFIX), host
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
            filename = g.get("filename") or g.get("fileName")
            url = g.get("url")
            ok, host = trusted_static(str(url)) if url else (False, None)
            fn_low = str(filename or "").lower()
            trade_like = (
                bool(filename)
                and any(tok in fn_low for tok in TRADE_FILENAME_TOKENS)
                and not any(tok in fn_low for tok in FORBIDDEN_FILENAME_TOKENS)
            )
            exact_target = TARGET_INST.lower() in fn_low.replace("_", "-")
            out.append({
                "filename": filename,
                "url": url,
                "trusted_url": ok,
                "host": host,
                "trade_like_filename": trade_like,
                "exact_target_in_filename": exact_target,
                "sizeMB_raw": g.get("sizeMB"),
            })
    return out


def discover(module: str, date_text: str) -> dict:
    payload = build_payload(module, date_text)
    attempts = []
    for domain in DOMAINS:
        url = domain + DISCOVERY_PATH + "?t=" + str(int(time.time() * 1000))
        obj, meta = request_json(url, payload)
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
                "module": module,
                "selected_domain": domain,
                "payload": payload,
                "links": links,
                "attempts": attempts,
            }
    return {
        "status": "NO_LINKS",
        "date": date_text,
        "module": module,
        "payload": payload,
        "links": [],
        "attempts": attempts,
    }


def head_remote(url: str) -> dict:
    ok, host = trusted_static(url)
    if not ok:
        return {"status": "REJECTED_URL", "host": host}
    try:
        req = Request(url, method="HEAD", headers={"User-Agent": USER_AGENT, "Referer": REFERER})
        with urlopen(req, timeout=TIMEOUT) as resp:
            final = resp.geturl()
            final_ok, final_host = trusted_static(final)
            if not final_ok:
                return {"status": "REJECTED_REDIRECT", "final_url": final, "host": final_host}
            cl = resp.headers.get("Content-Length")
            size = int(cl) if cl and cl.isdigit() else None
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


def choose_canonical(links: list[dict]) -> tuple[dict | None, str]:
    trade = [x for x in links if x.get("trade_like_filename") and x.get("trusted_url")]
    exact = [x for x in trade if x.get("exact_target_in_filename")]
    if len(exact) == 1:
        return exact[0], "EXACT_TARGET"
    if len(exact) > 1:
        return None, "AMBIGUOUS_EXACT_TARGET"
    if len(trade) == 1:
        return trade[0], "FAMILY_LEVEL_SINGLE"
    if not trade:
        return None, "NO_TRADE_LIKE_FILE"
    return None, "AMBIGUOUS_FAMILY_LEVEL"


def write_outputs(report: dict) -> None:
    atomic_json(REPORT, report)
    lines = [
        "# SC001-DATA-Q005 — OKX tick-trade preflight",
        "",
        f"- Overall: `{report.get('overall_status')}`",
        f"- Selected module: `{report.get('selected_trade_module')}`",
        "- Archive bodies downloaded: **NO**",
        "- Strategy features/P&L: **NO**",
        f"- Network bytes read: {report.get('network_bytes_read', 0)}",
        "",
        "## Fixed Q1 dates",
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
    report = {
        "stage": STAGE,
        "version": VERSION,
        "started_at_utc": now_iso(),
        "scope": {
            "venue": "OKX",
            "instType": INST_TYPE,
            "instFamily": INST_FAMILY,
            "targetInst": TARGET_INST,
            "dates": list(DATES),
            "module_candidates": list(MODULE_CANDIDATES),
            "probe_date": PROBE_DATE,
        },
        "archive_bodies_downloaded": False,
        "strategy_features_calculated": False,
        "strategy_pnl_calculated": False,
        "validation_or_final_accessed": False,
        "module_probe": [],
        "dates": [],
    }
    try:
        plausible_modules = []
        for module in MODULE_CANDIDATES:
            print(f"Probe module {module} on {PROBE_DATE}...")
            rec = discover(module, PROBE_DATE)
            canonical, mode = choose_canonical(rec.get("links", []))
            rec["canonical_identity_mode"] = mode
            rec["canonical_candidate"] = canonical
            report["module_probe"].append(rec)
            if canonical is not None:
                plausible_modules.append(module)
            report["network_bytes_read"] = network_bytes_read
            write_outputs(report)
            safety_check()

        if len(plausible_modules) != 1:
            report["selected_trade_module"] = None
            report["overall_status"] = "REDESIGN"
            report["reason"] = f"expected exactly one plausible trade module; got {plausible_modules}"
            report["finished_at_utc"] = now_iso()
            report["network_bytes_read"] = network_bytes_read
            write_outputs(report)
            print("COMPLETE: REDESIGN", plausible_modules)
            return

        selected = plausible_modules[0]
        report["selected_trade_module"] = selected

        for date_text in DATES:
            print(f"[{date_text}] module {selected} metadata...")
            if date_text == PROBE_DATE:
                rec = next(x for x in report["module_probe"] if x["module"] == selected)
            else:
                rec = discover(selected, date_text)
            canonical, mode = choose_canonical(rec.get("links", []))
            if canonical is None:
                row = {
                    "date": date_text,
                    "status": "REVIEW",
                    "identity_mode": mode,
                    "filename": None,
                    "url": None,
                    "head": None,
                }
            else:
                head = head_remote(str(canonical["url"]))
                size = head.get("content_length") if isinstance(head, dict) else None
                ok = (
                    head.get("status") == "PASS"
                    and isinstance(size, int)
                    and size > 0
                    and canonical.get("trusted_url") is True
                )
                row = {
                    "date": date_text,
                    "status": "PASS" if ok else "REVIEW",
                    "identity_mode": mode,
                    "filename": canonical.get("filename"),
                    "url": canonical.get("url"),
                    "head": head,
                }
            report["dates"].append(row)
            report["network_bytes_read"] = network_bytes_read
            write_outputs(report)
            safety_check()

        report["overall_status"] = (
            "PASS"
            if len(report["dates"]) == len(DATES)
            and all(x.get("status") == "PASS" for x in report["dates"])
            else "REVIEW"
        )
        report["finished_at_utc"] = now_iso()
        report["network_bytes_read"] = network_bytes_read
        write_outputs(report)
        print(
            f"COMPLETE: {report['overall_status']} | module={selected} | "
            f"network={network_bytes_read} | archive_body=NO | P&L=NO"
        )
    except Exception as exc:
        report["overall_status"] = "ERROR"
        report["error"] = repr(exc)
        report["finished_at_utc"] = now_iso()
        report["network_bytes_read"] = network_bytes_read
        write_outputs(report)
        raise


if __name__ == "__main__":
    main()
