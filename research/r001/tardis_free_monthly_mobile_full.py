"""R001 Android/Pydroid full free monthly Deribit BTC options collector.

Collects first-of-month BTC option ticker snapshots from Tardis without an API
key, one month at a time, at a fixed 12:00 UTC decision timestamp.

Designed for Android/Pydroid reliability:
- resumable checkpointing (completed months are not fetched again),
- one compact request per month,
- retry/backoff on transient HTTP/network failures,
- month-level append to CSV so progress survives app interruption,
- explicit failure log,
- no look-ahead: only local timestamps <= decision time are retained.

Research-only screening data. First-of-month snapshots are not a substitute for
full intramonth option history or final validation.
"""

from __future__ import annotations

import csv
import gzip
import json
import os
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

BASE = "https://api.tardis.dev/v1/data-feeds/deribit"
DOWNLOAD = "/storage/emulated/0/Download"
OUTPUT = os.path.join(DOWNLOAD, "r001_tardis_free_monthly_2019-10_to_2026-09.csv")
STATE = os.path.join(DOWNLOAD, "r001_tardis_free_monthly_state.json")
FAILURES = os.path.join(DOWNLOAD, "r001_tardis_free_monthly_failures.txt")

START_YEAR = 2019
START_MONTH = 10
END_YEAR = 2026
END_MONTH = 9
DECISION_HOUR = 12
LOOKBACK_MINUTES = 5
REQUEST_TIMEOUT = 120
MAX_RETRIES = 3
RETRY_BASE_SECONDS = 3
SLEEP_BETWEEN_MONTHS = 1.0

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


def month_list():
    out = []
    y, m = START_YEAR, START_MONTH
    while (y, m) <= (END_YEAR, END_MONTH):
        out.append(f"{y:04d}-{m:02d}-01")
        m += 1
        if m == 13:
            m = 1
            y += 1
    return out


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
    try:
        text = raw.decode("utf-8").strip()
        if not text:
            return None
        ts_text, json_text = text.split(" ", 1)
        local_ts_us = iso_to_us(ts_text)
        if local_ts_us is None:
            return None
        return local_ts_us, json.loads(json_text)
    except Exception:
        return None


def build_url(day):
    start_minute = 60 - LOOKBACK_MINUTES
    start_hour = DECISION_HOUR - 1
    from_value = f"{day}T{start_hour:02d}:{start_minute:02d}:00.000Z"
    filters = json.dumps([{"channel": "ticker"}], separators=(",", ":"))
    return (
        f"{BASE}?from={quote(from_value)}"
        f"&filters={quote(filters)}"
        f"&offset=0"
        f"&sliceSize={LOOKBACK_MINUTES + 1}"
    )


def extract_ticker(msg):
    if not isinstance(msg, dict):
        return None
    params = msg.get("params")
    if not isinstance(params, dict):
        return None
    data = params.get("data")
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


def load_state():
    if not os.path.exists(STATE):
        return {"completed": [], "failed": {}}
    try:
        with open(STATE, "r", encoding="utf-8") as f:
            obj = json.load(f)
        if not isinstance(obj, dict):
            raise ValueError
        obj.setdefault("completed", [])
        obj.setdefault("failed", {})
        return obj
    except Exception:
        return {"completed": [], "failed": {}}


def save_state(state):
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)
    os.replace(tmp, STATE)


def log_failure(day, message):
    with open(FAILURES, "a", encoding="utf-8") as f:
        f.write(f"{day}\t{message}\n")


def collect_month(day):
    decision = datetime.fromisoformat(f"{day}T{DECISION_HOUR:02d}:00:00+00:00")
    decision_us = int(decision.timestamp() * 1_000_000)
    url = build_url(day)

    req = Request(
        url,
        headers={
            "User-Agent": "r001-android-research/0.3",
            "Accept-Encoding": "gzip",
        },
    )

    latest = {}
    line_count = 0

    with urlopen(req, timeout=REQUEST_TIMEOUT) as response:
        encoding = (response.headers.get("Content-Encoding") or "").lower()
        stream = gzip.GzipFile(fileobj=response) if encoding == "gzip" else response

        for raw in stream:
            line_count += 1
            parsed = parse_line(raw)
            if parsed is None:
                continue
            local_ts_us, msg = parsed
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

    return rows, line_count, with_delta, two_sided


def append_rows(rows):
    new_file = not os.path.exists(OUTPUT) or os.path.getsize(OUTPUT) == 0
    with open(OUTPUT, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k) for k in FIELDS})


def main():
    os.makedirs(DOWNLOAD, exist_ok=True)
    months = month_list()
    state = load_state()
    completed = set(state.get("completed", []))

    print("=" * 64)
    print("R001 FREE MONTHLY DERIBIT COLLECTOR v0.3")
    print(f"Period: {months[0]} -> {months[-1]}")
    print(f"Decision time: {DECISION_HOUR:02d}:00 UTC")
    print("No API key / first-of-month free Tardis data")
    print("Resumable: YES")
    print("=" * 64)
    print("Already completed:", len(completed), "/", len(months))
    print("Output:", OUTPUT)

    for idx, day in enumerate(months, start=1):
        if day in completed:
            print(f"[{idx}/{len(months)}] SKIP {day} (already completed)")
            continue

        print()
        print(f"[{idx}/{len(months)}] Fetching {day} {DECISION_HOUR:02d}:00 UTC")

        success = False
        last_error = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                rows, raw_lines, with_delta, two_sided = collect_month(day)
                if not rows:
                    raise ValueError("No BTC option rows returned")

                append_rows(rows)
                state["completed"].append(day)
                state.get("failed", {}).pop(day, None)
                save_state(state)
                completed.add(day)

                print("  raw lines:", raw_lines)
                print("  BTC options:", len(rows))
                print("  with delta:", with_delta)
                print("  two-sided:", two_sided)
                print("  saved: YES")
                success = True
                break

            except (HTTPError, URLError, TimeoutError, ValueError, OSError) as e:
                last_error = repr(e)
                print(f"  attempt {attempt}/{MAX_RETRIES} failed: {last_error}")
                if attempt < MAX_RETRIES:
                    wait = RETRY_BASE_SECONDS * attempt
                    print("  retry in", wait, "seconds...")
                    time.sleep(wait)

            except Exception as e:
                last_error = repr(e)
                print(f"  unexpected error: {last_error}")
                break

        if not success:
            state.setdefault("failed", {})[day] = last_error or "unknown error"
            save_state(state)
            log_failure(day, last_error or "unknown error")
            print("  month recorded as FAILED; collector continues")

        time.sleep(SLEEP_BETWEEN_MONTHS)

    state = load_state()
    completed_final = len(set(state.get("completed", [])))
    failed_final = len(state.get("failed", {}))

    print()
    print("=" * 64)
    print("FINISHED")
    print("=" * 64)
    print("Completed months:", completed_final, "/", len(months))
    print("Failed months:", failed_final)
    if os.path.exists(OUTPUT):
        print("Output size: %.2f MB" % (os.path.getsize(OUTPUT) / (1024 * 1024)))
    print("Output:", OUTPUT)
    print("State:", STATE)
    if failed_final:
        print("Failures log:", FAILURES)
        print("Run the same script again later; completed months will be skipped.")
    print()
    print("When complete, upload the CSV to ChatGPT for E003-S screening.")
    input("Press Enter to finish...")


if __name__ == "__main__":
    main()
