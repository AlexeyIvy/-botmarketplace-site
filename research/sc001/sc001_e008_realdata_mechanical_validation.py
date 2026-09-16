"""SC001-E008 non-promotional real-data mechanical queue validation v0.1.

Uses only four contaminated engineering days. Creates deterministic probe orders
solely to validate frozen queue/state mechanics. NO spread capture, markout,
fees/rebates, inventory P&L or profitability.
"""
from __future__ import annotations

import itertools
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import sc001_e008_queue_audit_lib as L
from sc001_e008_queue_simulator_synthetic_v0_1 import QueueModel

STAGE = "SC001-E008-REALDATA-MECHANICAL-VALIDATION"
VERSION = "0.1"
PASS = "E008_QUEUE_SIMULATOR_MECHANICAL_PASS"
REVIEW = "E008_QUEUE_SIMULATOR_MECHANICAL_REVIEW"
SCHEDULE_MS = 15 * 60 * 1000
PLACEMENT_LAG_MS = 1000
TTL_MS = 60_000
STALE_MS = 5000
QTY = 1.0

ROOT = L.DATA_ROOT
OUT_DIR = ROOT / "SC001_E008_REALDATA_MECHANICAL_VALIDATION"
OUT_JSON = OUT_DIR / "sc001_e008_realdata_mechanical_validation_report.json"
SYNTH_REPORT = ROOT / "SC001_E008_QUEUE_SIM_SYNTHETIC" / "sc001_e008_queue_simulator_synthetic_report.json"
STALE_REPORT = ROOT / "SC001_E008_STALE_LATCH_MODEL" / "sc001_e008_stale_latch_model_report.json"


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def prereqs() -> tuple[dict, dict, dict]:
    inv, q6 = L.qualified_state()
    synth = L.load_json(SYNTH_REPORT)
    stale = L.load_json(STALE_REPORT)
    if synth.get("status") != "E008_QUEUE_SIMULATOR_SYNTHETIC_PASS":
        fail("synthetic queue simulator is not PASS")
    if synth.get("real_market_data_opened") is not False or synth.get("profitability_calculated") is not False:
        fail("synthetic firewall mismatch")
    if stale.get("status") != "E008_STALE_LATCH_MODEL_PASS":
        fail("stale-latch model is not PASS")
    for key in ("fill_simulation_calculated", "spread_capture_calculated", "inventory_calculated", "maker_pnl_calculated", "profitability_calculated"):
        if stale.get(key) is not False:
            fail(f"stale-latch firewall mismatch: {key}")
    return inv, q6, {"synthetic": synth.get("status"), "stale_latch": stale.get("status")}


def valid_book(asks, bids, ap, bp) -> bool:
    if not ap or not bp:
        return False
    bid, ask = bp[-1], ap[0]
    if bid >= ask:
        return False
    bs, bo = bids[bid]
    a_s, ao = asks[ask]
    return bs > 0 and a_s > 0 and bo > 0 and ao > 0


def validate_day(day: str, l2_path: Path, trade: dict) -> dict:
    lo, hi = L.day_bounds(day)
    schedules = [lo + i * SCHEDULE_MS for i in range(96)]
    slot = 0

    asks, bids, ap, bp = {}, {}, [], []
    model = QueueModel()
    model.trusted = False
    last_l2_ts = None
    live_order = None
    live_ttl = None

    placed = 0
    skipped = 0
    max_concurrent = 0
    outcomes = Counter()
    partial_cancel_count = 0
    credited_fill_qty = 0.0
    stale_latch_count = 0
    same_ms_ambiguous = 0
    size_increase_events = 0
    size_decrease_events = 0
    level_disappear_events = 0
    snapshot_resync_cancels = 0
    ttl_cancels = 0
    invariant_errors: list[str] = []

    ti = 0
    ntr = int(trade["rows"])

    def finish(reason: str) -> None:
        nonlocal live_order, live_ttl, partial_cancel_count, credited_fill_qty
        if live_order is None:
            return
        qty = float(live_order.filled_qty)
        if qty < -1e-12 or qty > QTY + 1e-12:
            invariant_errors.append(f"filled_qty_out_of_bounds:{qty}")
        credited_fill_qty += max(0.0, min(QTY, qty))
        if qty > 1e-12 and live_order.status != "FILLED":
            partial_cancel_count += 1
        outcomes[reason] += 1
        live_order = None
        live_ttl = None

    def maybe_time_controls(t: int) -> None:
        nonlocal stale_latch_count, ttl_cancels
        if live_order is not None and live_ttl is not None and live_ttl <= t:
            model.ttl_cancel()
            ttl_cancels += 1
            finish("TTL_CANCELLED")
        if model.trusted and last_l2_ts is not None and t > last_l2_ts + STALE_MS:
            model.stale_latch()
            stale_latch_count += 1
            if live_order is not None:
                finish("STALE_CANCELLED")

    def process_trade(i: int, ambiguous: bool = False) -> None:
        nonlocal same_ms_ambiguous
        t = int(trade["ts"][i])
        maybe_time_controls(t)
        if ambiguous:
            same_ms_ambiguous += 1
            # Explicit zero-credit path.
            return
        if live_order is None or not model.trusted:
            return
        side = "BUY" if bool(trade["side"][i]) else "SELL"
        model.trade(side, float(trade["px"][i]), float(trade["sz"][i]), same_ms_ambiguous=False)
        if live_order.status == "FILLED":
            finish("FILLED")

    def advance_schedules_at_l2(t: int) -> None:
        nonlocal slot, placed, skipped, live_order, live_ttl, max_concurrent
        while slot < len(schedules) and t > schedules[slot] + PLACEMENT_LAG_MS:
            skipped += 1
            slot += 1
        if slot >= len(schedules):
            return
        sched = schedules[slot]
        if not (sched <= t <= sched + PLACEMENT_LAG_MS):
            return
        if not model.trusted or not valid_book(asks, bids, ap, bp):
            return
        if live_order is not None:
            invariant_errors.append("overlap_at_schedule")
            return
        side = "BUY" if slot % 2 == 0 else "SELL"
        if side == "BUY":
            p = bp[-1]
            displayed = float(bids[p][0])
        else:
            p = ap[0]
            displayed = float(asks[p][0])
        o = model.place_qty(side, float(p), float(p), displayed, QTY)
        if o is None:
            invariant_errors.append("trusted_best_placement_rejected")
            return
        live_order = o
        live_ttl = t + TTL_MS
        placed += 1
        max_concurrent = max(max_concurrent, 1)
        slot += 1

    for t, group in itertools.groupby(L.iter_l2(l2_path), key=lambda x: x[0]):
        t = int(t)
        while ti < ntr and int(trade["ts"][ti]) < t:
            process_trade(ti, False)
            ti += 1
        maybe_time_controls(t)
        while ti < ntr and int(trade["ts"][ti]) == t:
            process_trade(ti, True)
            ti += 1

        rows = list(group)
        has_snapshot = any(a == "snapshot" for _tt, a, _aa, _bb in rows)
        old_size = None
        old_price_present = False
        if live_order is not None:
            book = bids if live_order.side == "BUY" else asks
            if live_order.price in book:
                old_price_present = True
                old_size = float(book[live_order.price][0])

        if has_snapshot and live_order is not None:
            model.ttl_cancel()
            snapshot_resync_cancels += 1
            finish("SNAPSHOT_RESYNC_CANCELLED")

        for _tt, action, aa, bb in rows:
            if action == "snapshot":
                asks.clear(); bids.clear(); ap.clear(); bp.clear()
            L.apply(asks, ap, aa)
            L.apply(bids, bp, bb)

        if has_snapshot:
            model.full_snapshot()
        else:
            model.incremental_update()
        last_l2_ts = t

        if model.trusted and not valid_book(asks, bids, ap, bp):
            if live_order is not None:
                model.level_disappears()
                level_disappear_events += 1
                finish("INVALID_BOOK_CANCELLED")
            model.trusted = False

        if live_order is not None and model.trusted:
            book = bids if live_order.side == "BUY" else asks
            if live_order.price not in book:
                model.level_disappears()
                level_disappear_events += 1
                finish("LEVEL_DISAPPEAR_CANCELLED")
            elif old_price_present and old_size is not None:
                new_size = float(book[live_order.price][0])
                if new_size > old_size + 1e-12:
                    size_increase_events += 1
                elif new_size < old_size - 1e-12:
                    size_decrease_events += 1
                model.displayed_size_change(old_size, new_size)

        advance_schedules_at_l2(t)

    while ti < ntr:
        process_trade(ti, False)
        ti += 1

    maybe_time_controls(hi)
    if live_order is not None:
        model.ttl_cancel()
        ttl_cancels += 1
        finish("DAY_END_CANCELLED")

    while slot < len(schedules):
        skipped += 1
        slot += 1

    terminal = sum(outcomes.values())
    if placed != terminal:
        invariant_errors.append(f"placed_vs_terminal:{placed}!={terminal}")
    if placed + skipped != 96:
        invariant_errors.append(f"schedule_accounting:{placed}+{skipped}!=96")
    if max_concurrent > 1:
        invariant_errors.append(f"max_concurrent:{max_concurrent}")

    return {
        "date": day,
        "scheduled_probes": 96,
        "placed_probes": placed,
        "skipped_no_trusted_state": skipped,
        "terminal_outcomes": dict(sorted(outcomes.items())),
        "partial_before_cancel_count": partial_cancel_count,
        "credited_fill_qty_units": round(credited_fill_qty, 12),
        "same_ms_ambiguous_trade_count": same_ms_ambiguous,
        "stale_latch_count": stale_latch_count,
        "size_increase_events_while_live": size_increase_events,
        "size_decrease_events_while_live_zero_credit": size_decrease_events,
        "level_disappear_events": level_disappear_events,
        "snapshot_resync_cancels": snapshot_resync_cancels,
        "ttl_cancels": ttl_cancels,
        "max_concurrent_live_probes": max_concurrent,
        "invariant_errors": invariant_errors,
        "day_pass": not invariant_errors,
    }


def main() -> int:
    inv, q6, parents = prereqs()
    rows = []
    errors = []
    for day in L.DAYS:
        try:
            l2, l2_bytes, l2_sha = L.resolve_l2(inv, day)
            ep, np = L.resolve_trades(q6[day])
            print(f"MECHANICAL VALIDATION {day}: load UTC trades")
            tr = L.load_trade_day(day, ep, np)
            print(f"MECHANICAL VALIDATION {day}: replay probes")
            r = validate_day(day, l2, tr)
            r.update({"l2_bytes": l2_bytes, "l2_sha256": l2_sha})
            rows.append(r)
            print(f"MECHANICAL VALIDATION {day} {'PASS' if r['day_pass'] else 'REVIEW'} placed={r['placed_probes']} skipped={r['skipped_no_trusted_state']} outcomes={r['terminal_outcomes']}")
        except Exception as exc:
            msg = f"{day}: {type(exc).__name__}: {exc}"
            errors.append(msg)
            rows.append({"date": day, "day_pass": False, "error": msg})
            print("MECHANICAL VALIDATION REVIEW", msg)

    passed = len(rows) == 4 and all(x.get("day_pass") for x in rows) and not errors
    status = PASS if passed else REVIEW
    report = {
        "stage": STAGE,
        "version": VERSION,
        "status": status,
        "prerequisites": parents,
        "probe_schedule": {
            "interval_ms": SCHEDULE_MS,
            "placement_lag_ms": PLACEMENT_LAG_MS,
            "ttl_ms": TTL_MS,
            "qty_units": QTY,
            "side_rule": "even_slot_BUY_odd_slot_SELL",
        },
        "days": rows,
        "errors": errors,
        "engineering_days_are_non_promotional": True,
        "real_hypothetical_orders_created_for_mechanics_only": True,
        "real_fill_mechanics_calculated": True,
        "spread_capture_calculated": False,
        "markout_calculated": False,
        "maker_fees_or_rebates_calculated": False,
        "inventory_pnl_calculated": False,
        "profitability_calculated": False,
        "tfi_used": False,
        "q2_accessed": False,
        "validation_or_final_accessed": False,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    atomic_json(OUT_JSON, report)
    print(status)
    print("qualified_day_count =", sum(1 for x in rows if x.get("day_pass")), "/ 4")
    print("engineering days promotional = False")
    print("spread_capture/markout/fees/inventory_PnL/profitability calculated = False")
    print("TFI used = False")
    print("Q2/Validation/Final = CLOSED")
    print("report =", OUT_JSON)
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
