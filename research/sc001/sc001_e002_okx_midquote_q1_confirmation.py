"""SC001-E002 OKX Q1 four-day midquote confirmation.

Uses only already-qualified 2024-Q1 OKX trade/L2 data. No market-data
network download, no strategy P&L, no execution-profitability claim, no
2024-Q2 / formal Validation / Final access.

Designed for Android Termux / Python stdlib. Per-day computational
checkpoints are saved only to make long phone runs resumable. They are not
for interim interpretation; final verdict is written only after all four
frozen days complete.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import statistics
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

STAGE = "SC001-E002-OKX-MIDQUOTE-Q1-CONFIRMATION"
VERSION = "0.1"
PROTOCOL_COMMIT = "c6f9f01f7aed9a84786c6bb791ab88707dd1a5d7"
PILOT_ENGINE_COMMIT = "94c77febc73601c76976da4ab71bedecc69a485a"
PILOT_ENGINE_PATH = "research/sc001/sc001_e002_okx_midquote_pilot.py"
PILOT_ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + PILOT_ENGINE_COMMIT + "/" + PILOT_ENGINE_PATH
)
MAX_ENGINE_BYTES = 2_000_000

DOWNLOAD = Path("/storage/emulated/0/Download")
WORKSPACE = DOWNLOAD / "SC001_E002_OKX_MIDQUOTE_Q1_CONFIRMATION"
CHECKPOINT_DIR = WORKSPACE / "_checkpoints_do_not_inspect_until_complete"
PROGRESS = WORKSPACE / "sc001_e002_okx_midquote_q1_confirmation_progress.json"
REPORT = WORKSPACE / "sc001_e002_okx_midquote_q1_confirmation_report.json"
METRICS = WORKSPACE / "sc001_e002_okx_midquote_q1_confirmation_daily_metrics.csv"
SUMMARY = WORKSPACE / "sc001_e002_okx_midquote_q1_confirmation_summary.md"
SAFETY = WORKSPACE / "sc001_e002_okx_midquote_q1_confirmation_final_safety.json"

Q006R_REPORT = (
    DOWNLOAD / "SC001_DATA_Q006R_OKX_UTC_STITCH" /
    "sc001_data_q006r_okx_utc_stitch_report.json"
)
Q009A_REPORT = (
    DOWNLOAD / "SC001_DATA_Q009A_OKX_L2_BATCH_A" /
    "sc001_data_q009a_okx_l2_batch_a_report.json"
)
Q009B_REPORT = (
    DOWNLOAD / "SC001_DATA_Q009B_OKX_L2_BATCH_B" /
    "sc001_data_q009b_okx_l2_batch_b_report.json"
)

GRID_MS = 5_000
LOOKBACK_MS = 5_000
HORIZON_MS = 5_000
LATENCIES_MS = (100, 250, 500)
PRIMARY_LATENCY_MS = 100
MIN_FREE_RESERVE_BYTES = 4_000_000_000
WORKSPACE_CAP_BYTES = 100_000_000

DAYS = (
    {
        "date": "2024-01-14",
        "sample_type": "ORDINARY_WEEKEND",
        "event_class": None,
        "expected_decisions": 16_886,
        "next_date": "2024-01-15",
        "l2_root": "SC001_DATA_Q009A_OKX_L2_BATCH_A",
        "l2_bytes": 426_641_072,
    },
    {
        "date": "2024-01-31",
        "sample_type": "EVENT",
        "event_class": "FOMC",
        "expected_decisions": 17_129,
        "next_date": "2024-02-01",
        "l2_root": "SC001_DATA_Q009A_OKX_L2_BATCH_A",
        "l2_bytes": 519_114_508,
    },
    {
        "date": "2024-02-12",
        "sample_type": "ORDINARY_WEEKDAY",
        "event_class": None,
        "expected_decisions": 17_179,
        "next_date": "2024-02-13",
        "l2_root": "SC001_DATA_Q009B_OKX_L2_BATCH_B",
        "l2_bytes": 601_976_188,
    },
    {
        "date": "2024-02-13",
        "sample_type": "EVENT",
        "event_class": "CPI",
        "expected_decisions": 17_226,
        "next_date": "2024-02-14",
        "l2_root": "SC001_DATA_Q009B_OKX_L2_BATCH_B",
        "l2_bytes": 550_675_409,
    },
)


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
        raise RuntimeError("confirmation workspace cap exceeded")
    if free_bytes() < MIN_FREE_RESERVE_BYTES:
        raise RuntimeError("minimum free-space reserve violated")


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def atomic_json(path: Path, obj) -> None:
    atomic_text(path, json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    if not path.exists():
        raise RuntimeError(f"missing required report: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def verify_firewall_false(obj: dict, label: str) -> None:
    for key in (
        "strategy_pnl_calculated",
        "execution_profitability_calculated",
        "q2_okx_accessed",
        "validation_or_final_accessed",
    ):
        if obj.get(key) is not False:
            raise RuntimeError(f"{label} firewall mismatch: {key}")


def verify_parents() -> tuple[dict, dict]:
    q6 = load_json(Q006R_REPORT)
    if q6.get("overall_status") != "PASS" or q6.get("stage") != "SC001-DATA-Q006R-OKX-UTC-STITCH":
        raise RuntimeError("Q006R parent is not PASS")
    if q6.get("q2_okx_accessed") is not False or q6.get("validation_or_final_accessed") is not False:
        raise RuntimeError("Q006R firewall mismatch")

    q9a = load_json(Q009A_REPORT)
    if q9a.get("overall_status") != "PASS" or q9a.get("stage") != "SC001-DATA-Q009A-OKX-L2-Q1-BATCH-A":
        raise RuntimeError("Q009A parent is not PASS")
    verify_firewall_false(q9a, "Q009A")
    if q9a.get("midquote_response_calculated") is not False or q9a.get("strategy_features_calculated") is not False:
        raise RuntimeError("Q009A alpha firewall mismatch")

    q9b = load_json(Q009B_REPORT)
    if q9b.get("overall_status") != "PASS" or q9b.get("stage") != "SC001-DATA-Q009B-OKX-L2-Q1-BATCH-B":
        raise RuntimeError("Q009B parent is not PASS")
    verify_firewall_false(q9b, "Q009B")
    if q9b.get("midquote_response_calculated") is not False or q9b.get("strategy_features_calculated") is not False:
        raise RuntimeError("Q009B alpha firewall mismatch")

    rows = {}
    for source, report in (("Q009A", q9a), ("Q009B", q9b)):
        for row in report.get("days") or []:
            if row.get("status") == "FULL_DAY_PASS":
                rows[row.get("date")] = {"source": source, **row}
    if set(rows) != {x["date"] for x in DAYS}:
        raise RuntimeError(f"L2 parent dates mismatch: {sorted(rows)}")
    return rows, q6


def load_pilot_engine() -> tuple[dict, str]:
    req = Request(
        PILOT_ENGINE_URL,
        headers={"User-Agent": "BotMarketplace-SC001-E002-Q1-confirmation/0.1"},
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(MAX_ENGINE_BYTES + 1)
    if len(raw) > MAX_ENGINE_BYTES:
        raise RuntimeError("pinned pilot engine exceeds safety cap")
    required = [
        b'STAGE = "SC001-E002-OKX-MIDQUOTE-PILOT"',
        b'def build_scores',
        b'def replay_and_sample',
        b'def summarize',
        b'L2 replay progress:',
    ]
    if not raw or not all(token in raw for token in required):
        raise RuntimeError("pinned pilot engine identity mismatch")
    digest = hashlib.sha256(raw).hexdigest()
    ns = {
        "__name__": "sc001_e002_midquote_pilot_library",
        "__file__": "<pinned-midquote-pilot-library>",
        "__package__": None,
    }
    exec(compile(raw, "<pinned-midquote-pilot-library>", "exec"), ns, ns)
    return ns, digest


def path_set(day: dict) -> dict:
    date = day["date"]
    next_date = day["next_date"]
    exact = (
        DOWNLOAD / "SC001_DATA_Q006_OKX_TRADES" / "archives" /
        f"BTC-USDT-SWAP-trades-{date}.zip"
    )
    neighbor = (
        DOWNLOAD / "SC001_DATA_Q006R_OKX_UTC_STITCH" / "neighbor_archives" /
        f"BTC-USDT-SWAP-trades-{next_date}.zip"
    )
    l2 = (
        DOWNLOAD / day["l2_root"] / date /
        f"BTC-USDT-SWAP-L2orderbook-400lv-{date}.tar.gz"
    )
    return {"trade_exact": exact, "trade_neighbor": neighbor, "l2": l2}


def validate_day_sources(day: dict, parent_rows: dict) -> dict:
    date = day["date"]
    p = path_set(day)
    for key in ("trade_exact", "trade_neighbor", "l2"):
        if not p[key].exists():
            raise RuntimeError(f"{date}: missing {key}: {p[key]}")
    if p["l2"].stat().st_size != day["l2_bytes"]:
        raise RuntimeError(f"{date}: L2 size mismatch")
    parent = parent_rows[date]
    archive = parent.get("archive") or {}
    parent_sha = archive.get("sha256")
    if not isinstance(parent_sha, str) or len(parent_sha) != 64:
        raise RuntimeError(f"{date}: missing parent L2 SHA256")
    return {
        "paths": {k: str(v) for k, v in p.items()},
        "l2_size": p["l2"].stat().st_size,
        "l2_mtime_ns": p["l2"].stat().st_mtime_ns,
        "parent_l2_sha256": parent_sha,
        "parent_source": parent.get("source"),
    }


def checkpoint_path(date: str) -> Path:
    return CHECKPOINT_DIR / f"{date}.json"


def load_checkpoint(day: dict, source_meta: dict) -> dict | None:
    path = checkpoint_path(day["date"])
    if not path.exists():
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    expected = {
        "stage": STAGE,
        "protocol_commit": PROTOCOL_COMMIT,
        "pilot_engine_commit": PILOT_ENGINE_COMMIT,
        "date": day["date"],
        "expected_decisions": day["expected_decisions"],
        "l2_size": source_meta["l2_size"],
        "l2_mtime_ns": source_meta["l2_mtime_ns"],
        "parent_l2_sha256": source_meta["parent_l2_sha256"],
    }
    if not all(obj.get(k) == v for k, v in expected.items()):
        return None
    if not isinstance(obj.get("summary"), dict) or not isinstance(obj.get("replay_stats"), dict):
        return None
    return obj


def save_checkpoint(day: dict, source_meta: dict, pilot_sha: str, result: dict) -> None:
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    obj = {
        "stage": STAGE,
        "protocol_commit": PROTOCOL_COMMIT,
        "pilot_engine_commit": PILOT_ENGINE_COMMIT,
        "pilot_engine_sha256": pilot_sha,
        "date": day["date"],
        "expected_decisions": day["expected_decisions"],
        "l2_size": source_meta["l2_size"],
        "l2_mtime_ns": source_meta["l2_mtime_ns"],
        "parent_l2_sha256": source_meta["parent_l2_sha256"],
        "created_at_utc": now_iso(),
        "trade_stats": result["trade_stats"],
        "replay_stats": result["replay_stats"],
        "summary": result["summary"],
        "do_not_interpret_before_all_four_days_complete": True,
    }
    atomic_json(checkpoint_path(day["date"]), obj)


def process_day(day: dict, parent_rows: dict, lib: dict, pilot_sha: str) -> tuple[dict, bool]:
    date = day["date"]
    source_meta = validate_day_sources(day, parent_rows)
    cp = load_checkpoint(day, source_meta)
    if cp is not None:
        print(f"[{date}] computational checkpoint REUSED; no L2 replay needed")
        return {
            "date": date,
            "sample_type": day["sample_type"],
            "event_class": day["event_class"],
            "expected_decisions": day["expected_decisions"],
            "source": source_meta,
            "trade_stats": cp["trade_stats"],
            "replay_stats": cp["replay_stats"],
            "summary": cp["summary"],
        }, True

    p = path_set(day)
    print("=" * 78)
    print(f"MIDQUOTE CONFIRMATION DAY: {date}")
    print(f"Expected decisions: {day['expected_decisions']:,}")
    print("No market-data download. Full L2 replay progress every 1,000,000 records.")
    print("=" * 78)

    print(f"[{date}] verifying current L2 SHA256...")
    current_sha = sha256_file(p["l2"])
    if current_sha != source_meta["parent_l2_sha256"]:
        raise RuntimeError(f"{date}: L2 SHA256 changed from qualified parent")

    lib["DATE"] = date
    lib["TRADE_EXACT"] = p["trade_exact"]
    lib["TRADE_NEIGHBOR"] = p["trade_neighbor"]
    lib["L2_ARCHIVE"] = p["l2"]
    lib["EXPECTED_DECISIONS"] = day["expected_decisions"]
    lib["GRID_MS"] = GRID_MS
    lib["LOOKBACK_MS"] = LOOKBACK_MS
    lib["HORIZON_MS"] = HORIZON_MS
    lib["LATENCIES_MS"] = LATENCIES_MS
    lib["PRIMARY_LATENCY_MS"] = PRIMARY_LATENCY_MS

    scores, decisions, trade_stats, _, day_end = lib["build_scores"]()
    print(f"[{date}] frozen TFI decisions: {len(scores):,}")
    print(f"[{date}] starting L2 replay...")
    samples, replay_stats = lib["replay_and_sample"](decisions, day_end)
    summary = lib["summarize"](scores, samples)
    # Pilot verdict is not used. Integrity requires exact expected decision count.
    for lat in LATENCIES_MS:
        if summary["latencies"][str(lat)]["n"] != day["expected_decisions"]:
            raise RuntimeError(f"{date}: valid-decision mismatch at {lat}ms")
    if replay_stats.get("unfilled_targets") != 0:
        raise RuntimeError(f"{date}: unfilled midquote targets")

    result = {
        "date": date,
        "sample_type": day["sample_type"],
        "event_class": day["event_class"],
        "expected_decisions": day["expected_decisions"],
        "source": {**source_meta, "current_l2_sha256": current_sha},
        "trade_stats": trade_stats,
        "replay_stats": replay_stats,
        "summary": summary,
    }
    save_checkpoint(day, source_meta, pilot_sha, result)
    print(f"[{date}] computation checkpoint saved. Do not interpret partial result.")
    return result, False


def median(xs):
    return statistics.median(xs)


def final_summary(days: list[dict]) -> dict:
    lat_out = {}
    for lat in LATENCIES_MS:
        key = str(lat)
        rhos = [d["summary"]["latencies"][key]["spearman"] for d in days]
        spreads = [d["summary"]["latencies"][key]["extreme_decile"]["spread_bps"] for d in days]
        event_rhos = [
            d["summary"]["latencies"][key]["spearman"]
            for d in days if d["sample_type"] == "EVENT"
        ]
        ordinary_rhos = [
            d["summary"]["latencies"][key]["spearman"]
            for d in days if d["sample_type"] != "EVENT"
        ]
        lat_out[key] = {
            "positive_days": sum(1 for x in rhos if x > 0),
            "median_daily_spearman": median(rhos),
            "mean_daily_spearman": sum(rhos) / len(rhos),
            "positive_extreme_spread_days": sum(1 for x in spreads if x > 0),
            "median_daily_extreme_spread_bps": median(spreads),
            "event_day_median_spearman": median(event_rhos),
            "ordinary_day_median_spearman": median(ordinary_rhos),
        }

    p = lat_out["100"]
    s = lat_out["250"]
    gates = {
        "primary_positive_days_eq_4_of_4": p["positive_days"] == 4,
        "primary_median_spearman_positive": p["median_daily_spearman"] > 0,
        "primary_extreme_spread_positive_days_eq_4": p["positive_extreme_spread_days"] == 4,
        "primary_median_extreme_spread_positive": p["median_daily_extreme_spread_bps"] > 0,
        "event_day_median_positive": p["event_day_median_spearman"] > 0,
        "ordinary_day_median_positive": p["ordinary_day_median_spearman"] > 0,
        "stress_250ms_positive_days_ge_3": s["positive_days"] >= 3,
        "stress_250ms_median_spearman_positive": s["median_daily_spearman"] > 0,
    }
    primary_keys = (
        "primary_positive_days_eq_4_of_4",
        "primary_median_spearman_positive",
        "primary_extreme_spread_positive_days_eq_4",
        "primary_median_extreme_spread_positive",
        "event_day_median_positive",
        "ordinary_day_median_positive",
    )
    stress_keys = (
        "stress_250ms_positive_days_ge_3",
        "stress_250ms_median_spearman_positive",
    )
    if all(gates[k] for k in primary_keys) and all(gates[k] for k in stress_keys):
        verdict = "MIDQUOTE_CONFIRMATION_PASS"
    elif all(gates[k] for k in primary_keys):
        verdict = "MIDQUOTE_CONFIRMATION_WEAK"
    else:
        verdict = "MIDQUOTE_CONFIRMATION_FAIL"
    return {
        "latencies": lat_out,
        "gates": gates,
        "four_of_four_sign_probability_under_50_50_null": 0.0625,
        "verdict": verdict,
    }


def write_progress(completed: list[str], reused: list[str]) -> None:
    atomic_json(PROGRESS, {
        "stage": STAGE,
        "protocol_commit": PROTOCOL_COMMIT,
        "completed_dates": completed,
        "checkpoint_reused_dates": reused,
        "partial_alpha_interpretation_forbidden_until_complete": True,
        "updated_at_utc": now_iso(),
    })


def write_final_outputs(report: dict) -> None:
    atomic_json(REPORT, report)
    rows = []
    for d in report["daily"]:
        for lat in LATENCIES_MS:
            m = d["summary"]["latencies"][str(lat)]
            ext = m["extreme_decile"]
            rows.append({
                "date": d["date"],
                "sample_type": d["sample_type"],
                "event_class": d["event_class"] or "",
                "latency_ms": lat,
                "n": m["n"],
                "spearman": m["spearman"],
                "bottom_mean_bps": ext["bottom_mean_bps"],
                "top_mean_bps": ext["top_mean_bps"],
                "extreme_spread_bps": ext["spread_bps"],
                "directional_hit_rate": ext["directional_hit_rate"],
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
    out = []
    from io import StringIO
    buf = StringIO()
    w = csv.DictWriter(buf, fieldnames=header, lineterminator="\n")
    w.writeheader(); w.writerows(rows)
    atomic_text(METRICS, buf.getvalue())

    s = report["summary"]
    p = s["latencies"]["100"]
    st = s["latencies"]["250"]
    lines = [
        "# SC001-E002 OKX Q1 Midquote Confirmation",
        "",
        f"- Verdict: `{s['verdict']}`",
        "- Scope: four frozen non-pilot 2024-Q1 OKX days",
        "- Strategy P&L / execution profitability: **NO**",
        "- Q2 / formal Validation / Final: **NO**",
        "",
        "## Primary 100 ms",
        f"- Positive daily Spearman: {p['positive_days']} / 4",
        f"- Median daily Spearman: {p['median_daily_spearman']}",
        f"- Positive extreme-spread days: {p['positive_extreme_spread_days']} / 4",
        f"- Median extreme spread bps: {p['median_daily_extreme_spread_bps']}",
        f"- Event-day median Spearman: {p['event_day_median_spearman']}",
        f"- Ordinary-day median Spearman: {p['ordinary_day_median_spearman']}",
        "",
        "## Stress 250 ms",
        f"- Positive daily Spearman: {st['positive_days']} / 4",
        f"- Median daily Spearman: {st['median_daily_spearman']}",
        "",
        "## Boundary",
        "This is midquote predictability confirmation only. It does not charge observed spread/depth, fees or slippage and is not executable-strategy P&L.",
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
        "final_verdict_written": True,
    })


def main() -> None:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    safety_check()
    started = now_iso()
    print("=" * 78)
    print("SC001-E002 OKX Q1 MIDQUOTE CONFIRMATION v0.1")
    print("Four frozen days; no market-data download; no Q2/Validation/Final.")
    print("Per-day checkpoints make long Termux runs resumable.")
    print("DO NOT interpret partial checkpoints before all four days complete.")
    print("=" * 78)

    parent_rows, _ = verify_parents()
    print("Parent Q006R/Q009A/Q009B checks: PASS")
    lib, pilot_sha = load_pilot_engine()
    print("Pinned pilot engine loaded; SHA256:", pilot_sha)

    daily = []
    completed = []
    reused = []
    try:
        for day in DAYS:
            result, was_reused = process_day(day, parent_rows, lib, pilot_sha)
            daily.append(result)
            completed.append(day["date"])
            if was_reused:
                reused.append(day["date"])
            write_progress(completed, reused)
            safety_check()

        if len(daily) != 4:
            raise RuntimeError("confirmation incomplete")
        summary = final_summary(daily)
        report = {
            "stage": STAGE,
            "version": VERSION,
            "protocol_commit": PROTOCOL_COMMIT,
            "pilot_engine_commit": PILOT_ENGINE_COMMIT,
            "pilot_engine_sha256": pilot_sha,
            "started_at_utc": started,
            "finished_at_utc": now_iso(),
            "scope": {
                "dates": [x["date"] for x in DAYS],
                "grid_ms": GRID_MS,
                "lookback_ms": LOOKBACK_MS,
                "horizon_ms": HORIZON_MS,
                "latencies_ms": list(LATENCIES_MS),
                "venue": "OKX",
                "instrument": "BTC-USDT-SWAP",
                "response": "causal last-known L2 midquote at/before target",
            },
            "daily": daily,
            "summary": summary,
            "verdict": summary["verdict"],
            "strategy_features_calculated": True,
            "midquote_response_calculated": True,
            "strategy_pnl_calculated": False,
            "execution_profitability_calculated": False,
            "q2_okx_accessed": False,
            "validation_or_final_accessed": False,
            "network_market_data_bytes_read": 0,
        }
        write_final_outputs(report)
        safety_check()
        print("=" * 78)
        print("COMPLETE:", summary["verdict"])
        print("Outputs:", WORKSPACE)
        print("=" * 78)
    except Exception as exc:
        write_progress(completed, reused)
        atomic_json(WORKSPACE / "sc001_e002_okx_midquote_q1_confirmation_error.json", {
            "stage": STAGE,
            "protocol_commit": PROTOCOL_COMMIT,
            "error": repr(exc),
            "completed_dates": completed,
            "partial_alpha_interpretation_forbidden_until_complete": True,
            "time_utc": now_iso(),
        })
        raise


if __name__ == "__main__":
    main()
