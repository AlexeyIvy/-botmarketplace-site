"""Android/Pydroid smoke test for free first-of-month Deribit BTC option snapshots.

Self-contained: copy into Pydroid 3 and press Run.
Requests small first-of-month Tardis HTTP windows for 2020-03 through 2020-06
at 12:00 UTC, reconstructs the latest BTC option ticker state at decision time,
and writes one compact CSV to Android Download.

Research-only. No API key required for Tardis first-day-of-month sample access.
"""

from __future__ import annotations

import csv
import gzip
import json
import os
import time
from datetime import datetime, timezone
from urllib.parse import quote
from urllib.request import Request, urlopen

BASE = "https://api.tardis.dev/v1/data-feeds/deribit"
OUTPUT = "/storage/emulated/0/Download/r001_tardis_free_2020-03_to_2020-06.csv"
MONTHS = ["2020-03-01", "2020-04-01", "2020-05-01", "2020-06-01"]
DECISION_HOUR = 12
LOOKBACK_MINUTES = 5

FIELDS = [
    "decision_time",
    "local_timestamp_us",
    "exchange_timestamp_us",
    "instrument_name",
    "option_type",
    "strike_price",
    "expiry_code",
    "best_bid_price",
    "best_bid_amount",
    "best_ask_price",
    "best_ask_amount",
    "mark_price",
    "mark_iv",
    "underlying_price",
    "delta",
    "gamma",
    "vega",
    "theta",
    "open_interest",
]


def fnum(v):
    if v is None:
        return None
    try:
        return float(v)
    except Exception:
        return None


def parse_name(name):
    parts = name.split("-")
    if len(parts) != 4 or parts[0] != "BTC" or parts[3] not in ("P", "C"):
        return None
    try:
        strike = float(parts[2])
    except Exception:
        return None
    return {
        "option_type": "put" if parts[3] == "P" else "call",
        "strike_price": strike,
        "expiry_code": parts[1],
    }


def iso_to_us(value):
    """Convert Tardis ISO-8601 local timestamp to integer microseconds UTC."""
    try:
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1_000_000)
    except Exception:
        return None


def parse_line(raw):
    """Tardis data-feeds line: <ISO localTimestamp> <exchange JSON>."""
    try:
        text = raw.decode("utf-8").strip()
        if not text:
            return None
        ts_text, json_text = text.split(" ", 1)
        local_ts_us = iso_to_us(ts_text)
        if local_ts_us is None:
            return None
        msg = json.loads(json_text)
        return local_ts_us, msg
    except Exception:
        return None


def build_url(day, hour, lookback_minutes):
    start_minute = 60 - lookback_minutes if lookback_minutes > 0 else 0
    start_hour = hour - 1 if hour > 0 else 23
    from_value = f"{day}T{start_hour:02d}:{start_minute:02d}:00.000Z"
    filters = json.dumps([{"channel": "ticker"}], separators=(",", ":"))
    return (
        f"{BASE}?from={quote(from_value)}"
        f"&filters={quote(filters)}"
        f"&offset=0"
        f"&sliceSize={lookback_minutes + 1}"
    )


def extract_ticker(msg):
    params = msg.get("params") if isinstance(msg, dict) else None
    data = params.get("data") if isinstance(params, dict) else None
    if not isinstance(data, dict):
        return None

    name = data.get("instrument_name")
    if not isinstance(name, str):
        return None

    parsed = parse_name(name)
    if parsed is None:
        return None

    greeks = data.get("greeks") if isinstance(data.get("greeks"), dict) else {}

    exchange_ts = data.get("timestamp")
    try:
        exchange_ts = int(exchange_ts)
        if exchange_ts < 10**15:
            exchange_ts *= 1000
    except Exception:
        exchange_ts = None

    return {
        "instrument_name": name,
        "option_type": parsed["option_type"],
        "strike_price": parsed["strike_price"],
        "expiry_code": parsed["expiry_code"],
        "exchange_timestamp_us": exchange_ts,
        "best_bid_price": fnum(data.get("best_bid_price")),
        "best_bid_amount": fnum(data.get("best_bid_amount")),
        "best_ask_price": fnum(data.get("best_ask_price")),
        "best_ask_amount": fnum(data.get("best_ask_amount")),
        "mark_price": fnum(data.get("mark_price")),
        "mark_iv": fnum(data.get("mark_iv")),
        "underlying_price": fnum(data.get("underlying_price")),
        "delta": fnum(greeks.get("delta")),
        "gamma": fnum(greeks.get("gamma")),
        "vega": fnum(greeks.get("vega")),
        "theta": fnum(greeks.get("theta")),
        "open_interest": fnum(data.get("open_interest")),
    }


def collect_month(day):
    decision = datetime.fromisoformat(f"{day}T{DECISION_HOUR:02d}:00:00+00:00")
    decision_us = int(decision.timestamp() * 1_000_000)
    url = build_url(day, DECISION_HOUR, LOOKBACK_MINUTES)

    print()
    print("Fetching:", day, f"{DECISION_HOUR:02d}:00 UTC")

    req = Request(
        url,
        headers={
            "User-Agent": "r001-android-research/0.2",
            "Accept-Encoding": "gzip",
        },
    )

    latest = {}
    line_count = 0

    with urlopen(req, timeout=120) as resp:
        encoding = (resp.headers.get("Content-Encoding") or "").lower()
        stream = gzip.GzipFile(fileobj=resp) if encoding == "gzip" else resp

        for raw in stream:
            line_count += 1
            parsed = parse_line(raw)
            if parsed is None:
                continue

            local_ts_us, msg = parsed

            # No look-ahead: ignore anything captured after decision time.
            if local_ts_us > decision_us:
                continue

            row = extract_ticker(msg)
            if row is None:
                continue

            row["decision_time"] = decision.isoformat()
            row["local_timestamp_us"] = local_ts_us

            symbol = row["instrument_name"]
            prev = latest.get(symbol)
            if prev is None or local_ts_us > prev["local_timestamp_us"]:
                latest[symbol] = row

    rows = sorted(latest.values(), key=lambda x: x["instrument_name"])
    two_sided = sum(
        1 for r in rows
        if (r["best_bid_price"] or 0) > 0 and (r["best_ask_price"] or 0) > 0
    )
    with_delta = sum(1 for r in rows if r["delta"] is not None)

    print("Raw feed lines:", line_count)
    print("BTC options:", len(rows))
    print("With delta:", with_delta)
    print("Two-sided bid/ask:", two_sided)

    return rows


def main():
    print("=" * 60)
    print("R001 FREE TARDIS MONTHLY TEST v0.2")
    print("2020-03 -> 2020-06")
    print("Decision time: 12:00 UTC")
    print("No API key")
    print("=" * 60)

    all_rows = []
    failures = []

    for day in MONTHS:
        try:
            rows = collect_month(day)
            all_rows.extend(rows)
        except Exception as e:
            print()
            print("FAILED:", day)
            print(repr(e))
            failures.append((day, repr(e)))
        time.sleep(1)

    if not all_rows:
        print()
        print("NO DATA COLLECTED")
        print("Failures:", failures)
        input("Press Enter to exit...")
        return

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for row in all_rows:
            writer.writerow({key: row.get(key) for key in FIELDS})

    size_kb = os.path.getsize(OUTPUT) / 1024

    print()
    print("=" * 60)
    print("DONE")
    print("=" * 60)
    print("Rows written:", len(all_rows))
    print("Output:", OUTPUT)
    print(f"Size: {size_kb:.1f} KB")
    if failures:
        print("Some months failed:", failures)
    print()
    print("Upload the resulting CSV to ChatGPT.")
    input("Press Enter to finish...")


if __name__ == "__main__":
    main()
