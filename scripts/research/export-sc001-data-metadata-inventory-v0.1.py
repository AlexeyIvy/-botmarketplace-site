#!/usr/bin/env python3
"""Export a deterministic, metadata-only inventory for an explicit directory."""

from __future__ import annotations

import argparse
import json
import os
import stat
import tempfile
from pathlib import Path, PurePosixPath
from typing import Sequence

SCHEMA = "sc001.legacy_metadata_inventory.v0.1"
ENTRY_FIELDS = {
    "logical_path",
    "basename",
    "kind",
    "size_bytes",
    "suffix",
}
SUMMARY_FIELDS = {
    "schema",
    "root_label",
    "entry_count",
    "file_count",
    "directory_count",
    "symlink_count",
    "other_count",
    "total_file_bytes",
    "entries",
}


class InventoryError(RuntimeError):
    """Fail-closed inventory error."""


def _utf8_key(value: str) -> bytes:
    try:
        return value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise InventoryError("a path is not valid strict UTF-8") from exc


def _directory_open_flags() -> int:
    required = ("O_DIRECTORY", "O_NOFOLLOW")
    missing = [name for name in required if not hasattr(os, name)]
    if missing:
        raise InventoryError(
            "safe directory traversal is unavailable: missing " + ", ".join(missing)
        )
    return (
        os.O_RDONLY
        | os.O_DIRECTORY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )


def _normalize_root(root_arg: str) -> Path:
    if not root_arg:
        raise InventoryError("--root must name an existing directory")

    lexical = Path(os.path.abspath(os.fspath(root_arg)))
    try:
        resolved = lexical.resolve(strict=True)
        metadata = lexical.lstat()
    except OSError as exc:
        raise InventoryError(f"cannot resolve root: {exc}") from exc

    if lexical != resolved:
        raise InventoryError("root path must not contain or be a symbolic link")
    if stat.S_ISLNK(metadata.st_mode):
        raise InventoryError("root must not be a symbolic link")
    if not stat.S_ISDIR(metadata.st_mode):
        raise InventoryError("root is not a directory")
    if not resolved.name:
        raise InventoryError("filesystem root is not an allowed inventory root")
    return resolved


def _normalize_output(output_arg: str, root: Path) -> Path:
    if not output_arg:
        raise InventoryError("--output must name a JSON file")

    lexical = Path(os.path.abspath(os.fspath(output_arg)))
    if not lexical.name:
        raise InventoryError("--output must name a file")

    try:
        lexical.parent.mkdir(parents=True, exist_ok=True)
        parent = lexical.parent.resolve(strict=True)
    except OSError as exc:
        raise InventoryError(f"cannot create or resolve output parent: {exc}") from exc

    if Path(os.path.abspath(os.fspath(lexical.parent))) != parent:
        raise InventoryError("output parent path must not contain a symbolic link")

    output = parent / lexical.name
    try:
        output.relative_to(root)
    except ValueError:
        pass
    else:
        raise InventoryError("output must be outside the inventory root")

    if os.path.lexists(output):
        try:
            metadata = output.lstat()
        except OSError as exc:
            raise InventoryError(f"cannot inspect existing output: {exc}") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise InventoryError("output must not be a symbolic link")
        if not stat.S_ISREG(metadata.st_mode):
            raise InventoryError("existing output is not a regular file")

    return output


def _kind(mode: int) -> str:
    if stat.S_ISREG(mode):
        return "file"
    if stat.S_ISDIR(mode):
        return "directory"
    if stat.S_ISLNK(mode):
        return "symlink"
    return "other"


def _scan_directory(
    directory_fd: int,
    segments: tuple[str, ...],
    seen_directories: set[tuple[int, int]],
    entries: list[dict[str, object]],
) -> None:
    try:
        with os.scandir(directory_fd) as iterator:
            children = list(iterator)
    except OSError as exc:
        logical = "/".join(segments) or "."
        raise InventoryError(f"cannot read directory {logical!r}: {exc}") from exc

    children.sort(key=lambda child: _utf8_key(child.name))

    for child in children:
        name = child.name
        _utf8_key(name)
        logical_path = "/".join((*segments, name))

        try:
            metadata = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        except OSError as exc:
            raise InventoryError(
                f"cannot inspect entry {logical_path!r}: {exc}"
            ) from exc

        kind = _kind(metadata.st_mode)
        entry = {
            "logical_path": logical_path,
            "basename": name,
            "kind": kind,
            "size_bytes": metadata.st_size if kind == "file" else None,
            "suffix": PurePosixPath(name).suffix,
        }
        if set(entry) != ENTRY_FIELDS:
            raise InventoryError("internal entry schema violation")
        entries.append(entry)

        if kind != "directory":
            continue

        flags = _directory_open_flags()
        try:
            child_fd = os.open(name, flags, dir_fd=directory_fd)
        except OSError as exc:
            raise InventoryError(
                f"cannot safely open directory {logical_path!r}: {exc}"
            ) from exc

        try:
            opened = os.fstat(child_fd)
            if not stat.S_ISDIR(opened.st_mode):
                raise InventoryError(
                    f"directory changed type during traversal: {logical_path!r}"
                )
            if (opened.st_dev, opened.st_ino) != (
                metadata.st_dev,
                metadata.st_ino,
            ):
                raise InventoryError(
                    f"directory changed identity during traversal: {logical_path!r}"
                )

            identity = (opened.st_dev, opened.st_ino)
            if identity in seen_directories:
                raise InventoryError(
                    f"directory cycle or duplicate identity: {logical_path!r}"
                )
            seen_directories.add(identity)
            _scan_directory(
                child_fd,
                (*segments, name),
                seen_directories,
                entries,
            )
        finally:
            os.close(child_fd)


def build_inventory(root: Path) -> dict[str, object]:
    flags = _directory_open_flags()
    try:
        root_fd = os.open(root, flags)
    except OSError as exc:
        raise InventoryError(f"cannot safely open root: {exc}") from exc

    try:
        root_metadata = os.fstat(root_fd)
        if not stat.S_ISDIR(root_metadata.st_mode):
            raise InventoryError("root changed type during traversal")

        entries: list[dict[str, object]] = []
        seen_directories = {(root_metadata.st_dev, root_metadata.st_ino)}
        _scan_directory(root_fd, (), seen_directories, entries)
    finally:
        os.close(root_fd)

    entries.sort(key=lambda entry: _utf8_key(str(entry["logical_path"])))

    counts = {
        "file": 0,
        "directory": 0,
        "symlink": 0,
        "other": 0,
    }
    total_file_bytes = 0
    for entry in entries:
        kind = str(entry["kind"])
        counts[kind] += 1
        if kind == "file":
            total_file_bytes += int(entry["size_bytes"])

    inventory = {
        "schema": SCHEMA,
        "root_label": root.name,
        "entry_count": len(entries),
        "file_count": counts["file"],
        "directory_count": counts["directory"],
        "symlink_count": counts["symlink"],
        "other_count": counts["other"],
        "total_file_bytes": total_file_bytes,
        "entries": entries,
    }
    if set(inventory) != SUMMARY_FIELDS:
        raise InventoryError("internal summary schema violation")
    return inventory


def _write_atomic(output: Path, inventory: dict[str, object]) -> None:
    payload = (
        json.dumps(
            inventory,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            separators=(",", ": "),
        )
        + "\n"
    ).encode("utf-8")

    temporary_path: Path | None = None
    descriptor = -1
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{output.name}.",
            suffix=".tmp",
            dir=output.parent,
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            descriptor = -1
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(temporary_path, output)
        temporary_path = None

        parent_fd = os.open(output.parent, _directory_open_flags())
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    except OSError as exc:
        raise InventoryError(f"atomic output write failed: {exc}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise InventoryError("self-test failed: " + message)


def run_self_test() -> None:
    with tempfile.TemporaryDirectory(
        prefix="sc001-metadata-inventory-self-test-"
    ) as temporary:
        base = Path(temporary)
        root = base / "synthetic-root"
        outside = base / "outside"
        output = base / "published" / "inventory-v0.1.json"

        root.mkdir()
        outside.mkdir()
        (root / "a-dir").mkdir()
        (root / ".hidden").write_bytes(b"xyz")
        (root / "a-dir" / "child.txt").write_bytes(b"hello")
        (root / "z.bin").write_bytes(b"\x00\xffAB")
        (outside / "must-not-appear.dat").write_bytes(b"secret")
        os.symlink(outside, root / "m-link", target_is_directory=True)

        output.parent.mkdir(parents=True)
        output.write_text("stale\n", encoding="utf-8")

        safe_root = _normalize_root(str(root))
        safe_output = _normalize_output(str(output), safe_root)
        first = build_inventory(safe_root)
        _write_atomic(safe_output, first)

        parsed = json.loads(safe_output.read_text(encoding="utf-8"))
        _require(parsed == first, "atomic JSON readback differs")
        _require(set(first) == SUMMARY_FIELDS, "summary fields are not exact")

        entries = list(first["entries"])
        _require(
            all(set(entry) == ENTRY_FIELDS for entry in entries),
            "entry fields are not exact",
        )

        logical_paths = [str(entry["logical_path"]) for entry in entries]
        _require(
            logical_paths == sorted(logical_paths, key=_utf8_key),
            "entry ordering is not UTF-8 bytewise",
        )
        _require(".hidden" in logical_paths, "hidden entry was omitted")
        _require("m-link" in logical_paths, "symlink entry was omitted")
        _require(
            not any(path.startswith("m-link/") for path in logical_paths),
            "symlink target was traversed",
        )
        _require(
            int(first["total_file_bytes"]) == 3 + 5 + 4,
            "file byte accounting is incorrect",
        )

        (root / "z.bin").write_bytes(b"\x99\x88CD")
        second = build_inventory(safe_root)
        _require(
            second == first,
            "same-size content change altered metadata inventory",
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Write a deterministic metadata-only directory inventory. "
            "File bodies are never opened or parsed."
        )
    )
    parser.add_argument("--root", help="existing directory to inventory")
    parser.add_argument("--output", help="JSON output path outside the root")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run only the built-in synthetic self-test",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    if args.self_test:
        if args.root is not None or args.output is not None:
            parser.error("--self-test cannot be combined with --root or --output")
        try:
            run_self_test()
        except (InventoryError, OSError) as exc:
            parser.exit(2, f"SELF_TEST_FAIL: {exc}\n")
        print("SELF_TEST_PASS")
        return 0

    if args.root is None or args.output is None:
        parser.error("--root and --output are required unless --self-test is used")

    try:
        root = _normalize_root(args.root)
        output = _normalize_output(args.output, root)
        inventory = build_inventory(root)
        _write_atomic(output, inventory)
    except (InventoryError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")

    print(
        json.dumps(
            {
                "status": "OK",
                "schema": SCHEMA,
                "entry_count": inventory["entry_count"],
            },
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
