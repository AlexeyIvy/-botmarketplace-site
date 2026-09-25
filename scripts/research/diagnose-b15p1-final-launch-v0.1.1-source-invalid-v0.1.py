#!/usr/bin/env python3
from __future__ import annotations

import collections
import hashlib
import json
import os
import pwd
import grp
import subprocess
from pathlib import Path
from typing import Any

OUT_DIR = Path("/home/botmarket/sc001_data/SC001_B15P1_TRANSFERABILITY")
STATE = OUT_DIR / "collector_state.json"
MANIFEST = OUT_DIR / "collector_manifest.json"
SNAPSHOT = OUT_DIR / "source_capability_snapshot.json"
AUTH = OUT_DIR / "collector_launch_authorization.json"
POLLS = OUT_DIR / "polls"
GAPS = OUT_DIR / "gaps"
INVALID = OUT_DIR / "invalid"
FEES = OUT_DIR / "fees"
RAW = OUT_DIR / "raw_objects"
SYSTEMD_LOG = OUT_DIR / "systemd.log"
DIAG_DIR = OUT_DIR / "diagnostics"
REPORT = DIAG_DIR / "final_launch_v011_source_invalid_diagnostic.json"
SERVICE = "sc001-b15p1-transferability.service"
RUNTIME_UNIT = Path("/etc/systemd/system") / SERVICE

MAX_TOP_ERRORS = 12
MAX_RAW_SUMMARIES = 12


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"JSON object expected: {path}")
    return obj


def iter_jsonl(path: Path):
    if not path.is_file() or path.is_symlink():
        return
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception as exc:
                yield {
                    "_decode_error": f"{type(exc).__name__}: {exc}",
                    "_file": str(path),
                    "_line": line_no,
                }
                continue
            if isinstance(obj, dict):
                yield obj
            else:
                yield {
                    "_decode_error": "JSONL row is not object",
                    "_file": str(path),
                    "_line": line_no,
                }


def rows_under(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not root.exists():
        return rows
    for p in sorted(root.rglob("*.jsonl")):
        rows.extend(iter_jsonl(p) or [])
    return rows


def systemctl_value(args: list[str]) -> str:
    p = subprocess.run(
        ["systemctl", *args],
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )
    return (p.stdout or p.stderr or "").strip()


def classify(status: str, error: str | None) -> str:
    s = str(status or "")
    e = str(error or "")
    if s == "OK":
        return "OK"
    if s == "REQUEST_DEADLINE_EXCEEDED":
        return "REQUEST_DEADLINE"
    if s == "SCHEDULER_OVERRUN":
        return "SCHEDULER_OVERRUN"
    if e.startswith("HTTP_"):
        return "HTTP_STATUS"
    if "retCode=" in e:
        return "BYBIT_API_CODE"
    if "OKX code=" in e or e.startswith("code="):
        return "OKX_API_CODE"
    if "schema drift" in e or "rows missing" in e or "identity field empty" in e:
        return "SCHEMA_PARSE"
    if "JSONDecodeError" in e or "JSON object expected" in e:
        return "JSON_PARSE"
    if any(x in e for x in ("TimeoutError", "timed out", "URLError", "Connection", "SSL")):
        return "TRANSPORT"
    if s == "SOURCE_INVALID":
        return "SOURCE_INVALID_OTHER"
    return s or "UNKNOWN"


def safe_raw_summary(venue: str, raw_sha: str) -> dict[str, Any]:
    out: dict[str, Any] = {"venue": venue, "sha256": raw_sha}
    path = RAW / venue.lower() / raw_sha[:2] / f"{raw_sha}.bin"
    out["path"] = str(path)
    out["exists"] = path.is_file() and not path.is_symlink()
    if not out["exists"]:
        return out
    out["size_bytes"] = path.stat().st_size
    actual = sha256_file(path)
    out["sha256_matches"] = actual == raw_sha
    try:
        obj = json.loads(path.read_bytes().decode("utf-8"))
        if not isinstance(obj, dict):
            out["json_type"] = type(obj).__name__
            return out
        out["top_level_keys"] = sorted(str(k) for k in obj.keys())[:40]
        if venue == "BYBIT":
            result = obj.get("result") or {}
            rows = result.get("rows") if isinstance(result, dict) else None
            out.update(
                {
                    "retCode": obj.get("retCode"),
                    "retMsg": obj.get("retMsg"),
                    "result_keys": sorted(str(k) for k in result.keys())[:40]
                    if isinstance(result, dict)
                    else [],
                    "row_count": len(rows) if isinstance(rows, list) else None,
                    "first_row_keys": sorted(str(k) for k in rows[0].keys())[:80]
                    if isinstance(rows, list) and rows and isinstance(rows[0], dict)
                    else [],
                }
            )
        elif venue == "OKX":
            data = obj.get("data")
            out.update(
                {
                    "code": obj.get("code"),
                    "msg": obj.get("msg"),
                    "row_count": len(data) if isinstance(data, list) else None,
                    "first_row_keys": sorted(str(k) for k in data[0].keys())[:80]
                    if isinstance(data, list) and data and isinstance(data[0], dict)
                    else [],
                }
            )
    except Exception as exc:
        out["json_decode_error"] = f"{type(exc).__name__}: {exc}"
    return out


def summarize_venue(polls: list[dict[str, Any]], venue: str) -> dict[str, Any]:
    statuses = collections.Counter()
    errors = collections.Counter()
    classes = collections.Counter()
    http_statuses = collections.Counter()
    raw_shas = collections.Counter()
    elapsed: list[int] = []
    headers_seen: collections.Counter[str] = collections.Counter()
    first_problem = None
    last_problem = None

    for row in polls:
        v = (row.get("venues") or {}).get(venue) or {}
        status = str(v.get("status") or "MISSING")
        error = v.get("error")
        statuses[status] += 1
        classes[classify(status, error)] += 1
        if error:
            errors[str(error)] += 1
        if v.get("http_status") is not None:
            http_statuses[str(v.get("http_status"))] += 1
        if v.get("elapsed_ms") is not None:
            try:
                elapsed.append(int(v.get("elapsed_ms")))
            except Exception:
                pass
        raw_sha = str(v.get("raw_body_sha256") or "")
        if len(raw_sha) == 64:
            raw_shas[raw_sha] += 1

        safe_headers = v.get("safe_headers") or {}
        if isinstance(safe_headers, dict):
            for k, val in safe_headers.items():
                headers_seen[f"{k}={val}"] += 1

        if status != "OK":
            p = {
                "scheduled_slot_ms": row.get("scheduled_slot_ms"),
                "status": status,
                "http_status": v.get("http_status"),
                "elapsed_ms": v.get("elapsed_ms"),
                "error": error,
                "raw_body_sha256": v.get("raw_body_sha256"),
                "raw_body_size_bytes": v.get("raw_body_size_bytes"),
            }
            if first_problem is None:
                first_problem = p
            last_problem = p

    raw_summaries = [
        safe_raw_summary(venue, sha)
        for sha, _ in raw_shas.most_common(MAX_RAW_SUMMARIES)
    ]

    return {
        "status_counts": dict(statuses),
        "error_class_counts": dict(classes),
        "top_errors": [
            {"error": e, "count": n}
            for e, n in errors.most_common(MAX_TOP_ERRORS)
        ],
        "http_status_counts": dict(http_statuses),
        "elapsed_ms": {
            "count": len(elapsed),
            "min": min(elapsed) if elapsed else None,
            "max": max(elapsed) if elapsed else None,
            "avg": round(sum(elapsed) / len(elapsed), 2) if elapsed else None,
        },
        "unique_raw_body_count": len(raw_shas),
        "raw_body_occurrences": [
            {"sha256": sha, "count": n}
            for sha, n in raw_shas.most_common(MAX_RAW_SUMMARIES)
        ],
        "raw_summaries": raw_summaries,
        "safe_header_examples": [
            {"header": h, "count": n}
            for h, n in headers_seen.most_common(20)
        ],
        "first_problem": first_problem,
        "last_problem": last_problem,
    }


def main() -> int:
    if not STATE.is_file():
        raise SystemExit("collector_state.json missing; do not retry launch before review")
    if not MANIFEST.is_file():
        raise SystemExit("collector_manifest.json missing; do not retry launch before review")

    state = load_json(STATE)
    manifest = load_json(MANIFEST)
    polls = rows_under(POLLS)
    gaps = rows_under(GAPS)
    invalid = rows_under(INVALID)
    fees = rows_under(FEES)

    poll_decode_errors = [r for r in polls if r.get("_decode_error")]
    poll_rows = [r for r in polls if not r.get("_decode_error")]
    valid_poll_count = sum(
        1
        for row in poll_rows
        if all(
            (((row.get("venues") or {}).get(v) or {}).get("status") == "OK")
            for v in ("BYBIT", "OKX")
        )
    )

    venue = {
        "BYBIT": summarize_venue(poll_rows, "BYBIT"),
        "OKX": summarize_venue(poll_rows, "OKX"),
    }

    state_poll_count = int(state.get("poll_count") or 0)
    state_invalid_count = int(state.get("invalid_poll_count") or 0)

    gap_errors = collections.Counter(
        f"{r.get('venue')}|{r.get('event')}|{r.get('error')}"
        for r in gaps
        if not r.get("_decode_error")
    )
    invalid_errors = collections.Counter(
        f"{r.get('event')}|{r.get('venue')}|{r.get('error')}"
        for r in invalid
        if not r.get("_decode_error")
    )

    fee_summary = collections.Counter()
    for r in fees:
        if r.get("_decode_error"):
            continue
        fee_summary[f"{r.get('venue')}|ok={r.get('ok')}|error={r.get('error')}"] += 1

    primary = []
    for v in ("BYBIT", "OKX"):
        classes = venue[v]["error_class_counts"]
        non_ok = [(k, n) for k, n in classes.items() if k != "OK"]
        non_ok.sort(key=lambda x: (-x[1], x[0]))
        if non_ok:
            primary.append(
                {"venue": v, "class": non_ok[0][0], "count": non_ok[0][1]}
            )

    service = {
        "active": systemctl_value(["is-active", SERVICE]),
        "enabled": systemctl_value(["is-enabled", SERVICE]),
        "substate": systemctl_value(["show", SERVICE, "-p", "SubState", "--value"]),
        "main_pid": systemctl_value(["show", SERVICE, "-p", "MainPID", "--value"]),
        "nrestarts": systemctl_value(["show", SERVICE, "-p", "NRestarts", "--value"]),
        "fragment_path": systemctl_value(["show", SERVICE, "-p", "FragmentPath", "--value"]),
        "dropins": systemctl_value(["show", SERVICE, "-p", "DropInPaths", "--value"]),
    }

    report = {
        "schema": "sc001.b15.p1_final_launch_v011_source_invalid_diagnostic.v0.1",
        "status": "B15P1_FINAL_LAUNCH_V011_SOURCE_INVALID_DIAGNOSTIC_COMPLETE",
        "credentials_read": False,
        "exchange_calls_performed": False,
        "price_data_used": False,
        "pnl_data_used": False,
        "service": service,
        "runtime_unit": {
            "present": RUNTIME_UNIT.is_file() and not RUNTIME_UNIT.is_symlink(),
            "sha256": sha256_file(RUNTIME_UNIT)
            if RUNTIME_UNIT.is_file() and not RUNTIME_UNIT.is_symlink()
            else None,
        },
        "runtime_authorization": {
            "present": AUTH.is_file() and not AUTH.is_symlink(),
            "sha256": sha256_file(AUTH)
            if AUTH.is_file() and not AUTH.is_symlink()
            else None,
        },
        "snapshot": {
            "present": SNAPSHOT.is_file() and not SNAPSHOT.is_symlink(),
            "sha256": sha256_file(SNAPSHOT)
            if SNAPSHOT.is_file() and not SNAPSHOT.is_symlink()
            else None,
        },
        "state": {
            "status": state.get("status"),
            "process_epoch": state.get("process_epoch"),
            "process_restart_count": state.get("process_restart_count"),
            "poll_count": state_poll_count,
            "invalid_poll_count": state_invalid_count,
            "valid_poll_count_derived": valid_poll_count,
            "missed_poll_slots": state.get("missed_poll_slots"),
            "source_gap_count": state.get("source_gap_count"),
            "open_source_gaps": state.get("open_source_gaps"),
            "last_heartbeat_ms": state.get("last_heartbeat_ms"),
            "last_scheduled_slot_ms": state.get("last_scheduled_slot_ms"),
            "last_poll_chain_hash": state.get("last_poll_chain_hash"),
            "price_data_collected": state.get("price_data_collected"),
            "pnl_calculated": state.get("pnl_calculated"),
        },
        "manifest": {
            "runner_sha256": manifest.get("runner_sha256"),
            "library_sha256": manifest.get("library_sha256"),
            "implementation_freeze_sha256": manifest.get("implementation_freeze_sha256"),
            "capability_snapshot_sha256": manifest.get("capability_snapshot_sha256"),
            "fast_cadence_seconds": manifest.get("fast_cadence_seconds"),
            "request_deadline_seconds": manifest.get("request_deadline_seconds"),
            "price_data_authorized": manifest.get("price_data_authorized"),
            "pnl_authorized": manifest.get("pnl_authorized"),
        },
        "poll_files": {
            "jsonl_row_count": len(poll_rows),
            "decode_error_count": len(poll_decode_errors),
            "valid_poll_count": valid_poll_count,
            "state_poll_count_matches": len(poll_rows) == state_poll_count,
        },
        "venues": venue,
        "source_gap_top": [
            {"key": k, "count": n}
            for k, n in gap_errors.most_common(20)
        ],
        "invalid_top": [
            {"key": k, "count": n}
            for k, n in invalid_errors.most_common(20)
        ],
        "fee_top": [
            {"key": k, "count": n}
            for k, n in fee_summary.most_common(20)
        ],
        "primary_failure_classes": primary,
        "systemd_log": {
            "present": SYSTEMD_LOG.is_file() and not SYSTEMD_LOG.is_symlink(),
            "sha256": sha256_file(SYSTEMD_LOG)
            if SYSTEMD_LOG.is_file() and not SYSTEMD_LOG.is_symlink()
            else None,
            "size_bytes": SYSTEMD_LOG.stat().st_size
            if SYSTEMD_LOG.is_file() and not SYSTEMD_LOG.is_symlink()
            else None,
        },
        "next_state": "STOP_AND_CLASSIFY_SOURCE_INVALID_BEFORE_ANY_COLLECTOR_RETRY",
    }

    DIAG_DIR.mkdir(parents=True, exist_ok=True)
    uid = pwd.getpwnam("botmarket").pw_uid
    gid = grp.getgrnam("botmarket").gr_gid
    os.chown(DIAG_DIR, uid, gid)
    os.chmod(DIAG_DIR, 0o750)

    tmp = REPORT.with_name(REPORT.name + ".tmp")
    tmp.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.chmod(tmp, 0o640)
    os.chown(tmp, uid, gid)
    os.replace(tmp, REPORT)

    print("B15P1_FINAL_LAUNCH_V011_SOURCE_INVALID_DIAGNOSTIC_COMPLETE")
    print("report =", REPORT)
    print("poll_count =", state_poll_count)
    print("invalid_poll_count =", state_invalid_count)
    print("valid_poll_count =", valid_poll_count)
    for v in ("BYBIT", "OKX"):
        print(v, "status_counts =", json.dumps(venue[v]["status_counts"], sort_keys=True))
        print(v, "error_class_counts =", json.dumps(venue[v]["error_class_counts"], sort_keys=True))
        print(v, "top_errors =", json.dumps(venue[v]["top_errors"][:5], ensure_ascii=False))
        print(v, "http_status_counts =", json.dumps(venue[v]["http_status_counts"], sort_keys=True))
        print(v, "elapsed_ms =", json.dumps(venue[v]["elapsed_ms"], sort_keys=True))
    print("primary_failure_classes =", json.dumps(primary, sort_keys=True))
    print("credentials_read = False")
    print("exchange_calls_performed = False")
    print("price/PnL = CLOSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
