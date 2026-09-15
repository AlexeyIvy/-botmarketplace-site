"""SC001-E004 frozen volatility-compression breakout engine.

Implements:
  docs/research/sc001-e004-volatility-compression-breakout-executable-protocol-v1.0.md
with implementation/data-audit semantics frozen in:
  docs/research/sc001-e004-implementation-preflight-spec-v1.1.md

The discovery/confirmation CLI is fail-closed behind a matching PREFLIGHT_PASS.
No L2, no Q2, no Validation/Final, no E002 TFI, no E003 FLOW_IMPULSE.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import math
import os
import platform
import random
import statistics
import subprocess
import sys
import zipfile
from array import array
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

STAGE = "SC001-E004-VOLATILITY-COMPRESSION-BREAKOUT"
ENGINE_VERSION = "1.0"
PROTOCOL_PATH = "docs/research/sc001-e004-volatility-compression-breakout-executable-protocol-v1.0.md"
PREFLIGHT_SPEC_PATH = "docs/research/sc001-e004-implementation-preflight-spec-v1.1.md"
DEFAULT_CONFIG_PATH = Path(__file__).with_name("sc001_e004_config_v1_0.json")

UTC = timezone.utc
DAY_MS = 86_400_000
MIN_MS = 60_000

def fail(msg: str) -> None:
    raise RuntimeError(msg)

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing required JSON: {path}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        fail(f"JSON object expected: {path}")
    return obj

def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

def atomic_json(path: Path, obj: object) -> None:
    atomic_text(path, json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

def parse_date(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=UTC)

def date_ms(s: str) -> int:
    return int(parse_date(s).timestamp() * 1000)

def day_text(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000, tz=UTC).strftime("%Y-%m-%d")

def next_day_text(s: str) -> str:
    return (parse_date(s) + timedelta(days=1)).strftime("%Y-%m-%d")

def iter_dates(start: str, end: str):
    d = parse_date(start)
    e = parse_date(end)
    while d <= e:
        yield d.strftime("%Y-%m-%d")
        d += timedelta(days=1)

def parse_clock_ms(s: str) -> int:
    hh, mm, rest = s.split(":")
    if "." in rest:
        ss, ms = rest.split(".")
        ms = (ms + "000")[:3]
    else:
        ss, ms = rest, "000"
    return (int(hh)*3600 + int(mm)*60 + int(ss))*1000 + int(ms)

def parse_ts_ms(text: str) -> int:
    v = int(str(text).strip())
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

def git_commit(repo_root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None

def repo_root_from_file() -> Path:
    p = Path(__file__).resolve()
    return p.parents[2]

def load_config(path: Path = DEFAULT_CONFIG_PATH) -> dict:
    cfg = load_json(path)
    if cfg.get("experiment") != "SC001-E004":
        fail("wrong experiment config")
    if cfg.get("protocol_version") != "1.0":
        fail("wrong E004 protocol version")
    if cfg.get("primary_id") != "E004_P_W15_Q20_LB1440_B2_ARM15_LAT250_H15_CAP4":
        fail("wrong primary configuration identifier")
    fw = cfg.get("firewalls") or {}
    if any(fw.get(k) is not False for k in ("use_tfi","use_flow_impulse","l2","q2","validation","final")):
        fail("E004 firewall config mismatch")
    return cfg

def data_paths(cfg: dict) -> tuple[Path, Path, Path]:
    root = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
    source_root = root / cfg["source_root"]
    archives = source_root / cfg["archive_subdir"]
    source_report = source_root / cfg["source_report"]
    return root, archives, source_report

def source_manifest(cfg: dict, required_labels: set[str]) -> dict[str, dict]:
    _, archives, source_report = data_paths(cfg)
    rep = load_json(source_report)
    if rep.get("stage") != cfg["source_stage"] or rep.get("status") != "PASS":
        fail("qualified March source stage is not PASS")
    if rep.get("q2_market_data_body_accessed") is not False:
        fail("source report says Q2 market-data body was accessed")
    if rep.get("validation_or_final_accessed") is not False:
        fail("source report says Validation/Final was accessed")
    if rep.get("alpha_calculated") is not False or rep.get("pnl_calculated") is not False:
        fail("source report alpha/P&L firewall mismatch")
    out: dict[str, dict] = {}
    for row in rep.get("archives") or []:
        if not isinstance(row, dict):
            continue
        d = row.get("date")
        if d not in required_labels:
            continue
        fn = row.get("filename")
        size = row.get("bytes")
        digest = row.get("sha256")
        expected_fn = f"{cfg['instrument']}-trades-{d}.zip"
        if fn != expected_fn or not isinstance(size, int) or size <= 0:
            fail(f"bad manifest identity for {d}")
        if not isinstance(digest, str) or len(digest) != 64:
            fail(f"bad manifest SHA for {d}")
        out[d] = {
            "date": d, "filename": fn, "bytes": size, "sha256": digest,
            "path": archives / fn,
        }
    if set(out) != set(required_labels):
        missing = sorted(set(required_labels) - set(out))
        fail(f"missing required source manifest labels: {missing}")
    return out

def verify_archive_identity(meta: dict, full_crc: bool = True) -> None:
    p = Path(meta["path"])
    if not p.exists():
        fail(f"missing archive: {p}")
    if p.stat().st_size != int(meta["bytes"]):
        fail(f"archive size mismatch: {p.name}")
    if sha256_file(p) != meta["sha256"]:
        fail(f"archive SHA mismatch: {p.name}")
    with zipfile.ZipFile(p, "r") as zf:
        if full_crc:
            bad = zf.testzip()
            if bad is not None:
                fail(f"ZIP CRC failure {p.name}: {bad}")
        members = [m for m in zf.infolist() if not m.is_dir()]
        if len(members) != 1:
            fail(f"unexpected ZIP member count {p.name}: {len(members)}")

def _iter_archive_rows(path: Path, cfg: dict):
    expected = cfg["expected_header"]
    with zipfile.ZipFile(path, "r") as zf:
        members = [m for m in zf.infolist() if not m.is_dir()]
        if len(members) != 1:
            fail(f"unexpected ZIP member count {path.name}: {len(members)}")
        with zf.open(members[0], "r") as raw:
            reader = csv.reader((line.decode("utf-8") for line in raw))
            header = next(reader, None)
            if header != expected:
                fail(f"unexpected trade header in {path.name}: {header!r}")
            src_last_ts = None
            src_last_tid = None
            for seq, row in enumerate(reader):
                if not row:
                    continue
                if len(row) != 6:
                    fail(f"malformed row in {path.name} at {seq+2}")
                inst, tid_txt, side, ptxt, stxt, ttxt = row
                if inst != cfg["instrument"]:
                    continue
                try:
                    tid = int(tid_txt)
                    ts = parse_ts_ms(ttxt)
                    px = float(ptxt)
                    sz = float(stxt)
                except Exception as exc:
                    raise RuntimeError(f"invalid target row in {path.name} at {seq+2}") from exc
                if side not in {"buy","sell"} or not math.isfinite(px) or px <= 0 or not math.isfinite(sz) or sz <= 0:
                    fail(f"invalid values in {path.name} at {seq+2}")
                if src_last_ts is not None and ts < src_last_ts:
                    fail(f"source timestamp reversal in {path.name}")
                if src_last_tid is not None and tid <= src_last_tid:
                    fail(f"source trade-id duplicate/backward in {path.name}")
                src_last_ts = ts
                src_last_tid = tid
                yield ts, tid, px, side, seq

def reconstruct_utc_day(date_text: str, cfg: dict, manifest: dict[str, dict], *,
                        include_side: bool = False) -> dict:
    lo = date_ms(date_text)
    hi = lo + DAY_MS
    d1 = next_day_text(date_text)
    timestamps = array("q")
    trade_ids = array("q")
    prices = array("d")
    sides = array("b") if include_side else None
    src_seq = array("q")
    minute_seen = bytearray(1440)
    buy = sell = 0
    target_last_ts = None
    target_last_tid = None
    global_seq = 0
    for label in (date_text, d1):
        meta = manifest[label]
        for ts, tid, px, side, seq in _iter_archive_rows(Path(meta["path"]), cfg):
            if lo <= ts < hi:
                if target_last_ts is not None and ts < target_last_ts:
                    fail(f"stitched UTC timestamp reversal for {date_text}")
                if target_last_tid is not None and tid <= target_last_tid:
                    fail(f"stitched UTC trade-id duplicate/backward for {date_text}")
                target_last_ts = ts
                target_last_tid = tid
                timestamps.append(ts)
                trade_ids.append(tid)
                prices.append(px)
                src_seq.append(global_seq)
                if sides is not None:
                    sides.append(1 if side == "buy" else -1)
                if side == "buy": buy += 1
                else: sell += 1
                minute_seen[(ts-lo)//MIN_MS] = 1
            global_seq += 1
    if not timestamps:
        fail(f"no admitted trades for UTC day {date_text}")
    if buy == 0 or sell == 0:
        fail(f"missing buy/sell side for UTC day {date_text}")
    if sum(minute_seen) != 1440:
        fail(f"UTC minute coverage failure for {date_text}: {sum(minute_seen)}/1440")
    return {
        "date": date_text, "start_ms": lo, "end_ms": hi,
        "timestamps": timestamps, "trade_ids": trade_ids, "prices": prices,
        "source_seq": src_seq, "sides": sides,
        "buy_count": buy, "sell_count": sell,
    }

def load_stream(start: str, end: str, cfg: dict, manifest: dict[str, dict]) -> dict:
    start_ms = date_ms(start)
    end_ms = date_ms(end) + DAY_MS
    timestamps = array("q")
    prices = array("d")
    seqs = array("q")
    day_counts = {}
    gseq = 0
    for d in iter_dates(start, end):
        one = reconstruct_utc_day(d, cfg, manifest)
        day_counts[d] = len(one["timestamps"])
        for i in range(len(one["timestamps"])):
            timestamps.append(int(one["timestamps"][i]))
            prices.append(float(one["prices"][i]))
            seqs.append(gseq)
            gseq += 1
    if len(timestamps) != len(prices):
        fail("stream length mismatch")
    return {
        "start": start, "end": end, "start_ms": start_ms, "end_ms": end_ms,
        "timestamps": timestamps, "prices": prices, "seqs": seqs,
        "day_counts": day_counts,
    }

def nearest_rank(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        fail("nearest-rank on empty list")
    rank = math.ceil(q * len(sorted_values))
    rank = min(max(rank, 1), len(sorted_values))
    return float(sorted_values[rank-1])

def compression_bps(high: float, low: float) -> float:
    if not (math.isfinite(high) and math.isfinite(low) and high >= low and low > 0):
        fail("bad high/low for compression")
    mid = (high + low) / 2.0
    return 10_000.0 * (high - low) / mid

def window_high_low(timestamps, prices, t_ms: int, window_ms: int) -> tuple[float, float]:
    lo = bisect.bisect_left(timestamps, t_ms - window_ms)
    hi = bisect.bisect_left(timestamps, t_ms)
    if lo >= hi:
        fail("empty compression window")
    vals = prices[lo:hi]
    return max(vals), min(vals)

def build_minute_indicators(stream: dict, cfg: dict, *,
                            window_minutes: int | None = None,
                            percentile: float | None = None) -> tuple[list[dict], dict]:
    w = int(window_minutes if window_minutes is not None else cfg["compression_window_minutes"])
    q = float(percentile if percentile is not None else cfg["compression_percentile"])
    lb = int(cfg["threshold_lookback_minutes"])
    start_ms = int(stream["start_ms"])
    end_ms = int(stream["end_ms"])
    n_minutes = (end_ms - start_ms) // MIN_MS
    minute_hi = [float("-inf")] * n_minutes
    minute_lo = [float("inf")] * n_minutes
    timestamps = stream["timestamps"]
    prices = stream["prices"]
    for i in range(len(timestamps)):
        k = (int(timestamps[i]) - start_ms) // MIN_MS
        if 0 <= k < n_minutes:
            px = float(prices[i])
            if px > minute_hi[k]: minute_hi[k] = px
            if px < minute_lo[k]: minute_lo[k] = px
    missing_minutes = sum(1 for h in minute_hi if not math.isfinite(h))
    c_records: list[dict] = []
    for boundary_idx in range(w, n_minutes + 1):
        hs = minute_hi[boundary_idx-w:boundary_idx]
        ls = minute_lo[boundary_idx-w:boundary_idx]
        if any(not math.isfinite(x) for x in hs) or any(not math.isfinite(x) for x in ls):
            continue
        high = max(hs)
        low = min(ls)
        c = compression_bps(high, low)
        c_records.append({
            "t": start_ms + boundary_idx*MIN_MS,
            "high": high, "low": low, "c": c,
        })
    hist_q: list[float] = []
    hist_sorted: list[float] = []
    eligible = []
    tie_count = 0
    prev_z = None
    for rec in c_records:
        if len(hist_q) == lb:
            thr = nearest_rank(hist_sorted, q)
            z = rec["c"] <= thr
            if rec["c"] == thr:
                tie_count += 1
            eligible.append({
                **rec, "threshold": thr, "z": z, "prev_z": prev_z,
                "transition": bool(z and prev_z is False),
            })
            prev_z = z
        bisect.insort(hist_sorted, rec["c"])
        hist_q.append(rec["c"])
        if len(hist_q) > lb:
            old = hist_q.pop(0)
            j = bisect.bisect_left(hist_sorted, old)
            if j >= len(hist_sorted) or hist_sorted[j] != old:
                fail("rolling threshold state corruption")
            hist_sorted.pop(j)
    first_eligible = eligible[0]["t"] if eligible else None
    return eligible, {
        "minute_count": n_minutes,
        "missing_minute_count": missing_minutes,
        "compression_stat_count": len(c_records),
        "eligible_minute_count": len(eligible),
        "threshold_tie_count": tie_count,
        "first_eligible_ms": first_eligible,
    }

def first_trade_at_or_after(timestamps, target_ms: int, max_ms: int | None = None) -> int | None:
    i = bisect.bisect_left(timestamps, target_ms)
    if i >= len(timestamps):
        return None
    ts = int(timestamps[i])
    if max_ms is not None and ts > max_ms:
        return None
    return i

def first_breakout(timestamps, prices, arm_ts: int, expiry_ts: int,
                   upper: float, lower: float) -> tuple[int,int,int] | None:
    i = bisect.bisect_right(timestamps, arm_ts)
    while i < len(timestamps):
        ts = int(timestamps[i])
        if ts > expiry_ts:
            return None
        px = float(prices[i])
        if px > upper:
            return i, ts, 1
        if px < lower:
            return i, ts, -1
        i += 1
    return None

def proxy_leg(timestamps, target_ms: int, tolerance_ms: int) -> int | None:
    return first_trade_at_or_after(timestamps, target_ms, target_ms + tolerance_ms)

def simulate_primary(stream: dict, indicators: list[dict], cfg: dict,
                     phase_start: str, phase_end: str, *,
                     breakout_buffer_bps: float | None = None,
                     holding_minutes: int | None = None,
                     calculate_alpha: bool = True) -> tuple[list[dict], dict]:
    buf = float(cfg["breakout_buffer_bps"] if breakout_buffer_bps is None else breakout_buffer_bps)
    hold_ms = int((cfg["holding_minutes"] if holding_minutes is None else holding_minutes) * MIN_MS)
    arm_ms = int(cfg["arm_minutes"] * MIN_MS)
    cooldown_ms = int(cfg["cooldown_minutes"] * MIN_MS)
    latency = int(cfg["primary_latency_ms"])
    tol = int(cfg["entry_exit_tolerance_ms"])
    arm_latest = parse_clock_ms(cfg["arm_latest_utc"])
    decision_latest = parse_clock_ms(cfg["decision_latest_utc"])
    max_decisions = int(cfg["max_decisions_per_utc_day"])
    phase_lo = date_ms(phase_start)
    phase_hi = date_ms(phase_end) + DAY_MS
    timestamps = stream["timestamps"]
    prices = stream["prices"]

    available_at = phase_lo
    current_day: str | None = None
    locked_day: str | None = None
    day_decisions: Counter[str] = Counter()
    events: list[dict] = []
    counts = Counter()
    max_concurrent = 0

    for rec in indicators:
        arm_ts = int(rec["t"])
        if not (phase_lo <= arm_ts < phase_hi):
            continue
        d = day_text(arm_ts)
        day_start = date_ms(d)
        if current_day != d:
            current_day = d
            available_at = day_start
            locked_day = None
        if day_decisions[d] >= max_decisions:
            locked_day = d
        if locked_day == d:
            counts["candidate_transition_while_day_locked"] += 1 if rec["transition"] else 0
            continue
        if not rec["transition"]:
            continue
        counts["compression_transitions"] += 1
        if arm_ts < available_at:
            counts["transition_while_not_idle"] += 1
            continue
        if arm_ts - day_start > arm_latest:
            counts["arm_after_cutoff"] += 1
            continue

        upper = float(rec["high"]) * (1.0 + buf/10_000.0)
        lower = float(rec["low"]) * (1.0 - buf/10_000.0)
        expiry = arm_ts + arm_ms
        counts["arms"] += 1
        br = first_breakout(timestamps, prices, arm_ts, expiry, upper, lower)
        if br is None:
            counts["arm_expiries"] += 1
            available_at = expiry + cooldown_ms
            continue
        bi, decision_ts, direction = br
        if decision_ts - day_start > decision_latest:
            counts["late_ineligible_breakouts"] += 1
            available_at = decision_ts + cooldown_ms
            continue

        day_decisions[d] += 1
        counts["decisions"] += 1
        if day_decisions[d] >= max_decisions:
            locked_day = d

        entry_target = decision_ts + latency
        ei = proxy_leg(timestamps, entry_target, tol)
        event = {
            "date": d, "arm_ts": arm_ts, "decision_ts": decision_ts,
            "direction": direction, "completed": False,
            "entry_ts": None, "exit_ts": None, "gross_edge_bps": None,
        }
        if ei is None or int(timestamps[ei]) >= day_start + DAY_MS:
            counts["entry_incomplete"] += 1
            terminal = min(entry_target + tol, day_start + DAY_MS)
            available_at = terminal + cooldown_ms
            events.append(event)
            continue

        entry_ts = int(timestamps[ei])
        exit_target = entry_ts + hold_ms
        if exit_target >= day_start + DAY_MS:
            counts["exit_day_cross_incomplete"] += 1
            event["entry_ts"] = entry_ts
            terminal = day_start + DAY_MS
            available_at = terminal
            events.append(event)
            continue
        xi = proxy_leg(timestamps, exit_target, tol)
        if xi is None or int(timestamps[xi]) >= day_start + DAY_MS:
            counts["exit_incomplete"] += 1
            event["entry_ts"] = entry_ts
            terminal = min(exit_target + tol, day_start + DAY_MS)
            available_at = terminal + cooldown_ms
            events.append(event)
            continue

        exit_ts = int(timestamps[xi])
        event["entry_ts"] = entry_ts
        event["exit_ts"] = exit_ts
        event["completed"] = True
        if calculate_alpha:
            ep = float(prices[ei])
            xp = float(prices[xi])
            event["entry_price"] = ep
            event["exit_price"] = xp
            event["gross_edge_bps"] = direction * 10_000.0 * (xp/ep - 1.0)
        counts["completed"] += 1
        available_at = exit_ts + cooldown_ms
        events.append(event)
        max_concurrent = max(max_concurrent, 1)

    max_decisions_day = max(day_decisions.values(), default=0)
    if max_decisions_day > max_decisions:
        fail("daily decision cap invariant breached")
    return events, {
        **dict(counts),
        "max_decisions_per_day_observed": max_decisions_day,
        "max_concurrent_positions": max_concurrent,
        "daily_decision_counts": dict(sorted(day_decisions.items())),
    }

def replay_latency(stream: dict, primary_events: list[dict], cfg: dict, latency_ms: int,
                   holding_minutes: int | None = None, calculate_alpha: bool = True) -> list[dict]:
    hold_ms = int((cfg["holding_minutes"] if holding_minutes is None else holding_minutes) * MIN_MS)
    tol = int(cfg["entry_exit_tolerance_ms"])
    timestamps = stream["timestamps"]
    prices = stream["prices"]
    out = []
    for p in primary_events:
        d = p["date"]
        day_start = date_ms(d)
        decision_ts = int(p["decision_ts"])
        direction = int(p["direction"])
        row = {"date": d, "decision_ts": decision_ts, "direction": direction,
               "completed": False, "entry_ts": None, "exit_ts": None, "gross_edge_bps": None}
        entry_target = decision_ts + int(latency_ms)
        ei = proxy_leg(timestamps, entry_target, tol)
        if ei is None or int(timestamps[ei]) >= day_start + DAY_MS:
            out.append(row); continue
        entry_ts = int(timestamps[ei])
        exit_target = entry_ts + hold_ms
        if exit_target >= day_start + DAY_MS:
            row["entry_ts"] = entry_ts
            out.append(row); continue
        xi = proxy_leg(timestamps, exit_target, tol)
        if xi is None or int(timestamps[xi]) >= day_start + DAY_MS:
            row["entry_ts"] = entry_ts
            out.append(row); continue
        exit_ts = int(timestamps[xi])
        row.update({"completed": True, "entry_ts": entry_ts, "exit_ts": exit_ts})
        if calculate_alpha:
            ep = float(prices[ei]); xp = float(prices[xi])
            row["entry_price"] = ep; row["exit_price"] = xp
            row["gross_edge_bps"] = direction * 10_000.0 * (xp/ep - 1.0)
        out.append(row)
    return out

def trimmed_mean(vals: list[float], frac: float = 0.10) -> float | None:
    if not vals:
        return None
    xs = sorted(vals)
    k = math.floor(frac * len(xs))
    core = xs[k:len(xs)-k] if k else xs
    if not core:
        return None
    return float(statistics.fmean(core))

def bootstrap_lcb(events: list[dict], cfg: dict) -> float | None:
    by_day: dict[str, list[float]] = {}
    for e in events:
        if e.get("completed") and e.get("gross_edge_bps") is not None:
            by_day.setdefault(e["date"], []).append(float(e["gross_edge_bps"]))
    days = sorted(by_day)
    if not days:
        return None
    bcfg = cfg["bootstrap"]
    rng = random.Random(int(bcfg["seed"]))
    means = []
    for _ in range(int(bcfg["resamples"])):
        sample = [rng.choice(days) for _ in days]
        vals = []
        for d in sample:
            vals.extend(by_day[d])
        means.append(statistics.fmean(vals))
    means.sort()
    return nearest_rank(means, float(bcfg["lower_quantile"]))

def scenario_metrics(events: list[dict], cfg: dict, *, include_bootstrap: bool = True) -> dict:
    completed = [e for e in events if e.get("completed") and e.get("gross_edge_bps") is not None]
    vals = [float(e["gross_edge_bps"]) for e in completed]
    decisions = len(events)
    by_day: dict[str, list[float]] = {}
    by_side: dict[int, list[float]] = {1: [], -1: []}
    for e in completed:
        by_day.setdefault(e["date"], []).append(float(e["gross_edge_bps"]))
        by_side[int(e["direction"])].append(float(e["gross_edge_bps"]))
    daily_means = {d: statistics.fmean(v) for d,v in sorted(by_day.items())}
    day_sums = {d: sum(v) for d,v in sorted(by_day.items())}
    denom = sum(abs(v) for v in day_sums.values())
    shares = sorted((abs(v)/denom for v in day_sums.values()), reverse=True) if denom > 0 else [1.0]
    long_n = len(by_side[1]); short_n = len(by_side[-1])
    n = len(completed)
    return {
        "decisions": decisions,
        "completed_trades": n,
        "completion_rate": n/decisions if decisions else 0.0,
        "active_days": len(by_day),
        "mean_bps": statistics.fmean(vals) if vals else None,
        "median_bps": statistics.median(vals) if vals else None,
        "trimmed_mean_bps": trimmed_mean(vals),
        "median_daily_mean_bps": statistics.median(daily_means.values()) if daily_means else None,
        "positive_active_days": sum(1 for x in daily_means.values() if x > 0),
        "positive_active_day_share": (sum(1 for x in daily_means.values() if x > 0)/len(daily_means)) if daily_means else 0.0,
        "long_completed": long_n, "short_completed": short_n,
        "max_side_share": max(long_n, short_n)/n if n else 1.0,
        "top1_abs_day_share": shares[0] if shares else 1.0,
        "top3_abs_day_share": sum(shares[:3]) if shares else 1.0,
        "bootstrap_95_lcb_bps": bootstrap_lcb(events, cfg) if include_bootstrap else None,
        "daily_means_bps": daily_means,
        "daily_sums_bps": day_sums,
        "long_mean_bps": statistics.fmean(by_side[1]) if by_side[1] else None,
        "short_mean_bps": statistics.fmean(by_side[-1]) if by_side[-1] else None,
    }

def evaluate_gates(phase: str, metrics: dict, stress500: dict, stress1000: dict,
                   sim_meta: dict, cfg: dict) -> tuple[bool, list[dict]]:
    g = cfg[phase]["gates"]
    checks = []
    def add(name, ok, value, rule):
        checks.append({"gate": name, "pass": bool(ok), "value": value, "rule": rule})
    n = metrics["completed_trades"]
    add("completed_range", g["completed_min"] <= n <= g["completed_max"], n,
        f"{g['completed_min']} <= completed <= {g['completed_max']}")
    add("active_days", metrics["active_days"] >= g["active_days_min"], metrics["active_days"], f">= {g['active_days_min']}")
    add("completion_rate", metrics["completion_rate"] >= g["completion_rate_min"], metrics["completion_rate"], f">= {g['completion_rate_min']}")
    add("mean_bps", metrics["mean_bps"] is not None and metrics["mean_bps"] >= g["mean_bps_min"], metrics["mean_bps"], f">= {g['mean_bps_min']}")
    add("trimmed_mean_bps", metrics["trimmed_mean_bps"] is not None and metrics["trimmed_mean_bps"] >= g["trimmed_mean_bps_min"], metrics["trimmed_mean_bps"], f">= {g['trimmed_mean_bps_min']}")
    add("median_bps", metrics["median_bps"] is not None and metrics["median_bps"] >= g["median_bps_min"], metrics["median_bps"], f">= {g['median_bps_min']}")
    add("median_daily_mean_bps", metrics["median_daily_mean_bps"] is not None and metrics["median_daily_mean_bps"] >= g["median_daily_mean_bps_min"], metrics["median_daily_mean_bps"], f">= {g['median_daily_mean_bps_min']}")
    add("positive_active_day_share", metrics["positive_active_day_share"] >= g["positive_active_day_share_min"], metrics["positive_active_day_share"], f">= {g['positive_active_day_share_min']}")
    add("bootstrap_lcb", metrics["bootstrap_95_lcb_bps"] is not None and metrics["bootstrap_95_lcb_bps"] > g["bootstrap_lcb_bps_strict_gt"], metrics["bootstrap_95_lcb_bps"], f"> {g['bootstrap_lcb_bps_strict_gt']}")
    add("top1_concentration", metrics["top1_abs_day_share"] <= g["top1_abs_day_share_max"], metrics["top1_abs_day_share"], f"<= {g['top1_abs_day_share_max']}")
    add("top3_concentration", metrics["top3_abs_day_share"] <= g["top3_abs_day_share_max"], metrics["top3_abs_day_share"], f"<= {g['top3_abs_day_share_max']}")
    add("each_side_count", min(metrics["long_completed"], metrics["short_completed"]) >= g["each_side_completed_min"],
        min(metrics["long_completed"], metrics["short_completed"]), f">= {g['each_side_completed_min']} each")
    add("max_side_share", metrics["max_side_share"] <= g["max_side_share_max"], metrics["max_side_share"], f"<= {g['max_side_share_max']}")
    add("lat500_mean", stress500["mean_bps"] is not None and stress500["mean_bps"] >= g["lat500_mean_bps_min"], stress500["mean_bps"], f">= {g['lat500_mean_bps_min']}")
    add("lat500_trim", stress500["trimmed_mean_bps"] is not None and stress500["trimmed_mean_bps"] >= g["lat500_trimmed_mean_bps_min"], stress500["trimmed_mean_bps"], f">= {g['lat500_trimmed_mean_bps_min']}")
    add("lat1000_mean", stress1000["mean_bps"] is not None and stress1000["mean_bps"] >= g["lat1000_mean_bps_min"], stress1000["mean_bps"], f">= {g['lat1000_mean_bps_min']}")
    add("lat1000_trim", stress1000["trimmed_mean_bps"] is not None and stress1000["trimmed_mean_bps"] >= g["lat1000_trimmed_mean_bps_min"], stress1000["trimmed_mean_bps"], f">= {g['lat1000_trimmed_mean_bps_min']}")
    add("daily_cap", sim_meta.get("max_decisions_per_day_observed", 99) <= cfg["max_decisions_per_utc_day"],
        sim_meta.get("max_decisions_per_day_observed"), f"<= {cfg['max_decisions_per_utc_day']}")
    add("max_one_position", sim_meta.get("max_concurrent_positions", 99) <= 1,
        sim_meta.get("max_concurrent_positions"), "<= 1")
    return all(x["pass"] for x in checks), checks

def required_labels_for_phase(phase: str, cfg: dict) -> set[str]:
    if phase == "discovery":
        start = cfg["discovery"]["indicator_warmup_start"]
        end = cfg["discovery"]["end"]
    elif phase == "confirmation":
        start = cfg["confirmation"]["indicator_warmup_start"]
        end = cfg["confirmation"]["end"]
    else:
        fail(f"bad phase {phase}")
    labels = set(iter_dates(start, end))
    labels.add(next_day_text(end))
    return labels

def preflight_report_path(cfg: dict) -> Path:
    root, _, _ = data_paths(cfg)
    return root / "SC001_E004" / "preflight" / "sc001_e004_preflight_report.json"

def require_preflight_pass(cfg_path: Path, cfg: dict) -> dict:
    rep_path = preflight_report_path(cfg)
    rep = load_json(rep_path)
    if rep.get("status") != "PREFLIGHT_PASS":
        fail("E004 discovery/confirmation blocked: exact PREFLIGHT_PASS absent")
    if rep.get("protocol_version") != "1.0" or rep.get("preflight_spec_version") != "1.1":
        fail("preflight report version mismatch")
    if rep.get("config_sha256") != sha256_file(cfg_path):
        fail("preflight config SHA mismatch")
    if rep.get("engine_sha256") != sha256_file(Path(__file__).resolve()):
        fail("preflight engine SHA mismatch")
    return rep

def require_confirmation_gate(cfg: dict, cfg_path: Path = DEFAULT_CONFIG_PATH) -> dict:
    root, _, _ = data_paths(cfg)
    p = root / "SC001_E004" / "discovery" / "sc001_e004_run_state.json"
    rep = load_json(p)
    if rep.get("terminal_status") != "E004_DISCOVERY_PASS_OPEN_CONFIRMATION_ONCE":
        fail("confirmation blocked: Discovery PASS token absent")
    if rep.get("engine_sha256") != sha256_file(Path(__file__).resolve()):
        fail("confirmation blocked: engine SHA differs from Discovery")
    if rep.get("config_sha256") != sha256_file(cfg_path):
        fail("confirmation blocked: config SHA differs from Discovery")
    return rep

def runtime_identity(cfg_path: Path) -> dict:
    repo = repo_root_from_file()
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "timezone": "UTC",
        "git_commit": git_commit(repo),
        "engine_sha256": sha256_file(Path(__file__).resolve()),
        "config_sha256": sha256_file(cfg_path),
    }

def output_root_for_phase(cfg: dict, phase: str) -> Path:
    root, _, _ = data_paths(cfg)
    return root / "SC001_E004" / phase

def ensure_new_output_dir(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        fail(f"refusing to overwrite non-empty output directory: {path}")
    path.mkdir(parents=True, exist_ok=True)

def write_csv_atomic(path: Path, header: list[str], rows: list[list]) -> None:
    tmp = Path(str(path)+".tmp")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tmp.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)

def write_phase_artifacts(outdir: Path, phase: str, cfg_path: Path, cfg: dict,
                          manifest: dict[str,dict], events: list[dict], metrics: dict,
                          stress500: dict, stress1000: dict, sim_meta: dict,
                          gate_rows: list[dict], terminal: str, indicator_meta: dict) -> None:
    atomic_text(outdir / "sc001_e004_frozen_config.json", cfg_path.read_text(encoding="utf-8"))
    manifest_out = [{
        "date": d, "filename": x["filename"], "bytes": x["bytes"], "sha256": x["sha256"]
    } for d,x in sorted(manifest.items())]
    atomic_json(outdir / "sc001_e004_input_manifest.json", {"archives": manifest_out})
    trows = []
    for e in events:
        trows.append([
            e["date"], e["arm_ts"], e["decision_ts"], "LONG" if e["direction"]==1 else "SHORT",
            e.get("entry_ts"), e.get("exit_ts"), e.get("entry_price"), e.get("exit_price"),
            e.get("gross_edge_bps"), int(bool(e.get("completed")))
        ])
    write_csv_atomic(outdir / "sc001_e004_trades.csv",
                     ["date","arm_ts_ms","decision_ts_ms","side","entry_ts_ms","exit_ts_ms",
                      "entry_price","exit_price","gross_edge_bps","completed"], trows)
    drows = []
    for d,mean in metrics["daily_means_bps"].items():
        vals = [e["gross_edge_bps"] for e in events if e.get("completed") and e["date"]==d]
        drows.append([d, len(vals), mean, sum(vals), int(mean>0)])
    write_csv_atomic(outdir / "sc001_e004_daily_metrics.csv",
                     ["date","completed_trades","mean_gross_edge_bps","sum_gross_edge_bps","positive_mean"], drows)
    aggregate = {
        "stage": STAGE, "phase": phase, "primary_id": cfg["primary_id"],
        "primary_metrics": metrics,
        "latency_500ms_metrics": stress500,
        "latency_1000ms_metrics": stress1000,
        "simulation_meta": sim_meta,
        "indicator_meta": indicator_meta,
        "gates": gate_rows,
        "terminal_status": terminal,
    }
    atomic_json(outdir / "sc001_e004_aggregate_metrics.json", aggregate)
    ident = runtime_identity(cfg_path)
    state = {
        "stage": STAGE, "phase": phase, "protocol_version": "1.0",
        "preflight_spec_version": "1.1", "terminal_status": terminal,
        **ident,
        "q2_accessed": False, "validation_or_final_accessed": False,
        "l2_accessed": False, "tfi_used": False, "flow_impulse_used": False,
    }
    atomic_json(outdir / "sc001_e004_run_state.json", state)
    summary = [
        f"# SC001-E004 {phase.upper()}",
        "",
        f"Terminal status: `{terminal}`",
        f"Primary configuration: `{cfg['primary_id']}`",
        f"Decisions: {metrics['decisions']}",
        f"Completed: {metrics['completed_trades']}",
        f"Mean gross edge: {metrics['mean_bps']}",
        f"Median gross edge: {metrics['median_bps']}",
        f"Trimmed mean gross edge: {metrics['trimmed_mean_bps']}",
        "",
        "All gates must pass. Diagnostic variants cannot alter this terminal verdict.",
    ]
    atomic_text(outdir / "sc001_e004_summary.md", "\n".join(summary)+"\n")

def run_phase(phase: str, cfg_path: Path) -> str:
    cfg = load_config(cfg_path)
    require_preflight_pass(cfg_path, cfg)
    if phase == "confirmation":
        require_confirmation_gate(cfg, cfg_path)
    phase_cfg = cfg[phase]
    labels = required_labels_for_phase(phase, cfg)
    manifest = source_manifest(cfg, labels)
    for d in sorted(labels):
        verify_archive_identity(manifest[d], full_crc=True)
    stream = load_stream(phase_cfg["indicator_warmup_start"], phase_cfg["end"], cfg, manifest)
    indicators, indicator_meta = build_minute_indicators(stream, cfg)
    events, sim_meta = simulate_primary(
        stream, indicators, cfg, phase_cfg["start"], phase_cfg["end"], calculate_alpha=True
    )
    stress500_events = replay_latency(stream, events, cfg, 500, calculate_alpha=True)
    stress1000_events = replay_latency(stream, events, cfg, 1000, calculate_alpha=True)
    metrics = scenario_metrics(events, cfg, include_bootstrap=True)
    s500 = scenario_metrics(stress500_events, cfg, include_bootstrap=False)
    s1000 = scenario_metrics(stress1000_events, cfg, include_bootstrap=False)
    passed, gates = evaluate_gates(phase, metrics, s500, s1000, sim_meta, cfg)
    terminal = (
        "E004_DISCOVERY_PASS_OPEN_CONFIRMATION_ONCE" if phase=="discovery" and passed
        else "E004_DISCOVERY_FAIL" if phase=="discovery"
        else "E004_CONFIRMATION_PASS_OPEN_L2_PROTOCOL_FREEZE" if passed
        else "E004_CONFIRMATION_FAIL"
    )
    outdir = output_root_for_phase(cfg, phase)
    ensure_new_output_dir(outdir)
    write_phase_artifacts(outdir, phase, cfg_path, cfg, manifest, events, metrics, s500, s1000,
                          sim_meta, gates, terminal, indicator_meta)
    print(terminal)
    return terminal

def diagnostic_variants(cfg: dict) -> list[tuple[str,dict]]:
    out = []
    for x in cfg["diagnostics"]["compression_window_minutes"]:
        out.append((f"W{x}", {"window_minutes": int(x)}))
    for x in cfg["diagnostics"]["compression_percentile"]:
        out.append((f"Q{int(round(x*100))}", {"percentile": float(x)}))
    for x in cfg["diagnostics"]["breakout_buffer_bps"]:
        out.append((f"B{x:g}", {"breakout_buffer_bps": float(x)}))
    for x in cfg["diagnostics"]["holding_minutes"]:
        out.append((f"H{x}", {"holding_minutes": int(x)}))
    if len(out) != 8:
        fail("diagnostic neighborhood must contain exactly 8 one-factor variants")
    return out

def run_diagnostics(phase: str, cfg_path: Path) -> None:
    cfg = load_config(cfg_path)
    root = output_root_for_phase(cfg, phase)
    state = load_json(root / "sc001_e004_run_state.json")
    allowed = {
        "E004_DISCOVERY_FAIL","E004_DISCOVERY_PASS_OPEN_CONFIRMATION_ONCE",
        "E004_CONFIRMATION_FAIL","E004_CONFIRMATION_PASS_OPEN_L2_PROTOCOL_FREEZE"
    }
    if state.get("terminal_status") not in allowed:
        fail("diagnostics blocked: primary terminal verdict absent")
    phase_cfg = cfg[phase]
    labels = required_labels_for_phase(phase, cfg)
    manifest = source_manifest(cfg, labels)
    stream = load_stream(phase_cfg["indicator_warmup_start"], phase_cfg["end"], cfg, manifest)
    rows = []
    for name, change in diagnostic_variants(cfg):
        inds, _ = build_minute_indicators(
            stream, cfg,
            window_minutes=change.get("window_minutes"),
            percentile=change.get("percentile"),
        )
        ev, _ = simulate_primary(
            stream, inds, cfg, phase_cfg["start"], phase_cfg["end"],
            breakout_buffer_bps=change.get("breakout_buffer_bps"),
            holding_minutes=change.get("holding_minutes"),
            calculate_alpha=True,
        )
        m = scenario_metrics(ev, cfg, include_bootstrap=False)
        rows.append({
            "variant": name, "single_change": change,
            "completed_trades": m["completed_trades"], "mean_bps": m["mean_bps"],
            "median_bps": m["median_bps"], "trimmed_mean_bps": m["trimmed_mean_bps"],
            "non_promotional": True,
        })
    atomic_json(root / "sc001_e004_diagnostics_read_only.json", {
        "phase": phase, "primary_terminal_status_unchanged": state["terminal_status"],
        "variants": rows, "cannot_rescue_primary": True,
    })

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["discovery","confirmation","diagnostics"])
    ap.add_argument("--phase", choices=["discovery","confirmation"], default="discovery")
    ap.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    args = ap.parse_args()
    cfg_path = Path(args.config).expanduser().resolve()
    if args.mode in {"discovery","confirmation"}:
        run_phase(args.mode, cfg_path)
    else:
        run_diagnostics(args.phase, cfg_path)

if __name__ == "__main__":
    main()
