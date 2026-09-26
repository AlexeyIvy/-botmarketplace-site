#!/usr/bin/env python3
from __future__ import annotations

import argparse
import bisect
import json
import math
import os
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import sc001_b15p1_stage_e_w1_input_census_v0_1 as census

PASS = "B15P1_STAGE_E_W1_SEVEN_DAY_OPERATIONAL_CHECKPOINT_PASS"
REVIEW = "B15P1_STAGE_E_W1_SEVEN_DAY_OPERATIONAL_CHECKPOINT_REVIEW"
SELFTEST_PASS = "B15P1_STAGE_E_W1_SOURCE_ONLY_ANALYZER_V01_SELF_TEST_PASS"
BLOCKED_STATES = {
    "BLOCKED_SOURCE_WITHDRAWAL",
    "BLOCKED_DESTINATION_DEPOSIT",
    "BLOCKED_BOTH",
}
FEE_FRESH_MS = 8 * 60 * 60 * 1000
CLUSTER_JOIN_MS = 10 * 60 * 1000


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def atomic_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


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


def route_key(direction: str, canonical_key: str) -> str:
    return f"{direction}|{canonical_key}"


def split_route_key(key: str) -> tuple[str, str, str]:
    direction, sep, canonical = key.partition("|")
    if not sep or direction not in {"BYBIT_TO_OKX", "OKX_TO_BYBIT"}:
        fail(f"invalid route_key={key}")
    asset, sep2, _rest = canonical.partition("|")
    if not sep2 or not asset:
        fail(f"invalid canonical route key={canonical}")
    return direction, asset, canonical


def effective_state(route_states: dict[str, str], keys: list[str]) -> str:
    if not keys:
        return "UNKNOWN"
    states = [route_states.get(k, "SOURCE_UNKNOWN") for k in keys]
    if any(s == "ACTIVE" for s in states):
        return "ACTIVE"
    if all(s in BLOCKED_STATES for s in states):
        return "BLOCKED"
    return "UNKNOWN"


def blocker_components(direction: str, route_states: dict[str, str], keys: list[str]) -> list[str]:
    if direction == "BYBIT_TO_OKX":
        source = "BYBIT_WITHDRAW"
        dest = "OKX_DEPOSIT"
    elif direction == "OKX_TO_BYBIT":
        source = "OKX_WITHDRAW"
        dest = "BYBIT_DEPOSIT"
    else:
        fail(f"bad direction={direction}")
    out: set[str] = set()
    for k in keys:
        s = route_states.get(k)
        if s == "BLOCKED_SOURCE_WITHDRAWAL":
            out.add(source)
        elif s == "BLOCKED_DESTINATION_DEPOSIT":
            out.add(dest)
        elif s == "BLOCKED_BOTH":
            out.add(source)
            out.add(dest)
        elif s not in BLOCKED_STATES:
            fail("blocker signature requested for non-blocked route set")
    return sorted(out)


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return xs[lo]
    return xs[lo] * (hi - pos) + xs[hi] * (pos - lo)


def latest_fee_before(series: list[dict[str, Any]], ts_ms: int) -> dict[str, Any] | None:
    if not series:
        return None
    times = [int(x["receive_ms"]) for x in series]
    idx = bisect.bisect_right(times, ts_ms) - 1
    return series[idx] if idx >= 0 else None


def asset_from_fee_instrument(venue: str, instrument: str) -> str:
    if venue == "BYBIT" and instrument.endswith("USDT") and len(instrument) > 4:
        return instrument[:-4]
    if venue == "OKX" and instrument.endswith("-USDT") and len(instrument) > 5:
        return instrument[:-5]
    fail(f"unexpected USDT spot instrument venue={venue} instrument={instrument}")


def verify_and_load_listed_input(root: Path, item: dict[str, Any]) -> Path:
    path_text = str(item.get("path") or "")
    prefix = "SC001_B15P1_TRANSFERABILITY/"
    if not path_text.startswith(prefix):
        fail(f"unexpected census input path={path_text}")
    rel = path_text[len(prefix):]
    p = root / rel
    if not p.is_file() or p.is_symlink():
        fail(f"listed W1 analysis input missing/invalid: {rel}")
    expected_sha = item.get("sha256")
    if expected_sha and census.sha256_file(p) != expected_sha:
        fail(f"listed W1 analysis input SHA mismatch: {rel}")
    expected_rows = item.get("rows")
    if expected_rows is not None:
        actual_rows = sum(1 for _ in iter_jsonl(p))
        if actual_rows != int(expected_rows):
            fail(f"listed W1 analysis input row mismatch: {rel}")
    return p


def load_baseline_routes(path: Path, w1_start_ms: int) -> tuple[dict[str, str], dict[str, str]]:
    last = None
    for row in iter_jsonl(path):
        last = row
    if last is None:
        fail("pre-window route baseline file empty")
    slot = int(last.get("scheduled_slot_ms") or 0)
    if slot <= 0 or slot >= w1_start_ms:
        fail("pre-window route baseline slot not before W1")
    routes = last.get("routes")
    if not isinstance(routes, list) or not routes:
        fail("pre-window route baseline routes missing")
    states: dict[str, str] = {}
    classes: dict[str, str] = {}
    for r in routes:
        if not isinstance(r, dict):
            fail("route baseline row invalid")
        direction = str(r.get("direction") or "")
        canonical = str(r.get("canonical_representation_key") or "")
        cls = str(r.get("route_class") or "")
        state = str(r.get("state") or "")
        k = route_key(direction, canonical)
        if k in states:
            fail(f"duplicate route baseline key={k}")
        split_route_key(k)
        if cls not in {"ASSET", "QUOTE"}:
            fail(f"bad route class={cls}")
        if state not in {"ACTIVE", "BLOCKED_SOURCE_WITHDRAWAL", "BLOCKED_DESTINATION_DEPOSIT", "BLOCKED_BOTH", "SOURCE_UNKNOWN", "METADATA_INVALID"}:
            fail(f"bad route state={state}")
        states[k] = state
        classes[k] = cls
    return states, classes


def build_groups(classes: dict[str, str]) -> tuple[dict[tuple[str, str], list[str]], dict[str, list[str]]]:
    assets: dict[tuple[str, str], list[str]] = defaultdict(list)
    quotes: dict[str, list[str]] = defaultdict(list)
    for k, cls in classes.items():
        direction, asset, _canonical = split_route_key(k)
        if cls == "ASSET":
            assets[(asset, direction)].append(k)
        elif cls == "QUOTE":
            if asset != "USDT":
                fail(f"unexpected quote asset={asset}")
            quotes[direction].append(k)
    if not assets:
        fail("no asset route groups in baseline")
    if set(quotes) != {"BYBIT_TO_OKX", "OKX_TO_BYBIT"}:
        fail("both USDT quote directions required")
    return {k: sorted(v) for k, v in assets.items()}, {k: sorted(v) for k, v in quotes.items()}


def load_events(event_paths: list[Path], w1_start_ms: int, w1_end_ms: int) -> list[dict[str, Any]]:
    rows = []
    for p in event_paths:
        for row in iter_jsonl(p):
            event = str(row.get("event") or "")
            if not event.startswith("ROUTE_"):
                continue
            slot = int(row.get("scheduled_slot_ms") or 0)
            if not (w1_start_ms <= slot < w1_end_ms):
                fail(f"route event outside W1: {p} slot={slot}")
            if not row.get("route_key"):
                fail(f"route event missing route_key: {p}")
            rows.append(row)
    rows.sort(key=lambda x: (int(x["scheduled_slot_ms"]), str(x["route_key"]), str(x.get("event") or "")))
    return rows


def load_fees(fee_paths: list[Path]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    out: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for p in fee_paths:
        for row in iter_jsonl(p):
            if row.get("ok") is not True:
                continue
            venue = str(row.get("venue") or "")
            instrument = str(row.get("instrument") or "")
            asset = asset_from_fee_instrument(venue, instrument)
            receive_ms = int(row.get("receive_ms") or 0)
            if receive_ms <= 0:
                fail("successful fee row missing receive_ms")
            out[(venue, asset)].append({
                "receive_ms": receive_ms,
                "instrument": instrument,
                "taker_fee_rate": row.get("taker_fee_rate"),
                "maker_fee_rate": row.get("maker_fee_rate"),
                "account_fee_group": row.get("account_fee_group"),
            })
    for key in out:
        out[key].sort(key=lambda x: int(x["receive_ms"]))
    return out


def fee_diagnostic(fees: dict[tuple[str, str], list[dict[str, Any]]], asset: str, ts_ms: int) -> dict[str, Any]:
    venue_diag = {}
    both_fresh = True
    for venue in ("BYBIT", "OKX"):
        row = latest_fee_before(fees.get((venue, asset), []), ts_ms)
        if row is None:
            venue_diag[venue] = {"present": False, "fresh": False}
            both_fresh = False
            continue
        age = ts_ms - int(row["receive_ms"])
        fresh = 0 <= age <= FEE_FRESH_MS
        venue_diag[venue] = {
            "present": True,
            "fresh": fresh,
            "age_ms": age,
            "receive_ms": row["receive_ms"],
            "instrument": row["instrument"],
        }
        both_fresh = both_fresh and fresh
    return {"venues": venue_diag, "both_fresh": both_fresh}


def intervals_overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return max(a_start, b_start) <= min(a_end, b_end)


def cluster_episodes(episodes: list[dict[str, Any]], w1_end_ms: int) -> list[dict[str, Any]]:
    n = len(episodes)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i in range(n):
        ei = episodes[i]
        comps_i = set(ei["blocker_components"])
        end_i = int(ei.get("observed_end_ms") or w1_end_ms)
        for j in range(i + 1, n):
            ej = episodes[j]
            if not (comps_i & set(ej["blocker_components"])):
                continue
            end_j = int(ej.get("observed_end_ms") or w1_end_ms)
            starts_close = abs(int(ei["start_ms"]) - int(ej["start_ms"])) <= CLUSTER_JOIN_MS
            overlap = intervals_overlap(int(ei["start_ms"]), end_i, int(ej["start_ms"]), end_j)
            if starts_close or overlap:
                union(i, j)

    groups: dict[int, list[int]] = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)

    out = []
    for seq, idxs in enumerate(sorted(groups.values(), key=lambda ids: min(episodes[i]["start_ms"] for i in ids)), 1):
        eps = [episodes[i] for i in idxs]
        out.append({
            "cluster_id": f"W1C{seq:04d}",
            "start_ms": min(int(e["start_ms"]) for e in eps),
            "end_ms": max(int(e.get("observed_end_ms") or w1_end_ms) for e in eps),
            "episode_count": len(eps),
            "affected_assets": sorted({str(e["asset"]) for e in eps}),
            "affected_asset_count": len({str(e["asset"]) for e in eps}),
            "directions": sorted({str(e["direction"]) for e in eps}),
            "blocker_components": sorted({c for e in eps for c in e["blocker_components"]}),
            "cause_class": "CAUSE_UNCLASSIFIED",
            "scheduled_classification": "UNCLASSIFIED",
            "completed_episode_count": sum(1 for e in eps if e["disposition"] == "COMPLETED"),
            "censored_episode_count": sum(1 for e in eps if e["disposition"] != "COMPLETED"),
        })
    return out


def analyze(root: Path, out: Path, days: list[str], expected_per_day: int = census.EXPECTED_PER_DAY, quiet: bool = False) -> dict[str, Any]:
    census_result = census.analyze(root, out, days, expected_per_day, quiet=True)
    if census_result["status"] != census.PASS:
        fail("W1 census/data-quality gate is not PASS")

    start_ms, _ = census.day_bounds_ms(days[0])
    _, end_ms = census.day_bounds_ms(days[-1])

    baseline_item = None
    event_items = []
    fee_items = []
    gap_item = None
    for item in census_result["next_analysis_inputs"]:
        path = str(item.get("path") or "")
        if "/normalized/routes/" in path:
            if baseline_item is not None:
                fail("multiple baseline route inputs")
            baseline_item = item
        elif "/events/" in path:
            event_items.append(item)
        elif "/fees/" in path:
            fee_items.append(item)
        elif path.endswith("/gaps/source_gaps.jsonl"):
            gap_item = item
        else:
            fail(f"unexpected next-analysis input={path}")
    if baseline_item is None:
        fail("baseline route input absent from census")

    baseline_path = verify_and_load_listed_input(root, baseline_item)
    event_paths = [verify_and_load_listed_input(root, x) for x in event_items]
    fee_paths = [verify_and_load_listed_input(root, x) for x in fee_items]
    if gap_item is not None:
        gap_path = verify_and_load_listed_input(root, gap_item)
        # Only parse/validate now; source-gap timing remains descriptive.
        _gap_rows = list(iter_jsonl(gap_path))
    else:
        _gap_rows = []

    route_states, route_classes = load_baseline_routes(baseline_path, start_ms)
    asset_groups, quote_groups = build_groups(route_classes)
    fee_series = load_fees(fee_paths)
    route_events = load_events(event_paths, start_ms, end_ms)

    initial_effective = {k: effective_state(route_states, keys) for k, keys in asset_groups.items()}
    left_censored_blocked = [
        {"asset": asset, "direction": direction}
        for (asset, direction), state in sorted(initial_effective.items())
        if state == "BLOCKED"
    ]

    open_eps: dict[tuple[str, str], dict[str, Any]] = {}
    episodes: list[dict[str, Any]] = []
    nonclean_unknown_to_blocked = 0

    by_slot: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for ev in route_events:
        by_slot[int(ev["scheduled_slot_ms"])].append(ev)

    for slot in sorted(by_slot):
        batch = by_slot[slot]
        affected: set[tuple[str, str]] = set()
        before: dict[tuple[str, str], str] = {}
        for ev in batch:
            k = str(ev["route_key"])
            if k not in route_states:
                fail(f"event route_key absent from baseline graph: {k}")
            direction, asset, _ = split_route_key(k)
            if route_classes[k] == "ASSET":
                affected.add((asset, direction))
        for ad in affected:
            before[ad] = effective_state(route_states, asset_groups[ad])

        for ev in batch:
            k = str(ev["route_key"])
            prev = str(ev.get("previous_state") or "")
            cur = str(ev.get("current_state") or "")
            if route_states[k] != prev:
                fail(f"route event previous-state mismatch key={k} slot={slot}")
            route_states[k] = cur

        for ad in sorted(affected):
            asset, direction = ad
            prev_eff = before[ad]
            cur_eff = effective_state(route_states, asset_groups[ad])
            if prev_eff == "ACTIVE" and cur_eff == "BLOCKED":
                if ad in open_eps:
                    fail("duplicate open clean episode")
                comps = blocker_components(direction, route_states, asset_groups[ad])
                opposite = "OKX_TO_BYBIT" if direction == "BYBIT_TO_OKX" else "BYBIT_TO_OKX"
                quote_state = effective_state(route_states, quote_groups[opposite])
                ep = {
                    "asset": asset,
                    "direction": direction,
                    "start_ms": slot,
                    "blocker_components": comps,
                    "route_count": len(asset_groups[ad]),
                    "opposite_direction_usdt_state_at_start": quote_state,
                    "fee_snapshot_at_start": fee_diagnostic(fee_series, asset, slot),
                    "disposition": "OPEN",
                    "observed_end_ms": None,
                    "observed_duration_ms": None,
                }
                open_eps[ad] = ep
            elif prev_eff == "BLOCKED" and cur_eff == "ACTIVE":
                ep = open_eps.pop(ad, None)
                if ep is not None:
                    ep["disposition"] = "COMPLETED"
                    ep["observed_end_ms"] = slot
                    ep["observed_duration_ms"] = slot - int(ep["start_ms"])
                    episodes.append(ep)
            elif prev_eff == "BLOCKED" and cur_eff == "UNKNOWN":
                ep = open_eps.pop(ad, None)
                if ep is not None:
                    ep["disposition"] = "CENSORED_TO_UNKNOWN"
                    ep["observed_end_ms"] = slot
                    ep["observed_duration_ms"] = None
                    episodes.append(ep)
            elif prev_eff == "UNKNOWN" and cur_eff == "BLOCKED":
                nonclean_unknown_to_blocked += 1

    for ad, ep in sorted(open_eps.items()):
        ep["disposition"] = "RIGHT_CENSORED_W1_END"
        ep["observed_end_ms"] = end_ms
        ep["observed_duration_ms"] = None
        episodes.append(ep)

    episodes.sort(key=lambda e: (int(e["start_ms"]), str(e["asset"]), str(e["direction"])))
    clusters = cluster_episodes(episodes, end_ms)
    completed_durations_min = [float(e["observed_duration_ms"]) / 60_000 for e in episodes if e["disposition"] == "COMPLETED"]

    result = {
        "schema": "sc001.b15.p1_stage_e_w1_source_only_analysis_result.v0.1",
        "status": PASS,
        "window": census_result["window"],
        "data_quality": census_result["quality"],
        "collector_binding": census_result["collector_binding"],
        "source_gap_summary": census_result["source_gap_summary"],
        "event_file_count": len(event_paths),
        "route_event_rows": len(route_events),
        "fee_file_count": len(fee_paths),
        "successful_fee_asset_series": len(fee_series),
        "left_censored_blocked_asset_directions": left_censored_blocked,
        "clean_episode_count": len(episodes),
        "completed_episode_count": sum(1 for e in episodes if e["disposition"] == "COMPLETED"),
        "censored_episode_count": sum(1 for e in episodes if e["disposition"] != "COMPLETED"),
        "nonclean_unknown_to_blocked_transition_count": nonclean_unknown_to_blocked,
        "episodes": episodes,
        "independent_outage_cluster_count": len(clusters),
        "clusters": clusters,
        "completed_duration_minutes": {
            "count": len(completed_durations_min),
            "p25": percentile(completed_durations_min, 0.25),
            "median": percentile(completed_durations_min, 0.50),
            "p75": percentile(completed_durations_min, 0.75),
            "p90": percentile(completed_durations_min, 0.90),
        },
        "episode_start_diagnostics": {
            "opposite_usdt_active_count": sum(1 for e in episodes if e["opposite_direction_usdt_state_at_start"] == "ACTIVE"),
            "opposite_usdt_blocked_count": sum(1 for e in episodes if e["opposite_direction_usdt_state_at_start"] == "BLOCKED"),
            "opposite_usdt_unknown_count": sum(1 for e in episodes if e["opposite_direction_usdt_state_at_start"] == "UNKNOWN"),
            "both_venue_fee_snapshot_fresh_count": sum(1 for e in episodes if e["fee_snapshot_at_start"]["both_fresh"]),
        },
        "cause_classification": "CAUSE_UNCLASSIFIED",
        "scheduled_unscheduled_split_available": False,
        "opportunity_rate_inference_performed": False,
        "formal_W2_opportunity_rate_authorized": False,
        "price_data_used": False,
        "pnl_data_used": False,
        "collector_mutation_performed": False,
        "collector_restart_performed": False,
        "network_calls_performed": False,
        "next_state": "CONTINUE_COLLECTION_TO_W2_30_COMPLETE_UTC_DAYS",
    }
    atomic_json(out / "stage_e_w1_source_only_analysis_manifest.json", result)
    if not quiet:
        print(PASS)
        print("clean_episode_count =", len(episodes))
        print("independent_outage_cluster_count =", len(clusters))
        print("formal_W2_opportunity_rate_authorized = False")
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
        census.atomic_json(root / "collector_state.json", {
            "stage": census.STAGE, "version": census.VERSION,
            "status": "B15P1_NONPRICE_COLLECTION_RUNNING",
            "process_epoch": 1, "process_restart_count": 0, "source_gap_count": 0,
            "price_data_collected": False, "pnl_calculated": False,
        })
        census.atomic_json(root / "collector_manifest.json", {
            "stage": census.STAGE, "version": census.VERSION, "fast_cadence_seconds": 15,
            "price_data_authorized": False, "pnl_authorized": False,
            "runner_sha256": "r", "library_sha256": "l", "route_graph_sha256": "g", "capability_snapshot_sha256": "c",
        })
        days = ["2099-01-01", "2099-01-02"]
        w1_start, _ = census.day_bounds_ms(days[0])
        pre_day = census.PREWINDOW_DAY
        pre_by = root / "fees" / "bybit" / f"{pre_day}.jsonl"
        pre_ok = root / "fees" / "okx" / f"{pre_day}.jsonl"
        fee_t = w1_start - 60_000
        write_jsonl(pre_by, [
            {"venue":"BYBIT","instrument":"ABCUSDT","ok":True,"receive_ms":fee_t,"taker_fee_rate":"0.001","maker_fee_rate":"0.001"},
            {"venue":"BYBIT","instrument":"XYZUSDT","ok":True,"receive_ms":fee_t,"taker_fee_rate":"0.001","maker_fee_rate":"0.001"},
        ])
        write_jsonl(pre_ok, [
            {"venue":"OKX","instrument":"ABC-USDT","ok":True,"receive_ms":fee_t,"taker_fee_rate":"-0.001","maker_fee_rate":"-0.001"},
            {"venue":"OKX","instrument":"XYZ-USDT","ok":True,"receive_ms":fee_t,"taker_fee_rate":"-0.001","maker_fee_rate":"-0.001"},
        ])
        pre_routes = root / "normalized" / "routes" / f"{pre_day}.jsonl"
        baseline_routes = [
            {"route_class":"ASSET","canonical_representation_key":"ABC|n1|native:ABC","direction":"BYBIT_TO_OKX","state":"ACTIVE"},
            {"route_class":"ASSET","canonical_representation_key":"ABC|n2|native:ABC","direction":"BYBIT_TO_OKX","state":"ACTIVE"},
            {"route_class":"ASSET","canonical_representation_key":"XYZ|n1|native:XYZ","direction":"BYBIT_TO_OKX","state":"ACTIVE"},
            {"route_class":"QUOTE","canonical_representation_key":"USDT|q1|token:q1","direction":"BYBIT_TO_OKX","state":"ACTIVE"},
            {"route_class":"QUOTE","canonical_representation_key":"USDT|q1|token:q1","direction":"OKX_TO_BYBIT","state":"ACTIVE"},
        ]
        write_jsonl(pre_routes, [{"scheduled_slot_ms":w1_start-15_000,"routes":baseline_routes}])
        census.atomic_json(root / "daily_manifests" / f"{pre_day}.json", {
            "schema":"sc001.b15.p1_nonprice_collector_daily_manifest.v0.1",
            "stage":census.STAGE,"utc_day":pre_day,
            "files":{
                "routes":{"path":str(pre_routes),"sha256":census.sha256_file(pre_routes),"size_bytes":pre_routes.stat().st_size,"rows":1},
                "fees_bybit":{"path":str(pre_by),"sha256":census.sha256_file(pre_by),"size_bytes":pre_by.stat().st_size,"rows":2},
                "fees_okx":{"path":str(pre_ok),"sha256":census.sha256_file(pre_ok),"size_bytes":pre_ok.stat().st_size,"rows":2},
            },
            "polls":{"full_day_window_covered":False},"source_gap_summary":{},
            "price_data_collected":False,"pnl_calculated":False,
        })

        prev="0"*64
        event_rows=[]
        for di, day in enumerate(days):
            start,_=census.day_bounds_ms(day)
            polls=[]
            for i in range(4):
                slot=start+i*census.CADENCE_MS
                by,ok,norm,route="1"*64,"2"*64,"3"*64,"4"*64
                h=census.chain_hash(prev,by,ok,norm,route)
                polls.append({"scheduled_slot_ms":slot,
                    "venues":{"BYBIT":{"status":"OK","raw_body_sha256":by},"OKX":{"status":"OK","raw_body_sha256":ok}},
                    "normalized_state_sha256":norm,"route_state_sha256":route,
                    "previous_poll_chain_hash":prev,"poll_chain_hash":h,"price_data_collected":False})
                prev=h
            poll_path=root/"polls"/f"{day}.jsonl"; write_jsonl(poll_path,polls)
            route_dummy=root/"normalized"/"routes"/f"{day}.jsonl"; write_jsonl(route_dummy,[{"scheduled_slot_ms":start,"routes":baseline_routes}])
            event_path=root/"events"/f"{day}.jsonl"
            day_events=[]
            if di==0:
                t1=start+15_000; t2=start+30_000; t3=start+45_000
                day_events=[
                    {"event":"ROUTE_ACTIVE_TO_BLOCKED","scheduled_slot_ms":t1,"route_key":"BYBIT_TO_OKX|ABC|n1|native:ABC","previous_state":"ACTIVE","current_state":"BLOCKED_SOURCE_WITHDRAWAL"},
                    {"event":"ROUTE_ACTIVE_TO_BLOCKED","scheduled_slot_ms":t2,"route_key":"BYBIT_TO_OKX|ABC|n2|native:ABC","previous_state":"ACTIVE","current_state":"BLOCKED_SOURCE_WITHDRAWAL"},
                    {"event":"ROUTE_ACTIVE_TO_BLOCKED","scheduled_slot_ms":t2,"route_key":"BYBIT_TO_OKX|XYZ|n1|native:XYZ","previous_state":"ACTIVE","current_state":"BLOCKED_SOURCE_WITHDRAWAL"},
                    {"event":"ROUTE_BLOCKED_TO_ACTIVE","scheduled_slot_ms":t3,"route_key":"BYBIT_TO_OKX|ABC|n1|native:ABC","previous_state":"BLOCKED_SOURCE_WITHDRAWAL","current_state":"ACTIVE"},
                    {"event":"ROUTE_BLOCKED_TO_ACTIVE","scheduled_slot_ms":t3,"route_key":"BYBIT_TO_OKX|XYZ|n1|native:XYZ","previous_state":"BLOCKED_SOURCE_WITHDRAWAL","current_state":"ACTIVE"},
                ]
                write_jsonl(event_path,day_events)
            files={
                "polls":{"path":str(poll_path),"sha256":census.sha256_file(poll_path),"size_bytes":poll_path.stat().st_size,"rows":4},
                "routes":{"path":str(route_dummy),"sha256":census.sha256_file(route_dummy),"size_bytes":route_dummy.stat().st_size,"rows":1},
                "events":{"path":str(event_path),"sha256":census.sha256_file(event_path) if event_path.exists() else None,"size_bytes":event_path.stat().st_size if event_path.exists() else 0,"rows":len(day_events)},
                "fees_bybit":{"path":str(root/"fees"/"bybit"/f"{day}.jsonl"),"sha256":None,"size_bytes":0,"rows":0},
                "fees_okx":{"path":str(root/"fees"/"okx"/f"{day}.jsonl"),"sha256":None,"size_bytes":0,"rows":0},
            }
            census.atomic_json(root/"daily_manifests"/f"{day}.json",{
                "schema":"sc001.b15.p1_nonprice_collector_daily_manifest.v0.1","stage":census.STAGE,"utc_day":day,
                "files":files,
                "polls":{"observed_slots":4,"expected_slots_per_full_day":4,"first_slot_ms":polls[0]["scheduled_slot_ms"],"last_slot_ms":polls[-1]["scheduled_slot_ms"],"full_day_window_covered":True,"terminal_poll_chain_hash":prev},
                "referenced_raw_object_count":8,"source_gap_summary":{},"price_data_collected":False,"pnl_calculated":False,
            })
        result=analyze(root,out,days,expected_per_day=4,quiet=True)
        assert result["status"]==PASS
        assert result["clean_episode_count"]==2
        assert result["completed_episode_count"]==2
        assert result["independent_outage_cluster_count"]==1
        assert result["episode_start_diagnostics"]["both_venue_fee_snapshot_fresh_count"]==2
        assert result["episodes"][0]["start_ms"]==w1_start+30_000
    print(SELFTEST_PASS)


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("self-test","analyze"),default="self-test")
    ap.add_argument("--data-root")
    ap.add_argument("--out-dir",default=os.environ.get("OUTPUT_DIR","/work/run/output"))
    ap.add_argument("_runner_package_root",nargs="?")
    ap.add_argument("_runner_entrypoint",nargs="?")
    args=ap.parse_args()
    validate_launcher_args(args._runner_package_root,args._runner_entrypoint)
    if args.mode=="self-test":
        selftest(); return 0
    if not args.data_root: fail("--data-root required for analyze")
    root=Path(args.data_root).resolve()
    if not root.is_dir(): fail("data root missing")
    analyze(root,Path(args.out_dir).resolve(),census.W1_DAYS,census.EXPECTED_PER_DAY)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
