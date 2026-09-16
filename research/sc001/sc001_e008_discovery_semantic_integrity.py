"""SC001-E008 full semantic integrity qualification for frozen Discovery data.

Data-quality only: no maker orders, fills, spread capture, markout, fees,
inventory P&L or profitability.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import io
import json
import math
import os
import tarfile
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

STAGE = "SC001-E008-DISCOVERY-SEMANTIC-INTEGRITY"
VERSION = "1.0"
PASS = "E008_DISCOVERY_SEMANTIC_INTEGRITY_PASS"
REVIEW = "E008_DISCOVERY_SEMANTIC_INTEGRITY_REVIEW"
DAY_PASS = "DAY_PASS"
INST = "BTC-USDT-SWAP"
DAYS = (
    "2024-01-06", "2024-01-13", "2024-01-19", "2024-01-24",
    "2024-02-06", "2024-02-11", "2024-02-21", "2024-02-23",
)
TRADE_HEADER = ["instrument_name", "trade_id", "side", "price", "size", "created_time"]
DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
ROOT = DATA_ROOT / "SC001_E008_DISCOVERY_DATA"
TRADES = ROOT / "trades"
L2 = ROOT / "l2"
VERIFY_REPORT = ROOT / "reports" / "sc001_e008_discovery_acquisition_verify.json"
OUT = DATA_ROOT / "SC001_E008_DISCOVERY_SEMANTIC_INTEGRITY"
CHECKPOINTS = OUT / "checkpoints"
REPORT = OUT / "sc001_e008_discovery_semantic_integrity_report.json"


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_ts_ms(text: str) -> int:
    v = int(str(text).strip()); a = abs(v)
    if a >= 10**17: return v // 1_000_000
    if a >= 10**14: return v // 1_000
    if a >= 10**11: return v
    if a >= 10**9: return v * 1000
    fail(f"timestamp scale unresolved: {text!r}")


def day_bounds(day: str) -> tuple[int, int]:
    d = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    lo = int(d.timestamp() * 1000)
    return lo, lo + 86_400_000


def next_day(day: str) -> str:
    return (datetime.strptime(day, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")


def load_verify() -> dict:
    if not VERIFY_REPORT.exists(): fail(f"missing verify report: {VERIFY_REPORT}")
    x = json.loads(VERIFY_REPORT.read_text(encoding="utf-8"))
    if x.get("status") != "E008_DISCOVERY_ACQUISITION_VERIFY_PASS":
        fail("acquisition verify report is not exact PASS")
    if x.get("profitability_calculated") is not False or x.get("confirmation_body_accessed") is not False:
        fail("verify firewall mismatch")
    files = x.get("files") or []
    if len(files) != 24: fail(f"verify file count mismatch: {len(files)}")
    return x


def verified_by_basename(v: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for row in v.get("files") or []:
        p = Path(str(row.get("path", "")))
        if not p.name: fail("bad path in verify report")
        if p.name in out: fail(f"duplicate basename in verify report: {p.name}")
        out[p.name] = row
    return out


def resolve_day(day: str, vb: dict[str, dict]) -> tuple[Path, Path, Path, dict]:
    l2name = f"{INST}-L2orderbook-400lv-{day}.tar.gz"
    ename = f"{INST}-trades-{day}.zip"
    nname = f"{INST}-trades-{next_day(day)}.zip"
    lp = L2 / day / l2name
    ep = TRADES / ename
    np = TRADES / nname
    for p in (lp, ep, np):
        if not p.exists(): fail(f"missing local source {p}")
        vr = vb.get(p.name)
        if not isinstance(vr, dict): fail(f"source not in verify report: {p.name}")
        if p.stat().st_size != int(vr.get("bytes") or -1): fail(f"size mismatch {p.name}")
    return lp, ep, np, {"l2": vb[l2name], "exact": vb[ename], "neighbor": vb[nname]}


def scan_trades(day: str, exact: Path, neighbor: Path) -> dict:
    lo, hi = day_bounds(day)
    admitted = invalid = inst_bad = side_bad = nonpos = ts_back = id_back = id_gaps = 0
    mins = bytearray(1440); buys = sells = 0
    first_ts = last_ts = prev_ts = prev_id = None
    sources = []
    for p in (exact, neighbor):
        src = {"path": str(p), "bytes": p.stat().st_size, "sha256": sha256_file(p), "rows": 0}
        with zipfile.ZipFile(p, "r") as zf:
            bad = zf.testzip()
            if bad is not None: fail(f"ZIP CRC failure {p.name}: {bad}")
            ms = [m for m in zf.infolist() if not m.is_dir()]
            if len(ms) != 1: fail(f"trade member count {p.name}: {len(ms)}")
            with zf.open(ms[0], "r") as raw:
                rd = csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline=""))
                hdr = [s.strip().lower() for s in (next(rd, None) or [])]
                if hdr != TRADE_HEADER: fail(f"trade header mismatch {p.name}: {hdr}")
                for rn, row in enumerate(rd, start=2):
                    if not row: continue
                    src["rows"] += 1
                    try:
                        if len(row) != 6: raise ValueError("width")
                        inst, tidt, side, price, size, ttxt = row
                        tid = int(tidt); sd = side.strip().lower(); pr = float(price); sz = float(size); ts = parse_ts_ms(ttxt)
                    except Exception:
                        invalid += 1; continue
                    if lo <= ts < hi:
                        admitted += 1
                        if inst.strip() != INST: inst_bad += 1
                        if sd not in {"buy", "sell"}: side_bad += 1
                        if not math.isfinite(pr) or pr <= 0 or not math.isfinite(sz) or sz <= 0: nonpos += 1
                        if first_ts is None: first_ts = ts
                        last_ts = ts
                        mins[(ts - lo)//60_000] = 1
                        if sd == "buy": buys += 1
                        elif sd == "sell": sells += 1
                        if prev_ts is not None and ts < prev_ts: ts_back += 1
                        if prev_id is not None:
                            if tid <= prev_id: id_back += 1
                            elif tid != prev_id + 1: id_gaps += 1
                        prev_ts, prev_id = ts, tid
        sources.append(src)
    return {
        "sources": sources,
        "admitted_rows": admitted,
        "invalid_rows": invalid,
        "instrument_mismatch": inst_bad,
        "side_invalid": side_bad,
        "nonpositive_or_nonfinite": nonpos,
        "timestamp_backwards": ts_back,
        "trade_id_backwards_or_dup": id_back,
        "trade_id_gap_count": id_gaps,
        "minute_buckets": int(sum(mins)),
        "buy_rows": buys,
        "sell_rows": sells,
        "first_ts": first_ts,
        "last_ts": last_ts,
    }


def parse_level(x):
    if not isinstance(x, list) or len(x) != 3: raise ValueError("level shape")
    p = float(x[0]); s = float(x[1]); of = float(x[2]); o = int(round(of))
    if not (math.isfinite(p) and math.isfinite(s) and math.isfinite(of)): raise ValueError("nonfinite")
    if p <= 0 or s < 0 or o < 0 or abs(of-o) > 1e-9: raise ValueError("invalid level")
    if s == 0 and o != 0: raise ValueError("zero-size nonzero orders")
    return p, s, o


def apply(book: dict, prices: list, levels: list[tuple[float,float,int]]) -> int:
    missing_delete = 0
    for p, s, o in levels:
        if s == 0:
            if p not in book:
                missing_delete += 1
            else:
                del book[p]
                i = bisect.bisect_left(prices, p)
                if i < len(prices) and prices[i] == p: prices.pop(i)
        else:
            if p not in book: bisect.insort(prices, p)
            book[p] = (s, o)
    return missing_delete


def scan_l2(day: str, path: Path) -> dict:
    lo, hi = day_bounds(day)
    asks: dict = {}; bids: dict = {}; ap: list = []; bp: list = []
    regular = records = snapshots = updates = malformed = wrong_inst = bad_action = ts_back = 0
    out_day = crossed = empty = delete_missing = best_bad = 0
    mins = bytearray(1440); first_action = None; first_ts = last_ts = prev_ts = None
    gap_gt5 = 0; max_gap = 0; first_gap = last_gap = None
    sha = sha256_file(path)
    with tarfile.open(path, mode="r|gz") as tf:
        for member in tf:
            if not member.isfile(): continue
            regular += 1
            if regular > 1: fail(f"multiple regular L2 members {path.name}")
            f = tf.extractfile(member)
            if f is None: fail(f"cannot extract {path.name}")
            for raw in f:
                if not raw.strip(): continue
                try:
                    r = json.loads(raw)
                except Exception:
                    malformed += 1; continue
                if not isinstance(r, dict): malformed += 1; continue
                records += 1
                if r.get("instId") != INST: wrong_inst += 1
                a = r.get("action")
                if a not in {"snapshot", "update"}: bad_action += 1; continue
                try: ts = int(r.get("ts"))
                except Exception: malformed += 1; continue
                if first_action is None: first_action = a
                if first_ts is None: first_ts = ts
                last_ts = ts
                if prev_ts is not None:
                    if ts < prev_ts: ts_back += 1
                    else:
                        gap = ts - prev_ts; max_gap = max(max_gap, gap)
                        if gap > 5000:
                            gap_gt5 += 1
                            if first_gap is None: first_gap = [prev_ts, ts]
                            last_gap = [prev_ts, ts]
                prev_ts = ts
                if not (lo <= ts < hi): out_day += 1
                else: mins[(ts-lo)//60_000] = 1
                aa = r.get("asks"); bb = r.get("bids")
                if not isinstance(aa, list) or not isinstance(bb, list): malformed += 1; continue
                try:
                    pa = [parse_level(x) for x in aa]; pb = [parse_level(x) for x in bb]
                except Exception:
                    malformed += 1; continue
                if a == "snapshot":
                    snapshots += 1; asks.clear(); bids.clear(); ap.clear(); bp.clear()
                else: updates += 1
                delete_missing += apply(asks, ap, pa); delete_missing += apply(bids, bp, pb)
                if not ap or not bp:
                    empty += 1; continue
                bid = bp[-1]; ask = ap[0]
                if bid >= ask:
                    crossed += 1; continue
                bs, bo = bids[bid]; a_s, ao = asks[ask]
                if bs <= 0 or a_s <= 0 or bo <= 0 or ao <= 0: best_bad += 1
    return {
        "path": str(path), "bytes": path.stat().st_size, "sha256": sha,
        "regular_members": regular, "records": records, "snapshots": snapshots, "updates": updates,
        "first_action": first_action, "first_ts": first_ts, "last_ts": last_ts,
        "minute_buckets": int(sum(mins)), "out_of_day_records": out_day,
        "malformed": malformed, "wrong_instrument": wrong_inst, "invalid_action": bad_action,
        "timestamp_backwards": ts_back, "delete_missing_level": delete_missing,
        "crossed_states": crossed, "empty_states": empty, "best_level_nonpositive_or_zero_orders": best_bad,
        "gap_gt_5000_count": gap_gt5, "max_interrecord_gap_ms": max_gap,
        "first_gap_gt_5000": first_gap, "last_gap_gt_5000": last_gap,
    }


def day_ok(day: str, t: dict, l: dict) -> tuple[bool, list[str]]:
    lo, hi = day_bounds(day); reasons = []
    checks = {
        "trade_rows_positive": t["admitted_rows"] > 0,
        "trade_1440_minutes": t["minute_buckets"] == 1440,
        "trade_schema": t["invalid_rows"] == 0 and t["instrument_mismatch"] == 0 and t["side_invalid"] == 0 and t["nonpositive_or_nonfinite"] == 0,
        "trade_chronology": t["timestamp_backwards"] == 0 and t["trade_id_backwards_or_dup"] == 0 and t["trade_id_gap_count"] == 0,
        "trade_both_sides": t["buy_rows"] > 0 and t["sell_rows"] > 0,
        "trade_bounds": t["first_ts"] is not None and lo <= t["first_ts"] < hi and t["last_ts"] is not None and lo <= t["last_ts"] < hi,
        "l2_member": l["regular_members"] == 1,
        "l2_initial_snapshot": l["first_action"] == "snapshot" and l["snapshots"] >= 1 and l["updates"] >= 1,
        "l2_1440_minutes": l["minute_buckets"] == 1440,
        "l2_bounds": l["out_of_day_records"] == 0 and l["first_ts"] is not None and lo <= l["first_ts"] < hi and l["last_ts"] is not None and lo <= l["last_ts"] < hi,
        "l2_schema": l["malformed"] == 0 and l["wrong_instrument"] == 0 and l["invalid_action"] == 0 and l["timestamp_backwards"] == 0,
        "l2_book_integrity": l["delete_missing_level"] == 0 and l["crossed_states"] == 0 and l["empty_states"] == 0 and l["best_level_nonpositive_or_zero_orders"] == 0,
    }
    for k, v in checks.items():
        if not v: reasons.append(k)
    return all(checks.values()), reasons


def checkpoint_path(day: str) -> Path:
    return CHECKPOINTS / f"{day}.json"


def current_source_hashes(lp: Path, ep: Path, np: Path) -> dict:
    return {"l2_sha256": sha256_file(lp), "exact_trade_sha256": sha256_file(ep), "neighbor_trade_sha256": sha256_file(np)}


def load_checkpoint(day: str, hashes: dict) -> dict | None:
    p = checkpoint_path(day)
    if not p.exists(): return None
    try: x = json.loads(p.read_text(encoding="utf-8"))
    except Exception: return None
    if x.get("stage") != STAGE or x.get("version") != VERSION or x.get("date") != day or x.get("status") != DAY_PASS: return None
    if any(x.get(k) != v for k, v in hashes.items()): return None
    return x


def process_day(day: str, vb: dict[str,dict]) -> dict:
    lp, ep, np, _ = resolve_day(day, vb)
    hashes = current_source_hashes(lp, ep, np)
    cp = load_checkpoint(day, hashes)
    if cp is not None:
        print(f"SEMANTIC {day} REUSED DAY_PASS")
        return cp
    print(f"SEMANTIC {day}: scan trades")
    t = scan_trades(day, ep, np)
    print(f"SEMANTIC {day}: replay L2")
    l = scan_l2(day, lp)
    ok, reasons = day_ok(day, t, l)
    row = {"stage": STAGE, "version": VERSION, "date": day, "status": DAY_PASS if ok else "DAY_REVIEW", **hashes, "trade": t, "l2": l, "review_reasons": reasons}
    atomic_json(checkpoint_path(day), row)
    print(f"SEMANTIC {day} {'PASS' if ok else 'REVIEW'} trades={t['admitted_rows']} l2_records={l['records']} gaps_gt5={l['gap_gt_5000_count']}")
    return row


def firewall() -> dict:
    return {
        "hypothetical_maker_orders_created": False,
        "fill_simulation_calculated": False,
        "spread_capture_calculated": False,
        "markout_calculated": False,
        "fees_calculated": False,
        "inventory_pnl_calculated": False,
        "profitability_calculated": False,
        "tfi_used": False,
        "confirmation_body_accessed": False,
        "q2_accessed": False,
        "validation_or_final_accessed": False,
    }


def preflight() -> None:
    v = load_verify(); vb = verified_by_basename(v)
    for day in DAYS: resolve_day(day, vb)
    print("E008_DISCOVERY_SEMANTIC_PREFLIGHT_PASS")
    print("days =", len(DAYS))
    print("verified acquisition files =", len(v.get("files") or []))
    print("maker orders/fills/PnL calculated = False")
    print("Confirmation/Q2/Validation/Final = CLOSED")


def run() -> int:
    v = load_verify(); vb = verified_by_basename(v); rows = []
    for day in DAYS:
        try: rows.append(process_day(day, vb))
        except Exception as e:
            rows.append({"stage": STAGE, "version": VERSION, "date": day, "status": "DAY_ERROR", "error": repr(e)})
            print("SEMANTIC REVIEW", day, repr(e))
    passed = len(rows) == len(DAYS) and all(x.get("status") == DAY_PASS for x in rows)
    status = PASS if passed else REVIEW
    rep = {"stage": STAGE, "version": VERSION, "status": status, "days": rows, **firewall()}
    atomic_json(REPORT, rep)
    print(status)
    print("qualified_day_count =", sum(1 for x in rows if x.get("status") == DAY_PASS), "/", len(DAYS))
    print("maker orders/fills/spread_capture/markout/fees/inventory_PnL/profitability calculated = False")
    print("Confirmation/Q2/Validation/Final = CLOSED")
    print("report =", REPORT)
    return 0 if passed else 2


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("mode", choices=("preflight", "run")); a = ap.parse_args()
    if a.mode == "preflight": preflight(); return 0
    return run()


if __name__ == "__main__": raise SystemExit(main())
