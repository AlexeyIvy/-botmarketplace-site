from __future__ import annotations

import bisect
import itertools
import json
import math
import os
import statistics
import subprocess
import tarfile
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

STAGE = "SC001-C10-S0-NEAR-TOUCH-LIQUIDITY-VACUUM-HEADROOM-V0.1"
SURVIVE = "C10_S0_HEADROOM_SURVIVE"
REJECT = "C10_S0_REJECT_HEADROOM"
DEFER = "C10_S0_DEFER_SAMPLE"

INST = "BTC-USDT-SWAP"
PILOT_DATE = "2024-02-12"
EXPECTED_FILENAME = "BTC-USDT-SWAP-L2orderbook-400lv-2024-02-12.tar.gz"
EXPECTED_BYTES = 601_976_188

TOP_LEVELS = 5
GRID_MS = 1_000
STALE_MS = 1_000
BASELINE_SECONDS = 60
MIN_BASELINE_OBS = 45
LOW_RATIO = 1.0 / 3.0
OTHER_SIDE_FLOOR = 2.0 / 3.0
HORIZON_SECONDS = 5

VALID_SECONDS_MIN = 80_000
BASELINE_ELIGIBLE_MIN = 70_000
EVENT_MIN = 50
EVENT_HOURS_MIN = 8
PER_SIDE_EVENT_MIN = 10

MOVE_HURDLE_BPS = 15.0
MOVE_EVENT_MIN = 10
MOVE_HOURS_MIN = 4
P90_MOVE_HURDLE_BPS = 15.0
MAX_MOVE_HURDLE_BPS = 30.0

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/sc001-c10-s0-near-touch-liquidity-vacuum-headroom-sentinel-v0.1.md"
REGISTRY = ROOT / "docs/research/sc001-contamination-registry-v0.13.json"
FREEZE = ROOT / "docs/research/sc001-c10-s0-implementation-freeze-v0.1.json"

DATA_ROOT = Path(
    os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))
).expanduser().resolve()

Q009B = (
    DATA_ROOT / "SC001_DATA_Q009B_OKX_L2_BATCH_B"
    / "sc001_data_q009b_okx_l2_batch_b_report.json"
)
L2_PATH = (
    DATA_ROOT / "SC001_DATA_Q009B_OKX_L2_BATCH_B"
    / PILOT_DATE / EXPECTED_FILENAME
)

OUT_DIR = DATA_ROOT / "SC001_C10_S0_HEADROOM"
STRATEGY_OUT = OUT_DIR / "c10_s0_strategy_evidence_v0_1.json"
FEATURE_OUT = OUT_DIR / "c10_s0_feature_block_evidence_v0_1.json"

EPS = 1e-12


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing JSON: {path}")
    x = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x, dict):
        fail(f"JSON object expected: {path}")
    return x


def atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def git_blob(path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(ROOT), "hash-object", str(path.relative_to(ROOT))],
        text=True,
    ).strip()


def sha256_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def day_bounds_ms(day: str) -> tuple[int, int]:
    d = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    lo = int(d.timestamp() * 1000)
    return lo, lo + 86_400_000


def require_freeze() -> None:
    fr = load_json(FREEZE)
    if fr.get("status") != "FROZEN_BEFORE_FIRST_C10_S0_OUTCOME":
        fail("C10-S0 freeze status mismatch")
    if fr.get("runner_git_blob_sha") != git_blob(Path(__file__).resolve()):
        fail("C10-S0 runner identity mismatch")
    if fr.get("protocol_git_blob_sha") != git_blob(PROTOCOL):
        fail("C10-S0 protocol identity mismatch")
    if fr.get("contamination_registry_git_blob_sha") != git_blob(REGISTRY):
        fail("C10-S0 registry identity mismatch")
    expected = {
        "pilot_date": PILOT_DATE,
        "top_levels": TOP_LEVELS,
        "grid_ms": GRID_MS,
        "stale_limit_ms": STALE_MS,
        "baseline_seconds": BASELINE_SECONDS,
        "minimum_baseline_observations": MIN_BASELINE_OBS,
        "future_horizon_seconds": HORIZON_SECONDS,
        "move_hurdle_bps": MOVE_HURDLE_BPS,
    }
    for k, v in expected.items():
        if fr.get(k) != v:
            fail(f"C10-S0 freeze mismatch {k}: {fr.get(k)!r} != {v!r}")
    for k in (
        "c5_labels_authorized",
        "aggressive_flow_conditioning_authorized",
        "fill_model_authorized",
        "queue_model_authorized",
        "fees_authorized",
        "pnl_authorized",
        "promotional_alpha_authorized",
    ):
        if fr.get(k) is not False:
            fail(f"C10-S0 firewall mismatch: {k}")


def require_registry() -> None:
    reg = load_json(REGISTRY)
    if str(reg.get("version")) != "0.13":
        fail("contamination registry version mismatch")
    row = reg.get("c10_l2_selection_calibration") or {}
    if row.get("classification") != "NONPROMOTIONAL_SELECTION_CALIBRATION":
        fail("C10 calibration role mismatch")
    if row.get("target_utc_date") != PILOT_DATE:
        fail("C10 calibration date mismatch")
    if row.get("authorized_body") != EXPECTED_FILENAME:
        fail("C10 authorized body mismatch")
    if row.get("c5_labels_authorized") is not False:
        fail("C10 registry C5 firewall mismatch")
    if row.get("aggressive_flow_conditioning_authorized") is not False:
        fail("C10 registry aggressive-flow firewall mismatch")


def q009b_identity() -> str:
    q = load_json(Q009B)
    if q.get("stage") != "SC001-DATA-Q009B-OKX-L2-Q1-BATCH-B":
        fail("Q009B stage mismatch")
    if q.get("overall_status") != "PASS":
        fail("Q009B not PASS")
    for row in q.get("days") or []:
        if isinstance(row, dict) and row.get("date") == PILOT_DATE:
            if row.get("status") != "FULL_DAY_PASS":
                fail("Q009B pilot day not FULL_DAY_PASS")
            a = row.get("archive") or {}
            if a.get("bytes") != EXPECTED_BYTES:
                fail("Q009B archive byte mismatch")
            sha = a.get("sha256")
            if not isinstance(sha, str) or len(sha) != 64:
                fail("Q009B archive SHA missing")
            return sha
    fail("Q009B pilot day missing")


def parse_level(x) -> tuple[float, float, int]:
    if not isinstance(x, list) or len(x) != 3:
        fail("L2 level shape")
    p = float(x[0])
    s = float(x[1])
    of = float(x[2])
    o = int(round(of))
    if not (math.isfinite(p) and math.isfinite(s) and math.isfinite(of)):
        fail("nonfinite L2 level")
    if p <= 0 or s < 0 or o < 0 or abs(of - o) > 1e-9:
        fail("invalid L2 level")
    if s == 0 and o != 0:
        fail("zero-size delete with nonzero order count")
    return p, s, o


def apply_levels(book: dict, prices: list, levels: list[tuple[float, float, int]]) -> None:
    for p, s, o in levels:
        if s == 0:
            if p not in book:
                fail(f"delete-missing L2 level: {p}")
            del book[p]
            i = bisect.bisect_left(prices, p)
            if i < len(prices) and prices[i] == p:
                prices.pop(i)
        else:
            if p not in book:
                bisect.insort(prices, p)
            book[p] = (s, o)


def valid_book(asks: dict, bids: dict, ap: list, bp: list) -> bool:
    if len(ap) < TOP_LEVELS or len(bp) < TOP_LEVELS:
        return False
    best_bid = bp[-1]
    best_ask = ap[0]
    if best_bid >= best_ask:
        return False
    if bids[best_bid][0] <= 0 or asks[best_ask][0] <= 0:
        return False
    return True


def iter_l2(path: Path):
    with tarfile.open(path, mode="r|gz") as tf:
        regular = 0
        first = True
        last = None
        for member in tf:
            if not member.isfile():
                continue
            regular += 1
            if regular > 1:
                fail(f"multiple regular members: {path.name}")
            f = tf.extractfile(member)
            if f is None:
                fail(f"cannot extract: {path.name}")
            for raw in f:
                if not raw.strip():
                    continue
                r = json.loads(raw)
                if not isinstance(r, dict) or r.get("instId") != INST:
                    fail("L2 record/instrument mismatch")
                action = r.get("action")
                if action not in {"snapshot", "update"}:
                    fail("bad L2 action")
                ts = int(r.get("ts"))
                if last is not None and ts < last:
                    fail("L2 timestamp reversal")
                if first and action != "snapshot":
                    fail("first L2 action is not snapshot")
                first = False
                last = ts
                aa = r.get("asks")
                bb = r.get("bids")
                if not isinstance(aa, list) or not isinstance(bb, list):
                    fail("bad L2 sides")
                pa = [parse_level(x) for x in aa]
                pb = [parse_level(x) for x in bb]
                if len({x[0] for x in pa}) != len(pa):
                    fail("duplicate ask price within record")
                if len({x[0] for x in pb}) != len(pb):
                    fail("duplicate bid price within record")
                yield ts, action, pa, pb
        if regular != 1:
            fail(f"L2 regular member count = {regular}")


def top_depth(book: dict, prices: list, side: str) -> float:
    chosen = prices[:TOP_LEVELS] if side == "ask" else prices[-TOP_LEVELS:]
    return sum(float(book[p][0]) for p in chosen)


def reconstruct_samples(path: Path) -> tuple[dict[int, tuple[float, float, float]], dict]:
    lo, hi = day_bounds_ms(PILOT_DATE)

    asks: dict = {}
    bids: dict = {}
    ap: list = []
    bp: list = []

    samples: dict[int, tuple[float, float, float]] = {}
    next_grid = lo
    last_l2_ts = None
    records = 0
    snapshots = 0
    updates = 0
    stale_grid = 0
    invalid_grid = 0

    def emit(boundary_ms: int) -> None:
        nonlocal stale_grid, invalid_grid
        if not (lo <= boundary_ms < hi):
            return
        if last_l2_ts is None or boundary_ms - last_l2_ts > STALE_MS:
            stale_grid += 1
            return
        if not valid_book(asks, bids, ap, bp):
            invalid_grid += 1
            return

        best_bid = bp[-1]
        best_ask = ap[0]
        mid = 0.5 * (best_bid + best_ask)
        bd = top_depth(bids, bp, "bid")
        ad = top_depth(asks, ap, "ask")

        if not (
            math.isfinite(mid) and mid > 0
            and math.isfinite(bd) and bd > 0
            and math.isfinite(ad) and ad > 0
        ):
            fail("invalid sampled book feature")

        samples[boundary_ms // 1000] = (mid, bd, ad)

    for t, group in itertools.groupby(iter_l2(path), key=lambda x: x[0]):
        t = int(t)

        while next_grid < t and next_grid < hi:
            emit(next_grid)
            next_grid += GRID_MS

        rows = list(group)
        for _ts, action, aa, bb in rows:
            if action == "snapshot":
                asks.clear()
                bids.clear()
                ap.clear()
                bp.clear()
                snapshots += 1
            else:
                updates += 1

            apply_levels(asks, ap, aa)
            apply_levels(bids, bp, bb)
            records += 1

            if not valid_book(asks, bids, ap, bp):
                fail(f"invalid reconstructed book at {t}")

        last_l2_ts = t

        if next_grid == t and next_grid < hi:
            emit(next_grid)
            next_grid += GRID_MS

    while next_grid < hi:
        emit(next_grid)
        next_grid += GRID_MS

    return samples, {
        "records_parsed": records,
        "snapshot_records": snapshots,
        "update_records": updates,
        "valid_sampled_seconds": len(samples),
        "stale_grid_seconds": stale_grid,
        "invalid_grid_seconds": invalid_grid,
    }


def median_sorted(vals: list[float]) -> float:
    n = len(vals)
    if n == 0:
        raise ValueError("empty median")
    m = n // 2
    return vals[m] if n % 2 else 0.5 * (vals[m - 1] + vals[m])


def nearest_rank_percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    vals = sorted(values)
    idx = max(0, min(len(vals) - 1, math.ceil(q * len(vals)) - 1))
    return vals[idx]


def derive_events(samples: dict[int, tuple[float, float, float]]) -> tuple[list[dict], int]:
    secs = sorted(samples)

    win = deque()
    sorted_bid: list[float] = []
    sorted_ask: list[float] = []

    states: dict[int, int] = {}
    ratios: dict[int, tuple[float, float]] = {}
    baseline_eligible = 0

    for sec in secs:
        cutoff = sec - BASELINE_SECONDS
        while win and win[0][0] < cutoff:
            _old_sec, old_bid, old_ask = win.popleft()

            i = bisect.bisect_left(sorted_bid, old_bid)
            if i >= len(sorted_bid) or sorted_bid[i] != old_bid:
                fail("bid rolling median removal mismatch")
            sorted_bid.pop(i)

            j = bisect.bisect_left(sorted_ask, old_ask)
            if j >= len(sorted_ask) or sorted_ask[j] != old_ask:
                fail("ask rolling median removal mismatch")
            sorted_ask.pop(j)

        _mid, bid_depth, ask_depth = samples[sec]

        if len(sorted_bid) >= MIN_BASELINE_OBS:
            bid_med = median_sorted(sorted_bid)
            ask_med = median_sorted(sorted_ask)

            if bid_med <= 0 or ask_med <= 0:
                fail("nonpositive causal depth median")

            br = bid_depth / bid_med
            ar = ask_depth / ask_med
            ratios[sec] = (br, ar)
            baseline_eligible += 1

            bid_vac = br <= LOW_RATIO and ar >= OTHER_SIDE_FLOOR
            ask_vac = ar <= LOW_RATIO and br >= OTHER_SIDE_FLOOR

            if bid_vac and not ask_vac:
                states[sec] = -1
            elif ask_vac and not bid_vac:
                states[sec] = 1
            else:
                states[sec] = 0

        bisect.insort(sorted_bid, bid_depth)
        bisect.insort(sorted_ask, ask_depth)
        win.append((sec, bid_depth, ask_depth))

    events: list[dict] = []

    for sec in sorted(states):
        state = states[sec]
        if state == 0:
            continue

        prev = sec - 1
        if prev not in samples:
            continue
        if states.get(prev) != 0:
            continue

        future = sec + HORIZON_SECONDS
        if future not in samples:
            continue

        mid0 = samples[sec][0]
        mid1 = samples[future][0]
        raw_move = 10_000.0 * math.log(mid1 / mid0)
        abs_move = abs(raw_move)
        signed = float(state) * raw_move
        br, ar = ratios[sec]

        events.append({
            "event_second": sec,
            "event_time_utc": datetime.fromtimestamp(sec, tz=timezone.utc).isoformat(),
            "event_type": "ASK_VACUUM" if state > 0 else "BID_VACUUM",
            "predicted_sign": state,
            "bid_depth_ratio": br,
            "ask_depth_ratio": ar,
            "midquote_event": mid0,
            "midquote_plus_5s": mid1,
            "raw_move_5s_bps": raw_move,
            "abs_move_5s_bps": abs_move,
            "signed_move_5s_bps": signed,
        })

    return events, baseline_eligible


def main() -> int:
    try:
        require_freeze()
        require_registry()
        expected_sha = q009b_identity()

        if STRATEGY_OUT.exists():
            old = load_json(STRATEGY_OUT)
            if old.get("status") in {SURVIVE, REJECT, DEFER}:
                fail(f"one-shot guard: terminal C10-S0 report already exists: {old.get('status')}")

        if not L2_PATH.exists() or L2_PATH.stat().st_size != EXPECTED_BYTES:
            fail("C10-S0 L2 local identity mismatch")

        print("C10-S0 verify frozen L2 SHA256", flush=True)
        actual_sha = sha256_file(L2_PATH)
        if actual_sha != expected_sha:
            fail("C10-S0 L2 SHA mismatch")

        print("C10-S0 replay L2 and build causal 1s book states", flush=True)
        samples, replay = reconstruct_samples(L2_PATH)

        print("C10-S0 derive frozen liquidity-vacuum events", flush=True)
        events, baseline_eligible = derive_events(samples)

        abs_moves = [float(e["abs_move_5s_bps"]) for e in events]
        signed_moves = [float(e["signed_move_5s_bps"]) for e in events]

        bid_events = [e for e in events if e["event_type"] == "BID_VACUUM"]
        ask_events = [e for e in events if e["event_type"] == "ASK_VACUUM"]

        event_hours = {
            datetime.fromtimestamp(int(e["event_second"]), tz=timezone.utc).hour
            for e in events
        }

        large = [e for e in events if float(e["abs_move_5s_bps"]) >= MOVE_HURDLE_BPS]
        large_hours = {
            datetime.fromtimestamp(int(e["event_second"]), tz=timezone.utc).hour
            for e in large
        }

        p50 = nearest_rank_percentile(abs_moves, 0.50)
        p90 = nearest_rank_percentile(abs_moves, 0.90)
        p99 = nearest_rank_percentile(abs_moves, 0.99)
        mx = max(abs_moves) if abs_moves else None

        sample_gates = {
            "valid_sampled_seconds_gte80000": len(samples) >= VALID_SECONDS_MIN,
            "baseline_eligible_seconds_gte70000": baseline_eligible >= BASELINE_ELIGIBLE_MIN,
            "evaluable_events_gte50": len(events) >= EVENT_MIN,
            "event_hours_gte8": len(event_hours) >= EVENT_HOURS_MIN,
            "bid_vacuum_events_gte10": len(bid_events) >= PER_SIDE_EVENT_MIN,
            "ask_vacuum_events_gte10": len(ask_events) >= PER_SIDE_EVENT_MIN,
        }

        headroom_gates = {
            "events_abs_move_gte15bps_gte10": len(large) >= MOVE_EVENT_MIN,
            "large_move_event_hours_gte4": len(large_hours) >= MOVE_HOURS_MIN,
            "p90_abs_move_gte15bps": p90 is not None and p90 >= P90_MOVE_HURDLE_BPS,
            "max_abs_move_gte30bps": mx is not None and mx >= MAX_MOVE_HURDLE_BPS,
        }

        if not all(sample_gates.values()):
            status = DEFER
        elif all(headroom_gates.values()):
            status = SURVIVE
        else:
            status = REJECT

        def mean_signed(rows: list[dict]) -> float | None:
            vals = [float(x["signed_move_5s_bps"]) for x in rows]
            return statistics.fmean(vals) if vals else None

        strategy = {
            "stage": STAGE,
            "version": "0.1",
            "status": status,
            "selection_calibration_only": True,
            "candidate": "C10",
            "mechanism": "one-sided near-touch L2 liquidity vacuum",
            "pilot_date": PILOT_DATE,
            "source": {
                "path": str(L2_PATH),
                "filename": EXPECTED_FILENAME,
                "bytes": EXPECTED_BYTES,
                "sha256": actual_sha,
            },
            "frozen_event_definition": {
                "grid_ms": GRID_MS,
                "stale_limit_ms": STALE_MS,
                "top_levels": TOP_LEVELS,
                "baseline_seconds": BASELINE_SECONDS,
                "minimum_baseline_observations": MIN_BASELINE_OBS,
                "vacuum_ratio_lte": LOW_RATIO,
                "opposite_side_ratio_gte": OTHER_SIDE_FLOOR,
                "onset_requires_immediately_previous_valid_none_state": True,
                "future_horizon_seconds": HORIZON_SECONDS,
            },
            "structural_reference": {
                "execution_family_if_later_directional": "two_fill_taker",
                "taker_reference_bps_per_fill": 5.0,
                "two_fill_fee_reference_floor_bps": 10.0,
                "gross_move_hurdle_bps": MOVE_HURDLE_BPS,
            },
            "replay": replay,
            "valid_sampled_seconds": len(samples),
            "baseline_eligible_seconds": baseline_eligible,
            "evaluable_event_count": len(events),
            "bid_vacuum_event_count": len(bid_events),
            "ask_vacuum_event_count": len(ask_events),
            "event_utc_hours": len(event_hours),
            "large_move_event_count": len(large),
            "large_move_event_utc_hours": len(large_hours),
            "p50_abs_move_5s_bps": p50,
            "p90_abs_move_5s_bps": p90,
            "p99_abs_move_5s_bps": p99,
            "max_abs_move_5s_bps": mx,
            "mean_signed_move_5s_bps": (
                statistics.fmean(signed_moves) if signed_moves else None
            ),
            "median_signed_move_5s_bps": (
                statistics.median(signed_moves) if signed_moves else None
            ),
            "positive_signed_move_share": (
                sum(1 for x in signed_moves if x > 0) / len(signed_moves)
                if signed_moves else None
            ),
            "bid_vacuum_mean_signed_move_5s_bps": mean_signed(bid_events),
            "ask_vacuum_mean_signed_move_5s_bps": mean_signed(ask_events),
            "sample_gates": sample_gates,
            "headroom_gates": headroom_gates,
            "failed_sample_gates": [k for k, v in sample_gates.items() if not v],
            "failed_headroom_gates": [k for k, v in headroom_gates.items() if not v],
            "events": events,
            "c5_labels_used": False,
            "aggressive_flow_conditioning_used": False,
            "fill_model_calculated": False,
            "queue_model_calculated": False,
            "fees_calculated": False,
            "pnl_calculated": False,
            "promotional_alpha_accessed": False,
        }

        feature = {
            "stage": "SC001-C10-S0-FEATURE-BLOCK-EVIDENCE-V0.1",
            "version": "0.1",
            "evidence_maturity": "SELECTION_CALIBRATION_ONLY",
            "strategy_status_reference": status,
            "blocks": {
                "C10-F1": {
                    "name": "near-touch 5-level visible depth",
                    "roles": ["R2", "R6"],
                    "measurement_validity": True,
                    "top_levels": TOP_LEVELS,
                },
                "C10-F2": {
                    "name": "causal side-specific depth baseline",
                    "roles": ["R6"],
                    "measurement_validity": True,
                    "lookback_seconds": BASELINE_SECONDS,
                    "minimum_observations": MIN_BASELINE_OBS,
                    "statistic": "median",
                },
                "C10-F3": {
                    "name": "one-sided liquidity-vacuum onset",
                    "roles": ["R1", "R2"],
                    "measurement_validity": True,
                    "bid_vacuum_events": len(bid_events),
                    "ask_vacuum_events": len(ask_events),
                    "event_hours": len(event_hours),
                    "p50_abs_move_5s_bps": p50,
                    "p90_abs_move_5s_bps": p90,
                    "p99_abs_move_5s_bps": p99,
                    "max_abs_move_5s_bps": mx,
                    "mean_signed_move_5s_bps": (
                        statistics.fmean(signed_moves) if signed_moves else None
                    ),
                    "positive_signed_move_share": (
                        sum(1 for x in signed_moves if x > 0) / len(signed_moves)
                        if signed_moves else None
                    ),
                    "economic_move_hurdle_bps": MOVE_HURDLE_BPS,
                },
            },
            "c5_labels_used": False,
            "aggressive_flow_conditioning_used": False,
            "works_global_claim_allowed": False,
            "execution_evidence_present": False,
            "promotional_alpha_accessed": False,
        }

        atomic_json(STRATEGY_OUT, strategy)
        atomic_json(FEATURE_OUT, feature)

        print(status)
        print("valid_sampled_seconds =", len(samples))
        print("baseline_eligible_seconds =", baseline_eligible)
        print("evaluable_event_count =", len(events))
        print("bid_vacuum_event_count =", len(bid_events))
        print("ask_vacuum_event_count =", len(ask_events))
        print("event_utc_hours =", len(event_hours))
        print("large_move_event_count =", len(large))
        print("large_move_event_utc_hours =", len(large_hours))
        print("p50_abs_move_5s_bps =", p50)
        print("p90_abs_move_5s_bps =", p90)
        print("p99_abs_move_5s_bps =", p99)
        print("max_abs_move_5s_bps =", mx)
        print("mean_signed_move_5s_bps =", strategy["mean_signed_move_5s_bps"])
        print("positive_signed_move_share =", strategy["positive_signed_move_share"])
        print("failed_sample_gates =", strategy["failed_sample_gates"])
        print("failed_headroom_gates =", strategy["failed_headroom_gates"])
        print("C5 labels/aggressive flow/fill/queue/fees/PnL = False")
        print("promotional alpha accessed = False")
        print("strategy_report =", STRATEGY_OUT)
        print("feature_report =", FEATURE_OUT)
        return 0

    except Exception as exc:
        print("C10_S0_IMPLEMENTATION_FAIL")
        print("error =", f"{type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
