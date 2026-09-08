"""Android/Pydroid cross-asset daily collector for R002 SMA120 robustness.

Collects daily USDT linear-perpetual klines from Bybit V5 for a small fixed
cross-asset panel. Uses only fully closed UTC candles. The same SMA120 rule will
later be applied to every asset without per-asset tuning.

Research note: this is a current-large-liquid panel, so it is useful for
cross-market robustness but does not remove survivorship bias. A historical
point-in-time universe is a later, separate test.
"""

import csv
import json
import os
import time
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE = "https://api.bybit.com/v5/market/kline"
DOWNLOAD = "/storage/emulated/0/Download"
OUTPUT = os.path.join(DOWNLOAD, "r002_bybit_cross_asset_daily.csv")

CATEGORY = "linear"
INTERVAL = "D"
SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "LTCUSDT",
    "ADAUSDT",
    "BNBUSDT",
]

START = datetime(2019, 1, 1, tzinfo=timezone.utc)
LIMIT = 1000
MAX_RETRIES = 3
RETRY_BASE_SECONDS = 2
SLEEP_BETWEEN_PAGES = 0.4
SLEEP_BETWEEN_SYMBOLS = 1.0

FIELDS = [
    "symbol",
    "start_time_ms",
    "date_utc",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "turnover",
]


def ms(dt):
    return int(dt.timestamp() * 1000)


def last_closed_utc_day_start():
    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    return today_start - timedelta(days=1)


def fetch_page(symbol, start_ms, end_ms):
    params = {
        "category": CATEGORY,
        "symbol": symbol,
        "interval": INTERVAL,
        "start": start_ms,
        "end": end_ms,
        "limit": LIMIT,
    }
    url = BASE + "?" + urlencode(params)
    req = Request(url, headers={"User-Agent": "r002-cross-asset-research/0.1"})
    with urlopen(req, timeout=60) as resp:
        obj = json.loads(resp.read().decode("utf-8"))
    if obj.get("retCode") != 0:
        raise RuntimeError(f"Bybit API error for {symbol}: {obj}")
    return obj.get("result", {}).get("list", [])


def collect_symbol(symbol, end_dt):
    start_floor_ms = ms(START)
    end_ms = ms(end_dt)
    collected = {}
    page = 0

    while end_ms >= start_floor_ms:
        page += 1
        window_start_ms = max(start_floor_ms, end_ms - 999 * 86400000)
        print(
            f"  Page {page}: "
            f"{datetime.fromtimestamp(window_start_ms/1000, tz=timezone.utc).date()} -> "
            f"{datetime.fromtimestamp(end_ms/1000, tz=timezone.utc).date()}"
        )

        rows = None
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                rows = fetch_page(symbol, window_start_ms, end_ms)
                break
            except (HTTPError, URLError, TimeoutError, OSError, RuntimeError) as e:
                last_error = repr(e)
                print(f"    attempt {attempt}/{MAX_RETRIES} failed: {last_error}")
                if attempt < MAX_RETRIES:
                    wait = RETRY_BASE_SECONDS * attempt
                    print("    retry in", wait, "seconds...")
                    time.sleep(wait)

        if rows is None:
            raise RuntimeError(f"{symbol}: failed page after retries: {last_error}")
        if not rows:
            break

        valid_ts = []
        for r in rows:
            if len(r) < 7:
                continue
            ts = int(r[0])
            valid_ts.append(ts)
            if ts < start_floor_ms or ts > ms(end_dt):
                continue
            collected[ts] = {
                "symbol": symbol,
                "start_time_ms": ts,
                "date_utc": datetime.fromtimestamp(ts / 1000, tz=timezone.utc).date().isoformat(),
                "open": r[1],
                "high": r[2],
                "low": r[3],
                "close": r[4],
                "volume": r[5],
                "turnover": r[6],
            }

        if not valid_ts:
            break
        oldest = min(valid_ts)
        print("    rows received:", len(rows), "unique total:", len(collected))
        if oldest <= start_floor_ms:
            break
        end_ms = oldest - 1
        time.sleep(SLEEP_BETWEEN_PAGES)

    return collected


def main():
    os.makedirs(DOWNLOAD, exist_ok=True)
    end_dt = last_closed_utc_day_start()

    print("=" * 68)
    print("R002 CROSS-ASSET DAILY COLLECTOR")
    print("Category: linear USDT perpetual")
    print("Symbols:", ", ".join(SYMBOLS))
    print("Start request floor:", START.date())
    print("Last fully closed UTC candle:", end_dt.date())
    print("=" * 68)

    all_rows = []
    failures = []

    for i, symbol in enumerate(SYMBOLS, start=1):
        print()
        print(f"[{i}/{len(SYMBOLS)}] {symbol}")
        try:
            rows = collect_symbol(symbol, end_dt)
            if not rows:
                raise RuntimeError("no rows collected")
            first = rows[min(rows)]["date_utc"]
            last = rows[max(rows)]["date_utc"]
            print(f"  DONE: {len(rows)} rows, {first} -> {last}")
            all_rows.extend(rows[ts] for ts in sorted(rows))
        except Exception as e:
            failures.append((symbol, repr(e)))
            print("  FAILED:", repr(e))
        time.sleep(SLEEP_BETWEEN_SYMBOLS)

    if not all_rows:
        raise RuntimeError(f"No data collected. Failures: {failures}")

    tmp = OUTPUT + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for row in sorted(all_rows, key=lambda x: (x["symbol"], int(x["start_time_ms"]))):
            w.writerow(row)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, OUTPUT)

    print()
    print("=" * 68)
    print("FINISHED")
    print("=" * 68)
    print("Total rows:", len(all_rows))
    print("Output:", OUTPUT)
    print("Size: %.2f MB" % (os.path.getsize(OUTPUT) / (1024 * 1024)))
    if failures:
        print("Failures:")
        for item in failures:
            print(" ", item)
    else:
        print("All symbols collected successfully.")
    print()
    print("Upload r002_bybit_cross_asset_daily.csv to ChatGPT.")
    input("Press Enter to finish...")


if __name__ == "__main__":
    main()
