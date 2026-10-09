#!/usr/bin/env python3
"""Fail-closed Test Executor adapter for the frozen SC001 X1 PIT capture."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Sequence

import sc001_x1_pit_lineage_capture_v0_1 as capture


_ENV_KEY = "BM_TEST_OUTPUT_DIR"
_CHILD_NAME = "sc001-x1-pit-metadata-capture"
_FAILURE_EXIT_CODE = 2


class AdapterError(Exception):
    """The executor-owned output path is not safe for delegation."""


def _delegated_arguments(argv: Sequence[str]) -> list[str]:
    if argv:
        raise AdapterError("CLI_ARGUMENTS_FORBIDDEN")

    raw_root = os.environ.get(_ENV_KEY)
    if raw_root is None:
        raise AdapterError("BM_TEST_OUTPUT_DIR_MISSING")
    if not raw_root:
        raise AdapterError("BM_TEST_OUTPUT_DIR_EMPTY")

    supplied_root = Path(raw_root)
    if not supplied_root.is_absolute():
        raise AdapterError("BM_TEST_OUTPUT_DIR_NOT_ABSOLUTE")

    try:
        resolved_root = supplied_root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise AdapterError("BM_TEST_OUTPUT_DIR_CANNOT_RESOLVE") from exc

    if not resolved_root.is_dir():
        raise AdapterError("BM_TEST_OUTPUT_DIR_NOT_DIRECTORY")

    try:
        resolved_child = (resolved_root / _CHILD_NAME).resolve(strict=False)
        resolved_child.relative_to(resolved_root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise AdapterError("OUTPUT_CHILD_ESCAPES_ROOT_OR_CANNOT_RESOLVE") from exc

    return ["--output-dir", str(resolved_child)]


def main(argv: Sequence[str] | None = None) -> int:
    effective_argv = sys.argv[1:] if argv is None else argv
    try:
        delegated_argv = _delegated_arguments(effective_argv)
    except AdapterError as exc:
        print(f"OUTPUT_ADAPTER_ERROR: {exc}", file=sys.stderr)
        return _FAILURE_EXIT_CODE
    return capture.main(delegated_argv)


if __name__ == "__main__":
    raise SystemExit(main())
