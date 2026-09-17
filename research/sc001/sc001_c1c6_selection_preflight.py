from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

STAGE = "SC001-C1C6-SELECTION-PREFLIGHT"
PASS = "SC001_C1C6_SELECTION_PREFLIGHT_PASS"
FAIL = "SC001_C1C6_SELECTION_PREFLIGHT_FAIL"

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
OUT_DIR = DATA_ROOT / "SC001_C1C6_SELECTION_PREFLIGHT"
OUT = OUT_DIR / "sc001_c1c6_selection_preflight_report.json"

RUNNER = ROOT / "research/sc001/sc001_c1c6_selection_preflight.py"
PROTOCOL = ROOT / "docs/research/sc001-c1-c6-selection-preflight-protocol-v0.1.md"
FREEZE = ROOT / "docs/research/sc001-c1-c6-selection-preflight-implementation-freeze-v1.0.json"

JULY_ACQ = DATA_ROOT / "SC001_E007R1_TRADE_ACQUISITION"
JULY_SEM = DATA_ROOT / "SC001_E007R1_TRADE_SEMANTIC_INTEGRITY" / "sc001_e007r1_trade_semantic_integrity_report.json"
SEP_ACQ = DATA_ROOT / "SC001_E009_TRADE_ACQUISITION"
SEP_SEM = DATA_ROOT / "SC001_E009_TRADE_SEMANTIC_INTEGRITY" / "sc001_e009_trade_semantic_integrity_report.json"

E006_SPOT = DATA_ROOT / "SC001_E006_SPOT_FEASIBILITY"
E006_SPOT_REPORT = E006_SPOT / "sc001_e006_spot_body_integrity_report.json"
E006_SWAP = DATA_ROOT / "SC001_E003_OKX_MARCH_TRADES"
E006_SWAP_REPORT = E006_SWAP / "sc001_e003_okx_march_trade_stage_report.json"

ASSETS = ("BTC", "ETH", "DOGE", "ORDI", "UNI", "XRP", "OP", "BCH")
HOLDOUT_ASSETS = ("SOL", "FIL", "LTC", "SUI")
BODY_SUFFIXES = (".zip", ".csv", ".gz", ".parquet", ".feather")


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing required JSON: {path}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        fail(f"JSON object expected: {path}")
    return obj


def atomic_json(path: Path, obj: dict) -> None:
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


def git_blob(path: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(ROOT), "hash-object", str(path)],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception as exc:
        raise RuntimeError(f"git hash-object failed for {path}") from exc


def date_range(start: str, end: str) -> list[str]:
    a = date.fromisoformat(start)
    b = date.fromisoformat(end)
    out = []
    while a <= b:
        out.append(a.isoformat())
        a += timedelta(days=1)
    return out


def check_identity_freeze() -> dict:
    fr = load_json(FREEZE)
    if fr.get("status") != "FROZEN_BEFORE_SELECTION_PREFLIGHT_RUN":
        fail("implementation freeze status mismatch")
    r = git_blob(RUNNER)
    p = git_blob(PROTOCOL)
    if fr.get("runner_git_blob_sha") != r:
        fail(f"runner identity mismatch {r} != {fr.get('runner_git_blob_sha')}")
    if fr.get("protocol_git_blob_sha") != p:
        fail(f"protocol identity mismatch {p} != {fr.get('protocol_git_blob_sha')}")
    return {"runner_git_blob_sha": r, "protocol_git_blob_sha": p}


def verify_trade_sandbox(
    *,
    name: str,
    acq_root: Path,
    sem_path: Path,
    verify_filename: str,
    verify_status: str,
    semantic_status: str,
    batch_prefix: str,
    semantic_firewalls: tuple[str, ...],
) -> dict:
    verify = load_json(acq_root / verify_filename)
    sem = load_json(sem_path)

    if verify.get("status") != verify_status:
        fail(f"{name} acquisition verify status mismatch")
    if int(verify.get("verified_files", 0)) != 128:
        fail(f"{name} verified_files mismatch")
    if sem.get("status") != semantic_status:
        fail(f"{name} semantic status mismatch")
    if int(sem.get("source_files_qualified", 0)) != 128:
        fail(f"{name} semantic source count mismatch")
    if int(sem.get("reconstructed_utc_days_qualified", 0)) != 120:
        fail(f"{name} semantic day count mismatch")

    for key in semantic_firewalls:
        if sem.get(key) is not False:
            fail(f"{name} semantic firewall mismatch: {key}")

    acquired: dict[str, dict] = {}
    for b in "abcd":
        rp = acq_root / "reports" / f"batch_{b}.json"
        x = load_json(rp)
        expected = f"{batch_prefix}_BATCH_{b.upper()}_PASS"
        if x.get("status") != expected or int(x.get("verified_files", 0)) != 32:
            fail(f"{name} batch {b} report mismatch")
        for row in x.get("files") or []:
            fn = row.get("filename")
            inst = row.get("instrument")
            if not isinstance(fn, str) or not isinstance(inst, str):
                fail(f"{name} malformed batch file row")
            if fn in acquired:
                fail(f"{name} duplicate archive identity: {fn}")
            acquired[fn] = row

    if len(acquired) != 128:
        fail(f"{name} acquired manifest count {len(acquired)} != 128")

    total = 0
    per_asset = {s: 0 for s in ASSETS}
    for i, fn in enumerate(sorted(acquired), 1):
        row = acquired[fn]
        inst = row["instrument"]
        sym = inst.split("-")[0]
        if sym not in per_asset:
            fail(f"{name} unexpected asset in manifest: {inst}")
        path = acq_root / "archives" / sym / fn
        expected_bytes = int(row.get("local_bytes", row.get("expected_bytes", -1)))
        expected_sha = row.get("sha256")
        if expected_bytes <= 0 or not isinstance(expected_sha, str) or len(expected_sha) != 64:
            fail(f"{name} invalid recorded identity: {fn}")
        if not path.exists() or path.stat().st_size != expected_bytes:
            fail(f"{name} archive size/existence mismatch: {path}")
        actual_sha = sha256_file(path)
        if actual_sha != expected_sha:
            fail(f"{name} archive SHA mismatch: {fn}")
        total += expected_bytes
        per_asset[sym] += 1
        if i % 32 == 0:
            print(f"{name}: verified {i}/128 archive identities", flush=True)

    if any(v != 16 for v in per_asset.values()):
        fail(f"{name} per-asset archive counts mismatch: {per_asset}")
    if int(verify.get("verified_total_bytes", total)) != total:
        fail(f"{name} aggregate byte mismatch")

    return {
        "verify_status": verify.get("status"),
        "semantic_status": sem.get("status"),
        "verified_files": 128,
        "verified_total_bytes": total,
        "per_asset_archive_files": per_asset,
        "source_files_qualified": 128,
        "reconstructed_utc_days_qualified": 120,
        "sha256_reverified_now": True,
    }


def verify_optional_legacy_e006() -> dict:
    spot_exists = E006_SPOT_REPORT.exists()
    swap_exists = E006_SWAP_REPORT.exists()
    out = {
        "spot_report_present": spot_exists,
        "swap_report_present": swap_exists,
        "ready": False,
        "warnings": [],
    }
    if not spot_exists and not swap_exists:
        out["state"] = "MISSING_OPTIONAL"
        return out
    if not spot_exists or not swap_exists:
        out["state"] = "PARTIAL_OPTIONAL"
        out["warnings"].append("legacy E006 spot/swap report pair incomplete")
        return out

    try:
        spot = load_json(E006_SPOT_REPORT)
        swap = load_json(E006_SWAP_REPORT)
        if spot.get("status") != "E006_SPOT_BODY_INTEGRITY_PASS":
            raise RuntimeError("legacy E006 spot body report not PASS")
        if swap.get("stage") != "SC001-E003-OKX-MARCH-TRADE-STAGE" or swap.get("status") != "PASS":
            raise RuntimeError("legacy E006 swap source report not PASS")

        required = set(date_range("2024-03-01", "2024-03-21"))
        spot_rows = {r.get("date_label"): r for r in (spot.get("archives") or []) if r.get("date_label") in required}
        swap_rows = {r.get("date"): r for r in (swap.get("archives") or []) if r.get("date") in required}
        if set(spot_rows) != required:
            raise RuntimeError(f"legacy E006 spot labels missing: {sorted(required-set(spot_rows))}")
        if set(swap_rows) != required:
            raise RuntimeError(f"legacy E006 swap labels missing: {sorted(required-set(swap_rows))}")

        def verify_rows(root: Path, rows: dict[str, dict], date_key: str) -> int:
            n = 0
            for d in sorted(rows):
                r = rows[d]
                fn = r.get("filename")
                expected_bytes = int(r.get("bytes", r.get("local_bytes", -1)))
                expected_sha = r.get("sha256")
                if not isinstance(fn, str) or expected_bytes <= 0 or not isinstance(expected_sha, str) or len(expected_sha) != 64:
                    raise RuntimeError(f"bad legacy archive identity for {d}")
                p = root / "archives" / fn
                if not p.exists() or p.stat().st_size != expected_bytes:
                    raise RuntimeError(f"legacy archive size/existence mismatch: {p}")
                if sha256_file(p) != expected_sha:
                    raise RuntimeError(f"legacy archive SHA mismatch: {fn}")
                n += 1
            return n

        out["spot_archives_verified"] = verify_rows(E006_SPOT, spot_rows, "date_label")
        out["swap_archives_verified"] = verify_rows(E006_SWAP, swap_rows, "date")
        out["ready"] = True
        out["state"] = "READY_OPTIONAL"
        return out
    except Exception as exc:
        out["state"] = "INCONSISTENT_OPTIONAL"
        out["warnings"].append(str(exc))
        return out


def body_files() -> list[Path]:
    if not DATA_ROOT.exists():
        return []
    out = []
    for p in DATA_ROOT.rglob("*"):
        if not p.is_file():
            continue
        lower = p.name.lower()
        if any(lower.endswith(s) for s in BODY_SUFFIXES):
            out.append(p)
    return out


def path_has_any_date(text: str, dates: list[str]) -> bool:
    return any(d in text for d in dates)


def scan_protected_bodies(files: list[Path]) -> list[str]:
    july_holdout = date_range("2024-07-01", "2024-07-14")
    july_gap = date_range("2024-07-16", "2024-07-30")
    august = date_range("2024-08-01", "2024-08-30")
    sep_holdout = date_range("2024-09-01", "2024-09-14")
    october = date_range("2024-10-01", "2024-10-14")
    march_confirm = date_range("2024-03-22", "2024-03-30")

    hits = []
    for p in files:
        text = str(p).upper()
        if path_has_any_date(text, july_gap) or path_has_any_date(text, august) or path_has_any_date(text, october):
            hits.append(str(p))
            continue
        if path_has_any_date(text, july_holdout) or path_has_any_date(text, sep_holdout):
            if any(f"{s}-USDT" in text or f"/{s}/" in text for s in HOLDOUT_ASSETS):
                hits.append(str(p))
                continue
        if path_has_any_date(text, march_confirm):
            if "SC001_E006_SPOT_FEASIBILITY" in text or "SC001_E003_OKX_MARCH_TRADES" in text:
                hits.append(str(p))
    return sorted(set(hits))


def detect_c1_multiasset_spot(files: list[Path]) -> dict:
    allowed_dates = date_range("2024-07-01", "2024-07-14") + date_range("2024-09-01", "2024-09-14")
    by_asset = {s: 0 for s in ASSETS}
    examples = []
    for p in files:
        text = str(p).upper()
        if not path_has_any_date(text, allowed_dates):
            continue
        if "SWAP" in text:
            continue
        for s in ASSETS:
            if f"{s}-USDT" in text or f"/{s}/" in text:
                by_asset[s] += 1
                if len(examples) < 20:
                    examples.append(str(p))
                break
    ready_assets = [s for s, n in by_asset.items() if n > 0]
    return {
        "probable_spot_body_files_by_asset": by_asset,
        "assets_with_any_probable_spot_body": ready_assets,
        "all_8_assets_have_any_probable_spot_body": len(ready_assets) == 8,
        "data_gap_expected": len(ready_assets) < 8,
        "examples": examples,
    }


def run_preflight() -> dict:
    identity = check_identity_freeze()

    try:
        import numpy as np
    except Exception as exc:
        raise RuntimeError("NumPy import failed") from exc

    july = verify_trade_sandbox(
        name="JULY_E007R1",
        acq_root=JULY_ACQ,
        sem_path=JULY_SEM,
        verify_filename="sc001_e007r1_trade_acquisition_verify_report.json",
        verify_status="E007R1_TRADE_ACQUISITION_VERIFY_PASS",
        semantic_status="E007R1_TRADE_SEMANTIC_INTEGRITY_PASS",
        batch_prefix="E007R1_TRADE_ACQUISITION",
        semantic_firewalls=("asset_holdout_accessed", "august_confirmation_accessed"),
    )

    sep = verify_trade_sandbox(
        name="SEPTEMBER_E009",
        acq_root=SEP_ACQ,
        sem_path=SEP_SEM,
        verify_filename="sc001_e009_trade_acquisition_verify_report.json",
        verify_status="E009_TRADE_ACQUISITION_VERIFY_PASS",
        semantic_status="E009_TRADE_SEMANTIC_INTEGRITY_PASS",
        batch_prefix="E009_TRADE_ACQUISITION",
        semantic_firewalls=("asset_holdout_accessed", "october_confirmation_accessed", "august_repurposed"),
    )

    files = body_files()
    protected_hits = scan_protected_bodies(files)
    if protected_hits:
        fail(f"protected market-body files detected: {protected_hits[:5]}{' ...' if len(protected_hits)>5 else ''}")

    legacy = verify_optional_legacy_e006()
    c1_spot = detect_c1_multiasset_spot(files)

    rep = {
        "stage": STAGE,
        "status": PASS,
        **identity,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "data_root": str(DATA_ROOT),
        "july_e007r1": july,
        "september_e009": sep,
        "legacy_e006_optional": legacy,
        "c1_july_september_multiasset_spot_inventory": c1_spot,
        "protected_market_body_hits": [],
        "protected_market_body_hit_count": 0,
        "market_body_files_scanned": len(files),
        "strategy_signal_calculated": False,
        "sentinel_outcome_calculated": False,
        "pnl_calculated": False,
        "promotional_alpha_accessed": False,
        "july_asset_holdout_accessed": False,
        "july_gap_accessed": False,
        "august_protected_accessed": False,
        "september_asset_holdout_accessed": False,
        "october_confirmation_accessed": False,
        "legacy_e006_confirmation_accessed": False,
    }
    atomic_json(OUT, rep)
    return rep


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", nargs="?", default="preflight", choices=["preflight"])
    ap.parse_args()

    try:
        rep = run_preflight()
    except Exception as exc:
        fail_rep = {
            "stage": STAGE,
            "status": FAIL,
            "error": str(exc),
            "strategy_signal_calculated": False,
            "sentinel_outcome_calculated": False,
            "pnl_calculated": False,
            "promotional_alpha_accessed": False,
        }
        try:
            atomic_json(OUT, fail_rep)
        except Exception:
            pass
        print(FAIL)
        print("error =", exc)
        print("report =", OUT)
        return 2

    print(PASS)
    print("python =", rep["python_version"], "numpy =", rep["numpy_version"])
    print("July E007R1 archives verified =", rep["july_e007r1"]["verified_files"])
    print("September E009 archives verified =", rep["september_e009"]["verified_files"])
    print("legacy E006 optional state =", rep["legacy_e006_optional"]["state"])
    print("C1 multi-asset spot data gap expected =", rep["c1_july_september_multiasset_spot_inventory"]["data_gap_expected"])
    print("protected market-body hits = 0")
    print("strategy signal calculated = False")
    print("sentinel outcome calculated = False")
    print("PnL calculated = False")
    print("promotional alpha accessed = False")
    print("report =", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
