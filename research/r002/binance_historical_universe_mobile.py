"""Fast resumable Android/Pydroid manifest collector for Binance USD-M 1d archives.

v0.2 architecture:
- discovers symbol directories using S3 delimiter="/" instead of scanning every archive key;
- lists only each symbol's 1d directory;
- processes symbols concurrently;
- writes one atomic shard per symbol, so Android/Pydroid interruption is recoverable;
- caches the discovered symbol list;
- rebuilds compact manifest + summary from shards at the end.

Standard library only.
"""

import csv
import json
import os
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
ROOT_PREFIX = "data/futures/um/monthly/klines/"
INTERVAL = "1d"

DOWNLOAD = "/storage/emulated/0/Download"
WORKDIR = os.path.join(DOWNLOAD, "r002_binance_um_manifest_parts")
SYMBOLS_CACHE = os.path.join(DOWNLOAD, "r002_binance_um_symbols.csv")
STATE_OUT = os.path.join(DOWNLOAD, "r002_binance_um_manifest_state.json")
MANIFEST_OUT = os.path.join(DOWNLOAD, "r002_binance_um_1d_manifest.csv")
SUMMARY_OUT = os.path.join(DOWNLOAD, "r002_binance_um_symbol_summary.csv")

MAX_RETRIES = 4
RETRY_BASE_SECONDS = 2
REQUEST_TIMEOUT = 45
MAX_WORKERS = 6

MANIFEST_FIELDS = ["symbol", "month", "archive_key", "archive_url"]


def strip_ns(tag):
    return tag.split("}", 1)[-1]


def request_xml(params):
    url = S3 + "?" + urlencode(params)
    req = Request(url, headers={"User-Agent": "r002-historical-universe/0.2"})

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                return resp.read()
        except (HTTPError, URLError, TimeoutError, OSError) as e:
            last_error = repr(e)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BASE_SECONDS * attempt)

    raise RuntimeError(f"S3 request failed after retries: {last_error}")


def parse_listing(xml_bytes):
    root = ET.fromstring(xml_bytes)
    keys = []
    prefixes = []
    next_token = None
    truncated = False

    for child in root:
        name = strip_ns(child.tag)

        if name == "Contents":
            for x in child:
                if strip_ns(x.tag) == "Key" and x.text:
                    keys.append(x.text)
                    break

        elif name == "CommonPrefixes":
            for x in child:
                if strip_ns(x.tag) == "Prefix" and x.text:
                    prefixes.append(x.text)
                    break

        elif name == "NextContinuationToken":
            next_token = child.text

        elif name == "IsTruncated":
            truncated = (child.text or "").lower() == "true"

    return keys, prefixes, next_token, truncated


def list_all(prefix, delimiter=None):
    token = None
    all_keys = []
    all_prefixes = []

    while True:
        params = {
            "list-type": "2",
            "prefix": prefix,
            "max-keys": "1000",
        }
        if delimiter is not None:
            params["delimiter"] = delimiter
        if token:
            params["continuation-token"] = token

        xml_bytes = request_xml(params)
        keys, prefixes, next_token, truncated = parse_listing(xml_bytes)
        all_keys.extend(keys)
        all_prefixes.extend(prefixes)

        if not truncated:
            break
        if not next_token:
            raise RuntimeError("S3 response is truncated but has no continuation token")
        token = next_token

    return all_keys, all_prefixes


def write_csv_atomic(path, fieldnames, rows):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def write_json_atomic(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def load_cached_symbols():
    if not os.path.exists(SYMBOLS_CACHE):
        return None

    try:
        with open(SYMBOLS_CACHE, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != ["symbol"]:
                return None
            symbols = sorted({
                row["symbol"].strip()
                for row in reader
                if row.get("symbol", "").strip().endswith("USDT")
            })
        return symbols or None
    except Exception:
        return None


def discover_symbols():
    cached = load_cached_symbols()
    if cached:
        print("Using cached symbol list:", len(cached))
        return cached

    print("Discovering symbol directories with S3 delimiter...")
    _, prefixes = list_all(ROOT_PREFIX, delimiter="/")

    symbols = []
    for prefix in prefixes:
        if not prefix.startswith(ROOT_PREFIX):
            continue
        tail = prefix[len(ROOT_PREFIX):].strip("/")
        if "/" in tail or not tail.endswith("USDT"):
            continue
        symbols.append(tail)

    symbols = sorted(set(symbols))
    if not symbols:
        raise RuntimeError("No USDT symbol directories found")

    write_csv_atomic(
        SYMBOLS_CACHE,
        ["symbol"],
        [{"symbol": s} for s in symbols],
    )
    print("Discovered USDT symbols:", len(symbols))
    print("Symbol cache saved:", SYMBOLS_CACHE)
    return symbols


def part_path(symbol):
    return os.path.join(WORKDIR, f"{symbol}.csv")


def valid_part(symbol):
    path = part_path(symbol)
    if not os.path.exists(path):
        return False

    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != MANIFEST_FIELDS:
                return False
            for row in reader:
                if row.get("symbol") != symbol:
                    return False
        return True
    except Exception:
        return False


def parse_month_key(symbol, key):
    expected_prefix = f"{ROOT_PREFIX}{symbol}/{INTERVAL}/"
    if not key.startswith(expected_prefix) or not key.endswith(".zip"):
        return None

    filename = key.rsplit("/", 1)[-1]
    file_prefix = f"{symbol}-{INTERVAL}-"
    if not filename.startswith(file_prefix):
        return None

    month = filename[len(file_prefix):-4]
    try:
        datetime.strptime(month, "%Y-%m")
    except ValueError:
        return None

    return {
        "symbol": symbol,
        "month": month,
        "archive_key": key,
        "archive_url": "https://data.binance.vision/" + key,
    }


def collect_symbol(symbol):
    prefix = f"{ROOT_PREFIX}{symbol}/{INTERVAL}/"
    keys, _ = list_all(prefix)

    dedup = {}
    for key in keys:
        row = parse_month_key(symbol, key)
        if row is not None:
            dedup[row["month"]] = row

    rows = [dedup[m] for m in sorted(dedup)]
    return rows


def save_part(symbol, rows):
    write_csv_atomic(part_path(symbol), MANIFEST_FIELDS, rows)


def read_all_parts(symbols):
    records = []

    for symbol in symbols:
        if not valid_part(symbol):
            continue

        with open(part_path(symbol), "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append({
                    "symbol": row["symbol"],
                    "month": row["month"],
                    "archive_key": row["archive_key"],
                    "archive_url": row["archive_url"],
                })

    records.sort(key=lambda r: (r["symbol"], r["month"]))
    return records


def build_outputs(symbols):
    records = read_all_parts(symbols)
    if not records:
        raise RuntimeError("No monthly 1d archive records found in completed parts")

    write_csv_atomic(MANIFEST_OUT, MANIFEST_FIELDS, records)

    months_by_symbol = {}
    for row in records:
        months_by_symbol.setdefault(row["symbol"], []).append(row["month"])

    latest_global_month = max(row["month"] for row in records)
    summary_rows = []

    for symbol in sorted(months_by_symbol):
        months = sorted(set(months_by_symbol[symbol]))
        summary_rows.append({
            "symbol": symbol,
            "first_month": months[0],
            "last_month": months[-1],
            "months_count": len(months),
            "present_in_latest_archive_month": int(months[-1] == latest_global_month),
        })

    write_csv_atomic(
        SUMMARY_OUT,
        [
            "symbol",
            "first_month",
            "last_month",
            "months_count",
            "present_in_latest_archive_month",
        ],
        summary_rows,
    )

    historical = [
        row for row in summary_rows
        if row["present_in_latest_archive_month"] == 0
    ]
    return len(records), len(summary_rows), latest_global_month, len(historical)


def main():
    os.makedirs(DOWNLOAD, exist_ok=True)
    os.makedirs(WORKDIR, exist_ok=True)

    print("=" * 70)
    print("R002 BINANCE HISTORICAL UNIVERSE MANIFEST v0.2")
    print("FAST + RESUMABLE + CRASH-SAFE")
    print("=" * 70)

    symbols = discover_symbols()
    completed = [s for s in symbols if valid_part(s)]
    pending = [s for s in symbols if not valid_part(s)]

    state = {
        "version": "0.2",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "symbols_total": len(symbols),
        "completed": completed,
        "failed": {},
    }
    write_json_atomic(STATE_OUT, state)

    print("Symbols total:", len(symbols))
    print("Already completed:", len(completed))
    print("Pending:", len(pending))
    print("Workers:", MAX_WORKERS)
    print("Parts:", WORKDIR)
    print()

    completed_set = set(completed)

    if pending:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {pool.submit(collect_symbol, s): s for s in pending}

            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    rows = future.result()
                    save_part(symbol, rows)
                    completed_set.add(symbol)
                    print(
                        f"[{len(completed_set)}/{len(symbols)}] "
                        f"{symbol}: {len(rows)} month archives saved"
                    )
                    state["failed"].pop(symbol, None)
                except Exception as e:
                    msg = repr(e)
                    state["failed"][symbol] = msg
                    print(f"{symbol}: FAILED: {msg}")

                state["completed"] = sorted(completed_set)
                state["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
                write_json_atomic(STATE_OUT, state)

    completed_final = [s for s in symbols if valid_part(s)]
    missing_final = [s for s in symbols if not valid_part(s)]

    records_count, symbols_with_data, latest_month, historical_count = build_outputs(symbols)

    state["completed"] = completed_final
    state["missing"] = missing_final
    state["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    state["manifest_records"] = records_count
    state["symbols_with_1d_data"] = symbols_with_data
    state["latest_archive_month"] = latest_month
    write_json_atomic(STATE_OUT, state)

    print()
    print("=" * 70)
    print("FINISHED")
    print("=" * 70)
    print("Completed symbol shards:", len(completed_final), "/", len(symbols))
    print("Missing/failed symbols:", len(missing_final))
    print("Unique symbol-month archives:", records_count)
    print("Symbols with 1d data:", symbols_with_data)
    print("Latest archive month:", latest_month)
    print("Symbols absent from latest archive month:", historical_count)
    print("Manifest:", MANIFEST_OUT)
    print("Summary:", SUMMARY_OUT)
    print("State:", STATE_OUT)

    if missing_final:
        print()
        print("Some symbols failed. Run THIS SAME SAVED SCRIPT again.")
        print("Completed symbols will be skipped; only missing ones will retry.")

    print()
    print("Upload BOTH manifest and summary CSV files to ChatGPT.")
    input("Press Enter to finish...")


if __name__ == "__main__":
    main()
