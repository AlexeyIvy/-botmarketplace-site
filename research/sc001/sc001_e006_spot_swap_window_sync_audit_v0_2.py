"""SC001-E006 window synchronization audit v0.2.

DATA/TIMESTAMP ENGINEERING ONLY.
NO PRICE COMPARISON. NO BASIS. NO RETURNS. NO PNL. NO ALPHA.

Tests exact UTC 10-second boundaries and requires a causal prior print from both
qualified SPOT/SWAP legs no older than 10 seconds.
"""
from __future__ import annotations

import importlib.util
import json
import os
from array import array
from pathlib import Path

HERE = Path(__file__).resolve().parent
V1_PATH = HERE / "sc001_e006_spot_swap_sync_audit.py"


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def load_v1():
    spec = importlib.util.spec_from_file_location("e006_sync_v1", V1_PATH)
    if spec is None or spec.loader is None:
        fail("cannot load frozen v0.1 synchronization module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing JSON: {path}")
    x = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x, dict):
        fail(f"JSON object expected: {path}")
    return x


def spot_sha_manifest(V) -> dict[str, str]:
    rep = load_json(V.SPOT_BODY_REPORT)
    if rep.get("status") != "E006_SPOT_BODY_INTEGRITY_PASS":
        fail("SPOT body-integrity report not PASS")
    if any(rep.get(k) is not False for k in (
        "basis_calculated", "returns_calculated", "pnl_calculated",
        "l2_accessed", "q2_accessed", "validation_or_final_accessed",
    )):
        fail("SPOT body-integrity firewall mismatch")
    out = {}
    for row in rep.get("archives") or []:
        d = row.get("date_label")
        sha = row.get("sha256")
        if d in V.REQUIRED_LABELS:
            if not isinstance(sha, str) or len(sha) != 64:
                fail(f"bad SPOT SHA in body report: {d}")
            out[d] = sha
    if set(out) != set(V.REQUIRED_LABELS):
        fail("SPOT SHA label set mismatch")
    return out


def audit_day(V, day: str, spot_ts: array, swap_ts: array) -> tuple[dict, dict[str, array], dict[int, int]]:
    lo = V.day_start_ms(day)
    step = 10_000
    caps = (2_000, 5_000, 10_000, 20_000)
    total = 0
    paired = 0
    fresh10 = 0
    cap_counts = {c: 0 for c in caps}
    spot_age = array("I")
    swap_age = array("I")
    max_age = array("I")
    skew = array("I")
    si = -1
    wi = -1

    for t in range(lo + step, lo + V.DAY_MS, step):
        total += 1
        while si + 1 < len(spot_ts) and int(spot_ts[si + 1]) < t:
            si += 1
        while wi + 1 < len(swap_ts) and int(swap_ts[wi + 1]) < t:
            wi += 1
        if si < 0 or wi < 0:
            continue
        paired += 1
        sa = t - int(spot_ts[si])
        wa = t - int(swap_ts[wi])
        if sa <= 0 or wa <= 0:
            fail("strict-causal age invariant breached")
        ma = max(sa, wa)
        sk = abs(int(spot_ts[si]) - int(swap_ts[wi]))
        spot_age.append(sa)
        swap_age.append(wa)
        max_age.append(ma)
        skew.append(sk)
        if ma <= 10_000:
            fresh10 += 1
        for c in caps:
            if ma <= c:
                cap_counts[c] += 1

    if total != 8_639:
        fail(f"unexpected 10-second grid count for {day}: {total}")

    result = {
        "date": day,
        "grid_points": total,
        "paired_points": paired,
        "paired_share": paired / total,
        "paired_fresh10_points": fresh10,
        "paired_fresh10_share": fresh10 / total,
        "spot_age_ms": V.summarize(spot_age),
        "swap_age_ms": V.summarize(swap_age),
        "max_leg_age_ms": V.summarize(max_age),
        "timestamp_skew_ms": V.summarize(skew),
        "both_age_cap_share": {str(c): cap_counts[c] / total for c in caps},
    }
    vals = {"spot_age": spot_age, "swap_age": swap_age, "max_age": max_age, "skew": skew}
    return result, vals, cap_counts


def main() -> int:
    V = load_v1()
    spot = V.spot_manifest()
    swap = V.swap_manifest()
    spot_shas = spot_sha_manifest(V)

    for d in V.REQUIRED_LABELS:
        V.verify_archive(spot[d], expected_sha=spot_shas[d])
        V.verify_archive(swap[d], expected_sha=swap[d]["sha256"])
        print(f"SOURCE PASS {d}")

    per_day = []
    pooled_spot = array("I")
    pooled_swap = array("I")
    pooled_max = array("I")
    pooled_skew = array("I")
    pooled_caps = {c: 0 for c in (2_000, 5_000, 10_000, 20_000)}
    total_grid = 0
    total_paired = 0
    total_fresh10 = 0

    for d in V.TARGET_DAYS:
        s = V.reconstruct_day(d, V.SPOT_INST, spot)
        w = V.reconstruct_day(d, V.SWAP_INST, swap)
        row, vals, counts = audit_day(V, d, s, w)
        per_day.append(row)
        total_grid += row["grid_points"]
        total_paired += row["paired_points"]
        total_fresh10 += row["paired_fresh10_points"]
        pooled_spot.extend(vals["spot_age"])
        pooled_swap.extend(vals["swap_age"])
        pooled_max.extend(vals["max_age"])
        pooled_skew.extend(vals["skew"])
        for c, n in counts.items():
            pooled_caps[c] += n
        print(f"WINDOW SYNC {d} fresh10={row['paired_fresh10_points']}/{row['grid_points']}")

    pooled = {
        "grid_points": total_grid,
        "paired_points": total_paired,
        "paired_share": total_paired / total_grid,
        "paired_fresh10_points": total_fresh10,
        "paired_fresh10_share": total_fresh10 / total_grid,
        "spot_age_ms": V.summarize(pooled_spot),
        "swap_age_ms": V.summarize(pooled_swap),
        "max_leg_age_ms": V.summarize(pooled_max),
        "timestamp_skew_ms": V.summarize(pooled_skew),
        "both_age_cap_share": {str(c): pooled_caps[c] / total_grid for c in pooled_caps},
    }

    min_day_fresh10 = min(x["paired_fresh10_share"] for x in per_day)
    gates = {
        "all_20_days": len(per_day) == 20,
        "paired_share_ge_0_9999": pooled["paired_share"] >= 0.9999,
        "pooled_fresh10_ge_0_99": pooled["paired_fresh10_share"] >= 0.99,
        "every_day_fresh10_ge_0_98": min_day_fresh10 >= 0.98,
        "p99_max_leg_age_le_10000ms": pooled["max_leg_age_ms"]["p99"] is not None and pooled["max_leg_age_ms"]["p99"] <= 10_000,
    }
    status = "E006_WINDOW_SYNC_AUDIT_PASS" if all(gates.values()) else "E006_WINDOW_SYNC_AUDIT_REVIEW"

    out_root = V.DATA_ROOT / "SC001_E006_SYNC_AUDIT"
    out_report = out_root / "sc001_e006_spot_swap_window_sync_audit_v0_2_report.json"
    report = {
        "stage": "SC001-E006-SPOT-SWAP-WINDOW-SYNC-AUDIT",
        "version": "0.2",
        "status": status,
        "parent_v0_1_status": "E006_SYNC_AUDIT_REVIEW",
        "grid": "exact UTC 10-second boundaries strictly inside each day",
        "fresh10_semantics": "last causal trade timestamp strictly before boundary and age <=10000ms on both legs",
        "target_days": list(V.TARGET_DAYS),
        "required_archive_labels": list(V.REQUIRED_LABELS),
        "boundary_neighbor_label": "2024-03-21",
        "per_day": per_day,
        "pooled": pooled,
        "minimum_daily_fresh10_share": min_day_fresh10,
        "gates": gates,
        "spot_swap_price_compared": False,
        "basis_calculated": False,
        "returns_calculated": False,
        "pnl_calculated": False,
        "alpha_calculated": False,
        "l2_accessed": False,
        "q2_accessed": False,
        "validation_or_final_accessed": False,
    }
    V.atomic_json(out_report, report)

    print(status)
    print("target_day_count =", len(per_day))
    print("grid_points =", pooled["grid_points"])
    print("paired_share =", pooled["paired_share"])
    print("paired_fresh10_share =", pooled["paired_fresh10_share"])
    print("minimum_daily_fresh10_share =", min_day_fresh10)
    print("max_leg_age_p99_ms =", pooled["max_leg_age_ms"]["p99"])
    print("both_age_le_5000ms_share =", pooled["both_age_cap_share"]["5000"])
    print("both_age_le_10000ms_share =", pooled["both_age_cap_share"]["10000"])
    print("spot_swap_price_compared = False")
    print("basis/returns/P&L/alpha calculated = False")
    print("L2/Q2/Validation/Final = CLOSED")
    print("report =", out_report)
    return 0 if status == "E006_WINDOW_SYNC_AUDIT_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
