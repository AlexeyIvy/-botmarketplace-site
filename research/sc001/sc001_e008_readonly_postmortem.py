"""SC001-E008 read-only postmortem.

Consumes only already-produced terminal artifacts. It does not rerun the maker
strategy, create orders/fills, alter gates, or open Confirmation/Q2/Validation/Final.
"""
from __future__ import annotations

import json
import math
import os
import statistics
from collections import Counter
from pathlib import Path

STAGE = "SC001-E008-READONLY-POSTMORTEM"
VERSION = "1.0"
PASS = "E008_READONLY_POSTMORTEM_PASS"

DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
MAKER_DIR = DATA_ROOT / "SC001_E008_MAKER_DISCOVERY"
MAKER_REPORT = MAKER_DIR / "sc001_e008_maker_discovery_report.json"
PREFLIGHT_REPORT = MAKER_DIR / "sc001_e008_maker_discovery_preflight_report.json"
SEMANTIC_REPORT = DATA_ROOT / "SC001_E008_DISCOVERY_SEMANTIC_INTEGRITY" / "sc001_e008_discovery_semantic_integrity_report.json"
OUT_DIR = DATA_ROOT / "SC001_E008_READONLY_POSTMORTEM"
OUT_JSON = OUT_DIR / "sc001_e008_readonly_postmortem_report.json"


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing JSON: {path}")
    x = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x, dict):
        fail(f"JSON object expected: {path}")
    return x


def atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    text = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with tmp.open("w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def q(vals: list[float], p: float) -> float | None:
    if not vals:
        return None
    xs = sorted(float(x) for x in vals)
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * p
    lo = int(math.floor(pos)); hi = int(math.ceil(pos))
    if lo == hi:
        return xs[lo]
    w = pos - lo
    return xs[lo] * (1.0 - w) + xs[hi] * w


def mean(vals: list[float]) -> float | None:
    return statistics.fmean(vals) if vals else None


def cycle_group(cycles: list[dict]) -> dict:
    gross = [float(c["gross_edge_bps"]) for c in cycles]
    net = [float(c["net_edge_bps"]) for c in cycles]
    fee_drag = [g - n for g, n in zip(gross, net)]
    durations = [float(c.get("duration_ms", 0)) for c in cycles]
    fill_counts = [int(c.get("fill_count", 0)) for c in cycles]
    maker_fills = 0
    taker_fills = 0
    maker_qty = 0.0
    taker_qty = 0.0
    for c in cycles:
        for f in c.get("fills", []):
            liq = str(f.get("liquidity", ""))
            qty = float(f.get("qty", 0.0))
            if liq == "maker":
                maker_fills += 1; maker_qty += qty
            elif liq == "taker":
                taker_fills += 1; taker_qty += qty
    return {
        "cycles": len(cycles),
        "mean_gross_edge_bps": mean(gross),
        "median_gross_edge_bps": statistics.median(gross) if gross else None,
        "mean_net_edge_bps": mean(net),
        "median_net_edge_bps": statistics.median(net) if net else None,
        "mean_realized_fee_drag_bps": mean(fee_drag),
        "median_realized_fee_drag_bps": statistics.median(fee_drag) if fee_drag else None,
        "gross_positive_share": sum(1 for x in gross if x > 0) / len(gross) if gross else None,
        "net_positive_share": sum(1 for x in net if x > 0) / len(net) if net else None,
        "duration_ms_p50": q(durations, 0.50),
        "duration_ms_p90": q(durations, 0.90),
        "duration_ms_p99": q(durations, 0.99),
        "fill_count_p50": q([float(x) for x in fill_counts], 0.50),
        "cycles_with_more_than_2_fill_events": sum(1 for x in fill_counts if x > 2),
        "maker_fill_events": maker_fills,
        "taker_fill_events": taker_fills,
        "maker_fill_qty_contracts": maker_qty,
        "taker_fill_qty_contracts": taker_qty,
    }


def summarize_scenario(days: list[dict]) -> dict:
    cycles = [c for d in days for c in d.get("cycles", [])]
    forced = [c for c in cycles if c.get("forced_taker") is True]
    maker_only = [c for c in cycles if c.get("forced_taker") is not True]
    invalid = Counter(r for d in days for r in d.get("invalid_reasons", []))
    lifecycle_keys = (
        "stale_latches", "snapshot_resync_cancels", "level_disappear_cancels",
        "best_move_cancel_requests", "ttl_cancel_requests", "cancel_acks",
        "placement_rejects", "placement_activations", "same_ms_zero_credit_trades",
        "size_increase_events", "size_decrease_zero_credit_events",
        "firewall_flat_cancels", "forced_taker_exits",
    )
    lifecycle = {k: sum(int(d.get(k, 0)) for d in days) for k in lifecycle_keys}
    per_day = []
    for d in days:
        cs = d.get("cycles", [])
        per_day.append({
            "date": d.get("date"),
            "completed_cycles": int(d.get("completed_cycles", 0)),
            "forced_taker_exits": int(d.get("forced_taker_exits", 0)),
            "forced_taker_share": int(d.get("forced_taker_exits", 0)) / int(d.get("completed_cycles", 1)) if int(d.get("completed_cycles", 0)) else None,
            "unresolved_inventory": int(d.get("unresolved_inventory", 0)),
            "day_valid": bool(d.get("day_valid", False)),
            "max_abs_inventory": float(d.get("max_abs_inventory", 0.0)),
            "invalid_reasons": list(d.get("invalid_reasons", [])),
            "mean_gross_edge_bps": mean([float(c["gross_edge_bps"]) for c in cs]),
            "mean_net_edge_bps": mean([float(c["net_edge_bps"]) for c in cs]),
            "level_disappear_cancels": int(d.get("level_disappear_cancels", 0)),
            "best_move_cancel_requests": int(d.get("best_move_cancel_requests", 0)),
            "placement_activations": int(d.get("placement_activations", 0)),
        })
    return {
        "all_cycles": cycle_group(cycles),
        "forced_taker_cycles": cycle_group(forced),
        "maker_only_cycles": cycle_group(maker_only),
        "forced_taker_share": len(forced) / len(cycles) if cycles else None,
        "first_side_counts": dict(Counter(str(c.get("first_side")) for c in cycles)),
        "invalid_reason_counts": dict(invalid),
        "lifecycle_totals": lifecycle,
        "per_day": per_day,
    }


def main() -> int:
    maker = load_json(MAKER_REPORT)
    sem = load_json(SEMANTIC_REPORT)
    pre = load_json(PREFLIGHT_REPORT)

    if maker.get("status") != "E008_DISCOVERY_FAIL":
        fail(f"maker report not terminal FAIL: {maker.get('status')}")
    if sem.get("status") != "E008_DISCOVERY_SEMANTIC_INTEGRITY_PASS":
        fail("semantic parent not exact PASS")
    if pre.get("status") != "E008_MAKER_DISCOVERY_IMPLEMENTATION_PREFLIGHT_PASS":
        fail("maker preflight parent not exact PASS")
    if pre.get("identity_gate_status") != "E008_MAKER_DISCOVERY_IDENTITY_GATE_PASS":
        fail("maker identity parent not exact PASS")

    scenarios_raw = maker.get("scenarios") or {}
    expected = ("primary", "latency_500ms", "queue_2x")
    if any(name not in scenarios_raw for name in expected):
        fail("maker scenario set incomplete")

    scenarios = {name: summarize_scenario(list(scenarios_raw[name])) for name in expected}

    sem_days = []
    total_trade_rows = 0
    total_snapshots = 0
    total_gaps = 0
    for d in sem.get("days") or []:
        t = d.get("trade") or {}; l2 = d.get("l2") or {}
        total_trade_rows += int(t.get("admitted_rows", 0))
        total_snapshots += int(l2.get("snapshots", 0))
        total_gaps += int(l2.get("gap_gt_5000_count", 0))
        sem_days.append({
            "date": d.get("date"),
            "status": d.get("status"),
            "trade_rows": int(t.get("admitted_rows", 0)),
            "l2_records": int(l2.get("records", 0)),
            "snapshots": int(l2.get("snapshots", 0)),
            "updates": int(l2.get("updates", 0)),
            "gap_gt_5000_count": int(l2.get("gap_gt_5000_count", 0)),
            "max_interrecord_gap_ms": int(l2.get("max_interrecord_gap_ms", 0)),
        })

    primary_same_ms = scenarios["primary"]["lifecycle_totals"]["same_ms_zero_credit_trades"]
    p_all = scenarios["primary"]["all_cycles"]
    p_forced = scenarios["primary"]["forced_taker_cycles"]
    p_maker = scenarios["primary"]["maker_only_cycles"]

    findings = []
    if scenarios["primary"]["forced_taker_share"] is not None and scenarios["primary"]["forced_taker_share"] > 0.95:
        findings.append("FORCED_TAKER_DOMINANCE")
    if p_all["mean_gross_edge_bps"] is not None and p_all["mean_gross_edge_bps"] < 0:
        findings.append("MEAN_GROSS_EDGE_NEGATIVE_BEFORE_FEES")
    if p_all["mean_realized_fee_drag_bps"] is not None and p_all["mean_realized_fee_drag_bps"] > 5:
        findings.append("FEE_DRAG_MATERIAL")
    if p_maker["cycles"] < 20:
        findings.append("PASSIVE_EXIT_COMPLETION_EXTREMELY_SPARSE")
    if scenarios["primary"]["lifecycle_totals"]["level_disappear_cancels"] > 0:
        findings.append("LEVEL_DISAPPEAR_CANCEL_PATH_ACTIVE")
    if total_snapshots > 8:
        findings.append("REPEATED_SNAPSHOTS_PRESENT")
    if total_gaps == 0:
        findings.append("STALE_GAPS_NOT_PRIMARY_CAUSE")

    report = {
        "stage": STAGE,
        "version": VERSION,
        "status": PASS,
        "terminal_e008_status_preserved": maker.get("status"),
        "scenarios": scenarios,
        "semantic_diagnostics": {
            "days": sem_days,
            "total_trade_rows": total_trade_rows,
            "total_l2_snapshots": total_snapshots,
            "total_gap_gt_5000_count": total_gaps,
            "primary_same_ms_zero_credit_trades": primary_same_ms,
            "primary_same_ms_zero_credit_share_of_trade_rows": primary_same_ms / total_trade_rows if total_trade_rows else None,
        },
        "primary_decomposition": {
            "all_cycles": p_all,
            "forced_taker_cycles": p_forced,
            "maker_only_cycles": p_maker,
        },
        "forensic_flags": findings,
        "strategy_rerun_performed": False,
        "strategy_parameters_changed": False,
        "promotion_gates_changed": False,
        "confirmation_body_accessed": False,
        "q2_accessed": False,
        "validation_or_final_accessed": False,
    }
    atomic_json(OUT_JSON, report)

    print(PASS)
    print("terminal E008 status =", maker.get("status"))
    print("primary cycles =", p_all["cycles"])
    print("primary forced share =", scenarios["primary"]["forced_taker_share"])
    print("primary mean gross edge bps =", p_all["mean_gross_edge_bps"])
    print("primary mean realized fee drag bps =", p_all["mean_realized_fee_drag_bps"])
    print("primary mean net edge bps =", p_all["mean_net_edge_bps"])
    print("forced-cycle mean gross/net bps =", p_forced["mean_gross_edge_bps"], p_forced["mean_net_edge_bps"])
    print("maker-only cycles =", p_maker["cycles"])
    print("maker-only mean gross/net bps =", p_maker["mean_gross_edge_bps"], p_maker["mean_net_edge_bps"])
    print("primary level-disappear cancels =", scenarios["primary"]["lifecycle_totals"]["level_disappear_cancels"])
    print("primary best-move cancel requests =", scenarios["primary"]["lifecycle_totals"]["best_move_cancel_requests"])
    print("primary placement activations =", scenarios["primary"]["lifecycle_totals"]["placement_activations"])
    print("semantic total snapshots =", total_snapshots)
    print("semantic >5s gaps =", total_gaps)
    print("same-ms zero-credit share of trade rows =", report["semantic_diagnostics"]["primary_same_ms_zero_credit_share_of_trade_rows"])
    print("forensic flags =", findings)
    print("strategy rerun performed = False")
    print("E008 terminal decision changed = False")
    print("Confirmation/Q2/Validation/Final = CLOSED")
    print("report =", OUT_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
