#!/usr/bin/env python3
from __future__ import annotations
import argparse
import grp
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

TASK_ID = "SC001-H1-004J"
INSTALLER_SHA256 = "0e9afe9b9a3e12beb7aa451a7608eda3ffa30a46ba9b07faf0a869bfda518968"
RESOURCE_ID = "b97ffeefed4dd1b4caa771df734b59b5a6dc2b6a9ada3b3c9b8ce0c6de6319bf"
ACQUISITION_SHA256 = "1eb597e3186023540a5ab9929f433f7f5a81b9d587f10386cf2e3e55f625c760"
SHARED_ROOT = Path("/var/lib/botmarket-test-executor/shared-data/sc001")
POLICY = Path("/etc/botmarket-test-executor/policy.json")
RUNNER = Path("/opt/botmarket-test-executor/job_runner.py")
LAUNCHER = Path("/usr/local/sbin/botmarket-test-launch")
SERVER = Path("/opt/botmarket-test-executor/server.py")
SERVICE = "botmarket-test-executor.service"
GRANTS = Path("/etc/botmarket-test-executor/sc001-shared-cache-grants")
BACKUPS = Path("/var/lib/botmarket-test-executor/capability-backups")
RECEIPTS = Path("/var/lib/botmarket-test-executor/capability-receipts")
SOURCE_INSTALLER = Path("scripts/mcp/install-botmarket-test-executor-v1.sh")
FILES = (POLICY, RUNNER, LAUNCHER, SERVER)
MAX_SINGLE_DATASET_BYTES = 5 * 1024**3
MAX_PEAK_WORKSPACE_INCREMENT = 15 * 1024**3
MAX_TIMEOUT_SECONDS = 900
ACK = "SC001-H1-004J-T3-HOST-MUTATION"
ROLES = {"NONE", "ACQUIRE_WRITE", "CONSUME_READ_ONLY", "SMOKE_WRITE", "SMOKE_READ_ONLY"}

class GateError(RuntimeError):
    pass

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def canonical_bytes(obj: object) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode()

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise GateError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)

def patch_policy(text: str) -> str:
    obj = json.loads(text)
    expected = {
        "schema": "botmarket.test_executor_policy.v1",
        "max_timeout_seconds": 900,
        "max_concurrent_jobs": 1,
        "memory_max_bytes": 1073741824,
        "tasks_max": 64,
        "cpu_quota_percent": 200,
        "trading_credentials_available_to_jobs": False,
        "arbitrary_shell_tool": False,
        "repo_write": False,
        "sudo_inside_job": False,
    }
    for key, value in expected.items():
        if obj.get(key) != value:
            raise GateError(f"policy drift: {key}")
    if "shared_cache" in obj:
        raise GateError("policy already contains shared_cache")
    obj["shared_cache"] = {
        "schema": "sc001.shared_cache_capability.v0.1",
        "root": str(SHARED_ROOT),
        "resource_id": RESOURCE_ID,
        "acquisition_entrypoint_sha256": ACQUISITION_SHA256,
        "roles": sorted(ROLES - {"NONE"}),
        "grant_directory": str(GRANTS),
        "max_single_dataset_bytes": MAX_SINGLE_DATASET_BYTES,
        "max_peak_workspace_increment": MAX_PEAK_WORKSPACE_INCREMENT,
        "max_timeout_seconds": MAX_TIMEOUT_SECONDS,
        "ordinary_jobs_access": "NONE",
        "grants_created_by_install": False,
    }
    return json.dumps(obj, indent=2) + "\n"

def patch_runner(text: str) -> str:
    text = replace_once(
        text, 'BASH=Path("/usr/bin/bash")\n',
        'BASH=Path("/usr/bin/bash")\n'
        f'SHARED_ROOT=Path("{SHARED_ROOT}")\n'
        f'RESOURCE_ID="{RESOURCE_ID}"\n', "runner constants")
    text = replace_once(
        text,
        '        if m.get("trading_credentials_available") is not False:\n'
        '            raise RuntimeError("TRADING_CREDENTIAL_BOUNDARY")\n'
        '        entry_rel=m.get("entrypoint")\n',
        '        if m.get("trading_credentials_available") is not False:\n'
        '            raise RuntimeError("TRADING_CREDENTIAL_BOUNDARY")\n'
        '        role=m.get("shared_cache_role") or "NONE"\n'
        '        resource=m.get("shared_cache_resource_id")\n'
        '        token=m.get("shared_cache_grant_token")\n'
        '        if role not in {"NONE","ACQUIRE_WRITE","CONSUME_READ_ONLY","SMOKE_WRITE","SMOKE_READ_ONLY"}:\n'
        '            raise RuntimeError("SHARED_CACHE_ROLE")\n'
        '        if role in {"ACQUIRE_WRITE","CONSUME_READ_ONLY"} and resource!=RESOURCE_ID:\n'
        '            raise RuntimeError("SHARED_CACHE_RESOURCE")\n'
        '        if role.startswith("SMOKE_") and resource!="SYNTHETIC":\n'
        '            raise RuntimeError("SHARED_CACHE_SMOKE_RESOURCE")\n'
        '        if role!="NONE" and (not isinstance(token,str) or not token):\n'
        '            raise RuntimeError("SHARED_CACHE_GRANT_TOKEN")\n'
        '        entry_rel=m.get("entrypoint")\n', "runner manifest gate")
    text = replace_once(
        text, '        env={\n',
        '        network_profile=str(m.get("network_profile") or "offline")\n'
        '        if role in {"ACQUIRE_WRITE","CONSUME_READ_ONLY"}:\n'
        '            data_root=SHARED_ROOT\n'
        '        elif role in {"SMOKE_WRITE","SMOKE_READ_ONLY"}:\n'
        '            data_root=SHARED_ROOT/"_capability_smoke"/str(token)\n'
        '        else:\n'
        '            data_root=output/"data"\n'
        '        env={\n', "runner data root")
    text = replace_once(
        text,
        '            "BM_TEST_NETWORK_PROFILE":str(m.get("network_profile") or "offline"),\n',
        '            "BM_TEST_NETWORK_PROFILE":network_profile,\n'
        '            "SC001_NETWORK_PROFILE":network_profile,\n'
        '            "SC001_SHARED_CACHE_ROLE":role,\n', "runner network mapping")
    text = replace_once(
        text, '            "SC001_DATA_ROOT":str(output/"data"),\n',
        '            "SC001_DATA_ROOT":str(data_root),\n', "runner SC001_DATA_ROOT")
    return replace_once(
        text,
        '        (output/"home").mkdir(parents=True,exist_ok=True)\n'
        '        (output/"data").mkdir(parents=True,exist_ok=True)\n',
        '        (output/"home").mkdir(parents=True,exist_ok=True)\n'
        '        if role=="NONE":\n'
        '            (output/"data").mkdir(parents=True,exist_ok=True)\n',
        "runner ordinary data directory")

def patch_launcher(text: str) -> str:
    text = replace_once(
        text, 'import sys\nfrom pathlib import Path\n',
        'import sys\nfrom datetime import datetime,timezone\nfrom pathlib import Path\n',
        "launcher datetime import")
    text = replace_once(
        text,
        'PUBLIC_RESOLV=Path("/var/lib/botmarket-test-executor/public-resolv.conf").resolve()\n',
        'PUBLIC_RESOLV=Path("/var/lib/botmarket-test-executor/public-resolv.conf").resolve()\n'
        f'SHARED_ROOT=Path("{SHARED_ROOT}").resolve()\n'
        f'GRANTS=Path("{GRANTS}").resolve()\n'
        f'RESOURCE_ID="{RESOURCE_ID}"\n'
        f'ACQUISITION_SHA256="{ACQUISITION_SHA256}"\n'
        f'MAX_SINGLE_DATASET_BYTES={MAX_SINGLE_DATASET_BYTES}\n'
        f'MAX_PEAK_WORKSPACE_INCREMENT={MAX_PEAK_WORKSPACE_INCREMENT}\n'
        'TOKEN_RE=re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{7,95}$")\n',
        "launcher constants")
    anchor = (
        'timeout=int(m.get("timeout_seconds") or 0)\n'
        'if timeout<1 or timeout>900:\n'
        '    die("TIMEOUT")\n\n'
        'for root,dirs,files in os.walk(package,followlinks=False):\n')
    inserted = (
        'timeout=int(m.get("timeout_seconds") or 0)\n'
        'if timeout<1 or timeout>900:\n'
        '    die("TIMEOUT")\n\n'
        'role=m.get("shared_cache_role") or "NONE"\n'
        'resource=m.get("shared_cache_resource_id")\n'
        'token=m.get("shared_cache_grant_token")\n'
        'grant=None\n'
        'if role not in {"NONE","ACQUIRE_WRITE","CONSUME_READ_ONLY","SMOKE_WRITE","SMOKE_READ_ONLY"}:\n'
        '    die("SHARED_CACHE_ROLE")\n'
        'if role=="NONE":\n'
        '    if resource is not None or token is not None:\n'
        '        die("SHARED_CACHE_NONE_FIELDS")\n'
        'else:\n'
        '    if not isinstance(token,str) or not TOKEN_RE.fullmatch(token):\n'
        '        die("SHARED_CACHE_TOKEN")\n'
        '    grant_path=(GRANTS/(token+".json")).resolve()\n'
        '    try:\n'
        '        grant_path.relative_to(GRANTS)\n'
        '    except ValueError:\n'
        '        die("SHARED_CACHE_GRANT_ESCAPE")\n'
        '    if not grant_path.is_file() or grant_path.is_symlink():\n'
        '        die("SHARED_CACHE_GRANT_MISSING")\n'
        '    try:\n'
        '        grant=json.loads(grant_path.read_text(encoding="utf-8"))\n'
        '    except Exception as exc:\n'
        '        die(f"SHARED_CACHE_GRANT_PARSE:{type(exc).__name__}")\n'
        '    expected_resource=RESOURCE_ID if role in {"ACQUIRE_WRITE","CONSUME_READ_ONLY"} else "SYNTHETIC"\n'
        '    if resource!=expected_resource or grant.get("resource_id")!=expected_resource:\n'
        '        die("SHARED_CACHE_RESOURCE")\n'
        '    if grant.get("schema")!="sc001.shared_cache_grant.v0.1" or grant.get("status")!="AUTHORIZED":\n'
        '        die("SHARED_CACHE_GRANT_SCHEMA")\n'
        '    if grant.get("task_id")!=m.get("shared_cache_task_id") or grant.get("role")!=role:\n'
        '        die("SHARED_CACHE_GRANT_SCOPE")\n'
        '    if grant.get("network_profile")!=network or grant.get("entrypoint_sha256")!=sha256_file(entry):\n'
        '        die("SHARED_CACHE_GRANT_BINDING")\n'
        '    if not isinstance(grant.get("t3_user_approval_ref"),str) or not grant["t3_user_approval_ref"]:\n'
        '        die("SHARED_CACHE_T3_REF")\n'
        '    try:\n'
        '        expiry=datetime.fromisoformat(str(grant["expires_utc"]).replace("Z","+00:00"))\n'
        '    except Exception:\n'
        '        die("SHARED_CACHE_GRANT_EXPIRY")\n'
        '    if expiry.tzinfo is None or expiry<=datetime.now(timezone.utc):\n'
        '        die("SHARED_CACHE_GRANT_EXPIRED")\n'
        '    if int(grant.get("max_timeout_seconds",0))>900 or timeout>int(grant.get("max_timeout_seconds",0)):\n'
        '        die("SHARED_CACHE_TIMEOUT_CAP")\n'
        '    if int(grant.get("max_single_dataset_bytes",0))>MAX_SINGLE_DATASET_BYTES:\n'
        '        die("SHARED_CACHE_DATASET_CAP")\n'
        '    if int(grant.get("max_peak_workspace_increment",0))>MAX_PEAK_WORKSPACE_INCREMENT:\n'
        '        die("SHARED_CACHE_PEAK_CAP")\n'
        '    if role=="ACQUIRE_WRITE":\n'
        '        if sha256_file(entry)!=ACQUISITION_SHA256 or network!="public_research":\n'
        '            die("SHARED_CACHE_ACQUIRE_BINDING")\n'
        '        for field in ("t1_task_authorization_ref","reservation_ref","disk_preflight_ref","collector_isolation_ref"):\n'
        '            if not isinstance(grant.get(field),str) or not grant[field]:\n'
        '                die("SHARED_CACHE_ACQUIRE_PREREQUISITE:"+field)\n'
        '    elif role=="CONSUME_READ_ONLY":\n'
        '        for field in ("verified_dataset_record","evidence_access_receipt"):\n'
        '            if not isinstance(grant.get(field),str) or not grant[field]:\n'
        '                die("SHARED_CACHE_CONSUME_PREREQUISITE:"+field)\n'
        '    elif network!="offline":\n'
        '        die("SHARED_CACHE_SMOKE_MUST_BE_OFFLINE")\n\n'
        'for root,dirs,files in os.walk(package,followlinks=False):\n')
    text = replace_once(text, anchor, inserted, "launcher grant gate")
    mount_anchor = (
        '    f"--property=ReadOnlyPaths={package} {manifest_path} {RUNNER}",\n'
        '    f"--property=ReadWritePaths={output}",\n'
        ']\n\nfor p in (\n')
    mount_insert = (
        '    f"--property=ReadOnlyPaths={package} {manifest_path} {RUNNER}",\n'
        ']\n'
        'rw_paths=[str(output)]\n'
        'ro_paths=[]\n'
        'if role=="ACQUIRE_WRITE":\n'
        '    rw_paths += [str(SHARED_ROOT/"_raw_cache"/"binance"/RESOURCE_ID), str(SHARED_ROOT/"quarantine"/RESOURCE_ID)]\n'
        'elif role=="CONSUME_READ_ONLY":\n'
        '    ro_paths.append(str(SHARED_ROOT))\n'
        'elif role in {"SMOKE_WRITE","SMOKE_READ_ONLY"}:\n'
        '    smoke=(SHARED_ROOT/"_capability_smoke"/str(token)).resolve()\n'
        '    try:\n'
        '        smoke.relative_to(SHARED_ROOT/"_capability_smoke")\n'
        '    except ValueError:\n'
        '        die("SHARED_CACHE_SMOKE_ESCAPE")\n'
        '    if not smoke.is_dir() or smoke.is_symlink():\n'
        '        die("SHARED_CACHE_SMOKE_DIR_MISSING")\n'
        '    (rw_paths if role=="SMOKE_WRITE" else ro_paths).append(str(smoke))\n'
        'common.append("--property=ReadWritePaths="+" ".join(rw_paths))\n'
        'if ro_paths:\n'
        '    common.append("--property=ReadOnlyPaths="+" ".join(ro_paths))\n'
        'if role=="NONE" and SHARED_ROOT.exists():\n'
        '    common.append(f"--property=InaccessiblePaths={SHARED_ROOT}")\n\n'
        'for p in (\n')
    text = replace_once(text, mount_anchor, mount_insert, "launcher mounts")
    return replace_once(
        text,
        'print(json.dumps({"job_id":job_id,"unit":unit,"network_profile":network,"timeout_seconds":timeout},sort_keys=True))\n',
        'print(json.dumps({"job_id":job_id,"unit":unit,"network_profile":network,"timeout_seconds":timeout,"shared_cache_role":role},sort_keys=True))\n',
        "launcher receipt")

def patch_server(text: str) -> str:
    signature = (
        'def run_repo_test(\n'
        '    repo_head_sha:str,\n'
        '    entrypoint:str,\n'
        '    args:list[str]|None=None,\n'
        '    network_profile:str="offline",\n'
        '    timeout_seconds:int|None=None,\n'
        ')->dict[str,Any]:\n')
    new_signature = (
        'def run_repo_test(\n'
        '    repo_head_sha:str,\n'
        '    entrypoint:str,\n'
        '    args:list[str]|None=None,\n'
        '    network_profile:str="offline",\n'
        '    timeout_seconds:int|None=None,\n'
        '    shared_cache_role:str="NONE",\n'
        '    shared_cache_resource_id:str|None=None,\n'
        '    shared_cache_grant_token:str|None=None,\n'
        '    shared_cache_task_id:str|None=None,\n'
        ')->dict[str,Any]:\n')
    text = replace_once(text, signature, new_signature, "server signature")
    gate_anchor = (
        '    if network_profile not in set(p["network_profiles"]):\n'
        '        raise ValueError("NETWORK_PROFILE")\n'
        '    timeout=int(timeout_seconds or p["default_timeout_seconds"])\n')
    gate_insert = (
        '    if network_profile not in set(p["network_profiles"]):\n'
        '        raise ValueError("NETWORK_PROFILE")\n'
        '    roles={"NONE","ACQUIRE_WRITE","CONSUME_READ_ONLY","SMOKE_WRITE","SMOKE_READ_ONLY"}\n'
        '    if shared_cache_role not in roles:\n'
        '        raise ValueError("SHARED_CACHE_ROLE")\n'
        '    if shared_cache_role=="NONE":\n'
        '        if any(x is not None for x in (shared_cache_resource_id,shared_cache_grant_token,shared_cache_task_id)):\n'
        '            raise ValueError("SHARED_CACHE_NONE_FIELDS")\n'
        '    else:\n'
        '        expected_resource="' + RESOURCE_ID + '" if shared_cache_role in {"ACQUIRE_WRITE","CONSUME_READ_ONLY"} else "SYNTHETIC"\n'
        '        if shared_cache_resource_id!=expected_resource:\n'
        '            raise ValueError("SHARED_CACHE_RESOURCE")\n'
        '        if not isinstance(shared_cache_grant_token,str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{7,95}",shared_cache_grant_token):\n'
        '            raise ValueError("SHARED_CACHE_GRANT_TOKEN")\n'
        '        if not isinstance(shared_cache_task_id,str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{3,95}",shared_cache_task_id):\n'
        '            raise ValueError("SHARED_CACHE_TASK_ID")\n'
        '    timeout=int(timeout_seconds or p["default_timeout_seconds"])\n')
    text = replace_once(text, gate_anchor, gate_insert, "server input gate")
    text = replace_once(
        text,
        '            "timeout_seconds":timeout,\n'
        '            "snapshot_file_count":snap["file_count"],\n',
        '            "timeout_seconds":timeout,\n'
        '            "shared_cache_role":shared_cache_role,\n'
        '            "shared_cache_resource_id":shared_cache_resource_id,\n'
        '            "shared_cache_grant_token":shared_cache_grant_token,\n'
        '            "shared_cache_task_id":shared_cache_task_id,\n'
        '            "snapshot_file_count":snap["file_count"],\n',
        "server manifest")
    return replace_once(
        text,
        '            "timeout_seconds":timeout,\n'
        '            "unit_state":unit_state(job_id),\n',
        '            "timeout_seconds":timeout,\n'
        '            "shared_cache_role":shared_cache_role,\n'
        '            "unit_state":unit_state(job_id),\n',
        "server return")

PATCHERS: dict[Path, Callable[[str], str]] = {
    POLICY: patch_policy, RUNNER: patch_runner, LAUNCHER: patch_launcher, SERVER: patch_server,
}

def verify_source_installer(path: Path) -> None:
    if not path.is_file() or path.is_symlink():
        raise GateError("source installer missing or symlinked")
    actual = sha256_file(path)
    if actual != INSTALLER_SHA256:
        raise GateError(f"source installer hash mismatch: {actual}")

def build_plan(source_installer: Path) -> tuple[dict, dict[Path, bytes]]:
    verify_source_installer(source_installer)
    targets: dict[Path, bytes] = {}
    entries = []
    for path in FILES:
        if not path.is_file() or path.is_symlink():
            raise GateError(f"installed artifact missing or symlinked: {path}")
        original = path.read_bytes()
        patched = PATCHERS[path](original.decode("utf-8")).encode()
        if patched == original:
            raise GateError(f"no-op patch: {path}")
        targets[path] = patched
        entries.append({
            "path": str(path), "before_sha256": sha256_bytes(original),
            "after_sha256": sha256_bytes(patched),
            "before_bytes": len(original), "after_bytes": len(patched),
        })
    plan = {
        "schema": "sc001.h1_shared_cache_capability_plan.v0.1", "task_id": TASK_ID,
        "source_installer": str(source_installer), "source_installer_sha256": INSTALLER_SHA256,
        "shared_root": str(SHARED_ROOT), "resource_id": RESOURCE_ID,
        "ordinary_jobs_access": "NONE", "grants_created": 0, "files": entries,
    }
    return plan, targets

def run_checked(*argv: str) -> None:
    subprocess.run(argv, check=True, stdin=subprocess.DEVNULL)

def ensure_root() -> None:
    if os.geteuid() != 0:
        raise GateError("root required")

def atomic_write(path: Path, data: bytes, mode: int, uid: int, gid: int) -> None:
    tmp = path.with_name(path.name + ".sc001-004j.tmp")
    if tmp.exists():
        raise GateError(f"stale temporary file: {tmp}")
    with tmp.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.chmod(tmp, mode)
    os.chown(tmp, uid, gid)
    os.replace(tmp, path)

def apply(args: argparse.Namespace) -> dict:
    ensure_root()
    if args.ack != ACK or not args.approval_ref:
        raise GateError("exact T3 acknowledgement and approval reference required")
    plan, targets = build_plan(args.source_installer)
    plan_hash = sha256_bytes(canonical_bytes(plan))
    if args.expected_plan_sha256 != plan_hash:
        raise GateError(f"plan hash mismatch; expected exact {plan_hash}")
    group_gid = grp.getgrnam("botmarket-test-jobs").gr_gid
    backup = BACKUPS / plan_hash
    if backup.exists():
        raise GateError(f"backup already exists: {backup}")
    BACKUPS.mkdir(mode=0o700, parents=True, exist_ok=True)
    RECEIPTS.mkdir(mode=0o700, parents=True, exist_ok=True)
    backup.mkdir(mode=0o700)
    for path in FILES:
        data = path.read_bytes()
        entry = next(x for x in plan["files"] if x["path"] == str(path))
        if sha256_bytes(data) != entry["before_sha256"]:
            raise GateError(f"changed after plan: {path}")
        name = hashlib.sha256(str(path).encode()).hexdigest() + ".bak"
        atomic_write(backup / name, data, path.stat().st_mode & 0o7777, 0, 0)
    (backup / "plan.json").write_bytes(canonical_bytes(plan))
    os.chmod(backup / "plan.json", 0o400)
    run_checked("systemctl", "stop", SERVICE)
    for path in FILES:
        st = path.stat()
        atomic_write(path, targets[path], st.st_mode & 0o7777, st.st_uid, st.st_gid)
    for path, mode in (
        (SHARED_ROOT, 0o2750), (SHARED_ROOT / "_raw_cache", 0o2750),
        (SHARED_ROOT / "_raw_cache" / "binance", 0o2750),
        (SHARED_ROOT / "_raw_cache" / "binance" / RESOURCE_ID, 0o2770),
        (SHARED_ROOT / "quarantine", 0o2750),
        (SHARED_ROOT / "quarantine" / RESOURCE_ID, 0o2770),
        (SHARED_ROOT / "_capability_smoke", 0o2750),
    ):
        path.mkdir(mode=mode, parents=True, exist_ok=True)
        os.chown(path, 0, group_gid)
        os.chmod(path, mode)
    GRANTS.mkdir(mode=0o750, parents=True, exist_ok=True)
    os.chown(GRANTS, 0, 0)
    os.chmod(GRANTS, 0o750)
    run_checked("systemctl", "daemon-reload")
    run_checked("systemctl", "start", SERVICE)
    receipt = {
        "schema": "sc001.h1_shared_cache_capability_apply_receipt.v0.1",
        "task_id": TASK_ID, "plan_sha256": plan_hash, "approval_ref": args.approval_ref,
        "applied_utc": datetime.now(timezone.utc).isoformat(), "backup": str(backup),
        "files": plan["files"], "shared_root_preserve_on_rollback": True,
        "grants_created": 0, "market_data_accessed": False,
    }
    receipt_path = RECEIPTS / (plan_hash + ".json")
    atomic_write(receipt_path, canonical_bytes(receipt), 0o400, 0, 0)
    return receipt

def rollback(args: argparse.Namespace) -> dict:
    ensure_root()
    if args.ack != ACK or not args.approval_ref:
        raise GateError("exact T3 acknowledgement and approval reference required")
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    if receipt.get("schema") != "sc001.h1_shared_cache_capability_apply_receipt.v0.1":
        raise GateError("receipt schema")
    backup = Path(receipt["backup"]).resolve()
    backup.relative_to(BACKUPS)
    plan = json.loads((backup / "plan.json").read_text(encoding="utf-8"))
    for entry in plan["files"]:
        path = Path(entry["path"])
        if sha256_file(path) != entry["after_sha256"]:
            raise GateError(f"installed file changed; rollback refused: {path}")
    run_checked("systemctl", "stop", SERVICE)
    for entry in plan["files"]:
        path = Path(entry["path"])
        name = hashlib.sha256(str(path).encode()).hexdigest() + ".bak"
        saved = backup / name
        if sha256_file(saved) != entry["before_sha256"]:
            raise GateError(f"backup hash mismatch: {path}")
        st = path.stat()
        atomic_write(path, saved.read_bytes(), st.st_mode & 0o7777, st.st_uid, st.st_gid)
    run_checked("systemctl", "daemon-reload")
    run_checked("systemctl", "start", SERVICE)
    return {
        "schema": "sc001.h1_shared_cache_capability_rollback_receipt.v0.1",
        "task_id": TASK_ID, "rolled_back_utc": datetime.now(timezone.utc).isoformat(),
        "approval_ref": args.approval_ref, "shared_root_deleted": False,
        "verified_cache_deleted": False,
    }

def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--source-installer", type=Path, default=SOURCE_INSTALLER)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("plan")
    a = sub.add_parser("apply")
    a.add_argument("--expected-plan-sha256", required=True)
    a.add_argument("--approval-ref", required=True)
    a.add_argument("--ack", required=True)
    r = sub.add_parser("rollback")
    r.add_argument("--receipt", required=True, type=Path)
    r.add_argument("--approval-ref", required=True)
    r.add_argument("--ack", required=True)
    return p

def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "plan":
            plan, _ = build_plan(args.source_installer)
            obj = {"plan": plan, "plan_sha256": sha256_bytes(canonical_bytes(plan))}
        elif args.command == "apply":
            obj = apply(args)
        else:
            obj = rollback(args)
        print(json.dumps(obj, indent=2, sort_keys=True))
        return 0
    except (GateError, OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(f"SC001_H1_CAPABILITY_FAIL_CLOSED:{type(exc).__name__}:{exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
