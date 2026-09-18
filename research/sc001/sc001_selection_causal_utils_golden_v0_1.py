from __future__ import annotations

import json
import math
import os
from pathlib import Path

from sc001_selection_causal_utils_v0_1 import (
    Trade,
    bar_start_ms,
    bars_equal,
    build_time_bars,
    completed_bars,
    filter_utc_day,
    non_overlapping_times,
    return_bps,
    robust_zscore,
    signed_response_bps,
    stitch_filter_utc_day,
    trailing_completed_bars,
    utc_day_bounds_ms,
    validate_trade_sequence,
)

PASS = "SC001_SELECTION_CAUSAL_UTILS_GOLDEN_PASS"
FAIL = "SC001_SELECTION_CAUSAL_UTILS_GOLDEN_FAIL"

DATA_ROOT = Path(
    os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))
).expanduser().resolve()
OUT_DIR = DATA_ROOT / "SC001_SELECTION_CAUSAL_UTILS_GOLDEN"
OUT = OUT_DIR / "sc001_selection_causal_utils_golden_report_v0_1.json"


def atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def check(name: str, cond: bool) -> None:
    if not cond:
        raise AssertionError(name)


def expect_raises(name: str, fn) -> None:
    try:
        fn()
    except Exception:
        return
    raise AssertionError(f"{name}: expected exception")


def run() -> dict:
    checks: list[str] = []

    fixture = [
        Trade(0, 100.0, 1.0, "buy", 1),
        Trade(30_000, 110.0, 2.0, "sell", 2),
        Trade(59_999, 90.0, 1.0, "buy", 3),
        Trade(60_000, 120.0, 1.0, "buy", 4),
    ]
    bars = build_time_bars(fixture, 60_000)

    check("two bars expected", len(bars) == 2)
    check("bar0 half-open start", bars[0].start_ms == 0)
    check("bar0 close", bars[0].close_ms == 60_000)
    check("boundary trade goes to next bar", bars[1].start_ms == 60_000)
    checks.append("half_open_boundary_assignment")

    b0 = bars[0]
    check("open exact", b0.open == 100.0)
    check("high exact", b0.high == 110.0)
    check("low exact", b0.low == 90.0)
    check("close exact", b0.close == 90.0)
    check("volume exact", b0.volume == 4.0)
    check("notional exact", b0.notional == 410.0)
    check("vwap exact", math.isclose(b0.vwap, 102.5, rel_tol=0, abs_tol=1e-12))
    check("trade count exact", b0.trade_count == 3)
    check("buy notional exact", b0.buy_notional == 190.0)
    check("sell notional exact", b0.sell_notional == 220.0)
    check("signed aggressive exact", b0.signed_aggressive_notional == -30.0)
    checks.append("ohlc_vwap_notional_signed_flow_arithmetic")

    check("bar unavailable before close", completed_bars(bars, 59_999) == [])
    at_close = completed_bars(bars, 60_000)
    check("bar available exactly at close", len(at_close) == 1 and at_close[0] == b0)
    checks.append("completed_bar_availability_no_same_bar_lookahead")

    trailing = trailing_completed_bars(bars, 60_000, 5)
    check("trailing only completed", len(trailing) == 1 and trailing[0] == b0)
    checks.append("trailing_completed_history_only")

    future_fixture = fixture + [
        Trade(119_999, 121.0, 1.0, "sell", 5),
        Trade(120_000, 130.0, 1.0, "buy", 6),
    ]
    future_bars = build_time_bars(future_fixture, 60_000)
    trailing_after_future_append = trailing_completed_bars(future_bars, 60_000, 5)
    check(
        "future append invariant",
        bars_equal(trailing, trailing_after_future_append),
    )
    checks.append("future_append_does_not_mutate_historical_window")

    sparse = [
        Trade(0, 100.0, 1.0, "buy", 1),
        Trade(120_000, 101.0, 1.0, "sell", 2),
    ]
    sparse_bars = build_time_bars(sparse, 60_000)
    check(
        "no empty bar fabricated",
        [b.start_ms for b in sparse_bars] == [0, 120_000],
    )
    checks.append("empty_bars_not_fabricated")

    selected = non_overlapping_times([0, 500, 1000, 1500, 2000], 1000)
    check("non-overlap deterministic", selected == [0, 1000, 2000])
    checks.append("deterministic_non_overlap")

    expect_raises(
        "duplicate trade id fail closed",
        lambda: validate_trade_sequence(
            [
                Trade(0, 1.0, 1.0, "buy", 10),
                Trade(1, 1.0, 1.0, "sell", 10),
            ]
        ),
    )
    expect_raises(
        "backward trade id fail closed",
        lambda: validate_trade_sequence(
            [
                Trade(0, 1.0, 1.0, "buy", 10),
                Trade(1, 1.0, 1.0, "sell", 9),
            ]
        ),
    )
    checks.append("duplicate_backward_trade_ids_fail_closed")

    lo, hi = utc_day_bounds_ms("2024-07-01")
    source_d = [
        Trade(lo - 1, 100.0, 1.0, "buy", 1),
        Trade(lo + 1, 101.0, 1.0, "buy", 2),
    ]
    source_d1 = [
        Trade(hi - 1, 102.0, 1.0, "sell", 3),
        Trade(hi, 103.0, 1.0, "sell", 4),
    ]
    stitched = stitch_filter_utc_day(source_d, source_d1, "2024-07-01")
    check("utc stitch retained two", len(stitched) == 2)
    check("utc stitch exact ids", [t.trade_id for t in stitched] == [2, 3])
    check("utc stitch lower bound", all(lo <= t.ts_ms for t in stitched))
    check("utc stitch upper bound", all(t.ts_ms < hi for t in stitched))
    checks.append("d_plus_d1_utc_half_open_filter")

    check("bar start at boundary", bar_start_ms(60_000, 60_000) == 60_000)
    check("return bps exact", math.isclose(return_bps(100, 101), 100.0))
    check("signed response exact", math.isclose(signed_response_bps(100, 101, -1), -100.0))
    checks.append("return_and_direction_sign")

    hist = [-2.0, -1.0, 0.0, 1.0, 2.0]
    z = robust_zscore(3.0, hist)
    check("robust z finite positive", math.isfinite(z) and z > 0)
    checks.append("robust_z_history_only_primitive")

    rep = {
        "stage": "SC001-SELECTION-CAUSAL-UTILS-GOLDEN-V0.1",
        "status": PASS,
        "checks_passed": checks,
        "check_count": len(checks),
        "market_data_body_required": False,
        "strategy_signal_calculated": False,
        "sentinel_outcome_calculated": False,
        "pnl_calculated": False,
        "protected_market_data_accessed": False,
        "promotional_alpha_accessed": False,
        "sentinel_variant_budget": 11,
    }
    atomic_json(OUT, rep)
    return rep


def main() -> int:
    try:
        rep = run()
    except Exception as exc:
        fail_rep = {
            "stage": "SC001-SELECTION-CAUSAL-UTILS-GOLDEN-V0.1",
            "status": FAIL,
            "error": f"{type(exc).__name__}: {exc}",
            "strategy_signal_calculated": False,
            "sentinel_outcome_calculated": False,
            "pnl_calculated": False,
            "protected_market_data_accessed": False,
            "promotional_alpha_accessed": False,
            "sentinel_variant_budget": 11,
        }
        try:
            atomic_json(OUT, fail_rep)
        except Exception:
            pass
        print(FAIL)
        print("error =", fail_rep["error"])
        print("report =", OUT)
        return 2

    print(PASS)
    print("checks_passed =", rep["check_count"])
    print("market_data_body_required = False")
    print("strategy signal / sentinel outcome / PnL = False")
    print("protected market data accessed = False")
    print("promotional alpha accessed = False")
    print("sentinel variant budget = 11")
    print("report =", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
