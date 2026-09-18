from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
from statistics import median
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Trade:
    ts_ms: int
    price: float
    size: float
    side: str
    trade_id: int | None = None

    @property
    def notional(self) -> float:
        return self.price * self.size


@dataclass(frozen=True)
class Bar:
    start_ms: int
    close_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    notional: float
    vwap: float
    trade_count: int
    buy_notional: float
    sell_notional: float
    signed_aggressive_notional: float


def _finite_positive(x: float, name: str) -> None:
    if not math.isfinite(x) or x <= 0:
        raise ValueError(f"{name} must be finite and > 0: {x!r}")


def validate_trade_sequence(trades: Sequence[Trade]) -> None:
    prev_ts: int | None = None
    prev_id: int | None = None
    for i, t in enumerate(trades):
        if not isinstance(t.ts_ms, int):
            raise ValueError(f"trade[{i}] ts_ms must be int")
        _finite_positive(float(t.price), f"trade[{i}].price")
        _finite_positive(float(t.size), f"trade[{i}].size")
        if t.side not in {"buy", "sell"}:
            raise ValueError(f"trade[{i}].side invalid: {t.side!r}")

        if prev_ts is not None and t.ts_ms < prev_ts:
            raise ValueError(
                f"timestamp moved backward at trade[{i}]: {t.ts_ms} < {prev_ts}"
            )

        if t.trade_id is not None:
            if not isinstance(t.trade_id, int):
                raise ValueError(f"trade[{i}].trade_id must be int or None")
            if prev_id is not None and t.trade_id <= prev_id:
                raise ValueError(
                    f"trade_id duplicate/backward at trade[{i}]: "
                    f"{t.trade_id} <= {prev_id}"
                )
            prev_id = t.trade_id
        elif prev_id is not None:
            raise ValueError("trade_id presence must be consistent within sequence")

        prev_ts = t.ts_ms


def bar_start_ms(ts_ms: int, width_ms: int, origin_ms: int = 0) -> int:
    if width_ms <= 0:
        raise ValueError("width_ms must be > 0")
    if ts_ms < origin_ms:
        raise ValueError("ts_ms must be >= origin_ms")
    return origin_ms + ((ts_ms - origin_ms) // width_ms) * width_ms


def build_time_bars(
    trades: Sequence[Trade],
    width_ms: int,
    *,
    origin_ms: int = 0,
) -> list[Bar]:
    if width_ms <= 0:
        raise ValueError("width_ms must be > 0")
    validate_trade_sequence(trades)
    if not trades:
        return []

    out: list[Bar] = []
    current_start: int | None = None
    prices: list[float] = []
    volume = 0.0
    notional = 0.0
    buy_notional = 0.0
    sell_notional = 0.0

    def flush() -> None:
        nonlocal current_start, prices, volume, notional
        nonlocal buy_notional, sell_notional
        if current_start is None or not prices:
            return
        if volume <= 0:
            raise ValueError("bar volume must be > 0")
        out.append(
            Bar(
                start_ms=current_start,
                close_ms=current_start + width_ms,
                open=prices[0],
                high=max(prices),
                low=min(prices),
                close=prices[-1],
                volume=volume,
                notional=notional,
                vwap=notional / volume,
                trade_count=len(prices),
                buy_notional=buy_notional,
                sell_notional=sell_notional,
                signed_aggressive_notional=buy_notional - sell_notional,
            )
        )

    for t in trades:
        s = bar_start_ms(t.ts_ms, width_ms, origin_ms)
        if current_start is None:
            current_start = s
        elif s != current_start:
            flush()
            current_start = s
            prices = []
            volume = 0.0
            notional = 0.0
            buy_notional = 0.0
            sell_notional = 0.0

        n = t.notional
        prices.append(float(t.price))
        volume += float(t.size)
        notional += n
        if t.side == "buy":
            buy_notional += n
        else:
            sell_notional += n

    flush()
    return out


def completed_bars(bars: Sequence[Bar], decision_ms: int) -> list[Bar]:
    return [b for b in bars if b.close_ms <= decision_ms]


def trailing_completed_bars(
    bars: Sequence[Bar],
    decision_ms: int,
    count: int,
) -> list[Bar]:
    if count < 0:
        raise ValueError("count must be >= 0")
    if count == 0:
        return []
    eligible = completed_bars(bars, decision_ms)
    return eligible[-count:]


def return_bps(start_price: float, end_price: float) -> float:
    _finite_positive(float(start_price), "start_price")
    _finite_positive(float(end_price), "end_price")
    return (float(end_price) / float(start_price) - 1.0) * 10_000.0


def signed_response_bps(
    start_price: float,
    end_price: float,
    direction: int,
) -> float:
    if direction not in {-1, 1}:
        raise ValueError("direction must be -1 or +1")
    return direction * return_bps(start_price, end_price)


def robust_zscore(value: float, history: Sequence[float]) -> float:
    if len(history) < 3:
        raise ValueError("history must contain at least 3 values")
    vals = [float(x) for x in history]
    if not all(math.isfinite(x) for x in vals) or not math.isfinite(value):
        raise ValueError("robust_zscore inputs must be finite")
    m = median(vals)
    mad = median(abs(x - m) for x in vals)
    if mad == 0:
        raise ValueError("robust_zscore undefined for zero MAD")
    sigma = 1.4826 * mad
    return (float(value) - m) / sigma


def non_overlapping_times(event_times_ms: Iterable[int], horizon_ms: int) -> list[int]:
    if horizon_ms <= 0:
        raise ValueError("horizon_ms must be > 0")
    times = sorted(int(x) for x in event_times_ms)
    out: list[int] = []
    next_allowed: int | None = None
    for t in times:
        if next_allowed is None or t >= next_allowed:
            out.append(t)
            next_allowed = t + horizon_ms
    return out


def utc_day_bounds_ms(day: str) -> tuple[int, int]:
    d = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    lo = int(d.timestamp() * 1000)
    return lo, lo + 86_400_000


def filter_utc_day(trades: Sequence[Trade], day: str) -> list[Trade]:
    validate_trade_sequence(trades)
    lo, hi = utc_day_bounds_ms(day)
    return [t for t in trades if lo <= t.ts_ms < hi]


def stitch_filter_utc_day(
    source_d: Sequence[Trade],
    source_d1: Sequence[Trade],
    day: str,
) -> list[Trade]:
    validate_trade_sequence(source_d)
    validate_trade_sequence(source_d1)
    combined = list(source_d) + list(source_d1)
    validate_trade_sequence(combined)
    return filter_utc_day(combined, day)


def bars_equal(a: Sequence[Bar], b: Sequence[Bar], tol: float = 1e-12) -> bool:
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if (
            x.start_ms != y.start_ms
            or x.close_ms != y.close_ms
            or x.trade_count != y.trade_count
        ):
            return False
        for vx, vy in (
            (x.open, y.open),
            (x.high, y.high),
            (x.low, y.low),
            (x.close, y.close),
            (x.volume, y.volume),
            (x.notional, y.notional),
            (x.vwap, y.vwap),
            (x.buy_notional, y.buy_notional),
            (x.sell_notional, y.sell_notional),
            (x.signed_aggressive_notional, y.signed_aggressive_notional),
        ):
            if not math.isclose(vx, vy, rel_tol=tol, abs_tol=tol):
                return False
    return True
