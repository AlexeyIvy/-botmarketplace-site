"""SC001-E007 frozen extreme-displacement mean-reversion engine.

Implements:
  docs/research/sc001-e007-extreme-displacement-mean-reversion-executable-protocol-v1.0.md
Preflight semantics:
  docs/research/sc001-e007-implementation-preflight-spec-v1.0.md

Discovery/confirmation are fail-closed behind matching E007_PREFLIGHT_PASS.
No L2/Q2/Validation/Final and no E002/E003/E004/E006 auxiliary features.
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

STAGE = "SC001-E007-EXTREME-DISPLACEMENT-MEAN-REVERSION"
ENGINE_VERSION = "1.0"
PROTOCOL_PATH = "docs/research/sc001-e007-extreme-displacement-mean-reversion-executable-protocol-v1.0.md"
PREFLIGHT_SPEC_PATH = "docs/research/sc001-e007-implementation-preflight-spec-v1.0.md"
DEFAULT_CONFIG_PATH = Path(__file__).with_name("sc001_e007_config_v1_0.json")
UTC = timezone.utc
DAY_MS = 86_400_000
EXPECTED_HEADER = ["instrument_name", "trade_id", "side", "price", "size", "created_time"]

def fail(msg: str) -> None:
    raise RuntimeError(msg)

def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        f.write(text); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)

def atomic_json(path: Path, obj: object) -> None:
    atomic_text(path, json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_json(path: Path) -> dict:
    if not path.exists(): fail(f"missing required JSON: {path}")
    x = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x, dict): fail(f"JSON object expected: {path}")
    return x

def parse_ts_ms(text: str) -> int:
    v = int(str(text).strip()); av = abs(v)
    if av >= 10**17: return v // 1_000_000
    if av >= 10**14: return v // 1_000
    if av >= 10**11: return v
    if av >= 10**9: return v * 1000
    fail(f"unresolved timestamp scale: {text!r}")

def parse_date(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=UTC)

def date_ms(s: str) -> int:
    return int(parse_date(s).timestamp() * 1000)

def next_day_text(s: str) -> str:
    return (parse_date(s) + timedelta(days=1)).strftime("%Y-%m-%d")

def iter_dates(start: str, end: str):
    d = parse_date(start); e = parse_date(end)
    while d <= e:
        yield d.strftime("%Y-%m-%d"); d += timedelta(days=1)

def day_text(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000, tz=UTC).strftime("%Y-%m-%d")

def parse_clock_ms(s: str) -> int:
    hh, mm, rest = s.split(":")
    if "." in rest:
        ss, ms = rest.split("."); ms = (ms + "000")[:3]
    else: ss, ms = rest, "000"
    return (int(hh) * 3600 + int(mm) * 60 + int(ss)) * 1000 + int(ms)

def repo_root_from_file() -> Path:
    return Path(__file__).resolve().parents[2]

def git_commit(repo_root: Path) -> str | None:
    try:
        return subprocess.check_output(["git", "-C", str(repo_root), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception: return None

def load_config(path: Path = DEFAULT_CONFIG_PATH) -> dict:
    cfg = load_json(path)
    if cfg.get("experiment") != "SC001-E007": fail("wrong E007 experiment config")
    if cfg.get("protocol_version") != "1.0": fail("wrong E007 protocol version")
    if cfg.get("primary_id") != "E007_REV_G5_W60_T80_R50_LAT500_H10_CAP4": fail("wrong E007 primary identifier")
    if cfg.get("grid_ms") != 5000 or cfg.get("anchor_offset_buckets") != 12: fail("grid/anchor config mismatch")
    if float(cfg.get("displacement_threshold_bps")) != 80.0: fail("threshold config mismatch")
    if float(cfg.get("retracement_fraction")) != 0.5: fail("retracement config mismatch")
    fw = cfg.get("firewalls") or {}
    if fw.get("reversal_only") is not True or fw.get("diagnostic_grid") is not False: fail("reversal/diagnostic firewall mismatch")
    for k in ("use_tfi","use_flow_impulse","use_e004_compression","use_e006_basis","l2","q2","validation","final"):
        if fw.get(k) is not False: fail(f"firewall config mismatch: {k}")
    return cfg

def data_roots() -> dict[str, Path]:
    root = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
    return {"root": root, "swap_root": root / "SC001_E003_OKX_MARCH_TRADES", "e007_root": root / "SC001_E007"}

def required_labels_for_phase(phase: str, cfg: dict) -> tuple[str, ...]:
    if phase == "discovery": start, end = cfg["discovery"]["start"], cfg["discovery"]["end"]
    elif phase == "confirmation": start, end = cfg["confirmation"]["warmup_start"], cfg["confirmation"]["end"]
    else: fail(f"bad phase: {phase}")
    labels = list(iter_dates(start, end)); labels.append(next_day_text(end)); return tuple(labels)

def swap_manifest(labels: tuple[str, ...], cfg: dict) -> dict[str, dict]:
    roots = data_roots(); rep = load_json(roots["swap_root"] / cfg["source_report"])
    if rep.get("stage") != "SC001-E003-OKX-MARCH-TRADE-STAGE" or rep.get("status") != "PASS": fail("SWAP March source stage is not PASS")
    if rep.get("q2_market_data_body_accessed") is not False or rep.get("validation_or_final_accessed") is not False: fail("SWAP protected-data firewall mismatch")
    if rep.get("alpha_calculated") is not False or rep.get("pnl_calculated") is not False: fail("SWAP alpha/P&L firewall mismatch")
    out = {}
    for row in rep.get("archives") or []:
        d = row.get("date")
        if d not in labels: continue
        fn, b, digest = row.get("filename"), row.get("bytes"), row.get("sha256")
        if fn != f"{cfg['instrument']}-trades-{d}.zip": fail(f"bad SWAP filename for {d}")
        if not isinstance(b, int) or b <= 0 or not isinstance(digest, str) or len(digest) != 64: fail(f"bad SWAP manifest identity: {d}")
        out[d] = {"date": d, "filename": fn, "bytes": b, "sha256": digest, "path": roots["swap_root"] / cfg["archive_subdir"] / fn}
    if set(out) != set(labels): fail(f"SWAP label mismatch; missing={sorted(set(labels)-set(out))}")
    return out

def verify_archive(meta: dict) -> None:
    p = Path(meta["path"])
    if not p.exists() or p.stat().st_size != int(meta["bytes"]): fail(f"archive existence/size mismatch: {p}")
    if sha256_file(p) != meta["sha256"]: fail(f"archive SHA mismatch: {p.name}")
    with zipfile.ZipFile(p, "r") as zf:
        bad = zf.testzip()
        if bad is not None: fail(f"ZIP CRC failure {p.name}: {bad}")
        members = [m for m in zf.infolist() if not m.is_dir()]
        if len(members) != 1: fail(f"unexpected ZIP member count {p.name}: {len(members)}")

def _iter_rows(path: Path, instrument: str):
    with zipfile.ZipFile(path, "r") as zf:
        members = [m for m in zf.infolist() if not m.is_dir()]
        if len(members) != 1: fail(f"unexpected ZIP member count: {path.name}")
        with zf.open(members[0], "r") as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", newline=""); reader = csv.reader(text)
            if next(reader, None) != EXPECTED_HEADER: fail(f"header mismatch: {path.name}")
            prev_ts = prev_tid = None
            for rownum, row in enumerate(reader, start=2):
                if not row: continue
                if len(row) != 6: fail(f"malformed row {path.name}:{rownum}")
                inst, tid_txt, _side, ptxt, stxt, ts_txt = row
                if inst != instrument: fail(f"instrument mismatch {path.name}:{rownum}: {inst}")
                try: tid, px, sz, ts = int(tid_txt), float(ptxt), float(stxt), parse_ts_ms(ts_txt)
                except Exception as exc: raise RuntimeError(f"parse failure {path.name}:{rownum}") from exc
                if not math.isfinite(px) or px <= 0 or not math.isfinite(sz) or sz <= 0: fail(f"invalid price/size {path.name}:{rownum}")
                if prev_ts is not None and ts < prev_ts: fail(f"source timestamp reversal {path.name}:{rownum}")
                if prev_tid is not None and tid <= prev_tid: fail(f"source trade-id duplicate/backward {path.name}:{rownum}")
                prev_ts, prev_tid = ts, tid; yield ts, tid, px, sz

def load_stream(manifest: dict[str, dict], cfg: dict, start: str, end: str) -> dict:
    lo, hi = date_ms(start), date_ms(end) + DAY_MS
    ts, px, sz = array("q"), array("d"), array("d"); last_ts = last_tid = None
    for d in sorted(manifest):
        for t, tid, p, s in _iter_rows(Path(manifest[d]["path"]), cfg["instrument"]):
            if lo <= t < hi:
                if last_ts is not None and t < last_ts: fail("stitched timestamp reversal")
                if last_tid is not None and tid <= last_tid: fail("stitched trade-id duplicate/backward")
                last_ts, last_tid = t, tid; ts.append(t); px.append(p); sz.append(s)
    if not ts: fail("empty E007 stream")
    n_minutes = (hi - lo) // 60_000; seen = bytearray(n_minutes)
    for t in ts:
        k = (int(t) - lo) // 60_000
        if 0 <= k < n_minutes: seen[k] = 1
    if sum(seen) != n_minutes: fail(f"minute coverage failure: {sum(seen)}/{n_minutes}")
    return {"start_ms": lo, "end_ms": hi, "timestamps": ts, "prices": px, "sizes": sz}

def build_5s_vwap(stream: dict, grid_ms: int) -> tuple[list[float | None], list[int]]:
    lo, hi = int(stream["start_ms"]), int(stream["end_ms"]); n = (hi-lo)//grid_ms
    pv, sv, cnt = [0.0]*n, [0.0]*n, [0]*n
    ts, px, sz = stream["timestamps"], stream["prices"], stream["sizes"]
    for i in range(len(ts)):
        k = (int(ts[i])-lo)//grid_ms
        if 0 <= k < n:
            p, s = float(px[i]), float(sz[i]); pv[k] += p*s; sv[k] += s; cnt[k] += 1
    vw = [None]*n
    for k in range(n):
        if cnt[k] > 0 and sv[k] > 0: vw[k] = pv[k]/sv[k]
    return vw, cnt

def displacement_bps(anchor: float, current: float) -> float:
    if not (math.isfinite(anchor) and math.isfinite(current) and anchor > 0 and current > 0): fail("invalid displacement inputs")
    return 10_000.0 * (current / anchor - 1.0)

def build_displacement_records(vwap: list[float | None], stream_start_ms: int, cfg: dict) -> tuple[list[dict], dict]:
    off, grid = int(cfg["anchor_offset_buckets"]), int(cfg["grid_ms"]); records = []; valid = 0
    for k in range(len(vwap)):
        t = stream_start_ms + (k + 1) * grid; cur = vwap[k]; anchor = vwap[k-off] if k >= off else None
        if cur is None or anchor is None:
            records.append({"t": t, "valid": False, "anchor": None, "current": None, "disp_bps": None}); continue
        d = displacement_bps(float(anchor), float(cur)); valid += 1
        records.append({"t": t, "valid": True, "anchor": float(anchor), "current": float(cur), "disp_bps": d})
    first_valid = next((r["t"] for r in records if r["valid"]), None)
    return records, {"valid_record_count": valid, "first_valid_ms": first_valid, "total_grid_points": len(records)}

def build_trigger_candidates(records: list[dict], cfg: dict, perf_start: str, perf_end: str) -> list[dict]:
    threshold, frac = float(cfg["displacement_threshold_bps"]), float(cfg["retracement_fraction"])
    lo, hi = date_ms(perf_start), date_ms(perf_end) + DAY_MS; out = []; prev = None
    for r in records:
        t = int(r["t"])
        if not r["valid"]: prev = r; continue
        if prev is None or not prev.get("valid"): prev = r; continue
        pd, d = float(prev["disp_bps"]), float(r["disp_bps"])
        if lo <= t < hi and abs(pd) < threshold and abs(d) >= threshold:
            anchor, current = float(r["anchor"]), float(r["current"]); target = anchor + frac*(current-anchor); direction = -1 if d > 0 else 1
            out.append({"date": day_text(t), "trigger_ts": t, "direction": direction, "trigger_disp_bps": d,
                        "anchor_price": anchor, "trigger_vwap": current, "target_price": target})
        prev = r
    return out

def proxy_leg(stream: dict, target_ts: int, tolerance_ms: int, day_end_ms: int):
    ts = stream["timestamps"]; i = bisect.bisect_left(ts, target_ts)
    if i >= len(ts): return None
    actual = int(ts[i])
    if actual > target_ts + tolerance_ms or actual >= day_end_ms: return None
    return i, actual, float(stream["prices"][i])

def already_reverted(direction: int, price: float, target: float) -> bool:
    return price >= target if direction == 1 else price <= target

def grid_ceiling(ts_ms: int, origin_ms: int, grid_ms: int) -> int:
    if ts_ms <= origin_ms: return origin_ms
    x = ts_ms - origin_ms; return origin_ms + ((x + grid_ms - 1)//grid_ms)*grid_ms

def find_exit_decision(event: dict, records: list[dict], stream_start_ms: int, entry_ts: int, cfg: dict) -> tuple[int, str]:
    grid, max_hold = int(cfg["grid_ms"]), int(cfg["max_hold_ms"]); direction, target = int(event["direction"]), float(event["target_price"])
    first_idx = max(0, (entry_ts-stream_start_ms)//grid); max_decision = grid_ceiling(entry_ts+max_hold, stream_start_ms, grid)
    max_idx = min(len(records)-1, (max_decision-stream_start_ms)//grid - 1)
    for i in range(int(first_idx), max_idx+1):
        r = records[i]; t = int(r["t"])
        if t <= entry_ts or not r["valid"]: continue
        cur = float(r["current"]); hit = cur >= target if direction == 1 else cur <= target
        if hit: return t, "reversion"
    return max_decision, "time"

def simulate_primary(stream: dict, records: list[dict], candidates: list[dict], cfg: dict, latency_ms: int, calculate_alpha: bool = True) -> tuple[list[dict], dict]:
    tol, cooldown, cap = int(cfg["entry_exit_tolerance_ms"]), int(cfg["cooldown_ms"]), int(cfg["max_entry_decisions_per_day"])
    latest = parse_clock_ms(cfg["latest_entry_decision_utc"]); events = []; counts = Counter(); daily = Counter(); available_at = 0; locked_day = None; current_day = None; max_concurrent = 0
    for c in candidates:
        t, d = int(c["trigger_ts"]), c["date"]; ds, de = date_ms(d), date_ms(d)+DAY_MS
        if current_day != d:
            current_day = d; available_at = max(available_at, ds)
            if locked_day != d: locked_day = None
        if locked_day == d: counts["skipped_day_locked"] += 1; continue
        if t < available_at: counts["skipped_busy_or_cooldown"] += 1; continue
        if daily[d] >= cap: counts["skipped_daily_cap"] += 1; continue
        if t-ds > latest: counts["skipped_late"] += 1; continue
        daily[d] += 1; counts["decisions"] += 1
        event = dict(c); event.update({"completed":False,"entry_ts":None,"exit_decision_ts":None,"exit_ts":None,"entry_price":None,"exit_price":None,"gross_edge_bps":None,"exit_reason":None,"incomplete_reason":None})
        entry_target = t + int(latency_ms); leg = proxy_leg(stream, entry_target, tol, de)
        if leg is None:
            event["incomplete_reason"]="entry_missing"; counts["entry_missing"] += 1; available_at = entry_target + tol + cooldown; events.append(event); continue
        _ei, ets, ep = leg
        if already_reverted(int(c["direction"]), ep, float(c["target_price"])):
            event["entry_ts"] = ets; event["entry_price"] = ep if calculate_alpha else None; event["incomplete_reason"]="entry_already_reverted"; counts["entry_already_reverted"] += 1; available_at = ets + cooldown; events.append(event); continue
        event["entry_ts"] = ets
        if calculate_alpha: event["entry_price"] = ep
        exit_decision, reason = find_exit_decision(c, records, int(stream["start_ms"]), ets, cfg); event["exit_decision_ts"], event["exit_reason"] = exit_decision, reason
        if exit_decision >= de:
            event["incomplete_reason"]="exit_day_cross"; counts["exit_day_cross"] += 1; locked_day = d; available_at = de; events.append(event); continue
        xleg = proxy_leg(stream, exit_decision + int(latency_ms), tol, de)
        if xleg is None:
            event["incomplete_reason"]="exit_missing"; counts["exit_missing"] += 1; locked_day = d; available_at = de; events.append(event); continue
        _xi, xts, xp = xleg; event["exit_ts"] = xts; event["completed"] = True
        if calculate_alpha:
            event["exit_price"] = xp; event["gross_edge_bps"] = int(c["direction"]) * 10_000.0 * (xp/ep - 1.0)
        counts["completed"] += 1; available_at = xts + cooldown; max_concurrent = max(max_concurrent,1); events.append(event)
    return events, {**dict(counts), "max_decisions_per_day_observed":max(daily.values(),default=0), "daily_decision_counts":dict(sorted(daily.items())), "max_concurrent_positions":max_concurrent}

def replay_latency(primary_events: list[dict], stream: dict, cfg: dict, latency_ms: int, calculate_alpha: bool = True) -> list[dict]:
    tol = int(cfg["entry_exit_tolerance_ms"]); out = []
    for p in primary_events:
        row = {"date":p["date"],"trigger_ts":p["trigger_ts"],"direction":p["direction"],"target_price":p["target_price"],"completed":False,"entry_ts":None,"exit_decision_ts":p.get("exit_decision_ts"),"exit_ts":None,"gross_edge_bps":None,"incomplete_reason":None}
        if p.get("exit_decision_ts") is None: row["incomplete_reason"] = p.get("incomplete_reason") or "primary_no_exit_decision"; out.append(row); continue
        de = date_ms(p["date"])+DAY_MS; leg = proxy_leg(stream, int(p["trigger_ts"])+int(latency_ms), tol, de)
        if leg is None: row["incomplete_reason"]="entry_missing"; out.append(row); continue
        _ei, ets, ep = leg
        if already_reverted(int(p["direction"]), ep, float(p["target_price"])): row["entry_ts"]=ets; row["incomplete_reason"]="entry_already_reverted"; out.append(row); continue
        if ets >= int(p["exit_decision_ts"]): row["entry_ts"]=ets; row["incomplete_reason"]="entry_after_exit_decision"; out.append(row); continue
        row["entry_ts"] = ets; xleg = proxy_leg(stream, int(p["exit_decision_ts"])+int(latency_ms), tol, de)
        if xleg is None: row["incomplete_reason"]="exit_missing"; out.append(row); continue
        _xi, xts, xp = xleg; row["exit_ts"] = xts; row["completed"] = True
        if calculate_alpha: row["gross_edge_bps"] = int(p["direction"]) * 10_000.0 * (xp/ep - 1.0)
        out.append(row)
    return out

def trimmed_mean(vals: list[float], frac: float = 0.10):
    if not vals: return None
    xs = sorted(vals); k = math.floor(frac*len(xs)); core = xs[k:len(xs)-k] if k else xs
    return float(statistics.fmean(core)) if core else None

def bootstrap_lcb(events: list[dict], cfg: dict):
    by_day = {}
    for e in events:
        if e.get("completed") and e.get("gross_edge_bps") is not None: by_day.setdefault(e["date"],[]).append(float(e["gross_edge_bps"]))
    days = sorted(by_day)
    if not days: return None
    bcfg = cfg["bootstrap"]; rng = random.Random(int(bcfg["seed"])); means = []
    for _ in range(int(bcfg["resamples"])):
        sample = [rng.choice(days) for _ in days]; vals=[]
        for d in sample: vals.extend(by_day[d])
        means.append(statistics.fmean(vals))
    means.sort(); rank=max(1,math.ceil(float(bcfg["lower_quantile"])*len(means))); return float(means[rank-1])

def scenario_metrics(events: list[dict], cfg: dict, include_bootstrap: bool = True) -> dict:
    completed=[e for e in events if e.get("completed") and e.get("gross_edge_bps") is not None]; vals=[float(e["gross_edge_bps"]) for e in completed]; decisions=len(events); by_day={}; by_side={1:[],-1:[]}
    for e in completed:
        v=float(e["gross_edge_bps"]); by_day.setdefault(e["date"],[]).append(v); by_side[int(e["direction"])].append(v)
    daily_means={d:statistics.fmean(v) for d,v in sorted(by_day.items())}; day_sums={d:sum(v) for d,v in sorted(by_day.items())}; denom=sum(abs(v) for v in day_sums.values()); shares=sorted((abs(v)/denom for v in day_sums.values()),reverse=True) if denom>0 else [1.0]; n=len(completed); long_n=len(by_side[1]); short_n=len(by_side[-1])
    return {"decisions":decisions,"completed_trades":n,"completion_rate":n/decisions if decisions else 0.0,"active_days":len(by_day),"mean_bps":statistics.fmean(vals) if vals else None,"median_bps":statistics.median(vals) if vals else None,"trimmed_mean_bps":trimmed_mean(vals),"median_daily_mean_bps":statistics.median(daily_means.values()) if daily_means else None,"positive_active_days":sum(1 for x in daily_means.values() if x>0),"positive_active_day_share":sum(1 for x in daily_means.values() if x>0)/len(daily_means) if daily_means else 0.0,"long_completed":long_n,"short_completed":short_n,"max_side_share":max(long_n,short_n)/n if n else 1.0,"top1_abs_day_share":shares[0] if shares else 1.0,"top3_abs_day_share":sum(shares[:3]) if shares else 1.0,"bootstrap_95_lcb_bps":bootstrap_lcb(events,cfg) if include_bootstrap else None,"daily_means_bps":daily_means,"daily_sums_bps":day_sums}

def evaluate_gates(phase: str, metrics: dict, s1000: dict, s2000: dict, sim: dict, cfg: dict):
    g=cfg[phase]["gates"]; checks=[]
    def add(name,ok,value,rule): checks.append({"gate":name,"pass":bool(ok),"value":value,"rule":rule})
    n=metrics["completed_trades"]
    add("completed_range",g["completed_min"]<=n<=g["completed_max"],n,f"{g['completed_min']} <= completed <= {g['completed_max']}")
    add("active_days",metrics["active_days"]>=g["active_days_min"],metrics["active_days"],f">= {g['active_days_min']}")
    add("completion_rate",metrics["completion_rate"]>=g["completion_rate_min"],metrics["completion_rate"],f">= {g['completion_rate_min']}")
    add("mean_bps",metrics["mean_bps"] is not None and metrics["mean_bps"]>=g["mean_bps_min"],metrics["mean_bps"],f">= {g['mean_bps_min']}")
    add("trimmed_mean_bps",metrics["trimmed_mean_bps"] is not None and metrics["trimmed_mean_bps"]>=g["trimmed_mean_bps_min"],metrics["trimmed_mean_bps"],f">= {g['trimmed_mean_bps_min']}")
    add("median_bps",metrics["median_bps"] is not None and metrics["median_bps"]>=g["median_bps_min"],metrics["median_bps"],f">= {g['median_bps_min']}")
    add("median_daily_mean_bps",metrics["median_daily_mean_bps"] is not None and metrics["median_daily_mean_bps"]>=g["median_daily_mean_bps_min"],metrics["median_daily_mean_bps"],f">= {g['median_daily_mean_bps_min']}")
    add("positive_day_share",metrics["positive_active_day_share"]>=g["positive_active_day_share_min"],metrics["positive_active_day_share"],f">= {g['positive_active_day_share_min']}")
    add("bootstrap_lcb",metrics["bootstrap_95_lcb_bps"] is not None and metrics["bootstrap_95_lcb_bps"]>g["bootstrap_lcb_bps_strict_gt"],metrics["bootstrap_95_lcb_bps"],f"> {g['bootstrap_lcb_bps_strict_gt']}")
    add("top1_concentration",metrics["top1_abs_day_share"]<=g["top1_abs_day_share_max"],metrics["top1_abs_day_share"],f"<= {g['top1_abs_day_share_max']}")
    add("top3_concentration",metrics["top3_abs_day_share"]<=g["top3_abs_day_share_max"],metrics["top3_abs_day_share"],f"<= {g['top3_abs_day_share_max']}")
    add("each_side_count",min(metrics["long_completed"],metrics["short_completed"])>=g["each_side_completed_min"],min(metrics["long_completed"],metrics["short_completed"]),f">= {g['each_side_completed_min']} each")
    add("max_side_share",metrics["max_side_share"]<=g["max_side_share_max"],metrics["max_side_share"],f"<= {g['max_side_share_max']}")
    add("lat1000_mean",s1000["mean_bps"] is not None and s1000["mean_bps"]>=g["lat1000_mean_bps_min"],s1000["mean_bps"],f">= {g['lat1000_mean_bps_min']}")
    add("lat1000_trim",s1000["trimmed_mean_bps"] is not None and s1000["trimmed_mean_bps"]>=g["lat1000_trimmed_mean_bps_min"],s1000["trimmed_mean_bps"],f">= {g['lat1000_trimmed_mean_bps_min']}")
    add("lat2000_mean",s2000["mean_bps"] is not None and s2000["mean_bps"]>=g["lat2000_mean_bps_min"],s2000["mean_bps"],f">= {g['lat2000_mean_bps_min']}")
    add("lat2000_trim",s2000["trimmed_mean_bps"] is not None and s2000["trimmed_mean_bps"]>=g["lat2000_trimmed_mean_bps_min"],s2000["trimmed_mean_bps"],f">= {g['lat2000_trimmed_mean_bps_min']}")
    add("daily_cap",sim.get("max_decisions_per_day_observed",99)<=cfg["max_entry_decisions_per_day"],sim.get("max_decisions_per_day_observed"),f"<= {cfg['max_entry_decisions_per_day']}")
    add("one_position",sim.get("max_concurrent_positions",99)<=1,sim.get("max_concurrent_positions"),"<= 1")
    return all(x["pass"] for x in checks),checks

def preflight_report_path() -> Path:
    return data_roots()["e007_root"] / "preflight" / "sc001_e007_preflight_report.json"

def require_preflight_pass(cfg_path: Path) -> dict:
    rep=load_json(preflight_report_path())
    if rep.get("status") != "E007_PREFLIGHT_PASS": fail("E007 Discovery/Confirmation blocked: exact E007_PREFLIGHT_PASS absent")
    if rep.get("protocol_version") != "1.0" or rep.get("preflight_spec_version") != "1.0": fail("E007 preflight version mismatch")
    if rep.get("config_sha256") != sha256_file(cfg_path): fail("E007 preflight config SHA mismatch")
    if rep.get("engine_sha256") != sha256_file(Path(__file__).resolve()): fail("E007 preflight engine SHA mismatch")
    return rep

def output_root_for_phase(phase: str) -> Path:
    return data_roots()["e007_root"] / phase

def require_confirmation_gate(cfg_path: Path) -> dict:
    rep=load_json(output_root_for_phase("discovery") / "sc001_e007_run_state.json")
    if rep.get("terminal_status") != "E007_DISCOVERY_PASS_OPEN_CONFIRMATION_ONCE": fail("E007 confirmation blocked: Discovery PASS token absent")
    if rep.get("engine_sha256") != sha256_file(Path(__file__).resolve()): fail("confirmation blocked: engine SHA differs from Discovery")
    if rep.get("config_sha256") != sha256_file(cfg_path): fail("confirmation blocked: config SHA differs from Discovery")
    return rep

def ensure_new_output_dir(path: Path) -> None:
    if path.exists() and any(path.iterdir()): fail(f"refusing to overwrite non-empty output directory: {path}")
    path.mkdir(parents=True,exist_ok=True)

def write_csv_atomic(path: Path, header: list[str], rows: list[list]) -> None:
    tmp=Path(str(path)+".tmp"); path.parent.mkdir(parents=True,exist_ok=True)
    with tmp.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f); w.writerow(header); w.writerows(rows); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,path)

def runtime_identity(cfg_path: Path) -> dict:
    return {"python":sys.version,"platform":platform.platform(),"timezone":"UTC","git_commit":git_commit(repo_root_from_file()),"engine_sha256":sha256_file(Path(__file__).resolve()),"config_sha256":sha256_file(cfg_path)}

def write_phase_artifacts(outdir: Path, phase: str, cfg_path: Path, cfg: dict, manifest: dict, events: list[dict], metrics: dict, s1000: dict, s2000: dict, sim: dict, disp_meta: dict, gates: list[dict], terminal: str) -> None:
    atomic_text(outdir/"sc001_e007_frozen_config.json",cfg_path.read_text(encoding="utf-8")); atomic_json(outdir/"sc001_e007_input_manifest.json",{"archives":[{"date":d,"filename":x["filename"],"bytes":x["bytes"],"sha256":x["sha256"]} for d,x in sorted(manifest.items())]})
    rows=[]
    for e in events: rows.append([e["date"],e["trigger_ts"],"LONG" if e["direction"]==1 else "SHORT",e["trigger_disp_bps"],e["anchor_price"],e["trigger_vwap"],e["target_price"],e.get("entry_ts"),e.get("exit_decision_ts"),e.get("exit_ts"),e.get("entry_price"),e.get("exit_price"),e.get("gross_edge_bps"),int(bool(e.get("completed"))),e.get("exit_reason"),e.get("incomplete_reason")])
    write_csv_atomic(outdir/"sc001_e007_trades.csv",["date","trigger_ts_ms","side","trigger_displacement_bps","anchor_vwap","trigger_vwap","retracement_target","entry_ts_ms","exit_decision_ts_ms","exit_ts_ms","entry_price","exit_price","gross_edge_bps","completed","exit_reason","incomplete_reason"],rows)
    drows=[]
    for d,mean in metrics["daily_means_bps"].items():
        vals=[e["gross_edge_bps"] for e in events if e.get("completed") and e["date"]==d]; drows.append([d,len(vals),mean,sum(vals),int(mean>0)])
    write_csv_atomic(outdir/"sc001_e007_daily_metrics.csv",["date","completed_trades","mean_gross_edge_bps","sum_gross_edge_bps","positive_mean"],drows)
    atomic_json(outdir/"sc001_e007_aggregate_metrics.json",{"stage":STAGE,"phase":phase,"primary_id":cfg["primary_id"],"primary_metrics":metrics,"latency_1000ms_metrics":s1000,"latency_2000ms_metrics":s2000,"simulation_meta":sim,"displacement_meta":disp_meta,"gates":gates,"terminal_status":terminal})
    atomic_json(outdir/"sc001_e007_run_state.json",{"stage":STAGE,"phase":phase,"protocol_version":"1.0","preflight_spec_version":"1.0","terminal_status":terminal,**runtime_identity(cfg_path),"q2_accessed":False,"validation_or_final_accessed":False,"l2_accessed":False,"tfi_used":False,"flow_impulse_used":False,"e004_compression_used":False,"e006_basis_used":False})
    atomic_text(outdir/"sc001_e007_summary.md","\n".join([f"# SC001-E007 {phase.upper()}","",f"Terminal status: `{terminal}`",f"Primary configuration: `{cfg['primary_id']}`",f"Decisions: {metrics['decisions']}",f"Completed: {metrics['completed_trades']}",f"Mean gross edge: {metrics['mean_bps']}",f"Median gross edge: {metrics['median_bps']}",f"Trimmed mean gross edge: {metrics['trimmed_mean_bps']}","","No diagnostic grid is authorized for E007 v1.0."])+"\n")

def run_phase(phase: str, cfg_path: Path) -> str:
    cfg=load_config(cfg_path); require_preflight_pass(cfg_path)
    if phase=="confirmation": require_confirmation_gate(cfg_path)
    labels=required_labels_for_phase(phase,cfg); manifest=swap_manifest(labels,cfg)
    for d in labels: verify_archive(manifest[d])
    if phase=="discovery": load_start=cfg["discovery"]["start"]; perf_start=cfg["discovery"]["start"]; perf_end=cfg["discovery"]["end"]
    else: load_start=cfg["confirmation"]["warmup_start"]; perf_start=cfg["confirmation"]["start"]; perf_end=cfg["confirmation"]["end"]
    stream=load_stream(manifest,cfg,load_start,perf_end); vw,_=build_5s_vwap(stream,int(cfg["grid_ms"])); records,disp_meta=build_displacement_records(vw,int(stream["start_ms"]),cfg); candidates=build_trigger_candidates(records,cfg,perf_start,perf_end)
    events,sim=simulate_primary(stream,records,candidates,cfg,int(cfg["primary_latency_ms"]),calculate_alpha=True); s1000_e=replay_latency(events,stream,cfg,1000,calculate_alpha=True); s2000_e=replay_latency(events,stream,cfg,2000,calculate_alpha=True)
    metrics=scenario_metrics(events,cfg,include_bootstrap=True); s1000=scenario_metrics(s1000_e,cfg,include_bootstrap=False); s2000=scenario_metrics(s2000_e,cfg,include_bootstrap=False); passed,gates=evaluate_gates(phase,metrics,s1000,s2000,sim,cfg)
    terminal=("E007_DISCOVERY_PASS_OPEN_CONFIRMATION_ONCE" if phase=="discovery" and passed else "E007_DISCOVERY_FAIL" if phase=="discovery" else "E007_CONFIRMATION_PASS_OPEN_L2_PROTOCOL_FREEZE" if passed else "E007_CONFIRMATION_FAIL")
    outdir=output_root_for_phase(phase); ensure_new_output_dir(outdir); write_phase_artifacts(outdir,phase,cfg_path,cfg,manifest,events,metrics,s1000,s2000,sim,disp_meta,gates,terminal); print(terminal); return terminal

def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("mode",choices=["discovery","confirmation"]); ap.add_argument("--config",default=str(DEFAULT_CONFIG_PATH)); args=ap.parse_args(); run_phase(args.mode,Path(args.config).expanduser().resolve())

if __name__=="__main__":
    main()
