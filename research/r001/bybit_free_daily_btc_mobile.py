"""Android/Pydroid collector for free daily BTC data from Bybit V5 API.

Purpose: provide backward-looking daily BTC returns for R001/R002 research
without buying market data.

Important integrity rule: the current UTC daily candle is never included because
it may be incomplete. The collector automatically stops at the most recent fully
closed UTC day.
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
OUTPUT = "/storage/emulated/0/Download/r001_bybit_btcusd_daily_2019-09_to_latest_closed.csv"

CATEGORY = "inverse"
SYMBOL = "BTCUSD"
INTERVAL = "D"

START = datetime(2019, 9, 1, tzinfo=timezone.utc)

LIMIT = 1000
MAX_RETRIES = 3
RETRY_BASE_SECONDS = 2
DAY_MS = 86400000


def latest_closed_day_start():
    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    return today_start - timedelta(days=1)


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
    req = Request(url, headers={"User-Agent": "r001-r002-android-research/0.2"})
    with urlopen(req, timeout=60) as resp:
        obj = json.loads(resp.read().decode("utf-8"))
    if obj.get("retCode") != 0:
        raise RuntimeError(f"Bybit API error: {obj}")
    return obj.get("result", {}).get("list", [])


def main():
    end = latest_closed_day_start()
    print("=" * 64)
    print("FREE BYBIT DAILY BTC COLLECTOR v0.2")
    print("Instrument: BTCUSD inverse perpetual")
    print("Interval: daily")
    print("Last included CLOSED UTC day:", end.date())
    print("Current partial UTC candle excluded: YES")
    print("=" * 64)

    end_ms = ms(end)
    start_floor_ms = ms(START)
    collected = {}
    page = 0

    while end_ms >= start_floor_ms:
        page += 1
        window_start_ms = max(start_floor_ms, end_ms - 999 * DAY_MS)
        start_date = datetime.fromtimestamp(window_start_ms / 1000, tz=timezone.utc).date()
        end_date = datetime.fromtimestamp(end_ms / 1000, tz=timezone.utc).date()
        print(f"Page {page}: {start_date} -> {end_date}")

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

        valid_ts = []
        for r in rows:
            if len(r) < 7:
                continue
            ts = int(r[0])
            valid_ts.append(ts)
            if ts < start_floor_ms or ts > ms(end):
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

        if not valid_ts:
            raise RuntimeError("Page returned no valid timestamps")

        oldest = min(valid_ts)
        print("  rows received:", len(rows), "unique total:", len(collected))
        if oldest <= start_floor_ms:
            break
        end_ms = oldest - 1
        time.sleep(0.5)

    if not collected:
        raise RuntimeError("No daily BTC data collected")

    fields = ["start_time_ms", "date_utc", "open", "high", "low", "close", "volume", "turnover"]
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
    input("Press Enter to finish...")


if __name__ == "__main__":
    main()
