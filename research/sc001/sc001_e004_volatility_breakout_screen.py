"""SC001-E004 causal volatility-compression -> breakout/expansion screen.

Implements the frozen E004 v0.1 trade-tape protocol on already-qualified
March-2024 OKX BTC-USDT-SWAP archives.

Discovery and confirmation are separate modes. Confirmation is fail-closed
behind a terminal Discovery PASS produced by this exact engine SHA.

No L2, no Q2, no formal Validation/Final, no E002 TFI, no E003 FLOW_IMPULSE.
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
import sys
import zipfile
from array import array
from collections import deque
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

STAGE = "SC001-E004-VOLATILITY-COMPRESSION-BREAKOUT"
VERSION = "0.1"
PROTOCOL = "docs/research/sc001-e004-volatility-compression-breakout-protocol-v0.1.md"
PREFLIGHT_SPEC = "docs/research/sc001-e004-implementation-preflight-v0.1.md"
IMPLEMENTATION_FREEZE = "docs/research/sc001-e004-implementation-freeze-v0.1.md"

INST = "BTC-USDT-SWAP"
EXPECTED_HEADER = ["instrument_name", "trade_id", "side", "price", "size", "created_time"]

SECOND_MS = 1_000
BLOCK_SECONDS = 300
BLOCK_MS = BLOCK_SECONDS * SECOND_MS
SECONDS_PER_DAY = 86_400
BLOCKS_PER_DAY = SECONDS_PER_DAY // BLOCK_SECONDS
MIN_VALID_SECONDS = 270
ROLLING_N = 72

DISCOVERY_DAYS = tuple(f"2024-03-{d:02d}" for d in range(1, 21))
CONFIRM_DAYS = tuple(f"2024-03-{d:02d}" for d in range(21, 31))
TARGET_DAYS = DISCOVERY_DAYS + CONFIRM_DAYS
REQUIRED_ARCHIVE_DAYS = tuple(f"2024-03-{d:02d}" for d in range(1, 32))

DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
SOURCE_ROOT = DATA_ROOT / "SC001_E003_OKX_MARCH_TRADES"
ARCHIVES = SOURCE_ROOT / "archives"
SOURCE_REPORT = SOURCE_ROOT / "sc001_e003_okx_march_trade_stage_report.json"

WORKSPACE = DATA_ROOT / "SC001_E004_VOLATILITY_BREAKOUT"
DISCOVERY_ROOT = WORKSPACE / "discovery"
CONFIRM_ROOT = WORKSPACE / "confirmation"
DISCOVERY_REPORT = DISCOVERY_ROOT / "sc001_e004_discovery_report.json"
DISCOVERY_SUMMARY = DISCOVERY_ROOT / "sc001_e004_discovery_summary.md"
CONFIRM_REPORT = CONFIRM_ROOT / "sc001_e004_confirmation_report.json"
CONFIRM_SUMMARY = CONFIRM_ROOT / "sc001_e004_confirmation_summary.md"

# name, compression quantile, latency ms, horizon ms, role
SCENARIOS = (
    ("q20_250ms_600s", 0.20, 250, 600_000, "primary"),
    ("q20_500ms_600s", 0.20, 500, 600_000, "stress_latency"),
    ("q15_250ms_600s", 0.15, 250, 600_000, "diagnostic_compression"),
    ("q25_250ms_600s", 0.25, 250, 600_000, "diagnostic_compression"),
    ("q20_250ms_300s", 0.20, 250, 300_000, "diagnostic_horizon"),
    ("q20_250ms_900s", 0.20, 250, 900_000, "diagnostic_horizon"),
    ("q20_1000ms_600s", 0.20, 1000, 600_000, "diagnostic_latency"),
)
PRIMARY_NAME = "q20_250ms_600s"
STRESS_NAME = "q20_500ms_600s"


def fail(msg: str) -> None:
    raise RuntimeError(msg)


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


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing required JSON: {path}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        fail(f"JSON object expected: {path}")
    return obj


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def script_sha() -> str:
    return sha256_file(Path(__file__).resolve())


def parse_ts_ms(text: str) -> int:
    v = int(text.strip())
    av = abs(v)
    if av >= 10**17:
        return v // 1_000_000
    if av >= 10**14:
        return v // 1_000
    if av >= 10**11:
        return v
    if av >= 10**9:
        return v * 1000
    fail(f"unresolved timestamp scale: {text!r}")


def utc_bounds(date_text: str) -> tuple[int, int]:
    d = datetime.strptime(date_text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    lo = int(d.timestamp() * 1000)
    return lo, lo + 86_400_000


def next_day(date_text: str) -> str:
    return (datetime.strptime(date_text, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")


def nearest_rank(sorted_xs: list[float], q: float, n_expected: int = ROLLING_N) -> float:
    if len(sorted_xs) != n_expected:
        fail(f"nearest-rank window length mismatch: {len(sorted_xs)} != {n_expected}")
    idx = math.ceil(q * n_expected) - 1
    return float(sorted_xs[idx])


def add_sorted(q: deque[float], xs: list[float], value: float, maxlen: int = ROLLING_N) -> None:
    bisect.insort(xs, value)
    q.append(value)
    if len(q) > maxlen:
        old = q.popleft()
        i = bisect.bisect_left(xs, old)
        if i >= len(xs) or xs[i] != old:
            fail("rolling sorted state corruption")
        xs.pop(i)


def source_manifest() -> dict[str, dict]:
    rep = load_json(SOURCE_REPORT)
    if rep.get("stage") != "SC001-E003-OKX-MARCH-TRADE-STAGE" or rep.get("status") != "PASS":
        fail("March source stage is not PASS")
    if rep.get("q2_market_data_body_accessed") is not False or rep.get("validation_or_final_accessed") is not False:
        fail("source-stage firewall mismatch")
    if rep.get("alpha_calculated") is not False or rep.get("pnl_calculated") is not False:
        fail("source-stage alpha/P&L firewall mismatch")
    rows = rep.get("archives") or []
    if len(rows) != 31:
        fail(f"source manifest archive count mismatch: {len(rows)}")
    out: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict):
            fail("source manifest row type mismatch")
        d = row.get("date")
        fn = row.get("filename")
        size = row.get("bytes")
        digest = row.get("sha256")
        if d not in REQUIRED_ARCHIVE_DAYS:
            fail(f"unexpected source archive date: {d}")
        if fn != f"{INST}-trades-{d}.zip":
            fail(f"bad source filename for {d}: {fn}")
        if not isinstance(size, int) or size <= 0 or not isinstance(digest, str) or len(digest) != 64:
            fail(f"bad source identity for {d}")
        out[d] = {"path": ARCHIVES / fn, "filename": fn, "bytes": size, "sha256": digest}
    if set(out) != set(REQUIRED_ARCHIVE_DAYS):
        fail("source date set mismatch")
    return out


def verify_sources(manifest: dict[str, dict]) -> None:
    for d in REQUIRED_ARCHIVE_DAYS:
        x = manifest[d]
        p = Path(x["path"])
        if not p.exists() or p.stat().st_size != x["bytes"]:
            fail(f"source size/existence mismatch: {p}")
        if sha256_file(p) != x["sha256"]:
            fail(f"source SHA mismatch: {p.name}")
        with zipfile.ZipFile(p, "r") as zf:
            bad = zf.testzip()
            if bad is not None:
                fail(f"ZIP CRC failure {p.name}: {bad}")
            members = [m for m in zf.infolist() if not m.is_dir()]
            if len(members) != 1:
                fail(f"unexpected ZIP member count {p.name}: {len(members)}")
        print(f"SOURCE PASS {d} {p.name}", flush=True)


def read_archive_for_day(
    path: Path,
    day_start: int,
    day_end: int,
    second_num: array,
    second_den: array,
    timestamps: array,
    prices: array,
    stats: dict,
    last_state: dict,
) -> None:
    with zipfile.ZipFile(path, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            fail(f"ZIP CRC failure {path.name}: {bad}")
        members = [m for m in zf.infolist() if not m.is_dir()]
        if len(members) != 1:
            fail(f"unexpected ZIP member count {path.name}: {len(members)}")
        with zf.open(members[0], "r") as raw:
            reader = csv.reader((line.decode("utf-8") for line in raw))
            if next(reader, None) != EXPECTED_HEADER:
                fail(f"trade header mismatch in {path.name}")
            source_last_ts = None
            source_last_id = None
            for row in reader:
                if not row:
                    continue
                stats["source_rows"] += 1
                if len(row) != 6:
                    fail(f"malformed trade row in {path.name}")
                inst, tid_txt, side, ptxt, stxt, ttxt = row
                if inst != INST:
                    stats["other_instrument_rows"] += 1
                    continue
                try:
                    ts = parse_ts_ms(ttxt)
                    tid = int(tid_txt)
                    px = float(ptxt)
                    sz = float(stxt)
                except Exception as exc:
                    raise RuntimeError(f"invalid target trade row in {path.name}: {row!r}") from exc
                if side not in {"buy", "sell"} or not math.isfinite(px) or not math.isfinite(sz) or px <= 0 or sz <= 0:
                    fail(f"invalid target trade values in {path.name}")
                if source_last_ts is not None and ts < source_last_ts:
                    fail(f"source timestamp reversal in {path.name}")
                if source_last_id is not None and tid <= source_last_id:
                    fail(f"source trade-id duplicate/backward in {path.name}")
                source_last_ts = ts
                source_last_id = tid

                if day_start <= ts < day_end:
                    prev_ts = last_state.get("ts")
                    prev_id = last_state.get("id")
                    if prev_ts is not None and ts < prev_ts:
                        fail("stitched target timestamp reversal")
                    if prev_id is not None:
                        if tid <= prev_id:
                            fail("stitched target trade-id duplicate/backward")
                        if tid != prev_id + 1:
                            fail(f"stitched target trade-id gap: {prev_id}->{tid}")
                    last_state["ts"] = ts
                    last_state["id"] = tid
                    sidx = (ts - day_start) // SECOND_MS
                    second_num[sidx] += px * sz
                    second_den[sidx] += sz
                    timestamps.append(ts)
                    prices.append(px)
                    stats["admitted_rows"] += 1


def build_day_stream(date_text: str, manifest: dict[str, dict]) -> dict:
    if date_text not in TARGET_DAYS:
        fail(f"unauthorized E004 target day: {date_text}")
    day_start, day_end = utc_bounds(date_text)
    second_num = array("d", [0.0]) * SECONDS_PER_DAY
    second_den = array("d", [0.0]) * SECONDS_PER_DAY
    timestamps = array("q")
    prices = array("d")
    stats = {"source_rows": 0, "other_instrument_rows": 0, "admitted_rows": 0}
    state = {"ts": None, "id": None}

    read_archive_for_day(
        Path(manifest[date_text]["path"]), day_start, day_end,
        second_num, second_den, timestamps, prices, stats, state
    )
    read_archive_for_day(
        Path(manifest[next_day(date_text)]["path"]), day_start, day_end,
        second_num, second_den, timestamps, prices, stats, state
    )

    if stats["admitted_rows"] <= 0:
        fail(f"no admitted rows for {date_text}")
    minute_count = len(set((int(ts) - day_start) // 60_000 for ts in timestamps))
    if minute_count != 1440:
        fail(f"UTC minute coverage failure {date_text}: {minute_count}/1440")

    second_vwap = array("d", [math.nan]) * SECONDS_PER_DAY
    valid_seconds = 0
    for i in range(SECONDS_PER_DAY):
        den = float(second_den[i])
        if den > 0:
            v = float(second_num[i]) / den
            if not math.isfinite(v) or v <= 0:
                fail(f"non-finite/non-positive second VWAP {date_text} idx={i}")
            second_vwap[i] = v
            valid_seconds += 1

    return {
        "date": date_text,
        "day_start": day_start,
        "day_end": day_end,
        "timestamps": timestamps,
        "prices": prices,
        "second_vwap": second_vwap,
        "stats": stats,
        "valid_seconds": valid_seconds,
        "minute_count": minute_count,
    }


def build_blocks(stream: dict) -> list[dict]:
    vwaps: array = stream["second_vwap"]
    day_start = int(stream["day_start"])
    blocks: list[dict] = []
    for k in range(BLOCKS_PER_DAY):
        lo = k * BLOCK_SECONDS
        hi = lo + BLOCK_SECONDS
        vals = [float(vwaps[i]) for i in range(lo, hi) if math.isfinite(float(vwaps[i]))]
        valid_count = len(vals)
        row = {
            "k": k,
            "start_ts": day_start + lo * SECOND_MS,
            "end_ts": day_start + hi * SECOND_MS,
            "valid_seconds": valid_count,
            "valid": valid_count >= MIN_VALID_SECONDS,
            "high": None,
            "low": None,
            "range_bps": None,
        }
        if row["valid"]:
            high = max(vals)
            low = min(vals)
            if not (math.isfinite(high) and math.isfinite(low) and high > 0 and low > 0 and high >= low):
                fail("bad five-minute extrema")
            r = 10_000.0 * math.log(high / low)
            if not math.isfinite(r) or r < 0:
                fail("bad five-minute log range")
            row.update({"high": high, "low": low, "range_bps": r})
        blocks.append(row)
    return blocks


def compression_flags(blocks: list[dict], q: float) -> list[dict | None]:
    if q not in {0.15, 0.20, 0.25}:
        fail(f"unauthorized compression q: {q}")
    rq: deque[float] = deque()
    rs: list[float] = []
    out: list[dict | None] = [None] * len(blocks)
    for b in blocks:
        if not b["valid"]:
            continue
        r = float(b["range_bps"])
        if len(rq) == ROLLING_N:
            thr = nearest_rank(rs, q)
            out[b["k"]] = {
                "threshold_bps": thr,
                "compressed": r < thr,
                "range_bps": r,
            }
        add_sorted(rq, rs, r)
    return out


def potential_breakouts(stream: dict, blocks: list[dict], q: float) -> list[dict]:
    flags = compression_flags(blocks, q)
    vwaps: array = stream["second_vwap"]
    day_start = int(stream["day_start"])
    episodes: list[dict] = []
    for k, info in enumerate(flags):
        if info is None or not info["compressed"] or k + 1 >= BLOCKS_PER_DAY:
            continue
        b = blocks[k]
        h = float(b["high"])
        l = float(b["low"])
        lo = (k + 1) * BLOCK_SECONDS
        hi = lo + BLOCK_SECONDS
        found = None
        for sidx in range(lo, hi):
            p = float(vwaps[sidx])
            if not math.isfinite(p):
                continue
            if p > h:
                found = (sidx, p, 1)
                break
            if p < l:
                found = (sidx, p, -1)
                break
        if found is None:
            continue
        sidx, p, direction = found
        decision_ts = day_start + (sidx + 1) * SECOND_MS
        episodes.append({
            "arm_ts": int(b["end_ts"]),
            "arm_end_ts": int(b["end_ts"]) + BLOCK_MS,
            "decision_ts": decision_ts,
            "direction": direction,
            "confirm_vwap": p,
            "box_high": h,
            "box_low": l,
            "compression_range_bps": float(info["range_bps"]),
            "compression_threshold_bps": float(info["threshold_bps"]),
            "compression_block_k": k,
        })
    return episodes


def first_trade_at_or_after(timestamps: array, target: int, day_end: int) -> int | None:
    i = bisect.bisect_left(timestamps, target)
    if i >= len(timestamps) or int(timestamps[i]) >= day_end:
        return None
    return i


def simulate_scenario(stream: dict, episodes: list[dict], latency_ms: int, horizon_ms: int) -> dict:
    timestamps: array = stream["timestamps"]
    prices: array = stream["prices"]
    day_end = int(stream["day_end"])
    rows: list[dict] = []
    skipped_while_open = 0
    ineligible_day_end = 0
    unfilled_entry = 0
    unfilled_exit = 0
    open_until = -1

    for e in episodes:
        arm_ts = int(e["arm_ts"])
        if arm_ts <= open_until:
            skipped_while_open += 1
            continue

        decision = int(e["decision_ts"])
        entry_target = decision + latency_ms
        exit_target = entry_target + horizon_ms
        if exit_target >= day_end:
            ineligible_day_end += 1
            continue

        ei = first_trade_at_or_after(timestamps, entry_target, day_end)
        if ei is None:
            unfilled_entry += 1
            continue
        entry_ts = int(timestamps[ei])
        entry_px = float(prices[ei])

        xi = first_trade_at_or_after(timestamps, exit_target, day_end)
        if xi is None:
            unfilled_exit += 1
            open_until = day_end
            continue
        exit_ts = int(timestamps[xi])
        exit_px = float(prices[xi])
        open_until = exit_ts

        edge = int(e["direction"]) * (exit_px / entry_px - 1.0) * 10_000.0
        if not math.isfinite(edge):
            fail("non-finite gross edge")
        rows.append({
            "arm_ts": arm_ts,
            "decision_ts": decision,
            "direction": int(e["direction"]),
            "entry_target_ts": entry_target,
            "entry_ts": entry_ts,
            "entry_price": entry_px,
            "exit_target_ts": exit_target,
            "exit_ts": exit_ts,
            "exit_price": exit_px,
            "gross_edge_bps": edge,
        })

    raw = len(episodes)
    eligible = raw - skipped_while_open - ineligible_day_end
    completed = len(rows)
    completion_rate = (completed / eligible) if eligible > 0 else None
    return {
        "breakout_candidates": raw,
        "skipped_while_open": skipped_while_open,
        "ineligible_day_end": ineligible_day_end,
        "unfilled_entry": unfilled_entry,
        "unfilled_exit": unfilled_exit,
        "eligible_nonoverlap": eligible,
        "completed": completed,
        "completion_rate": completion_rate,
        "trades": rows,
    }


def process_day(date_text: str, manifest: dict[str, dict]) -> dict:
    stream = build_day_stream(date_text, manifest)
    blocks = build_blocks(stream)
    episode_cache = {
        0.15: potential_breakouts(stream, blocks, 0.15),
        0.20: potential_breakouts(stream, blocks, 0.20),
        0.25: potential_breakouts(stream, blocks, 0.25),
    }
    scenarios: dict[str, dict] = {}
    for name, q, latency, horizon, role in SCENARIOS:
        r = simulate_scenario(stream, episode_cache[q], latency, horizon)
        r["role"] = role
        r["q"] = q
        r["latency_ms"] = latency
        r["horizon_ms"] = horizon
        scenarios[name] = r
    return {
        "date": date_text,
        "source_stats": stream["stats"],
        "valid_seconds": stream["valid_seconds"],
        "valid_blocks": sum(1 for b in blocks if b["valid"]),
        "invalid_blocks": sum(1 for b in blocks if not b["valid"]),
        "scenarios": scenarios,
    }


def trimmed_mean(vals: list[float], frac: float = 0.10) -> float | None:
    if not vals:
        return None
    xs = sorted(float(v) for v in vals)
    m = math.floor(frac * len(xs))
    if 2 * m >= len(xs):
        return None
    kept = xs[m: len(xs) - m if m else None]
    if not kept:
        return None
    return float(statistics.fmean(kept))


def aggregate_scenario(days: list[dict], scenario_name: str) -> dict:
    day_rows: list[dict] = []
    all_edges: list[float] = []
    total_candidates = total_skipped = total_ineligible = total_eligible = total_completed = 0
    total_unfilled_entry = total_unfilled_exit = 0

    for d in days:
        s = d["scenarios"][scenario_name]
        edges = [float(t["gross_edge_bps"]) for t in s["trades"]]
        all_edges.extend(edges)
        mean_edge = float(statistics.fmean(edges)) if edges else None
        gross_sum = float(sum(edges)) if edges else 0.0
        day_rows.append({
            "date": d["date"],
            "completed": len(edges),
            "mean_gross_edge_bps": mean_edge,
            "gross_edge_sum_bps": gross_sum,
        })
        total_candidates += int(s["breakout_candidates"])
        total_skipped += int(s["skipped_while_open"])
        total_ineligible += int(s["ineligible_day_end"])
        total_eligible += int(s["eligible_nonoverlap"])
        total_completed += int(s["completed"])
        total_unfilled_entry += int(s["unfilled_entry"])
        total_unfilled_exit += int(s["unfilled_exit"])

    completion_rate = (total_completed / total_eligible) if total_eligible > 0 else None
    pooled_mean = float(statistics.fmean(all_edges)) if all_edges else None
    pooled_median = float(statistics.median(all_edges)) if all_edges else None
    tmean = trimmed_mean(all_edges, 0.10)

    active_means = [float(x["mean_gross_edge_bps"]) for x in day_rows if x["mean_gross_edge_bps"] is not None]
    median_daily = float(statistics.median(active_means)) if active_means else None
    active_days = len(active_means)
    positive_days = sum(1 for x in day_rows if x["mean_gross_edge_bps"] is not None and float(x["mean_gross_edge_bps"]) > 0)
    max_trades_day = max((int(x["completed"]) for x in day_rows), default=0)

    pos_contrib = sorted((max(float(x["gross_edge_sum_bps"]), 0.0) for x in day_rows), reverse=True)
    pos_total = sum(pos_contrib)
    top1 = (pos_contrib[0] / pos_total) if pos_total > 0 and pos_contrib else None
    top3 = (sum(pos_contrib[:3]) / pos_total) if pos_total > 0 and pos_contrib else None

    return {
        "scenario": scenario_name,
        "completed": total_completed,
        "breakout_candidates": total_candidates,
        "skipped_while_open": total_skipped,
        "ineligible_day_end": total_ineligible,
        "eligible_nonoverlap": total_eligible,
        "unfilled_entry": total_unfilled_entry,
        "unfilled_exit": total_unfilled_exit,
        "completion_rate": completion_rate,
        "pooled_mean_gross_edge_bps": pooled_mean,
        "trimmed_mean_10pct_gross_edge_bps": tmean,
        "pooled_median_gross_edge_bps": pooled_median,
        "median_active_daily_mean_gross_edge_bps": median_daily,
        "active_days": active_days,
        "positive_daily_mean_days": positive_days,
        "max_completed_trades_any_day": max_trades_day,
        "top1_positive_day_share": top1,
        "top3_positive_day_share": top3,
        "daily": day_rows,
    }


def ge(x: float | None, threshold: float) -> bool:
    return x is not None and math.isfinite(float(x)) and float(x) >= threshold


def gt(x: float | None, threshold: float) -> bool:
    return x is not None and math.isfinite(float(x)) and float(x) > threshold


def le(x: float | None, threshold: float) -> bool:
    return x is not None and math.isfinite(float(x)) and float(x) <= threshold


def evaluate_gates(stage: str, aggs: dict[str, dict]) -> tuple[str, list[dict]]:
    p = aggs[PRIMARY_NAME]
    st = aggs[STRESS_NAME]
    if stage == "discovery":
        req_active, req_positive, n_min, n_max = 16, 14, 40, 160
        top1_max, top3_max = 0.30, 0.60
        pass_label, fail_label = "E004_DISCOVERY_PASS", "E004_DISCOVERY_FAIL"
    elif stage == "confirmation":
        req_active, req_positive, n_min, n_max = 8, 7, 20, 80
        top1_max, top3_max = 0.35, 0.70
        pass_label, fail_label = "E004_CONFIRMATION_PASS", "E004_CONFIRMATION_FAIL"
    else:
        fail(f"bad gate stage: {stage}")

    checks = [
        ("pooled_mean_gross_edge_bps>=15", ge(p["pooled_mean_gross_edge_bps"], 15.0), p["pooled_mean_gross_edge_bps"]),
        ("trimmed_mean_10pct_gross_edge_bps>=12", ge(p["trimmed_mean_10pct_gross_edge_bps"], 12.0), p["trimmed_mean_10pct_gross_edge_bps"]),
        ("pooled_median_gross_edge_bps>0", gt(p["pooled_median_gross_edge_bps"], 0.0), p["pooled_median_gross_edge_bps"]),
        ("median_active_daily_mean_gross_edge_bps>=10", ge(p["median_active_daily_mean_gross_edge_bps"], 10.0), p["median_active_daily_mean_gross_edge_bps"]),
        (f"active_days>={req_active}", int(p["active_days"]) >= req_active, p["active_days"]),
        (f"positive_daily_mean_days>={req_positive}", int(p["positive_daily_mean_days"]) >= req_positive, p["positive_daily_mean_days"]),
        (f"completed>={n_min}", int(p["completed"]) >= n_min, p["completed"]),
        (f"completed<={n_max}", int(p["completed"]) <= n_max, p["completed"]),
        ("max_completed_trades_any_day<=12", int(p["max_completed_trades_any_day"]) <= 12, p["max_completed_trades_any_day"]),
        ("completion_rate>=0.99", ge(p["completion_rate"], 0.99), p["completion_rate"]),
        (f"top1_positive_day_share<={top1_max}", le(p["top1_positive_day_share"], top1_max), p["top1_positive_day_share"]),
        (f"top3_positive_day_share<={top3_max}", le(p["top3_positive_day_share"], top3_max), p["top3_positive_day_share"]),
        ("500ms_stress_pooled_mean>=13", ge(st["pooled_mean_gross_edge_bps"], 13.0), st["pooled_mean_gross_edge_bps"]),
        ("500ms_stress_trimmed_mean>=10", ge(st["trimmed_mean_10pct_gross_edge_bps"], 10.0), st["trimmed_mean_10pct_gross_edge_bps"]),
    ]
    gate_rows = [{"gate": name, "pass": bool(ok), "value": value} for name, ok, value in checks]
    verdict = pass_label if all(x["pass"] for x in gate_rows) else fail_label
    return verdict, gate_rows


def require_confirmation_authorized() -> dict:
    rep = load_json(DISCOVERY_REPORT)
    if rep.get("stage") != STAGE or rep.get("version") != VERSION:
        fail("discovery report identity mismatch")
    if rep.get("mode") != "discovery" or rep.get("verdict") != "E004_DISCOVERY_PASS":
        fail("confirmation is closed: terminal E004_DISCOVERY_PASS not found")
    if rep.get("engine_sha256") != script_sha():
        fail("confirmation is closed: engine SHA differs from Discovery")
    if rep.get("protocol") != PROTOCOL:
        fail("confirmation is closed: protocol identity mismatch")
    fw = rep.get("firewalls") or {}
    if fw.get("q2_market_data_body_accessed") is not False or fw.get("validation_or_final_accessed") is not False:
        fail("confirmation is closed: Discovery firewall mismatch")
    return rep


def run_mode(mode: str, workers: int) -> dict:
    if mode == "discovery":
        days = DISCOVERY_DAYS
        out_report = DISCOVERY_REPORT
        out_summary = DISCOVERY_SUMMARY
    elif mode == "confirmation":
        require_confirmation_authorized()
        days = CONFIRM_DAYS
        out_report = CONFIRM_REPORT
        out_summary = CONFIRM_SUMMARY
    else:
        fail(f"unsupported mode: {mode}")

    manifest = source_manifest()
    verify_sources(manifest)

    print(f"{STAGE} {mode.upper()} starting {len(days)} days with workers={workers}", flush=True)
    results: list[dict] = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(process_day, d, manifest): d for d in days}
        for fut in as_completed(futs):
            d = futs[fut]
            r = fut.result()
            results.append(r)
            # Deliberately no per-day alpha metrics in stdout.
            print(f"DAY COMPLETE {d}", flush=True)
    results.sort(key=lambda x: x["date"])

    aggs = {name: aggregate_scenario(results, name) for name, *_ in SCENARIOS}
    verdict, gates = evaluate_gates(mode, aggs)

    report = {
        "stage": STAGE,
        "version": VERSION,
        "mode": mode,
        "protocol": PROTOCOL,
        "preflight_spec": PREFLIGHT_SPEC,
        "implementation_freeze": IMPLEMENTATION_FREEZE,
        "engine_sha256": script_sha(),
        "python_version": sys.version,
        "dates": list(days),
        "verdict": verdict,
        "gates": gates,
        "scenarios": aggs,
        "day_integrity": [
            {
                "date": r["date"],
                "source_stats": r["source_stats"],
                "valid_seconds": r["valid_seconds"],
                "valid_blocks": r["valid_blocks"],
                "invalid_blocks": r["invalid_blocks"],
            }
            for r in results
        ],
        "firewalls": {
            "l2_accessed": False,
            "q2_market_data_body_accessed": False,
            "validation_or_final_accessed": False,
            "e002_tfi_used": False,
            "e003_flow_impulse_used": False,
            "maker_model_used": False,
        },
    }

    if mode == "confirmation" and verdict == "E004_CONFIRMATION_PASS":
        report["gross_hurdle_status"] = "E004_GROSS_HURDLE_PASS"
    elif mode == "confirmation":
        report["gross_hurdle_status"] = "CLOSED"

    atomic_json(out_report, report)
    summary = render_summary(report)
    atomic_text(out_summary, summary)
    print(f"FINAL VERDICT {verdict}", flush=True)
    print(f"REPORT {out_report}", flush=True)
    print(f"SUMMARY {out_summary}", flush=True)
    return report


def fmt(x: object, digits: int = 6) -> str:
    if x is None:
        return "NA"
    if isinstance(x, float):
        return f"{x:.{digits}f}"
    return str(x)


def render_summary(report: dict) -> str:
    p = report["scenarios"][PRIMARY_NAME]
    st = report["scenarios"][STRESS_NAME]
    lines = [
        f"# SC001-E004 {report['mode'].upper()} Summary",
        "",
        f"- Verdict: `{report['verdict']}`",
        f"- Engine SHA256: `{report['engine_sha256']}`",
        f"- Primary completed trades: {p['completed']}",
        f"- Primary pooled mean gross edge: {fmt(p['pooled_mean_gross_edge_bps'])} bps",
        f"- Primary 10% trimmed mean: {fmt(p['trimmed_mean_10pct_gross_edge_bps'])} bps",
        f"- Primary pooled median: {fmt(p['pooled_median_gross_edge_bps'])} bps",
        f"- Primary median active-day mean: {fmt(p['median_active_daily_mean_gross_edge_bps'])} bps",
        f"- Primary positive days: {p['positive_daily_mean_days']} / {len(report['dates'])}",
        f"- Primary active days: {p['active_days']} / {len(report['dates'])}",
        f"- Primary completion rate: {fmt(p['completion_rate'])}",
        f"- Primary max trades/day: {p['max_completed_trades_any_day']}",
        f"- Primary top-1 positive-day share: {fmt(p['top1_positive_day_share'])}",
        f"- Primary top-3 positive-day share: {fmt(p['top3_positive_day_share'])}",
        f"- 500 ms stress pooled mean: {fmt(st['pooled_mean_gross_edge_bps'])} bps",
        f"- 500 ms stress 10% trimmed mean: {fmt(st['trimmed_mean_10pct_gross_edge_bps'])} bps",
        "",
        "## Gate ledger",
        "",
    ]
    for g in report["gates"]:
        lines.append(f"- {'PASS' if g['pass'] else 'FAIL'} — {g['gate']} — value `{fmt(g['value'])}`")
    lines += [
        "",
        "Diagnostics are read-only and cannot replace a failed primary or mandatory stress gate.",
        "",
        "No L2/Q2/Validation/Final access occurred in this stage.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["discovery", "confirmation"])
    ap.add_argument("--workers", type=int, default=min(4, max(1, os.cpu_count() or 1)))
    args = ap.parse_args()
    if args.workers < 1 or args.workers > 4:
        fail("--workers must be in [1,4]")
    run_mode(args.mode, args.workers)


if __name__ == "__main__":
    main()
