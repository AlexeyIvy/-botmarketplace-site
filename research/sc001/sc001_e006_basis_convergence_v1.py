"""SC001-E006 frozen same-venue SPOT/perpetual basis-convergence engine.

Implements:
  docs/research/sc001-e006-spot-perp-basis-convergence-executable-protocol-v1.0.md

Discovery/confirmation are fail-closed behind a matching E006_PREFLIGHT_PASS.
No L2, no Q2, no Validation/Final, no TFI/FLOW_IMPULSE/E004 filters.
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
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path

STAGE = "SC001-E006-SPOT-PERP-BASIS-CONVERGENCE"
ENGINE_VERSION = "1.0"
PROTOCOL_PATH = "docs/research/sc001-e006-spot-perp-basis-convergence-executable-protocol-v1.0.md"
PREFLIGHT_SPEC_PATH = "docs/research/sc001-e006-implementation-preflight-spec-v1.0.md"
DEFAULT_CONFIG_PATH = Path(__file__).with_name("sc001_e006_config_v1_0.json")

UTC = timezone.utc
DAY_MS = 86_400_000
EXPECTED_HEADER = ["instrument_name", "trade_id", "side", "price", "size", "created_time"]

def fail(msg: str) -> None:
    raise RuntimeError(msg)

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

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing required JSON: {path}")
    x = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x, dict):
        fail(f"JSON object expected: {path}")
    return x

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

def repo_root_from_file() -> Path:
    return Path(__file__).resolve().parents[2]

def git_commit(repo_root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None

def load_config(path: Path = DEFAULT_CONFIG_PATH) -> dict:
    cfg = load_json(path)
    if cfg.get("experiment") != "SC001-E006":
        fail("wrong E006 experiment config")
    if cfg.get("protocol_version") != "1.0":
        fail("wrong E006 protocol version")
    if cfg.get("primary_id") != "E006_POSBASIS_G10_VWAP10_LB6H_TRIG50_EXIT10_LAT500_H30_CAP4":
        fail("wrong E006 primary identifier")
    fw = cfg.get("firewalls") or {}
    if fw.get("primary_positive_basis_only") is not True:
        fail("primary sign firewall mismatch")
    for k in ("use_tfi","use_flow_impulse","use_e004_compression","l2","q2","validation","final"):
        if fw.get(k) is not False:
            fail(f"firewall config mismatch: {k}")
    return cfg

def data_roots() -> dict[str, Path]:
    root = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
    return {
        "root": root,
        "spot_root": root / "SC001_E006_SPOT_FEASIBILITY",
        "swap_root": root / "SC001_E003_OKX_MARCH_TRADES",
        "e006_root": root / "SC001_E006",
    }

def required_labels_for_phase(phase: str, cfg: dict) -> tuple[str, ...]:
    if phase == "discovery":
        start = cfg["discovery"]["start"]
        end = cfg["discovery"]["end"]
    elif phase == "confirmation":
        start = cfg["confirmation"]["warmup_start"]
        end = cfg["confirmation"]["end"]
    else:
        fail(f"bad phase: {phase}")
    labels = list(iter_dates(start, end))
    labels.append(next_day_text(end))
    return tuple(labels)

def spot_manifest(labels: tuple[str, ...]) -> dict[str, dict]:
    p = data_roots()
    body = load_json(p["spot_root"] / "sc001_e006_spot_body_integrity_report.json")
    if body.get("status") != "E006_SPOT_BODY_INTEGRITY_PASS":
        fail("SPOT body-integrity stage is not PASS")
    for k in ("basis_calculated","returns_calculated","pnl_calculated","l2_accessed","q2_accessed","validation_or_final_accessed"):
        if body.get(k) is not False:
            fail(f"SPOT body firewall mismatch: {k}")
    rows = body.get("archives") or []
    out = {}
    for row in rows:
        d = row.get("date_label")
        if d not in labels:
            continue
        fn = row.get("filename")
        b = row.get("bytes")
        digest = row.get("sha256")
        if not isinstance(fn, str) or not isinstance(b, int) or b <= 0 or not isinstance(digest, str) or len(digest) != 64:
            fail(f"bad SPOT archive identity: {d}")
        out[d] = {"date": d, "filename": fn, "bytes": b, "sha256": digest, "path": p["spot_root"] / "archives" / fn}
    if set(out) != set(labels):
        fail(f"SPOT label mismatch; missing={sorted(set(labels)-set(out))}")
    return out

def swap_manifest(labels: tuple[str, ...]) -> dict[str, dict]:
    p = data_roots()
    rep = load_json(p["swap_root"] / "sc001_e003_okx_march_trade_stage_report.json")
    if rep.get("stage") != "SC001-E003-OKX-MARCH-TRADE-STAGE" or rep.get("status") != "PASS":
        fail("SWAP March source stage is not PASS")
    if rep.get("q2_market_data_body_accessed") is not False or rep.get("validation_or_final_accessed") is not False:
        fail("SWAP protected-data firewall mismatch")
    if rep.get("alpha_calculated") is not False or rep.get("pnl_calculated") is not False:
        fail("SWAP alpha/P&L firewall mismatch")
    out = {}
    for row in rep.get("archives") or []:
        d = row.get("date")
        if d not in labels:
            continue
        fn = row.get("filename")
        b = row.get("bytes")
        digest = row.get("sha256")
        if not isinstance(fn, str) or not isinstance(b, int) or b <= 0 or not isinstance(digest, str) or len(digest) != 64:
            fail(f"bad SWAP archive identity: {d}")
        out[d] = {"date": d, "filename": fn, "bytes": b, "sha256": digest, "path": p["swap_root"] / "archives" / fn}
    if set(out) != set(labels):
        fail(f"SWAP label mismatch; missing={sorted(set(labels)-set(out))}")
    return out

def verify_archive(meta: dict) -> None:
    p = Path(meta["path"])
    if not p.exists() or p.stat().st_size != int(meta["bytes"]):
        fail(f"archive existence/size mismatch: {p}")
    if sha256_file(p) != meta["sha256"]:
        fail(f"archive SHA mismatch: {p.name}")
    with zipfile.ZipFile(p, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            fail(f"ZIP CRC failure {p.name}: {bad}")
        members = [m for m in zf.infolist() if not m.is_dir()]
        if len(members) != 1:
            fail(f"unexpected ZIP member count {p.name}: {len(members)}")

def _iter_rows(path: Path, instrument: str):
    with zipfile.ZipFile(path, "r") as zf:
        members = [m for m in zf.infolist() if not m.is_dir()]
        if len(members) != 1:
            fail(f"unexpected ZIP member count: {path.name}")
        with zf.open(members[0], "r") as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            reader = csv.reader(text)
            if next(reader, None) != EXPECTED_HEADER:
                fail(f"header mismatch: {path.name}")
            prev_ts = prev_tid = None
            for rownum, row in enumerate(reader, start=2):
                if not row:
                    continue
                if len(row) != 6:
                    fail(f"malformed row {path.name}:{rownum}")
                inst, tid_txt, _side, ptxt, stxt, ts_txt = row
                if inst != instrument:
                    fail(f"instrument mismatch {path.name}:{rownum}: {inst}")
                try:
                    tid = int(tid_txt)
                    px = float(ptxt)
                    sz = float(stxt)
                    ts = parse_ts_ms(ts_txt)
                except Exception as exc:
                    raise RuntimeError(f"parse failure {path.name}:{rownum}") from exc
                if not math.isfinite(px) or px <= 0 or not math.isfinite(sz) or sz <= 0:
                    fail(f"invalid price/size {path.name}:{rownum}")
                if prev_ts is not None and ts < prev_ts:
                    fail(f"source timestamp reversal {path.name}:{rownum}")
                if prev_tid is not None and tid <= prev_tid:
                    fail(f"source trade-id duplicate/backward {path.name}:{rownum}")
                prev_ts, prev_tid = ts, tid
                yield ts, tid, px, sz

def load_leg_stream(instrument: str, manifest: dict[str, dict], start: str, end: str) -> dict:
    lo = date_ms(start)
    hi = date_ms(end) + DAY_MS
    ts = array("q")
    px = array("d")
    sz = array("d")
    last_ts = last_tid = None
    for d in sorted(manifest):
        for t, tid, p, s in _iter_rows(Path(manifest[d]["path"]), instrument):
            if lo <= t < hi:
                if last_ts is not None and t < last_ts:
                    fail(f"stitched timestamp reversal {instrument}")
                if last_tid is not None and tid <= last_tid:
                    fail(f"stitched trade-id duplicate/backward {instrument}")
                last_ts, last_tid = t, tid
                ts.append(t); px.append(p); sz.append(s)
    if not ts:
        fail(f"empty stream for {instrument}")
    n_minutes = (hi - lo) // 60_000
    seen = bytearray(n_minutes)
    for t in ts:
        seen[(int(t)-lo)//60_000] = 1
    if sum(seen) != n_minutes:
        fail(f"minute coverage failure {instrument}: {sum(seen)}/{n_minutes}")
    return {"instrument": instrument, "start_ms": lo, "end_ms": hi, "timestamps": ts, "prices": px, "sizes": sz}

def build_10s_vwap(stream: dict, grid_ms: int) -> tuple[list[float | None], list[int]]:
    lo = int(stream["start_ms"])
    hi = int(stream["end_ms"])
    n = (hi-lo)//grid_ms
    pv = [0.0]*n
    sv = [0.0]*n
    cnt = [0]*n
    ts = stream["timestamps"]; px = stream["prices"]; sz = stream["sizes"]
    for i in range(len(ts)):
        k = (int(ts[i])-lo)//grid_ms
        if 0 <= k < n:
            s = float(sz[i]); p = float(px[i])
            pv[k] += p*s
            sv[k] += s
            cnt[k] += 1
    out: list[float | None] = [None]*n
    for k in range(n):
        if cnt[k] > 0 and sv[k] > 0:
            out[k] = pv[k]/sv[k]
    return out, cnt

def basis_bps(spot: float, perp: float) -> float:
    if not (math.isfinite(spot) and math.isfinite(perp) and spot > 0 and perp > 0):
        fail("invalid basis inputs")
    return 10_000.0*(perp/spot - 1.0)

def ordinary_median(sorted_vals: list[float]) -> float:
    n = len(sorted_vals)
    if n <= 0:
        fail("median of empty")
    if n % 2:
        return float(sorted_vals[n//2])
    return float((sorted_vals[n//2-1]+sorted_vals[n//2])/2.0)

def add_sorted(xs: list[float], v: float) -> None:
    bisect.insort(xs, v)

def remove_sorted(xs: list[float], v: float) -> None:
    i = bisect.bisect_left(xs, v)
    if i >= len(xs) or xs[i] != v:
        fail("rolling sorted state corruption")
    xs.pop(i)

def build_basis_state(spot_vwap, perp_vwap, cfg: dict) -> tuple[list[dict], dict]:
    if len(spot_vwap) != len(perp_vwap):
        fail("VWAP vector length mismatch")
    look = int(cfg["baseline_lookback_points"])
    min_valid = int(cfg["baseline_min_valid_points"])
    q: deque[float | None] = deque()
    sorted_valid: list[float] = []
    records: list[dict] = []
    valid_current = baseline_eligible = 0
    for k in range(len(spot_vwap)):
        cur_basis = None
        if spot_vwap[k] is not None and perp_vwap[k] is not None:
            cur_basis = basis_bps(float(spot_vwap[k]), float(perp_vwap[k]))
            valid_current += 1
        baseline = None
        dis = None
        eligible = len(q) == look and len(sorted_valid) >= min_valid and cur_basis is not None
        if eligible:
            baseline = ordinary_median(sorted_valid)
            dis = cur_basis - baseline
            baseline_eligible += 1
        records.append({"k": k, "basis_bps": cur_basis, "baseline_bps": baseline, "dislocation_bps": dis, "eligible": eligible})
        q.append(cur_basis)
        if cur_basis is not None:
            add_sorted(sorted_valid, cur_basis)
        if len(q) > look:
            old = q.popleft()
            if old is not None:
                remove_sorted(sorted_valid, old)
    return records, {"scheduled_points": len(records), "valid_current_points": valid_current, "baseline_eligible_points": baseline_eligible}

def build_trigger_candidates(records: list[dict], start_ms: int, cfg: dict,
                             perf_start: str, perf_end: str) -> list[dict]:
    grid = int(cfg["grid_ms"])
    trig = float(cfg["trigger_dislocation_bps"])
    lo = date_ms(perf_start)
    hi = date_ms(perf_end) + DAY_MS
    latest_clock = parse_clock_ms(cfg["latest_entry_decision_utc"])
    out = []
    for k in range(1, len(records)):
        r = records[k]; prev = records[k-1]
        t = start_ms + (k+1)*grid
        if not (lo <= t < hi):
            continue
        if (t - date_ms(day_text(t))) > latest_clock:
            continue
        if not (prev.get("eligible") and r.get("eligible")):
            continue
        pd = prev.get("dislocation_bps"); cd = r.get("dislocation_bps")
        if pd is None or cd is None:
            continue
        if pd < trig and cd >= trig:
            out.append({
                "trigger_k": k,
                "trigger_ts": t,
                "date": day_text(t),
                "frozen_baseline_bps": float(r["baseline_bps"]),
                "trigger_basis_bps": float(r["basis_bps"]),
                "trigger_dislocation_bps": float(cd),
            })
    return out

def first_trade_at_or_after(ts: array, target: int) -> int | None:
    i = bisect.bisect_left(ts, target)
    return None if i >= len(ts) else i

def proxy_leg(stream: dict, target: int, tolerance_ms: int, day_end: int) -> tuple[int,int,float] | None:
    ts = stream["timestamps"]; px = stream["prices"]
    i = first_trade_at_or_after(ts, target)
    if i is None:
        return None
    t = int(ts[i])
    if t > target + tolerance_ms or t >= day_end:
        return None
    return i, t, float(px[i])

def ceil_grid(ts_ms: int, origin_ms: int, grid_ms: int) -> int:
    if ts_ms <= origin_ms:
        return origin_ms
    n = (ts_ms-origin_ms + grid_ms - 1)//grid_ms
    return origin_ms + n*grid_ms

def find_exit_decision(event: dict, records: list[dict], global_start_ms: int,
                       pair_open_ts: int, cfg: dict) -> tuple[int,str]:
    grid = int(cfg["grid_ms"])
    max_hold = int(cfg["max_hold_ms"])
    exit_thr = float(cfg["exit_dislocation_bps"])
    frozen = float(event["frozen_baseline_bps"])
    time_exit = ceil_grid(pair_open_ts + max_hold, global_start_ms, grid)
    k0 = max(0, (pair_open_ts - global_start_ms)//grid)
    k1 = min(len(records)-1, (time_exit - global_start_ms)//grid)
    for k in range(k0, k1+1):
        t = global_start_ms + (k+1)*grid
        if t <= pair_open_ts:
            continue
        if t >= time_exit:
            break
        b = records[k].get("basis_bps")
        if b is not None and (float(b)-frozen) <= exit_thr:
            return t, "convergence"
    return time_exit, "time"

def simulate_primary(spot_stream: dict, perp_stream: dict, records: list[dict],
                     candidates: list[dict], cfg: dict, latency_ms: int,
                     calculate_alpha: bool = True) -> tuple[list[dict],dict]:
    tol = int(cfg["proxy_tolerance_ms"])
    cooldown = int(cfg["cooldown_ms"])
    max_daily = int(cfg["max_entry_decisions_per_day"])
    start_ms = int(spot_stream["start_ms"])
    available_at = -1
    locked_day = None
    day_decisions: dict[str,int] = {}
    events = []
    skipped_busy = skipped_locked = 0
    entry_incomplete = exit_incomplete = 0
    max_concurrent = 0

    for c in candidates:
        t = int(c["trigger_ts"]); d = c["date"]; ds = date_ms(d); de = ds + DAY_MS
        if locked_day == d:
            skipped_locked += 1; continue
        if t < available_at:
            skipped_busy += 1; continue
        n = day_decisions.get(d,0)
        if n >= max_daily:
            locked_day = d; skipped_locked += 1; continue
        n += 1; day_decisions[d] = n
        ev = dict(c)
        ev.update({
            "latency_ms": latency_ms, "completed": False, "entry_complete": False,
            "exit_complete": False, "spot_entry_ts": None, "perp_entry_ts": None,
            "spot_exit_ts": None, "perp_exit_ts": None, "exit_decision_ts": None,
            "exit_reason": None, "pair_open_ts": None, "legging_span_ms": None,
            "paired_gross_edge_bps": None,
        })
        target = t + latency_ms
        se = proxy_leg(spot_stream,target,tol,de)
        pe = proxy_leg(perp_stream,target,tol,de)
        if se is None or pe is None:
            entry_incomplete += 1
            available_at = target + tol + cooldown
            events.append(ev)
            if n >= max_daily: locked_day = d
            continue
        _, set_, sep = se
        _, pet, pep = pe
        pair_open = max(set_,pet)
        ev.update({
            "entry_complete": True, "spot_entry_ts": set_, "perp_entry_ts": pet,
            "pair_open_ts": pair_open, "legging_span_ms": abs(set_-pet),
        })
        exit_decision, reason = find_exit_decision(ev,records,start_ms,pair_open,cfg)
        ev["exit_decision_ts"] = exit_decision; ev["exit_reason"] = reason
        exit_target = exit_decision + latency_ms
        sx = proxy_leg(spot_stream,exit_target,tol,de)
        px = proxy_leg(perp_stream,exit_target,tol,de)
        if sx is None or px is None:
            exit_incomplete += 1
            available_at = de
            locked_day = d
            events.append(ev)
            continue
        _, sxt, sxp = sx
        _, pxt, pxp = px
        ev.update({"exit_complete": True, "spot_exit_ts": sxt, "perp_exit_ts": pxt, "completed": True})
        if calculate_alpha:
            spot_ret = sxp/sep - 1.0
            short_perp_ret = 1.0 - pxp/pep
            ev.update({
                "spot_entry_price": sep, "perp_entry_price": pep,
                "spot_exit_price": sxp, "perp_exit_price": pxp,
                "spot_return": spot_ret, "short_perp_return": short_perp_ret,
                "paired_gross_edge_bps": 10_000.0*(spot_ret + short_perp_ret),
            })
        terminal_ts = max(sxt,pxt)
        available_at = terminal_ts + cooldown
        max_concurrent = max(max_concurrent,1)
        if n >= max_daily: locked_day = d
        events.append(ev)

    return events, {
        "candidate_count": len(candidates),
        "entry_decisions": len(events),
        "skipped_busy": skipped_busy,
        "skipped_day_locked": skipped_locked,
        "entry_incomplete": entry_incomplete,
        "exit_incomplete": exit_incomplete,
        "max_decisions_per_day_observed": max(day_decisions.values(), default=0),
        "max_concurrent_pairs": max_concurrent,
        "daily_decision_counts": dict(sorted(day_decisions.items())),
    }

def replay_latency(primary_events: list[dict], spot_stream: dict, perp_stream: dict,
                   cfg: dict, latency_ms: int, calculate_alpha: bool = True) -> list[dict]:
    tol = int(cfg["proxy_tolerance_ms"])
    out = []
    for p in primary_events:
        d = p["date"]; de = date_ms(d)+DAY_MS
        row = {
            "date": d, "trigger_ts": p["trigger_ts"], "exit_decision_ts": p.get("exit_decision_ts"),
            "exit_reason": p.get("exit_reason"), "completed": False, "paired_gross_edge_bps": None,
            "latency_ms": latency_ms,
        }
        if p.get("exit_decision_ts") is None:
            out.append(row); continue
        et = int(p["trigger_ts"]) + latency_ms
        se = proxy_leg(spot_stream,et,tol,de)
        pe = proxy_leg(perp_stream,et,tol,de)
        if se is None or pe is None:
            out.append(row); continue
        _, _, sep = se; _, _, pep = pe
        xt = int(p["exit_decision_ts"]) + latency_ms
        sx = proxy_leg(spot_stream,xt,tol,de)
        px = proxy_leg(perp_stream,xt,tol,de)
        if sx is None or px is None:
            out.append(row); continue
        _, _, sxp = sx; _, _, pxp = px
        row["completed"] = True
        if calculate_alpha:
            row["paired_gross_edge_bps"] = 10_000.0*((sxp/sep - 1.0) + (1.0 - pxp/pep))
        out.append(row)
    return out

def trimmed_mean(vals: list[float], frac: float=0.10) -> float | None:
    if not vals: return None
    xs = sorted(vals); k = math.floor(frac*len(xs))
    core = xs[k:len(xs)-k] if k else xs
    return float(statistics.fmean(core)) if core else None

def nearest_rank(vals: list[float], q: float) -> float | None:
    if not vals: return None
    xs = sorted(vals)
    i = max(0,min(len(xs)-1,math.ceil(q*len(xs))-1))
    return float(xs[i])

def bootstrap_lcb(events: list[dict], cfg: dict) -> float | None:
    by_day: dict[str,list[float]] = {}
    for e in events:
        v = e.get("paired_gross_edge_bps")
        if e.get("completed") and v is not None:
            by_day.setdefault(e["date"],[]).append(float(v))
    days = sorted(by_day)
    if not days: return None
    b = cfg["bootstrap"]; rng = random.Random(int(b["seed"]))
    means = []
    for _ in range(int(b["resamples"])):
        vals = []
        for _j in days:
            d = rng.choice(days)
            vals.extend(by_day[d])
        means.append(statistics.fmean(vals))
    return nearest_rank(means,float(b["lower_quantile"]))

def scenario_metrics(events: list[dict], cfg: dict, *, bootstrap: bool) -> dict:
    completed = [e for e in events if e.get("completed") and e.get("paired_gross_edge_bps") is not None]
    vals = [float(e["paired_gross_edge_bps"]) for e in completed]
    by_day: dict[str,list[float]] = {}
    legging = []
    convergence = timeex = 0
    for e in completed:
        by_day.setdefault(e["date"],[]).append(float(e["paired_gross_edge_bps"]))
        if e.get("legging_span_ms") is not None: legging.append(float(e["legging_span_ms"]))
        if e.get("exit_reason")=="convergence": convergence += 1
        if e.get("exit_reason")=="time": timeex += 1
    daily_means = {d: statistics.fmean(v) for d,v in sorted(by_day.items())}
    daily_sums = {d: sum(v) for d,v in sorted(by_day.items())}
    denom = sum(abs(v) for v in daily_sums.values())
    shares = sorted((abs(v)/denom for v in daily_sums.values()), reverse=True) if denom>0 else []
    decisions = len(events)
    return {
        "entry_decisions": decisions,
        "completed_pairs": len(completed),
        "completion_rate": len(completed)/decisions if decisions else 0.0,
        "active_days": len(by_day),
        "mean_bps": statistics.fmean(vals) if vals else None,
        "median_bps": statistics.median(vals) if vals else None,
        "trimmed_mean_bps": trimmed_mean(vals),
        "median_daily_mean_bps": statistics.median(daily_means.values()) if daily_means else None,
        "positive_active_days": sum(1 for v in daily_means.values() if v>0),
        "positive_active_day_share": sum(1 for v in daily_means.values() if v>0)/len(daily_means) if daily_means else 0.0,
        "bootstrap_95_lcb_bps": bootstrap_lcb(events,cfg) if bootstrap else None,
        "top1_abs_day_share": shares[0] if shares else 1.0,
        "top3_abs_day_share": sum(shares[:3]) if shares else 1.0,
        "legging_span_ms_p50": nearest_rank(legging,0.50),
        "legging_span_ms_p95": nearest_rank(legging,0.95),
        "legging_span_ms_p99": nearest_rank(legging,0.99),
        "legging_span_ms_max": max(legging) if legging else None,
        "convergence_exit_share": convergence/len(completed) if completed else 0.0,
        "time_exit_share": timeex/len(completed) if completed else 0.0,
        "daily_means_bps": daily_means,
        "daily_sums_bps": daily_sums,
    }

def evaluate_gates(phase: str, metrics: dict, s1000: dict, s2000: dict, sim: dict, cfg: dict) -> tuple[bool,list[dict]]:
    g = cfg[phase]["gates"]; checks=[]
    def add(name,ok,value,rule): checks.append({"gate":name,"pass":bool(ok),"value":value,"rule":rule})
    add("completed_min",metrics["completed_pairs"]>=g["completed_min"],metrics["completed_pairs"],f">= {g['completed_min']}")
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
    add("lat1000_mean",s1000["mean_bps"] is not None and s1000["mean_bps"]>=g["lat1000_mean_bps_min"],s1000["mean_bps"],f">= {g['lat1000_mean_bps_min']}")
    add("lat1000_trim",s1000["trimmed_mean_bps"] is not None and s1000["trimmed_mean_bps"]>=g["lat1000_trimmed_mean_bps_min"],s1000["trimmed_mean_bps"],f">= {g['lat1000_trimmed_mean_bps_min']}")
    add("lat2000_mean",s2000["mean_bps"] is not None and s2000["mean_bps"]>=g["lat2000_mean_bps_min"],s2000["mean_bps"],f">= {g['lat2000_mean_bps_min']}")
    add("lat2000_trim",s2000["trimmed_mean_bps"] is not None and s2000["trimmed_mean_bps"]>=g["lat2000_trimmed_mean_bps_min"],s2000["trimmed_mean_bps"],f">= {g['lat2000_trimmed_mean_bps_min']}")
    add("daily_cap",sim.get("max_decisions_per_day_observed",99)<=cfg["max_entry_decisions_per_day"],sim.get("max_decisions_per_day_observed"),f"<= {cfg['max_entry_decisions_per_day']}")
    add("one_pair",sim.get("max_concurrent_pairs",99)<=1,sim.get("max_concurrent_pairs"),"<= 1")
    return all(x["pass"] for x in checks), checks

def preflight_report_path() -> Path:
    return data_roots()["e006_root"] / "preflight" / "sc001_e006_preflight_report.json"

def require_preflight_pass(cfg_path: Path, cfg: dict) -> dict:
    rep = load_json(preflight_report_path())
    if rep.get("status") != "E006_PREFLIGHT_PASS":
        fail("E006 Discovery/Confirmation blocked: exact E006_PREFLIGHT_PASS absent")
    if rep.get("protocol_version") != "1.0" or rep.get("preflight_spec_version") != "1.0":
        fail("E006 preflight version mismatch")
    if rep.get("config_sha256") != sha256_file(cfg_path):
        fail("E006 preflight config SHA mismatch")
    if rep.get("engine_sha256") != sha256_file(Path(__file__).resolve()):
        fail("E006 preflight engine SHA mismatch")
    return rep

def output_root_for_phase(phase: str) -> Path:
    return data_roots()["e006_root"] / phase

def require_confirmation_gate(cfg_path: Path) -> dict:
    p = output_root_for_phase("discovery") / "sc001_e006_run_state.json"
    rep = load_json(p)
    if rep.get("terminal_status") != "E006_DISCOVERY_PASS_OPEN_CONFIRMATION_ONCE":
        fail("E006 Confirmation blocked: Discovery PASS token absent")
    if rep.get("engine_sha256") != sha256_file(Path(__file__).resolve()):
        fail("E006 Confirmation engine SHA mismatch")
    if rep.get("config_sha256") != sha256_file(cfg_path):
        fail("E006 Confirmation config SHA mismatch")
    return rep

def ensure_new_output_dir(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        fail(f"refusing to overwrite non-empty output directory: {path}")
    path.mkdir(parents=True,exist_ok=True)

def runtime_identity(cfg_path: Path) -> dict:
    return {
        "git_commit": git_commit(repo_root_from_file()),
        "engine_sha256": sha256_file(Path(__file__).resolve()),
        "config_sha256": sha256_file(cfg_path),
        "python": sys.version,
        "platform": platform.platform(),
        "timezone": "UTC",
    }

def write_csv_atomic(path: Path, header: list[str], rows: list[list]) -> None:
    tmp = Path(str(path)+".tmp"); path.parent.mkdir(parents=True,exist_ok=True)
    with tmp.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f); w.writerow(header); w.writerows(rows); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,path)

def write_phase_artifacts(outdir: Path, phase: str, cfg_path: Path, cfg: dict, spot_m: dict, swap_m: dict,
                          events: list[dict], metrics: dict, s1000: dict, s2000: dict, sim: dict,
                          basis_meta: dict, gates: list[dict], terminal: str) -> None:
    atomic_text(outdir/"sc001_e006_frozen_config.json",cfg_path.read_text(encoding="utf-8"))
    atomic_json(outdir/"sc001_e006_input_manifest.json",{
        "spot":[{"date":d,"filename":x["filename"],"bytes":x["bytes"],"sha256":x["sha256"]} for d,x in sorted(spot_m.items())],
        "swap":[{"date":d,"filename":x["filename"],"bytes":x["bytes"],"sha256":x["sha256"]} for d,x in sorted(swap_m.items())],
    })
    rows=[]
    for e in events:
        rows.append([
            e["date"],e["trigger_ts"],e.get("trigger_basis_bps"),e.get("frozen_baseline_bps"),e.get("trigger_dislocation_bps"),
            e.get("spot_entry_ts"),e.get("perp_entry_ts"),e.get("pair_open_ts"),e.get("legging_span_ms"),
            e.get("exit_decision_ts"),e.get("exit_reason"),e.get("spot_exit_ts"),e.get("perp_exit_ts"),
            e.get("spot_entry_price"),e.get("perp_entry_price"),e.get("spot_exit_price"),e.get("perp_exit_price"),
            e.get("paired_gross_edge_bps"),int(bool(e.get("completed")))
        ])
    write_csv_atomic(outdir/"sc001_e006_trades.csv",
        ["date","trigger_ts_ms","trigger_basis_bps","frozen_baseline_bps","trigger_dislocation_bps",
         "spot_entry_ts_ms","perp_entry_ts_ms","pair_open_ts_ms","legging_span_ms","exit_decision_ts_ms","exit_reason",
         "spot_exit_ts_ms","perp_exit_ts_ms","spot_entry_price","perp_entry_price","spot_exit_price","perp_exit_price",
         "paired_gross_edge_bps","completed"],rows)
    drows=[]
    for d,mean in metrics["daily_means_bps"].items():
        vals=[float(e["paired_gross_edge_bps"]) for e in events if e.get("completed") and e["date"]==d]
        drows.append([d,len(vals),mean,sum(vals),int(mean>0)])
    write_csv_atomic(outdir/"sc001_e006_daily_metrics.csv",["date","completed_pairs","mean_gross_edge_bps","sum_gross_edge_bps","positive_mean"],drows)
    aggregate={"stage":STAGE,"phase":phase,"primary_id":cfg["primary_id"],"primary_metrics":metrics,
               "latency_1000ms_metrics":s1000,"latency_2000ms_metrics":s2000,"simulation_meta":sim,
               "basis_meta":basis_meta,"gates":gates,"terminal_status":terminal}
    atomic_json(outdir/"sc001_e006_aggregate_metrics.json",aggregate)
    state={"stage":STAGE,"phase":phase,"protocol_version":"1.0","preflight_spec_version":"1.0","terminal_status":terminal,
           **runtime_identity(cfg_path),"q2_accessed":False,"validation_or_final_accessed":False,"l2_accessed":False,
           "tfi_used":False,"flow_impulse_used":False,"e004_compression_used":False}
    atomic_json(outdir/"sc001_e006_run_state.json",state)
    summary=[f"# SC001-E006 {phase.upper()}","",f"Terminal status: `{terminal}`",f"Primary: `{cfg['primary_id']}`",
             f"Entry decisions: {metrics['entry_decisions']}",f"Completed pairs: {metrics['completed_pairs']}",
             f"Mean paired gross edge: {metrics['mean_bps']}",f"Median paired gross edge: {metrics['median_bps']}",
             f"Trimmed mean: {metrics['trimmed_mean_bps']}","","Diagnostics cannot alter primary verdict."]
    atomic_text(outdir/"sc001_e006_summary.md","\n".join(summary)+"\n")

def run_phase(phase: str, cfg_path: Path) -> str:
    cfg=load_config(cfg_path); require_preflight_pass(cfg_path,cfg)
    if phase=="confirmation": require_confirmation_gate(cfg_path)
    labels=required_labels_for_phase(phase,cfg)
    sm=spot_manifest(labels); wm=swap_manifest(labels)
    for d in labels:
        verify_archive(sm[d]); verify_archive(wm[d])
    if phase=="discovery":
        load_start=cfg["discovery"]["start"]; perf_start=cfg["discovery"]["start"]; perf_end=cfg["discovery"]["end"]
    else:
        load_start=cfg["confirmation"]["warmup_start"]; perf_start=cfg["confirmation"]["start"]; perf_end=cfg["confirmation"]["end"]
    load_end=perf_end
    ss=load_leg_stream(cfg["spot_instrument"],sm,load_start,load_end)
    ws=load_leg_stream(cfg["perp_instrument"],wm,load_start,load_end)
    sv,_=build_10s_vwap(ss,int(cfg["grid_ms"])); wv,_=build_10s_vwap(ws,int(cfg["grid_ms"]))
    records,bmeta=build_basis_state(sv,wv,cfg)
    candidates=build_trigger_candidates(records,int(ss["start_ms"]),cfg,perf_start,perf_end)
    events,sim=simulate_primary(ss,ws,records,candidates,cfg,int(cfg["primary_latency_ms"]),calculate_alpha=True)
    s1e=replay_latency(events,ss,ws,cfg,1000,calculate_alpha=True)
    s2e=replay_latency(events,ss,ws,cfg,2000,calculate_alpha=True)
    m=scenario_metrics(events,cfg,bootstrap=True)
    s1=scenario_metrics(s1e,cfg,bootstrap=False); s2=scenario_metrics(s2e,cfg,bootstrap=False)
    passed,gates=evaluate_gates(phase,m,s1,s2,sim,cfg)
    terminal=("E006_DISCOVERY_PASS_OPEN_CONFIRMATION_ONCE" if phase=="discovery" and passed else
              "E006_DISCOVERY_FAIL" if phase=="discovery" else
              "E006_CONFIRMATION_PASS_OPEN_PAIRED_L2_PROTOCOL_FREEZE" if passed else "E006_CONFIRMATION_FAIL")
    out=output_root_for_phase(phase); ensure_new_output_dir(out)
    write_phase_artifacts(out,phase,cfg_path,cfg,sm,wm,events,m,s1,s2,sim,bmeta,gates,terminal)
    print(terminal)
    return terminal

def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("mode",choices=["discovery","confirmation"])
    ap.add_argument("--config",default=str(DEFAULT_CONFIG_PATH))
    args=ap.parse_args()
    run_phase(args.mode,Path(args.config).expanduser().resolve())

if __name__=="__main__":
    main()
