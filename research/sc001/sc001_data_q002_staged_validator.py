"""SC001-DATA-Q002 staged source qualification for Android/Pydroid.

Purpose:
- Revalidate the existing Q001 Binance aggTrades sample using the CORRECT timestamp column.
- Revalidate the existing Q001 Bybit tick-trades sample with streaming checks.
- Probe documented OKX public endpoints and the official historical-data page.
- Do NOT bulk-download historical OKX L2.
- Enforce strict storage/network safety caps.

Research-only. No strategy/P&L calculations.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import os
import re
import shutil
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

VERSION = "0.1"
STAGE = "SC001-DATA-Q002"

DOWNLOAD = Path("/storage/emulated/0/Download")
Q001 = DOWNLOAD / "SC001_DATA_Q001"
OUTDIR = DOWNLOAD / "SC001_DATA_Q002"
REPORT = OUTDIR / "sc001_data_q002_report.json"
SUMMARY = OUTDIR / "sc001_data_q002_summary.md"
OKX_REPORT = OUTDIR / "sc001_data_q002_okx_probe.json"

FIXED_DATE = "2025-01-15"
DAY_BEGIN_MS = 1736899200000
DAY_END_MS = 1736985600000

BINANCE_AGG = Q001 / "BTCUSDT-aggTrades-2025-01-15.zip"
BYBIT_TRADES = Q001 / "BTCUSDT2025-01-15.csv.gz"

USER_AGENT = "BotMarketplace-SC001-DATA-Q002/0.1"
TIMEOUT = 60
RETRIES = 3

# HARD STORAGE / DOWNLOAD SAFETY
# Decimal 2 GB, deliberately stricter than 2 GiB.
SESSION_DOWNLOAD_CAP_BYTES = 2_000_000_000
WORKSPACE_CAP_BYTES = 2_000_000_000
PER_FILE_CAP_BYTES = 512_000_000
MIN_FREE_RESERVE_BYTES = 4_000_000_000
MAX_JSON_BYTES = 4_000_000
MAX_HTML_BYTES = 2_000_000

downloaded_this_run = 0


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def safety_check(extra_bytes: int = 0):
    if extra_bytes < 0:
        raise ValueError("extra_bytes must be non-negative")

    ws = dir_size(OUTDIR)
    if ws + extra_bytes > WORKSPACE_CAP_BYTES:
        raise RuntimeError(
            f"Q002 workspace safety cap would be exceeded: "
            f"{ws + extra_bytes:,} > {WORKSPACE_CAP_BYTES:,} bytes"
        )

    global downloaded_this_run
    if downloaded_this_run + extra_bytes > SESSION_DOWNLOAD_CAP_BYTES:
        raise RuntimeError(
            f"Session download safety cap would be exceeded: "
            f"{downloaded_this_run + extra_bytes:,} > "
            f"{SESSION_DOWNLOAD_CAP_BYTES:,} bytes"
        )

    free = free_bytes()
    if free - extra_bytes < MIN_FREE_RESERVE_BYTES:
        raise RuntimeError(
            "Storage reserve protection triggered. "
            f"Free={free:,}, requested={extra_bytes:,}, "
            f"required reserve={MIN_FREE_RESERVE_BYTES:,} bytes"
        )


def atomic_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = text.encode("utf-8")
    safety_check(len(raw))
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("wb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def atomic_json(path: Path, obj):
    atomic_text(path, json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def request_bytes(url: str, max_bytes: int, accept: str = "*/*") -> tuple[bytes, dict]:
    """Small-response request only. Counts bytes toward the 2 GB session cap."""
    global downloaded_this_run

    if max_bytes > PER_FILE_CAP_BYTES:
        raise ValueError("Requested response cap exceeds per-file safety cap")

    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": accept,
                },
            )
            with urlopen(req, timeout=TIMEOUT) as resp:
                advertised = resp.headers.get("Content-Length")
                if advertised and advertised.isdigit():
                    adv = int(advertised)
                    if adv > max_bytes:
                        raise RuntimeError(
                            f"Advertised response {adv:,} exceeds local cap {max_bytes:,}"
                        )
                    safety_check(adv)

                raw = resp.read(max_bytes + 1)
                status = getattr(resp, "status", 200)
                headers = dict(resp.headers.items())

            if len(raw) > max_bytes:
                raise RuntimeError(
                    f"Response exceeded safety cap {max_bytes:,} bytes"
                )

            safety_check(len(raw))
            downloaded_this_run += len(raw)

            return raw, {
                "status": int(status),
                "bytes": len(raw),
                "headers": headers,
            }

        except HTTPError as e:
            body = e.read(min(max_bytes, 256_000))
            safety_check(len(body))
            downloaded_this_run += len(body)
            return body, {
                "status": int(e.code),
                "bytes": len(body),
                "http_error": True,
                "headers": dict(e.headers.items()) if e.headers else {},
            }
        except (URLError, TimeoutError, OSError, RuntimeError) as e:
            last = repr(e)
            if attempt < RETRIES:
                time.sleep(attempt * 2)

    raise RuntimeError(f"Request failed: {url} :: {last}")


def request_json(url: str):
    raw, meta = request_bytes(url, MAX_JSON_BYTES, "application/json,*/*")
    text = raw.decode("utf-8", errors="replace")
    meta["preview"] = text[:500]
    try:
        obj = json.loads(text)
        meta["json_ok"] = True
        return obj, meta
    except Exception:
        meta["json_ok"] = False
        return None, meta


def validate_binance_aggtrades(path: Path):
    if not path.exists():
        return {"status": "MISSING", "file": str(path)}

    result = {
        "status": "RUNNING",
        "file": str(path),
        "compressed_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }

    with zipfile.ZipFile(path, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            result.update({"status": "FAIL", "reason": f"bad zip member: {bad}"})
            return result

        names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not names:
            result.update({"status": "FAIL", "reason": "no CSV member"})
            return result

        data_rows = 0
        invalid_rows = 0
        out_of_day = 0
        time_nonmono = 0
        agg_id_nonmono = 0
        agg_id_gaps = 0
        same_timestamp_adjacent = 0
        first_ts = last_ts = None
        first_id = last_id = None
        header = None

        with zf.open(names[0], "r") as raw:
            text = io.TextIOWrapper(
                raw, encoding="utf-8", errors="replace", newline=""
            )
            reader = csv.reader(text)

            for idx, row in enumerate(reader):
                if idx == 0:
                    header = row
                    if row and str(row[0]).strip().lower() == "agg_trade_id":
                        continue

                if len(row) < 7:
                    invalid_rows += 1
                    continue

                try:
                    agg_id = int(row[0])
                    price = float(row[1])
                    qty = float(row[2])
                    ts = int(row[5])  # CORRECT Binance USD-M aggTrades timestamp
                except Exception:
                    invalid_rows += 1
                    continue

                if price <= 0 or qty <= 0:
                    invalid_rows += 1
                    continue

                data_rows += 1

                if first_ts is None:
                    first_ts = ts
                    first_id = agg_id

                if not (DAY_BEGIN_MS <= ts < DAY_END_MS):
                    out_of_day += 1

                if last_ts is not None:
                    if ts < last_ts:
                        time_nonmono += 1
                    elif ts == last_ts:
                        same_timestamp_adjacent += 1

                if last_id is not None:
                    if agg_id <= last_id:
                        agg_id_nonmono += 1
                    elif agg_id != last_id + 1:
                        agg_id_gaps += 1

                last_ts = ts
                last_id = agg_id

                if data_rows % 500_000 == 0:
                    print(f"  Binance aggTrades checked: {data_rows:,} rows")

    result.update(
        {
            "status": "PASS"
            if invalid_rows == 0
            and out_of_day == 0
            and time_nonmono == 0
            and agg_id_nonmono == 0
            else "REVIEW",
            "header": header,
            "data_rows": data_rows,
            "invalid_rows": invalid_rows,
            "out_of_fixed_day_rows": out_of_day,
            "timestamp_column": "transact_time",
            "first_timestamp_ms": first_ts,
            "last_timestamp_ms": last_ts,
            "timestamp_nonmonotonic_rows": time_nonmono,
            "same_timestamp_adjacent_pairs": same_timestamp_adjacent,
            "first_agg_trade_id": first_id,
            "last_agg_trade_id": last_id,
            "agg_trade_id_nonmonotonic_rows": agg_id_nonmono,
            "agg_trade_id_gap_count": agg_id_gaps,
        }
    )
    return result


def validate_bybit_trades(path: Path):
    if not path.exists():
        return {"status": "MISSING", "file": str(path)}

    result = {
        "status": "RUNNING",
        "file": str(path),
        "compressed_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }

    data_rows = 0
    invalid_rows = 0
    out_of_day = 0
    time_nonmono = 0
    same_timestamp_adjacent = 0
    invalid_side = 0
    first_us = last_us = None
    header = None

    begin_us = DAY_BEGIN_MS * 1000
    end_us = DAY_END_MS * 1000

    with gzip.open(
        path, "rt", encoding="utf-8", errors="replace", newline=""
    ) as f:
        reader = csv.reader(f)
        for idx, row in enumerate(reader):
            if idx == 0:
                header = row
                if row and str(row[0]).strip().lower() == "timestamp":
                    continue

            if len(row) < 5:
                invalid_rows += 1
                continue

            try:
                ts_us = int(round(float(row[0]) * 1_000_000))
                side = str(row[2]).strip()
                size = float(row[3])
                price = float(row[4])
            except Exception:
                invalid_rows += 1
                continue

            if size <= 0 or price <= 0:
                invalid_rows += 1
                continue

            if side not in ("Buy", "Sell"):
                invalid_side += 1

            data_rows += 1

            if first_us is None:
                first_us = ts_us

            if not (begin_us <= ts_us < end_us):
                out_of_day += 1

            if last_us is not None:
                if ts_us < last_us:
                    time_nonmono += 1
                elif ts_us == last_us:
                    same_timestamp_adjacent += 1

            last_us = ts_us

            if data_rows % 500_000 == 0:
                print(f"  Bybit trades checked: {data_rows:,} rows")

    result.update(
        {
            "status": "PASS"
            if invalid_rows == 0
            and invalid_side == 0
            and out_of_day == 0
            and time_nonmono == 0
            else "REVIEW",
            "header": header,
            "data_rows": data_rows,
            "invalid_rows": invalid_rows,
            "invalid_side_rows": invalid_side,
            "out_of_fixed_day_rows": out_of_day,
            "timestamp_unit": "seconds with fractional sub-second precision",
            "first_timestamp_us": first_us,
            "last_timestamp_us": last_us,
            "timestamp_nonmonotonic_rows": time_nonmono,
            "same_timestamp_adjacent_pairs": same_timestamp_adjacent,
        }
    )
    return result


def okx_probe_domain(domain: str):
    out = {
        "domain": domain,
        "fixed_date": FIXED_DATE,
        "requests": [],
    }

    def add(name, path, params=None):
        url = domain + path
        if params:
            url += "?" + urlencode(params)
        obj, meta = request_json(url)
        rec = {"name": name, "url": url, "meta": meta}
        if isinstance(obj, dict):
            rec["code"] = obj.get("code")
            rec["msg"] = obj.get("msg")
            data = obj.get("data")
            rec["data_count"] = len(data) if isinstance(data, list) else None
            if isinstance(data, list) and data:
                rec["data_preview"] = data[:2]
        out["requests"].append(rec)
        return obj, rec

    # Documented historical 1m candles around the fixed date.
    candles, candles_rec = add(
        "history_candles_fixed_date",
        "/api/v5/market/history-candles",
        {
            "instId": "BTC-USDT-SWAP",
            "bar": "1m",
            "after": str(DAY_END_MS),
            "limit": "100",
        },
    )
    if isinstance(candles, dict) and candles.get("code") == "0":
        rows = candles.get("data") or []
        in_day = 0
        for r in rows:
            try:
                ts = int(r[0])
                if DAY_BEGIN_MS <= ts < DAY_END_MS:
                    in_day += 1
            except Exception:
                pass
        candles_rec["fixed_day_rows_returned"] = in_day

    # Public recent historical trades: documented as last 3 months only.
    add(
        "history_trades_recent_schema_only",
        "/api/v5/market/history-trades",
        {
            "instId": "BTC-USDT-SWAP",
            "type": "2",
            "limit": "100",
        },
    )

    # Current 5-level book: schema/connectivity only, NOT historical evidence.
    add(
        "current_books_schema_only",
        "/api/v5/market/books",
        {"instId": "BTC-USDT-SWAP", "sz": "5"},
    )

    # Correct the Q001 mistake: named modules rather than numeric values.
    for module in ("volume", "openInterest", "tradeCount"):
        add(
            f"market_data_history_{module}",
            "/api/v5/public/market-data-history",
            {
                "module": module,
                "instType": "SWAP",
                "dateAggrType": "1D",
                "begin": str(DAY_BEGIN_MS),
                "end": str(DAY_END_MS),
                "instIdList": "BTC-USDT-SWAP",
            },
        )
        time.sleep(0.35)

    return out


def probe_okx_historical_page():
    urls = [
        "https://www.okx.com/en-eu/historical-data",
        "https://www.okx.com/en-us/historical-data",
        "https://www.okx.com/historical-data",
    ]
    out = []

    for url in urls:
        try:
            raw, meta = request_bytes(url, MAX_HTML_BYTES, "text/html,*/*")
            text = raw.decode("utf-8", errors="replace")

            # Discovery only. DO NOT FOLLOW any bulk file URL.
            found = sorted(
                set(
                    re.findall(
                        r'https?://[^"\'< >\s]+'.replace(" ", ""),
                        text,
                        flags=re.IGNORECASE,
                    )
                )
            )
            candidates = [
                u
                for u in found
                if any(
                    k in u.lower()
                    for k in (
                        "static.okx",
                        "traderecord",
                        "orderbook",
                        ".zip",
                        ".gz",
                        ".tar",
                    )
                )
            ][:100]

            out.append(
                {
                    "url": url,
                    "status": meta.get("status"),
                    "bytes": len(raw),
                    "contains_trade_history_text": "trade history" in text.lower(),
                    "contains_order_book_text": "order book" in text.lower(),
                    "candidate_bulk_urls_found_but_not_followed": candidates,
                }
            )
        except Exception as e:
            out.append({"url": url, "error": repr(e)})

    return out


def write_summary(report):
    b = report["local_validation"]["binance_aggtrades"]
    y = report["local_validation"]["bybit_trades"]
    okx = report["okx"]

    lines = [
        "# SC001-DATA-Q002 — Validation + OKX Probe",
        "",
        f"- Fixed historical reference date: `{FIXED_DATE} UTC`",
        "- Strategy/P&L calculated: **NO**",
        "- Bulk OKX L2 downloaded: **NO**",
        f"- Hard session download cap: **{SESSION_DOWNLOAD_CAP_BYTES/1e9:.2f} GB**",
        f"- Hard Q002 workspace cap: **{WORKSPACE_CAP_BYTES/1e9:.2f} GB**",
        f"- Minimum free-storage reserve: **{MIN_FREE_RESERVE_BYTES/1e9:.2f} GB**",
        "",
        "## Existing Q001 samples revalidated",
        f"- Binance aggTrades: **{b.get('status')}**; rows={b.get('data_rows')}; "
        f"timestamp column={b.get('timestamp_column')}; "
        f"non-monotonic timestamps={b.get('timestamp_nonmonotonic_rows')}; "
        f"out-of-day rows={b.get('out_of_fixed_day_rows')}",
        f"- Bybit trades: **{y.get('status')}**; rows={y.get('data_rows')}; "
        f"non-monotonic timestamps={y.get('timestamp_nonmonotonic_rows')}; "
        f"out-of-day rows={y.get('out_of_fixed_day_rows')}",
        "",
        "## OKX",
    ]

    for d in okx["domains"]:
        lines.append(f"- Domain: `{d['domain']}`")
        for r in d["requests"]:
            lines.append(
                f"  - {r['name']}: HTTP {r['meta'].get('status')}, "
                f"code={r.get('code')}, rows={r.get('data_count')}"
            )

    lines += [
        "",
        "## Safety",
        f"- Network bytes downloaded by Q002 probes: {report['safety']['downloaded_this_run_bytes']:,}",
        f"- Q002 workspace bytes at finish: {report['safety']['workspace_bytes_end']:,}",
        "- No discovered bulk OKX archive URL was automatically followed.",
        "",
        "## Next decision",
        "Use this report to freeze the first staged bulk calendar. "
        "Do not start multi-year tick/L2 download before reviewing actual source behavior and size.",
        "",
    ]
    atomic_text(SUMMARY, "\n".join(lines))


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    safety_check()

    print("=" * 78)
    print("SC001-DATA-Q002 — STAGED VALIDATION / OKX PROBE v0.1")
    print("Strategy/P&L: NO")
    print("Bulk L2 download: NO")
    print("Hard session download cap: 2.00 GB")
    print("Hard Q002 workspace cap: 2.00 GB")
    print("Minimum free reserve: 4.00 GB")
    print("=" * 78)

    report = {
        "stage": STAGE,
        "version": VERSION,
        "fixed_date": FIXED_DATE,
        "started_at_utc": now_iso(),
        "strategy_pnl_calculated": False,
        "bulk_okx_l2_downloaded": False,
        "safety": {
            "session_download_cap_bytes": SESSION_DOWNLOAD_CAP_BYTES,
            "workspace_cap_bytes": WORKSPACE_CAP_BYTES,
            "per_file_cap_bytes": PER_FILE_CAP_BYTES,
            "minimum_free_reserve_bytes": MIN_FREE_RESERVE_BYTES,
            "free_bytes_start": free_bytes(),
            "downloaded_this_run_bytes": 0,
        },
        "local_validation": {},
        "okx": {},
    }

    print("\n[1/4] Revalidating Binance aggTrades with correct timestamp column...")
    report["local_validation"]["binance_aggtrades"] = validate_binance_aggtrades(
        BINANCE_AGG
    )

    print("\n[2/4] Revalidating Bybit tick trades...")
    report["local_validation"]["bybit_trades"] = validate_bybit_trades(
        BYBIT_TRADES
    )

    print("\n[3/4] Probing documented OKX endpoints...")
    domains = []
    for domain in ("https://www.okx.com", "https://us.okx.com"):
        try:
            domains.append(okx_probe_domain(domain))
        except Exception as e:
            domains.append({"domain": domain, "error": repr(e), "requests": []})
        time.sleep(1.0)

    print("\n[4/4] Inspecting official OKX historical-data pages without following bulk links...")
    pages = probe_okx_historical_page()

    report["okx"] = {
        "domains": domains,
        "historical_pages": pages,
        "bulk_links_followed": False,
    }

    report["finished_at_utc"] = now_iso()
    report["safety"]["downloaded_this_run_bytes"] = downloaded_this_run
    report["safety"]["workspace_bytes_end"] = dir_size(OUTDIR)
    report["safety"]["free_bytes_end"] = free_bytes()

    atomic_json(OKX_REPORT, report["okx"])
    atomic_json(REPORT, report)
    write_summary(report)

    print("\n" + "=" * 78)
    print("SC001-DATA-Q002 COMPLETE")
    print("=" * 78)
    print(
        "Binance aggTrades:",
        report["local_validation"]["binance_aggtrades"].get("status"),
    )
    print(
        "Bybit trades:",
        report["local_validation"]["bybit_trades"].get("status"),
    )
    print("Network bytes downloaded this run:", f"{downloaded_this_run:,}")
    print("Results:", OUTDIR)
    print("\nUpload these 3 files to ChatGPT:")
    print("1) sc001_data_q002_report.json")
    print("2) sc001_data_q002_summary.md")
    print("3) sc001_data_q002_okx_probe.json")


if __name__ == "__main__":
    main()
