#!/usr/bin/env python3
from __future__ import annotations
import argparse
import grp
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

TASK_ID = "SC001-H1-004J-R1"
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
ACK = "SC001-H1-004J-R1-T3-HOST-MUTATION"
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
        'import sys\nimport stat\nfrom datetime import datetime,timezone\nfrom pathlib import Path\n',
        "launcher datetime import")
    text = replace_once(
        text,
        'PUBLIC_RESOLV=Path("/var/lib/botmarket-test-executor/public-resolv.conf").resolve()\n',
        'PUBLIC_RESOLV=Path("/var/lib/botmarket-test-executor/public-resolv.conf").resolve()\n'
        f'SHARED_ROOT=Path("{SHARED_ROOT}").resolve()\n'
        f'GRANTS=Path("{GRANTS}")\n'
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
        '    grant_path=GRANTS/(token+".json")\n'
        '    grant_dir_fd=None\n'
        '    grant_fd=None\n'
        '    try:\n'
        '        if GRANTS.resolve()!=GRANTS:\n'
        '            die("SHARED_CACHE_GRANT_DIRECTORY")\n'
        '        grant_dir_fd=os.open(GRANTS,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)\n'
        '        directory_stat=os.fstat(grant_dir_fd)\n'
        '        if not stat.S_ISDIR(directory_stat.st_mode) or directory_stat.st_uid!=0 or directory_stat.st_mode&0o022:\n'
        '            die("SHARED_CACHE_GRANT_DIRECTORY")\n'
        '        grant_fd=os.open(token+".json",os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=grant_dir_fd)\n'
        '        grant_stat=os.fstat(grant_fd)\n'
        '        if not stat.S_ISREG(grant_stat.st_mode) or grant_stat.st_uid!=0 or grant_stat.st_mode&0o022:\n'
        '            die("SHARED_CACHE_GRANT_PERMISSIONS")\n'
        '        with os.fdopen(grant_fd,"r",encoding="utf-8") as stream:\n'
        '            grant_fd=None\n'
        '            raw=stream.read(65537)\n'
        '        if len(raw)>65536:\n'
        '            die("SHARED_CACHE_GRANT_SIZE")\n'
        '        grant=json.loads(raw)\n'
        '        if not isinstance(grant,dict):\n'
        '            die("SHARED_CACHE_GRANT_SCHEMA")\n'
        '    except (OSError,ValueError) as exc:\n'
        '        die(f"SHARED_CACHE_GRANT_READ:{type(exc).__name__}")\n'
        '    finally:\n'
        '        if grant_fd is not None:\n'
        '            os.close(grant_fd)\n'
        '        if grant_dir_fd is not None:\n'
        '            os.close(grant_dir_fd)\n'
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
        '    for field,ceiling,error in (\n'
        '        ("max_timeout_seconds",900,"SHARED_CACHE_TIMEOUT_CAP"),\n'
        '        ("max_single_dataset_bytes",MAX_SINGLE_DATASET_BYTES,"SHARED_CACHE_DATASET_CAP"),\n'
        '        ("max_peak_workspace_increment",MAX_PEAK_WORKSPACE_INCREMENT,"SHARED_CACHE_PEAK_CAP"),\n'
        '    ):\n'
        '        value=grant.get(field)\n'
        '        if type(value) is not int or not 1<=value<=ceiling:\n'
        '            die(error)\n'
        '    if timeout>grant["max_timeout_seconds"]:\n'
        '        die("SHARED_CACHE_TIMEOUT_CAP")\n'
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
        st = path.stat()
        entries.append({
            "path": str(path), "before_sha256": sha256_bytes(original),
            "after_sha256": sha256_bytes(patched),
            "before_bytes": len(original), "after_bytes": len(patched),
            "before_mode": stat.S_IMODE(st.st_mode), "before_uid": st.st_uid, "before_gid": st.st_gid,
        })
    plan = {
        "schema": "sc001.h1_shared_cache_capability_plan.v0.2", "task_id": TASK_ID,
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

def fsync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def temporary_path(path: Path) -> Path:
    return path.with_name(path.name + ".sc001-004j-r1.tmp")


def reject_target_temps() -> None:
    for path in FILES:
        tmp = temporary_path(path)
        if tmp.exists() or tmp.is_symlink():
            raise GateError(f"target temporary file already exists: {tmp}")


def atomic_write(path: Path, data: bytes, mode: int, uid: int, gid: int) -> None:
    tmp = temporary_path(path)
    # Exclusive open rejects stale/dangling temporary files without deleting them.
    created = False
    try:
        with tmp.open("xb") as stream:
            created = True
            stream.write(data)
            stream.flush()
            os.fchown(stream.fileno(), uid, gid)
            os.fchmod(stream.fileno(), mode)
            os.fsync(stream.fileno())
        os.replace(tmp, path)
        created = False
        fsync_directory(path.parent)
    finally:
        # A failed write must not strand our temporary file and block rollback.
        if created:
            tmp.unlink()


def open_authority_directory(path: Path) -> int:
    if not path.is_absolute() or path.resolve() != path:
        raise GateError("authority path must be absolute and symlink-free")
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        st = os.fstat(fd)
        if not stat.S_ISDIR(st.st_mode) or st.st_uid != 0 or st.st_mode & 0o022:
            raise GateError("authority directory ownership or mode")
        return fd
    except BaseException:
        os.close(fd)
        raise


def trusted_bytes(path: Path, limit: int = 131072) -> bytes:
    """Read one root-owned non-writable artifact through pinned descriptors."""
    directory_fd = open_authority_directory(path.parent)
    fd = None
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid != 0 or st.st_mode & 0o022:
            raise GateError("authority file ownership or mode")
        with os.fdopen(fd, "rb") as stream:
            fd = None
            data = stream.read(limit + 1)
        if len(data) > limit:
            raise GateError("authority artifact size")
        return data
    finally:
        if fd is not None:
            os.close(fd)
        os.close(directory_fd)


def trusted_json(path: Path) -> dict:
    obj = json.loads(trusted_bytes(path))
    if not isinstance(obj, dict):
        raise GateError("authority JSON object required")
    return obj


def apply(args: argparse.Namespace) -> dict:
    ensure_root()
    if args.ack != ACK or not args.approval_ref:
        raise GateError("exact T3 acknowledgement and approval reference required")
    plan, targets = build_plan(args.source_installer)
    plan_hash = sha256_bytes(canonical_bytes(plan))
    if args.expected_plan_sha256 != plan_hash:
        raise GateError(f"plan hash mismatch; expected exact {plan_hash}")
    reject_target_temps()
    group_gid = grp.getgrnam("botmarket-test-jobs").gr_gid
    backup = BACKUPS / plan_hash
    receipt_path = RECEIPTS / (plan_hash + ".json")
    if backup.exists() or backup.is_symlink() or receipt_path.exists() or receipt_path.is_symlink():
        raise GateError("backup or receipt already exists")
    BACKUPS.mkdir(mode=0o700, parents=True, exist_ok=True)
    RECEIPTS.mkdir(mode=0o700, parents=True, exist_ok=True)
    for directory in (BACKUPS, RECEIPTS):
        os.close(open_authority_directory(directory))
    fsync_directory(BACKUPS.parent)
    fsync_directory(RECEIPTS.parent)
    backup.mkdir(mode=0o700)
    fsync_directory(BACKUPS)
    for path, entry in zip(FILES, plan["files"]):
        data = path.read_bytes()
        if sha256_bytes(data) != entry["before_sha256"]:
            raise GateError(f"changed after plan: {path}")
        name = hashlib.sha256(str(path).encode()).hexdigest() + ".bak"
        atomic_write(backup / name, data, 0o400, 0, 0)
    atomic_write(backup / "plan.json", canonical_bytes(plan), 0o400, 0, 0)
    receipt = {
        "schema": "sc001.h1_shared_cache_capability_apply_receipt.v0.2",
        "task_id": TASK_ID, "plan_sha256": plan_hash, "approval_ref": args.approval_ref,
        "state": "PREPARED", "prepared_utc": datetime.now(timezone.utc).isoformat(),
        "backup": str(backup), "files": plan["files"],
        "shared_root_preserve_on_rollback": True, "grants_created": 0,
        "market_data_accessed": False,
    }
    # Durable rollback authority exists BEFORE the first service/target mutation.
    atomic_write(receipt_path, canonical_bytes(receipt), 0o400, 0, 0)
    run_checked("systemctl", "stop", SERVICE)
    for path, entry in zip(FILES, plan["files"]):
        atomic_write(path, targets[path], entry["before_mode"], entry["before_uid"], entry["before_gid"])
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
    receipt["state"] = "APPLIED"
    receipt["applied_utc"] = datetime.now(timezone.utc).isoformat()
    atomic_write(receipt_path, canonical_bytes(receipt), 0o400, 0, 0)
    return receipt


def rollback(args: argparse.Namespace) -> dict:
    ensure_root()
    if args.ack != ACK or not args.approval_ref:
        raise GateError("exact T3 acknowledgement and approval reference required")
    plan_hash = args.expected_plan_sha256
    if not isinstance(plan_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", plan_hash):
        raise GateError("expected plan SHA256 required")
    if args.receipt != RECEIPTS / (plan_hash + ".json"):
        raise GateError("receipt path does not match expected plan")
    receipt = trusted_json(args.receipt)
    if (receipt.get("schema") != "sc001.h1_shared_cache_capability_apply_receipt.v0.2"
            or receipt.get("task_id") != TASK_ID
            or receipt.get("state") not in {"PREPARED", "APPLIED"}
            or receipt.get("plan_sha256") != plan_hash
            or not isinstance(receipt.get("approval_ref"), str) or not receipt["approval_ref"]
            or receipt.get("shared_root_preserve_on_rollback") is not True
            or type(receipt.get("grants_created")) is not int or receipt["grants_created"] != 0
            or receipt.get("market_data_accessed") is not False):
        raise GateError("receipt binding")
    backup = BACKUPS / plan_hash
    if receipt.get("backup") != str(backup):
        raise GateError("receipt backup binding")
    plan = trusted_json(backup / "plan.json")
    if sha256_bytes(canonical_bytes(plan)) != plan_hash:
        raise GateError("plan hash mismatch")
    if (plan.get("schema") != "sc001.h1_shared_cache_capability_plan.v0.2"
            or plan.get("task_id") != TASK_ID
            or plan.get("source_installer_sha256") != INSTALLER_SHA256
            or plan.get("shared_root") != str(SHARED_ROOT)
            or plan.get("resource_id") != RESOURCE_ID
            or plan.get("ordinary_jobs_access") != "NONE"
            or type(plan.get("grants_created")) is not int or plan["grants_created"] != 0
            or plan.get("files") != receipt.get("files")):
        raise GateError("plan binding")
    entries = plan.get("files")
    if not isinstance(entries, list) or len(entries) != len(FILES):
        raise GateError("plan file count")
    restore = []
    # Validate ALL targets and backups before stopping or modifying anything.
    for path, entry in zip(FILES, entries):
        if not isinstance(entry, dict) or entry.get("path") != str(path):
            raise GateError("plan file allowlist")
        for field in ("before_sha256", "after_sha256"):
            if not isinstance(entry.get(field), str) or not re.fullmatch(r"[0-9a-f]{64}", entry[field]):
                raise GateError("plan file hash")
        for field in ("before_bytes", "after_bytes", "before_mode", "before_uid", "before_gid"):
            if type(entry.get(field)) is not int or entry[field] < 0:
                raise GateError("plan file metadata")
        if entry["before_mode"] > 0o7777 or not path.is_file() or path.is_symlink():
            raise GateError("installed file type or mode")
        if sha256_file(path) not in {entry["before_sha256"], entry["after_sha256"]}:
            raise GateError(f"installed file changed; rollback refused: {path}")
        name = hashlib.sha256(str(path).encode()).hexdigest() + ".bak"
        data = trusted_bytes(backup / name, limit=entry["before_bytes"])
        if len(data) != entry["before_bytes"] or sha256_bytes(data) != entry["before_sha256"]:
            raise GateError(f"backup hash mismatch: {path}")
        restore.append((path, data, entry))
    reject_target_temps()
    run_checked("systemctl", "stop", SERVICE)
    for path, data, entry in restore:
        atomic_write(path, data, entry["before_mode"], entry["before_uid"], entry["before_gid"])
    run_checked("systemctl", "daemon-reload")
    run_checked("systemctl", "start", SERVICE)
    return {
        "schema": "sc001.h1_shared_cache_capability_rollback_receipt.v0.2",
        "task_id": TASK_ID, "plan_sha256": plan_hash,
        "rolled_back_utc": datetime.now(timezone.utc).isoformat(),
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
    r.add_argument("--expected-plan-sha256", required=True)
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
