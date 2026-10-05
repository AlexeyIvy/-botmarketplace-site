from __future__ import annotations

import errno
import json
import os
import re
import stat
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

SCHEMA = "sc001.b13c_operational_health.v0.1"
ADAPTER_VERSION = "0.1"
COLLECTOR_ID = "SC001_B13C_PROSPECTIVE_LIQUIDATIONS"
EXPECTED_STAGE = "SC001-B13C-BYBIT-PROSPECTIVE-LIQUIDATION-COLLECTOR-V0.3"
EXPECTED_VERSION = "0.3"
FIXED_STATE_PATH = Path(
    "/home/botmarket/sc001_data/"
    "SC001_B13C_PROSPECTIVE_LIQUIDATIONS/collector_state.json"
)
FIXED_SYSTEMD_UNIT = "sc001-b13c-liquidation.service"
FIXED_SYSTEMD_COMMAND = (
    "systemctl",
    "show",
    FIXED_SYSTEMD_UNIT,
    "--property=ActiveState",
    "--property=SubState",
    "--no-pager",
)
MAX_STATE_BYTES = 65_536
HEARTBEAT_STALE_AFTER_MS = 90_000
MAX_COUNTER = 2**63 - 1

_ALLOWED_COLLECTOR_STATUS = {
    "INITIALIZED",
    "B13C_COLLECTION_RUNNING",
    "B13C_COLLECTION_SOURCE_REVIEW",
    "B13C_COLLECTION_IMPLEMENTATION_FAIL",
    "B13C_COLLECTION_STOPPED",
}
_ALLOWED_CONNECTION_STATUS = {"CONNECTED", "DISCONNECTED", "STOPPED"}
_PROCESS_TOKEN = re.compile(r"[a-z][a-z0-9-]{0,31}\Z")

_STATE_VALUE_KEYS = (
    "collector_status",
    "connection_state",
    "heartbeat",
    "qualified_symbol_count",
    "reconnect_diagnostics",
    "process_gap_diagnostics",
)


class AdapterError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _unavailable_state(code: str) -> dict[str, Any]:
    return {
        "availability": "UNAVAILABLE",
        "error": code,
        "collector_status": None,
        "connection_state": None,
        "heartbeat": {"state": "UNAVAILABLE", "age_ms": None},
        "qualified_symbol_count": None,
        "reconnect_diagnostics": {
            "reconnect_count": None,
            "cumulative_gap_ms": None,
        },
        "process_gap_diagnostics": {
            "process_restart_count": None,
            "cumulative_process_gap_ms": None,
        },
    }


def _map_open_error(exc: OSError) -> AdapterError:
    if exc.errno == errno.ENOENT:
        return AdapterError("STATE_MISSING")
    if exc.errno in {errno.EACCES, errno.EPERM}:
        return AdapterError("STATE_PERMISSION_DENIED")
    if exc.errno == errno.ELOOP:
        return AdapterError("STATE_SYMLINK_REJECTED")
    if exc.errno == errno.ENOTDIR:
        return AdapterError("STATE_NONREGULAR")
    return AdapterError("STATE_IO_ERROR")


def _read_regular_bytes(path: Path) -> bytes:
    """Read one opened regular-file inode without following any path symlink."""
    if not path.is_absolute():
        raise AdapterError("STATE_PATH_INVALID")

    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC
    file_flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NONBLOCK
    if hasattr(os, "O_NOFOLLOW"):
        directory_flags |= os.O_NOFOLLOW
        file_flags |= os.O_NOFOLLOW

    parts = path.parts
    directory_fd: int | None = None
    file_fd: int | None = None
    try:
        directory_fd = os.open("/", directory_flags)
        for component in parts[1:-1]:
            try:
                next_fd = os.open(component, directory_flags, dir_fd=directory_fd)
            except OSError as exc:
                raise _map_open_error(exc) from None
            os.close(directory_fd)
            directory_fd = next_fd

        try:
            file_fd = os.open(parts[-1], file_flags, dir_fd=directory_fd)
        except OSError as exc:
            raise _map_open_error(exc) from None

        try:
            metadata = os.fstat(file_fd)
        except OSError:
            raise AdapterError("STATE_IO_ERROR") from None
        if not stat.S_ISREG(metadata.st_mode):
            raise AdapterError("STATE_NONREGULAR")
        if metadata.st_size > MAX_STATE_BYTES:
            raise AdapterError("STATE_TOO_LARGE")

        chunks: list[bytes] = []
        remaining = MAX_STATE_BYTES + 1
        while remaining:
            try:
                chunk = os.read(file_fd, min(remaining, 16_384))
            except OSError:
                raise AdapterError("STATE_IO_ERROR") from None
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        if len(payload) > MAX_STATE_BYTES:
            raise AdapterError("STATE_TOO_LARGE")
        return payload
    finally:
        if file_fd is not None:
            os.close(file_fd)
        if directory_fd is not None:
            os.close(directory_fd)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AdapterError("STATE_DUPLICATE_KEY")
        result[key] = value
    return result


def _decode_state(payload: bytes) -> dict[str, Any]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        raise AdapterError("STATE_INVALID_UTF8") from None
    try:
        obj = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except AdapterError:
        raise
    except (json.JSONDecodeError, RecursionError):
        raise AdapterError("STATE_INVALID_JSON") from None
    if type(obj) is not dict:
        raise AdapterError("STATE_INVALID_JSON")
    if obj.get("stage") != EXPECTED_STAGE or obj.get("version") != EXPECTED_VERSION:
        raise AdapterError("STATE_WRONG_IDENTITY")
    return obj


def _optional_enum(
    state: dict[str, Any], key: str, allowed: set[str]
) -> tuple[str | None, bool]:
    if key not in state:
        return None, True
    value = state[key]
    if type(value) is not str or value not in allowed:
        raise AdapterError("STATE_TYPE_ERROR")
    return value, False


def _optional_int(
    state: dict[str, Any], key: str, maximum: int = MAX_COUNTER
) -> tuple[int | None, bool]:
    if key not in state:
        return None, True
    value = state[key]
    if type(value) is not int or value < 0 or value > maximum:
        raise AdapterError("STATE_TYPE_ERROR")
    return value, False


def _project_state(state: dict[str, Any], observed_at_ms: int) -> dict[str, Any]:
    if type(observed_at_ms) is not int or observed_at_ms <= 0:
        raise AdapterError("OBSERVATION_TIME_INVALID")

    collector_status, missing_status = _optional_enum(
        state, "status", _ALLOWED_COLLECTOR_STATUS
    )
    connection_state, missing_connection = _optional_enum(
        state, "connection_status", _ALLOWED_CONNECTION_STATUS
    )
    qualified, missing_qualified = _optional_int(
        state, "source_qualified_symbols", 12
    )
    reconnect_count, missing_reconnect = _optional_int(state, "reconnect_count")
    cumulative_gap_ms, missing_connection_gap = _optional_int(
        state, "cumulative_gap_ms"
    )
    process_restart_count, missing_process_restart = _optional_int(
        state, "process_restart_count"
    )
    cumulative_process_gap_ms, missing_process_gap = _optional_int(
        state, "cumulative_process_gap_ms"
    )
    heartbeat_ms, missing_heartbeat = _optional_int(
        state, "last_heartbeat_ms", 10**16
    )

    missing_any = any(
        (
            missing_status,
            missing_connection,
            missing_qualified,
            missing_reconnect,
            missing_connection_gap,
            missing_process_restart,
            missing_process_gap,
            missing_heartbeat,
        )
    )
    anomaly = False
    if heartbeat_ms is None:
        heartbeat = {"state": "UNAVAILABLE", "age_ms": None}
    elif heartbeat_ms > observed_at_ms:
        heartbeat = {"state": "FUTURE", "age_ms": None}
        anomaly = True
    else:
        age_ms = observed_at_ms - heartbeat_ms
        heartbeat = {
            "state": (
                "STALE"
                if age_ms > HEARTBEAT_STALE_AFTER_MS
                else "CURRENT"
            ),
            "age_ms": age_ms,
        }

    if anomaly:
        availability = "PARTIAL"
        error = "STATE_HEARTBEAT_FUTURE"
    elif missing_any:
        availability = "PARTIAL"
        error = "STATE_FIELDS_UNAVAILABLE"
    else:
        availability = "AVAILABLE"
        error = "NONE"

    return {
        "availability": availability,
        "error": error,
        "collector_status": collector_status,
        "connection_state": connection_state,
        "heartbeat": heartbeat,
        "qualified_symbol_count": qualified,
        "reconnect_diagnostics": {
            "reconnect_count": reconnect_count,
            "cumulative_gap_ms": cumulative_gap_ms,
        },
        "process_gap_diagnostics": {
            "process_restart_count": process_restart_count,
            "cumulative_process_gap_ms": cumulative_process_gap_ms,
        },
    }


def _state_health(payload: bytes, observed_at_ms: int) -> dict[str, Any]:
    try:
        return _project_state(_decode_state(payload), observed_at_ms)
    except AdapterError as exc:
        return _unavailable_state(exc.code)


def _read_fixed_state_health(observed_at_ms: int) -> dict[str, Any]:
    try:
        payload = _read_regular_bytes(FIXED_STATE_PATH)
    except AdapterError as exc:
        return _unavailable_state(exc.code)
    return _state_health(payload, observed_at_ms)


def _unavailable_process(code: str) -> dict[str, Any]:
    return {
        "availability": "UNAVAILABLE",
        "error": code,
        "active_state": None,
        "sub_state": None,
        "running": None,
    }


def _query_fixed_process_state(
    run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    try:
        completed = run(
            FIXED_SYSTEMD_COMMAND,
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=2.0,
            text=True,
            encoding="utf-8",
            errors="strict",
            shell=False,
        )
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return _unavailable_process("PROCESS_QUERY_FAILED")
    if type(completed.returncode) is not int or completed.returncode != 0:
        return _unavailable_process("PROCESS_QUERY_FAILED")
    if type(completed.stdout) is not str or len(completed.stdout) > 256:
        return _unavailable_process("PROCESS_RESPONSE_INVALID")

    parsed: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        if not line:
            continue
        if "=" not in line:
            return _unavailable_process("PROCESS_RESPONSE_INVALID")
        key, value = line.split("=", 1)
        if key not in {"ActiveState", "SubState"} or key in parsed:
            return _unavailable_process("PROCESS_RESPONSE_INVALID")
        if _PROCESS_TOKEN.fullmatch(value) is None:
            return _unavailable_process("PROCESS_RESPONSE_INVALID")
        parsed[key] = value
    if set(parsed) != {"ActiveState", "SubState"}:
        return _unavailable_process("PROCESS_RESPONSE_INVALID")

    active = parsed["ActiveState"]
    sub = parsed["SubState"]
    return {
        "availability": "AVAILABLE",
        "error": "NONE",
        "active_state": active,
        "sub_state": sub,
        "running": active == "active" and sub == "running",
    }


def get_health() -> dict[str, Any]:
    """Return fixed-purpose B13-C operational health; accepts no caller input."""
    observed_at_ms = time.time_ns() // 1_000_000
    return {
        "schema": SCHEMA,
        "adapter_version": ADAPTER_VERSION,
        "collector_id": COLLECTOR_ID,
        "observed_at_ms": observed_at_ms,
        "state": _read_fixed_state_health(observed_at_ms),
        "process": _query_fixed_process_state(),
        "evidence_eligibility": "NOT_EVALUATED",
    }


__all__ = ["get_health"]
