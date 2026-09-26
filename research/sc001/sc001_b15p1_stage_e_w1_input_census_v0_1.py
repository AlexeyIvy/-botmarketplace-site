#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

STAGE = "SC001-B15P1-NONPRICE-TRANSFERABILITY-COLLECTOR-V0.1.4"
VERSION = "0.1.4"
CADENCE_MS = 15_000
EXPECTED_PER_DAY = 5_760
W1_DAYS = [f"2026-10-{d:02d}" for d in ()]  # overwritten below, avoids locale/date magic
W1_DAYS = ["2026-09-27", "2026-09-28", "2026-09-29", "2026-09-30", "2026-10-01", "2026-10-02", "2026-10-03"]
PREWINDOW_DAY = "2026-09-26"
PASS = "B15P1_STAGE_E_W1_INPUT_CENSUS_PASS"
REVIEW = "B15P1_STAGE_E_W1_INPUT_CENSUS_REVIEW"
SELFTEST_PASS = "B15P1_STAGE_E_W1_INPUT_CENSUS_V01_SELF_TEST_PASS"


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception as exc:
                fail(f"invalid JSONL {path}:{line_no}:{exc}")
            if not isinstance(obj, dict):
                fail(f"JSON object required {path}:{line_no}")
            yield obj


def chain_hash(prev: str, by: str, ok: str, norm: str, route: str) -> str:
    return hashlib.sha256("|".join([prev, by, ok, norm, route]).encode("utf-8")).hexdigest()


def atomic_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def day_bounds_ms(day: str) -> tuple[int, int]:
    dt = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    start = int(dt.timestamp() * 1000)
    return start, start + 86_400_000


def rel_from_manifest_path(value: str, day: str, category: str) -> str:
    # Daily manifests contain absolute host paths. Stage E binds only the
    # known collector layout and never follows arbitrary manifest paths.
    expected_tail = f"/{category}/{day}.jsonl"
    if category.startswith("fees/"):
        expected_tail = f"/{category}/{day}.jsonl"
    value = str(value or "")
    if not value.endswith(expected_tail):
        fail(f"manifest path tail mismatch: category={category} value={value}")
    return f"{category}/{day}.jsonl"


def validate_launcher_args(package_root_arg: str | None, entrypoint_arg: str | None) -> None:
    if (package_root_arg is None) != (entrypoint_arg is None):
        fail("incomplete Runner launcher positional contract")
    if package_root_arg is None:
        return
    package_root = Path(package_root_arg).resolve()
    entrypoint = Path(entrypoint_arg).resolve()
    current = Path(__file__).resolve()
    if entrypoint != current:
        fail("Runner launcher entrypoint mismatch")
    if package_root not in current.parents:
        fail("Runner launcher package root mismatch")


def check_state_manifest(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    state_path = root / "collector_state.json"
    manifest_path = root / "collector_manifest.json"
    if not state_path.is_file() or state_path.is_symlink():
        fail("collector_state missing/invalid")
    if not manifest_path.is_file() or manifest_path.is_symlink():
        fail("collector_manifest missing/invalid")
    state = load_json(state_path)
    manifest = load_json(manifest_path)
    if state.get("stage") != STAGE or state.get("version") != VERSION:
        fail("collector state identity mismatch")
    if state.get("status") != "B15P1_NONPRICE_COLLECTION_RUNNING":
        fail("collector snapshot not running")
    if state.get("price_data_collected") is not False or state.get("pnl_calculated") is not False:
        fail("collector state firewall mismatch")
    if manifest.get("stage") != STAGE or manifest.get("version") != VERSION:
        fail("collector manifest identity mismatch")
    if manifest.get("price_data_authorized") is not False or manifest.get("pnl_authorized") is not False:
        fail("collector manifest firewall mismatch")
    if int(manifest.get("fast_cadence_seconds") or 0) != 15:
        fail("collector cadence mismatch")
    return state, manifest


def verify_poll_day(path: Path, day: str, expected_per_day: int, prior_terminal_hash: str | None) -> tuple[dict[str, Any], str]:
    rows = []
    both_valid = 0
    prev = prior_terminal_hash
    first_prev = None
    for row in iter_jsonl(path):
        if row.get("poll_chain_hash") is None:
            continue
        if row.get("price_data_collected") is not False:
            fail(f"price firewall mismatch in {path}")
        scheduled = int(row.get("scheduled_slot_ms") or 0)
        if scheduled <= 0:
            fail(f"scheduled slot missing in {path}")
        pprev = str(row.get("previous_poll_chain_hash") or "")
        if first_prev is None:
            first_prev = pprev
            if prev is not None and pprev != prev:
                fail(f"cross-day poll chain continuity mismatch day={day}")
        elif pprev != prev:
            fail(f"within-day poll chain continuity mismatch day={day}")
        venues = row.get("venues") or {}
        by = venues.get("BYBIT") or {}
        ok = venues.get("OKX") or {}
        calculated = chain_hash(
            pprev,
            str(by.get("raw_body_sha256") or "0" * 64),
            str(ok.get("raw_body_sha256") or "0" * 64),
            str(row.get("normalized_state_sha256") or ""),
            str(row.get("route_state_sha256") or ""),
        )
        if calculated != row.get("poll_chain_hash"):
            fail(f"poll chain hash mismatch day={day}")
        prev = str(row["poll_chain_hash"])
        if by.get("status") == "OK" and ok.get("status") == "OK":
            both_valid += 1
        rows.append(row)
    if not rows:
        fail(f"no scheduled poll rows day={day}")
    slots = [int(r["scheduled_slot_ms"]) for r in rows]
    if slots != sorted(set(slots)):
        fail(f"slots not strictly increasing day={day}")
    start, end = day_bounds_ms(day)
    if not all(start <= x < end for x in slots):
        fail(f"poll slot outside UTC day={day}")
    if any(x % CADENCE_MS != 0 for x in slots):
        fail(f"poll phase mismatch day={day}")
    coverage = len(rows) / expected_per_day
    valid_fraction = both_valid / expected_per_day
    return {
        "observed_slots": len(rows),
        "expected_slots": expected_per_day,
        "coverage_fraction": coverage,
        "both_venue_valid_rows": both_valid,
        "both_venue_valid_fraction": valid_fraction,
        "first_slot_ms": slots[0],
        "last_slot_ms": slots[-1],
        "first_previous_poll_chain_hash": first_prev,
        "terminal_poll_chain_hash": prev,
    }, str(prev)


def analyze(root: Path, out: Path, days: list[str], expected_per_day: int = EXPECTED_PER_DAY, quiet: bool = False) -> dict[str, Any]:
    state, collector_manifest = check_state_manifest(root)
    if days != W1_DAYS and expected_per_day == EXPECTED_PER_DAY:
        fail("real W1 window mismatch")

    day_results: dict[str, Any] = {}
    previous_terminal = None

    # The 8-hour fee-freshness rule can reach into the partial collector day
    # immediately before W1. Bind only its finalized daily manifest here; the
    # exact fee files (when present) are listed for the later W1 analysis bundle.
    pre_dm_path = root / "daily_manifests" / f"{PREWINDOW_DAY}.json"
    if not pre_dm_path.is_file() or pre_dm_path.is_symlink():
        fail("pre-window daily manifest missing/invalid")
    pre_dm = load_json(pre_dm_path)
    if pre_dm.get("schema") != "sc001.b15.p1_nonprice_collector_daily_manifest.v0.1":
        fail("pre-window daily manifest schema mismatch")
    if pre_dm.get("stage") != STAGE or pre_dm.get("utc_day") != PREWINDOW_DAY:
        fail("pre-window daily manifest identity mismatch")
    if pre_dm.get("price_data_collected") is not False or pre_dm.get("pnl_calculated") is not False:
        fail("pre-window daily manifest firewall mismatch")
    prewindow_fee_inputs: list[dict[str, Any]] = []
    pre_files = pre_dm.get("files") or {}
    for venue_key, category in (("fees_bybit", "fees/bybit"), ("fees_okx", "fees/okx")):
        meta = pre_files.get(venue_key) or {}
        if int(meta.get("rows") or 0) > 0:
            rel = rel_from_manifest_path(meta.get("path"), PREWINDOW_DAY, category)
            prewindow_fee_inputs.append({
                "root": "sc001_data",
                "path": f"SC001_B15P1_TRANSFERABILITY/{rel}",
                "dest": f"b15w1/{rel}",
                "sha256": meta.get("sha256"),
                "rows": int(meta.get("rows") or 0),
            })
    pre_route_meta = pre_files.get("routes") or {}
    if int(pre_route_meta.get("rows") or 0) <= 0 or not pre_route_meta.get("sha256"):
        fail("pre-window route baseline metadata unavailable")
    pre_route_rel = rel_from_manifest_path(pre_route_meta.get("path"), PREWINDOW_DAY, "normalized/routes")
    baseline_route_input = {
        "root": "sc001_data",
        "path": f"SC001_B15P1_TRANSFERABILITY/{pre_route_rel}",
        "dest": f"b15w1/{pre_route_rel}",
        "sha256": pre_route_meta.get("sha256"),
        "rows": int(pre_route_meta.get("rows") or 0),
    }
    total_expected = 0
    total_observed = 0
    total_both_valid = 0
    total_selected_bytes = 0
    event_inputs: list[dict[str, Any]] = []
    fee_inputs: list[dict[str, Any]] = []
    gap_summary: dict[str, int] = {}

    for idx, day in enumerate(days):
        dm_path = root / "daily_manifests" / f"{day}.json"
        poll_path = root / "polls" / f"{day}.jsonl"
        if not dm_path.is_file() or dm_path.is_symlink():
            fail(f"daily manifest missing/invalid day={day}")
        if not poll_path.is_file() or poll_path.is_symlink():
            fail(f"poll file missing/invalid day={day}")
        dm = load_json(dm_path)
        if dm.get("schema") != "sc001.b15.p1_nonprice_collector_daily_manifest.v0.1":
            fail(f"daily manifest schema mismatch day={day}")
        if dm.get("stage") != STAGE or dm.get("utc_day") != day:
            fail(f"daily manifest identity mismatch day={day}")
        if dm.get("price_data_collected") is not False or dm.get("pnl_calculated") is not False:
            fail(f"daily manifest firewall mismatch day={day}")
        files = dm.get("files") or {}
        polls_meta = files.get("polls") or {}
        if str(polls_meta.get("sha256") or "") != sha256_file(poll_path):
            fail(f"poll file SHA mismatch day={day}")
        poll_result, previous_terminal = verify_poll_day(poll_path, day, expected_per_day, previous_terminal)
        if int(polls_meta.get("rows") or -1) != poll_result["observed_slots"]:
            fail(f"poll row count mismatch day={day}")
        dm_polls = dm.get("polls") or {}
        if int(dm_polls.get("expected_slots_per_full_day") or expected_per_day) != expected_per_day:
            fail(f"daily manifest expected-slot mismatch day={day}")
        if int(dm_polls.get("observed_slots") or -1) != poll_result["observed_slots"]:
            fail(f"daily manifest observed-slot mismatch day={day}")
        if dm_polls.get("terminal_poll_chain_hash") != poll_result["terminal_poll_chain_hash"]:
            fail(f"daily manifest terminal chain mismatch day={day}")
        if expected_per_day == EXPECTED_PER_DAY and dm_polls.get("full_day_window_covered") is not True:
            fail(f"daily manifest full-day window not covered day={day}")

        event_meta = files.get("events") or {}
        if int(event_meta.get("rows") or 0) > 0:
            rel = rel_from_manifest_path(event_meta.get("path"), day, "events")
            event_inputs.append({
                "root": "sc001_data",
                "path": f"SC001_B15P1_TRANSFERABILITY/{rel}",
                "dest": f"b15w1/{rel}",
                "sha256": event_meta.get("sha256"),
                "rows": int(event_meta.get("rows") or 0),
            })
        for venue_key, category in (("fees_bybit", "fees/bybit"), ("fees_okx", "fees/okx")):
            meta = files.get(venue_key) or {}
            if int(meta.get("rows") or 0) > 0:
                rel = rel_from_manifest_path(meta.get("path"), day, category)
                fee_inputs.append({
                    "root": "sc001_data",
                    "path": f"SC001_B15P1_TRANSFERABILITY/{rel}",
                    "dest": f"b15w1/{rel}",
                    "sha256": meta.get("sha256"),
                    "rows": int(meta.get("rows") or 0),
                })


        for k, v in (dm.get("source_gap_summary") or {}).items():
            gap_summary[str(k)] = gap_summary.get(str(k), 0) + int(v or 0)
        for meta in files.values():
            if isinstance(meta, dict):
                total_selected_bytes += int(meta.get("size_bytes") or 0)

        total_expected += expected_per_day
        total_observed += poll_result["observed_slots"]
        total_both_valid += poll_result["both_venue_valid_rows"]
        day_results[day] = {
            "daily_manifest_sha256": sha256_file(dm_path),
            "poll_file_sha256": sha256_file(poll_path),
            "poll": poll_result,
            "event_rows": int(event_meta.get("rows") or 0),
            "fee_rows_bybit": int((files.get("fees_bybit") or {}).get("rows") or 0),
            "fee_rows_okx": int((files.get("fees_okx") or {}).get("rows") or 0),
            "referenced_raw_object_count": int(dm.get("referenced_raw_object_count") or 0),
        }

    coverage = total_observed / total_expected
    both_valid_fraction = total_both_valid / total_expected
    quality_pass = coverage >= 0.99 and both_valid_fraction >= 0.99
    status = PASS if quality_pass else REVIEW

    next_inputs = [baseline_route_input] + prewindow_fee_inputs + event_inputs + fee_inputs
    if any(v > 0 for v in gap_summary.values()) or int(state.get("source_gap_count") or 0) > 0:
        next_inputs.append({
            "root": "sc001_data",
            "path": "SC001_B15P1_TRANSFERABILITY/gaps/source_gaps.jsonl",
            "dest": "b15w1/gaps/source_gaps.jsonl",
            "sha256": None,
            "rows": None,
        })

    result = {
        "schema": "sc001.b15.p1_stage_e_w1_input_census_result.v0.1",
        "status": status,
        "window": {
            "label": "W1_7_COMPLETE_UTC_DAYS",
            "days": days,
            "complete_utc_days": len(days),
        },
        "collector_binding": {
            "status": state.get("status"),
            "process_epoch": state.get("process_epoch"),
            "process_restart_count": state.get("process_restart_count"),
            "source_gap_count_total": state.get("source_gap_count"),
            "runner_sha256": collector_manifest.get("runner_sha256"),
            "library_sha256": collector_manifest.get("library_sha256"),
            "route_graph_sha256": collector_manifest.get("route_graph_sha256"),
            "capability_snapshot_sha256": collector_manifest.get("capability_snapshot_sha256"),
            "fast_cadence_seconds": collector_manifest.get("fast_cadence_seconds"),
        },
        "quality": {
            "expected_slots": total_expected,
            "observed_slots": total_observed,
            "poll_coverage_fraction": coverage,
            "both_venue_valid_rows": total_both_valid,
            "both_venue_valid_fraction": both_valid_fraction,
            "formal_minimum_fraction": 0.99,
            "quality_pass": quality_pass,
        },
        "days": day_results,
        "source_gap_summary": dict(sorted(gap_summary.items())),
        "prewindow_daily_manifest_sha256": sha256_file(pre_dm_path),
        "prewindow_fee_input_count": len(prewindow_fee_inputs),
        "manifest_event_input_count": len(event_inputs),
        "manifest_fee_input_count": len(fee_inputs),
        "next_analysis_inputs": next_inputs,
        "selected_manifest_file_bytes": total_selected_bytes,
        "price_data_used": False,
        "pnl_data_used": False,
        "opportunity_rate_inference_performed": False,
        "collector_mutation_performed": False,
        "collector_restart_performed": False,
        "network_calls_performed": False,
        "next_state": (
            "PREPARE_EXACT_W1_SOURCE_ONLY_ANALYSIS_BUNDLE"
            if quality_pass
            else "STOP_AND_REVIEW_W1_DATA_QUALITY"
        ),
    }
    atomic_json(out / "stage_e_w1_input_census_manifest.json", result)
    if not quiet:
        print(status)
        print("coverage =", round(coverage, 8))
        print("both_venue_valid_fraction =", round(both_valid_fraction, 8))
        print("event_input_count =", len(event_inputs))
        print("fee_input_count =", len(fee_inputs))
    return result


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, separators=(",", ":")) + "\n")


def selftest() -> None:
    current = Path(__file__).resolve()
    validate_launcher_args(str(current.parents[2]), str(current))
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "in"
        out = Path(td) / "out"
        root.mkdir(parents=True)
        atomic_json(root / "collector_state.json", {
            "stage": STAGE, "version": VERSION,
            "status": "B15P1_NONPRICE_COLLECTION_RUNNING",
            "process_epoch": 1, "process_restart_count": 0,
            "source_gap_count": 0,
            "price_data_collected": False, "pnl_calculated": False,
        })
        atomic_json(root / "collector_manifest.json", {
            "stage": STAGE, "version": VERSION,
            "fast_cadence_seconds": 15,
            "price_data_authorized": False, "pnl_authorized": False,
            "runner_sha256": "r", "library_sha256": "l",
            "route_graph_sha256": "g", "capability_snapshot_sha256": "c",
        })
        days = ["2099-01-01", "2099-01-02"]
        # Self-test uses the real PREWINDOW_DAY name because analyze() binds it.
        pre_by = root / "fees" / "bybit" / f"{PREWINDOW_DAY}.jsonl"
        pre_ok = root / "fees" / "okx" / f"{PREWINDOW_DAY}.jsonl"
        write_jsonl(pre_by, [{"venue":"BYBIT","instrument":"BTCUSDT","ok":True}])
        write_jsonl(pre_ok, [{"venue":"OKX","instrument":"BTC-USDT","ok":True}])
        pre_route = root / "normalized" / "routes" / f"{PREWINDOW_DAY}.jsonl"
        write_jsonl(pre_route, [{"scheduled_slot_ms": day_bounds_ms(PREWINDOW_DAY)[0] + 15_000, "routes": []}])
        atomic_json(root / "daily_manifests" / f"{PREWINDOW_DAY}.json", {
            "schema": "sc001.b15.p1_nonprice_collector_daily_manifest.v0.1",
            "stage": STAGE, "utc_day": PREWINDOW_DAY,
            "files": {
                "fees_bybit": {"path": str(pre_by), "sha256": sha256_file(pre_by), "size_bytes": pre_by.stat().st_size, "rows": 1},
                "fees_okx": {"path": str(pre_ok), "sha256": sha256_file(pre_ok), "size_bytes": pre_ok.stat().st_size, "rows": 1},
                "routes": {"path": str(pre_route), "sha256": sha256_file(pre_route), "size_bytes": pre_route.stat().st_size, "rows": 1},
            },
            "polls": {"full_day_window_covered": False},
            "source_gap_summary": {},
            "price_data_collected": False, "pnl_calculated": False,
        })
        prev = "0" * 64
        for day in days:
            start, _ = day_bounds_ms(day)
            poll_rows = []
            for i in range(4):
                slot = start + i * CADENCE_MS
                by, ok, norm, route = "1"*64, "2"*64, "3"*64, "4"*64
                h = chain_hash(prev, by, ok, norm, route)
                poll_rows.append({
                    "scheduled_slot_ms": slot,
                    "venues": {"BYBIT": {"status": "OK", "raw_body_sha256": by},
                               "OKX": {"status": "OK", "raw_body_sha256": ok}},
                    "normalized_state_sha256": norm,
                    "route_state_sha256": route,
                    "previous_poll_chain_hash": prev,
                    "poll_chain_hash": h,
                    "price_data_collected": False,
                })
                prev = h
            poll_path = root / "polls" / f"{day}.jsonl"
            write_jsonl(poll_path, poll_rows)
            # Minimal non-empty route baseline metadata; actual route file is materialized later.
            route_path = root / "normalized" / "routes" / f"{day}.jsonl"
            write_jsonl(route_path, [{"scheduled_slot_ms": start, "routes": []}])
            files = {
                "polls": {"path": str(poll_path), "sha256": sha256_file(poll_path), "size_bytes": poll_path.stat().st_size, "rows": 4},
                "routes": {"path": str(route_path), "sha256": sha256_file(route_path), "size_bytes": route_path.stat().st_size, "rows": 1},
                "events": {"path": str(root / "events" / f"{day}.jsonl"), "sha256": None, "size_bytes": 0, "rows": 0},
                "fees_bybit": {"path": str(root / "fees" / "bybit" / f"{day}.jsonl"), "sha256": None, "size_bytes": 0, "rows": 0},
                "fees_okx": {"path": str(root / "fees" / "okx" / f"{day}.jsonl"), "sha256": None, "size_bytes": 0, "rows": 0},
            }
            atomic_json(root / "daily_manifests" / f"{day}.json", {
                "schema": "sc001.b15.p1_nonprice_collector_daily_manifest.v0.1",
                "stage": STAGE,
                "utc_day": day,
                "files": files,
                "polls": {"observed_slots": 4, "expected_slots_per_full_day": 4,
                          "first_slot_ms": poll_rows[0]["scheduled_slot_ms"],
                          "last_slot_ms": poll_rows[-1]["scheduled_slot_ms"],
                          "full_day_window_covered": True,
                          "terminal_poll_chain_hash": prev},
                "referenced_raw_object_count": 8,
                "source_gap_summary": {},
                "price_data_collected": False,
                "pnl_calculated": False,
            })
        result = analyze(root, out, days, expected_per_day=4, quiet=True)
        assert result["status"] == PASS
        assert result["quality"]["observed_slots"] == 8
        assert result["manifest_event_input_count"] == 0
        assert result["next_analysis_inputs"][0]["path"].endswith(f"normalized/routes/{PREWINDOW_DAY}.jsonl")
    print(SELFTEST_PASS)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("self-test", "census"), default="self-test")
    ap.add_argument("--data-root")
    ap.add_argument("--out-dir", default=os.environ.get("OUTPUT_DIR", "/work/run/output"))
    ap.add_argument("_runner_package_root", nargs="?")
    ap.add_argument("_runner_entrypoint", nargs="?")
    args = ap.parse_args()
    validate_launcher_args(args._runner_package_root, args._runner_entrypoint)
    if args.mode == "self-test":
        selftest()
        return 0
    if not args.data_root:
        fail("--data-root required for census")
    root = Path(args.data_root).resolve()
    if not root.is_dir():
        fail("data root missing")
    result = analyze(root, Path(args.out_dir).resolve(), W1_DAYS, EXPECTED_PER_DAY)
    return 0 if result["status"] == PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
