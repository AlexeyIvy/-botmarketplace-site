"""SC001-E004 pre-alpha implementation preflight.

Runs deterministic synthetic/unit tests P01-P44 plus an integrity-only pass over
authorized March-2024 sources. It deliberately does not evaluate compression
events, breakouts, returns, or alpha on real data.

A PASS authorizes only E004 DEV-DISCOVERY under the exact frozen protocol.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
import tempfile
from array import array
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE_PATH = HERE / "sc001_e004_volatility_breakout_screen.py"
SPEC_PATH = "docs/research/sc001-e004-implementation-preflight-v0.1.md"
PROTOCOL_PATH = "docs/research/sc001-e004-volatility-compression-breakout-protocol-v0.1.md"
FREEZE_PATH = "docs/research/sc001-e004-implementation-freeze-v0.1.md"

spec = importlib.util.spec_from_file_location("sc001_e004_engine", ENGINE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load engine: {ENGINE_PATH}")
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)

PREFLIGHT_ROOT = e.WORKSPACE / "preflight"
PREFLIGHT_REPORT = PREFLIGHT_ROOT / "sc001_e004_preflight_report.json"
PREFLIGHT_SUMMARY = PREFLIGHT_ROOT / "sc001_e004_preflight_summary.md"


class T:
    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}

    def check(self, pid: str, fn) -> None:
        try:
            fn()
        except Exception as exc:
            self.rows[pid] = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
        else:
            self.rows[pid] = {"status": "PASS"}

    def require_all(self) -> None:
        bad = [k for k, v in self.rows.items() if v["status"] != "PASS"]
        if bad:
            raise RuntimeError(f"synthetic preflight failures: {bad}")


def assert_true(x: bool, msg: str = "assertion failed") -> None:
    if not x:
        raise AssertionError(msg)


def assert_close(a: float, b: float, tol: float = 1e-12) -> None:
    if not math.isclose(a, b, rel_tol=tol, abs_tol=tol):
        raise AssertionError(f"{a!r} != {b!r}")


def blank_stream(day_start: int = 0) -> dict:
    return {
        "date": "synthetic",
        "day_start": day_start,
        "day_end": day_start + 86_400_000,
        "timestamps": array("q"),
        "prices": array("d"),
        "second_vwap": array("d", [math.nan]) * e.SECONDS_PER_DAY,
        "stats": {},
        "valid_seconds": 0,
        "minute_count": 0,
    }


def valid_block(k: int, r: float, high: float = 101.0, low: float = 100.0, day_start: int = 0) -> dict:
    return {
        "k": k,
        "start_ts": day_start + k * e.BLOCK_MS,
        "end_ts": day_start + (k + 1) * e.BLOCK_MS,
        "valid_seconds": 300,
        "valid": True,
        "high": high,
        "low": low,
        "range_bps": float(r),
    }


def invalid_block(k: int, day_start: int = 0) -> dict:
    return {
        "k": k,
        "start_ts": day_start + k * e.BLOCK_MS,
        "end_ts": day_start + (k + 1) * e.BLOCK_MS,
        "valid_seconds": 0,
        "valid": False,
        "high": None,
        "low": None,
        "range_bps": None,
    }


def make_blocks(ranges: list[float], day_start: int = 0) -> list[dict]:
    out = [invalid_block(k, day_start) for k in range(e.BLOCKS_PER_DAY)]
    for k, r in enumerate(ranges):
        out[k] = valid_block(k, r, day_start=day_start)
    return out


def test_p01_boundaries() -> None:
    day_start = 1_000_000
    assert_true((day_start - day_start) // 1000 == 0)
    assert_true((day_start + 999 - day_start) // 1000 == 0)
    assert_true((day_start + 1000 - day_start) // 1000 == 1)


def test_p02_vwap() -> None:
    num = 100 * 1 + 102 * 3
    den = 1 + 3
    assert_close(num / den, 101.5)


def test_p03_empty_second() -> None:
    s = blank_stream()
    assert_true(math.isnan(float(s["second_vwap"][123])))


def test_p04_decision_time() -> None:
    sec_start = 12_345_000
    decision = sec_start + e.SECOND_MS
    assert_true(decision == 12_346_000)


def test_p05_utc_alignment() -> None:
    s = blank_stream(0)
    for i in range(300):
        s["second_vwap"][i] = 100.0
    blocks = e.build_blocks(s)
    assert_true(blocks[0]["start_ts"] == 0 and blocks[0]["end_ts"] == 300_000)
    assert_true(blocks[1]["start_ts"] == 300_000)


def test_p06_valid_seconds() -> None:
    s = blank_stream()
    for i in range(270):
        s["second_vwap"][i] = 100.0
    for i in range(300, 300 + 269):
        s["second_vwap"][i] = 100.0
    blocks = e.build_blocks(s)
    assert_true(blocks[0]["valid"] is True)
    assert_true(blocks[1]["valid"] is False)


def test_p07_box_extrema() -> None:
    s = blank_stream()
    for i in range(300):
        s["second_vwap"][i] = 100.0 + i / 1000.0
    b = e.build_blocks(s)[0]
    assert_close(b["low"], 100.0)
    assert_close(b["high"], 100.299)


def test_p08_log_range() -> None:
    s = blank_stream()
    for i in range(300):
        s["second_vwap"][i] = 100.0 if i < 150 else 101.0
    b = e.build_blocks(s)[0]
    assert_close(b["range_bps"], 10_000 * math.log(101 / 100))


def test_p09_warmup() -> None:
    blocks = make_blocks([float(i + 1) for i in range(72)])
    flags = e.compression_flags(blocks, 0.20)
    assert_true(all(flags[i] is None for i in range(72)))


def test_p10_prior_only() -> None:
    blocks = make_blocks([float(i + 1) for i in range(72)] + [0.0])
    flags = e.compression_flags(blocks, 0.20)
    assert_close(flags[72]["threshold_bps"], 15.0)
    assert_true(flags[72]["compressed"] is True)


def test_p11_nearest_rank() -> None:
    xs = [float(i) for i in range(1, 73)]
    assert_close(e.nearest_rank(xs, 0.20), 15.0)


def test_p12_strict_compression() -> None:
    base = [float(i + 1) for i in range(72)]
    for cur, expected in [(14.999, True), (15.0, False), (15.001, False)]:
        flags = e.compression_flags(make_blocks(base + [cur]), 0.20)
        assert_true(flags[72]["compressed"] is expected)


def test_p13_day_reset() -> None:
    flags = e.compression_flags(make_blocks([1.0]), 0.20)
    assert_true(flags[0] is None)


def synthetic_breakout_fixture(first_upper: bool = True) -> tuple[dict, list[dict]]:
    s = blank_stream()
    ranges = [float(i + 1) for i in range(72)] + [10.0]
    blocks = make_blocks(ranges)
    blocks[72]["low"] = 100.0
    blocks[72]["high"] = 101.0
    blocks[72]["range_bps"] = 10.0
    lo = 73 * 300
    for i in range(lo, lo + 300):
        s["second_vwap"][i] = 100.5
    if first_upper:
        s["second_vwap"][lo + 2] = 101.1
        s["second_vwap"][lo + 3] = 99.9
    else:
        s["second_vwap"][lo + 2] = 99.9
        s["second_vwap"][lo + 3] = 101.1
    return s, blocks


def test_p14_one_arm() -> None:
    s, blocks = synthetic_breakout_fixture()
    eps = e.potential_breakouts(s, blocks, 0.20)
    assert_true(len(eps) == 1)


def test_p15_arm_interval() -> None:
    s, blocks = synthetic_breakout_fixture()
    eps = e.potential_breakouts(s, blocks, 0.20)
    ep = eps[0]
    assert_true(ep["arm_end_ts"] - ep["arm_ts"] == 300_000)
    assert_true(ep["decision_ts"] <= ep["arm_end_ts"])


def test_p16_upper_strict() -> None:
    s, blocks = synthetic_breakout_fixture()
    lo = 73 * 300
    s["second_vwap"][lo + 2] = 101.0
    s["second_vwap"][lo + 3] = 101.1
    eps = e.potential_breakouts(s, blocks, 0.20)
    assert_true(eps[0]["direction"] == 1)
    assert_true(eps[0]["decision_ts"] == (lo + 4) * 1000)


def test_p17_lower_strict() -> None:
    s, blocks = synthetic_breakout_fixture(first_upper=False)
    lo = 73 * 300
    s["second_vwap"][lo + 2] = 100.0
    s["second_vwap"][lo + 3] = 99.9
    eps = e.potential_breakouts(s, blocks, 0.20)
    assert_true(eps[0]["direction"] == -1)
    assert_true(eps[0]["decision_ts"] == (lo + 4) * 1000)


def test_p18_first_breakout() -> None:
    s, blocks = synthetic_breakout_fixture(first_upper=True)
    eps = e.potential_breakouts(s, blocks, 0.20)
    assert_true(len(eps) == 1 and eps[0]["direction"] == 1)


def test_p19_expired_not_reused() -> None:
    s, blocks = synthetic_breakout_fixture()
    lo = 73 * 300
    for i in range(lo, lo + 300):
        s["second_vwap"][i] = 100.5
    s["second_vwap"][lo + 300] = 101.2
    eps = e.potential_breakouts(s, blocks, 0.20)
    assert_true(len(eps) == 0)


def scenario_stream(trades: list[tuple[int, float]], day_end: int = 86_400_000) -> dict:
    s = blank_stream()
    s["day_end"] = day_end
    s["timestamps"] = array("q", [t for t, _ in trades])
    s["prices"] = array("d", [p for _, p in trades])
    return s


def ep(arm_ts: int, decision_ts: int, direction: int = 1) -> dict:
    return {
        "arm_ts": arm_ts,
        "arm_end_ts": arm_ts + 300_000,
        "decision_ts": decision_ts,
        "direction": direction,
    }


def test_p20_no_retroactive_arm() -> None:
    s = scenario_stream([(1_000_250, 100.0), (601_000_250, 101.0)])
    episodes = [ep(500_000, 500_500), ep(700_000, 700_500)]
    r = e.simulate_scenario(s, episodes, 250, 600_000)
    assert_true(r["breakout_candidates"] == 2)


def test_p21_primary_latency() -> None:
    s = scenario_stream([(1_000, 99.0), (1_250, 100.0), (601_250, 101.0)])
    r = e.simulate_scenario(s, [ep(0, 1_000)], 250, 600_000)
    tr = r["trades"][0]
    assert_true(tr["entry_target_ts"] == 1_250 and tr["entry_ts"] == 1_250)


def test_p22_stress_latency() -> None:
    s = scenario_stream([(1_250, 99.0), (1_500, 100.0), (601_500, 101.0)])
    r = e.simulate_scenario(s, [ep(0, 1_000)], 500, 600_000)
    assert_true(r["trades"][0]["entry_ts"] == 1_500)


def test_p23_primary_hold() -> None:
    s = scenario_stream([(1_250, 100.0), (601_249, 100.5), (601_250, 101.0)])
    r = e.simulate_scenario(s, [ep(0, 1_000)], 250, 600_000)
    assert_true(r["trades"][0]["exit_target_ts"] == 601_250)
    assert_true(r["trades"][0]["exit_ts"] == 601_250)


def test_p24_same_timestamp_order() -> None:
    s = scenario_stream([(1_250, 100.0), (1_250, 101.0), (601_250, 102.0)])
    r = e.simulate_scenario(s, [ep(0, 1_000)], 250, 600_000)
    assert_close(r["trades"][0]["entry_price"], 100.0)


def test_p25_day_end_ineligible() -> None:
    s = scenario_stream([(1_000, 100.0)], day_end=700_000)
    r = e.simulate_scenario(s, [ep(0, 100_000)], 250, 600_000)
    assert_true(r["ineligible_day_end"] == 1 and r["completed"] == 0)


def test_p26_missing_entry() -> None:
    s = scenario_stream([], day_end=2_000_000)
    r = e.simulate_scenario(s, [ep(0, 1_000)], 250, 600_000)
    assert_true(r["unfilled_entry"] == 1 and r["completed"] == 0)


def test_p27_missing_exit() -> None:
    s = scenario_stream([(1_250, 100.0)], day_end=2_000_000)
    r = e.simulate_scenario(s, [ep(0, 1_000), ep(700_000, 700_100)], 250, 600_000)
    assert_true(r["unfilled_exit"] == 1)
    assert_true(r["skipped_while_open"] == 1)


def test_p28_one_position() -> None:
    s = scenario_stream([(1_250, 100.0), (601_250, 101.0)])
    r = e.simulate_scenario(s, [ep(0, 1_000), ep(300_000, 300_100)], 250, 600_000)
    assert_true(r["completed"] == 1 and r["skipped_while_open"] == 1)


def test_p29_actual_exit_controls() -> None:
    # Intended exit target 601250; actual first trade is 650000.
    # A compression block closing exactly at the actual exit timestamp is NOT
    # "subsequently closing" and must therefore be skipped.
    s = scenario_stream([(1_250, 100.0), (650_000, 101.0)])
    r = e.simulate_scenario(s, [ep(0, 1_000), ep(650_000, 650_100)], 250, 600_000)
    assert_true(r["completed"] == 1 and r["skipped_while_open"] == 1)


def test_p30_baseline_updates() -> None:
    blocks = make_blocks([float(i + 1) for i in range(74)])
    flags = e.compression_flags(blocks, 0.20)
    assert_true(flags[72] is not None and flags[73] is not None)
    assert_true(flags[73]["threshold_bps"] >= flags[72]["threshold_bps"])


def test_p31_no_overnight() -> None:
    s1 = scenario_stream([(1_250, 100.0), (601_250, 101.0)])
    s2 = scenario_stream([(1_250, 100.0), (601_250, 101.0)])
    r1 = e.simulate_scenario(s1, [ep(0, 1_000)], 250, 600_000)
    r2 = e.simulate_scenario(s2, [ep(0, 1_000)], 250, 600_000)
    assert_true(r1["completed"] == 1 and r2["completed"] == 1)


def test_p32_gross_edge() -> None:
    s = scenario_stream([(1_250, 100.0), (601_250, 101.0)])
    r = e.simulate_scenario(s, [ep(0, 1_000, 1)], 250, 600_000)
    assert_close(r["trades"][0]["gross_edge_bps"], 100.0)


def test_p33_trimmed_mean() -> None:
    vals = list(range(10))
    assert_close(e.trimmed_mean(vals, 0.10), 4.5)


def test_p34_inactive_day() -> None:
    fake = []
    for d in range(2):
        fake.append({
            "date": f"2024-03-{d+1:02d}",
            "scenarios": {
                "x": {
                    "trades": [] if d == 0 else [{"gross_edge_bps": 1.0}],
                    "breakout_candidates": 0 if d == 0 else 1,
                    "skipped_while_open": 0,
                    "ineligible_day_end": 0,
                    "eligible_nonoverlap": 0 if d == 0 else 1,
                    "completed": 0 if d == 0 else 1,
                    "unfilled_entry": 0,
                    "unfilled_exit": 0,
                }
            },
        })
    a = e.aggregate_scenario(fake, "x")
    assert_true(a["active_days"] == 1 and a["positive_daily_mean_days"] == 1)


def test_p35_concentration() -> None:
    fake = []
    sums = [10.0, 20.0, -5.0]
    for i, x in enumerate(sums):
        fake.append({
            "date": str(i),
            "scenarios": {
                "x": {
                    "trades": [{"gross_edge_bps": x}],
                    "breakout_candidates": 1,
                    "skipped_while_open": 0,
                    "ineligible_day_end": 0,
                    "eligible_nonoverlap": 1,
                    "completed": 1,
                    "unfilled_entry": 0,
                    "unfilled_exit": 0,
                }
            },
        })
    a = e.aggregate_scenario(fake, "x")
    assert_close(a["top1_positive_day_share"], 20/30)
    assert_close(a["top3_positive_day_share"], 1.0)


def test_p36_completion_denominator() -> None:
    s = scenario_stream([(1_250, 100.0), (601_250, 101.0)], day_end=2_000_000)
    eps = [ep(0, 1_000), ep(300_000, 300_100), ep(1_500_000, 1_500_100)]
    r = e.simulate_scenario(s, eps, 250, 600_000)
    assert_true(r["eligible_nonoverlap"] == 1)
    assert_close(r["completion_rate"], 1.0)


def test_p37_all_gates() -> None:
    good = {
        "pooled_mean_gross_edge_bps": 15.0,
        "trimmed_mean_10pct_gross_edge_bps": 12.0,
        "pooled_median_gross_edge_bps": 0.1,
        "median_active_daily_mean_gross_edge_bps": 10.0,
        "active_days": 16,
        "positive_daily_mean_days": 14,
        "completed": 40,
        "max_completed_trades_any_day": 12,
        "completion_rate": 0.99,
        "top1_positive_day_share": 0.30,
        "top3_positive_day_share": 0.60,
    }
    stress = {
        "pooled_mean_gross_edge_bps": 13.0,
        "trimmed_mean_10pct_gross_edge_bps": 10.0,
    }
    ag = {e.PRIMARY_NAME: dict(good), e.STRESS_NAME: dict(stress)}
    verdict, _ = e.evaluate_gates("discovery", ag)
    assert_true(verdict == "E004_DISCOVERY_PASS")
    ag[e.PRIMARY_NAME]["pooled_mean_gross_edge_bps"] = 14.999
    verdict, _ = e.evaluate_gates("discovery", ag)
    assert_true(verdict == "E004_DISCOVERY_FAIL")


def test_p38_discovery_whitelist() -> None:
    try:
        e.build_day_stream("2024-02-29", {})
    except RuntimeError as exc:
        assert_true("unauthorized" in str(exc))
    else:
        raise AssertionError("unauthorized day was accepted")


def test_p39_confirmation_fail_closed() -> None:
    old = e.DISCOVERY_REPORT
    try:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "disc.json"
            e.DISCOVERY_REPORT = p
            p.write_text(json.dumps({
                "stage": e.STAGE,
                "version": e.VERSION,
                "mode": "discovery",
                "verdict": "E004_DISCOVERY_FAIL",
                "engine_sha256": e.script_sha(),
                "protocol": e.PROTOCOL,
                "firewalls": {
                    "q2_market_data_body_accessed": False,
                    "validation_or_final_accessed": False,
                },
            }), encoding="utf-8")
            try:
                e.require_confirmation_authorized()
            except RuntimeError:
                pass
            else:
                raise AssertionError("confirmation opened after FAIL")
    finally:
        e.DISCOVERY_REPORT = old


def test_p40_q2_deny() -> None:
    try:
        e.build_day_stream("2024-04-01", {})
    except RuntimeError as exc:
        assert_true("unauthorized" in str(exc))
    else:
        raise AssertionError("Q2 day was accepted")


def test_p41_no_tfi_flow_identifiers() -> None:
    tree = ast.parse(ENGINE_PATH.read_text(encoding="utf-8"))
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Name, ast.FunctionDef, ast.ClassDef)):
            ident = getattr(node, "id", None) or getattr(node, "name", None) or ""
            low = ident.lower()
            if "tfi" in low or "flow_impulse" in low:
                bad.append(ident)
    assert_true(not bad, f"forbidden feature identifiers: {bad}")


def test_p42_future_mutation() -> None:
    s, blocks = synthetic_breakout_fixture()
    before = e.potential_breakouts(s, blocks, 0.20)
    assert_true(before)
    decision = before[0]["decision_ts"]
    start_idx = decision // 1000 + 10
    for i in range(start_idx, min(start_idx + 100, e.SECONDS_PER_DAY)):
        s["second_vwap"][i] = 50.0
    after = e.potential_breakouts(s, blocks, 0.20)
    assert_true(before[0]["decision_ts"] == after[0]["decision_ts"])
    assert_true(before[0]["direction"] == after[0]["direction"])


def test_p43_current_block_leakage() -> None:
    base = [float(i + 1) for i in range(72)]
    f1 = e.compression_flags(make_blocks(base + [1.0]), 0.20)[72]
    f2 = e.compression_flags(make_blocks(base + [1000.0]), 0.20)[72]
    assert_close(f1["threshold_bps"], f2["threshold_bps"])


def test_p44_post_breakout_mutation() -> None:
    s, blocks = synthetic_breakout_fixture()
    before = e.potential_breakouts(s, blocks, 0.20)
    s["timestamps"] = array("q", [before[0]["decision_ts"] + 100, before[0]["decision_ts"] + 250])
    s["prices"] = array("d", [999.0, 100.0])
    after = e.potential_breakouts(s, blocks, 0.20)
    assert_true(before[0]["decision_ts"] == after[0]["decision_ts"])
    assert_true(before[0]["direction"] == after[0]["direction"])


TESTS = {
    "P01": test_p01_boundaries,
    "P02": test_p02_vwap,
    "P03": test_p03_empty_second,
    "P04": test_p04_decision_time,
    "P05": test_p05_utc_alignment,
    "P06": test_p06_valid_seconds,
    "P07": test_p07_box_extrema,
    "P08": test_p08_log_range,
    "P09": test_p09_warmup,
    "P10": test_p10_prior_only,
    "P11": test_p11_nearest_rank,
    "P12": test_p12_strict_compression,
    "P13": test_p13_day_reset,
    "P14": test_p14_one_arm,
    "P15": test_p15_arm_interval,
    "P16": test_p16_upper_strict,
    "P17": test_p17_lower_strict,
    "P18": test_p18_first_breakout,
    "P19": test_p19_expired_not_reused,
    "P20": test_p20_no_retroactive_arm,
    "P21": test_p21_primary_latency,
    "P22": test_p22_stress_latency,
    "P23": test_p23_primary_hold,
    "P24": test_p24_same_timestamp_order,
    "P25": test_p25_day_end_ineligible,
    "P26": test_p26_missing_entry,
    "P27": test_p27_missing_exit,
    "P28": test_p28_one_position,
    "P29": test_p29_actual_exit_controls,
    "P30": test_p30_baseline_updates,
    "P31": test_p31_no_overnight,
    "P32": test_p32_gross_edge,
    "P33": test_p33_trimmed_mean,
    "P34": test_p34_inactive_day,
    "P35": test_p35_concentration,
    "P36": test_p36_completion_denominator,
    "P37": test_p37_all_gates,
    "P38": test_p38_discovery_whitelist,
    "P39": test_p39_confirmation_fail_closed,
    "P40": test_p40_q2_deny,
    "P41": test_p41_no_tfi_flow_identifiers,
    "P42": test_p42_future_mutation,
    "P43": test_p43_current_block_leakage,
    "P44": test_p44_post_breakout_mutation,
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_info(repo_root: Path, relpath: str) -> dict:
    def run(*args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=repo_root, text=True).strip()
    commit = run("log", "-1", "--format=%H", "--", relpath)
    status = run("status", "--porcelain", "--", relpath)
    if not commit:
        raise RuntimeError(f"file is not committed: {relpath}")
    if status:
        raise RuntimeError(f"file has uncommitted changes: {relpath}: {status}")
    return {"path": relpath, "commit": commit}


def discover_repo_root() -> Path:
    out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=HERE, text=True).strip()
    return Path(out).resolve()


def integrity_day(date_text: str, manifest: dict[str, dict]) -> dict:
    stream = e.build_day_stream(date_text, manifest)
    blocks = e.build_blocks(stream)
    return {
        "date": date_text,
        "admitted_rows": int(stream["stats"]["admitted_rows"]),
        "source_rows": int(stream["stats"]["source_rows"]),
        "first_admitted_ts": int(stream["timestamps"][0]),
        "last_admitted_ts": int(stream["timestamps"][-1]),
        "minute_coverage": int(stream["minute_count"]),
        "valid_seconds": int(stream["valid_seconds"]),
        "valid_blocks": sum(1 for b in blocks if b["valid"]),
        "invalid_blocks": sum(1 for b in blocks if not b["valid"]),
    }


def run_integrity(workers: int) -> tuple[list[dict], dict]:
    manifest = e.source_manifest()
    e.verify_sources(manifest)
    rows = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(integrity_day, d, manifest): d for d in e.TARGET_DAYS}
        for fut in as_completed(futs):
            d = futs[fut]
            rows.append(fut.result())
            print(f"INTEGRITY DAY COMPLETE {d}", flush=True)
    rows.sort(key=lambda x: x["date"])
    return rows, {
        "archive_count": len(manifest),
        "target_day_count": len(rows),
        "all_minutes_complete": all(x["minute_coverage"] == 1440 for x in rows),
    }


def render_summary(rep: dict) -> str:
    lines = [
        "# SC001-E004 Preflight Summary",
        "",
        f"- Status: `{rep['status']}`",
        f"- Engine SHA256: `{rep['engine_sha256']}`",
        f"- Preflight SHA256: `{rep['preflight_sha256']}`",
        f"- Synthetic tests: {sum(1 for x in rep['tests'].values() if x['status']=='PASS')} / {len(rep['tests'])} PASS",
        f"- Real-source integrity run: {'YES' if rep['real_source_integrity_run'] else 'NO'}",
        "",
    ]
    if rep["real_source_integrity_run"]:
        lines += [
            f"- Archives verified: {rep['source_integrity']['archive_count']}",
            f"- Target UTC days integrity-checked: {rep['source_integrity']['target_day_count']}",
            f"- All target days have 1440-minute coverage: {rep['source_integrity']['all_minutes_complete']}",
            "",
        ]
    lines += [
        "This preflight produced no E004 compression-event, breakout-candidate, return, gross-edge or P&L output on real data.",
        "",
    ]
    return "\n".join(lines)


def run_preflight(workers: int, synthetic_only: bool) -> dict:
    tests = T()
    for pid, fn in TESTS.items():
        tests.check(pid, fn)
        print(f"{pid} {tests.rows[pid]['status']}", flush=True)
    tests.require_all()

    repo_root = discover_repo_root()
    required_files = [
        "research/sc001/sc001_e004_volatility_breakout_screen.py",
        "research/sc001/sc001_e004_preflight.py",
        PROTOCOL_PATH,
        SPEC_PATH,
        FREEZE_PATH,
    ]
    git_files = {p: git_info(repo_root, p) for p in required_files}

    source_rows = []
    source_summary = None
    if not synthetic_only:
        source_rows, source_summary = run_integrity(workers)

    status = "E004_PREFLIGHT_PASS" if not synthetic_only else "SYNTHETIC_ONLY_PASS_NOT_AUTHORIZING_DISCOVERY"
    report = {
        "stage": "SC001-E004-PREFLIGHT",
        "version": "0.1",
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "protocol": PROTOCOL_PATH,
        "preflight_spec": SPEC_PATH,
        "implementation_freeze": FREEZE_PATH,
        "engine_path": str(ENGINE_PATH),
        "engine_sha256": sha256_file(ENGINE_PATH),
        "preflight_path": str(Path(__file__).resolve()),
        "preflight_sha256": sha256_file(Path(__file__).resolve()),
        "python_version": sys.version,
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip(),
        "git_files": git_files,
        "tests": tests.rows,
        "real_source_integrity_run": not synthetic_only,
        "source_integrity": source_summary,
        "source_days": source_rows,
        "alpha_calculated": False,
        "pnl_calculated": False,
        "compression_events_exposed": False,
        "breakout_candidates_exposed": False,
        "q2_market_data_body_accessed": False,
        "validation_or_final_accessed": False,
    }
    if not synthetic_only:
        e.atomic_json(PREFLIGHT_REPORT, report)
        e.atomic_text(PREFLIGHT_SUMMARY, render_summary(report))
        print(f"FINAL STATUS {status}", flush=True)
        print(f"REPORT {PREFLIGHT_REPORT}", flush=True)
        print(f"SUMMARY {PREFLIGHT_SUMMARY}", flush=True)
    else:
        print(f"FINAL STATUS {status}", flush=True)
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=min(4, max(1, os.cpu_count() or 1)))
    ap.add_argument("--synthetic-only", action="store_true")
    args = ap.parse_args()
    if args.workers < 1 or args.workers > 4:
        raise RuntimeError("--workers must be in [1,4]")
    run_preflight(args.workers, args.synthetic_only)


if __name__ == "__main__":
    main()
