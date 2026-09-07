from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Optional

MICROS_PER_DAY = 86_400_000_000


@dataclass(frozen=True)
class OptionQuote:
    symbol: str
    timestamp_us: int
    option_type: str
    strike_price: float
    expiration_us: int
    bid_price: Optional[float]
    ask_price: Optional[float]
    bid_amount: Optional[float]
    ask_amount: Optional[float]
    delta: Optional[float]
    underlying_price: Optional[float]

    @property
    def dte(self) -> float:
        return (self.expiration_us - self.timestamp_us) / MICROS_PER_DAY

    @property
    def spread(self) -> Optional[float]:
        if self.bid_price is None or self.ask_price is None:
            return None
        return self.ask_price - self.bid_price


@dataclass(frozen=True)
class SelectionConfig:
    option_type: str = "put"
    target_abs_delta: float = 0.15
    target_dte: float = 90.0
    min_dte: float = 60.0
    max_dte: float = 120.0
    max_quote_age_seconds: float = 300.0
    require_two_sided: bool = True
    min_ask_amount: float = 0.0


@dataclass(frozen=True)
class SelectionResult:
    quote: OptionQuote
    delta_error: float
    dte_error: float


def parse_optional_float(value: str | None) -> Optional[float]:
    if value is None or value == "":
        return None
    return float(value)


def parse_row(row: dict[str, str]) -> OptionQuote:
    return OptionQuote(
        symbol=row["symbol"],
        timestamp_us=int(row["timestamp"]),
        option_type=row["type"].lower(),
        strike_price=float(row["strike_price"]),
        expiration_us=int(row["expiration"]),
        bid_price=parse_optional_float(row.get("bid_price")),
        ask_price=parse_optional_float(row.get("ask_price")),
        bid_amount=parse_optional_float(row.get("bid_amount")),
        ask_amount=parse_optional_float(row.get("ask_amount")),
        delta=parse_optional_float(row.get("delta")),
        underlying_price=parse_optional_float(row.get("underlying_price")),
    )


def select_option(
    quotes: Iterable[OptionQuote],
    decision_timestamp_us: int,
    config: SelectionConfig = SelectionConfig(),
) -> SelectionResult:
    """Select an executable historical option quote without look-ahead.

    Ranking is intentionally simple and auditable:
      1. Filter to quotes known at decision time and not stale.
      2. Filter option type and DTE window.
      3. Require usable delta and executable ask (and bid if configured).
      4. Rank first by distance to target DTE, then target |delta|,
         then tighter spread, then symbol for deterministic tie-breaking.

    Buy-side backtests should execute at quote.ask_price, not mark/mid.
    """
    max_age_us = int(config.max_quote_age_seconds * 1_000_000)
    eligible: list[OptionQuote] = []

    for q in quotes:
        if q.timestamp_us > decision_timestamp_us:
            continue
        if decision_timestamp_us - q.timestamp_us > max_age_us:
            continue
        if q.option_type != config.option_type:
            continue
        if not (config.min_dte <= q.dte <= config.max_dte):
            continue
        if q.delta is None or q.ask_price is None or q.ask_price <= 0:
            continue
        if config.require_two_sided and (q.bid_price is None or q.bid_price < 0):
            continue
        if q.ask_amount is not None and q.ask_amount < config.min_ask_amount:
            continue
        eligible.append(q)

    if not eligible:
        raise ValueError("No eligible historical option quote for selection")

    def rank(q: OptionQuote) -> tuple[float, float, float, str]:
        spread = q.spread if q.spread is not None else float("inf")
        return (
            abs(q.dte - config.target_dte),
            abs(abs(q.delta) - config.target_abs_delta),
            spread,
            q.symbol,
        )

    chosen = min(eligible, key=rank)
    return SelectionResult(
        quote=chosen,
        delta_error=abs(abs(chosen.delta or 0.0) - config.target_abs_delta),
        dte_error=abs(chosen.dte - config.target_dte),
    )


def iso_from_us(ts_us: int) -> str:
    return datetime.fromtimestamp(ts_us / 1_000_000, tz=timezone.utc).isoformat()
