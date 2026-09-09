"""Android/Pydroid manifest collector for Binance USD-M historical universe.

Purpose
-------
Build a point-in-time archive inventory for R002 without relying on today's
active-symbol list. The Binance public-data S3 archive can contain historical
and delisted contracts, so the archive index is used as the source of truth.

This script does NOT download market candles yet. It only inventories available
monthly 1d kline ZIP files for USD-M futures and writes two compact CSV files:

1) r002_binance_um_1d_manifest.csv
   One row per symbol-month archive.
2) r002_binance_um_symbol_summary.csv
   One row per symbol with first/last archived month and month count.

Standard library only; suitable for Pydroid 3.
"""

import csv
import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
PREFIX = "data/futures/um/monthly/klines/"
INTERVAL = "1d"

DOWNLOAD = "/storage/emulated/0/Download"
MANIFEST_OUT = os.path.join(DOWNLOAD, "r002_binance_um_1d_manifest.csv")
SUMMARY_OUT = os.path.join(DOWNLOAD, "r002_binance_um_symbol_summary.csv")

MAX_RETRIES = 4
RETRY_BASE_SECONDS = 2
REQUEST_TIMEOUT = 60
PAGE_SLEEP = 0.15


def fetch_xml(continuation_token=None):
    params = {
        "list-type": "2",
        "prefix": PREFIX,
        "max-keys": "1000",
    }
    if continuation_token:
        params["continuation-token"] = continuation_token

    url = S3 + "?" + urlencode(params)
    req = Request(url, headers={"User-Agent": "r002-historical-universe/0.1"})

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                return resp.read()
        except (HTTPError, URLError, TimeoutError, OSError) as e:
            last_error = repr(e)
            print(f"  request attempt {attempt}/{MAX_RETRIES} failed: {last_error}")
            if attempt < MAX_RETRIES:
                wait = RETRY_BASE_SECONDS * attempt
                print("  retry in", wait, "seconds...")
                time.sleep(wait)

    raise RuntimeError(f"S3 listing failed after retries: {last_error}")


def strip_ns(tag):
    return tag.split("}", 1)[-1]


def parse_page(xml_bytes):
    root = ET.fromstring(xml_bytes)
    keys = []
    next_token = None
    truncated = False

    for child in root:
        name = strip_ns(child.tag)
        if name == "Contents":
            key = None
            for x in child:
                if strip_ns(x.tag) == "Key":
                    key = x.text
                    break
            if key:
                keys.append(key)
        elif name == "NextContinuationToken":
            next_token = child.text
        elif name == "IsTruncated":
            truncated = (child.text or "").lower() == "true"

    return keys, next_token, truncated


def parse_archive_key(key):
    # Expected:
    # data/futures/um/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2020-01.zip
    if not key.endswith(".zip"):
        return None

    parts = key.split("/")
    if len(parts) != 8:
        return None
    if parts[0:5] != ["data", "futures", "um", "monthly", "klines"]:
        return None

    symbol = parts[5]
    interval = parts[6]
    filename = parts[7]

    if interval != INTERVAL:
        return None
    if not symbol.endswith("USDT"):
        return None

    prefix = f"{symbol}-{INTERVAL}-"
    if not filename.startswith(prefix) or not filename.endswith(".zip"):
        return None

    month = filename[len(prefix):-4]
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


def write_atomic(path, fieldnames, rows):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def main():
    os.makedirs(DOWNLOAD, exist_ok=True)

    print("=" * 70)
    print("R002 BINANCE HISTORICAL UNIVERSE MANIFEST")
    print("Source: Binance public USD-M monthly 1d archive index")
    print("Goal: include historical/delisted symbols, not only today's survivors")
    print("=" * 70)

    records = []
    token = None
    page = 0
    total_keys = 0

    while True:
        page += 1
        print(f"Page {page}...")
        xml_bytes = fetch_xml(token)
        keys, next_token, truncated = parse_page(xml_bytes)
        total_keys += len(keys)

        accepted = 0
        for key in keys:
            row = parse_archive_key(key)
            if row is not None:
                records.append(row)
                accepted += 1

        print("  keys:", len(keys), "accepted 1d USDT archives:", accepted)

        if not truncated:
            break
        if not next_token:
            raise RuntimeError("S3 says truncated but returned no continuation token")

        token = next_token
        time.sleep(PAGE_SLEEP)

    if not records:
        raise RuntimeError("No historical 1d USDT archive records found")

    # Deduplicate defensively.
    dedup = {}
    for r in records:
        dedup[(r["symbol"], r["month"])] = r
    records = sorted(dedup.values(), key=lambda r: (r["symbol"], r["month"]))

    summary = {}
    for r in records:
        s = summary.setdefault(r["symbol"], [])
        s.append(r["month"])

    latest_global_month = max(r["month"] for r in records)
    summary_rows = []
    for symbol in sorted(summary):
        months = sorted(set(summary[symbol]))
        summary_rows.append({
            "symbol": symbol,
            "first_month": months[0],
            "last_month": months[-1],
            "months_count": len(months),
            "present_in_latest_archive_month": int(months[-1] == latest_global_month),
        })

    write_atomic(
        MANIFEST_OUT,
        ["symbol", "month", "archive_key", "archive_url"],
        records,
    )
    write_atomic(
        SUMMARY_OUT,
        ["symbol", "first_month", "last_month", "months_count", "present_in_latest_archive_month"],
        summary_rows,
    )

    likely_historical = [r for r in summary_rows if not r["present_in_latest_archive_month"]]

    print()
    print("=" * 70)
    print("FINISHED")
    print("=" * 70)
    print("S3 keys scanned:", total_keys)
    print("Unique symbol-month 1d archives:", len(records))
    print("Unique USDT symbols:", len(summary_rows))
    print("Latest archive month:", latest_global_month)
    print("Symbols absent from latest archive month:", len(likely_historical))
    print("Manifest:", MANIFEST_OUT)
    print("Summary:", SUMMARY_OUT)
    print()
    print("Upload BOTH CSV files to ChatGPT for point-in-time universe design.")
    input("Press Enter to finish...")


if __name__ == "__main__":
    main()
