#!/usr/bin/env python3
"""Offline, fail-closed technical admission for SC001 Test Executor tasks.

No network, execution, repository writes, governance decisions or evidence access.
A PASS is NOT a research authorization; the live executor and binding rules must
be checked again immediately before any actual job submission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any

WORKERS = {
    "H1_HISTORICAL_INDICATORS",
    "X1_CROSS_ASSET_STRUCTURE",
    "P1_PROSPECTIVE_EVENT",
}
ENTRY_ROOTS = ("scripts/research/", "tests/research/")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def continuation_key(repository: str, terminal_comment_id: int, stage: str,
                     frozen_scope_sha256: str) -> str:
    """Stable key for the SAME terminal/stage/scope; not an execution lease."""
    if not repository or isinstance(terminal_comment_id, bool) or terminal_comment_id <= 0:
        raise ValueError("INVALID_TERMINAL_IDENTITY")
    if not re.fullmatch(r"[A-Z0-9_-]{2,80}", stage):
        raise ValueError("INVALID_STAGE")
    if not SHA256_RE.fullmatch(frozen_scope_sha256):
        raise ValueError("INVALID_SCOPE_SHA256")
    material = json.dumps(
        [repository, terminal_comment_id, stage, frozen_scope_sha256],
        ensure_ascii=True, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _int(value: Any) -> bool:
    return type(value) is int and value >= 0


def _relative(value: Any) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return (not path.is_absolute() and not any(part in ("", ".", "..") for part in
            value.split("/")) and path.as_posix() == value)


def _sha_bindings(task: dict[str, Any]) -> list[tuple[str, str]]:
    bindings: list[tuple[str, str]] = []
    for section in ("frozen_inputs", "implementation", "offline_test", "canonical_freeze"):
        obj = task.get(section)
        if not isinstance(obj, dict):
            continue
        if section == "frozen_inputs":
            pairs = (("implementation_path", "implementation_sha256"),
                     ("test_path", "test_sha256"))
        else:
            pairs = (("path", "sha256"),)
        for p_key, h_key in pairs:
            if p_key in obj or h_key in obj:
                bindings.append((obj.get(p_key), obj.get(h_key)))
    return bindings


def preflight(task: dict[str, Any], executor: dict[str, Any], main_head: str,
              repo_root: Path, authorization: dict[str, Any] | None = None) -> dict[str, Any]:
    errors: list[str] = []
    deferred: list[str] = []

    def need(ok: bool, reason: str) -> None:
        if not ok and reason not in errors:
            errors.append(reason)

    execution = task.get("exact_execution")
    if not isinstance(execution, dict):
        execution = {}
        errors.append("MISSING_EXACT_EXECUTION")
    worker = task.get("worker_id")
    need(worker in WORKERS, "UNKNOWN_WORKER")
    task_id = task.get("task_id")
    need(isinstance(task_id, str) and task_id.startswith("SC001-"), "INVALID_TASK_ID")
    tier = task.get("authorization_class", "")
    need(isinstance(tier, str) and (tier.startswith("T0") or tier in ("T1", "T2")),
         "AUTHORIZATION_CLASS_NOT_DELEGATED")
    entry = execution.get("entrypoint")
    need(_relative(entry) and any(entry.startswith(prefix) for prefix in ENTRY_ROOTS)
         and entry.endswith((".py", ".sh")), "INVALID_EXECUTOR_ENTRYPOINT")
    args = execution.get("args")
    need(isinstance(args, list) and all(isinstance(a, str) for a in args),
         "INVALID_EXECUTOR_ARGS")
    profile = execution.get("network_profile")
    profiles = executor.get("network_profiles")
    need(isinstance(profiles, list) and profile in profiles, "UNSUPPORTED_NETWORK_PROFILE")

    limits = executor.get("limits")
    limits = limits if isinstance(limits, dict) else {}
    timeout = execution.get("timeout_seconds")
    maximum = limits.get("max_timeout_seconds")
    need(_int(timeout) and timeout > 0, "INVALID_TIMEOUT")
    need(_int(maximum) and maximum > 0, "MISSING_LIVE_TIMEOUT_CAP")
    if _int(timeout) and _int(maximum):
        need(timeout <= maximum, "TIMEOUT_EXCEEDS_LIVE_CAP")

    count = execution.get("max_executions", execution.get("max_execution_attempts", 1))
    need(_int(count) and count == 1, "EXECUTION_COUNT_NOT_ONE")
    network_runs = execution.get("max_network_runs", task.get("max_network_runs", 0))
    need(_int(network_runs) and network_runs <= 1, "INVALID_NETWORK_RUN_BUDGET")
    if profile == "offline":
        need(network_runs == 0, "OFFLINE_JOB_HAS_NETWORK_BUDGET")
    if tier == "T1":
        need(profile == "public_research" and network_runs == 1,
             "T1_NETWORK_PROFILE_OR_BUDGET_MISMATCH")

    need(isinstance(main_head, str) and bool(GIT_SHA_RE.fullmatch(main_head)),
         "INVALID_CANONICAL_MAIN_HEAD")
    need(executor.get("head") == main_head, "EXECUTOR_HEAD_NOT_CANONICAL_MAIN")
    need(execution.get("repo_head_sha") == main_head, "TASK_HEAD_NOT_CANONICAL_MAIN")

    root = repo_root.resolve()
    if _relative(entry):
        resolved = (root / entry).resolve()
        need(resolved.is_relative_to(root) and resolved.is_file(), "ENTRYPOINT_NOT_IN_REPOSITORY")
    for rel, expected in _sha_bindings(task):
        if not _relative(rel) or not isinstance(expected, str) or not SHA256_RE.fullmatch(expected):
            need(False, "INVALID_FROZEN_FILE_BINDING")
            continue
        target = (root / rel).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            need(False, "FROZEN_FILE_MISSING_OR_UNSAFE")
        elif hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            need(False, "FROZEN_FILE_HASH_MISMATCH")

    if tier == "T1":
        need(authorization is not None, "MISSING_T1_AUTHORIZATION")
    if authorization is not None:
        need(authorization.get("task_id") == task_id
             and authorization.get("worker_id") == worker, "AUTHORIZATION_TASK_MISMATCH")
        need(authorization.get("status") == "AUTHORIZED_ONE_SHOT",
             "AUTHORIZATION_NOT_ACTIVE")
        need(authorization.get("canonical_main_head") == main_head,
             "AUTHORIZATION_MAIN_HEAD_MISMATCH")
        need(authorization.get("exact_entrypoint") == entry
             and authorization.get("exact_args") == args, "AUTHORIZATION_EXECUTION_MISMATCH")
        auth_budget = authorization.get("budgets")
        auth_budget = auth_budget if isinstance(auth_budget, dict) else {}
        need(auth_budget.get("max_wall_time_seconds") == timeout,
             "AUTHORIZATION_TIMEOUT_MISMATCH")
        task_network = task.get("frozen_request_contract")
        if isinstance(task_network, dict):
            need(auth_budget.get("max_requests_total") == task_network.get("max_requests_total"),
                 "AUTHORIZATION_REQUEST_CAP_MISMATCH")
            need(auth_budget.get("max_total_network_bytes") ==
                 task_network.get("max_response_bytes_total"),
                 "AUTHORIZATION_BYTE_CAP_MISMATCH")

    counts = executor.get("current_counts")
    counts = counts if isinstance(counts, dict) else {}
    for used_field, cap_field in (("running", "max_concurrent_jobs"),
                                  ("rolling_hour", "max_runs_per_rolling_hour"),
                                  ("utc_day", "max_runs_per_utc_day")):
        used, cap = counts.get(used_field), limits.get(cap_field)
        need(_int(used) and _int(cap) and cap > 0, "MISSING_LIVE_CAPACITY_FIELDS")
        if _int(used) and _int(cap) and cap > 0 and used >= cap:
            deferred.append("EXECUTOR_" + used_field.upper() + "_CAP_REACHED")

    if errors:
        status = "ADMISSION_BLOCKED"
    elif deferred:
        status = "ADMISSION_RESOURCE_DEFER"
    else:
        status = "ADMISSION_PRECHECK_PASS"
    return {
        "status": status, "task_id": task_id, "canonical_main_head": main_head,
        "errors": errors, "resource_defer_reasons": deferred,
        "execution_authorized_by_this_check": False,
        "live_recheck_required_immediately_before_job": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, type=Path)
    parser.add_argument("--executor-info", required=True, type=Path)
    parser.add_argument("--main-head", required=True)
    parser.add_argument("--repo-root", default=".", type=Path)
    parser.add_argument("--authorization", type=Path)
    args = parser.parse_args()
    try:
        task = json.loads(args.task.read_text(encoding="utf-8"))
        executor = json.loads(args.executor_info.read_text(encoding="utf-8"))
        auth = (json.loads(args.authorization.read_text(encoding="utf-8"))
                if args.authorization else None)
        if not isinstance(task, dict) or not isinstance(executor, dict):
            raise ValueError("INVALID_TOP_LEVEL_DOCUMENT")
        result = preflight(task, executor, args.main_head, args.repo_root, auth)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        result = {"status": "ADMISSION_BLOCKED", "errors": ["INPUT_UNREADABLE_OR_INVALID"],
                  "execution_authorized_by_this_check": False}
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return {"ADMISSION_PRECHECK_PASS": 0, "ADMISSION_RESOURCE_DEFER": 3}.get(result["status"], 2)


if __name__ == "__main__":
    sys.exit(main())
