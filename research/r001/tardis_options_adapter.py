"""Tardis Deribit options_chain CSV adapter for R001 research.

Research-only code. Converts normalized Tardis options_chain CSV rows into
plain dictionaries expected by option_selector.py. It deliberately preserves
exchange timestamps and executable bid/ask instead of replacing them with
mark/mid prices.
"""

from __future__ import annotations

import csv
import gzip
from pathlib import Path
from typing import Iterable, Iterator, Mapping, TextIO


NUMERIC_FIELDS = {
    "timestamp",
    "local_timestamp",
    "strike_price",
    "expiration",
    "open_interest",
    "last_price",
    "bid_price",
    "bid_amount",
    "bid_iv",
    "ask_price",
    "ask_amount",
    "ask_iv",
    "mark_price",
    "mark_iv",
    "underlying_price",
    "delta",
    "gamma",
    "vega",
    "theta",
    "rho",
}


def _num(value: str):
    if value is None or value == "":
        return None
    return float(value)


def normalize_row(row: Mapping[str, str]) -> dict:
    out = dict(row)
    for key in NUMERIC_FIELDS:
        if key in out:
            out[key] = _num(out[key])

    # Keep timestamps as integer microseconds when present. float conversion
    # above is convenient for generic CSV parsing but exact time ordering is
    # safer with ints.
    for key in ("timestamp", "local_timestamp", "expiration"):
        value = row.get(key)
        if value not in (None, ""):
            out[key] = int(value)

    out["type"] = (out.get("type") or "").lower()
    return out


def iter_csv(handle: TextIO) -> Iterator[dict]:
    for row in csv.DictReader(handle):
        yield normalize_row(row)


def iter_gzip_csv(path: str | Path) -> Iterator[dict]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        yield from iter_csv(handle)


def validate_required_fields(rows: Iterable[Mapping]) -> None:
    required = {
        "exchange",
        "symbol",
        "timestamp",
        "local_timestamp",
        "type",
        "strike_price",
        "expiration",
        "bid_price",
        "ask_price",
        "underlying_price",
        "delta",
    }
    for i, row in enumerate(rows):
        missing = sorted(k for k in required if k not in row)
        if missing:
            raise ValueError(f"row {i}: missing required fields: {', '.join(missing)}")
