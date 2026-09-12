"""SC001-E002 OKX Q1 one-day midquote falsification pilot.

Uses the already-frozen 5s OKX trade-flow imbalance on 2024-01-05 and
measures future response with causally sampled replayed L2 midquote.
No execution P&L, no Q2, no formal Validation/Final.
Standard library only; Android/Pydroid compatible.
"""
from __future__ import annotations

import bisect
import csv
import hashlib
import json
import math
import os
import shutil
import statistics
import tarfile
import zipfile
from array import array
from datetime import datetime, timezone
from pathlib import Path

STAGE = "SC001-E002-OKX-MIDQUOTE-PILOT"
VERSION = "0.1"
PROTOCOL_COMMIT = "4408d09e9a746804cfe2f65d01c0917100196c03"
DATE = "2024-01-05"
INST = "BTC-USDT-SWAP"
GRID_MS = 5_000
LOOKBACK_MS = 5_000
HORIZON_MS = 5_000
LATENCIES_MS = (100, 250, 500)
PRIMARY_LATENCY_MS = 100
EXPECTED_DECISIONS = 17_109
EXPECTED_L2_BYTES = 500_060_536
EXPECTED_L2_SHA256 = "7279d6b87021ea64982449f5a7c86e298a5c46c1c107ac41a368debeaaf5929a"
EXPECTED_HEADER = ["instrument_name", "trade_id", "side", "price", "size", "created_time"]
MIN_FREE_RESERVE_BYTES = 4_000_000_000
WORKSPACE_CAP_BYTES = 100_000_000

DOWNLOAD = Path("/storage/emulated/0/Download")
TRADE_EXACT = DOWNLOAD / "SC001_DATA_Q006_OKX_TRADES" / "archives" / "BTC-USDT-SWAP-trades-2024-01-05.zip"
TRADE_NEIGHBOR = DOWNLOAD / "SC001_DATA_Q006R_OKX_UTC_STITCH" / "neighbor_archives" / "BTC-USDT-SWAP-trades-2024-01-06.zip"
L2_ARCHIVE = DOWNLOAD / "SC001_DATA_Q008_OKX_L2_PILOT" / "BTC-USDT-SWAP-L2orderbook-400lv-2024-01-05.tar.gz"
Q006R_REPORT = DOWNLOAD / "SC001_DATA_Q006R_OKX_UTC_STITCH" / "sc001_data_q006r_okx_utc_stitch_report.json"
Q008_REPORT = DOWNLOAD / "SC001_DATA_Q008_OKX_L2_PILOT" / "sc001_data_q008_okx_l2_pilot_report.json"
OKX_REPLICATION_REPORT = DOWNLOAD / "SC001_E002_OKX_Q1_REPLICATION" / "sc001_e002_okx_q1_replication_report.json"

WORKSPACE = DOWNLOAD / "SC001_E002_OKX_MIDQUOTE_PILOT"
REPORT = WORKSPACE / "sc001_e002_okx_midquote_pilot_report.json"
METRICS = WORKSPACE / "sc001_e002_okx_midquote_pilot_metrics.csv"
SUMMARY = WORKSPACE / "sc001_e002_okx_midquote_pilot_summary.md"
SAFETY = WORKSPACE / "sc001_e002_okx_midquote_pilot_final_safety.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def free_bytes() -> int:
    return shutil.disk_usage(DOWNLOAD).free


def safety_check() -> None:
    if dir_size(WORKSPACE) > WORKSPACE_CAP_BYTES:
        raise RuntimeError("midquote pilot workspace cap exceeded")
    if free_bytes() < MIN_FREE_RESERVE_BYTES:
        raise RuntimeError("minimum free-space reserve violated")


def atomic_text(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        f.write(text)
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


def atomic_json(path: Path, obj) -> None:
    atomic_text(path, json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def percentile(values, p: float):
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return float(xs[0])
    pos = (len(xs) - 1) * p
    lo = int(math.floor(pos)); hi = int(math.ceil(pos))
    if lo == hi:
        return float(xs[lo])
    w = pos - lo
    return float(xs[lo] * (1.0 - w) + xs[hi] * w)


def rankdata(values):
    n = len(values)
    order = sorted(range(n), key=values.__getitem__)
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i + 1
        v = values[order[i]]
        while j < n and values[order[j]] == v:
            j += 1
        r = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[order[k]] = r
        i = j
    return ranks


def pearson(x, y):
    n = len(x)
    if n < 3:
        return None
    mx = sum(x) / n; my = sum(y) / n
    sxx = syy = sxy = 0.0
    for a, b in zip(x, y):
        dx = a - mx; dy = b - my
        sxx += dx * dx; syy += dy * dy; sxy += dx * dy
    if sxx <= 0 or syy <= 0:
        return 0.0
    return sxy / math.sqrt(sxx * syy)


def spearman(x, y):
    return pearson(rankdata(x), rankdata(y)) if len(x) == len(y) and len(x) >= 3 else None


def extreme_decile(scores, rets):
    n = len(scores)
    order = sorted(range(n), key=scores.__getitem__)
    m = max(1, n // 10)
    bot = order[:m]; top = order[-m:]
    bm = sum(rets[i] for i in bot) / m
    tm = sum(rets[i] for i in top) / m
    hits = sum(1 for i in top if rets[i] > 0) + sum(1 for i in bot if rets[i] < 0)
    return {
        "n_each": m,
        "bottom_mean_bps": bm,
        "top_mean_bps": tm,
        "spread_bps": tm - bm,
        "directional_hit_rate": hits / (2 * m),
    }


def verify_parents() -> dict:
    for p in (Q006R_REPORT, Q008_REPORT, OKX_REPLICATION_REPORT):
        if not p.exists():
            raise RuntimeError(f"missing required parent report: {p}")
    q6 = json.loads(Q006R_REPORT.read_text(encoding="utf-8"))
    q8 = json.loads(Q008_REPORT.read_text(encoding="utf-8"))
    rep = json.loads(OKX_REPLICATION_REPORT.read_text(encoding="utf-8"))
    if q6.get("overall_status") != "PASS":
        raise RuntimeError("Q006R parent is not PASS")
    if q8.get("overall_status") != "FULL_DAY_PASS":
        raise RuntimeError("Q008 parent is not FULL_DAY_PASS")
    if rep.get("verdict") != "OKX_REPLICATION_PASS":
        raise RuntimeError("OKX transaction-price replication parent is not PASS")
    if rep.get("q2_okx_accessed") is not False or rep.get("validation_or_final_accessed") is not False:
        raise RuntimeError("parent firewall mismatch")
    if not L2_ARCHIVE.exists() or L2_ARCHIVE.stat().st_size != EXPECTED_L2_BYTES:
        raise RuntimeError("Q008 L2 archive missing/wrong size")
    digest = sha256_file(L2_ARCHIVE)
    if digest != EXPECTED_L2_SHA256:
        raise RuntimeError("Q008 L2 archive SHA mismatch")
    return {
        "q006r_status": q6.get("overall_status"),
        "q008_status": q8.get("overall_status"),
        "okx_replication_verdict": rep.get("verdict"),
        "l2_sha256": digest,
    }


def read_trade_archive(path: Path, day_start: int, day_end: int, signed, total, timestamps, prices, stats):
    if not path.exists():
        raise RuntimeError(f"missing trade archive: {path}")
    with zipfile.ZipFile(path, "r") as zf:
        members = [x for x in zf.infolist() if not x.is_dir()]
        if len(members) != 1:
            raise RuntimeError("unexpected trade ZIP member count")
        with zf.open(members[0], "r") as raw:
            reader = csv.reader((line.decode("utf-8") for line in raw))
            header = next(reader)
            if header != EXPECTED_HEADER:
                raise RuntimeError(f"unexpected trade header: {header}")
            for row in reader:
                if not row:
                    continue
                stats["source_rows"] += 1
                if len(row) != 6:
                    stats["invalid_rows"] += 1; continue
                try:
                    inst, _, side, ptxt, stxt, ttxt = row
                    if inst != INST:
                        stats["instrument_mismatch"] += 1; continue
                    ts = int(ttxt)
                    price = float(ptxt); size = float(stxt)
                    if not (math.isfinite(price) and math.isfinite(size) and price > 0 and size > 0):
                        raise ValueError("invalid price/size")
                    if side not in {"buy", "sell"}:
                        raise ValueError("invalid side")
                except Exception:
                    stats["invalid_rows"] += 1; continue
                if day_start <= ts < day_end:
                    bucket = (ts - day_start) // GRID_MS
                    notional = price * size
                    sgn = 1.0 if side == "buy" else -1.0
                    signed[bucket] += sgn * notional
                    total[bucket] += notional
                    timestamps.append(ts)
                    prices.append(price)
                    stats["admitted_rows"] += 1


def build_scores():
    day_start = int(datetime.fromisoformat(DATE).replace(tzinfo=timezone.utc).timestamp() * 1000)
    day_end = day_start + 86_400_000
    n_buckets = 86_400_000 // GRID_MS
    signed = array("d", [0.0]) * n_buckets
    total = array("d", [0.0]) * n_buckets
    timestamps = array("q")
    prices = array("d")
    stats = {"source_rows": 0, "admitted_rows": 0, "invalid_rows": 0, "instrument_mismatch": 0}
    read_trade_archive(TRADE_EXACT, day_start, day_end, signed, total, timestamps, prices, stats)
    read_trade_archive(TRADE_NEIGHBOR, day_start, day_end, signed, total, timestamps, prices, stats)
    if stats["invalid_rows"] or stats["instrument_mismatch"]:
        raise RuntimeError(f"trade parse integrity failure: {stats}")

    scores = []
    decisions = []
    for k in range(n_buckets - 2):
        if total[k] <= 0:
            continue
        t = day_start + (k + 1) * GRID_MS
        scores.append(signed[k] / total[k])
        decisions.append(t)
    if len(scores) != EXPECTED_DECISIONS:
        raise RuntimeError(f"decision-count mismatch: {len(scores)} != {EXPECTED_DECISIONS}")
    stats["decision_count"] = len(scores)
    return scores, decisions, stats, day_start, day_end


def parse_level(x):
    if not isinstance(x, list) or len(x) != 3:
        raise ValueError("level shape")
    px = float(x[0]); sz = float(x[1]); orders_f = float(x[2])
    if not (math.isfinite(px) and math.isfinite(sz) and math.isfinite(orders_f)):
        raise ValueError("nonfinite level")
    orders = int(round(orders_f))
    if px <= 0 or sz < 0 or orders < 0 or abs(orders_f - orders) > 1e-9:
        raise ValueError("invalid level")
    return px, sz, orders


def book_apply(book, prices, levels):
    for px, sz, orders in levels:
        if sz == 0:
            if px in book:
                del book[px]
                i = bisect.bisect_left(prices, px)
                if i < len(prices) and prices[i] == px:
                    prices.pop(i)
        else:
            if px not in book:
                bisect.insort(prices, px)
            book[px] = (sz, orders)


def replay_and_sample(decisions, day_end):
    n = len(decisions)
    samples = {
        lat: {
            "entry": [None] * n, "exit": [None] * n,
            "entry_age": [None] * n, "exit_age": [None] * n,
        }
        for lat in LATENCIES_MS
    }
    events = []
    seq = 0
    for i, t in enumerate(decisions):
        for lat in LATENCIES_MS:
            events.append((t + lat, seq, i, lat, "entry")); seq += 1
            events.append((t + lat + HORIZON_MS, seq, i, lat, "exit")); seq += 1
    events.sort()
    ei = 0

    asks = {}; bids = {}; ask_prices = []; bid_prices = []
    current_mid = None
    state_ts = None
    last_ts = None
    records = 0
    snapshots = updates = 0
    integrity_errors = 0

    def fill_before(next_ts):
        nonlocal ei
        while ei < len(events) and events[ei][0] < next_ts:
            target, _, idx, lat, kind = events[ei]
            if current_mid is not None and state_ts is not None:
                samples[lat][kind][idx] = current_mid
                samples[lat][kind + "_age"][idx] = target - state_ts
            ei += 1

    with tarfile.open(L2_ARCHIVE, mode="r|gz") as tf:
        regular = 0
        for member in tf:
            if not member.isfile():
                continue
            regular += 1
            if regular != 1:
                raise RuntimeError("unexpected extra regular member in L2 archive")
            f = tf.extractfile(member)
            if f is None:
                raise RuntimeError("could not extract L2 stream")
            for raw in f:
                if not raw.strip():
                    continue
                rec = json.loads(raw)
                records += 1
                if records % 1_000_000 == 0:
                    print(f"L2 replay progress: {records:,} records")
                if rec.get("instId") != INST or rec.get("action") not in {"snapshot", "update"}:
                    integrity_errors += 1; continue
                ts = int(rec["ts"])
                if last_ts is not None and ts < last_ts:
                    integrity_errors += 1
                if last_ts is not None and ts > last_ts:
                    fill_before(ts)
                last_ts = ts
                asks_raw = rec.get("asks"); bids_raw = rec.get("bids")
                if not isinstance(asks_raw, list) or not isinstance(bids_raw, list):
                    integrity_errors += 1; continue
                pa = [parse_level(x) for x in asks_raw]
                pb = [parse_level(x) for x in bids_raw]
                if rec["action"] == "snapshot":
                    snapshots += 1
                    asks.clear(); bids.clear(); ask_prices.clear(); bid_prices.clear()
                else:
                    updates += 1
                book_apply(asks, ask_prices, pa)
                book_apply(bids, bid_prices, pb)
                if not ask_prices or not bid_prices or bid_prices[-1] >= ask_prices[0]:
                    integrity_errors += 1
                    current_mid = None
                else:
                    current_mid = (bid_prices[-1] + ask_prices[0]) / 2.0
                    state_ts = ts
        if current_mid is not None and state_ts is not None:
            while ei < len(events) and events[ei][0] <= day_end:
                target, _, idx, lat, kind = events[ei]
                samples[lat][kind][idx] = current_mid
                samples[lat][kind + "_age"][idx] = target - state_ts
                ei += 1

    if integrity_errors:
        raise RuntimeError(f"L2 replay integrity errors: {integrity_errors}")
    return samples, {"records": records, "snapshots": snapshots, "updates": updates, "unfilled_targets": len(events) - ei}


def summarize(scores, samples):
    out = {"latencies": {}}
    for lat in LATENCIES_MS:
        s = samples[lat]
        valid_scores = []
        rets = []
        entry_age = []
        exit_age = []
        for i, score in enumerate(scores):
            a = s["entry"][i]; b = s["exit"][i]
            ea = s["entry_age"][i]; xa = s["exit_age"][i]
            if a is None or b is None or ea is None or xa is None or a <= 0 or b <= 0:
                continue
            valid_scores.append(score)
            rets.append(math.log(b / a) * 10_000.0)
            entry_age.append(ea); exit_age.append(xa)
        ext = extreme_decile(valid_scores, rets)
        out["latencies"][str(lat)] = {
            "n": len(valid_scores),
            "spearman": spearman(valid_scores, rets),
            "mean_return_bps": sum(rets) / len(rets),
            "median_return_bps": statistics.median(rets),
            "extreme_decile": ext,
            "entry_book_state_age_ms": {
                "median": statistics.median(entry_age),
                "p95": percentile(entry_age, 0.95),
                "p99": percentile(entry_age, 0.99),
                "max": max(entry_age),
            },
            "exit_book_state_age_ms": {
                "median": statistics.median(exit_age),
                "p95": percentile(exit_age, 0.95),
                "p99": percentile(exit_age, 0.99),
                "max": max(exit_age),
            },
        }
    p = out["latencies"][str(PRIMARY_LATENCY_MS)]
    rho = p["spearman"]
    spread = p["extreme_decile"]["spread_bps"]
    if p["n"] != EXPECTED_DECISIONS:
        verdict = "ERROR_REVIEW"
    elif rho > 0 and spread > 0:
        verdict = "MIDQUOTE_PILOT_PASS"
    elif rho > 0 or spread > 0:
        verdict = "MIDQUOTE_PILOT_WEAK"
    else:
        verdict = "MIDQUOTE_PILOT_FAIL"
    out["verdict"] = verdict
    return out


def write_outputs(report):
    atomic_json(REPORT, report)
    rows = []
    for lat in LATENCIES_MS:
        m = report["summary"]["latencies"][str(lat)]
        rows.append({
            "latency_ms": lat,
            "n": m["n"],
            "spearman": m["spearman"],
            "extreme_spread_bps": m["extreme_decile"]["spread_bps"],
            "directional_hit_rate": m["extreme_decile"]["directional_hit_rate"],
            "entry_age_median_ms": m["entry_book_state_age_ms"]["median"],
            "entry_age_p95_ms": m["entry_book_state_age_ms"]["p95"],
            "entry_age_p99_ms": m["entry_book_state_age_ms"]["p99"],
            "entry_age_max_ms": m["entry_book_state_age_ms"]["max"],
            "exit_age_median_ms": m["exit_book_state_age_ms"]["median"],
            "exit_age_p95_ms": m["exit_book_state_age_ms"]["p95"],
            "exit_age_p99_ms": m["exit_book_state_age_ms"]["p99"],
            "exit_age_max_ms": m["exit_book_state_age_ms"]["max"],
        })
    header = list(rows[0].keys())
    text = ",".join(header) + "\n" + "\n".join(",".join(str(r[h]) for h in header) for r in rows) + "\n"
    atomic_text(METRICS, text)

    p = report["summary"]["latencies"]["100"]
    lines = [
        "# SC001-E002 OKX Midquote Falsification Pilot",
        "",
        f"- Verdict: `{report['summary']['verdict']}`",
        f"- Date: `{DATE}`",
        f"- Valid decisions: {p['n']}",
        f"- 100ms Spearman: {p['spearman']}",
        f"- 100ms extreme spread bps: {p['extreme_decile']['spread_bps']}",
        f"- 100ms entry book-state age median/p95/p99/max ms: {p['entry_book_state_age_ms']['median']} / {p['entry_book_state_age_ms']['p95']} / {p['entry_book_state_age_ms']['p99']} / {p['entry_book_state_age_ms']['max']}",
        "",
        "## Boundary",
        "Midquote predictability only. No bid/ask execution, fee, depth, capital or strategy P&L claim.",
        "Q2 OKX, formal Validation and Final remain unopened.",
    ]
    atomic_text(SUMMARY, "\n".join(lines) + "\n")
    atomic_json(SAFETY, {
        "stage": STAGE,
        "workspace_bytes_after_outputs": dir_size(WORKSPACE),
        "workspace_cap_bytes": WORKSPACE_CAP_BYTES,
        "free_bytes_after_outputs": free_bytes(),
        "minimum_free_reserve_bytes": MIN_FREE_RESERVE_BYTES,
        "network_market_data_bytes_read": 0,
        "strategy_pnl_calculated": False,
        "execution_profitability_calculated": False,
        "q2_okx_accessed": False,
        "validation_or_final_accessed": False,
    })


def main():
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    safety_check()
    started = now_iso()
    print("=" * 78)
    print("SC001-E002 OKX MIDQUOTE FALSIFICATION PILOT v0.1")
    print("Fixed date: 2024-01-05 | no market-data download")
    print("This full L2 replay can take a while; progress prints every 1,000,000 records.")
    print("=" * 78)
    parents = verify_parents()
    print("Parent/data checks: PASS")
    scores, decisions, trade_stats, _, day_end = build_scores()
    print(f"Frozen TFI decisions: {len(scores):,}")
    print("Starting full L2 replay and causal midquote sampling...")
    samples, replay_stats = replay_and_sample(decisions, day_end)
    summary = summarize(scores, samples)
    report = {
        "stage": STAGE,
        "version": VERSION,
        "protocol_commit": PROTOCOL_COMMIT,
        "started_at_utc": started,
        "finished_at_utc": now_iso(),
        "date": DATE,
        "parents": parents,
        "trade_stats": trade_stats,
        "replay_stats": replay_stats,
        "summary": summary,
        "verdict": summary["verdict"],
        "strategy_features_calculated": True,
        "midquote_response_calculated": True,
        "strategy_pnl_calculated": False,
        "execution_profitability_calculated": False,
        "q2_okx_accessed": False,
        "validation_or_final_accessed": False,
    }
    write_outputs(report)
    safety_check()
    print("COMPLETE:", summary["verdict"])
    print("Outputs:", WORKSPACE)


if __name__ == "__main__":
    main()
