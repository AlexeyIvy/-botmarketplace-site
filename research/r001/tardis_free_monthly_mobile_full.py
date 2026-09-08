"""R001 Android/Pydroid free monthly Deribit BTC options collector v0.4.

Collects first-of-month BTC option ticker snapshots from Tardis without an API
key, one month at a time, at a fixed 12:00 UTC decision timestamp.

Reliability design for Android/Pydroid:
- each month is written atomically to its own shard CSV;
- reruns skip only valid month shards, not a fragile append-only state flag;
- no duplicate months after app/process interruption;
- final combined CSV is rebuilt deterministically from shards;
- retry/backoff on transient HTTP/network failures;
- explicit failure/state logs;
- no look-ahead: only local timestamps <= decision time are retained;
- basic per-month quality diagnostics are persisted.

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
WORKDIR = os.path.join(DOWNLOAD, "r001_tardis_monthly_parts")
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

# Sanity checks are intentionally permissive for early/sparse option markets.
MIN_ROWS_PER_MONTH = 20
MIN_DELTA_COVERAGE = 0.50

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
    # Window 11:55:00 through 12:00:59 UTC when LOOKBACK_MINUTES=5.
    # We later reject any message whose local timestamp is after exactly 12:00:00.
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


def shard_path(day):
    return os.path.join(WORKDIR, f"{day}.csv")


def is_valid_shard(day):
    path = shard_path(day)
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return False
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != FIELDS:
                return False
            count = 0
            for row in reader:
                count += 1
                if row.get("decision_time", "")[:10] != day:
                    return False
            return count >= MIN_ROWS_PER_MONTH
    except Exception:
        return False


def write_shard_atomic(day, rows):
    path = shard_path(day)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k) for k in FIELDS})
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def rebuild_output(months):
    tmp = OUTPUT + ".tmp"
    total = 0
    with open(tmp, "w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=FIELDS)
        writer.writeheader()
        for day in months:
            if not is_valid_shard(day):
                continue
            with open(shard_path(day), "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    writer.writerow({k: row.get(k) for k in FIELDS})
                    total += 1
        out.flush()
        os.fsync(out.fileno())
    os.replace(tmp, OUTPUT)
    return total


def save_state(state):
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, STATE)


def log_failure(day, message):
    stamp = datetime.now(timezone.utc).isoformat()
    with open(FAILURES, "a", encoding="utf-8") as f:
        f.write(f"{stamp}\t{day}\t{message}\n")


def collect_month(day):
    decision = datetime.fromisoformat(f"{day}T{DECISION_HOUR:02d}:00:00+00:00")
    decision_us = int(decision.timestamp() * 1_000_000)
    url = build_url(day)

    req = Request(
        url,
        headers={
            "User-Agent": "r001-android-research/0.4",
            "Accept-Encoding": "gzip",
        },
    )

    latest = {}
    line_count = 0
    parse_failures = 0
    future_lines = 0

    with urlopen(req, timeout=REQUEST_TIMEOUT) as response:
        encoding = (response.headers.get("Content-Encoding") or "").lower()
        stream = gzip.GzipFile(fileobj=response) if encoding == "gzip" else response

        for raw in stream:
            line_count += 1
            parsed = parse_line(raw)
            if parsed is None:
                parse_failures += 1
                continue
            local_ts_us, msg = parsed
            if local_ts_us > decision_us:
                future_lines += 1
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
    with_delta = sum(1 for r in rows if r["delta"] is not None)
    two_sided = sum(
        1 for r in rows
        if (r["best_bid_price"] or 0) > 0 and (r["best_ask_price"] or 0) > 0
    )
    delta_coverage = with_delta / len(rows) if rows else 0.0

    if len(rows) < MIN_ROWS_PER_MONTH:
        raise ValueError(f"Too few BTC option rows: {len(rows)}")
    if delta_coverage < MIN_DELTA_COVERAGE:
        raise ValueError(f"Delta coverage too low: {delta_coverage:.1%}")

    stats = {
        "raw_lines": line_count,
        "parse_failures": parse_failures,
        "future_lines_rejected": future_lines,
        "btc_options": len(rows),
        "with_delta": with_delta,
        "delta_coverage": delta_coverage,
        "two_sided": two_sided,
        "two_sided_coverage": two_sided / len(rows) if rows else 0.0,
    }
    return rows, stats


def main():
    os.makedirs(DOWNLOAD, exist_ok=True)
    os.makedirs(WORKDIR, exist_ok=True)
    months = month_list()

    print("=" * 64)
    print("R001 FREE MONTHLY DERIBIT COLLECTOR v0.4")
    print(f"Period: {months[0]} -> {months[-1]}")
    print(f"Decision time: {DECISION_HOUR:02d}:00 UTC")
    print("No API key / first-of-month free Tardis data")
    print("Crash-safe monthly shards: YES")
    print("=" * 64)

    completed = [day for day in months if is_valid_shard(day)]
    state = {
        "version": "0.4",
        "period": [months[0], months[-1]],
        "decision_hour_utc": DECISION_HOUR,
        "completed": completed,
        "failed": {},
        "stats": {},
    }
    save_state(state)

    print("Valid existing month shards:", len(completed), "/", len(months))
    print("Parts folder:", WORKDIR)
    print("Final output:", OUTPUT)

    for idx, day in enumerate(months, start=1):
        if is_valid_shard(day):
            print(f"[{idx}/{len(months)}] SKIP {day} (valid shard exists)")
            continue

        print()
        print(f"[{idx}/{len(months)}] Fetching {day} {DECISION_HOUR:02d}:00 UTC")
        success = False
        last_error = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                rows, stats = collect_month(day)
                write_shard_atomic(day, rows)
                if not is_valid_shard(day):
                    raise ValueError("Shard failed post-write validation")

                state["stats"][day] = stats
                state["failed"].pop(day, None)
                state["completed"] = [d for d in months if is_valid_shard(d)]
                save_state(state)

                print("  raw lines:", stats["raw_lines"])
                print("  parse failures:", stats["parse_failures"])
                print("  future lines rejected:", stats["future_lines_rejected"])
                print("  BTC options:", stats["btc_options"])
                print("  delta coverage: %.1f%%" % (100 * stats["delta_coverage"]))
                print("  two-sided coverage: %.1f%%" % (100 * stats["two_sided_coverage"]))
                print("  saved atomically: YES")
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
            state["failed"][day] = last_error or "unknown error"
            state["completed"] = [d for d in months if is_valid_shard(d)]
            save_state(state)
            log_failure(day, last_error or "unknown error")
            print("  month recorded as FAILED; collector continues")

        time.sleep(SLEEP_BETWEEN_MONTHS)

    # Rebuild the combined dataset from validated month shards only.
    total_rows = rebuild_output(months)
    completed_final = [day for day in months if is_valid_shard(day)]
    failed_final = [day for day in months if day not in completed_final]

    state["completed"] = completed_final
    state["failed"] = {day: state["failed"].get(day, "missing/invalid shard") for day in failed_final}
    state["combined_rows"] = total_rows
    state["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    save_state(state)

    print()
    print("=" * 64)
    print("FINISHED")
    print("=" * 64)
    print("Completed months:", len(completed_final), "/", len(months))
    print("Failed/missing months:", len(failed_final))
    print("Combined rows:", total_rows)
    if os.path.exists(OUTPUT):
        print("Output size: %.2f MB" % (os.path.getsize(OUTPUT) / (1024 * 1024)))
    print("Output:", OUTPUT)
    print("State:", STATE)
    print("Parts folder:", WORKDIR)
    if failed_final:
        print("Failures log:", FAILURES)
        print("Missing months:", ", ".join(failed_final))
        print("Run the same script again later; valid shards will be skipped.")
    else:
        print("All months collected successfully.")
    print()
    print("Upload the combined CSV to ChatGPT for E003-S screening.")
    input("Press Enter to finish...")


if __name__ == "__main__":
    main()
