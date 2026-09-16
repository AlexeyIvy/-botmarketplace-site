"""SC001-E008 frozen maker Discovery engine v1.0.

Modes:
- preflight: no-alpha implementation/identity gate only. No maker simulation or P&L.
- run: one frozen promotional Discovery run on the eight pre-frozen dates.

This executable is intentionally fail-closed. It preserves the frozen queue, stale,
latency, fee, inventory, funding-firewall, and chronology rules.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import io
import itertools
import json
import math
import os
import random
import statistics
import subprocess
import tarfile
import zipfile
from array import array
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

STAGE = "SC001-E008-MAKER-DISCOVERY"
VERSION = "1.0"
PREFLIGHT_PASS = "E008_MAKER_DISCOVERY_IMPLEMENTATION_PREFLIGHT_PASS"
IDENTITY_PASS = "E008_MAKER_DISCOVERY_IDENTITY_GATE_PASS"
DISCOVERY_PASS = "E008_DISCOVERY_PASS_OPEN_CONFIRMATION_ONCE"
DISCOVERY_FAIL = "E008_DISCOVERY_FAIL"

INST = "BTC-USDT-SWAP"
DAYS = (
    "2024-01-06", "2024-01-13", "2024-01-19", "2024-01-24",
    "2024-02-06", "2024-02-11", "2024-02-21", "2024-02-23",
)
TRADE_HEADER = ["instrument_name", "trade_id", "side", "price", "size", "created_time"]

ORDER_QTY = 1.0
PRIMARY_LATENCY_MS = 250
STRESS_LATENCY_MS = 500
TTL_MS = 30_000
MAX_HOLD_MS = 60_000
STALE_MS = 5_000
FORCED_PROXY_WINDOW_MS = 5_000
MAKER_FEE_BPS = 2.0
TAKER_FEE_BPS = 5.0
QUEUE_STRESS_MULT = 2.0
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 8008
EPS = 1e-12

FROZEN_CONFIG = {
    "instrument": INST,
    "discovery_dates": list(DAYS),
    "order_qty_contracts": ORDER_QTY,
    "primary_placement_cancel_latency_ms": PRIMARY_LATENCY_MS,
    "latency_stress_ms": STRESS_LATENCY_MS,
    "quote_ttl_ms": TTL_MS,
    "max_inventory_abs_contracts": 1.0,
    "max_inventory_hold_ms": MAX_HOLD_MS,
    "stale_threshold_ms": STALE_MS,
    "forced_taker_proxy_window_ms": FORCED_PROXY_WINDOW_MS,
    "maker_fee_bps": MAKER_FEE_BPS,
    "taker_fee_bps": TAKER_FEE_BPS,
    "queue_stress_initial_ahead_multiplier": QUEUE_STRESS_MULT,
    "bootstrap_reps": BOOTSTRAP_REPS,
    "bootstrap_seed": BOOTSTRAP_SEED,
    "funding_boundaries_utc_hours": [0, 8, 16],
    "funding_firewall_half_width_ms": 120_000,
    "no_new_flat_cycle_after_utc": "23:58:00",
    "same_ms_trade_l2_queue_credit": False,
    "cancellation_size_decrease_queue_credit": False,
    "level_disappearance_implies_fill": False,
    "snapshot_resync_cancels_live_quotes": True,
    "incremental_update_restores_stale_trust": False,
}

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
DISC_ROOT = DATA_ROOT / "SC001_E008_DISCOVERY_DATA"
TRADES_DIR = DISC_ROOT / "trades"
L2_DIR = DISC_ROOT / "l2"
VERIFY_REPORT = DISC_ROOT / "reports" / "sc001_e008_discovery_acquisition_verify.json"
SEMANTIC_REPORT = DATA_ROOT / "SC001_E008_DISCOVERY_SEMANTIC_INTEGRITY" / "sc001_e008_discovery_semantic_integrity_report.json"
OUT = DATA_ROOT / "SC001_E008_MAKER_DISCOVERY"
PREFLIGHT_REPORT = OUT / "sc001_e008_maker_discovery_preflight_report.json"
DISCOVERY_REPORT = OUT / "sc001_e008_maker_discovery_report.json"
FREEZE_MANIFEST = REPO_ROOT / "docs" / "research" / "sc001-e008-maker-discovery-implementation-freeze-v1.0.json"

Side = Literal["BUY", "SELL"]


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


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing JSON: {path}")
    x = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x, dict):
        fail(f"JSON object expected: {path}")
    return x


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob(path: Path) -> str:
    if not path.exists():
        fail(f"frozen file missing: {path}")
    rel = path.resolve().relative_to(REPO_ROOT.resolve())
    cp = subprocess.run(
        ["git", "hash-object", str(rel)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return cp.stdout.strip()


def parse_ts_ms(text: str) -> int:
    v = int(str(text).strip())
    a = abs(v)
    if a >= 10**17:
        return v // 1_000_000
    if a >= 10**14:
        return v // 1_000
    if a >= 10**11:
        return v
    if a >= 10**9:
        return v * 1000
    fail(f"timestamp scale unresolved: {text!r}")


def day_bounds(day: str) -> tuple[int, int]:
    d = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    lo = int(d.timestamp() * 1000)
    return lo, lo + 86_400_000


def next_day(day: str) -> str:
    return (datetime.strptime(day, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")


def valid_book(asks: dict, bids: dict, ap: list, bp: list) -> bool:
    if not ap or not bp:
        return False
    bid, ask = bp[-1], ap[0]
    if bid >= ask:
        return False
    bs, bo = bids[bid]
    a_s, ao = asks[ask]
    return bs > 0 and a_s > 0 and bo > 0 and ao > 0


def best_price(side: Side, ap: list, bp: list) -> float | None:
    if side == "BUY":
        return float(bp[-1]) if bp else None
    return float(ap[0]) if ap else None


def best_size(side: Side, asks: dict, bids: dict, ap: list, bp: list) -> float | None:
    p = best_price(side, ap, bp)
    if p is None:
        return None
    book = bids if side == "BUY" else asks
    return float(book[p][0])


def parse_level(x) -> tuple[float, float, int]:
    if not isinstance(x, list) or len(x) != 3:
        fail("L2 level shape")
    p = float(x[0]); s = float(x[1]); of = float(x[2]); o = int(round(of))
    if not (math.isfinite(p) and math.isfinite(s) and math.isfinite(of)):
        fail("nonfinite L2 level")
    if p <= 0 or s < 0 or o < 0 or abs(of - o) > 1e-9:
        fail("invalid L2 level")
    if s == 0 and o != 0:
        fail("zero-size L2 delete with nonzero order count")
    return p, s, o


def apply_levels(book: dict, prices: list, levels: list[tuple[float, float, int]]) -> None:
    for p, s, o in levels:
        if s == 0:
            if p not in book:
                fail(f"delete-missing L2 level: {p}")
            del book[p]
            i = bisect.bisect_left(prices, p)
            if i < len(prices) and prices[i] == p:
                prices.pop(i)
        else:
            if p not in book:
                bisect.insort(prices, p)
            book[p] = (s, o)


def iter_l2(path: Path):
    with tarfile.open(path, mode="r|gz") as tf:
        regular = 0
        last = None
        first = True
        for member in tf:
            if not member.isfile():
                continue
            regular += 1
            if regular > 1:
                fail(f"multiple L2 regular members: {path.name}")
            f = tf.extractfile(member)
            if f is None:
                fail(f"cannot extract L2: {path.name}")
            for raw in f:
                if not raw.strip():
                    continue
                r = json.loads(raw)
                if not isinstance(r, dict) or r.get("instId") != INST:
                    fail("L2 record/instrument mismatch")
                action = r.get("action")
                if action not in {"snapshot", "update"}:
                    fail("bad L2 action")
                ts = int(r.get("ts"))
                if last is not None and ts < last:
                    fail("L2 timestamp reversal")
                if first and action != "snapshot":
                    fail("first L2 action is not snapshot")
                first = False
                last = ts
                aa = r.get("asks"); bb = r.get("bids")
                if not isinstance(aa, list) or not isinstance(bb, list):
                    fail("bad L2 sides")
                pa = [parse_level(x) for x in aa]
                pb = [parse_level(x) for x in bb]
                if len({x[0] for x in pa}) != len(pa) or len({x[0] for x in pb}) != len(pb):
                    fail("duplicate price within one L2 record")
                yield ts, action, pa, pb
        if regular != 1:
            fail(f"L2 regular member count {path.name}: {regular}")


def load_trade_day(day: str, exact: Path, neighbor: Path) -> dict:
    lo, hi = day_bounds(day)
    ts = array("q"); px = array("d"); sz = array("d"); side = bytearray()
    prev_ts = prev_id = None
    mins = bytearray(1440)
    for path in (exact, neighbor):
        with zipfile.ZipFile(path, "r") as zf:
            bad = zf.testzip()
            if bad is not None:
                fail(f"trade ZIP CRC failure {path.name}: {bad}")
            ms = [m for m in zf.infolist() if not m.is_dir()]
            if len(ms) != 1:
                fail(f"trade member count {path.name}: {len(ms)}")
            with zf.open(ms[0], "r") as raw:
                rd = csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline=""))
                hdr = [s.strip().lower() for s in (next(rd, None) or [])]
                if hdr != TRADE_HEADER:
                    fail(f"trade header mismatch {path.name}")
                for rn, row in enumerate(rd, start=2):
                    if not row:
                        continue
                    if len(row) != 6:
                        fail(f"trade width {path.name}:{rn}")
                    inst, tidt, sd, pt, st, tt = row
                    tid = int(tidt); sd = sd.strip().lower()
                    p = float(pt); q = float(st); t = parse_ts_ms(tt)
                    if inst.strip() != INST or sd not in {"buy", "sell"}:
                        fail(f"trade schema {path.name}:{rn}")
                    if not (math.isfinite(p) and p > 0 and math.isfinite(q) and q > 0):
                        fail(f"trade numeric {path.name}:{rn}")
                    if lo <= t < hi:
                        if prev_ts is not None and t < prev_ts:
                            fail(f"trade timestamp reversal {day}")
                        if prev_id is not None and tid != prev_id + 1:
                            fail(f"trade ID discontinuity {day}: {prev_id}->{tid}")
                        prev_ts, prev_id = t, tid
                        ts.append(t); px.append(p); sz.append(q)
                        side.append(1 if sd == "buy" else 0)
                        mins[(t - lo) // 60_000] = 1
    if not ts or sum(mins) != 1440:
        fail(f"trade coverage {day}: {sum(mins)}/1440")
    return {"ts": ts, "px": px, "sz": sz, "side": side, "rows": len(ts)}


def load_parent_state() -> tuple[dict, dict, dict[str, dict]]:
    verify = load_json(VERIFY_REPORT)
    if verify.get("status") != "E008_DISCOVERY_ACQUISITION_VERIFY_PASS":
        fail("acquisition verify not exact PASS")
    if len(verify.get("files") or []) != 24:
        fail("acquisition verify file count != 24")
    for k in ("profitability_calculated", "confirmation_body_accessed", "q2_accessed", "validation_or_final_accessed"):
        if verify.get(k) is not False:
            fail(f"acquisition verify firewall mismatch: {k}")

    sem = load_json(SEMANTIC_REPORT)
    if sem.get("status") != "E008_DISCOVERY_SEMANTIC_INTEGRITY_PASS":
        fail("semantic integrity not exact PASS")
    rows = sem.get("days") or []
    if len(rows) != 8 or [r.get("date") for r in rows] != list(DAYS):
        fail("semantic Discovery day chronology mismatch")
    if any(r.get("status") != "DAY_PASS" for r in rows):
        fail("semantic day not DAY_PASS")
    for k in (
        "hypothetical_maker_orders_created", "fill_simulation_calculated",
        "spread_capture_calculated", "markout_calculated", "fees_calculated",
        "inventory_pnl_calculated", "profitability_calculated", "tfi_used",
        "confirmation_body_accessed", "q2_accessed", "validation_or_final_accessed",
    ):
        if sem.get(k) is not False:
            fail(f"semantic firewall mismatch: {k}")

    vb: dict[str, dict] = {}
    for row in verify.get("files") or []:
        p = Path(str(row.get("path", "")))
        if not p.name:
            fail("bad verify path")
        if p.name in vb:
            fail(f"duplicate verify basename: {p.name}")
        vb[p.name] = row
    return verify, sem, vb


def resolve_sources(day: str, vb: dict[str, dict], sem_rows: dict[str, dict]) -> tuple[Path, Path, Path]:
    l2n = f"{INST}-L2orderbook-400lv-{day}.tar.gz"
    en = f"{INST}-trades-{day}.zip"
    nn = f"{INST}-trades-{next_day(day)}.zip"
    lp = L2_DIR / day / l2n
    ep = TRADES_DIR / en
    np = TRADES_DIR / nn
    sr = sem_rows[day]
    expected = {
        l2n: sr.get("l2_sha256"),
        en: sr.get("exact_trade_sha256"),
        nn: sr.get("neighbor_trade_sha256"),
    }
    for p in (lp, ep, np):
        vr = vb.get(p.name)
        if not p.exists() or not isinstance(vr, dict):
            fail(f"source missing/not verified: {p}")
        if p.stat().st_size != int(vr.get("bytes") or -1):
            fail(f"source size mismatch: {p.name}")
        if vr.get("sha256") != expected[p.name]:
            fail(f"semantic/verify SHA disagreement: {p.name}")
    return lp, ep, np


def frozen_identity_checks(hash_market_files: bool = True) -> dict:
    manifest = load_json(FREEZE_MANIFEST)
    if manifest.get("status") != "FROZEN" or manifest.get("version") != VERSION:
        fail("freeze manifest status/version mismatch")
    if manifest.get("config") != FROZEN_CONFIG:
        fail("freeze manifest config mismatch")

    identities = {}
    files = manifest.get("files") or {}
    if not isinstance(files, dict) or not files:
        fail("freeze manifest file identities missing")
    frozen_paths = []
    for name, row in files.items():
        if not isinstance(row, dict):
            fail(f"bad freeze identity row: {name}")
        rel = row.get("path"); expected = row.get("git_blob_sha")
        if not isinstance(rel, str) or not isinstance(expected, str):
            fail(f"bad freeze identity fields: {name}")
        path = REPO_ROOT / rel
        got = git_blob(path)
        identities[name] = {"path": rel, "expected_git_blob_sha": expected, "actual_git_blob_sha": got}
        frozen_paths.append(rel)
        if got != expected:
            fail(f"frozen Git blob mismatch: {rel}")

    cp = subprocess.run(
        ["git", "status", "--porcelain", "--", *frozen_paths],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    if cp.stdout.strip():
        fail(f"frozen implementation has uncommitted changes: {cp.stdout.strip()}")

    verify, sem, vb = load_parent_state()
    sem_rows = {r["date"]: r for r in sem["days"]}
    source_rows = []
    seen = set()
    for day in DAYS:
        for p in resolve_sources(day, vb, sem_rows):
            if p in seen:
                continue
            seen.add(p)
            vr = vb[p.name]
            row = {"path": str(p), "bytes": p.stat().st_size, "expected_sha256": vr.get("sha256")}
            if hash_market_files:
                row["actual_sha256"] = sha256_file(p)
                if row["actual_sha256"] != row["expected_sha256"]:
                    fail(f"market source SHA mismatch: {p.name}")
            source_rows.append(row)
    if len(source_rows) != 24:
        fail(f"unique source count mismatch: {len(source_rows)}")
    return {"manifest": manifest, "implementation_identities": identities, "source_files": source_rows}


def preflight() -> int:
    rep = {
        "stage": STAGE,
        "version": VERSION,
        "mode": "preflight",
        "status": "RUNNING",
        "maker_orders_created": False,
        "fill_simulation_calculated": False,
        "spread_capture_calculated": False,
        "fees_calculated": False,
        "inventory_pnl_calculated": False,
        "profitability_calculated": False,
        "tfi_used": False,
        "confirmation_body_accessed": False,
        "q2_accessed": False,
        "validation_or_final_accessed": False,
    }
    try:
        ident = frozen_identity_checks(hash_market_files=True)
        rep.update(ident)
        rep["status"] = PREFLIGHT_PASS
        rep["identity_gate_status"] = IDENTITY_PASS
        atomic_json(PREFLIGHT_REPORT, rep)
        print(PREFLIGHT_PASS)
        print(IDENTITY_PASS)
        print("verified frozen implementation files =", len(rep["implementation_identities"]))
        print("verified market source files =", len(rep["source_files"]))
        print("maker orders/fills/spread_capture/fees/inventory_PnL/profitability calculated = False")
        print("Confirmation/Q2/Validation/Final = CLOSED")
        print("report =", PREFLIGHT_REPORT)
        return 0
    except Exception as exc:
        rep["status"] = "REVIEW"
        rep["error"] = f"{type(exc).__name__}: {exc}"
        atomic_json(PREFLIGHT_REPORT, rep)
        print("E008_MAKER_DISCOVERY_IMPLEMENTATION_PREFLIGHT_REVIEW")
        print(rep["error"])
        return 2


@dataclass
class SimOrder:
    oid: int
    side: Side
    price: float
    qty: float
    queue_ahead: float
    remaining: float
    activated_ts: int
    ttl_submit_ts: int
    filled: float = 0.0
    cancel_due: int | None = None
    cancel_reason: str | None = None
    ttl_submitted: bool = False

    def compatible(self, aggressor_side: Side, trade_price: float) -> bool:
        if self.side == "BUY":
            return aggressor_side == "SELL" and trade_price <= self.price + EPS
        return aggressor_side == "BUY" and trade_price >= self.price - EPS

    def trade(self, aggressor_side: Side, trade_price: float, trade_qty: float, ambiguous: bool) -> float:
        if ambiguous or not self.compatible(aggressor_side, trade_price):
            return 0.0
        v = float(trade_qty)
        consume = min(self.queue_ahead, v)
        self.queue_ahead -= consume
        v -= consume
        if v <= EPS:
            return 0.0
        fill_qty = min(self.remaining, v)
        self.filled += fill_qty
        self.remaining -= fill_qty
        if self.remaining < EPS:
            self.remaining = 0.0
        return fill_qty

    def size_change(self, old_size: float, new_size: float) -> None:
        if new_size > old_size + EPS:
            self.queue_ahead += new_size - old_size


@dataclass
class PlacementIntent:
    side: Side
    qty: float
    intended_price: float
    decision_ts: int
    due_ts: int


@dataclass
class Cycle:
    first_side: Side
    first_fill_ts: int
    max_hold_ts: int
    fills: list[dict] = field(default_factory=list)
    forced_taker: bool = False


class Engine:
    def __init__(self, name: str, day: str, latency_ms: int, queue_mult: float):
        self.name = name
        self.day = day
        self.lo, self.hi = day_bounds(day)
        self.latency = int(latency_ms)
        self.queue_mult = float(queue_mult)

        self.trusted = False
        self.last_l2_ts: int | None = None
        self.live: dict[Side, SimOrder] = {}
        self.intents: dict[Side, PlacementIntent] = {}
        self.ready_at: dict[Side, int | None] = {"BUY": None, "SELL": None}
        self.next_oid = 1

        self.inventory = 0.0
        self.max_abs_inventory = 0.0
        self.cycle: Cycle | None = None
        self.cycles: list[dict] = []
        self.forced_pending: dict | None = None

        self.invalid_reasons: list[str] = []
        self.unresolved_inventory = 0

        self.stale_latches = 0
        self.snapshot_resync_cancels = 0
        self.level_disappear_cancels = 0
        self.best_move_cancel_requests = 0
        self.ttl_cancel_requests = 0
        self.cancel_acks = 0
        self.placement_rejects = 0
        self.placement_activations = 0
        self.same_ms_zero_credit_trades = 0
        self.size_increase_events = 0
        self.size_decrease_zero_credit_events = 0
        self.forced_taker_exits = 0
        self.order_fill_events = 0
        self.firewall_flat_cancels = 0

        self.funding_starts = [self.lo + 7*3600_000 + 58*60_000, self.lo + 15*3600_000 + 58*60_000, self.hi - 120_000]
        self.funding_ends = [self.lo + 120_000, self.lo + 8*3600_000 + 120_000, self.lo + 16*3600_000 + 120_000]
        self.funding_boundaries = [self.lo + 8*3600_000, self.lo + 16*3600_000, self.hi]
        self.processed_special: set[tuple[str, int]] = set()

    def mark_invalid(self, reason: str) -> None:
        if reason not in self.invalid_reasons:
            self.invalid_reasons.append(reason)

    def flat_allowed(self, t: int) -> bool:
        if t < self.lo + 120_000:
            return False
        if t >= self.hi - 120_000:
            return False
        for b in (self.lo + 8*3600_000, self.lo + 16*3600_000):
            if b - 120_000 <= t < b + 120_000:
                return False
        return True

    def desired_side_qty(self, side: Side) -> float:
        if self.forced_pending is not None:
            return 0.0
        if abs(self.inventory) <= EPS:
            if self.cycle is not None:
                return 0.0
            return ORDER_QTY
        if self.inventory > 0:
            return abs(self.inventory) if side == "SELL" else 0.0
        return abs(self.inventory) if side == "BUY" else 0.0

    def book_view(self, side: Side, asks, bids, ap, bp) -> tuple[float, float] | None:
        if not self.trusted or not valid_book(asks, bids, ap, bp):
            return None
        p = best_price(side, ap, bp)
        s = best_size(side, asks, bids, ap, bp)
        if p is None or s is None or s <= 0:
            return None
        return p, s

    def clear_intents(self) -> None:
        self.intents.clear()

    def immediate_cancel(self, side: Side, t: int, reason: str, impose_cancel_cooldown: bool) -> None:
        if side not in self.live:
            return
        del self.live[side]
        self.cancel_acks += 1
        if impose_cancel_cooldown:
            self.ready_at[side] = max(self.ready_at[side] or t, t + self.latency)
        if reason == "SNAPSHOT_RESYNC":
            self.snapshot_resync_cancels += 1
        elif reason == "LEVEL_DISAPPEAR":
            self.level_disappear_cancels += 1

    def immediate_cancel_all(self, t: int, reason: str, impose_cancel_cooldown: bool) -> None:
        for side in list(self.live):
            self.immediate_cancel(side, t, reason, impose_cancel_cooldown)
        self.clear_intents()

    def request_cancel(self, side: Side, t: int, reason: str) -> None:
        o = self.live.get(side)
        if o is None:
            return
        due = t + self.latency
        if o.cancel_due is None or due < o.cancel_due:
            o.cancel_due = due
            o.cancel_reason = reason
        if reason == "NOT_BEST":
            self.best_move_cancel_requests += 1
        elif reason == "TTL":
            self.ttl_cancel_requests += 1

    def schedule_intent(self, side: Side, qty: float, t: int, asks, bids, ap, bp) -> None:
        if qty <= EPS or side in self.intents or side in self.live:
            return
        ra = self.ready_at.get(side)
        if ra is not None and t < ra:
            return
        view = self.book_view(side, asks, bids, ap, bp)
        if view is None:
            return
        p, _s = view
        self.intents[side] = PlacementIntent(side, qty, p, t, t + self.latency)

    def maybe_finalize_cycle(self, t: int) -> None:
        if self.cycle is None or abs(self.inventory) > EPS:
            return
        if self.live or self.intents:
            return
        c = self.cycle
        buys = [f for f in c.fills if f["side"] == "BUY"]
        sells = [f for f in c.fills if f["side"] == "SELL"]
        buy_qty = sum(f["qty"] for f in buys)
        sell_qty = sum(f["qty"] for f in sells)
        if abs(buy_qty - sell_qty) > 1e-9 or buy_qty <= EPS:
            self.mark_invalid("cycle_quantity_not_flat")
            return
        buy_notional = sum(f["qty"] * f["price"] for f in buys)
        sell_notional = sum(f["qty"] * f["price"] for f in sells)
        first = c.first_side
        entry_notional = buy_notional if first == "BUY" else sell_notional
        if entry_notional <= 0:
            self.mark_invalid("cycle_entry_notional_nonpositive")
            return
        fee_notional = sum(
            f["qty"] * f["price"] * (MAKER_FEE_BPS if f["liquidity"] == "maker" else TAKER_FEE_BPS) / 10_000.0
            for f in c.fills
        )
        gross_pnl = sell_notional - buy_notional
        net_pnl = gross_pnl - fee_notional
        gross_bps = gross_pnl / entry_notional * 10_000.0
        net_bps = net_pnl / entry_notional * 10_000.0
        self.cycles.append({
            "first_side": first,
            "first_fill_ts": c.first_fill_ts,
            "completion_ts": t,
            "duration_ms": t - c.first_fill_ts,
            "fill_count": len(c.fills),
            "forced_taker": c.forced_taker,
            "buy_qty": buy_qty,
            "sell_qty": sell_qty,
            "buy_notional_normalized": buy_notional,
            "sell_notional_normalized": sell_notional,
            "fee_notional_normalized": fee_notional,
            "gross_pnl_normalized": gross_pnl,
            "net_pnl_normalized": net_pnl,
            "gross_edge_bps": gross_bps,
            "net_edge_bps": net_bps,
        })
        self.cycle = None

    def record_fill(self, t: int, side: Side, qty: float, price: float, liquidity: str) -> None:
        if qty <= EPS:
            return
        before = self.inventory
        if self.cycle is None:
            if liquidity != "maker":
                self.mark_invalid("cycle_started_by_nonmaker")
                return
            self.cycle = Cycle(first_side=side, first_fill_ts=t, max_hold_ts=t + MAX_HOLD_MS)
        delta = qty if side == "BUY" else -qty
        after = before + delta

        if before * after < -EPS:
            self.mark_invalid("inventory_sign_flip_without_flat_terminal")
            return
        self.inventory = 0.0 if abs(after) <= EPS else after
        self.max_abs_inventory = max(self.max_abs_inventory, abs(self.inventory))
        if self.max_abs_inventory > 1.0 + 1e-9:
            self.mark_invalid("max_inventory_exceeded")

        self.cycle.fills.append({
            "ts": t, "side": side, "qty": qty, "price": price, "liquidity": liquidity,
        })
        self.order_fill_events += 1

        self.clear_intents()
        for s in list(self.live):
            self.request_cancel(s, t, "STATE_CHANGE")

        if abs(self.inventory) <= EPS:
            self.maybe_finalize_cycle(t)

    def execute_forced_taker(self, t: int, price: float) -> None:
        if self.forced_pending is None or abs(self.inventory) <= EPS:
            return
        side: Side = "SELL" if self.inventory > 0 else "BUY"
        qty = abs(self.inventory)
        if self.cycle is None:
            self.mark_invalid("forced_exit_without_cycle")
            return
        self.cycle.forced_taker = True
        self.forced_taker_exits += 1
        self.record_fill(t, side, qty, float(price), "taker")
        self.forced_pending = None
        self.maybe_finalize_cycle(t)

    def reconcile(self, t: int, asks, bids, ap, bp) -> None:
        if self.invalid_reasons or self.forced_pending is not None:
            return

        self.maybe_finalize_cycle(t)

        if abs(self.inventory) <= EPS and self.cycle is not None:
            return

        if abs(self.inventory) <= EPS:
            if not self.flat_allowed(t):
                return
            for side in ("BUY", "SELL"):
                qty = self.desired_side_qty(side)
                if qty > EPS:
                    self.schedule_intent(side, qty, t, asks, bids, ap, bp)
            return

        side: Side = "SELL" if self.inventory > 0 else "BUY"
        qty = abs(self.inventory)

        conflicting = False
        desired_live = False
        for s, o in list(self.live.items()):
            if s == side and abs(o.qty - qty) <= 1e-9 and o.cancel_due is None:
                desired_live = True
                continue
            self.request_cancel(s, t, "STATE_CHANGE")
            conflicting = True

        if conflicting:
            self.clear_intents()
            return
        if desired_live:
            self.intents.pop(side, None)
            return

        self.clear_intents()
        self.schedule_intent(side, qty, t, asks, bids, ap, bp)

    def process_cancel_ack(self, side: Side, due: int) -> None:
        o = self.live.get(side)
        if o is None or o.cancel_due != due:
            return
        del self.live[side]
        self.cancel_acks += 1
        self.ready_at[side] = due

    def process_ttl_submit(self, side: Side, t: int) -> None:
        o = self.live.get(side)
        if o is None or o.ttl_submitted or o.ttl_submit_ts != t:
            return
        o.ttl_submitted = True
        self.request_cancel(side, t, "TTL")

    def process_activation(self, side: Side, due: int, asks, bids, ap, bp) -> None:
        intent = self.intents.get(side)
        if intent is None or intent.due_ts != due:
            return
        del self.intents[side]

        qty_now = self.desired_side_qty(side)
        if qty_now <= EPS or abs(qty_now - intent.qty) > 1e-9:
            self.placement_rejects += 1
            self.reconcile(due, asks, bids, ap, bp)
            return
        if abs(self.inventory) <= EPS and not self.flat_allowed(due):
            self.placement_rejects += 1
            return
        view = self.book_view(side, asks, bids, ap, bp)
        if view is None:
            self.placement_rejects += 1
            return
        p, s = view
        if abs(p - intent.intended_price) > EPS:
            self.placement_rejects += 1
            self.schedule_intent(side, qty_now, due, asks, bids, ap, bp)
            return
        bid = best_price("BUY", ap, bp); ask = best_price("SELL", ap, bp)
        if bid is None or ask is None:
            self.placement_rejects += 1
            return
        if (side == "BUY" and p >= ask - EPS) or (side == "SELL" and p <= bid + EPS):
            self.placement_rejects += 1
            return

        q_ahead = s * self.queue_mult
        self.live[side] = SimOrder(
            oid=self.next_oid, side=side, price=p, qty=qty_now,
            queue_ahead=q_ahead, remaining=qty_now,
            activated_ts=due, ttl_submit_ts=due + TTL_MS,
        )
        self.next_oid += 1
        self.placement_activations += 1

    def process_stale(self, t: int) -> None:
        if not self.trusted or self.last_l2_ts is None:
            return
        if t != self.last_l2_ts + STALE_MS + 1:
            return
        self.trusted = False
        self.stale_latches += 1
        self.immediate_cancel_all(t, "STALE_LATCH", impose_cancel_cooldown=False)

    def process_firewall_start(self, t: int) -> None:
        if abs(self.inventory) <= EPS and self.cycle is None:
            n = len(self.live)
            self.immediate_cancel_all(t, "FUNDING_FIREWALL", impose_cancel_cooldown=False)
            self.firewall_flat_cancels += n

    def process_funding_boundary(self, t: int) -> None:
        if abs(self.inventory) > EPS:
            self.unresolved_inventory = 1
            self.mark_invalid(f"inventory_nonzero_at_funding_boundary:{t}")

    def process_max_hold(self, t: int) -> None:
        if self.cycle is None or self.cycle.max_hold_ts != t:
            return
        if abs(self.inventory) <= EPS:
            self.maybe_finalize_cycle(t)
            return
        self.immediate_cancel_all(t, "MAX_HOLD_FORCE", impose_cancel_cooldown=False)
        self.forced_pending = {
            "decision_ts": t,
            "ready_ts": t + self.latency,
            "deadline_ts": t + self.latency + FORCED_PROXY_WINDOW_MS,
        }

    def process_forced_deadline(self, t: int) -> None:
        if self.forced_pending is None or self.forced_pending["deadline_ts"] != t:
            return
        if abs(self.inventory) > EPS:
            self.unresolved_inventory = 1
            self.mark_invalid("forced_taker_proxy_missing")
        self.forced_pending = None

    def due_times(self) -> list[tuple[str, int, str | None]]:
        out: list[tuple[str, int, str | None]] = []
        if self.trusted and self.last_l2_ts is not None:
            out.append(("stale", self.last_l2_ts + STALE_MS + 1, None))
        if self.cycle is not None and ("max_hold", self.cycle.max_hold_ts) not in self.processed_special:
            out.append(("max_hold", self.cycle.max_hold_ts, None))
        if self.forced_pending is not None:
            out.append(("forced_deadline", self.forced_pending["deadline_ts"], None))
        for side, o in self.live.items():
            if not o.ttl_submitted:
                out.append(("ttl", o.ttl_submit_ts, side))
            if o.cancel_due is not None:
                out.append(("cancel", o.cancel_due, side))
        for side, intent in self.intents.items():
            out.append(("activate", intent.due_ts, side))
        for side, ra in self.ready_at.items():
            if ra is not None:
                out.append(("ready", ra, side))
        for t in self.funding_starts:
            if ("firewall_start", t) not in self.processed_special:
                out.append(("firewall_start", t, None))
        for t in self.funding_ends:
            if ("firewall_end", t) not in self.processed_special:
                out.append(("firewall_end", t, None))
        for t in self.funding_boundaries:
            if ("funding_boundary", t) not in self.processed_special:
                out.append(("funding_boundary", t, None))
        return out

    def advance_pre(self, target: int, asks, bids, ap, bp) -> None:
        while True:
            cands = []
            for kind, t, side in self.due_times():
                if t < target or (t == target and kind not in {"activate", "forced_deadline"}):
                    cands.append((t, kind, side))
            if not cands:
                break
            t, kind, side = min(cands, key=lambda x: (x[0], x[1], x[2] or ""))
            if t > self.hi:
                break

            if kind == "stale":
                self.process_stale(t)
            elif kind == "max_hold":
                self.processed_special.add((kind, t))
                self.process_max_hold(t)
            elif kind == "forced_deadline":
                self.process_forced_deadline(t)
            elif kind == "ttl":
                self.process_ttl_submit(side, t)
            elif kind == "cancel":
                self.process_cancel_ack(side, t)
            elif kind == "ready":
                self.ready_at[side] = None
            elif kind == "firewall_start":
                self.processed_special.add((kind, t))
                self.process_firewall_start(t)
            elif kind == "firewall_end":
                self.processed_special.add((kind, t))
            elif kind == "funding_boundary":
                self.processed_special.add((kind, t))
                self.process_funding_boundary(t)
            elif kind == "activate":
                self.process_activation(side, t, asks, bids, ap, bp)
            self.reconcile(t, asks, bids, ap, bp)

    def advance_post(self, t: int, asks, bids, ap, bp) -> None:
        while True:
            due = [(it.due_ts, side) for side, it in self.intents.items() if it.due_ts <= t]
            if not due:
                break
            d, side = min(due)
            self.process_activation(side, d, asks, bids, ap, bp)
            self.reconcile(d, asks, bids, ap, bp)

        if self.forced_pending is not None and self.forced_pending["deadline_ts"] <= t:
            d = self.forced_pending["deadline_ts"]
            self.process_forced_deadline(d)
            self.reconcile(d, asks, bids, ap, bp)

        self.reconcile(t, asks, bids, ap, bp)

    def on_trade(self, t: int, aggressor_side: Side, price: float, qty: float, ambiguous: bool) -> None:
        if self.invalid_reasons:
            return

        if self.forced_pending is not None:
            ready = self.forced_pending["ready_ts"]
            deadline = self.forced_pending["deadline_ts"]
            if ready <= t <= deadline and abs(self.inventory) > EPS:
                self.execute_forced_taker(t, price)
                return

        if ambiguous:
            self.same_ms_zero_credit_trades += 1
            return
        if not self.trusted:
            return

        for side in ("BUY", "SELL"):
            o = self.live.get(side)
            if o is None:
                continue
            before = o.remaining
            fq = o.trade(aggressor_side, price, qty, ambiguous=False)
            if fq > EPS:
                self.record_fill(t, side, fq, o.price, "maker")
            if o.remaining <= EPS and side in self.live:
                del self.live[side]
            if fq > EPS and self.invalid_reasons:
                return
            if before > EPS and fq > EPS:
                self.reconcile(t, {}, {}, [], [])

    def capture_pre_l2(self, asks, bids) -> dict[int, tuple[bool, float | None]]:
        out = {}
        for o in self.live.values():
            book = bids if o.side == "BUY" else asks
            if o.price in book:
                out[o.oid] = (True, float(book[o.price][0]))
            else:
                out[o.oid] = (False, None)
        return out

    def on_l2(self, t: int, has_snapshot: bool, pre: dict[int, tuple[bool, float | None]], asks, bids, ap, bp) -> None:
        if self.invalid_reasons:
            return

        if has_snapshot:
            self.immediate_cancel_all(t, "SNAPSHOT_RESYNC", impose_cancel_cooldown=True)
            self.trusted = True
        self.last_l2_ts = t

        if self.trusted and not valid_book(asks, bids, ap, bp):
            self.mark_invalid("invalid_reconstructed_book")
            self.immediate_cancel_all(t, "INVALID_BOOK", impose_cancel_cooldown=False)
            self.trusted = False
            return

        if not self.trusted:
            return

        for side, o in list(self.live.items()):
            book = bids if side == "BUY" else asks
            was_present, old_size = pre.get(o.oid, (False, None))
            if o.price not in book:
                self.immediate_cancel(side, t, "LEVEL_DISAPPEAR", impose_cancel_cooldown=True)
                continue
            new_size = float(book[o.price][0])
            if was_present and old_size is not None:
                if new_size > old_size + EPS:
                    self.size_increase_events += 1
                elif new_size < old_size - EPS:
                    self.size_decrease_zero_credit_events += 1
                o.size_change(old_size, new_size)

            bp_now = best_price(side, ap, bp)
            if bp_now is None or abs(o.price - bp_now) > EPS:
                self.request_cancel(side, t, "NOT_BEST")

        self.reconcile(t, asks, bids, ap, bp)

    def finish_day(self, asks, bids, ap, bp) -> dict:
        self.advance_pre(self.hi, asks, bids, ap, bp)
        self.advance_post(self.hi, asks, bids, ap, bp)
        self.immediate_cancel_all(self.hi, "DAY_END", impose_cancel_cooldown=False)
        if abs(self.inventory) > EPS:
            self.unresolved_inventory = 1
            self.mark_invalid("inventory_nonzero_day_end")
        self.maybe_finalize_cycle(self.hi)

        if self.cycle is not None and abs(self.inventory) <= EPS and not self.live and not self.intents:
            self.maybe_finalize_cycle(self.hi)

        return {
            "date": self.day,
            "scenario": self.name,
            "latency_ms": self.latency,
            "initial_queue_multiplier": self.queue_mult,
            "completed_cycles": len(self.cycles),
            "cycles": self.cycles,
            "unresolved_inventory": self.unresolved_inventory,
            "max_abs_inventory": self.max_abs_inventory,
            "forced_taker_exits": self.forced_taker_exits,
            "stale_latches": self.stale_latches,
            "snapshot_resync_cancels": self.snapshot_resync_cancels,
            "level_disappear_cancels": self.level_disappear_cancels,
            "best_move_cancel_requests": self.best_move_cancel_requests,
            "ttl_cancel_requests": self.ttl_cancel_requests,
            "cancel_acks": self.cancel_acks,
            "placement_rejects": self.placement_rejects,
            "placement_activations": self.placement_activations,
            "same_ms_zero_credit_trades": self.same_ms_zero_credit_trades,
            "size_increase_events": self.size_increase_events,
            "size_decrease_zero_credit_events": self.size_decrease_zero_credit_events,
            "firewall_flat_cancels": self.firewall_flat_cancels,
            "invalid_reasons": self.invalid_reasons,
            "day_valid": not self.invalid_reasons and self.unresolved_inventory == 0 and self.max_abs_inventory <= 1.0 + 1e-9,
        }


def run_day(day: str, l2_path: Path, exact: Path, neighbor: Path) -> dict[str, dict]:
    print(f"MAKER DISCOVERY {day}: load trades")
    tr = load_trade_day(day, exact, neighbor)
    engines = {
        "primary": Engine("primary", day, PRIMARY_LATENCY_MS, 1.0),
        "latency_500ms": Engine("latency_500ms", day, STRESS_LATENCY_MS, 1.0),
        "queue_2x": Engine("queue_2x", day, PRIMARY_LATENCY_MS, QUEUE_STRESS_MULT),
    }

    asks: dict = {}; bids: dict = {}; ap: list = []; bp: list = []
    ti = 0
    ntr = int(tr["rows"])

    def process_trade_group(ts_value: int, ambiguous: bool) -> None:
        nonlocal ti
        for e in engines.values():
            e.advance_pre(ts_value, asks, bids, ap, bp)
        while ti < ntr and int(tr["ts"][ti]) == ts_value:
            side: Side = "BUY" if bool(tr["side"][ti]) else "SELL"
            p = float(tr["px"][ti]); q = float(tr["sz"][ti])
            for e in engines.values():
                e.on_trade(ts_value, side, p, q, ambiguous)
            ti += 1
        for e in engines.values():
            e.advance_post(ts_value, asks, bids, ap, bp)

    print(f"MAKER DISCOVERY {day}: replay L2 + 3 frozen scenarios")
    for t, group_iter in itertools.groupby(iter_l2(l2_path), key=lambda x: x[0]):
        t = int(t)

        while ti < ntr and int(tr["ts"][ti]) < t:
            tt = int(tr["ts"][ti])
            process_trade_group(tt, ambiguous=False)

        for e in engines.values():
            e.advance_pre(t, asks, bids, ap, bp)

        while ti < ntr and int(tr["ts"][ti]) == t:
            side: Side = "BUY" if bool(tr["side"][ti]) else "SELL"
            p = float(tr["px"][ti]); q = float(tr["sz"][ti])
            for e in engines.values():
                e.on_trade(t, side, p, q, ambiguous=True)
            ti += 1

        rows = list(group_iter)

        for _tt, action, aa, bb in rows:
            pre = {name: e.capture_pre_l2(asks, bids) for name, e in engines.items()}
            if action == "snapshot":
                asks.clear(); bids.clear(); ap.clear(); bp.clear()
            apply_levels(asks, ap, aa)
            apply_levels(bids, bp, bb)
            if not valid_book(asks, bids, ap, bp):
                fail(f"semantic-qualified L2 became invalid during replay {day} at {t}")
            for name, e in engines.items():
                e.on_l2(t, action == "snapshot", pre[name], asks, bids, ap, bp)

        for e in engines.values():
            e.advance_post(t, asks, bids, ap, bp)

    while ti < ntr:
        tt = int(tr["ts"][ti])
        process_trade_group(tt, ambiguous=False)

    out = {}
    for name, e in engines.items():
        out[name] = e.finish_day(asks, bids, ap, bp)
        print(
            f"MAKER DISCOVERY {day} {name}: "
            f"cycles={out[name]['completed_cycles']} "
            f"forced={out[name]['forced_taker_exits']} "
            f"unresolved={out[name]['unresolved_inventory']} "
            f"valid={out[name]['day_valid']}"
        )
    return out


def scenario_summary(days: list[dict]) -> dict:
    cycles = [c for d in days for c in d.get("cycles", [])]
    edges = [float(c["net_edge_bps"]) for c in cycles]
    day_means = []
    day_pnls = []
    for d in days:
        cs = d.get("cycles", [])
        day_means.append(statistics.fmean(float(c["net_edge_bps"]) for c in cs) if cs else -1e100)
        day_pnls.append(sum(float(c["net_pnl_normalized"]) for c in cs))

    valid_day_means = [x for x in day_means if math.isfinite(x)]
    n = len(edges)
    k = int(math.floor(0.10 * n))
    sedges = sorted(edges)
    trimmed = sedges[k:n-k] if n > 2*k and n else []
    total_abs_contrib = sum(abs(x) for x in day_pnls)
    sorted_abs = sorted((abs(x) for x in day_pnls), reverse=True)
    top1 = sorted_abs[0] / total_abs_contrib if total_abs_contrib > EPS and sorted_abs else 1e100
    top3 = sum(sorted_abs[:3]) / total_abs_contrib if total_abs_contrib > EPS else 1e100
    forced = sum(1 for c in cycles if c.get("forced_taker"))
    long_first = sum(1 for c in cycles if c.get("first_side") == "BUY")
    short_first = sum(1 for c in cycles if c.get("first_side") == "SELL")

    valid_days_count = sum(1 for d in days if d.get("day_valid") is True)
    unresolved_total = sum(int(d.get("unresolved_inventory", 0)) for d in days)
    return {
        "completed_cycles": n,
        "active_days": sum(1 for d in days if d.get("completed_cycles", 0) > 0),
        "valid_days": valid_days_count,
        "unresolved_inventory_total": unresolved_total,
        "accounting_complete": valid_days_count == 8 and unresolved_total == 0,
        "max_abs_inventory": max((float(d.get("max_abs_inventory", 0.0)) for d in days), default=0.0),
        "forced_taker_exits": forced,
        "forced_taker_exit_share": forced / n if n else 1e100,
        "mean_net_edge_bps": statistics.fmean(edges) if edges else -1e100,
        "trimmed_mean_10pct_net_edge_bps": statistics.fmean(trimmed) if trimmed else -1e100,
        "median_net_edge_bps": statistics.median(edges) if edges else -1e100,
        "positive_days": sum(1 for x in valid_day_means if x > 0),
        "daily_mean_net_edge_bps": day_means,
        "median_daily_mean_net_edge_bps": statistics.median(valid_day_means) if valid_day_means else -1e100,
        "daily_net_pnl_normalized": day_pnls,
        "total_net_pnl_normalized": sum(day_pnls),
        "top1_absolute_daily_contribution_share": top1,
        "top3_absolute_daily_contribution_share": top3,
        "long_first_cycles": long_first,
        "short_first_cycles": short_first,
        "invalid_reasons": sorted({r for d in days for r in d.get("invalid_reasons", [])}),
    }


def bootstrap_day_lcb(primary_days: list[dict]) -> float:
    if len(primary_days) != 8 or any(not d.get("cycles") for d in primary_days):
        return -1e100
    rng = random.Random(BOOTSTRAP_SEED)
    vals = []
    for _ in range(BOOTSTRAP_REPS):
        sample = [primary_days[rng.randrange(8)] for _j in range(8)]
        edges = [float(c["net_edge_bps"]) for d in sample for c in d["cycles"]]
        vals.append(statistics.fmean(edges))
    vals.sort()
    idx = int(math.floor(0.05 * BOOTSTRAP_REPS))
    return vals[idx]


def evaluate_gates(primary: dict, latency: dict, queue2: dict, lcb: float) -> dict:
    gates = {
        "source_data_integrity_8_of_8": primary["valid_days"] == 8,
        "completed_cycles_gte_100": primary["completed_cycles"] >= 100,
        "active_days_8_of_8": primary["active_days"] == 8,
        "unresolved_inventory_eq_0": primary["unresolved_inventory_total"] == 0,
        "max_abs_inventory_lte_1": primary["max_abs_inventory"] <= 1.0 + 1e-9,
        "forced_taker_exit_share_lte_10pct": primary["forced_taker_exit_share"] <= 0.10,
        "pooled_mean_net_edge_gte_1bps": primary["mean_net_edge_bps"] >= 1.0,
        "trimmed_mean_gte_0_5bps": primary["trimmed_mean_10pct_net_edge_bps"] >= 0.5,
        "pooled_median_gte_0": primary["median_net_edge_bps"] >= 0.0,
        "positive_days_gte_6_of_8": primary["positive_days"] >= 6,
        "median_daily_mean_gt_0": primary["median_daily_mean_net_edge_bps"] > 0.0,
        "day_block_bootstrap_95pct_lcb_gt_0": math.isfinite(lcb) and lcb > 0.0,
        "top1_abs_daily_contribution_lte_0_30": primary["top1_absolute_daily_contribution_share"] <= 0.30,
        "top3_abs_daily_contribution_lte_0_65": primary["top3_absolute_daily_contribution_share"] <= 0.65,
        "long_first_cycles_gte_20": primary["long_first_cycles"] >= 20,
        "short_first_cycles_gte_20": primary["short_first_cycles"] >= 20,
        "primary_invariants_exact_pass": not primary["invalid_reasons"] and primary["valid_days"] == 8,
        "latency_500ms_mean_gte_0": latency["accounting_complete"] and latency["mean_net_edge_bps"] >= 0.0,
        "latency_500ms_total_net_pnl_gt_0": latency["accounting_complete"] and latency["total_net_pnl_normalized"] > 0.0,
        "queue_2x_mean_gte_0": queue2["accounting_complete"] and queue2["mean_net_edge_bps"] >= 0.0,
        "queue_2x_unresolved_eq_0": queue2["unresolved_inventory_total"] == 0 and queue2["valid_days"] == 8,
    }
    return gates


def require_preflight_identity() -> dict:
    p = load_json(PREFLIGHT_REPORT)
    if p.get("status") != PREFLIGHT_PASS or p.get("identity_gate_status") != IDENTITY_PASS:
        fail("maker implementation preflight/identity gate not exact PASS")
    return frozen_identity_checks(hash_market_files=True)


def run_discovery() -> int:
    require_preflight_identity()
    verify, sem, vb = load_parent_state()
    sem_rows = {r["date"]: r for r in sem["days"]}

    all_days = {"primary": [], "latency_500ms": [], "queue_2x": []}
    source_identity = []
    errors = []

    for day in DAYS:
        try:
            lp, ep, np = resolve_sources(day, vb, sem_rows)
            source_identity.append({
                "date": day,
                "l2": {"path": str(lp), "sha256": sem_rows[day]["l2_sha256"]},
                "exact_trade": {"path": str(ep), "sha256": sem_rows[day]["exact_trade_sha256"]},
                "neighbor_trade": {"path": str(np), "sha256": sem_rows[day]["neighbor_trade_sha256"]},
            })
            r = run_day(day, lp, ep, np)
            for name in all_days:
                all_days[name].append(r[name])
        except Exception as exc:
            msg = f"{day}: {type(exc).__name__}: {exc}"
            errors.append(msg)
            print("MAKER DISCOVERY ERROR", msg)
            break

    if errors or any(len(v) != 8 for v in all_days.values()):
        rep = {
            "stage": STAGE, "version": VERSION, "status": DISCOVERY_FAIL,
            "errors": errors,
            "source_identity": source_identity,
            "confirmation_body_accessed": False,
            "q2_accessed": False,
            "validation_or_final_accessed": False,
            "tfi_used": False,
        }
        atomic_json(DISCOVERY_REPORT, rep)
        print(DISCOVERY_FAIL)
        print("run aborted fail-closed")
        print("Confirmation/Q2/Validation/Final = CLOSED")
        return 2

    summaries = {name: scenario_summary(days) for name, days in all_days.items()}
    lcb = bootstrap_day_lcb(all_days["primary"])
    gates = evaluate_gates(summaries["primary"], summaries["latency_500ms"], summaries["queue_2x"], lcb)
    passed = all(gates.values())
    status = DISCOVERY_PASS if passed else DISCOVERY_FAIL

    rep = {
        "stage": STAGE,
        "version": VERSION,
        "status": status,
        "frozen_config": FROZEN_CONFIG,
        "source_identity": source_identity,
        "scenarios": all_days,
        "summaries": summaries,
        "day_block_bootstrap_95pct_lcb_bps": lcb,
        "gates": gates,
        "failed_gates": [k for k, v in gates.items() if not v],
        "maker_orders_created": True,
        "fill_simulation_calculated": True,
        "spread_capture_calculated": True,
        "fees_calculated": True,
        "inventory_pnl_calculated": True,
        "profitability_calculated": True,
        "tfi_used": False,
        "confirmation_body_accessed": False,
        "q2_accessed": False,
        "validation_or_final_accessed": False,
    }
    atomic_json(DISCOVERY_REPORT, rep)

    print(status)
    print("primary_completed_cycles =", summaries["primary"]["completed_cycles"])
    print("primary_mean_net_edge_bps =", summaries["primary"]["mean_net_edge_bps"])
    print("primary_trimmed_mean_bps =", summaries["primary"]["trimmed_mean_10pct_net_edge_bps"])
    print("primary_median_bps =", summaries["primary"]["median_net_edge_bps"])
    print("primary_positive_days =", summaries["primary"]["positive_days"], "/ 8")
    print("primary_forced_taker_share =", summaries["primary"]["forced_taker_exit_share"])
    print("bootstrap_95pct_LCB_bps =", lcb)
    print("latency_500ms_mean_bps =", summaries["latency_500ms"]["mean_net_edge_bps"])
    print("queue_2x_mean_bps =", summaries["queue_2x"]["mean_net_edge_bps"])
    print("failed_gates =", rep["failed_gates"])
    print("Confirmation/Q2/Validation/Final = CLOSED")
    print("report =", DISCOVERY_REPORT)
    return 0 if passed else 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("preflight", "run"))
    a = ap.parse_args()
    if a.mode == "preflight":
        return preflight()
    return run_discovery()


if __name__ == "__main__":
    raise SystemExit(main())
