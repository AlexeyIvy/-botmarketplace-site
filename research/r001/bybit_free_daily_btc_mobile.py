"""Android/Pydroid collector for free daily BTC data from Bybit V5 API.

Purpose: provide backward-looking daily BTC returns for R001 E004-S IV/RV regime
research without buying market data.

Research-only. The script fetches daily BTCUSD inverse perpetual klines, which
have long history and are suitable as a BTC realised-volatility proxy. It writes
a compact CSV to Android Download.
"""

import csv
import json
import os
import time
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE = "https://api.bybit.com/v5/market/kline"
OUTPUT = "/storage/emulated/0/Download/r001_bybit_btcusd_daily_2019-09_to_2026-09.csv"

CATEGORY = "inverse"
SYMBOL = "BTCUSD"
INTERVAL = "D"

START = datetime(2019, 9, 1, tzinfo=timezone.utc)
END = datetime(2026, 9, 8, tzinfo=timezone.utc)

LIMIT = 1000
MAX_RETRIES = 3
RETRY_BASE_SECONDS = 2


def ms(dt):
    return int(dt.timestamp() * 1000)


def fetch_page(start_ms, end_ms):
    params = {
        "category": CATEGORY,
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "start": start_ms,
        "end": end_ms,
        "limit": LIMIT,
    }
    url = BASE + "?" + urlencode(params)
    req = Request(url, headers={"User-Agent": "r001-android-research/0.1"})
    with urlopen(req, timeout=60) as resp:
        obj = json.loads(resp.read().decode("utf-8"))
    if obj.get("retCode") != 0:
        raise RuntimeError(f"Bybit API error: {obj}")
    rows = obj.get("result", {}).get("list", [])
    return rows


def main():
    print("=" * 64)
    print("R001 FREE BYBIT DAILY BTC COLLECTOR")
    print("Instrument: BTCUSD inverse perpetual")
    print("Interval: daily")
    print("Purpose: RV20 / RV60 for IV-RV screening")
    print("=" * 64)

    # Bybit returns reverse chronological rows. We fetch backwards in chunks.
    end_ms = ms(END)
    start_floor_ms = ms(START)
    collected = {}

    page = 0

    while end_ms >= start_floor_ms:
        page += 1
        # A 1000-day request window stays within the API row limit.
        window_start_ms = max(start_floor_ms, end_ms - 999 * 86400000)

        print(f"Page {page}: {datetime.fromtimestamp(window_start_ms/1000, tz=timezone.utc).date()} -> {datetime.fromtimestamp(end_ms/1000, tz=timezone.utc).date()}")

        rows = None
        last_error = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                rows = fetch_page(window_start_ms, end_ms)
                break
            except (HTTPError, URLError, TimeoutError, OSError, RuntimeError) as e:
                last_error = repr(e)
                print(f"  attempt {attempt}/{MAX_RETRIES} failed: {last_error}")
                if attempt < MAX_RETRIES:
                    wait = RETRY_BASE_SECONDS * attempt
                    print("  retry in", wait, "seconds...")
                    time.sleep(wait)

        if rows is None:
            raise RuntimeError(f"Failed page after retries: {last_error}")

        if not rows:
            print("  no rows returned")
            break

        for r in rows:
            if len(r) < 7:
                continue
            ts = int(r[0])
            if ts < start_floor_ms or ts > ms(END):
                continue
            collected[ts] = {
                "start_time_ms": ts,
                "date_utc": datetime.fromtimestamp(ts / 1000, tz=timezone.utc).date().isoformat(),
                "open": r[1],
                "high": r[2],
                "low": r[3],
                "close": r[4],
                "volume": r[5],
                "turnover": r[6],
            }

        oldest = min(int(r[0]) for r in rows if len(r) >= 1)
        print("  rows received:", len(rows), "unique total:", len(collected))

        if oldest <= start_floor_ms:
            break

        # Next page ends just before the oldest returned candle.
        end_ms = oldest - 1
        time.sleep(0.5)

    if not collected:
        raise RuntimeError("No daily BTC data collected")

    fields = [
        "start_time_ms",
        "date_utc",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "turnover",
    ]

    tmp = OUTPUT + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for ts in sorted(collected):
            w.writerow(collected[ts])
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, OUTPUT)

    print()
    print("=" * 64)
    print("DONE")
    print("=" * 64)
    print("Daily rows:", len(collected))
    print("First date:", collected[min(collected)]["date_utc"])
    print("Last date:", collected[max(collected)]["date_utc"])
    print("Output:", OUTPUT)
    print("Size: %.2f MB" % (os.path.getsize(OUTPUT) / (1024 * 1024)))
    print()
    print("Upload this CSV to ChatGPT for the IV/RV screening stage.")
    input("Press Enter to finish...")


if __name__ == "__main__":
    main()
