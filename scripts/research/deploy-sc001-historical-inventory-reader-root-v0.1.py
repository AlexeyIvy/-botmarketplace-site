#!/usr/bin/env python3
"""Publish the frozen SC001 metadata inventory and add its Reader root safely."""

from __future__ import annotations

import argparse
import grp
import hashlib
import json
import os
import pwd
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NoReturn, Sequence


SOURCE_ROOT = Path("/home/botmarket/sc001_data")
EXPORTER_RELATIVE = Path(
    "scripts/research/export-sc001-data-metadata-inventory-v0.1.py"
)
EXPORTER_SHA256 = "a6806038c986c9f17ba40cfd41cbdafe2ebb04355ae3537aac4437ae1a018f21"
PUBLISHED_DIR = Path(
    "/var/lib/botmarket-research/published/sc001_historical_inventory"
)
INVENTORY_PATH = PUBLISHED_DIR / "inventory-v0.1.json"
READER_CONFIG = Path("/etc/botmarket-research/reader-roots.json")
READER_ROOT_NAME = "sc001_historical_inventory"
READER_SERVICE_USER = "botmarket-mcp"
READER_GROUP = "botmarket-reader"


class DeployError(RuntimeError):
    """Bounded fail-closed deployment error."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _fail(code: str) -> NoReturn:
    raise DeployError(code)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            while block := handle.read(1024 * 1024):
                digest.update(block)
    except OSError:
        _fail("EXPORTER_READ")
    return digest.hexdigest()


def _require_no_symlink_components(path: Path, final_kind: str) -> os.stat_result:
    absolute = Path(os.path.abspath(os.fspath(path)))
    current = Path(absolute.anchor)
    final_metadata: os.stat_result | None = None
    for segment in absolute.parts[1:]:
        current /= segment
        try:
            metadata = current.lstat()
        except OSError:
            _fail("PATH_INSPECTION")
        if stat.S_ISLNK(metadata.st_mode):
            _fail("SYMLINK_PATH")
        final_metadata = metadata

    if final_metadata is None:
        _fail("INVALID_PATH")
    if final_kind == "directory" and not stat.S_ISDIR(final_metadata.st_mode):
        _fail("EXPECTED_DIRECTORY")
    if final_kind == "file" and not stat.S_ISREG(final_metadata.st_mode):
        _fail("EXPECTED_FILE")
    return final_metadata


def _require_existing_ancestors_no_symlink(path: Path) -> None:
    absolute = Path(os.path.abspath(os.fspath(path)))
    current = Path(absolute.anchor)
    for segment in absolute.parts[1:]:
        current /= segment
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            return
        except OSError:
            _fail("PATH_INSPECTION")
        if stat.S_ISLNK(metadata.st_mode):
            _fail("SYMLINK_PATH")
        if current != absolute and not stat.S_ISDIR(metadata.st_mode):
            _fail("EXPECTED_DIRECTORY")


def _load_config(path: Path) -> tuple[dict[str, object], os.stat_result]:
    expected = _require_no_symlink_components(path, "file")
    descriptor = -1
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0),
        )
        metadata = os.fstat(descriptor)
        if (metadata.st_dev, metadata.st_ino) != (expected.st_dev, expected.st_ino):
            _fail("CONFIG_CHANGED")
        with os.fdopen(descriptor, "r", encoding="utf-8", closefd=True) as handle:
            descriptor = -1
            parsed = json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError):
        _fail("CONFIG_READ")
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if not isinstance(parsed, dict):
        _fail("CONFIG_SHAPE")
    if parsed.get("schema_version") != 1:
        _fail("CONFIG_SCHEMA")
    roots = parsed.get("roots")
    if not isinstance(roots, dict):
        _fail("CONFIG_ROOTS")
    return parsed, metadata


def _add_reader_root(config: dict[str, object], published_dir: Path) -> int:
    roots = config.get("roots")
    if not isinstance(roots, dict):
        _fail("CONFIG_ROOTS")
    expected = {"path": str(published_dir), "mode": "read_only"}
    if READER_ROOT_NAME in roots and roots[READER_ROOT_NAME] != expected:
        _fail("ROOT_NAME_CONFLICT")
    roots[READER_ROOT_NAME] = expected
    return len(roots)


def _atomic_write_config(
    path: Path,
    config: dict[str, object],
    metadata: os.stat_result,
) -> None:
    try:
        payload = (
            json.dumps(
                config,
                ensure_ascii=False,
                allow_nan=False,
                indent=2,
                separators=(",", ": "),
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError):
        _fail("CONFIG_SERIALIZE")

    descriptor = -1
    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
        )
        temporary_path = Path(temporary_name)
        current = os.fstat(descriptor)
        if (current.st_uid, current.st_gid) != (metadata.st_uid, metadata.st_gid):
            os.fchown(descriptor, metadata.st_uid, metadata.st_gid)
        os.fchmod(descriptor, stat.S_IMODE(metadata.st_mode))
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            descriptor = -1
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        current = _require_no_symlink_components(path, "file")
        unchanged_fields = (
            current.st_dev == metadata.st_dev,
            current.st_ino == metadata.st_ino,
            current.st_size == metadata.st_size,
            current.st_mtime_ns == metadata.st_mtime_ns,
            current.st_uid == metadata.st_uid,
            current.st_gid == metadata.st_gid,
            stat.S_IMODE(current.st_mode) == stat.S_IMODE(metadata.st_mode),
        )
        if not all(unchanged_fields):
            _fail("CONFIG_CHANGED")
        os.replace(temporary_path, path)
        temporary_path = None
        directory_fd = os.open(
            path.parent,
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_CLOEXEC", 0),
        )
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except OSError:
        _fail("CONFIG_ATOMIC_WRITE")
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except OSError:
                pass


def _resolve_reader_identity() -> tuple[int, int]:
    try:
        account = pwd.getpwnam(READER_SERVICE_USER)
        group = grp.getgrnam(READER_GROUP)
    except KeyError:
        _fail("READER_IDENTITY")
    member = account.pw_gid == group.gr_gid or account.pw_name in group.gr_mem
    if not member:
        _fail("READER_GROUP_MEMBERSHIP")
    return account.pw_uid, group.gr_gid


def _prepare_published_directory(group_id: int) -> None:
    _require_existing_ancestors_no_symlink(PUBLISHED_DIR)
    try:
        PUBLISHED_DIR.mkdir(mode=0o750, parents=True, exist_ok=True)
    except OSError:
        _fail("PUBLISHED_DIR_CREATE")
    metadata = _require_no_symlink_components(PUBLISHED_DIR, "directory")
    try:
        children = list(PUBLISHED_DIR.iterdir())
    except OSError:
        _fail("PUBLISHED_DIR_READ")
    if any(child.name != INVENTORY_PATH.name for child in children):
        _fail("PUBLISHED_DIR_NOT_DEDICATED")
    descriptor = -1
    try:
        descriptor = os.open(
            PUBLISHED_DIR,
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0),
        )
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
            _fail("PUBLISHED_DIR_CHANGED")
        os.fchown(descriptor, 0, group_id)
        os.fchmod(descriptor, 0o750)
    except OSError:
        _fail("PUBLISHED_DIR_PERMISSIONS")
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _run_exporter(exporter: Path) -> int:
    command = [
        sys.executable,
        str(exporter),
        "--root",
        str(SOURCE_ROOT),
        "--output",
        str(INVENTORY_PATH),
    ]
    try:
        completed = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="strict",
            check=False,
            timeout=3600,
        )
    except (OSError, subprocess.SubprocessError, UnicodeError):
        _fail("EXPORTER_EXECUTION")
    if completed.returncode != 0:
        _fail("EXPORTER_FAILED")
    lines = [line for line in completed.stdout.splitlines() if line]
    if len(lines) != 1:
        _fail("EXPORTER_OUTPUT")
    try:
        result = json.loads(lines[0])
    except json.JSONDecodeError:
        _fail("EXPORTER_OUTPUT")
    if not isinstance(result, dict) or result.get("status") != "OK":
        _fail("EXPORTER_OUTPUT")
    entry_count = result.get("entry_count")
    if not isinstance(entry_count, int) or isinstance(entry_count, bool) or entry_count < 0:
        _fail("EXPORTER_OUTPUT")
    return entry_count


def _finalize_inventory(group_id: int) -> None:
    metadata = _require_no_symlink_components(INVENTORY_PATH, "file")
    if metadata.st_nlink != 1:
        _fail("INVENTORY_LINK_COUNT")
    descriptor = -1
    try:
        descriptor = os.open(
            INVENTORY_PATH,
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0),
        )
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
            _fail("INVENTORY_CHANGED")
        os.fchown(descriptor, 0, group_id)
        os.fchmod(descriptor, 0o640)
    except OSError:
        _fail("INVENTORY_PERMISSIONS")
    finally:
        if descriptor >= 0:
            os.close(descriptor)

    try:
        children = list(PUBLISHED_DIR.iterdir())
    except OSError:
        _fail("PUBLISHED_DIR_READ")
    if len(children) != 1 or children[0].name != INVENTORY_PATH.name:
        _fail("PUBLISHED_DIR_NOT_DEDICATED")


def run_apply() -> tuple[int, int]:
    if os.geteuid() != 0:
        _fail("ROOT_REQUIRED")

    repository_root = Path(__file__).resolve(strict=True).parents[2]
    exporter = repository_root / EXPORTER_RELATIVE
    _require_no_symlink_components(exporter, "file")
    if _sha256(exporter) != EXPORTER_SHA256:
        _fail("EXPORTER_SHA256")

    _require_no_symlink_components(SOURCE_ROOT, "directory")
    _, group_id = _resolve_reader_identity()
    config, config_metadata = _load_config(READER_CONFIG)
    _prepare_published_directory(group_id)
    entry_count = _run_exporter(exporter)
    _finalize_inventory(group_id)
    root_count = _add_reader_root(config, PUBLISHED_DIR)
    _atomic_write_config(READER_CONFIG, config, config_metadata)
    return entry_count, root_count


def _self_test_require(condition: bool) -> None:
    if not condition:
        _fail("SELF_TEST_ASSERTION")


def run_self_test() -> None:
    with tempfile.TemporaryDirectory(
        prefix="sc001-reader-inventory-deploy-self-test-"
    ) as temporary:
        base = Path(temporary)
        published = base / "published" / "synthetic_inventory"
        published.mkdir(parents=True, mode=0o750)
        inventory = published / "inventory-v0.1.json"
        inventory.write_text('{"entry_count":2}\n', encoding="utf-8")

        config_path = base / "reader-roots.json"
        original_root = {"path": str(base / "existing"), "mode": "read_only"}
        original = {"schema_version": 1, "roots": {"existing": original_root}}
        config_path.write_text(json.dumps(original) + "\n", encoding="utf-8")
        os.chmod(config_path, 0o640)

        config, metadata = _load_config(config_path)
        original_identity = (metadata.st_uid, metadata.st_gid)
        root_count = _add_reader_root(config, published)
        _atomic_write_config(config_path, config, metadata)

        written, written_metadata = _load_config(config_path)
        roots = written.get("roots")
        _self_test_require(isinstance(roots, dict))
        _self_test_require(root_count == 2)
        _self_test_require(roots.get("existing") == original_root)
        _self_test_require(
            roots.get(READER_ROOT_NAME)
            == {"path": str(published), "mode": "read_only"}
        )
        _self_test_require(stat.S_IMODE(written_metadata.st_mode) == 0o640)
        _self_test_require(
            (written_metadata.st_uid, written_metadata.st_gid) == original_identity
        )
        _self_test_require(inventory.read_text(encoding="utf-8") == '{"entry_count":2}\n')

        conflict = {
            "schema_version": 1,
            "roots": {READER_ROOT_NAME: {"path": "/wrong", "mode": "read_only"}},
        }
        try:
            _add_reader_root(conflict, published)
        except DeployError as exc:
            _self_test_require(exc.code == "ROOT_NAME_CONFLICT")
        else:
            _fail("SELF_TEST_CONFLICT")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install the frozen SC001 metadata inventory Reader root."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--apply", action="store_true", help="perform the fixed root-only host update"
    )
    mode.add_argument(
        "--self-test", action="store_true", help="run only synthetic temporary checks"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.apply and not args.self_test:
        print("NO_ACTION_USE_APPLY_OR_SELF_TEST")
        return 0

    try:
        if args.self_test:
            run_self_test()
            print("SELF_TEST_PASS")
            return 0
        entry_count, root_count = run_apply()
    except DeployError as exc:
        prefix = "SELF_TEST_FAIL" if args.self_test else "APPLY_FAIL"
        print(f"{prefix}:{exc.code}", file=sys.stderr)
        return 2
    except Exception:
        prefix = "SELF_TEST_FAIL" if args.self_test else "APPLY_FAIL"
        print(f"{prefix}:UNEXPECTED", file=sys.stderr)
        return 2

    print(f"APPLY_PASS entry_count={entry_count} root_count={root_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
