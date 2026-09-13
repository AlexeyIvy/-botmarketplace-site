"""SC001-DATA-Q009B — OKX Q1 L2 Batch B.

Downloads/replays the final two frozen Q1 L2 days needed by the already
frozen four-day midquote confirmation. Data engineering only: no TFI,
no midquote alpha, no P&L, no Q2/Validation/Final.
Reuses the frozen Q008 replay implementation from a pinned commit.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from urllib.request import Request, urlopen

STAGE = "SC001-DATA-Q009B-OKX-L2-Q1-BATCH-B"
VERSION = "0.1"
PROTOCOL_COMMIT = "75e5f052014d39601191e1a0f1263d52476d872e"

Q008_LIB_COMMIT = "d4aa9720e43a39e215af7d866bd273c68340381c"
Q008_LIB_PATH = "research/sc001/sc001_data_q008_okx_l2_full_day_pilot.py"
Q008_LIB_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + Q008_LIB_COMMIT + "/" + Q008_LIB_PATH
)
MAX_LIB_BYTES = 2_000_000

DOWNLOAD = Path("/storage/emulated/0/Download")
BATCH_ROOT = DOWNLOAD / "SC001_DATA_Q009B_OKX_L2_BATCH_B"
REPORT = BATCH_ROOT / "sc001_data_q009b_okx_l2_batch_b_report.json"
SUMMARY = BATCH_ROOT / "sc001_data_q009b_okx_l2_batch_b_summary.md"
SAFETY = BATCH_ROOT / "sc001_data_q009b_okx_l2_batch_b_final_safety.json"

Q007_REPORT = (
    DOWNLOAD / "SC001_DATA_Q007_OKX_L2_Q1_PREFLIGHT" /
    "sc001_data_q007_okx_l2_q1_preflight_report.json"
)
Q008_REPORT = (
    DOWNLOAD / "SC001_DATA_Q008_OKX_L2_PILOT" /
    "sc001_data_q008_okx_l2_pilot_report.json"
)
Q009A_REPORT = (
    DOWNLOAD / "SC001_DATA_Q009A_OKX_L2_BATCH_A" /
    "sc001_data_q009a_okx_l2_batch_a_report.json"
)

SESSION_DOWNLOAD_CAP_BYTES = 1_350_000_000
WORKSPACE_CAP_BYTES = 1_350_000_000
PER_FILE_CAP_BYTES = 650_000_000
MIN_FREE_RESERVE_BYTES = 4_000_000_000
EXPECTED_BATCH_BYTES = 1_152_651_597

DATES = (
    (
        "2024-02-12",
        "BTC-USDT-SWAP-L2orderbook-400lv-2024-02-12.tar.gz",
        601_976_188,
    ),
    (
        "2024-02-13",
        "BTC-USDT-SWAP-L2orderbook-400lv-2024-02-13.tar.gz",
        550_675_409,
    ),
)


def dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def free_bytes() -> int:
    return shutil.disk_usage(DOWNLOAD).free


def atomic_text(path: Path, text: str) -> None:
    raw = text.encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("wb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def atomic_json(path: Path, obj) -> None:
    atomic_text(
        path,
        json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True, default=str),
    )


def verify_prerequisites() -> dict:
    if not Q007_REPORT.exists():
        raise RuntimeError("missing Q007 PASS report")
    q7 = json.loads(Q007_REPORT.read_text(encoding="utf-8"))
    if (
        q7.get("overall_status") != "PASS"
        or q7.get("stage") != "SC001-DATA-Q007-OKX-L2-Q1-PREFLIGHT"
    ):
        raise RuntimeError("Q007 prerequisite is not PASS")
    rows = {x.get("date"): x for x in (q7.get("dates") or [])}
    for date, filename, size in DATES:
        row = rows.get(date)
        if row is None or row.get("status") != "PASS":
            raise RuntimeError(f"Q007 missing/non-PASS date {date}")
        if (
            row.get("filename") != filename
            or (row.get("head") or {}).get("content_length") != size
        ):
            raise RuntimeError(f"Q007 identity/size mismatch {date}")

    if not Q008_REPORT.exists():
        raise RuntimeError("missing Q008 FULL_DAY_PASS report")
    q8 = json.loads(Q008_REPORT.read_text(encoding="utf-8"))
    if (
        q8.get("overall_status") != "FULL_DAY_PASS"
        or q8.get("stage") != "SC001-DATA-Q008-OKX-L2-FULL-DAY-PILOT"
    ):
        raise RuntimeError("Q008 prerequisite is not FULL_DAY_PASS")
    if (
        q8.get("midquote_response_calculated") is not False
        or q8.get("strategy_pnl_calculated") is not False
    ):
        raise RuntimeError("Q008 firewall mismatch")

    if not Q009A_REPORT.exists():
        raise RuntimeError("missing Q009A PASS report")
    q9a = json.loads(Q009A_REPORT.read_text(encoding="utf-8"))
    if (
        q9a.get("overall_status") != "PASS"
        or q9a.get("stage") != "SC001-DATA-Q009A-OKX-L2-Q1-BATCH-A"
    ):
        raise RuntimeError("Q009A prerequisite is not PASS")
    for key in (
        "strategy_features_calculated",
        "midquote_response_calculated",
        "strategy_pnl_calculated",
        "execution_profitability_calculated",
        "q2_okx_accessed",
        "validation_or_final_accessed",
    ):
        if q9a.get(key) is not False:
            raise RuntimeError(f"Q009A firewall mismatch: {key}")

    return {
        "q007": str(Q007_REPORT),
        "q008": str(Q008_REPORT),
        "q008_status": q8.get("overall_status"),
        "q009a": str(Q009A_REPORT),
        "q009a_status": q9a.get("overall_status"),
    }


def load_q008_library():
    req = Request(
        Q008_LIB_URL,
        headers={"User-Agent": "BotMarketplace-SC001-Q009B/0.1"},
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(MAX_LIB_BYTES + 1)
    if len(raw) > MAX_LIB_BYTES:
        raise RuntimeError("Q008 library source exceeds safety cap")
    required = [
        b'STAGE = "SC001-DATA-Q008-OKX-L2-FULL-DAY-PILOT"',
        b"def replay_full_archive",
        b"def download_resumable",
        b"FULL_DAY_PASS",
    ]
    if not raw or not all(x in raw for x in required):
        raise RuntimeError("pinned Q008 replay library identity mismatch")
    ns = {
        "__name__": "sc001_q008_replay_library",
        "__file__": "<pinned-q008-library>",
        "__package__": None,
    }
    exec(compile(raw, "<pinned-q008-library>", "exec"), ns, ns)
    return ns, hashlib.sha256(raw).hexdigest(), len(raw)


def write_batch_outputs(report: dict) -> None:
    atomic_json(REPORT, report)
    lines = [
        "# SC001-DATA-Q009B — OKX Q1 L2 Batch B",
        "",
        f"- Overall: `{report.get('overall_status')}`",
        f"- Expected batch bytes: {EXPECTED_BATCH_BYTES}",
        f"- Market-data bytes read this run: {report.get('network_market_data_bytes_read', 0)}",
        "- Strategy features / midquote alpha / P&L: **NO**",
        "- Q2 / Validation / Final: **NO**",
        "",
        "## Days",
    ]
    for x in report.get("days", []):
        r = x.get("replay") or {}
        a = x.get("archive") or {}
        lines.append(
            f"- {x.get('date')}: **{x.get('status')}**; bytes={a.get('bytes')}; "
            f"records={r.get('records_parsed')}; minutes={r.get('minute_buckets_observed')}/1440; "
            f"crossed={r.get('crossed_book_states')}; empty={r.get('empty_book_states')}; "
            f"max_gap_ms={r.get('max_interrecord_gap_ms')}"
        )
    lines += [
        "",
        "## Boundary",
        "Data-only acquisition/replay. If PASS, stop acquisition and run the already frozen four-day midquote confirmation exactly once.",
    ]
    atomic_text(SUMMARY, "\n".join(lines) + "\n")
    atomic_json(
        SAFETY,
        {
            "stage": STAGE,
            "network_market_data_bytes_read": report.get(
                "network_market_data_bytes_read", 0
            ),
            "workspace_bytes_after_outputs": dir_size(BATCH_ROOT),
            "free_bytes_after_outputs": free_bytes(),
            "caps": {
                "session_download": SESSION_DOWNLOAD_CAP_BYTES,
                "workspace": WORKSPACE_CAP_BYTES,
                "per_file": PER_FILE_CAP_BYTES,
                "reserve": MIN_FREE_RESERVE_BYTES,
            },
            "strategy_features_calculated": False,
            "midquote_response_calculated": False,
            "strategy_pnl_calculated": False,
            "execution_profitability_calculated": False,
            "q2_okx_accessed": False,
            "validation_or_final_accessed": False,
        },
    )


def main() -> None:
    BATCH_ROOT.mkdir(parents=True, exist_ok=True)
    if EXPECTED_BATCH_BYTES >= 2_000_000_000:
        raise RuntimeError("project 2 GB per-run hard cap violated before start")
    if dir_size(BATCH_ROOT) > WORKSPACE_CAP_BYTES:
        raise RuntimeError("existing batch workspace exceeds cap")
    if (
        free_bytes() - max(0, EXPECTED_BATCH_BYTES - dir_size(BATCH_ROOT))
        < MIN_FREE_RESERVE_BYTES
    ):
        raise RuntimeError("free-space reserve would be violated")

    prereq = verify_prerequisites()
    lib, lib_sha, lib_bytes = load_q008_library()

    lib["network_bytes_read"] = 0
    lib["SESSION_DOWNLOAD_CAP_BYTES"] = SESSION_DOWNLOAD_CAP_BYTES
    lib["PER_FILE_CAP_BYTES"] = PER_FILE_CAP_BYTES
    lib["MIN_FREE_RESERVE_BYTES"] = MIN_FREE_RESERVE_BYTES
    lib["PROTOCOL_COMMIT"] = PROTOCOL_COMMIT

    report = {
        "stage": STAGE,
        "version": VERSION,
        "protocol_commit": PROTOCOL_COMMIT,
        "prerequisites": prereq,
        "q008_library_commit": Q008_LIB_COMMIT,
        "q008_library_sha256": lib_sha,
        "q008_library_source_bytes": lib_bytes,
        "expected_batch_bytes": EXPECTED_BATCH_BYTES,
        "strategy_features_calculated": False,
        "midquote_response_calculated": False,
        "strategy_pnl_calculated": False,
        "execution_profitability_calculated": False,
        "q2_okx_accessed": False,
        "validation_or_final_accessed": False,
        "days": [],
    }

    try:
        for date, filename, size in DATES:
            if dir_size(BATCH_ROOT) > WORKSPACE_CAP_BYTES:
                raise RuntimeError("batch workspace cap exceeded")

            print("=" * 78)
            print(f"Q009B full-day L2 acquisition/replay: {date}")
            print(f"Expected bytes: {size:,}")
            print("No alpha/P&L. Progress may pause during semantic replay.")
            print("=" * 78)

            day_dir = BATCH_ROOT / date
            day_dir.mkdir(parents=True, exist_ok=True)

            lib["PILOT_DATE"] = date
            lib["EXPECTED_FILENAME"] = filename
            lib["EXPECTED_BYTES"] = size
            lib["STAGE"] = STAGE + "-" + date
            lib["WORKSPACE"] = day_dir
            lib["ARCHIVE"] = day_dir / filename
            lib["REPORT"] = day_dir / "report.json"
            lib["SUMMARY"] = day_dir / "summary.md"
            lib["SAFETY"] = day_dir / "final_safety.json"
            lib["WORKSPACE_CAP_BYTES"] = PER_FILE_CAP_BYTES + 25_000_000

            lib["main"]()
            day_report = json.loads(
                lib["REPORT"].read_text(encoding="utf-8")
            )
            row = {
                "date": date,
                "status": day_report.get("overall_status"),
                "archive": day_report.get("archive"),
                "live_head": day_report.get("live_head"),
                "replay": day_report.get("replay"),
                "report_path": str(lib["REPORT"]),
            }
            report["days"].append(row)
            report["network_market_data_bytes_read"] = lib["network_bytes_read"]
            write_batch_outputs(report)

            if row["status"] != "FULL_DAY_PASS":
                report["overall_status"] = "REVIEW"
                write_batch_outputs(report)
                print("STOP: non-FULL_DAY_PASS day", date)
                return

        report["network_market_data_bytes_read"] = lib["network_bytes_read"]
        if report["network_market_data_bytes_read"] > SESSION_DOWNLOAD_CAP_BYTES:
            raise RuntimeError("batch network cap exceeded")

        report["overall_status"] = (
            "PASS"
            if len(report["days"]) == 2
            and all(x.get("status") == "FULL_DAY_PASS" for x in report["days"])
            else "REVIEW"
        )
        write_batch_outputs(report)
        print("COMPLETE:", report["overall_status"])
        print("Results:", BATCH_ROOT)

    except Exception as exc:
        report["overall_status"] = "ERROR"
        report["error"] = repr(exc)
        report["network_market_data_bytes_read"] = lib.get(
            "network_bytes_read", 0
        )
        write_batch_outputs(report)
        raise


if __name__ == "__main__":
    main()
