"""Android/Pydroid downloader for R002 historical survivorship-bias subset.

Reads the previously created Binance USD-M 1d monthly manifest from Android
Download, filters to a fixed research subset, downloads only those monthly ZIP
archives, extracts daily klines, and writes one crash-safe shard per symbol.

Design goals:
- no full-universe bulk download;
- fixed pre-specified subset (historical/delisted + survivor controls);
- resumable after Android kills Pydroid;
- atomic per-symbol shards;
- retry/backoff on network errors;
- standard library only.

This collector does not run the strategy. It only builds the historical dataset
for later SMA120 / SMA120+ADX20 validation.
"""

import csv
import io
import json
import os
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DOWNLOAD = "/storage/emulated/0/Download"
MANIFEST = os.path.join(DOWNLOAD, "r002_binance_um_1d_manifest.csv")
WORKDIR = os.path.join(DOWNLOAD, "r002_binance_historical_subset_parts")
OUTPUT = os.path.join(DOWNLOAD, "r002_binance_historical_subset_daily.csv")
STATE = os.path.join(DOWNLOAD, "r002_binance_historical_subset_state.json")

MAX_WORKERS = 4
MAX_RETRIES = 4
RETRY_BASE_SECONDS = 2
REQUEST_TIMEOUT = 60

# Historical/non-survivor candidates: all symbols absent from the latest archive
# month with >= 12 archived months in the manifest snapshot collected 2026-09-09.
HISTORICAL_SYMBOLS = [
    "SXPUSDT",
    "EOSUSDT",
    "BTCSTUSDT",
    "MATICUSDT",
    "HNTUSDT",
    "SRMUSDT",
    "TOMOUSDT",
    "BTSUSDT",
    "AUDIOUSDT",
    "ANTUSDT",
    "GALUSDT",
    "AERGOUSDT",
    "FOOTBALLUSDT",
    "YFIIUSDT",
    "BLUEBIRDUSDT",
    "RNDRUSDT",
    "AKROUSDT",
    "LUNAUSDT",
    "BZRXUSDT",
    "DODOUSDT",
    "COCOSUSDT",
    "FRONTUSDT",
]

# Same current-large-liquid controls already used in our Bybit cross-asset work.
CONTROL_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "LTCUSDT",
    "ADAUSDT",
    "BNBUSDT",
]

SYMBOLS = HISTORICAL_SYMBOLS + CONTROL_SYMBOLS

FIELDS = [
    "symbol",
    "open_time_ms",
    "date_utc",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time_ms",
    "quote_volume",
    "trades",
    "taker_buy_base",
    "taker_buy_quote",
    "source_month",
]


def write_json_atomic(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


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


def part_path(symbol):
    return os.path.join(WORKDIR, f"{symbol}.csv")


def valid_part(symbol):
    path = part_path(symbol)
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return False
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            r = csv.DictReader(f)
            if r.fieldnames != FIELDS:
                return False
            count = 0
            last_ts = None
            for row in r:
                if row.get("symbol") != symbol:
                    return False
                ts = int(row["open_time_ms"])
                if last_ts is not None and ts <= last_ts:
                    return False
                last_ts = ts
                count += 1
            return count >= 120
    except Exception:
        return False


def load_manifest():
    if not os.path.exists(MANIFEST):
        raise FileNotFoundError(
            f"Manifest not found: {MANIFEST}. Put r002_binance_um_1d_manifest.csv in Download."
        )

    by_symbol = {s: [] for s in SYMBOLS}
    with open(MANIFEST, "r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        required = {"symbol", "month", "archive_url"}
        if not required.issubset(set(r.fieldnames or [])):
            raise ValueError(f"Manifest missing required columns: {required}")
        for row in r:
            symbol = row.get("symbol", "").strip()
            if symbol in by_symbol:
                by_symbol[symbol].append({
                    "symbol": symbol,
                    "month": row["month"].strip(),
                    "archive_url": row["archive_url"].strip(),
                })

    missing = [s for s, rows in by_symbol.items() if not rows]
    if missing:
        raise ValueError(f"Subset symbols missing from manifest: {missing}")

    for s in by_symbol:
        by_symbol[s].sort(key=lambda x: x["month"])
    return by_symbol


def download_bytes(url):
    req = Request(url, headers={"User-Agent": "r002-survivorship-research/0.1"})
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                return resp.read()
        except (HTTPError, URLError, TimeoutError, OSError) as e:
            last_error = repr(e)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BASE_SECONDS * attempt)
    raise RuntimeError(f"Download failed after retries: {url} :: {last_error}")


def parse_zip(symbol, month, blob):
    out = []
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not names:
            raise ValueError(f"{symbol} {month}: ZIP has no CSV")
        # Binance monthly kline archives normally contain one CSV.
        with zf.open(names[0], "r") as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8")
            reader = csv.reader(text)
            for cols in reader:
                if not cols:
                    continue
                # Some archive generations include a header row; skip it safely.
                try:
                    open_ts = int(cols[0])
                except Exception:
                    continue
                if len(cols) < 11:
                    continue

                # Binance introduced microsecond timestamps in some archives.
                # Normalize to milliseconds for a stable downstream schema.
                if open_ts > 10**14:
                    open_ts //= 1000

                try:
                    close_ts = int(cols[6])
                    if close_ts > 10**14:
                        close_ts //= 1000
                except Exception:
                    close_ts = None

                dt = datetime.fromtimestamp(open_ts / 1000, tz=timezone.utc)
                out.append({
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
    return out


def collect_symbol(symbol, archives):
    dedup = {}
    for idx, item in enumerate(archives, start=1):
        month = item["month"]
        blob = download_bytes(item["archive_url"])
        rows = parse_zip(symbol, month, blob)
        for row in rows:
            dedup[int(row["open_time_ms"])] = row
        if idx % 12 == 0 or idx == len(archives):
            print(f"    {symbol}: {idx}/{len(archives)} months downloaded")

    rows = [dedup[k] for k in sorted(dedup)]
    if len(rows) < 120:
        raise ValueError(f"{symbol}: only {len(rows)} daily rows")
    return rows


def rebuild_output(symbols):
    total = 0
    tmp = OUTPUT + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as out:
        w = csv.DictWriter(out, fieldnames=FIELDS)
        w.writeheader()
        for symbol in symbols:
            if not valid_part(symbol):
                continue
            with open(part_path(symbol), "r", encoding="utf-8", newline="") as f:
                r = csv.DictReader(f)
                for row in r:
                    w.writerow({k: row.get(k) for k in FIELDS})
                    total += 1
        out.flush()
        os.fsync(out.fileno())
    os.replace(tmp, OUTPUT)
    return total


def main():
    os.makedirs(DOWNLOAD, exist_ok=True)
    os.makedirs(WORKDIR, exist_ok=True)

    print("=" * 72)
    print("R002 BINANCE HISTORICAL SUBSET DOWNLOADER v0.1")
    print("Historical symbols:", len(HISTORICAL_SYMBOLS))
    print("Control symbols:", len(CONTROL_SYMBOLS))
    print("Total symbols:", len(SYMBOLS))
    print("Crash-safe / resumable: YES")
    print("=" * 72)

    manifest = load_manifest()

    completed = [s for s in SYMBOLS if valid_part(s)]
    pending = [s for s in SYMBOLS if not valid_part(s)]

    state = {
        "version": "0.1",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "historical_symbols": HISTORICAL_SYMBOLS,
        "control_symbols": CONTROL_SYMBOLS,
        "completed": completed,
        "failed": {},
    }
    write_json_atomic(STATE, state)

    print("Already completed:", len(completed), "/", len(SYMBOLS))
    print("Pending:", len(pending))
    print("Workers:", MAX_WORKERS)
    print("Parts:", WORKDIR)
    print()

    completed_set = set(completed)

    if pending:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {
                pool.submit(collect_symbol, symbol, manifest[symbol]): symbol
                for symbol in pending
            }
            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    rows = future.result()
                    write_csv_atomic(part_path(symbol), FIELDS, rows)
                    if not valid_part(symbol):
                        raise ValueError("post-write shard validation failed")
                    completed_set.add(symbol)
                    state["failed"].pop(symbol, None)
                    print(
                        f"[{len(completed_set)}/{len(SYMBOLS)}] {symbol}: "
                        f"{len(rows)} daily rows saved"
                    )
                except Exception as e:
                    state["failed"][symbol] = repr(e)
                    print(f"{symbol}: FAILED: {repr(e)}")

                state["completed"] = sorted(completed_set)
                state["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
                write_json_atomic(STATE, state)

    completed_final = [s for s in SYMBOLS if valid_part(s)]
    missing_final = [s for s in SYMBOLS if not valid_part(s)]
    total_rows = rebuild_output(SYMBOLS)

    state["completed"] = completed_final
    state["missing"] = missing_final
    state["combined_rows"] = total_rows
    state["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    write_json_atomic(STATE, state)

    print()
    print("=" * 72)
    print("FINISHED")
    print("=" * 72)
    print("Completed:", len(completed_final), "/", len(SYMBOLS))
    print("Missing/failed:", len(missing_final))
    print("Combined daily rows:", total_rows)
    print("Output:", OUTPUT)
    print("State:", STATE)
    print("Parts:", WORKDIR)
    if missing_final:
        print("Missing symbols:", ", ".join(missing_final))
        print("Run the SAME saved script again; completed shards will be skipped.")
    else:
        print("All subset symbols collected successfully.")
    print()
    print("Upload r002_binance_historical_subset_daily.csv to ChatGPT.")
    input("Press Enter to finish...")


if __name__ == "__main__":
    main()
