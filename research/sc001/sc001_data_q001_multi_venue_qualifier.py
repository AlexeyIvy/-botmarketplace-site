"""SC001-DATA-Q001 free multi-venue source qualification for Android/Pydroid.

Research-only. No strategy/P&L calculations. Fixed qualification date: 2025-01-15 UTC.
Downloads small qualification samples from Binance and Bybit, verifies/inspects them,
and probes OKX public historical-market-data metadata without bulk L2 download.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import os
import shutil
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

VERSION = "0.1"
QUAL_DATE = "2025-01-15"
DOWNLOAD = Path("/storage/emulated/0/Download")
OUTDIR = DOWNLOAD / "SC001_DATA_Q001"
REPORT = OUTDIR / "sc001_data_q001_report.json"
SUMMARY = OUTDIR / "sc001_data_q001_summary.md"
OKX_PROBE = OUTDIR / "sc001_data_q001_okx_probe.json"
USER_AGENT = "BotMarketplace-SC001-DATA-Q001/0.1"
TIMEOUT = 90
RETRIES = 4
MAX_SAMPLE_BYTES = 350 * 1024 * 1024
HARD_MIN_FREE_MB = 500
RECOMMENDED_FREE_MB = 1200

BINANCE_ITEMS = [
    {
        "name": "binance_um_btcusdt_1m_2025-01-15",
        "url": "https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/1m/BTCUSDT-1m-2025-01-15.zip",
        "checksum_url": "https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/1m/BTCUSDT-1m-2025-01-15.zip.CHECKSUM",
        "filename": "BTCUSDT-1m-2025-01-15.zip",
        "expected_interval_ms": 60_000,
    },
    {
        "name": "binance_um_btcusdt_aggtrades_2025-01-15",
        "url": "https://data.binance.vision/data/futures/um/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-2025-01-15.zip",
        "checksum_url": "https://data.binance.vision/data/futures/um/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-2025-01-15.zip.CHECKSUM",
        "filename": "BTCUSDT-aggTrades-2025-01-15.zip",
        "expected_interval_ms": None,
    },
]

BYBIT_ITEM = {
    "url": "https://public.bybit.com/trading/BTCUSDT/BTCUSDT2025-01-15.csv.gz",
    "filename": "BTCUSDT2025-01-15.csv.gz",
}

OKX_DOMAINS = ["https://www.okx.com", "https://us.okx.com"]
OKX_PATH = "/api/v5/public/market-data-history"
OKX_MODULE_CANDIDATES = [str(i) for i in range(1, 12)]
OKX_BEGIN_MS = "1736899200000"  # 2025-01-15 00:00:00 UTC
OKX_END_MS = "1736985600000"    # 2025-01-16 00:00:00 UTC


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def atomic_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def atomic_json(path, obj):
    atomic_text(path, json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def free_mb():
    return shutil.disk_usage(DOWNLOAD).free / (1024 * 1024)


def head_size(url):
    try:
        req = Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=TIMEOUT) as r:
            v = r.headers.get("Content-Length")
            return int(v) if v and v.isdigit() else None
    except Exception:
        return None


def fetch_text(url, max_bytes=256 * 1024):
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/plain,*/*"})
            with urlopen(req, timeout=TIMEOUT) as r:
                raw = r.read(max_bytes + 1)
            if len(raw) > max_bytes:
                raise RuntimeError("Text response too large")
            return raw.decode("utf-8", errors="replace")
        except Exception as e:
            last = repr(e)
            if attempt < RETRIES:
                time.sleep(attempt * 2)
    raise RuntimeError(f"Failed text fetch: {url} :: {last}")


def download_limited(url, path, cap_bytes=MAX_SAMPLE_BYTES):
    if path.exists() and path.stat().st_size > 0:
        return {"downloaded_this_run": False, "bytes": path.stat().st_size, "sha256": sha256_file(path)}
    advertised = head_size(url)
    if advertised is not None and advertised > cap_bytes:
        raise RuntimeError(f"Advertised size {advertised:,} exceeds safety cap {cap_bytes:,}")
    last = None
    for attempt in range(1, RETRIES + 1):
        tmp = path.with_suffix(path.suffix + ".part")
        try:
            if tmp.exists():
                tmp.unlink()
            req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
            h = hashlib.sha256()
            total = 0
            with urlopen(req, timeout=TIMEOUT) as r, tmp.open("wb") as f:
                while True:
                    chunk = r.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > cap_bytes:
                        raise RuntimeError(f"Download exceeded safety cap {cap_bytes:,} bytes")
                    f.write(chunk)
                    h.update(chunk)
                    if total // (25*1024*1024) != (total-len(chunk)) // (25*1024*1024):
                        print(f"    {path.name}: {total/(1024*1024):.1f} MB")
                f.flush(); os.fsync(f.fileno())
            os.replace(tmp, path)
            return {"downloaded_this_run": True, "bytes": total, "sha256": h.hexdigest(), "advertised_bytes": advertised}
        except Exception as e:
            last = repr(e)
            try:
                if tmp.exists(): tmp.unlink()
            except OSError:
                pass
            if attempt < RETRIES:
                time.sleep(attempt * 3)
    raise RuntimeError(f"Failed download: {url} :: {last}")


def parse_checksum(text):
    for line in text.splitlines():
        p = line.strip().split()
        if p and len(p[0]) == 64 and all(c in "0123456789abcdefABCDEF" for c in p[0]):
            return p[0].lower(), p[-1] if len(p) > 1 else None
    return None, None


def looks_header(row):
    if not row:
        return True
    try:
        int(str(row[0]).strip()); return False
    except Exception:
        return True


def inspect_zip_csv(path, expected_interval_ms=None):
    out = {"valid_zip": False, "members": [], "row_count_total": 0, "data_rows": 0,
           "header_detected": None, "header": None, "preview": [], "timestamp_monotonic": None,
           "timestamp_duplicates": None, "first_timestamp": None, "last_timestamp": None,
           "expected_interval_ms": expected_interval_ms, "interval_breaks": None}
    with zipfile.ZipFile(path, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            out["zip_error_member"] = bad; return out
        out["valid_zip"] = True
        names = [n for n in zf.namelist() if not n.endswith("/")]
        out["members"] = names
        csv_names = [n for n in names if n.lower().endswith(".csv")]
        if not csv_names:
            out["error"] = "no CSV member"; return out
        last_ts = None; dup = nonmono = breaks = 0; first = True
        with zf.open(csv_names[0], "r") as raw:
            reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline=""))
            for row in reader:
                if not row: continue
                out["row_count_total"] += 1
                if first:
                    first = False
                    hdr = looks_header(row); out["header_detected"] = hdr
                    if hdr:
                        out["header"] = row; continue
                if len(out["preview"]) < 5: out["preview"].append(row[:16])
                out["data_rows"] += 1
                try: ts = int(str(row[0]).strip())
                except Exception: continue
                if out["first_timestamp"] is None: out["first_timestamp"] = ts
                if last_ts is not None:
                    if ts == last_ts: dup += 1
                    elif ts < last_ts: nonmono += 1
                    if expected_interval_ms is not None and ts-last_ts != expected_interval_ms: breaks += 1
                last_ts = ts
        out["last_timestamp"] = last_ts
        out["timestamp_monotonic"] = nonmono == 0
        out["timestamp_duplicates"] = dup
        out["interval_breaks"] = breaks if expected_interval_ms is not None else None
    return out


def inspect_gzip_csv(path):
    out = {"valid_gzip": False, "row_count_total": 0, "data_rows": 0,
           "header_detected": None, "header": None, "preview": []}
    with gzip.open(path, "rt", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.reader(f); first = True
        for row in reader:
            if not row: continue
            out["row_count_total"] += 1
            if first:
                first = False; out["valid_gzip"] = True
                hdr = any(any(ch.isalpha() for ch in str(cell)) for cell in row[:8])
                out["header_detected"] = bool(hdr)
                if hdr:
                    out["header"] = row; continue
            if len(out["preview"]) < 5: out["preview"].append(row[:16])
            out["data_rows"] += 1
    return out


def collect_urls(obj):
    found = []
    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if isinstance(v, str) and v.startswith(("http://", "https://")):
                    found.append({"key": str(k), "url": v})
                else: walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    walk(obj); return found


def okx_probe():
    results = []; successful_domain = None
    for domain in OKX_DOMAINS:
        any_response = False
        print("  OKX domain probe:", domain)
        for module in OKX_MODULE_CANDIDATES:
            params = {"module": module, "instType": "SWAP", "dateAggrType": "1D",
                      "begin": OKX_BEGIN_MS, "end": OKX_END_MS, "instIdList": "BTC-USDT-SWAP"}
            url = domain + OKX_PATH + "?" + urlencode(params)
            item = {"domain": domain, "module": module, "request_url": url}
            try:
                req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json,*/*"})
                with urlopen(req, timeout=TIMEOUT) as r:
                    raw = r.read(5*1024*1024 + 1); item["http_status"] = getattr(r, "status", 200)
                if len(raw) > 5*1024*1024: raise RuntimeError("OKX metadata response too large")
                any_response = True
                obj = json.loads(raw.decode("utf-8", errors="replace"))
                item["code"] = obj.get("code") if isinstance(obj, dict) else None
                item["msg"] = obj.get("msg") if isinstance(obj, dict) else None
                data = obj.get("data") if isinstance(obj, dict) else None
                item["data_len"] = len(data) if isinstance(data, list) else None
                if isinstance(data, list) and data:
                    first = data[0]
                    item["first_record"] = {str(k): str(v)[:500] for k,v in first.items()} if isinstance(first, dict) else str(first)[:1500]
                item["urls_found"] = collect_urls(obj)
            except HTTPError as e:
                item["http_status"] = e.code
                try: item["error_body"] = e.read(4096).decode("utf-8", errors="replace")
                except Exception: pass
            except Exception as e:
                item["error"] = repr(e)
            results.append(item)
            print(f"    module {module}: HTTP {item.get('http_status','ERR')} code={item.get('code')} data={item.get('data_len')}")
            time.sleep(0.25)
        if any_response:
            successful_domain = domain; break
    return {"fixed_date": QUAL_DATE, "inst_type": "SWAP", "inst_id": "BTC-USDT-SWAP",
            "begin_ms": OKX_BEGIN_MS, "end_ms": OKX_END_MS, "bulk_download_followed": False,
            "successful_domain": successful_domain, "results": results}


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    free = free_mb()
    print("="*78)
    print("SC001-DATA-Q001 FREE MULTI-VENUE QUALIFICATION v0.1")
    print("Fixed date:", QUAL_DATE, "UTC")
    print("Strategy/P&L calculations: NO")
    print("Bulk OKX L2 download: NO")
    print("="*78)
    print(f"Free storage: {free:,.0f} MB")
    if free < HARD_MIN_FREE_MB:
        raise RuntimeError(f"Only {free:.0f} MB free; need at least {HARD_MIN_FREE_MB} MB safety headroom")
    if free < RECOMMENDED_FREE_MB:
        print(f"WARNING: below recommended {RECOMMENDED_FREE_MB} MB free; safety cap active")

    report = {"version": VERSION, "fixed_qualification_date": QUAL_DATE, "started_at_utc": now_iso(),
              "strategy_pnl_calculated": False, "free_storage_mb_start": free,
              "binance": {}, "bybit": {}, "okx": {}}
    atomic_json(REPORT, report)

    print("\n[1/3] Binance qualification")
    for spec in BINANCE_ITEMS:
        print("  ", spec["name"])
        item = {"url": spec["url"], "checksum_url": spec["checksum_url"], "status": "STARTED"}
        report["binance"][spec["name"]] = item; atomic_json(REPORT, report)
        try:
            path = OUTDIR / spec["filename"]
            dl = download_limited(spec["url"], path)
            expected, checksum_name = parse_checksum(fetch_text(spec["checksum_url"]))
            actual = sha256_file(path)
            inspect = inspect_zip_csv(path, spec.get("expected_interval_ms"))
            item.update({"status": "PASS" if expected and actual == expected else "CHECKSUM_FAIL",
                         "file": str(path), "bytes": path.stat().st_size, "sha256": actual,
                         "checksum_expected": expected, "checksum_filename": checksum_name,
                         "checksum_match": bool(expected and actual == expected), "download": dl,
                         "inspection": inspect})
        except Exception as e:
            item.update({"status": "FAIL", "error": repr(e)})
        atomic_json(REPORT, report)
        print("    status:", item["status"], "size MB:", round(item.get("bytes",0)/(1024*1024),2))

    print("\n[2/3] Bybit qualification")
    b = {"url": BYBIT_ITEM["url"], "status": "STARTED"}; report["bybit"] = b; atomic_json(REPORT, report)
    try:
        path = OUTDIR / BYBIT_ITEM["filename"]
        dl = download_limited(BYBIT_ITEM["url"], path)
        inspect = inspect_gzip_csv(path)
        b.update({"status": "PASS" if inspect.get("valid_gzip") and inspect.get("data_rows",0)>0 else "FAIL",
                  "file": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path),
                  "download": dl, "inspection": inspect})
    except Exception as e:
        b.update({"status": "FAIL", "error": repr(e)})
    atomic_json(REPORT, report)
    print("    status:", b["status"], "size MB:", round(b.get("bytes",0)/(1024*1024),2))

    print("\n[3/3] OKX public historical-data metadata probe")
    try:
        probe = okx_probe(); atomic_json(OKX_PROBE, probe)
        useful = [r for r in probe["results"] if str(r.get("code")) == "0" and (r.get("data_len") or 0) > 0]
        report["okx"] = {"status": "PASS" if useful else "NEEDS_REVIEW",
                         "successful_domain": probe.get("successful_domain"),
                         "useful_module_responses": len(useful), "probe_file": str(OKX_PROBE),
                         "bulk_download_followed": False}
    except Exception as e:
        report["okx"] = {"status": "FAIL", "error": repr(e), "bulk_download_followed": False}
    atomic_json(REPORT, report); print("    status:", report["okx"]["status"])

    report["finished_at_utc"] = now_iso(); report["free_storage_mb_end"] = free_mb()
    report["overall_status"] = "QUALIFICATION_COMPLETE" if report["binance"] and report["bybit"].get("status") == "PASS" else "QUALIFICATION_PARTIAL"
    atomic_json(REPORT, report)

    lines = ["# SC001-DATA-Q001 — Free Multi-Venue Qualification", "",
             f"- Fixed date: `{QUAL_DATE} UTC`", f"- Overall: `{report['overall_status']}`",
             "- Strategy/P&L calculated: **NO**", "- OKX bulk L2 downloaded: **NO**", "", "## Binance"]
    for name,item in report["binance"].items():
        ins = item.get("inspection",{})
        lines.append(f"- {name}: `{item.get('status')}`; {item.get('bytes',0)/(1024*1024):.2f} MB; rows={ins.get('data_rows')}; checksum={item.get('checksum_match')}")
    lines += ["", "## Bybit", f"- status: `{report['bybit'].get('status')}`",
              f"- compressed size: {report['bybit'].get('bytes',0)/(1024*1024):.2f} MB",
              f"- rows: {report['bybit'].get('inspection',{}).get('data_rows')}",
              f"- detected header: {report['bybit'].get('inspection',{}).get('header')}", "",
              "## OKX", f"- status: `{report['okx'].get('status')}`",
              f"- responding domain: {report['okx'].get('successful_domain')}",
              f"- useful module responses: {report['okx'].get('useful_module_responses')}",
              "- bulk L2 files were intentionally not followed/downloaded in Q001.", "", "## Next",
              "Upload the report, summary, and OKX probe JSON to ChatGPT. The bulk collector calendar will be frozen only after this qualification review."]
    atomic_text(SUMMARY, "\n".join(lines)+"\n")

    print("\n"+"="*78); print("SC001-DATA-Q001 COMPLETE"); print("="*78)
    print("Report:", REPORT); print("Summary:", SUMMARY); print("OKX probe:", OKX_PROBE)
    print("\nUpload these 3 files to ChatGPT:")
    print("1) sc001_data_q001_report.json")
    print("2) sc001_data_q001_summary.md")
    print("3) sc001_data_q001_okx_probe.json")
    input("\nPress Enter to finish...")


if __name__ == "__main__":
    main()
