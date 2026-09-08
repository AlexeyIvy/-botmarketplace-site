"""Free monthly Deribit BTC option snapshot collector for R001.

Uses Tardis unauthenticated historical HTTP access for the first day of each
month. The collector requests only a short ticker window around a fixed monthly
decision timestamp, reconstructs the latest quote per BTC option instrument,
and writes compact CSV snapshots suitable for R001 screening research.

Important research constraints:
- first-day-of-month only for no-key access;
- decision time is fixed ex ante (default 12:00 UTC);
- no look-ahead: keep only messages captured at/before decision time;
- preserve executable bid/ask; never substitute mark/mid for fills;
- this is screening data, not sufficient for intramonth path/drawdown analysis.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://api.tardis.dev/v1/data-feeds/deribit"
UTC = timezone.utc


@dataclass
class SnapshotRow:
    decision_timestamp: str
    local_timestamp: str
    instrument_name: str
    option_type: str
    strike_price: float
    expiration_code: str
    best_bid_price: float | None
    best_ask_price: float | None
    best_bid_amount: float | None
    best_ask_amount: float | None
    mark_price: float | None
    mark_iv: float | None
    underlying_price: float | None
    delta: float | None
    gamma: float | None
    vega: float | None
    theta: float | None
    open_interest: float | None


def _f(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_instrument(name: str) -> tuple[str, float, str] | None:
    parts = name.split("-")
    if len(parts) != 4 or parts[0] != "BTC" or parts[3] not in {"P", "C"}:
        return None
    try:
        strike = float(parts[2])
    except ValueError:
        return None
    return ("put" if parts[3] == "P" else "call", strike, parts[1])


def parse_local_timestamp(value: str) -> datetime:
    # Tardis uses ISO-8601 strings, commonly ending in Z and potentially with
    # sub-microsecond precision. Python accepts up to microseconds, so trim the
    # fractional portion conservatively when required.
    s = value.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    if "." in s:
        head, tail = s.split(".", 1)
        tz_pos = max(tail.find("+"), tail.find("-"))
        if tz_pos > 0:
            frac, tz = tail[:tz_pos], tail[tz_pos:]
        else:
            frac, tz = tail, ""
        frac = frac[:6]
        s = f"{head}.{frac}{tz}"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def iter_ndjson_response(resp) -> Iterable[tuple[str, dict[str, Any]]]:
    """Parse Tardis /data-feeds lines: '<localTimestamp> <json>'."""
    encoding = (resp.headers.get("Content-Encoding") or "").lower()
    raw_stream = resp
    if encoding == "gzip":
        raw_stream = gzip.GzipFile(fileobj=resp)
    text_stream = io.TextIOWrapper(raw_stream, encoding="utf-8")

    for line in text_stream:
        line = line.strip()
        if not line:
            continue
        try:
            local_ts, json_text = line.split(" ", 1)
            message = json.loads(json_text)
        except (ValueError, json.JSONDecodeError):
            continue
        if isinstance(message, dict):
            yield local_ts, message


def request_slice(start: datetime, minutes: int) -> Iterable[tuple[str, dict[str, Any]]]:
    if not 1 <= minutes <= 10:
        raise ValueError("minutes must be 1..10")

    filters = json.dumps([{"channel": "ticker"}], separators=(",", ":"))
    params = {
        "from": start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "offset": 0,
        "filters": filters,
        "sliceSize": minutes,
    }
    url = BASE + "?" + urlencode(params)
    req = Request(
        url,
        headers={
            "Accept-Encoding": "gzip",
            "User-Agent": "botmarketplace-r001-research/0.2",
        },
    )
    with urlopen(req, timeout=120) as resp:
        yield from iter_ndjson_response(resp)


def ticker_message_to_row(
    decision: datetime,
    local_ts: str,
    message: dict[str, Any],
) -> SnapshotRow | None:
    params = message.get("params")
    data = params.get("data") if isinstance(params, dict) else None
    if not isinstance(data, dict):
        return None

    name = data.get("instrument_name")
    if not isinstance(name, str):
        return None
    parsed = parse_instrument(name)
    if parsed is None:
        return None
    option_type, strike, expiry_code = parsed

    greeks = data.get("greeks") if isinstance(data.get("greeks"), dict) else {}

    return SnapshotRow(
        decision_timestamp=decision.isoformat(),
        local_timestamp=local_ts,
        instrument_name=name,
        option_type=option_type,
        strike_price=strike,
        expiration_code=expiry_code,
        best_bid_price=_f(data.get("best_bid_price")),
        best_ask_price=_f(data.get("best_ask_price")),
        best_bid_amount=_f(data.get("best_bid_amount")),
        best_ask_amount=_f(data.get("best_ask_amount")),
        mark_price=_f(data.get("mark_price")),
        mark_iv=_f(data.get("mark_iv")),
        underlying_price=_f(data.get("underlying_price")),
        delta=_f(greeks.get("delta")),
        gamma=_f(greeks.get("gamma")),
        vega=_f(greeks.get("vega")),
        theta=_f(greeks.get("theta")),
        open_interest=_f(data.get("open_interest")),
    )


def collect_month(
    year: int,
    month: int,
    hour: int = 12,
    lookback_minutes: int = 5,
) -> list[SnapshotRow]:
    decision = datetime(year, month, 1, hour, 0, 0, tzinfo=UTC)
    start = decision - timedelta(minutes=lookback_minutes)

    # Request one compact consecutive slice ending at decision time. A ticker
    # received after decision is rejected below even if it appears in the last
    # returned minute because localTimestamp is the research availability time.
    request_minutes = min(10, lookback_minutes + 1)
    latest: dict[str, tuple[datetime, SnapshotRow]] = {}

    for local_ts, message in request_slice(start, request_minutes):
        try:
            available_at = parse_local_timestamp(local_ts)
        except ValueError:
            continue
        if available_at > decision:
            continue
        if decision - available_at > timedelta(minutes=lookback_minutes):
            continue

        row = ticker_message_to_row(decision, local_ts, message)
        if row is None:
            continue

        prev = latest.get(row.instrument_name)
        if prev is None or available_at > prev[0]:
            latest[row.instrument_name] = (available_at, row)

    return sorted((item[1] for item in latest.values()), key=lambda r: r.instrument_name)


def month_range(start: str, end: str) -> list[tuple[int, int]]:
    s = datetime.strptime(start, "%Y-%m").replace(day=1)
    e = datetime.strptime(end, "%Y-%m").replace(day=1)
    if e < s:
        raise ValueError("end must be >= start")
    out: list[tuple[int, int]] = []
    cur = s
    while cur <= e:
        out.append((cur.year, cur.month))
        cur = (cur.replace(day=28) + timedelta(days=4)).replace(day=1)
    return out


def write_csv(rows: list[SnapshotRow], path: str) -> None:
    fields = list(SnapshotRow.__dataclass_fields__.keys())
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def main() -> None:
    p = argparse.ArgumentParser(description="Collect free first-of-month Deribit BTC option snapshots")
    p.add_argument("--start", default="2020-03", help="YYYY-MM")
    p.add_argument("--end", default="2020-03", help="YYYY-MM")
    p.add_argument("--hour", type=int, default=12)
    p.add_argument("--lookback-minutes", type=int, default=5)
    p.add_argument("--sleep", type=float, default=0.5, help="pause between months")
    p.add_argument("--out", default="r001_free_monthly_deribit_options.csv")
    args = p.parse_args()

    all_rows: list[SnapshotRow] = []
    failures: list[str] = []

    for year, month in month_range(args.start, args.end):
        label = f"{year:04d}-{month:02d}"
        print(f"Collecting {label}-01 {args.hour:02d}:00 UTC ...")
        try:
            rows = collect_month(year, month, args.hour, args.lookback_minutes)
            all_rows.extend(rows)
            two_sided = sum(
                1 for r in rows
                if r.best_bid_price not in (None, 0) and r.best_ask_price not in (None, 0)
            )
            with_delta = sum(1 for r in rows if r.delta is not None)
            print(f"  BTC options={len(rows)} delta={with_delta} two-sided={two_sided}")
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            failures.append(f"{label}: {exc!r}")
            print(f"  FAILED: {exc!r}")
        time.sleep(max(args.sleep, 0.0))

    write_csv(all_rows, args.out)
    print(f"Wrote {len(all_rows)} rows -> {args.out}")
    if failures:
        print("Failures:")
        for item in failures:
            print(" ", item)


if __name__ == "__main__":
    main()
