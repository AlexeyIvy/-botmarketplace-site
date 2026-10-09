#!/usr/bin/env python3
"""Install or remove the frozen, fixed-purpose SC001 B13-C health interface.

Repository/static validation is read-only and never opens collector state.  The
--apply and --rollback modes are host mutations and require a separately
approved exact T3 action.  This file deliberately provides no live-read mode.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import os
import pwd
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NoReturn, Sequence


SOURCE_ADAPTER_RELATIVE = Path("ops/mcp/sc001_b13c_health_adapter_v0_1.py")
SOURCE_ADAPTER_SHA256 = (
    "844949ec670c6cd1856d2a1ea016f3554b6c6e85b95b254b6e370907eb47d2c7"
)
PACKAGE_PARENT = Path("/usr/local/libexec/botmarket-research")
PACKAGE_DIR = PACKAGE_PARENT / "sc001-b13c-health-v0.1"
INSTALLED_ADAPTER = PACKAGE_DIR / "sc001_b13c_health_adapter_v0_1.py"
ENTRYPOINT = PACKAGE_DIR / "sc001_b13c_health_entrypoint_v0_1.py"
SUDOERS_PATH = Path("/etc/sudoers.d/sc001-b13c-health-v0.1")
TARGET_USER = "botmarket"
CALLER_USER = "botmarket-mcp"
PYTHON = Path("/usr/bin/python3")
VISUDO = Path("/usr/sbin/visudo")

ENTRYPOINT_CONTENT = '''#!/usr/bin/python3
"""Zero-argument, allowlist-enforcing B13-C operational-health entrypoint."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import NoReturn


ADAPTER_PATH = Path(
    "/usr/local/libexec/botmarket-research/sc001-b13c-health-v0.1/"
    "sc001_b13c_health_adapter_v0_1.py"
)
ADAPTER_SHA256 = "844949ec670c6cd1856d2a1ea016f3554b6c6e85b95b254b6e370907eb47d2c7"
MAX_OUTPUT_BYTES = 4096
TOP_KEYS = {
    "schema",
    "adapter_version",
    "collector_id",
    "observed_at_ms",
    "state",
    "process",
    "evidence_eligibility",
}
STATE_KEYS = {
    "availability",
    "error",
    "collector_status",
    "connection_state",
    "heartbeat",
    "qualified_symbol_count",
    "reconnect_diagnostics",
    "process_gap_diagnostics",
}
PROCESS_KEYS = {"availability", "error", "active_state", "sub_state", "running"}
STATE_AVAILABILITY = {"AVAILABLE", "PARTIAL", "UNAVAILABLE"}
STATE_ERRORS = {
    "NONE",
    "STATE_FIELDS_UNAVAILABLE",
    "STATE_HEARTBEAT_FUTURE",
    "STATE_MISSING",
    "STATE_PERMISSION_DENIED",
    "STATE_SYMLINK_REJECTED",
    "STATE_NONREGULAR",
    "STATE_IO_ERROR",
    "STATE_PATH_INVALID",
    "STATE_TOO_LARGE",
    "STATE_INVALID_UTF8",
    "STATE_DUPLICATE_KEY",
    "STATE_INVALID_JSON",
    "STATE_WRONG_IDENTITY",
    "STATE_TYPE_ERROR",
    "OBSERVATION_TIME_INVALID",
}
PROCESS_AVAILABILITY = {"AVAILABLE", "UNAVAILABLE"}
PROCESS_ERRORS = {"NONE", "PROCESS_QUERY_FAILED", "PROCESS_RESPONSE_INVALID"}
COLLECTOR_STATUS = {
    "INITIALIZED",
    "B13C_COLLECTION_RUNNING",
    "B13C_COLLECTION_SOURCE_REVIEW",
    "B13C_COLLECTION_IMPLEMENTATION_FAIL",
    "B13C_COLLECTION_STOPPED",
}
CONNECTION_STATE = {"CONNECTED", "DISCONNECTED", "STOPPED"}
HEARTBEAT_STATE = {"CURRENT", "STALE", "FUTURE", "UNAVAILABLE"}


def fail(code: str) -> NoReturn:
    print(f"SC001_B13C_HEALTH_FAIL:{code}", file=sys.stderr)
    raise SystemExit(2)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            while block := handle.read(65536):
                digest.update(block)
    except OSError:
        fail("ADAPTER_READ")
    return digest.hexdigest()


def exact_keys(value: object, expected: set[str], code: str) -> dict[str, object]:
    if type(value) is not dict or set(value) != expected:
        fail(code)
    return value


def bounded_int(value: object, maximum: int, nullable: bool, code: str) -> None:
    if nullable and value is None:
        return
    if type(value) is not int or value < 0 or value > maximum:
        fail(code)


def optional_token(value: object, allowed: set[str], code: str) -> None:
    if value is not None and (type(value) is not str or value not in allowed):
        fail(code)


def validate_health(value: object) -> dict[str, object]:
    health = exact_keys(value, TOP_KEYS, "TOP_LEVEL_ALLOWLIST")
    if health["schema"] != "sc001.b13c_operational_health.v0.1":
        fail("SCHEMA")
    if health["adapter_version"] != "0.1":
        fail("ADAPTER_VERSION")
    if health["collector_id"] != "SC001_B13C_PROSPECTIVE_LIQUIDATIONS":
        fail("COLLECTOR_ID")
    if health["evidence_eligibility"] != "NOT_EVALUATED":
        fail("EVIDENCE_ELIGIBILITY")
    bounded_int(health["observed_at_ms"], 10**16, False, "OBSERVED_AT")

    state = exact_keys(health["state"], STATE_KEYS, "STATE_ALLOWLIST")
    if state["availability"] not in STATE_AVAILABILITY:
        fail("STATE_AVAILABILITY")
    if state["error"] not in STATE_ERRORS:
        fail("STATE_ERROR")
    optional_token(state["collector_status"], COLLECTOR_STATUS, "COLLECTOR_STATUS")
    optional_token(state["connection_state"], CONNECTION_STATE, "CONNECTION_STATE")
    bounded_int(state["qualified_symbol_count"], 12, True, "QUALIFIED_COUNT")

    heartbeat = exact_keys(state["heartbeat"], {"state", "age_ms"}, "HEARTBEAT_ALLOWLIST")
    if heartbeat["state"] not in HEARTBEAT_STATE:
        fail("HEARTBEAT_STATE")
    bounded_int(heartbeat["age_ms"], 10**16, True, "HEARTBEAT_AGE")

    reconnect = exact_keys(
        state["reconnect_diagnostics"],
        {"reconnect_count", "cumulative_gap_ms"},
        "RECONNECT_ALLOWLIST",
    )
    bounded_int(reconnect["reconnect_count"], 2**63 - 1, True, "RECONNECT_COUNT")
    bounded_int(reconnect["cumulative_gap_ms"], 2**63 - 1, True, "CONNECTION_GAP")

    process_gap = exact_keys(
        state["process_gap_diagnostics"],
        {"process_restart_count", "cumulative_process_gap_ms"},
        "PROCESS_GAP_ALLOWLIST",
    )
    bounded_int(
        process_gap["process_restart_count"], 2**63 - 1, True, "PROCESS_RESTART_COUNT"
    )
    bounded_int(
        process_gap["cumulative_process_gap_ms"], 2**63 - 1, True, "PROCESS_GAP"
    )

    process = exact_keys(health["process"], PROCESS_KEYS, "PROCESS_ALLOWLIST")
    if process["availability"] not in PROCESS_AVAILABILITY:
        fail("PROCESS_AVAILABILITY")
    if process["error"] not in PROCESS_ERRORS:
        fail("PROCESS_ERROR")
    for name in ("active_state", "sub_state"):
        token = process[name]
        if token is not None and (
            type(token) is not str
            or not token
            or len(token) > 32
            or not token[0].islower()
            or any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-" for char in token)
        ):
            fail("PROCESS_TOKEN")
    if process["running"] is not None and type(process["running"]) is not bool:
        fail("PROCESS_RUNNING")
    return health


def main() -> int:
    if len(sys.argv) != 1:
        fail("ARGUMENTS_FORBIDDEN")
    sys.dont_write_bytecode = True
    os.environ.clear()
    os.environ["PATH"] = "/usr/bin:/bin"
    os.environ["LANG"] = "C.UTF-8"
    os.umask(0o077)

    if file_sha256(ADAPTER_PATH) != ADAPTER_SHA256:
        fail("ADAPTER_SHA256")
    try:
        spec = importlib.util.spec_from_file_location("sc001_b13c_health_adapter", ADAPTER_PATH)
        if spec is None or spec.loader is None:
            fail("ADAPTER_IMPORT")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        get_health = getattr(module, "get_health", None)
        if not callable(get_health):
            fail("ADAPTER_SURFACE")
        health = validate_health(get_health())
        payload = (
            json.dumps(health, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(",", ":"))
            + "\\n"
        ).encode("ascii")
    except SystemExit:
        raise
    except Exception:
        fail("ADAPTER_EXECUTION")
    if len(payload) > MAX_OUTPUT_BYTES:
        fail("OUTPUT_TOO_LARGE")
    sys.stdout.buffer.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

SUDOERS_CONTENT = (
    "# SC001 B13-C fixed read-only health interface v0.1\\n"
    "Cmnd_Alias SC001_B13C_HEALTH_V01 = /usr/bin/python3 -I "
    "/usr/local/libexec/botmarket-research/sc001-b13c-health-v0.1/"
    "sc001_b13c_health_entrypoint_v0_1.py\\n"
    "botmarket-mcp ALL=(botmarket) NOPASSWD:NOSETENV: SC001_B13C_HEALTH_V01\\n"
)


class DeployError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def fail(code: str) -> NoReturn:
    raise DeployError(code)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            while block := handle.read(1024 * 1024):
                digest.update(block)
    except OSError:
        fail("FILE_READ")
    return digest.hexdigest()


def repository_root() -> Path:
    try:
        script = Path(__file__).resolve(strict=True)
    except OSError:
        fail("SCRIPT_PATH")
    root = script.parents[2]
    if (root / SOURCE_ADAPTER_RELATIVE).is_file():
        return root
    fail("REPOSITORY_ROOT")


def source_adapter(root: Path) -> Path:
    source = root / SOURCE_ADAPTER_RELATIVE
    try:
        metadata = source.lstat()
    except OSError:
        fail("SOURCE_ADAPTER_MISSING")
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        fail("SOURCE_ADAPTER_TYPE")
    if sha256_file(source) != SOURCE_ADAPTER_SHA256:
        fail("SOURCE_ADAPTER_SHA256")
    return source


def expected_entrypoint_hash() -> str:
    return sha256_bytes(ENTRYPOINT_CONTENT.encode("utf-8"))


def expected_sudoers_hash() -> str:
    return sha256_bytes(SUDOERS_CONTENT.encode("utf-8"))


def require_root() -> None:
    if os.geteuid() != 0:
        fail("ROOT_REQUIRED")


def require_identities() -> None:
    try:
        target = pwd.getpwnam(TARGET_USER)
        caller = pwd.getpwnam(CALLER_USER)
    except KeyError:
        fail("REQUIRED_USER_MISSING")
    if target.pw_uid == 0 or caller.pw_uid == 0 or target.pw_uid == caller.pw_uid:
        fail("REQUIRED_USER_INVALID")


def require_fixed_tools() -> None:
    for path in (PYTHON, VISUDO):
        try:
            link_metadata = path.lstat()
            resolved = path.resolve(strict=True)
            metadata = resolved.stat()
        except OSError:
            fail("HOST_TOOL_MISSING")
        if (
            link_metadata.st_uid != 0
            or link_metadata.st_gid != 0
            or link_metadata.st_mode & 0o022
            or not stat.S_ISREG(metadata.st_mode)
        ):
            fail("HOST_TOOL_TYPE")
        if metadata.st_uid != 0 or metadata.st_gid != 0 or metadata.st_mode & 0o022:
            fail("HOST_TOOL_TRUST")


def require_trusted_directory(path: Path) -> None:
    try:
        metadata = path.lstat()
    except OSError:
        fail("TRUSTED_DIRECTORY_MISSING")
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != 0
        or metadata.st_gid != 0
        or metadata.st_mode & 0o022
    ):
        fail("TRUSTED_DIRECTORY_INVALID")


def ensure_parent() -> None:
    for trusted in (Path("/usr"), Path("/usr/local"), Path("/usr/local/libexec")):
        require_trusted_directory(trusted)
    try:
        PACKAGE_PARENT.mkdir(mode=0o755, exist_ok=True)
        metadata = PACKAGE_PARENT.lstat()
    except OSError:
        fail("PACKAGE_PARENT")
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != 0
        or metadata.st_gid != 0
        or metadata.st_mode & 0o022
    ):
        fail("PACKAGE_PARENT_TRUST")


def write_staged_file(path: Path, payload: bytes, mode: int) -> None:
    descriptor = -1
    try:
        descriptor = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0),
            mode,
        )
        os.fchown(descriptor, 0, 0)
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            descriptor = -1
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError:
        fail("STAGED_WRITE")
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def metadata_matches(path: Path, expected_hash: str, mode: int) -> bool:
    try:
        metadata = path.lstat()
    except OSError:
        return False
    return (
        stat.S_ISREG(metadata.st_mode)
        and not stat.S_ISLNK(metadata.st_mode)
        and metadata.st_uid == 0
        and metadata.st_gid == 0
        and stat.S_IMODE(metadata.st_mode) == mode
        and metadata.st_nlink == 1
        and sha256_file(path) == expected_hash
    )


def package_matches() -> bool:
    try:
        metadata = PACKAGE_DIR.lstat()
        names = {item.name for item in PACKAGE_DIR.iterdir()}
    except OSError:
        return False
    return (
        stat.S_ISDIR(metadata.st_mode)
        and not stat.S_ISLNK(metadata.st_mode)
        and metadata.st_uid == 0
        and metadata.st_gid == 0
        and stat.S_IMODE(metadata.st_mode) == 0o555
        and names == {INSTALLED_ADAPTER.name, ENTRYPOINT.name}
        and metadata_matches(INSTALLED_ADAPTER, SOURCE_ADAPTER_SHA256, 0o444)
        and metadata_matches(ENTRYPOINT, expected_entrypoint_hash(), 0o444)
    )


def sudoers_matches() -> bool:
    return metadata_matches(SUDOERS_PATH, expected_sudoers_hash(), 0o440)


def install_package(source: Path) -> None:
    if PACKAGE_DIR.exists() or PACKAGE_DIR.is_symlink():
        fail("PACKAGE_CONFLICT")
    try:
        adapter_payload = source.read_bytes()
    except OSError:
        fail("SOURCE_ADAPTER_READ")
    staging = Path(tempfile.mkdtemp(prefix=".sc001-b13c-health-v0.1-", dir=PACKAGE_PARENT))
    try:
        os.chown(staging, 0, 0)
        os.chmod(staging, 0o700)
        write_staged_file(staging / INSTALLED_ADAPTER.name, adapter_payload, 0o444)
        write_staged_file(staging / ENTRYPOINT.name, ENTRYPOINT_CONTENT.encode("utf-8"), 0o444)
        os.chmod(staging, 0o555)
        os.rename(staging, PACKAGE_DIR)
    except DeployError:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    except OSError:
        shutil.rmtree(staging, ignore_errors=True)
        fail("PACKAGE_INSTALL")
    if not package_matches():
        fail("PACKAGE_VERIFY")


def install_sudoers() -> None:
    if SUDOERS_PATH.exists() or SUDOERS_PATH.is_symlink():
        fail("SUDOERS_CONFLICT")
    try:
        directory = SUDOERS_PATH.parent.lstat()
    except OSError:
        fail("SUDOERS_PARENT")
    if (
        stat.S_ISLNK(directory.st_mode)
        or not stat.S_ISDIR(directory.st_mode)
        or directory.st_uid != 0
        or directory.st_gid != 0
        or directory.st_mode & 0o022
    ):
        fail("SUDOERS_PARENT_TRUST")

    descriptor = -1
    temporary: Path | None = None
    try:
        descriptor, name = tempfile.mkstemp(prefix=".sc001-b13c-health-v0.1-", dir=SUDOERS_PATH.parent)
        temporary = Path(name)
        os.fchown(descriptor, 0, 0)
        os.fchmod(descriptor, 0o440)
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            descriptor = -1
            handle.write(SUDOERS_CONTENT.encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        completed = subprocess.run(
            [str(VISUDO), "-cf", str(temporary)],
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            shell=False,
        )
        if completed.returncode != 0:
            fail("SUDOERS_SYNTAX")
        os.rename(temporary, SUDOERS_PATH)
        temporary = None
    except DeployError:
        raise
    except (OSError, subprocess.SubprocessError):
        fail("SUDOERS_INSTALL")
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary is not None:
            try:
                temporary.unlink()
            except OSError:
                pass
    if not sudoers_matches():
        fail("SUDOERS_VERIFY")


def remove_exact_package() -> None:
    if not package_matches() or not sudoers_matches():
        fail("ROLLBACK_IDENTITY_MISMATCH")
    try:
        SUDOERS_PATH.unlink()
        ENTRYPOINT.unlink()
        INSTALLED_ADAPTER.unlink()
        PACKAGE_DIR.rmdir()
    except OSError:
        fail("ROLLBACK_REMOVE")


def static_validate(root: Path) -> tuple[str, str]:
    source = source_adapter(root)
    try:
        ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        ast.parse(ENTRYPOINT_CONTENT, filename=ENTRYPOINT.name)
    except (OSError, UnicodeError, SyntaxError):
        fail("STATIC_PARSE")
    if "evidence_eligibility\"] != \"NOT_EVALUATED\"" not in ENTRYPOINT_CONTENT:
        fail("STATIC_EVIDENCE_GUARD")
    if "len(sys.argv) != 1" not in ENTRYPOINT_CONTENT:
        fail("STATIC_ARGUMENT_GUARD")
    return expected_entrypoint_hash(), expected_sudoers_hash()


def run_apply(root: Path) -> str:
    require_root()
    require_identities()
    require_fixed_tools()
    source = source_adapter(root)
    ensure_parent()
    package_exists = PACKAGE_DIR.exists() or PACKAGE_DIR.is_symlink()
    sudoers_exists = SUDOERS_PATH.exists() or SUDOERS_PATH.is_symlink()
    if package_exists or sudoers_exists:
        if package_matches() and sudoers_matches():
            return "ALREADY_INSTALLED"
        fail("PARTIAL_OR_CONFLICTING_INSTALL")
    install_package(source)
    try:
        install_sudoers()
    except DeployError:
        try:
            ENTRYPOINT.unlink()
            INSTALLED_ADAPTER.unlink()
            PACKAGE_DIR.rmdir()
        except OSError:
            pass
        raise
    return "INSTALLED"


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Freeze-controlled B13-C health interface installer.")
    mode = value.add_mutually_exclusive_group()
    mode.add_argument("--static-validate", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--rollback", action="store_true")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if not (args.static_validate or args.apply or args.rollback):
        print("NO_ACTION_USE_STATIC_VALIDATE_APPLY_OR_ROLLBACK")
        return 0
    try:
        root = repository_root()
        if args.static_validate:
            entrypoint_hash, sudoers_hash = static_validate(root)
            print(
                "STATIC_VALIDATION_PASS "
                f"adapter_sha256={SOURCE_ADAPTER_SHA256} "
                f"entrypoint_sha256={entrypoint_hash} sudoers_sha256={sudoers_hash}"
            )
            return 0
        if args.apply:
            result = run_apply(root)
            print(f"APPLY_PASS:{result}")
            return 0
        require_root()
        remove_exact_package()
        print("ROLLBACK_PASS:REMOVED_EXACT_PACKAGE")
        return 0
    except DeployError as exc:
        print(f"ACTION_FAIL:{exc.code}", file=sys.stderr)
        return 2
    except Exception:
        print("ACTION_FAIL:UNEXPECTED", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
