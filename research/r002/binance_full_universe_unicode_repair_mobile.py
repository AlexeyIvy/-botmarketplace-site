"""Repair four Binance USD-M symbols whose archive URLs contain non-ASCII path characters.

Why this exists
---------------
urllib/http.client requires the HTTP request target to be ASCII. The manifest
stores human-readable Unicode paths for a few Binance symbols, so a raw Request
raises UnicodeEncodeError. This script percent-encodes only the URL path before
requesting it, stores repaired shards under ASCII-safe hashed filenames, and
rebuilds the full combined CSV from normal + repaired shards.

Standard library only; suitable for Pydroid 3.
"""

import csv
import hashlib
import io
import json
import os
import time
import zipfile
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

DOWNLOAD = "/storage/emulated/0/Download"
MANIFEST = os.path.join(DOWNLOAD, "r002_binance_um_1d_manifest.csv")
NORMAL_PARTS = os.path.join(DOWNLOAD, "r002_binance_full_universe_parts")
REPAIR_PARTS = os.path.join(DOWNLOAD, "r002_binance_full_universe_repair_parts")
OUTPUT = os.path.join(DOWNLOAD, "r002_binance_full_universe_daily.csv")
STATE = os.path.join(DOWNLOAD, "r002_binance_full_universe_state.json")

TARGETS = ["币安人生USDT", "我踏马来了USDT", "牛来USDT", "龙虾USDT"]
MAX_RETRIES = 5
RETRY_BASE_SECONDS = 2
REQUEST_TIMEOUT = 60

FIELDS = [
    "symbol", "open_time_ms", "date_utc", "open", "high", "low", "close",
    "volume", "close_time_ms", "quote_volume", "trades", "taker_buy_base",
    "taker_buy_quote", "source_month",
]


def safe_name(symbol):
    return "repair_" + hashlib.sha256(symbol.encode("utf-8")).hexdigest()[:16] + ".csv"


def normal_part_path(symbol):
    return os.path.join(NORMAL_PARTS, f"{symbol}.csv")


def repair_part_path(symbol):
    return os.path.join(REPAIR_PARTS, safe_name(symbol))


def ascii_url(url):
    """Percent-encode Unicode URL path while preserving separators and % escapes."""
    p = urlsplit(url)
    path = quote(p.path, safe="/%:@")
    query = quote(p.query, safe="=&;%:+,/?@") if p.query else ""
    return urlunsplit((p.scheme, p.netloc, path, query, p.fragment))


def write_json_atomic(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def write_csv_atomic(path, rows):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def validate_part_file(path, symbol):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return False, 0, "missing or empty"
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            r = csv.DictReader(f)
            if r.fieldnames != FIELDS:
                return False, 0, "wrong columns"
            count = 0
            last_ts = None
            for row in r:
                if row.get("symbol") != symbol:
                    return False, count, "wrong symbol"
                ts = int(row["open_time_ms"])
                if last_ts is not None and ts <= last_ts:
                    return False, count, "timestamps not strictly increasing"
                last_ts = ts
                count += 1
            if count < 1:
                return False, 0, "no rows"
            return True, count, ""
    except Exception as e:
        return False, 0, repr(e)


def normalize_timestamp_to_ms(value):
    ts = int(value)
    if ts > 10**14:
        ts //= 1000
    return ts


def download_bytes(url):
    encoded = ascii_url(url)
    req = Request(
        encoded,
        headers={
            "User-Agent": "r002-full-universe-repair/0.2",
            "Accept": "*/*",
        },
    )
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                return resp.read()
        except (HTTPError, URLError, TimeoutError, OSError) as e:
            last_error = repr(e)
            if attempt < MAX_RETRIES:
                wait = RETRY_BASE_SECONDS * attempt
                print(f"      request failed {attempt}/{MAX_RETRIES}; retry in {wait}s")
                time.sleep(wait)
    raise RuntimeError(f"Download failed after {MAX_RETRIES} attempts: {encoded} :: {last_error}")


def parse_zip(symbol, month, blob):
    rows = []
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not names:
            raise ValueError(f"{symbol} {month}: ZIP has no CSV")
        for name in names:
            with zf.open(name, "r") as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8")
                for cols in csv.reader(text):
                    if not cols or len(cols) < 11:
                        continue
                    try:
                        open_ts = normalize_timestamp_to_ms(cols[0])
                    except Exception:
                        continue
                    try:
                        close_ts = normalize_timestamp_to_ms(cols[6])
                    except Exception:
                        close_ts = None
                    try:
                        dt = datetime.fromtimestamp(open_ts / 1000, tz=timezone.utc)
                    except Exception:
                        continue
                    rows.append({
                        "symbol": symbol,
                        "open_time_ms": open_ts,
                        "date_utc": dt.date().isoformat(),
                        "open": cols[1],
                        "high": cols[2],
                        "low": cols[3],
                        "close": cols[4],
                        "volume": cols[5],
                        "close_time_ms": close_ts,
                        "quote_volume": cols[7] if len(cols) > 7 else "",
                        "trades": cols[8] if len(cols) > 8 else "",
                        "taker_buy_base": cols[9] if len(cols) > 9 else "",
                        "taker_buy_quote": cols[10] if len(cols) > 10 else "",
                        "source_month": month,
                    })
    return rows


def load_manifest():
    if not os.path.exists(MANIFEST):
        raise FileNotFoundError(f"Manifest not found: {MANIFEST}")
    by_symbol = {}
    seen = set()
    with open(MANIFEST, "r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        required = {"symbol", "month", "archive_url"}
        actual = set(r.fieldnames or [])
        if not required.issubset(actual):
            raise ValueError(f"Manifest missing columns: {sorted(required - actual)}")
        for row in r:
            symbol = row.get("symbol", "").strip()
            month = row.get("month", "").strip()
            url = row.get("archive_url", "").strip()
            if not symbol or not month or not url:
                continue
            key = (symbol, month)
            if key in seen:
                continue
            seen.add(key)
            by_symbol.setdefault(symbol, []).append({"month": month, "archive_url": url})
    for symbol in by_symbol:
        by_symbol[symbol].sort(key=lambda x: x["month"])
    missing_targets = [s for s in TARGETS if s not in by_symbol]
    if missing_targets:
        raise ValueError(f"Targets missing from manifest: {missing_targets}")
    return dict(sorted(by_symbol.items()))


def collect_target(symbol, archives):
    dedup = {}
    for idx, item in enumerate(archives, 1):
        month = item["month"]
        print(f"    {symbol}: {idx}/{len(archives)} {month}")
        blob = download_bytes(item["archive_url"])
        for row in parse_zip(symbol, month, blob):
            dedup[int(row["open_time_ms"])] = row
    rows = [dedup[k] for k in sorted(dedup)]
    if not rows:
        raise ValueError(f"{symbol}: zero parsed rows")
    return rows


def locate_part(symbol):
    normal = normal_part_path(symbol)
    ok, count, _ = validate_part_file(normal, symbol)
    if ok:
        return normal, count
    repair = repair_part_path(symbol)
    ok, count, _ = validate_part_file(repair, symbol)
    if ok:
        return repair, count
    return None, 0


def rebuild_combined(manifest):
    symbols = sorted(manifest)
    total_rows = 0
    included = 0
    missing = []
    tmp = OUTPUT + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as out:
        w = csv.DictWriter(out, fieldnames=FIELDS)
        w.writeheader()
        for idx, symbol in enumerate(symbols, 1):
            path, _ = locate_part(symbol)
            if path is None:
                missing.append(symbol)
                continue
            included += 1
            with open(path, "r", encoding="utf-8", newline="") as f:
                r = csv.DictReader(f)
                for row in r:
                    w.writerow({k: row.get(k, "") for k in FIELDS})
                    total_rows += 1
            if idx % 100 == 0 or idx == len(symbols):
                print(f"  combine {idx}/{len(symbols)} | symbols={included} | rows={total_rows}")
        out.flush()
        os.fsync(out.fileno())
    os.replace(tmp, OUTPUT)
    return total_rows, included, missing


def main():
    os.makedirs(DOWNLOAD, exist_ok=True)
    os.makedirs(NORMAL_PARTS, exist_ok=True)
    os.makedirs(REPAIR_PARTS, exist_ok=True)

    print("=" * 72)
    print("R002 UNICODE REPAIR v0.2")
    print("Fix: percent-encode Unicode Binance URL paths before HTTP request")
    print("=" * 72)

    manifest = load_manifest()
    failed = {}

    for symbol in TARGETS:
        print("\n" + "-" * 72)
        print("TARGET:", symbol)
        path, count = locate_part(symbol)
        if path is not None:
            print("  Already valid:", count, "rows |", os.path.basename(path))
            continue

        repair = repair_part_path(symbol)
        try:
            rows = collect_target(symbol, manifest[symbol])
            write_csv_atomic(repair, rows)
            ok, count, reason = validate_part_file(repair, symbol)
            if not ok:
                raise ValueError("post-write validation failed: " + reason)
            print("  SAVED:", count, "rows |", os.path.basename(repair))
        except Exception as e:
            failed[symbol] = repr(e)
            print("  FAILED:", repr(e))

    print("\n" + "=" * 72)
    print("REBUILDING FULL COMBINED CSV")
    print("=" * 72)
    total_rows, included, missing = rebuild_combined(manifest)

    state = {
        "version": "unicode-repair-0.2",
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_symbols": len(manifest),
        "manifest_archives": sum(len(v) for v in manifest.values()),
        "repair_targets": TARGETS,
        "failed_repair_targets": failed,
        "combined_symbols": included,
        "combined_rows": total_rows,
        "missing": missing,
        "output": OUTPUT,
    }
    write_json_atomic(STATE, state)

    print("\n" + "=" * 72)
    print("FINISHED")
    print("=" * 72)
    print("Combined symbols:", included, "/", len(manifest))
    print("Combined rows:", total_rows)
    print("Missing:", len(missing))
    if missing:
        print("Missing symbols:")
        for symbol in missing:
            print(" ", symbol)
    else:
        print("SUCCESS: full manifest universe is complete (864/864).")
    print("CSV:", OUTPUT)
    print("STATE:", STATE)
    input("\nPress Enter to finish...")


if __name__ == "__main__":
    main()
