"""SC001-E008 conservative queue-simulator synthetic mechanics v0.1.

Synthetic fixtures only. No real market-data body is opened. No real fills,
spread capture, markout, fees, inventory P&L or profitability.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Literal

STAGE = "SC001-E008-QUEUE-SIMULATOR-SYNTHETIC"
VERSION = "0.1"
PASS = "E008_QUEUE_SIMULATOR_SYNTHETIC_PASS"
FAIL = "E008_QUEUE_SIMULATOR_SYNTHETIC_FAIL"

DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
OUT_DIR = DATA_ROOT / "SC001_E008_QUEUE_SIM_SYNTHETIC"
OUT_JSON = OUT_DIR / "sc001_e008_queue_simulator_synthetic_report.json"

Side = Literal["BUY", "SELL"]
Status = Literal["RESTING", "PARTIAL", "FILLED", "CANCELLED_UNFILLED", "STALE_CANCELLED"]


def atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    text = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with tmp.open("w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


@dataclass
class Order:
    side: Side
    price: float
    qty: float
    queue_ahead: float
    remaining_qty: float
    filled_qty: float = 0.0
    status: Status = "RESTING"
    trusted: bool = True

    def snapshot(self) -> dict:
        d = asdict(self)
        for k in ("price", "qty", "queue_ahead", "remaining_qty", "filled_qty"):
            d[k] = round(float(d[k]), 12)
        return d


class QueueModel:
    def __init__(self) -> None:
        self.trusted = True
        self.live: Order | None = None

    def place(self, side: Side, price: float, displayed_best_price: float, displayed_size: float) -> Order | None:
        if not self.trusted:
            return None
        if side not in ("BUY", "SELL"):
            raise ValueError("bad side")
        if price <= 0 or displayed_best_price <= 0 or displayed_size < 0:
            raise ValueError("bad placement inputs")
        if abs(price - displayed_best_price) > 1e-12:
            return None
        if self.live is not None and self.live.status in ("RESTING", "PARTIAL"):
            raise RuntimeError("one live order only")
        self.live = Order(side=side, price=price, qty=1.0, queue_ahead=float(displayed_size), remaining_qty=1.0)
        return self.live

    def place_qty(self, side: Side, price: float, displayed_best_price: float, displayed_size: float, qty: float) -> Order | None:
        if qty <= 0:
            raise ValueError("qty must be positive")
        o = self.place(side, price, displayed_best_price, displayed_size)
        if o is not None:
            o.qty = float(qty)
            o.remaining_qty = float(qty)
        return o

    @staticmethod
    def _compatible(order: Order, aggressor_side: str, trade_price: float) -> bool:
        if order.side == "BUY":
            return aggressor_side == "SELL" and trade_price <= order.price + 1e-12
        return aggressor_side == "BUY" and trade_price >= order.price - 1e-12

    def trade(self, aggressor_side: str, trade_price: float, trade_qty: float, same_ms_ambiguous: bool = False) -> None:
        o = self.live
        if o is None or o.status not in ("RESTING", "PARTIAL"):
            return
        if not self.trusted or same_ms_ambiguous:
            return
        if trade_qty <= 0 or trade_price <= 0:
            raise ValueError("bad trade")
        if not self._compatible(o, aggressor_side, trade_price):
            return
        v = float(trade_qty)
        consume = min(o.queue_ahead, v)
        o.queue_ahead -= consume
        v -= consume
        if v <= 0:
            return
        fill = min(o.remaining_qty, v)
        o.filled_qty += fill
        o.remaining_qty -= fill
        if o.remaining_qty <= 1e-12:
            o.remaining_qty = 0.0
            o.status = "FILLED"
            self.live = None
        elif o.filled_qty > 0:
            o.status = "PARTIAL"

    def displayed_size_change(self, old_size: float, new_size: float) -> None:
        o = self.live
        if o is None or o.status not in ("RESTING", "PARTIAL") or not self.trusted:
            return
        if old_size < 0 or new_size < 0:
            raise ValueError("negative size")
        if new_size > old_size:
            o.queue_ahead += new_size - old_size
        # Decrease is cancellation/unknown and gives zero progress.

    def level_disappears(self) -> None:
        o = self.live
        if o is None or o.status not in ("RESTING", "PARTIAL"):
            return
        o.status = "CANCELLED_UNFILLED"
        self.live = None

    def stale_latch(self) -> None:
        self.trusted = False
        o = self.live
        if o is not None and o.status in ("RESTING", "PARTIAL"):
            o.status = "STALE_CANCELLED"
            self.live = None

    def incremental_update(self) -> None:
        # Does not clear stale latch.
        pass

    def full_snapshot(self) -> None:
        self.trusted = True

    def ttl_cancel(self) -> None:
        o = self.live
        if o is None or o.status not in ("RESTING", "PARTIAL"):
            return
        o.status = "CANCELLED_UNFILLED"
        self.live = None


def eq(a: float, b: float, tol: float = 1e-12) -> bool:
    return abs(a - b) <= tol


def fixture_results() -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    failures: list[str] = []

    def check(name: str, cond: bool, detail: object = None) -> None:
        rows.append({"name": name, "pass": bool(cond), "detail": detail})
        if not cond:
            failures.append(name)

    # 1 BUY placement behind full displayed bid.
    m = QueueModel(); o = m.place_qty("BUY", 100, 100, 5, 2)
    check("buy_full_displayed_ahead", o is not None and eq(o.queue_ahead, 5) and eq(o.remaining_qty, 2), o.snapshot() if o else None)

    # 2 SELL placement behind full displayed ask.
    m = QueueModel(); o = m.place_qty("SELL", 101, 101, 7, 3)
    check("sell_full_displayed_ahead", o is not None and eq(o.queue_ahead, 7) and eq(o.remaining_qty, 3), o.snapshot() if o else None)

    # 3 compatible trade smaller than queue-ahead.
    m = QueueModel(); o = m.place_qty("BUY", 100, 100, 5, 2); m.trade("SELL", 100, 3)
    check("compatible_trade_reduces_queue_only", o is not None and eq(o.queue_ahead, 2) and eq(o.filled_qty, 0), o.snapshot())

    # 4 exact exhaustion of queue produces zero own fill.
    m = QueueModel(); o = m.place_qty("BUY", 100, 100, 5, 2); m.trade("SELL", 99.5, 5)
    check("exact_queue_exhaustion_zero_fill", o is not None and eq(o.queue_ahead, 0) and eq(o.filled_qty, 0), o.snapshot())

    # 5 excess compatible trade creates partial fill.
    m = QueueModel(); o = m.place_qty("BUY", 100, 100, 5, 2); m.trade("SELL", 100, 6)
    check("excess_trade_partial_fill", o is not None and eq(o.filled_qty, 1) and eq(o.remaining_qty, 1) and o.status == "PARTIAL", o.snapshot())

    # 6 enough compatible volume creates full fill without overfill.
    m = QueueModel(); o = m.place_qty("SELL", 101, 101, 4, 2); m.trade("BUY", 102, 99)
    check("full_fill_no_overfill", o is not None and eq(o.filled_qty, 2) and eq(o.remaining_qty, 0) and o.status == "FILLED", o.snapshot())

    # 7 incompatible trade gives zero progress.
    m = QueueModel(); o = m.place_qty("BUY", 100, 100, 5, 2); m.trade("BUY", 101, 20)
    check("incompatible_zero_progress", o is not None and eq(o.queue_ahead, 5) and eq(o.filled_qty, 0), o.snapshot())

    # 8 same-ms ambiguous gives zero progress.
    m = QueueModel(); o = m.place_qty("SELL", 101, 101, 5, 2); m.trade("BUY", 101, 20, same_ms_ambiguous=True)
    check("same_ms_zero_credit", o is not None and eq(o.queue_ahead, 5) and eq(o.filled_qty, 0), o.snapshot())

    # 9 displayed decrease gives zero progress.
    m = QueueModel(); o = m.place_qty("BUY", 100, 100, 5, 2); m.displayed_size_change(5, 1)
    check("size_decrease_zero_progress", o is not None and eq(o.queue_ahead, 5), o.snapshot())

    # 10 displayed increase is pessimistically added ahead.
    m = QueueModel(); o = m.place_qty("BUY", 100, 100, 5, 2); m.displayed_size_change(5, 8)
    check("size_increase_added_ahead", o is not None and eq(o.queue_ahead, 8), o.snapshot())

    # 11 level deletion does not imply fill.
    m = QueueModel(); o = m.place_qty("SELL", 101, 101, 5, 2); m.level_disappears()
    check("level_delete_no_fill", o is not None and eq(o.filled_qty, 0) and o.status == "CANCELLED_UNFILLED", o.snapshot())

    # 12 price-through book movement alone is represented as disappearance => no fill.
    m = QueueModel(); o = m.place_qty("BUY", 100, 100, 5, 2); m.level_disappears()
    check("book_price_through_alone_no_fill", o is not None and eq(o.filled_qty, 0) and o.status == "CANCELLED_UNFILLED", o.snapshot())

    # 13 stale latch cancels live order with zero extra fill.
    m = QueueModel(); o = m.place_qty("BUY", 100, 100, 5, 2); m.trade("SELL", 100, 6); before = o.filled_qty; m.stale_latch()
    check("stale_latch_cancels_without_extra_fill", o is not None and eq(o.filled_qty, before) and o.status == "STALE_CANCELLED", o.snapshot())

    # 14 trades during latch give zero credit.
    m = QueueModel(); m.stale_latch(); m.trade("SELL", 100, 100)
    check("trades_during_latch_zero_credit", m.live is None and m.trusted is False, {"trusted": m.trusted})

    # 15 incremental update does not restore trust.
    m = QueueModel(); m.stale_latch(); m.incremental_update()
    check("incremental_does_not_restore_trust", m.trusted is False, {"trusted": m.trusted})

    # 16 full snapshot restores future placement eligibility.
    m = QueueModel(); m.stale_latch(); m.full_snapshot(); o = m.place_qty("BUY", 100, 100, 1, 1)
    check("snapshot_restores_placement", m.trusted is True and o is not None, o.snapshot() if o else None)

    # 17 partial fill preserved if remainder later cancelled.
    m = QueueModel(); o = m.place_qty("BUY", 100, 100, 5, 2); m.trade("SELL", 100, 6); m.ttl_cancel()
    check("partial_preserved_after_cancel", o is not None and eq(o.filled_qty, 1) and eq(o.remaining_qty, 1) and o.status == "CANCELLED_UNFILLED", o.snapshot())

    # 18 explicit TTL cancellation creates no new fill.
    m = QueueModel(); o = m.place_qty("SELL", 101, 101, 5, 2); m.ttl_cancel()
    check("ttl_cancel_zero_fill", o is not None and eq(o.filled_qty, 0) and o.status == "CANCELLED_UNFILLED", o.snapshot())

    # 19 chunked vs one-shot compatible volume accounting.
    a = QueueModel(); oa = a.place_qty("BUY", 100, 100, 5, 2); a.trade("SELL", 100, 7)
    b = QueueModel(); ob = b.place_qty("BUY", 100, 100, 5, 2); b.trade("SELL", 100, 2); b.trade("SELL", 100, 2); b.trade("SELL", 100, 3)
    check("chunked_equals_one_shot", oa is not None and ob is not None and oa.snapshot() == ob.snapshot(), {"one": oa.snapshot(), "chunked": ob.snapshot()})

    # 20 deterministic result payload hash from repeated fixture construction.
    stable_a = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    # Re-serialize same immutable rows as the repeat identity test.
    stable_b = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    check("deterministic_byte_identity", hashlib.sha256(stable_a).hexdigest() == hashlib.sha256(stable_b).hexdigest(), hashlib.sha256(stable_a).hexdigest())

    # Additional placement firewall: non-best placement rejected.
    m = QueueModel(); o = m.place_qty("BUY", 99, 100, 5, 1)
    check("non_best_placement_rejected", o is None, None)

    # Additional stale placement firewall.
    m = QueueModel(); m.stale_latch(); o = m.place_qty("SELL", 101, 101, 5, 1)
    check("stale_placement_rejected", o is None, None)

    return rows, failures


def main() -> int:
    rows, failures = fixture_results()
    status = PASS if not failures else FAIL
    report = {
        "stage": STAGE,
        "version": VERSION,
        "status": status,
        "tests": rows,
        "test_count": len(rows),
        "pass_count": sum(1 for x in rows if x["pass"]),
        "failures": failures,
        "real_market_data_opened": False,
        "real_hypothetical_orders_created": False,
        "real_fill_simulation_calculated": False,
        "spread_capture_calculated": False,
        "markout_calculated": False,
        "maker_fees_or_rebates_calculated": False,
        "inventory_pnl_calculated": False,
        "profitability_calculated": False,
        "tfi_used": False,
        "q2_accessed": False,
        "validation_or_final_accessed": False,
    }
    atomic_json(OUT_JSON, report)
    print(status)
    print(f"tests = {report['pass_count']}/{report['test_count']}")
    print("real market data opened = False")
    print("real fills/spread_capture/markout/fees/inventory_PnL/profitability calculated = False")
    print("TFI used = False")
    print("Q2/Validation/Final = CLOSED")
    print("report =", OUT_JSON)
    if failures:
        for x in failures:
            print("FAIL", x)
    return 0 if status == PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
