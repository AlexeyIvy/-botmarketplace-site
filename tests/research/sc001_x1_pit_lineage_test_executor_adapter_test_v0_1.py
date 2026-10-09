#!/usr/bin/env python3
"""Synthetic tests for the SC001 X1 Test Executor output adapter."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "research"))

import sc001_x1_pit_lineage_test_executor_adapter_v0_1 as adapter  # noqa: E402


class TestExecutorOutputAdapterTests(unittest.TestCase):
    def test_missing_output_root_fails_closed_without_delegation(self) -> None:
        with (
            patch.dict(os.environ, {}, clear=True),
            patch.object(adapter.capture, "main") as delegated,
        ):
            self.assertEqual(adapter.main([]), 2)
            delegated.assert_not_called()

    def test_empty_output_root_fails_closed_without_delegation(self) -> None:
        with (
            patch.dict(os.environ, {"BM_TEST_OUTPUT_DIR": ""}, clear=True),
            patch.object(adapter.capture, "main") as delegated,
        ):
            self.assertEqual(adapter.main([]), 2)
            delegated.assert_not_called()

    def test_relative_output_root_fails_closed_without_delegation(self) -> None:
        with (
            patch.dict(os.environ, {"BM_TEST_OUTPUT_DIR": "relative/output"}, clear=True),
            patch.object(adapter.capture, "main") as delegated,
        ):
            self.assertEqual(adapter.main([]), 2)
            delegated.assert_not_called()

    def test_nonexistent_output_root_fails_closed_without_delegation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            nonexistent = Path(temporary) / "absent"
            with (
                patch.dict(
                    os.environ,
                    {"BM_TEST_OUTPUT_DIR": str(nonexistent)},
                    clear=True,
                ),
                patch.object(adapter.capture, "main") as delegated,
            ):
                self.assertEqual(adapter.main([]), 2)
                delegated.assert_not_called()

    def test_unexpected_cli_argument_fails_closed_without_delegation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with (
                patch.dict(
                    os.environ,
                    {"BM_TEST_OUTPUT_DIR": temporary},
                    clear=True,
                ),
                patch.object(adapter.capture, "main") as delegated,
            ):
                self.assertEqual(adapter.main(["unexpected"]), 2)
                delegated.assert_not_called()

    def test_valid_output_root_delegates_once_to_exact_fixed_child(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            expected = str(
                Path(temporary).resolve() / "sc001-x1-pit-metadata-capture"
            )
            with (
                patch.dict(
                    os.environ,
                    {"BM_TEST_OUTPUT_DIR": temporary},
                    clear=True,
                ),
                patch.object(adapter.capture, "main", return_value=0) as delegated,
            ):
                self.assertEqual(adapter.main([]), 0)
                delegated.assert_called_once_with(["--output-dir", expected])

    def test_delegated_success_and_source_incomplete_codes_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            expected_args = [
                "--output-dir",
                str(
                    Path(temporary).resolve()
                    / "sc001-x1-pit-metadata-capture"
                ),
            ]
            for exit_code in (0, 2):
                with self.subTest(exit_code=exit_code):
                    with (
                        patch.dict(
                            os.environ,
                            {"BM_TEST_OUTPUT_DIR": temporary},
                            clear=True,
                        ),
                        patch.object(
                            adapter.capture,
                            "main",
                            return_value=exit_code,
                        ) as delegated,
                    ):
                        self.assertEqual(adapter.main([]), exit_code)
                        delegated.assert_called_once_with(expected_args)


if __name__ == "__main__":
    unittest.main(verbosity=2)
