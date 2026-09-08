"""R001 free-data collector prototype.

Uses Tardis HTTP API's unauthenticated first-day-of-month access to request a
small Deribit ticker window around a fixed monthly decision timestamp.

Goal: reconstruct a compact BTC options snapshot without downloading the full
multi-hundred-megabyte daily options_chain file.

This is research-only code. It intentionally stores source timestamps and raw
payload fields so selections remain auditable.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Iterable
from urllib.parse import quote
from urllib.request import Request, urlopen

BASE = "https://api.tardis.dev/v1/data-feeds/deribit"


@dataclass
class TickerRow:
    decision_time: str
    local_timestamp: str
    instrument_name: str
    option_type: str
    strike_price: float
    expiration: str
    best_bid_price: float | None
    best_ask_price: float | None
    mark_price: float | None
    mark_iv: float | None
    underlying_price: float | None
    delta: float | None
    gamma: float | None
    vega: float | None
    theta: float | None
    open_interest: float | None


def _f(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_instrument(name: str) -> tuple[str, float, str] | None:
    """Parse Deribit BTC option name, e.g. BTC-26JUN20-7000-P."""
    parts = name.split("-")
    if len(parts) != 4 or parts[0] != "BTC" or parts[3] not in {"P", "C"}:
        return None
    try:
        strike = float(parts[2])
    except ValueError:
        return None
    return ("put" if parts[3] == "P" else "call", strike, parts[1])


def build_url(day: str, hour: int = 12, minute_offset: int = 0) -> str:
    """Build one-minute Tardis HTTP request for Deribit ticker channel.

    Tardis HTTP API serves one-minute slices. `offset` is minutes after the
    `from` timestamp. We request ticker for all instruments and filter BTC
    options client-side.
    """
    from_value = f"{day}T{hour:02d}:00:00.000Z"
    filters = json.dumps([{"channel": "ticker"}], separators=(",", ":"))
    return f"{BASE}?from={quote(from_value)}&filters={quote(filters)}&offset={minute_offset}"


def iter_tardis_lines(url: str) -> Iterable[tuple[str, dict[str, Any]]]:
    req = Request(url, headers={"Accept-Encoding": "gzip", "User-Agent": "r001-research/0.1"})
    with urlopen(req, timeout=60) as resp:
        # urllib transparently handles neither gzip nor chunk decompression in a
        # provider-independent way, so ask for identity on retry if needed.
        encoding = (resp.headers.get("Content-Encoding") or "").lower()
        stream = resp
        if encoding == "gzip":
            import gzip
            stream = gzip.GzipFile(fileobj=resp)
        for raw in stream:
            line = raw.decode("utf-8").strip()
            if not line:
                continue
            obj = json.loads(line)
            # Tardis raw feed line convention: [localTimestamp, message]
            if isinstance(obj, list) and len(obj) == 2 and isinstance(obj[1], dict):
                yield str(obj[0]), obj[1]
            elif isinstance(obj, dict):
                # Some API/client shapes may expose explicit fields.
                local_ts = obj.get("localTimestamp") or obj.get("local_timestamp") or ""
                message = obj.get("message") if isinstance(obj.get("message"), dict) else obj
                yield str(local_ts), message


def ticker_to_row(decision_time: str, local_ts: str, msg: dict[str, Any]) -> TickerRow | None:
    params = msg.get("params") if isinstance(msg.get("params"), dict) else None
    data = params.get("data") if params and isinstance(params.get("data"), dict) else msg.get("data")
    if not isinstance(data, dict):
        data = msg

    name = data.get("instrument_name")
    if not isinstance(name, str):
        return None
    parsed = parse_instrument(name)
    if parsed is None:
        return None
    option_type, strike, expiry_code = parsed

    greeks = data.get("greeks") if isinstance(data.get("greeks"), dict) else {}
    expiration = expiry_code

    return TickerRow(
        decision_time=decision_time,
        local_timestamp=local_ts,
        instrument_name=name,
        option_type=option_type,
        strike_price=strike,
        expiration=expiration,
        best_bid_price=_f(data.get("best_bid_price")),
        best_ask_price=_f(data.get("best_ask_price")),
        mark_price=_f(data.get("mark_price")),
        mark_iv=_f(data.get("mark_iv")),
        underlying_price=_f(data.get("underlying_price")),
        delta=_f(greeks.get("delta") if greeks else data.get("delta")),
        gamma=_f(greeks.get("gamma") if greeks else data.get("gamma")),
        vega=_f(greeks.get("vega") if greeks else data.get("vega")),
        theta=_f(greeks.get("theta") if greeks else data.get("theta")),
        open_interest=_f(data.get("open_interest")),
    )


def collect(day: str, hour: int, lookback_minutes: int) -> list[TickerRow]:
    decision = datetime.fromisoformat(f"{day}T{hour:02d}:00:00+00:00")
    decision_iso = decision.isoformat()
    latest: dict[str, TickerRow] = {}

    # Query minutes immediately before and including decision minute. Raw API
    # offset semantics are forward from `from`, so anchor earlier.
    anchor_minute = max(0, 60 - lookback_minutes)
    anchor_hour = hour - 1 if hour > 0 else 23
    anchor_day = day
    # This prototype intentionally targets 12:00 UTC where crossing midnight is
    # irrelevant. General date rollover can be added after the first comparison.
    anchor = f"{day}T{anchor_hour:02d}:{anchor_minute:02d}:00.000Z"
    filters = json.dumps([{"channel": "ticker"}], separators=(",", ":"))

    for offset in range(lookback_minutes + 1):
        url = f"{BASE}?from={quote(anchor)}&filters={quote(filters)}&offset={offset}"
        for local_ts, msg in iter_tardis_lines(url):
            row = ticker_to_row(decision_iso, local_ts, msg)
            if row is not None:
                latest[row.instrument_name] = row

    return sorted(latest.values(), key=lambda r: r.instrument_name)


def write_csv(rows: list[TickerRow], path: str) -> None:
    if not rows:
        raise ValueError("No BTC option ticker rows collected")
    fields = list(asdict(rows[0]).keys())
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow(asdict(row))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--day", default="2020-03-01", help="first day of month YYYY-MM-DD")
    p.add_argument("--hour", type=int, default=12)
    p.add_argument("--lookback-minutes", type=int, default=5)
    p.add_argument("--out", default="tardis_deribit_2020-03-01_1200_ticker.csv")
    args = p.parse_args()

    rows = collect(args.day, args.hour, args.lookback_minutes)
    write_csv(rows, args.out)

    two_sided = sum(1 for r in rows if r.best_bid_price not in (None, 0) and r.best_ask_price not in (None, 0))
    with_delta = sum(1 for r in rows if r.delta is not None)
    print(f"BTC option instruments: {len(rows)}")
    print(f"with delta: {with_delta}")
    print(f"two-sided bid/ask: {two_sided}")
    print(f"wrote: {args.out}")


if __name__ == "__main__":
    main()
