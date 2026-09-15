"""SC001-E008 no-alpha/no-P&L data inventory audit.

Purpose:
- locate qualified Q009A/Q009B L2 reports and archive bodies on the current VPS;
- locate corresponding BTC-USDT-SWAP trade tapes for the same four dates;
- record identities/sizes only.

NO fill simulation. NO spread capture. NO maker P&L. NO profitability.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone

STAGE = "SC001-E008-DATA-INVENTORY"
VERSION = "0.1"
DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
OUT_DIR = DATA_ROOT / "SC001_E008_DATA_INVENTORY"
OUT_JSON = OUT_DIR / "sc001_e008_data_inventory_report.json"

EXPECTED = {
    "2024-01-14": {
        "batch": "A",
        "l2_filename": "BTC-USDT-SWAP-L2orderbook-400lv-2024-01-14.tar.gz",
        "l2_bytes": 426_641_072,
    },
    "2024-01-31": {
        "batch": "A",
        "l2_filename": "BTC-USDT-SWAP-L2orderbook-400lv-2024-01-31.tar.gz",
        "l2_bytes": 519_114_508,
    },
    "2024-02-12": {
        "batch": "B",
        "l2_filename": "BTC-USDT-SWAP-L2orderbook-400lv-2024-02-12.tar.gz",
        "l2_bytes": 601_976_188,
    },
    "2024-02-13": {
        "batch": "B",
        "l2_filename": "BTC-USDT-SWAP-L2orderbook-400lv-2024-02-13.tar.gz",
        "l2_bytes": 550_675_409,
    },
}

REPORT_CANDIDATES = {
    "A": [
        DATA_ROOT / "SC001_DATA_Q009A_OKX_L2_BATCH_A" / "sc001_data_q009a_okx_l2_batch_a_report.json",
    ],
    "B": [
        DATA_ROOT / "SC001_DATA_Q009B_OKX_L2_BATCH_B" / "sc001_data_q009b_okx_l2_batch_b_report.json",
    ],
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    text = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with tmp.open("w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def find_exact(filename: str) -> list[Path]:
    out = []
    direct = DATA_ROOT / filename
    if direct.exists():
        out.append(direct)
    try:
        for p in DATA_ROOT.rglob(filename):
            if p.is_file() and p not in out:
                out.append(p)
    except Exception:
        pass
    return sorted(out)


def find_trade_candidates(day: str) -> list[Path]:
    names = [
        f"BTC-USDT-SWAP-trades-{day}.zip",
        f"BTC-USDT-SWAP-trades-{day}.tar.gz",
        f"BTC-USDT-SWAP-trades-{day}.csv.gz",
    ]
    found = []
    for name in names:
        for p in find_exact(name):
            if p not in found:
                found.append(p)
    if not found:
        # Last-resort name search, still identity-only and no body parsing.
        try:
            for p in DATA_ROOT.rglob(f"*{day}*"):
                if not p.is_file():
                    continue
                n = p.name.lower()
                if "btc-usdt-swap" in n and "trade" in n and p not in found:
                    found.append(p)
        except Exception:
            pass
    return sorted(found)


def load_report(batch: str) -> dict:
    paths = [p for p in REPORT_CANDIDATES[batch] if p.exists()]
    if not paths:
        # Search by known report basename in case the workspace was staged elsewhere.
        basename = (
            "sc001_data_q009a_okx_l2_batch_a_report.json"
            if batch == "A"
            else "sc001_data_q009b_okx_l2_batch_b_report.json"
        )
        paths = find_exact(basename)
    if not paths:
        return {"present": False, "paths": []}
    p = paths[0]
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"present": True, "path": str(p), "parse_error": repr(exc), "status": None}
    return {
        "present": True,
        "path": str(p),
        "sha256": sha256_file(p),
        "stage": obj.get("stage"),
        "status": obj.get("overall_status"),
        "days": [
            {"date": x.get("date"), "status": x.get("status")}
            for x in (obj.get("days") or []) if isinstance(x, dict)
        ],
    }


def day_status_from_report(report: dict, day: str) -> str | None:
    for x in report.get("days") or []:
        if x.get("date") == day:
            return x.get("status")
    return None


def main() -> int:
    reports = {b: load_report(b) for b in ("A", "B")}
    days = []
    errors = []

    for day, meta in EXPECTED.items():
        l2_paths = find_exact(meta["l2_filename"])
        l2_rows = []
        for p in l2_paths:
            try:
                l2_rows.append({"path": str(p), "bytes": p.stat().st_size})
            except Exception:
                pass
        exact_l2 = [x for x in l2_rows if x["bytes"] == meta["l2_bytes"]]

        trades = find_trade_candidates(day)
        trade_rows = []
        for p in trades:
            try:
                trade_rows.append({"path": str(p), "filename": p.name, "bytes": p.stat().st_size})
            except Exception:
                pass

        batch_report = reports[meta["batch"]]
        report_day_status = day_status_from_report(batch_report, day)
        report_pass = batch_report.get("status") == "PASS" and report_day_status == "FULL_DAY_PASS"
        l2_pass = len(exact_l2) >= 1
        trade_present = len(trade_rows) >= 1

        row = {
            "date": day,
            "batch": meta["batch"],
            "expected_l2_filename": meta["l2_filename"],
            "expected_l2_bytes": meta["l2_bytes"],
            "batch_report_pass": report_pass,
            "batch_day_status": report_day_status,
            "l2_archive_present_exact_size": l2_pass,
            "l2_candidates": l2_rows,
            "trade_tape_present": trade_present,
            "trade_candidates": trade_rows,
        }
        days.append(row)
        if not report_pass:
            errors.append(f"{day}: qualified Q009 batch/day PASS report not available on VPS")
        if not l2_pass:
            errors.append(f"{day}: exact-size qualified L2 archive body not found on VPS")
        if not trade_present:
            errors.append(f"{day}: corresponding BTC-USDT-SWAP trade tape not found on VPS")

        print(
            f"INVENTORY {day} report={'PASS' if report_pass else 'MISSING/REVIEW'} "
            f"l2={'PRESENT' if l2_pass else 'MISSING'} trades={'PRESENT' if trade_present else 'MISSING'}"
        )

    all_inputs = not errors
    status = "E008_DATA_INVENTORY_PASS" if all_inputs else "E008_DATA_INVENTORY_REVIEW"
    report = {
        "stage": STAGE,
        "version": VERSION,
        "status": status,
        "data_root": str(DATA_ROOT),
        "batch_reports": reports,
        "days": days,
        "errors": errors,
        "queue_model_inputs_complete": all_inputs,
        "exact_order_ids_assumed": False,
        "fill_simulation_calculated": False,
        "spread_capture_calculated": False,
        "maker_pnl_calculated": False,
        "profitability_calculated": False,
        "tfi_used": False,
        "q2_accessed": False,
        "validation_or_final_accessed": False,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    atomic_json(OUT_JSON, report)

    print(status)
    print("qualified_day_count =", sum(1 for x in days if x["batch_report_pass"] and x["l2_archive_present_exact_size"] and x["trade_tape_present"]), "/", len(days))
    print("fill/spread_capture/maker_PnL/profitability calculated = False")
    print("TFI used = False")
    print("Q2/Validation/Final = CLOSED")
    print("report =", OUT_JSON)
    if errors:
        print("=== MISSING / REVIEW ITEMS ===")
        for e in errors:
            print("REVIEW", e)
    return 0 if status == "E008_DATA_INVENTORY_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
