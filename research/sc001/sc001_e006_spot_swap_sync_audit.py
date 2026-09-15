"""SC001-E006 SPOT/SWAP synchronization-feasibility audit.

DATA/TIMESTAMP ENGINEERING ONLY.
NO PRICE COMPARISON. NO BASIS. NO RETURNS. NO PNL. NO L2/Q2/VALIDATION/FINAL.

Uses only local qualified March-2024 BTC-USDT SPOT and BTC-USDT-SWAP trade
archives. Audits causal last-trade timestamp availability on a 1-second UTC grid.
"""
from __future__ import annotations

import bisect
import csv
import hashlib
import io
import json
import math
import os
import zipfile
from array import array
from datetime import datetime, timezone
from pathlib import Path

STAGE = "SC001-E006-SPOT-SWAP-SYNC-AUDIT"
VERSION = "0.1"
EXPECTED_HEADER = ["instrument_name", "trade_id", "side", "price", "size", "created_time"]
SPOT_INST = "BTC-USDT"
SWAP_INST = "BTC-USDT-SWAP"
DAY_MS = 86_400_000
MIN_MS = 60_000
SECOND_MS = 1_000
CAPS_MS = (100, 250, 500, 1000, 5000)
TARGET_DAYS = tuple(f"2024-03-{d:02d}" for d in range(1, 21))
REQUIRED_LABELS = tuple(f"2024-03-{d:02d}" for d in range(1, 22))

DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
SPOT_ROOT = DATA_ROOT / "SC001_E006_SPOT_FEASIBILITY"
SPOT_ARCHIVES = SPOT_ROOT / "archives"
SPOT_META_REPORT = SPOT_ROOT / "sc001_e006_spot_metadata_preflight.json"
SPOT_BODY_REPORT = SPOT_ROOT / "sc001_e006_spot_body_integrity_report.json"
SWAP_ROOT = DATA_ROOT / "SC001_E003_OKX_MARCH_TRADES"
SWAP_ARCHIVES = SWAP_ROOT / "archives"
SWAP_REPORT = SWAP_ROOT / "sc001_e003_okx_march_trade_stage_report.json"
OUT_ROOT = DATA_ROOT / "SC001_E006_SYNC_AUDIT"
OUT_REPORT = OUT_ROOT / "sc001_e006_spot_swap_sync_audit_report.json"


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing required JSON: {path}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        fail(f"JSON object expected: {path}")
    return obj


def atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def day_start_ms(day: str) -> int:
    return int(datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)


def next_day(day: str) -> str:
    n = int(day[-2:]) + 1
    return f"2024-03-{n:02d}"


def nearest_rank(values, q: float) -> int | None:
    if not values:
        return None
    xs = sorted(values)
    i = max(0, min(len(xs) - 1, math.ceil(q * len(xs)) - 1))
    return int(xs[i])


def summarize(values) -> dict:
    if not values:
        return {"p50": None, "p95": None, "p99": None, "max": None}
    return {
        "p50": nearest_rank(values, 0.50),
        "p95": nearest_rank(values, 0.95),
        "p99": nearest_rank(values, 0.99),
        "max": int(max(values)),
    }


def spot_manifest() -> dict[str, dict]:
    meta = load_json(SPOT_META_REPORT)
    body = load_json(SPOT_BODY_REPORT)
    if meta.get("status") != "E006_SPOT_METADATA_PREFLIGHT_PASS":
        fail("SPOT metadata preflight is not PASS")
    if body.get("status") != "E006_SPOT_BODY_INTEGRITY_PASS":
        fail("SPOT body-integrity stage is not PASS")
    for k in ("basis_calculated", "returns_calculated", "pnl_calculated", "l2_accessed", "q2_accessed", "validation_or_final_accessed"):
        if body.get(k) is not False:
            fail(f"SPOT body firewall mismatch: {k}")
    rows = meta.get("archives") or []
    out = {}
    for row in rows:
        d = row.get("date_label")
        if d not in REQUIRED_LABELS:
            continue
        fn = row.get("filename")
        size = row.get("expected_bytes")
        if fn != f"{SPOT_INST}-trades-{d}.zip" or not isinstance(size, int) or size <= 0:
            fail(f"bad SPOT metadata identity: {d}")
        out[d] = {"filename": fn, "bytes": size, "path": SPOT_ARCHIVES / fn}
    if set(out) != set(REQUIRED_LABELS):
        fail("SPOT required label set mismatch")
    return out


def swap_manifest() -> dict[str, dict]:
    rep = load_json(SWAP_REPORT)
    if rep.get("stage") != "SC001-E003-OKX-MARCH-TRADE-STAGE" or rep.get("status") != "PASS":
        fail("SWAP March source stage is not PASS")
    if rep.get("q2_market_data_body_accessed") is not False or rep.get("validation_or_final_accessed") is not False:
        fail("SWAP source protected-data firewall mismatch")
    if rep.get("alpha_calculated") is not False or rep.get("pnl_calculated") is not False:
        fail("SWAP source alpha/P&L firewall mismatch")
    out = {}
    for row in rep.get("archives") or []:
        d = row.get("date")
        if d not in REQUIRED_LABELS:
            continue
        fn = row.get("filename")
        size = row.get("bytes")
        digest = row.get("sha256")
        if fn != f"{SWAP_INST}-trades-{d}.zip" or not isinstance(size, int) or size <= 0:
            fail(f"bad SWAP manifest identity: {d}")
        if not isinstance(digest, str) or len(digest) != 64:
            fail(f"bad SWAP manifest SHA: {d}")
        out[d] = {"filename": fn, "bytes": size, "sha256": digest, "path": SWAP_ARCHIVES / fn}
    if set(out) != set(REQUIRED_LABELS):
        fail("SWAP required label set mismatch")
    return out


def verify_archive(meta: dict, *, expected_sha: str | None = None) -> None:
    p = Path(meta["path"])
    if not p.exists() or p.stat().st_size != int(meta["bytes"]):
        fail(f"archive existence/size mismatch: {p}")
    if expected_sha is not None and sha256_file(p) != expected_sha:
        fail(f"archive SHA mismatch: {p.name}")
    with zipfile.ZipFile(p, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            fail(f"ZIP CRC failure {p.name}: {bad}")
        members = [m for m in zf.infolist() if not m.is_dir()]
        if len(members) != 1:
            fail(f"unexpected ZIP member count {p.name}: {len(members)}")


def read_target_timestamps(path: Path, instrument: str, lo: int, hi: int,
                           out_ts: array, stitch_state: dict) -> None:
    with zipfile.ZipFile(path, "r") as zf:
        members = [m for m in zf.infolist() if not m.is_dir()]
        if len(members) != 1:
            fail(f"unexpected ZIP member count: {path.name}")
        with zf.open(members[0], "r") as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            reader = csv.reader(text)
            if next(reader, None) != EXPECTED_HEADER:
                fail(f"header mismatch: {path.name}")
            src_last_ts = None
            src_last_tid = None
            for rownum, row in enumerate(reader, start=2):
                if not row:
                    continue
                if len(row) != 6:
                    fail(f"malformed row {path.name}:{rownum}")
                inst, tid_txt, _side, _price, _size, ts_txt = row
                if inst != instrument:
                    fail(f"instrument mismatch {path.name}:{rownum}: {inst}")
                try:
                    tid = int(tid_txt)
                    ts = parse_ts_ms(ts_txt)
                except Exception as exc:
                    raise RuntimeError(f"timestamp/id parse failure {path.name}:{rownum}") from exc
                if src_last_ts is not None and ts < src_last_ts:
                    fail(f"source timestamp reversal: {path.name}:{rownum}")
                if src_last_tid is not None and tid <= src_last_tid:
                    fail(f"source trade-id duplicate/backward: {path.name}:{rownum}")
                src_last_ts = ts
                src_last_tid = tid
                if lo <= ts < hi:
                    if stitch_state["last_ts"] is not None and ts < stitch_state["last_ts"]:
                        fail(f"stitched timestamp reversal for {instrument}")
                    if stitch_state["last_tid"] is not None and tid <= stitch_state["last_tid"]:
                        fail(f"stitched trade-id duplicate/backward for {instrument}")
                    stitch_state["last_ts"] = ts
                    stitch_state["last_tid"] = tid
                    out_ts.append(ts)


def reconstruct_day(day: str, instrument: str, manifest: dict[str, dict]) -> array:
    lo = day_start_ms(day)
    hi = lo + DAY_MS
    out = array("q")
    state = {"last_ts": None, "last_tid": None}
    for label in (day, next_day(day)):
        read_target_timestamps(Path(manifest[label]["path"]), instrument, lo, hi, out, state)
    if not out:
        fail(f"no admitted timestamps for {instrument} {day}")
    seen = bytearray(1440)
    for ts in out:
        seen[(int(ts) - lo) // MIN_MS] = 1
    if sum(seen) != 1440:
        fail(f"minute coverage failure {instrument} {day}: {sum(seen)}/1440")
    return out


def audit_day(day: str, spot_ts: array, swap_ts: array) -> tuple[dict, dict[str, array]]:
    lo = day_start_ms(day)
    total = 0
    paired = 0
    cap_counts = {c: 0 for c in CAPS_MS}
    spot_age = array("I")
    swap_age = array("I")
    max_age = array("I")
    skew = array("I")
    si = -1
    wi = -1
    for t in range(lo + SECOND_MS, lo + DAY_MS, SECOND_MS):
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
        ma = max(sa, wa)
        sk = abs(int(spot_ts[si]) - int(swap_ts[wi]))
        if min(sa, wa) <= 0:
            fail("causal age invariant breached")
        spot_age.append(sa)
        swap_age.append(wa)
        max_age.append(ma)
        skew.append(sk)
        for c in CAPS_MS:
            if sa <= c and wa <= c:
                cap_counts[c] += 1
    if total != 86_399:
        fail(f"unexpected one-second grid count for {day}: {total}")
    result = {
        "date": day,
        "grid_points": total,
        "paired_points": paired,
        "paired_share": paired / total,
        "spot_age_ms": summarize(spot_age),
        "swap_age_ms": summarize(swap_age),
        "max_leg_age_ms": summarize(max_age),
        "timestamp_skew_ms": summarize(skew),
        "both_age_cap_share": {str(c): cap_counts[c] / total for c in CAPS_MS},
    }
    return result, {"spot_age": spot_age, "swap_age": swap_age, "max_age": max_age, "skew": skew}


def main() -> int:
    spot = spot_manifest()
    swap = swap_manifest()
    for d in REQUIRED_LABELS:
        verify_archive(spot[d])
        verify_archive(swap[d], expected_sha=swap[d]["sha256"])
        print(f"SOURCE PASS {d}")

    per_day = []
    pooled_spot = array("I")
    pooled_swap = array("I")
    pooled_max = array("I")
    pooled_skew = array("I")
    pooled_caps = {c: 0 for c in CAPS_MS}
    total_grid = 0
    total_paired = 0

    for d in TARGET_DAYS:
        s = reconstruct_day(d, SPOT_INST, spot)
        w = reconstruct_day(d, SWAP_INST, swap)
        row, vals = audit_day(d, s, w)
        per_day.append(row)
        total_grid += row["grid_points"]
        total_paired += row["paired_points"]
        pooled_spot.extend(vals["spot_age"])
        pooled_swap.extend(vals["swap_age"])
        pooled_max.extend(vals["max_age"])
        pooled_skew.extend(vals["skew"])
        for c in CAPS_MS:
            pooled_caps[c] += round(row["both_age_cap_share"][str(c)] * row["grid_points"])
        print(f"SYNC AUDIT {d} paired={row['paired_points']}/{row['grid_points']}")

    pooled = {
        "grid_points": total_grid,
        "paired_points": total_paired,
        "paired_share": total_paired / total_grid,
        "spot_age_ms": summarize(pooled_spot),
        "swap_age_ms": summarize(pooled_swap),
        "max_leg_age_ms": summarize(pooled_max),
        "timestamp_skew_ms": summarize(pooled_skew),
        "both_age_cap_share": {str(c): pooled_caps[c] / total_grid for c in CAPS_MS},
    }

    gates = {
        "all_20_days": len(per_day) == 20,
        "paired_share_ge_0_9999": pooled["paired_share"] >= 0.9999,
        "both_age_1000ms_share_ge_0_99": pooled["both_age_cap_share"]["1000"] >= 0.99,
        "both_age_5000ms_share_ge_0_999": pooled["both_age_cap_share"]["5000"] >= 0.999,
        "max_leg_age_p99_le_1000ms": pooled["max_leg_age_ms"]["p99"] is not None and pooled["max_leg_age_ms"]["p99"] <= 1000,
    }
    status = "E006_SYNC_AUDIT_PASS" if all(gates.values()) else "E006_SYNC_AUDIT_REVIEW"

    report = {
        "stage": STAGE,
        "version": VERSION,
        "status": status,
        "audit_grid": "exact UTC 1-second boundaries strictly inside each day",
        "selection_semantics": "last trade timestamp strictly before boundary; no price read into synchronization metrics",
        "target_days": list(TARGET_DAYS),
        "required_archive_labels": list(REQUIRED_LABELS),
        "boundary_neighbor_label": "2024-03-21",
        "per_day": per_day,
        "pooled": pooled,
        "gates": gates,
        "spot_archive_identities": [
            {"date": d, "filename": spot[d]["filename"], "bytes": spot[d]["bytes"]} for d in REQUIRED_LABELS
        ],
        "swap_archive_identities": [
            {"date": d, "filename": swap[d]["filename"], "bytes": swap[d]["bytes"], "sha256": swap[d]["sha256"]} for d in REQUIRED_LABELS
        ],
        "spot_swap_price_compared": False,
        "basis_calculated": False,
        "returns_calculated": False,
        "pnl_calculated": False,
        "l2_accessed": False,
        "q2_accessed": False,
        "validation_or_final_accessed": False,
        "alpha_calculated": False,
    }
    atomic_json(OUT_REPORT, report)

    print(status)
    print("target_day_count =", len(per_day))
    print("grid_points =", pooled["grid_points"])
    print("paired_share =", pooled["paired_share"])
    print("max_leg_age_p99_ms =", pooled["max_leg_age_ms"]["p99"])
    print("both_age_le_1000ms_share =", pooled["both_age_cap_share"]["1000"])
    print("both_age_le_5000ms_share =", pooled["both_age_cap_share"]["5000"])
    print("spot_swap_price_compared = False")
    print("basis/returns/P&L/alpha calculated = False")
    print("L2/Q2/Validation/Final = CLOSED")
    print("report =", OUT_REPORT)
    return 0 if status == "E006_SYNC_AUDIT_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
