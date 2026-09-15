"""SC001-E003 rare flow-impulse economics-first screen.

Implements the frozen E003 v0.2 trade-price protocol on already-qualified
March-2024 OKX BTC-USDT-SWAP archives. Discovery and confirmation are separate
modes; confirmation is fail-closed behind a terminal Discovery PASS.

No L2, no Q2, no formal Validation/Final, no E002 TFI filter.
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
import zipfile
from array import array
from collections import deque
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

STAGE = "SC001-E003-FLOW-IMPULSE-CONTINUATION"
VERSION = "0.1"
PROTOCOL = "docs/research/sc001-e003-flow-impulse-continuation-protocol-v0.2.md"
IMPLEMENTATION_FREEZE = "docs/research/sc001-e003-flow-impulse-implementation-freeze-v0.1.md"
INST = "BTC-USDT-SWAP"
EXPECTED_HEADER = ["instrument_name", "trade_id", "side", "price", "size", "created_time"]

GRID_MS = 5_000
ROLLING_N = 720
QS = (("q99", 0.99), ("q99.5", 0.995), ("q99.75", 0.9975))
DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
SOURCE_ROOT = DATA_ROOT / "SC001_E003_OKX_MARCH_TRADES"
ARCHIVES = SOURCE_ROOT / "archives"
SOURCE_REPORT = SOURCE_ROOT / "sc001_e003_okx_march_trade_stage_report.json"
WORKSPACE = DATA_ROOT / "SC001_E003_FLOW_IMPULSE"
DISCOVERY_ROOT = WORKSPACE / "discovery"
CONFIRM_ROOT = WORKSPACE / "confirmation"
DISCOVERY_REPORT = DISCOVERY_ROOT / "sc001_e003_discovery_report.json"
DISCOVERY_SUMMARY = DISCOVERY_ROOT / "sc001_e003_discovery_summary.md"
CONFIRM_REPORT = CONFIRM_ROOT / "sc001_e003_confirmation_report.json"
CONFIRM_SUMMARY = CONFIRM_ROOT / "sc001_e003_confirmation_summary.md"

DISCOVERY_DAYS = tuple(f"2024-03-{d:02d}" for d in range(1, 21))
CONFIRM_DAYS = tuple(f"2024-03-{d:02d}" for d in range(21, 31))
REQUIRED_ARCHIVE_DAYS = tuple(f"2024-03-{d:02d}" for d in range(1, 32))

SCENARIOS = (
    ("q99", 250, 60_000, "diagnostic_threshold"),
    ("q99.5", 250, 60_000, "primary"),
    ("q99.75", 250, 60_000, "diagnostic_threshold"),
    ("q99.5", 500, 60_000, "stress_latency"),
    ("q99.5", 1000, 60_000, "diagnostic_latency"),
    ("q99.5", 250, 30_000, "diagnostic_horizon"),
    ("q99.5", 250, 120_000, "diagnostic_horizon"),
)


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        f.write(text)
        f.flush(); os.fsync(f.fileno())
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
    v = int(text.strip()); av = abs(v)
    if av >= 10**17: return v // 1_000_000
    if av >= 10**14: return v // 1_000
    if av >= 10**11: return v
    if av >= 10**9: return v * 1000
    fail(f"unresolved timestamp scale: {text!r}")


def utc_bounds(date_text: str) -> tuple[int, int]:
    d = datetime.strptime(date_text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    lo = int(d.timestamp() * 1000)
    return lo, lo + 86_400_000


def next_day(date_text: str) -> str:
    return (datetime.strptime(date_text, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")


def median_sorted(xs: list[float]) -> float:
    n = len(xs)
    if n == 0: fail("median of empty list")
    if n % 2: return float(xs[n // 2])
    return float((xs[n // 2 - 1] + xs[n // 2]) / 2.0)


def nearest_rank(sorted_xs: list[float], q: float) -> float:
    if len(sorted_xs) != ROLLING_N: fail("nearest-rank window length mismatch")
    return float(sorted_xs[math.ceil(q * ROLLING_N) - 1])


def add_sorted(q: deque[float], xs: list[float], value: float) -> None:
    bisect.insort(xs, value); q.append(value)
    if len(q) > ROLLING_N:
        old = q.popleft(); i = bisect.bisect_left(xs, old)
        if i >= len(xs) or xs[i] != old: fail("rolling sorted state corruption")
        xs.pop(i)


def percentile(vals: list[float], q: float) -> float | None:
    if not vals: return None
    xs = sorted(vals)
    if len(xs) == 1: return float(xs[0])
    pos = q * (len(xs) - 1); lo = math.floor(pos); hi = math.ceil(pos)
    if lo == hi: return float(xs[lo])
    w = pos - lo
    return float(xs[lo] * (1 - w) + xs[hi] * w)


def source_manifest() -> dict[str, dict]:
    rep = load_json(SOURCE_REPORT)
    if rep.get("stage") != "SC001-E003-OKX-MARCH-TRADE-STAGE" or rep.get("status") != "PASS":
        fail("March source stage is not PASS")
    if rep.get("q2_market_data_body_accessed") is not False or rep.get("validation_or_final_accessed") is not False:
        fail("source-stage firewall mismatch")
    if rep.get("alpha_calculated") is not False or rep.get("pnl_calculated") is not False:
        fail("source-stage alpha/P&L firewall mismatch")
    rows = rep.get("archives") or []
    if len(rows) != 31: fail(f"source manifest archive count mismatch: {len(rows)}")
    out = {}
    for row in rows:
        if not isinstance(row, dict): fail("source manifest row type mismatch")
        d = row.get("date"); fn = row.get("filename"); size = row.get("bytes"); digest = row.get("sha256")
        if d not in REQUIRED_ARCHIVE_DAYS: fail(f"unexpected source archive date: {d}")
        if fn != f"{INST}-trades-{d}.zip" or not isinstance(size, int) or size <= 0 or not isinstance(digest, str) or len(digest) != 64:
            fail(f"bad source identity for {d}")
        out[d] = {"path": ARCHIVES / fn, "filename": fn, "bytes": size, "sha256": digest}
    if set(out) != set(REQUIRED_ARCHIVE_DAYS): fail("source date set mismatch")
    return out


def verify_sources(manifest: dict[str, dict]) -> None:
    for d in REQUIRED_ARCHIVE_DAYS:
        x = manifest[d]; p = Path(x["path"])
        if not p.exists() or p.stat().st_size != x["bytes"]: fail(f"source size/existence mismatch: {p}")
        if sha256_file(p) != x["sha256"]: fail(f"source SHA mismatch: {p.name}")
        print(f"SOURCE PASS {d} {p.name}")


def read_archive_for_day(path: Path, day_start: int, day_end: int,
                         signed: array, total: array, timestamps: array, prices: array,
                         stats: dict, last_state: dict) -> None:
    with zipfile.ZipFile(path, "r") as zf:
        bad = zf.testzip()
        if bad is not None: fail(f"ZIP CRC failure {path.name}: {bad}")
        members = [m for m in zf.infolist() if not m.is_dir()]
        if len(members) != 1: fail(f"unexpected ZIP member count {path.name}: {len(members)}")
        with zf.open(members[0], "r") as raw:
            reader = csv.reader((line.decode("utf-8") for line in raw))
            if next(reader, None) != EXPECTED_HEADER: fail(f"trade header mismatch in {path.name}")
            source_last_ts = None; source_last_id = None
            for row in reader:
                if not row: continue
                stats["source_rows"] += 1
                if len(row) != 6: fail(f"malformed trade row in {path.name}")
                inst, tid_txt, side, ptxt, stxt, ttxt = row
                if inst != INST:
                    stats["other_instrument_rows"] += 1; continue
                try:
                    ts = parse_ts_ms(ttxt); tid = int(tid_txt); px = float(ptxt); sz = float(stxt)
                except Exception as exc:
                    raise RuntimeError(f"invalid target trade row in {path.name}: {row!r}") from exc
                if side not in {"buy", "sell"} or not math.isfinite(px) or not math.isfinite(sz) or px <= 0 or sz <= 0:
                    fail(f"invalid target trade values in {path.name}")
                if source_last_ts is not None and ts < source_last_ts: fail(f"source timestamp reversal in {path.name}")
                if source_last_id is not None and tid <= source_last_id: fail(f"source trade-id duplicate/backward in {path.name}")
                source_last_ts = ts; source_last_id = tid
                if day_start <= ts < day_end:
                    prev_ts = last_state.get("ts"); prev_id = last_state.get("id")
                    if prev_ts is not None and ts < prev_ts: fail("stitched target timestamp reversal")
                    if prev_id is not None:
                        if tid <= prev_id: fail("stitched target trade-id duplicate/backward")
                        if tid != prev_id + 1: fail(f"stitched target trade-id gap: {prev_id}->{tid}")
                    last_state["ts"] = ts; last_state["id"] = tid
                    k = (ts - day_start) // GRID_MS; n = px * sz
                    signed[k] += n if side == "buy" else -n; total[k] += n
                    timestamps.append(ts); prices.append(px); stats["admitted_rows"] += 1


def build_day_stream(date_text: str, manifest: dict[str, dict]) -> dict:
    day_start, day_end = utc_bounds(date_text); n_buckets = 86_400_000 // GRID_MS
    signed = array("d", [0.0]) * n_buckets; total = array("d", [0.0]) * n_buckets
    timestamps = array("q"); prices = array("d")
    stats = {"source_rows": 0, "other_instrument_rows": 0, "admitted_rows": 0}; state = {"ts": None, "id": None}
    read_archive_for_day(Path(manifest[date_text]["path"]), day_start, day_end, signed, total, timestamps, prices, stats, state)
    read_archive_for_day(Path(manifest[next_day(date_text)]["path"]), day_start, day_end, signed, total, timestamps, prices, stats, state)
    if stats["admitted_rows"] <= 0: fail(f"no admitted rows for {date_text}")
    if len(set((int(ts) - day_start) // 60_000 for ts in timestamps)) != 1440: fail(f"UTC minute coverage failure {date_text}")
    return {"date": date_text, "day_start": day_start, "day_end": day_end,
            "signed": signed, "total": total, "timestamps": timestamps, "prices": prices, "stats": stats}


def build_candidates(stream: dict) -> tuple[dict[str, list[dict]], dict]:
    activity_q: deque[float] = deque(); activity_sorted: list[float] = []
    score_q: deque[float] = deque(); score_sorted: list[float] = []
    out = {name: [] for name, _ in QS}; valid_buckets = scores_built = threshold_ready = 0
    tie_counts = {name: 0 for name, _ in QS}; day_start = int(stream["day_start"])
    for k in range(len(stream["total"])):
        tnot = float(stream["total"][k])
        if tnot <= 0: continue
        valid_buckets += 1
        if len(activity_q) == ROLLING_N:
            scale = median_sorted(activity_sorted)
            if not math.isfinite(scale) or scale <= 0: fail("non-positive/non-finite activity scale")
            flow = float(stream["signed"][k]) / scale
            if not math.isfinite(flow): fail("non-finite FLOW_IMPULSE")
            scores_built += 1; decision_ts = day_start + (k + 1) * GRID_MS
            if len(score_q) == ROLLING_N:
                threshold_ready += 1; af = abs(flow)
                for name, q in QS:
                    thr = nearest_rank(score_sorted, q)
                    if abs(af - thr) <= 1e-15: tie_counts[name] += 1
                    if af > thr and flow != 0.0:
                        out[name].append({"decision_ts": decision_ts, "flow_impulse": flow,
                                          "threshold": thr, "direction": 1 if flow > 0 else -1})
            add_sorted(score_q, score_sorted, abs(flow))
        add_sorted(activity_q, activity_sorted, tnot)
    return out, {"valid_buckets": valid_buckets, "flow_scores_built": scores_built,
                 "threshold_ready_scores": threshold_ready, "candidate_counts": {k: len(v) for k, v in out.items()},
                 "threshold_tie_counts_on_ready_scores": tie_counts}


def first_trade_at_or_after(timestamps: array, target: int, day_end: int) -> int | None:
    i = bisect.bisect_left(timestamps, target)
    if i >= len(timestamps) or int(timestamps[i]) >= day_end: return None
    return i


def simulate_scenario(stream: dict, candidates: list[dict], latency_ms: int, horizon_ms: int) -> dict:
    timestamps = stream["timestamps"]; prices = stream["prices"]; day_end = int(stream["day_end"])
    rows = []; skipped = ineligible = unfilled = 0; open_until = -1
    for c in candidates:
        decision = int(c["decision_ts"]); entry_target = decision + latency_ms; exit_target = entry_target + horizon_ms
        if exit_target >= day_end:
            ineligible += 1; continue
        if decision < open_until:
            skipped += 1; continue
        ei = first_trade_at_or_after(timestamps, entry_target, day_end)
        if ei is None:
            unfilled += 1; continue
        xi = first_trade_at_or_after(timestamps, exit_target, day_end)
        if xi is None:
            unfilled += 1; open_until = day_end; continue
        ets = int(timestamps[ei]); xts = int(timestamps[xi]); ep = float(prices[ei]); xp = float(prices[xi])
        edge = int(c["direction"]) * (xp / ep - 1.0) * 10_000.0
        rows.append({"entry_wait_ms": ets - entry_target, "exit_wait_ms": xts - exit_target, "gross_edge_bps": edge})
        open_until = xts
    eligible = len(candidates) - skipped - ineligible; completed = len(rows); vals = [r["gross_edge_bps"] for r in rows]
    return {"raw_candidate_count": len(candidates), "skipped_while_open": skipped, "ineligible_day_end": ineligible,
            "eligible_nonoverlap_count": eligible, "unfilled_count": unfilled, "completed_trade_count": completed,
            "completion_rate": completed / eligible if eligible else 0.0,
            "mean_gross_edge_bps": statistics.fmean(vals) if vals else None,
            "median_gross_edge_bps": statistics.median(vals) if vals else None,
            "positive_trade_fraction": (sum(v > 0 for v in vals) / len(vals)) if vals else None,
            "entry_wait_p95_ms": percentile([r["entry_wait_ms"] for r in rows], 0.95),
            "exit_wait_p95_ms": percentile([r["exit_wait_ms"] for r in rows], 0.95), "rows": rows}


def scenario_key(q: str, lat: int, horizon: int) -> str:
    return f"{q}|{lat}|{horizon}"


def worker(date_text: str, manifest: dict[str, dict], out_root: str, impl_sha: str) -> dict:
    day_dir = Path(out_root) / "days" / date_text; day_dir.mkdir(parents=True, exist_ok=True); report_path = day_dir / "day_report.json"
    if report_path.exists():
        old = load_json(report_path)
        if old.get("status") == "PASS" and old.get("implementation_sha256") == impl_sha:
            print(f"[{date_text}] COMPLETE CHECKPOINT REUSED", flush=True); return old
    stream = build_day_stream(date_text, manifest); candidates, feature_diag = build_candidates(stream)
    scenarios = []; primary_edges = []
    for qname, lat, horizon, role in SCENARIOS:
        sm = simulate_scenario(stream, candidates[qname], lat, horizon)
        if qname == "q99.5" and lat == 250 and horizon == 60_000:
            primary_edges = [float(r["gross_edge_bps"]) for r in sm["rows"]]
        sm.pop("rows", None); sm.update({"threshold_scenario": qname, "latency_ms": lat, "horizon_ms": horizon, "role": role}); scenarios.append(sm)
    rep = {"stage": STAGE, "version": VERSION, "status": "PASS", "date": date_text,
           "implementation_sha256": impl_sha, "source_stats": stream["stats"], "feature_diagnostics": feature_diag,
           "scenario_summaries": scenarios, "primary_gross_edges_bps": primary_edges,
           "q2_okx_accessed": False, "validation_or_final_accessed": False, "l2_accessed": False,
           "do_not_interpret_before_stage_complete": True}
    atomic_json(report_path, rep); return rep


def aggregate(day_reports: list[dict]) -> dict[str, dict]:
    by_sid: dict[str, list[tuple[str, dict]]] = {}
    for rep in day_reports:
        for s in rep["scenario_summaries"]:
            sid = scenario_key(s["threshold_scenario"], int(s["latency_ms"]), int(s["horizon_ms"]))
            by_sid.setdefault(sid, []).append((rep["date"], s))
    out = {}
    for qname, lat, horizon, role in SCENARIOS:
        sid = scenario_key(qname, lat, horizon); rows = sorted(by_sid.get(sid, []))
        if len(rows) != len(day_reports): fail(f"aggregate missing days for {sid}")
        completed = sum(int(s["completed_trade_count"]) for _, s in rows); eligible = sum(int(s["eligible_nonoverlap_count"]) for _, s in rows)
        daily = [s["mean_gross_edge_bps"] for _, s in rows]
        num = sum((float(s["mean_gross_edge_bps"]) if s["mean_gross_edge_bps"] is not None else 0.0) * int(s["completed_trade_count"]) for _, s in rows)
        out[sid] = {"threshold_scenario": qname, "latency_ms": lat, "horizon_ms": horizon, "role": role,
                    "completed_trade_count": completed, "eligible_nonoverlap_count": eligible,
                    "completion_rate": completed / eligible if eligible else 0.0,
                    "pooled_mean_gross_edge_bps": num / completed if completed else None,
                    "daily_mean_gross_edge_bps": {d: s["mean_gross_edge_bps"] for d, s in rows},
                    "median_daily_mean_gross_edge_bps": statistics.median(daily) if all(v is not None for v in daily) else None,
                    "positive_daily_mean_days": sum(v is not None and v > 0 for v in daily),
                    "all_days_have_completed_trades": all(v is not None for v in daily)}
    return out


def gates_for(stage: str, agg: dict[str, dict], primary_edges: list[float]) -> tuple[str, dict]:
    p = agg[scenario_key("q99.5", 250, 60_000)]; s = agg[scenario_key("q99.5", 500, 60_000)]
    min_days = 14 if stage == "discovery" else 7; min_trades = 200 if stage == "discovery" else 90
    p["pooled_median_gross_edge_bps"] = statistics.median(primary_edges) if primary_edges else None
    checks = {"pooled_mean_ge_12bps": p["pooled_mean_gross_edge_bps"] is not None and p["pooled_mean_gross_edge_bps"] >= 12.0,
              "median_daily_mean_ge_8bps": p["median_daily_mean_gross_edge_bps"] is not None and p["median_daily_mean_gross_edge_bps"] >= 8.0,
              "positive_daily_mean_days_gate": p["positive_daily_mean_days"] >= min_days,
              "pooled_median_positive": p["pooled_median_gross_edge_bps"] is not None and p["pooled_median_gross_edge_bps"] > 0,
              "completed_trade_count_gate": p["completed_trade_count"] >= min_trades,
              "completion_rate_ge_99pct": p["completion_rate"] >= 0.99,
              "stress_500ms_mean_ge_10bps": s["pooled_mean_gross_edge_bps"] is not None and s["pooled_mean_gross_edge_bps"] >= 10.0,
              "all_required_days_have_trades": p["all_days_have_completed_trades"] is True}
    verdict = ("E003_DISCOVERY_PASS" if all(checks.values()) else "E003_DISCOVERY_FAIL") if stage == "discovery" else ("E003_GROSS_HURDLE_PASS" if all(checks.values()) else "E003_CONFIRMATION_FAIL")
    return verdict, checks


def write_summary(path: Path, stage: str, verdict: str, agg: dict[str, dict], checks: dict) -> None:
    p = agg[scenario_key("q99.5", 250, 60_000)]; s = agg[scenario_key("q99.5", 500, 60_000)]
    lines = [f"# SC001-E003 {stage.title()} Flow-Impulse Screen", "", f"- Verdict: `{verdict}`", "- Q2 / Validation / Final: **NO**", "- L2 accessed: **NO**", "",
             "## Primary q99.5 / 250 ms / 60 s", f"- completed trades: {p['completed_trade_count']}", f"- completion rate: {p['completion_rate']}",
             f"- pooled mean gross edge bps: {p['pooled_mean_gross_edge_bps']}", f"- pooled median gross edge bps: {p.get('pooled_median_gross_edge_bps')}",
             f"- median daily mean gross edge bps: {p['median_daily_mean_gross_edge_bps']}", f"- positive daily mean days: {p['positive_daily_mean_days']}", "",
             "## 500 ms stress", f"- pooled mean gross edge bps: {s['pooled_mean_gross_edge_bps']}", "", "## Gates"]
    lines.extend(f"- {k}: {v}" for k, v in checks.items())
    lines += ["", "## Boundary", "This is a coarse trade-price gross-economics screen only. It does not prove executable profitability and does not include L2 spread/depth or fee charging."]
    atomic_text(path, "\n".join(lines) + "\n")


def preflight() -> dict[str, dict]:
    manifest = source_manifest(); verify_sources(manifest)
    print("E003_FLOW_IMPULSE_IMPLEMENTATION_PREFLIGHT_PASS")
    print("discovery_days =", list(DISCOVERY_DAYS)); print("confirmation_days =", list(CONFIRM_DAYS))
    print("primary = q99.5 / 250ms / 60s"); print("stress = q99.5 / 500ms / 60s")
    print("rolling activity = 720 valid buckets; rolling threshold = 720 prior valid scores")
    print("candidate inequality = strict >"); print("Q2/Validation/Final = CLOSED"); print("L2 = CLOSED")
    return manifest


def run_stage(stage: str, manifest: dict[str, dict]) -> None:
    if stage == "discovery":
        days = DISCOVERY_DAYS; root = DISCOVERY_ROOT; final_path = DISCOVERY_REPORT; summary_path = DISCOVERY_SUMMARY
        if final_path.exists(): fail("discovery terminal report already exists; refusing overwrite")
    else:
        drep = load_json(DISCOVERY_REPORT)
        if drep.get("verdict") != "E003_DISCOVERY_PASS" or drep.get("q2_okx_accessed") is not False or drep.get("validation_or_final_accessed") is not False:
            fail("confirmation firewall: terminal E003_DISCOVERY_PASS required")
        days = CONFIRM_DAYS; root = CONFIRM_ROOT; final_path = CONFIRM_REPORT; summary_path = CONFIRM_SUMMARY
        if final_path.exists(): fail("confirmation terminal report already exists; refusing overwrite")
    root.mkdir(parents=True, exist_ok=True); impl_sha = script_sha(); reports = []
    print(f"Starting {stage}: {len(days)} frozen UTC days, max 4 workers. Do not interpret partial day checkpoints.", flush=True)
    with ProcessPoolExecutor(max_workers=4) as pool:
        futs = {pool.submit(worker, d, manifest, str(root), impl_sha): d for d in days}
        for fut in as_completed(futs):
            d = futs[fut]; rep = fut.result(); reports.append(rep)
            print(f"[{d}] worker complete (withheld from interpretation until stage complete)", flush=True)
    if len(reports) != len(days) or any(r.get("status") != "PASS" for r in reports): fail("not all day workers completed PASS")
    reports.sort(key=lambda r: r["date"]); agg = aggregate(reports)
    primary_edges = [float(v) for r in reports for v in (r.get("primary_gross_edges_bps") or [])]
    verdict, checks = gates_for(stage, agg, primary_edges)
    report = {"stage": STAGE, "version": VERSION, "research_stage": stage, "protocol": PROTOCOL,
              "implementation_freeze": IMPLEMENTATION_FREEZE, "implementation_sha256": impl_sha, "verdict": verdict,
              "days": list(days), "day_reports": [str(root / "days" / d / "day_report.json") for d in days],
              "aggregates": agg, "gate_checks": checks, "q2_okx_accessed": False,
              "validation_or_final_accessed": False, "l2_accessed": False, "e002_tfi_used": False,
              "finished_at_utc": datetime.now(timezone.utc).isoformat()}
    atomic_json(final_path, report); write_summary(summary_path, stage, verdict, agg, checks); print(f"COMPLETE: {verdict}")


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("mode", choices=("preflight", "discovery", "confirmation")); args = ap.parse_args()
    manifest = preflight()
    if args.mode != "preflight": run_stage(args.mode, manifest)


if __name__ == "__main__":
    main()
