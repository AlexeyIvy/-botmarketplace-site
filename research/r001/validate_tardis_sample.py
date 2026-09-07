"""R001 Data Validation Gate for a Tardis Deribit options_chain sample.

Research-only utility. It audits one complete daily OPTIONS.csv.gz before any
portfolio/backtest simulator is trusted.

Usage:
    python research/r001/validate_tardis_sample.py /path/to/OPTIONS.csv.gz

The gate reports data quality and selection coverage. It does not claim that a
strategy is profitable.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Iterable

from option_selector import OptionQuote, SelectionConfig, parse_row, select_option
from tardis_options_adapter import iter_gzip_csv

MICROS_PER_SECOND = 1_000_000
MICROS_PER_DAY = 86_400_000_000


@dataclass
class AuditResult:
    rows: int
    symbols: int
    puts: int
    calls: int
    expiries: int
    pct_two_sided: float
    pct_delta: float
    pct_underlying: float
    pct_non_crossed: float
    min_timestamp_us: int
    max_timestamp_us: int
    max_abs_clock_lag_seconds: float
    duplicate_exchange_updates: int
    selection_checks: int
    selection_successes: int

    @property
    def selection_success_rate(self) -> float:
        if self.selection_checks == 0:
            return 0.0
        return self.selection_successes / self.selection_checks


def _pct(n: int, d: int) -> float:
    return 0.0 if d == 0 else 100.0 * n / d


def audit_rows(rows: list[dict]) -> AuditResult:
    if not rows:
        raise ValueError("sample contains no rows")

    required = {
        "exchange", "symbol", "timestamp", "local_timestamp", "type",
        "strike_price", "expiration", "bid_price", "ask_price",
        "underlying_price", "delta",
    }
    missing = sorted(required - set(rows[0].keys()))
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")

    n = len(rows)
    symbols = {r["symbol"] for r in rows if r.get("symbol")}
    expiries = {r["expiration"] for r in rows if r.get("expiration") is not None}
    puts = sum(r.get("type") == "put" for r in rows)
    calls = sum(r.get("type") == "call" for r in rows)

    two_sided = 0
    has_delta = 0
    has_underlying = 0
    non_crossed = 0
    clock_lags = []
    key_counts = Counter()

    for r in rows:
        bid = r.get("bid_price")
        ask = r.get("ask_price")
        if bid is not None and ask is not None and bid >= 0 and ask > 0:
            two_sided += 1
            if bid <= ask:
                non_crossed += 1
        if r.get("delta") is not None:
            has_delta += 1
        if r.get("underlying_price") is not None:
            has_underlying += 1

        ts = r.get("timestamp")
        lts = r.get("local_timestamp")
        if ts is not None and lts is not None:
            clock_lags.append(abs(lts - ts) / MICROS_PER_SECOND)

        if ts is not None and r.get("symbol"):
            key_counts[(r["symbol"], ts)] += 1

    timestamps = [r["timestamp"] for r in rows if r.get("timestamp") is not None]
    duplicate_updates = sum(c - 1 for c in key_counts.values() if c > 1)

    # Build one latest quote per symbol at several deterministic decision times.
    # This checks whether 10Δ/15Δ/20Δ puts and calls around ~90 DTE are actually
    # selectable from the observed sample without future information.
    by_symbol = defaultdict(list)
    for r in rows:
        by_symbol[r["symbol"]].append(r)
    for values in by_symbol.values():
        values.sort(key=lambda x: x["timestamp"])

    start = min(timestamps)
    end = max(timestamps)
    decision_times = [
        start + (end - start) * frac // 4 for frac in (1, 2, 3)
    ]

    checks = 0
    successes = 0
    for decision_ts in decision_times:
        latest = []
        for values in by_symbol.values():
            candidate = None
            for r in values:
                if r["timestamp"] <= decision_ts:
                    candidate = r
                else:
                    break
            if candidate is not None:
                latest.append(parse_row({k: "" if v is None else str(v) for k, v in candidate.items()}))

        for option_type in ("put", "call"):
            for delta in (0.10, 0.15, 0.20):
                checks += 1
                try:
                    select_option(
                        latest,
                        decision_ts,
                        SelectionConfig(
                            option_type=option_type,
                            target_abs_delta=delta,
                            target_dte=90.0,
                            min_dte=45.0,
                            max_dte=120.0,
                            max_quote_age_seconds=900.0,
                            require_two_sided=True,
                        ),
                    )
                    successes += 1
                except ValueError:
                    pass

    return AuditResult(
        rows=n,
        symbols=len(symbols),
        puts=puts,
        calls=calls,
        expiries=len(expiries),
        pct_two_sided=_pct(two_sided, n),
        pct_delta=_pct(has_delta, n),
        pct_underlying=_pct(has_underlying, n),
        pct_non_crossed=_pct(non_crossed, two_sided),
        min_timestamp_us=min(timestamps),
        max_timestamp_us=max(timestamps),
        max_abs_clock_lag_seconds=max(clock_lags) if clock_lags else 0.0,
        duplicate_exchange_updates=duplicate_updates,
        selection_checks=checks,
        selection_successes=successes,
    )


def gate_decision(result: AuditResult) -> tuple[str, list[str]]:
    """Conservative data gate. Thresholds are quality checks, not alpha tests."""
    reasons: list[str] = []
    if result.rows < 1000:
        reasons.append("too few rows for a full-day tick sample")
    if result.symbols < 20:
        reasons.append("too few distinct option instruments")
    if result.expiries < 2:
        reasons.append("insufficient expiry coverage")
    if result.pct_delta < 95:
        reasons.append("delta coverage below 95%")
    if result.pct_underlying < 95:
        reasons.append("underlying-price coverage below 95%")
    if result.pct_non_crossed < 99:
        reasons.append("too many crossed two-sided quotes")
    if result.selection_success_rate < 0.50:
        reasons.append("insufficient 10/15/20Δ ~90D selection coverage")

    return ("PASS" if not reasons else "FAIL", reasons)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("sample", type=Path)
    args = parser.parse_args()

    rows = list(iter_gzip_csv(args.sample))
    result = audit_rows(rows)
    decision, reasons = gate_decision(result)

    print("R001 Tardis Data Validation Gate")
    print(f"rows: {result.rows}")
    print(f"symbols: {result.symbols}")
    print(f"puts/calls: {result.puts}/{result.calls}")
    print(f"expiries: {result.expiries}")
    print(f"two-sided quotes: {result.pct_two_sided:.2f}%")
    print(f"delta coverage: {result.pct_delta:.2f}%")
    print(f"underlying coverage: {result.pct_underlying:.2f}%")
    print(f"non-crossed among two-sided: {result.pct_non_crossed:.2f}%")
    print(f"max |local-exchange timestamp lag|: {result.max_abs_clock_lag_seconds:.3f}s")
    print(f"duplicate (symbol,timestamp) updates: {result.duplicate_exchange_updates}")
    print(
        "selection coverage: "
        f"{result.selection_successes}/{result.selection_checks} "
        f"({100*result.selection_success_rate:.1f}%)"
    )
    print(f"GATE: {decision}")
    for reason in reasons:
        print(f"- {reason}")


if __name__ == "__main__":
    main()
