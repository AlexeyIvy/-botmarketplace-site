"""SC001-E002 OKX Q1 taker execution economics.

Implements frozen protocol v0.2 on the already-open four 2024-Q1 OKX days.
No Q2 / formal Validation / Final access. No maker assumptions. Stdlib only.

The four days may run in separate OS processes. Partial day outputs are compute
checkpoints only and must not be interpreted before final aggregation.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import math
import os
import statistics
import subprocess
import tarfile
from collections import deque
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR
from pathlib import Path

STAGE = "SC001-E002-OKX-Q1-TAKER-ECONOMICS"
VERSION = "0.1"
PROTOCOL = "docs/research/sc001-e002-okx-q1-taker-economics-protocol-v0.2.md"
PILOT_ENGINE_COMMIT = "94c77febc73601c76976da4ab71bedecc69a485a"
PILOT_ENGINE_PATH = "research/sc001/sc001_e002_okx_midquote_pilot.py"

GRID_MS = 5_000
HORIZON_MS = 5_000
ROLLING_N = 720
THRESHOLDS = (("q90", 0.90), ("q95", 0.95), ("q97.5", 0.975))
LATENCIES_MS = (100, 250, 500)
HAIRCUTS = (0.0, 0.25, 0.50)
TARGET_NOTIONALS = (1_000, 10_000, 50_000)
PRIMARY_Q = "q95"
PRIMARY_LATENCY = 100
PRIMARY_HAIRCUT = 0.0
PRIMARY_SIZE = 10_000

CT_VAL = Decimal("0.01")
TICK = Decimal("0.1")
TAKER_FEE = 0.0005
MIN_CONTRACTS = 1
LOT_STEP = 1

DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
REPO_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = DATA_ROOT / "SC001_E002_OKX_Q1_TAKER_ECONOMICS"
DAY_ROOT = WORKSPACE / "days"
REPORT = WORKSPACE / "sc001_e002_okx_q1_taker_economics_report.json"
SUMMARY = WORKSPACE / "sc001_e002_okx_q1_taker_economics_summary.md"
AGG_CSV = WORKSPACE / "sc001_e002_okx_q1_taker_economics_aggregate.csv"
SAFETY = WORKSPACE / "sc001_e002_okx_q1_taker_economics_final_safety.json"

CONFIRM_REPORT = DATA_ROOT / "SC001_E002_OKX_MIDQUOTE_Q1_CONFIRMATION" / "sc001_e002_okx_midquote_q1_confirmation_report.json"
Q006R_REPORT = DATA_ROOT / "SC001_DATA_Q006R_OKX_UTC_STITCH" / "sc001_data_q006r_okx_utc_stitch_report.json"
Q009A_REPORT = DATA_ROOT / "SC001_DATA_Q009A_OKX_L2_BATCH_A" / "sc001_data_q009a_okx_l2_batch_a_report.json"
Q009B_REPORT = DATA_ROOT / "SC001_DATA_Q009B_OKX_L2_BATCH_B" / "sc001_data_q009b_okx_l2_batch_b_report.json"
META_REPORT = DATA_ROOT / "SC001_E002_OKX_Q1_EXECUTION_METADATA" / "sc001_e002_okx_q1_execution_metadata_preflight_v0_2.json"
FUNDING_FILE = DATA_ROOT / "SC001_E002_OKX_Q1_EXECUTION_METADATA" / "sc001_e002_okx_q1_funding_rates_v0_2.json"

DAYS = (
    {"date": "2024-01-14", "sample_type": "ORDINARY_WEEKEND", "event_class": None, "expected_decisions": 16_886, "next_date": "2024-01-15", "l2_root": "SC001_DATA_Q009A_OKX_L2_BATCH_A"},
    {"date": "2024-01-31", "sample_type": "EVENT", "event_class": "FOMC", "expected_decisions": 17_129, "next_date": "2024-02-01", "l2_root": "SC001_DATA_Q009A_OKX_L2_BATCH_A"},
    {"date": "2024-02-12", "sample_type": "ORDINARY_WEEKDAY", "event_class": None, "expected_decisions": 17_179, "next_date": "2024-02-13", "l2_root": "SC001_DATA_Q009B_OKX_L2_BATCH_B"},
    {"date": "2024-02-13", "sample_type": "EVENT", "event_class": "CPI", "expected_decisions": 17_226, "next_date": "2024-02-14", "l2_root": "SC001_DATA_Q009B_OKX_L2_BATCH_B"},
)


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing required file: {path}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        fail(f"JSON object expected: {path}")
    return obj


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def atomic_json(path: Path, obj: object) -> None:
    atomic_text(path, json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def script_sha() -> str:
    return sha256_file(Path(__file__).resolve())


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    a = sorted(values)
    if len(a) == 1:
        return a[0]
    pos = q * (len(a) - 1)
    lo = int(math.floor(pos)); hi = int(math.ceil(pos))
    if lo == hi:
        return a[lo]
    w = pos - lo
    return a[lo] * (1.0 - w) + a[hi] * w


def safe_mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def safe_median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def load_pilot_engine() -> dict:
    cp = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", f"{PILOT_ENGINE_COMMIT}:{PILOT_ENGINE_PATH}"],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    raw = cp.stdout
    required = (b'def build_scores', b'STAGE = "SC001-E002-OKX-MIDQUOTE-PILOT"')
    if not raw or not all(x in raw for x in required):
        fail("pinned pilot engine identity mismatch")
    ns = {"__name__": "sc001_frozen_pilot_for_taker_economics", "__file__": f"<git:{PILOT_ENGINE_COMMIT}:{PILOT_ENGINE_PATH}>", "__package__": None}
    exec(compile(raw, ns["__file__"], "exec"), ns, ns)
    return ns


def parent_state() -> tuple[dict, dict, dict, dict, dict]:
    confirm = load_json(CONFIRM_REPORT)
    if confirm.get("verdict") != "MIDQUOTE_CONFIRMATION_PASS" or len(confirm.get("daily") or []) != 4:
        fail("midquote confirmation parent is not terminal PASS")
    if confirm.get("q2_okx_accessed") is not False or confirm.get("validation_or_final_accessed") is not False or confirm.get("strategy_pnl_calculated") is not False:
        fail("confirmation firewall mismatch")

    q6 = load_json(Q006R_REPORT)
    q9a = load_json(Q009A_REPORT); q9b = load_json(Q009B_REPORT)
    if q6.get("overall_status") != "PASS": fail("Q006R is not PASS")
    if q9a.get("overall_status") != "PASS": fail("Q009A is not PASS")
    if q9b.get("overall_status") != "PASS": fail("Q009B is not PASS")
    for x in (q6, q9a, q9b):
        if x.get("q2_okx_accessed") is not False or x.get("validation_or_final_accessed") is not False:
            fail("source parent firewall mismatch")

    meta = load_json(META_REPORT)
    if meta.get("status") != "PASS" or meta.get("q2_okx_accessed") is not False or meta.get("validation_or_final_accessed") is not False:
        fail("execution metadata preflight is not PASS")
    hf = meta.get("historical_q1_freeze") or {}
    expected = {
        "contract_value_btc": "0.01", "minimum_contracts": "1", "lot_step_contracts": "1",
        "tick_size": "0.1", "primary_taker_fee_rate": "0.0005",
    }
    for k, v in expected.items():
        if str(hf.get(k)) != v:
            fail(f"metadata freeze mismatch {k}: {hf.get(k)!r}")

    funding = load_json(FUNDING_FILE)
    if funding.get("q2_okx_accessed") is not False or funding.get("validation_or_final_accessed") is not False:
        fail("funding firewall mismatch")
    dates = funding.get("dates") or {}
    for d in [x["date"] for x in DAYS]:
        if len(dates.get(d) or []) != 3:
            fail(f"funding records missing for {d}")
    return q6, q9a, q9b, meta, funding


def source_specs(q6: dict, q9a: dict, q9b: dict) -> dict[str, dict]:
    q6rows = {x.get("date"): x for x in (q6.get("days") or [])}
    l2rows = {}
    for rep in (q9a, q9b):
        for row in rep.get("days") or []:
            if row.get("status") == "FULL_DAY_PASS":
                l2rows[row.get("date")] = row
    out = {}
    for day in DAYS:
        d = day["date"]
        q = q6rows[d]
        exact = q.get("exact_archive") or {}
        neigh = q.get("neighbor_archive") or {}
        ndl = neigh.get("download") or {}
        l2a = (l2rows[d].get("archive") or {})
        exact_name = exact.get("filename")
        neigh_name = neigh.get("filename")
        l2_name = f"BTC-USDT-SWAP-L2orderbook-400lv-{d}.tar.gz"
        specs = {
            "trade_exact": {
                "path": DATA_ROOT / "SC001_DATA_Q006_OKX_TRADES" / "archives" / exact_name,
                "bytes": exact.get("bytes"), "sha256": exact.get("sha256"),
            },
            "trade_neighbor": {
                "path": DATA_ROOT / "SC001_DATA_Q006R_OKX_UTC_STITCH" / "neighbor_archives" / neigh_name,
                "bytes": ndl.get("bytes"), "sha256": ndl.get("sha256"),
            },
            "l2": {
                "path": DATA_ROOT / day["l2_root"] / d / l2_name,
                "bytes": l2a.get("bytes"), "sha256": l2a.get("sha256"),
            },
        }
        for label, s in specs.items():
            if not isinstance(s["bytes"], int) or not isinstance(s["sha256"], str) or len(s["sha256"]) != 64:
                fail(f"incomplete source identity {d} {label}")
        out[d] = specs
    return out


def verify_sources(specs: dict[str, dict]) -> None:
    for d, group in specs.items():
        for label, s in group.items():
            p = Path(s["path"])
            if not p.exists() or p.stat().st_size != s["bytes"]:
                fail(f"{d} {label} size/existence mismatch: {p}")
            got = sha256_file(p)
            if got != s["sha256"]:
                fail(f"{d} {label} SHA mismatch")
            print(f"SOURCE PASS {d} {label} {p.name}")


def build_candidates(scores: list[float], decisions: list[int]) -> dict[str, list[dict]]:
    out = {name: [] for name, _ in THRESHOLDS}
    window = deque()
    sorted_abs: list[float] = []
    for i, (score, ts) in enumerate(zip(scores, decisions)):
        if len(window) == ROLLING_N:
            for name, q in THRESHOLDS:
                rank = max(1, math.ceil(q * ROLLING_N)) - 1
                threshold = sorted_abs[rank]
                if score != 0.0 and abs(score) >= threshold:
                    out[name].append({
                        "id": i, "decision_ts": int(ts), "score": float(score),
                        "threshold": float(threshold), "direction": 1 if score > 0 else -1,
                    })
        x = abs(float(score))
        bisect.insort(sorted_abs, x)
        window.append(x)
        if len(window) > ROLLING_N:
            old = window.popleft()
            j = bisect.bisect_left(sorted_abs, old)
            if j >= len(sorted_abs): fail("rolling threshold state corrupt")
            sorted_abs.pop(j)
    return out


def parse_level(x) -> tuple[float, float, int]:
    if not isinstance(x, list) or len(x) != 3:
        fail("L2 level shape mismatch")
    px_d = Decimal(str(x[0])); sz_d = Decimal(str(x[1])); ord_d = Decimal(str(x[2]))
    if not px_d.is_finite() or not sz_d.is_finite() or not ord_d.is_finite():
        fail("non-finite L2 level")
    if px_d <= 0 or sz_d < 0 or ord_d < 0:
        fail("invalid L2 level")
    if px_d % TICK != 0:
        fail(f"tick-grid violation price={px_d}")
    orders = int(ord_d)
    if ord_d != Decimal(orders):
        fail("non-integer L2 order count")
    return float(px_d), float(sz_d), orders


def book_apply(book: dict[float, tuple[float, int]], prices: list[float], levels: list[tuple[float, float, int]]) -> None:
    for px, sz, orders in levels:
        if sz == 0:
            if px in book:
                del book[px]
                i = bisect.bisect_left(prices, px)
                if i < len(prices) and prices[i] == px: prices.pop(i)
        else:
            if px not in book: bisect.insort(prices, px)
            book[px] = (sz, orders)


def qty_for_target(target: int, mid: float) -> int:
    raw = (Decimal(target) / (CT_VAL * Decimal(str(mid)))).to_integral_value(rounding=ROUND_FLOOR)
    return max(MIN_CONTRACTS, int(raw))


def consume(book: dict[float, tuple[float, int]], prices: list[float], ascending: bool, qty: int, haircut: float) -> dict:
    remaining = float(qty)
    pv = 0.0
    factor = 1.0 - haircut
    seq = prices if ascending else reversed(prices)
    for px in seq:
        avail = book[px][0] * factor
        if avail <= 0: continue
        take = min(remaining, avail)
        pv += take * px
        remaining -= take
        if remaining <= 1e-12: break
    if remaining > 1e-9:
        return {"filled": False, "vwap": None, "notional": None}
    vwap = pv / qty
    return {"filled": True, "vwap": vwap, "notional": float(CT_VAL) * qty * vwap}


def make_requests(candidates: dict[str, list[dict]]) -> list[dict]:
    reqs = []
    for qname, rows in candidates.items():
        for c in rows:
            for lat in LATENCIES_MS:
                entry_t = c["decision_ts"] + lat
                reqs.append({"target": entry_t, "q": qname, "cid": c["id"], "lat": lat, "kind": "entry", "direction": c["direction"]})
                reqs.append({"target": entry_t + HORIZON_MS, "q": qname, "cid": c["id"], "lat": lat, "kind": "exit", "direction": c["direction"]})
    reqs.sort(key=lambda r: (r["target"], 0 if r["kind"] == "entry" else 1, r["q"], r["cid"], r["lat"]))
    return reqs


def replay_execution_states(l2_path: Path, candidates: dict[str, list[dict]]) -> tuple[dict, dict]:
    reqs = make_requests(candidates)
    execs: dict[tuple, dict] = {}
    ri = 0
    asks: dict[float, tuple[float, int]] = {}; bids: dict[float, tuple[float, int]] = {}
    ask_prices: list[float] = []; bid_prices: list[float] = []
    last_ts = None; records = snapshots = updates = groups = 0
    pending_group: list[tuple[str, list, list]] = []; group_ts = None

    def resolve(ts: int) -> None:
        nonlocal ri
        if not ask_prices or not bid_prices or bid_prices[-1] >= ask_prices[0]:
            return
        mid = (bid_prices[-1] + ask_prices[0]) / 2.0
        while ri < len(reqs) and reqs[ri]["target"] <= ts:
            r = reqs[ri]; key = (r["q"], r["cid"], r["lat"])
            e = execs.setdefault(key, {})
            side_asks = (r["kind"] == "entry" and r["direction"] > 0) or (r["kind"] == "exit" and r["direction"] < 0)
            book = asks if side_asks else bids; prices = ask_prices if side_asks else bid_prices
            rec = {"target_ts": r["target"], "book_ts": ts, "wait_ms": ts - r["target"], "mid": mid, "sizes": {}}
            if r["kind"] == "entry":
                for target in TARGET_NOTIONALS:
                    qty = qty_for_target(target, mid)
                    hmap = {str(h): consume(book, prices, side_asks, qty, h) for h in HAIRCUTS}
                    rec["sizes"][str(target)] = {"qty_contracts": qty, "haircuts": hmap}
            else:
                entry = e.get("entry")
                if entry is None:
                    fail("exit resolved before entry")
                for target in TARGET_NOTIONALS:
                    qty = int(entry["sizes"][str(target)]["qty_contracts"])
                    hmap = {str(h): consume(book, prices, side_asks, qty, h) for h in HAIRCUTS}
                    rec["sizes"][str(target)] = {"qty_contracts": qty, "haircuts": hmap}
            e[r["kind"]] = rec
            ri += 1

    def apply_group(ts: int, group: list[tuple[str, list, list]]) -> None:
        nonlocal snapshots, updates, groups
        for action, asks_raw, bids_raw in group:
            pa = [parse_level(x) for x in asks_raw]; pb = [parse_level(x) for x in bids_raw]
            if action == "snapshot":
                snapshots += 1; asks.clear(); bids.clear(); ask_prices.clear(); bid_prices.clear()
            else: updates += 1
            book_apply(asks, ask_prices, pa); book_apply(bids, bid_prices, pb)
        groups += 1
        resolve(ts)

    with tarfile.open(l2_path, mode="r|gz") as tf:
        regular = 0
        for member in tf:
            if not member.isfile(): continue
            regular += 1
            if regular != 1: fail("unexpected extra regular member in L2 archive")
            f = tf.extractfile(member)
            if f is None: fail("could not open L2 member")
            for raw in f:
                if not raw.strip(): continue
                rec = json.loads(raw); records += 1
                if records % 1_000_000 == 0:
                    print(f"[{l2_path.name}] L2 progress {records:,}", flush=True)
                if rec.get("instId") != "BTC-USDT-SWAP" or rec.get("action") not in {"snapshot", "update"}:
                    fail("L2 record identity/action failure")
                ts = int(rec["ts"])
                if last_ts is not None and ts < last_ts: fail("L2 timestamp reversal")
                asks_raw = rec.get("asks"); bids_raw = rec.get("bids")
                if not isinstance(asks_raw, list) or not isinstance(bids_raw, list): fail("L2 asks/bids type failure")
                if group_ts is None: group_ts = ts
                if ts != group_ts:
                    apply_group(group_ts, pending_group)
                    pending_group = []; group_ts = ts
                pending_group.append((rec["action"], asks_raw, bids_raw)); last_ts = ts
        if group_ts is not None: apply_group(group_ts, pending_group)
    return execs, {"records": records, "snapshots": snapshots, "updates": updates, "timestamp_groups": groups, "unresolved_execution_requests": len(reqs) - ri, "tick_grid_violations": 0}


def funding_rows(funding: dict, date: str) -> list[tuple[int, float]]:
    out = []
    for x in (funding.get("dates") or {}).get(date) or []:
        out.append((int(x["fundingTime"]), abs(float(x["fundingRate"]))))
    out.sort()
    return out


def trade_row(day: dict, cand: dict, qname: str, lat: int, haircut: float, target: int, ex: dict, funding_events: list[tuple[int, float]]) -> dict | None:
    en = ex.get("entry"); out = ex.get("exit")
    if en is None or out is None: return None
    es = en["sizes"][str(target)]; xs = out["sizes"][str(target)]
    ef = es["haircuts"][str(haircut)]; xf = xs["haircuts"][str(haircut)]
    if not ef["filled"] or not xf["filled"]: return None
    qty = int(es["qty_contracts"]); entry_vwap = float(ef["vwap"]); exit_vwap = float(xf["vwap"])
    entry_notional = float(ef["notional"]); exit_notional = float(xf["notional"])
    direction = int(cand["direction"])
    gross = direction * (float(out["mid"]) - float(en["mid"])) / float(en["mid"]) * 10_000.0
    prefee = direction * (exit_vwap - entry_vwap) / entry_vwap * 10_000.0
    entry_fee = entry_notional * TAKER_FEE; exit_fee = exit_notional * TAKER_FEE
    fee_bps = (entry_fee + exit_fee) / entry_notional * 10_000.0
    crossed = [(ft, rate) for ft, rate in funding_events if int(en["book_ts"]) <= ft <= int(out["book_ts"])]
    funding_bps = sum(rate for _, rate in crossed) * 10_000.0
    net = prefee - fee_bps - funding_bps
    return {
        "date": day["date"], "sample_type": day["sample_type"], "event_class": day["event_class"] or "",
        "threshold_scenario": qname, "latency_ms": lat, "haircut": haircut, "target_notional": target,
        "decision_ts": cand["decision_ts"], "direction": "LONG" if direction > 0 else "SHORT",
        "tfi": cand["score"], "causal_threshold": cand["threshold"], "qty_contracts": qty,
        "entry_target_ts": en["target_ts"], "entry_book_ts": en["book_ts"], "entry_wait_ms": en["wait_ms"],
        "exit_target_ts": out["target_ts"], "exit_book_ts": out["book_ts"], "exit_wait_ms": out["wait_ms"],
        "arrival_mid_entry": en["mid"], "arrival_mid_exit": out["mid"],
        "entry_vwap": entry_vwap, "exit_vwap": exit_vwap,
        "actual_entry_notional": entry_notional, "actual_exit_notional": exit_notional,
        "gross_midquote_edge_bps": gross, "pre_fee_executable_edge_bps": prefee,
        "spread_depth_cost_bps": gross - prefee,
        "entry_fee_quote": entry_fee, "exit_fee_quote": exit_fee, "fee_cost_bps": fee_bps,
        "funding_crossings": len(crossed), "funding_cost_bps": funding_bps,
        "break_even_round_trip_fee_bps": prefee - funding_bps,
        "net_edge_bps": net,
        "net_pnl_quote": net / 10_000.0 * entry_notional,
    }


def summarize_rows(rows: list[dict], candidate_count: int, skipped: int, unfilled: int) -> dict:
    completed = len(rows); eligible = max(0, candidate_count - skipped)
    fill_rate = completed / eligible if eligible else 0.0
    def vals(k): return [float(x[k]) for x in rows]
    waits = vals("entry_wait_ms") + vals("exit_wait_ms")
    total_entry = sum(vals("actual_entry_notional")); total_pnl = sum(vals("net_pnl_quote"))
    return {
        "candidate_count": candidate_count, "completed_trade_count": completed, "skipped_while_open": skipped,
        "eligible_nonoverlap_count": eligible, "unfilled_count": unfilled, "completion_rate": fill_rate,
        "long_count": sum(1 for x in rows if x["direction"] == "LONG"), "short_count": sum(1 for x in rows if x["direction"] == "SHORT"),
        "mean_gross_midquote_edge_bps": safe_mean(vals("gross_midquote_edge_bps")), "median_gross_midquote_edge_bps": safe_median(vals("gross_midquote_edge_bps")),
        "mean_pre_fee_executable_edge_bps": safe_mean(vals("pre_fee_executable_edge_bps")), "median_pre_fee_executable_edge_bps": safe_median(vals("pre_fee_executable_edge_bps")),
        "mean_spread_depth_cost_bps": safe_mean(vals("spread_depth_cost_bps")), "median_spread_depth_cost_bps": safe_median(vals("spread_depth_cost_bps")),
        "mean_fee_cost_bps": safe_mean(vals("fee_cost_bps")), "median_fee_cost_bps": safe_median(vals("fee_cost_bps")),
        "mean_funding_cost_bps": safe_mean(vals("funding_cost_bps")), "median_funding_cost_bps": safe_median(vals("funding_cost_bps")), "max_funding_cost_bps": max(vals("funding_cost_bps"), default=None),
        "funding_crossing_trade_count": sum(1 for x in rows if int(x["funding_crossings"]) > 0),
        "mean_net_edge_bps": safe_mean(vals("net_edge_bps")), "median_net_edge_bps": safe_median(vals("net_edge_bps")),
        "weighted_net_edge_bps": (total_pnl / total_entry * 10_000.0) if total_entry else None,
        "total_net_pnl_quote": total_pnl, "win_rate_after_all_costs": (sum(1 for x in rows if float(x["net_edge_bps"]) > 0) / completed) if completed else None,
        "mean_break_even_round_trip_fee_bps": safe_mean(vals("break_even_round_trip_fee_bps")),
        "entry_wait_p50_ms": percentile(vals("entry_wait_ms"), 0.50), "entry_wait_p95_ms": percentile(vals("entry_wait_ms"), 0.95), "entry_wait_p99_ms": percentile(vals("entry_wait_ms"), 0.99),
        "exit_wait_p50_ms": percentile(vals("exit_wait_ms"), 0.50), "exit_wait_p95_ms": percentile(vals("exit_wait_ms"), 0.95), "exit_wait_p99_ms": percentile(vals("exit_wait_ms"), 0.99),
        "execution_wait_gt_250ms_count": sum(1 for v in waits if v > 250), "execution_wait_gt_500ms_count": sum(1 for v in waits if v > 500), "execution_wait_gt_1000ms_count": sum(1 for v in waits if v > 1000),
    }


def simulate_day(day: dict, candidates: dict[str, list[dict]], execs: dict, funding: dict, day_dir: Path, impl_sha: str, replay_stats: dict) -> dict:
    funding_events = funding_rows(funding, day["date"])
    csv_path = day_dir / "completed_trades.csv"
    rows_out = []
    summaries = []
    for qname, _ in THRESHOLDS:
        cands = candidates[qname]
        for lat in LATENCIES_MS:
            for haircut in HAIRCUTS:
                for target in TARGET_NOTIONALS:
                    open_until = -1; skipped = 0; unfilled = 0; completed_rows = []
                    for c in cands:
                        if int(c["decision_ts"]) < open_until:
                            skipped += 1; continue
                        ex = execs.get((qname, c["id"], lat), {})
                        en = ex.get("entry"); out = ex.get("exit")
                        if en is None:
                            unfilled += 1; continue
                        ef = en["sizes"][str(target)]["haircuts"][str(haircut)]
                        if not ef["filled"]:
                            unfilled += 1; continue
                        if out is None:
                            unfilled += 1; open_until = 86_400_000_000_000_000; continue
                        xf = out["sizes"][str(target)]["haircuts"][str(haircut)]
                        if not xf["filled"]:
                            unfilled += 1; open_until = int(out["book_ts"]); continue
                        tr = trade_row(day, c, qname, lat, haircut, target, ex, funding_events)
                        if tr is None: fail("completed trade unexpectedly missing")
                        completed_rows.append(tr); rows_out.append(tr); open_until = int(out["book_ts"])
                    sm = summarize_rows(completed_rows, len(cands), skipped, unfilled)
                    sm.update({"date": day["date"], "sample_type": day["sample_type"], "event_class": day["event_class"], "threshold_scenario": qname, "latency_ms": lat, "haircut": haircut, "target_notional": target})
                    summaries.append(sm)
    if rows_out:
        header = list(rows_out[0].keys())
        tmp = csv_path.with_suffix(".csv.tmp")
        with tmp.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=header); w.writeheader(); w.writerows(rows_out); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, csv_path)
    else:
        atomic_text(csv_path, "")
    report = {
        "stage": STAGE, "version": VERSION, "status": "PASS", "implementation_sha256": impl_sha,
        "date": day["date"], "sample_type": day["sample_type"], "event_class": day["event_class"],
        "replay_stats": replay_stats, "scenario_summaries": summaries, "completed_trades_csv": str(csv_path),
        "do_not_interpret_before_all_four_days_complete": True,
    }
    atomic_json(day_dir / "day_report.json", report)
    return report


def worker(day: dict, spec: dict, funding: dict, impl_sha: str) -> dict:
    day_dir = DAY_ROOT / day["date"]; day_dir.mkdir(parents=True, exist_ok=True)
    existing = day_dir / "day_report.json"
    if existing.exists():
        obj = load_json(existing)
        if obj.get("status") == "PASS" and obj.get("implementation_sha256") == impl_sha and Path(obj.get("completed_trades_csv", "")).exists():
            print(f"[{day['date']}] COMPLETE CHECKPOINT REUSED", flush=True)
            return obj
    lib = load_pilot_engine()
    lib["DATE"] = day["date"]; lib["TRADE_EXACT"] = Path(spec["trade_exact"]["path"]); lib["TRADE_NEIGHBOR"] = Path(spec["trade_neighbor"]["path"])
    lib["EXPECTED_DECISIONS"] = day["expected_decisions"]; lib["GRID_MS"] = GRID_MS; lib["LOOKBACK_MS"] = GRID_MS; lib["HORIZON_MS"] = HORIZON_MS
    scores, decisions, trade_stats, day_start, day_end = lib["build_scores"]()
    if len(scores) != day["expected_decisions"]: fail(f"{day['date']} decision count mismatch")
    candidates = build_candidates(list(scores), list(decisions))
    print(f"[{day['date']}] signal schedule frozen; starting grouped executable L2 replay", flush=True)
    execs, replay_stats = replay_execution_states(Path(spec["l2"]["path"]), candidates)
    replay_stats["trade_decision_count"] = len(scores); replay_stats["trade_stats"] = trade_stats
    replay_stats["candidate_counts"] = {k: len(v) for k, v in candidates.items()}
    return simulate_day(day, candidates, execs, funding, day_dir, impl_sha, replay_stats)


def read_day_rows(report: dict) -> list[dict]:
    path = Path(report["completed_trades_csv"])
    if not path.exists() or path.stat().st_size == 0: return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def scenario_id(q: str, lat: int, h: float, size: int) -> str:
    return f"{q}|{lat}|{h}|{size}"


def aggregate(days_reports: list[dict]) -> tuple[list[dict], dict]:
    daily_map = {}
    all_rows = []
    for rep in days_reports:
        for s in rep["scenario_summaries"]:
            daily_map[(s["date"], scenario_id(s["threshold_scenario"], s["latency_ms"], s["haircut"], s["target_notional"]))] = s
        all_rows.extend(read_day_rows(rep))
    groups = {}
    for row in all_rows:
        sid = scenario_id(row["threshold_scenario"], int(row["latency_ms"]), float(row["haircut"]), int(row["target_notional"]))
        groups.setdefault(sid, []).append(row)
    pooled = []
    for qname, _ in THRESHOLDS:
        for lat in LATENCIES_MS:
            for h in HAIRCUTS:
                for size in TARGET_NOTIONALS:
                    sid = scenario_id(qname, lat, h, size); rows = groups.get(sid, [])
                    dailies = [daily_map[(d["date"], sid)] for d in DAYS]
                    candidate_count = sum(int(x["candidate_count"]) for x in dailies); skipped = sum(int(x["skipped_while_open"]) for x in dailies); unfilled = sum(int(x["unfilled_count"]) for x in dailies)
                    sm = summarize_rows(rows, candidate_count, skipped, unfilled)
                    sm.update({"threshold_scenario": qname, "latency_ms": lat, "haircut": h, "target_notional": size,
                               "positive_daily_mean_net_days": sum(1 for x in dailies if x["mean_net_edge_bps"] is not None and x["mean_net_edge_bps"] > 0),
                               "median_daily_mean_net_edge_bps": safe_median([x["mean_net_edge_bps"] for x in dailies if x["mean_net_edge_bps"] is not None]),
                               "event_day_median_daily_mean_net_edge_bps": safe_median([x["mean_net_edge_bps"] for x in dailies if x["sample_type"] == "EVENT" and x["mean_net_edge_bps"] is not None]),
                               "ordinary_day_median_daily_mean_net_edge_bps": safe_median([x["mean_net_edge_bps"] for x in dailies if x["sample_type"] != "EVENT" and x["mean_net_edge_bps"] is not None])})
                    pooled.append(sm)
    return pooled, daily_map


def find_scenario(pooled: list[dict], q: str, lat: int, h: float, size: int) -> dict:
    for x in pooled:
        if x["threshold_scenario"] == q and x["latency_ms"] == lat and x["haircut"] == h and x["target_notional"] == size: return x
    fail("scenario missing")


def verdict(pooled: list[dict]) -> tuple[str, dict]:
    base = find_scenario(pooled, PRIMARY_Q, 100, 0.0, 10_000)
    sa = find_scenario(pooled, PRIMARY_Q, 250, 0.0, 10_000)
    sb = find_scenario(pooled, PRIMARY_Q, 100, 0.25, 10_000)
    base_checks = {
        "pooled_mean_net_positive": base["mean_net_edge_bps"] is not None and base["mean_net_edge_bps"] > 0,
        "median_daily_mean_net_positive": base["median_daily_mean_net_edge_bps"] is not None and base["median_daily_mean_net_edge_bps"] > 0,
        "positive_days_4_of_4": base["positive_daily_mean_net_days"] == 4,
        "event_median_positive": base["event_day_median_daily_mean_net_edge_bps"] is not None and base["event_day_median_daily_mean_net_edge_bps"] > 0,
        "ordinary_median_positive": base["ordinary_day_median_daily_mean_net_edge_bps"] is not None and base["ordinary_day_median_daily_mean_net_edge_bps"] > 0,
        "completion_rate_ge_99pct": base["completion_rate"] >= 0.99,
    }
    stress_a = (sa["mean_net_edge_bps"] is not None and sa["mean_net_edge_bps"] > 0 and sa["positive_daily_mean_net_days"] >= 3)
    stress_b = (sb["mean_net_edge_bps"] is not None and sb["mean_net_edge_bps"] > 0 and sb["positive_daily_mean_net_days"] >= 3)
    base_pass = all(base_checks.values())
    if not base_pass: v = "TAKER_ECONOMICS_FAIL"
    elif stress_a and stress_b: v = "TAKER_ECONOMICS_PASS"
    else: v = "TAKER_ECONOMICS_WEAK"
    return v, {"base": base, "stress_latency_250": sa, "stress_depth_25pct": sb, "base_checks": base_checks, "stress_a_pass": stress_a, "stress_b_pass": stress_b}


def write_final(days_reports: list[dict], meta: dict, funding: dict, impl_sha: str) -> None:
    pooled, daily_map = aggregate(days_reports)
    v, gates = verdict(pooled)
    report = {
        "stage": STAGE, "version": VERSION, "protocol": PROTOCOL, "implementation_sha256": impl_sha,
        "verdict": v, "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "metadata_preflight": meta, "funding_source_metadata": {"source": funding.get("source"), "archives": funding.get("archives"), "retrieved_at_utc": funding.get("retrieved_at_utc")},
        "daily_reports": [str(DAY_ROOT / x["date"] / "day_report.json") for x in DAYS],
        "pooled_scenarios": pooled, "promotion_gates": gates,
        "q2_okx_accessed": False, "validation_or_final_accessed": False, "maker_assumptions_used": False,
    }
    atomic_json(REPORT, report)
    # aggregate CSV
    if pooled:
        header = list(pooled[0].keys()); tmp = AGG_CSV.with_suffix(".csv.tmp")
        with tmp.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=header); w.writeheader(); w.writerows(pooled); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, AGG_CSV)
    base = gates["base"]; sa = gates["stress_latency_250"]; sb = gates["stress_depth_25pct"]
    lines = [
        "# SC001-E002 OKX Q1 Taker Execution Economics", "", f"- Verdict: `{v}`", "- Q2 / Validation / Final: **NO**", "- Primary execution: taker-only", "",
        "## Base q95 / 10k / 100ms / 0% haircut",
        f"- completed trades: {base['completed_trade_count']}", f"- completion rate: {base['completion_rate']}", f"- pooled mean net edge bps: {base['mean_net_edge_bps']}", f"- pooled median net edge bps: {base['median_net_edge_bps']}", f"- positive daily mean net days: {base['positive_daily_mean_net_days']} / 4", f"- median daily mean net bps: {base['median_daily_mean_net_edge_bps']}",
        "", "## Stress 250ms / 0% haircut", f"- pooled mean net edge bps: {sa['mean_net_edge_bps']}", f"- positive daily mean net days: {sa['positive_daily_mean_net_days']} / 4",
        "", "## Stress 100ms / 25% haircut", f"- pooled mean net edge bps: {sb['mean_net_edge_bps']}", f"- positive daily mean net days: {sb['positive_daily_mean_net_days']} / 4",
        "", "## Boundary", "This is the frozen Q1 executable taker-economics gate. PASS alone permits freezing the exact rule before the protected Q2 one-shot holdout; WEAK/FAIL keep Q2 closed.",
    ]
    atomic_text(SUMMARY, "\n".join(lines) + "\n")
    atomic_json(SAFETY, {"stage": STAGE, "final_verdict_written": True, "verdict": v, "q2_okx_accessed": False, "validation_or_final_accessed": False, "implementation_sha256": impl_sha})
    print(f"COMPLETE: {v}")


def preflight() -> tuple[dict, dict, dict]:
    q6, q9a, q9b, meta, funding = parent_state()
    specs = source_specs(q6, q9a, q9b)
    verify_sources(specs)
    print("TAKER_ECONOMICS_IMPLEMENTATION_PREFLIGHT_PASS")
    print("protocol =", PROTOCOL)
    print("frozen days =", [x["date"] for x in DAYS])
    print("thresholds =", [x[0] for x in THRESHOLDS], "rolling N =", ROLLING_N)
    print("latencies ms =", LATENCIES_MS, "haircuts =", HAIRCUTS, "sizes =", TARGET_NOTIONALS)
    print("taker fee per fill bps =", TAKER_FEE * 10_000)
    print("Q2/Validation/Final = CLOSED")
    return specs, meta, funding


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("mode", choices=("preflight", "run")); args = ap.parse_args()
    WORKSPACE.mkdir(parents=True, exist_ok=True); DAY_ROOT.mkdir(parents=True, exist_ok=True)
    impl_sha = script_sha()
    specs, meta, funding = preflight()
    if args.mode == "preflight": return
    if REPORT.exists(): fail("final economics report already exists; refusing overwrite")
    print("Starting four independent frozen Q1 workers. Do not interpret partial day outputs.", flush=True)
    reports = []
    with ProcessPoolExecutor(max_workers=4) as pool:
        futs = {pool.submit(worker, day, specs[day["date"]], funding, impl_sha): day["date"] for day in DAYS}
        for fut in as_completed(futs):
            d = futs[fut]; rep = fut.result(); reports.append(rep); print(f"[{d}] worker complete (withheld from interpretation until all four complete)", flush=True)
    if len(reports) != 4 or any(x.get("status") != "PASS" for x in reports): fail("not all four workers completed PASS")
    reports.sort(key=lambda x: x["date"])
    write_final(reports, meta, funding, impl_sha)


if __name__ == "__main__":
    main()
