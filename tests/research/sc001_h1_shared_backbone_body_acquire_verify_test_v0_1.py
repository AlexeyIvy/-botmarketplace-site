from __future__ import annotations

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts/research/sc001_h1_shared_backbone_body_acquire_verify_v0_1.py"
FREEZE_PATH = REPO_ROOT / "docs/research/sc001-h1-shared-backbone-bodyset-freeze-v0.1.json"

SPEC = importlib.util.spec_from_file_location("h1_bodyset", MODULE_PATH)
assert SPEC and SPEC.loader
h1 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(h1)


class FrozenManifestTests(unittest.TestCase):
    def test_exact_cardinality_order_and_source_identities(self) -> None:
        freeze = h1.load_and_validate_freeze(FREEZE_PATH)
        manifest = freeze["ordered_archive_manifest"]
        self.assertEqual(156, len(manifest))
        self.assertEqual(156, freeze["cardinality"]["zip_archives"])
        self.assertEqual(156, freeze["cardinality"]["checksum_sidecars"])
        self.assertEqual(list(range(1, 157)), [item["ordinal"] for item in manifest])
        expected_pairs = [
            (symbol, month)
            for symbol in h1.EXPECTED_SYMBOLS
            for month in h1.EXPECTED_MONTHS
        ]
        self.assertEqual(expected_pairs, [(item["symbol"], item["month_utc"]) for item in manifest])
        for item in manifest:
            self.assertTrue(item["archive"]["url"].startswith(h1.PUBLIC_PREFIX))
            self.assertEqual(item["archive"]["url"] + ".CHECKSUM", item["checksum_sidecar"]["url"])
            archive_name = Path(item["archive"]["relative_identity"]).name
            sidecar_name = Path(item["checksum_sidecar"]["relative_identity"]).name
            self.assertEqual(
                h1.cache_relative_path(archive_name).as_posix(),
                item["archive"]["cache_relative_path"],
            )
            self.assertEqual(
                h1.cache_relative_path(sidecar_name).as_posix(),
                item["checksum_sidecar"]["cache_relative_path"],
            )

    def test_canonical_dataset_key_and_resource_id_fixture(self) -> None:
        freeze = h1.load_and_validate_freeze(FREEZE_PATH)
        canonical = json.dumps(
            freeze["dataset_key"],
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        expected_resource_id = hashlib.sha256(canonical).hexdigest()
        self.assertEqual(canonical, h1.canonical_dataset_key_bytes(h1.DATASET_KEY))
        self.assertEqual(expected_resource_id, h1.RESOURCE_ID)
        self.assertEqual(expected_resource_id, freeze["resource_id"])
        self.assertEqual(64, len(expected_resource_id))

    def test_shared_cache_path_is_resource_bound_and_task_independent(self) -> None:
        first_task_path = h1.cache_relative_path("X.zip")
        second_task_path = h1.cache_relative_path("X.zip")
        self.assertEqual(first_task_path, second_task_path)
        self.assertEqual(
            Path("_raw_cache") / "binance" / h1.RESOURCE_ID / "X.zip",
            first_task_path,
        )
        self.assertNotIn("SC001-H1", first_task_path.as_posix())

    def test_checksum_parser_accepts_only_frozen_filename(self) -> None:
        digest = "a" * 64
        self.assertEqual(
            digest,
            h1.parse_checksum_sidecar(f"{digest}  X.zip\n", "X.zip"),
        )
        with self.assertRaises(h1.ContractError):
            h1.parse_checksum_sidecar(f"{digest}  Y.zip\n", "X.zip")
        with self.assertRaises(h1.ContractError):
            h1.parse_checksum_sidecar("not-a-digest X.zip\n", "X.zip")


class IntegrityTests(unittest.TestCase):
    @staticmethod
    def valid_row() -> list[str]:
        return [
            "0", "1.0", "3.0", "0.5", "2.0", "10.0",
            "59999", "20.0", "4", "5.0", "10.0", "0",
        ]

    def test_positive_ohlcv_close_time_row_passes(self) -> None:
        self.assertEqual(0, h1.validate_kline_row(self.valid_row(), "ROW", 1))

    def test_zero_negative_and_nonfinite_ohlc_rejected(self) -> None:
        cases = ((1, "0"), (4, "-1"), (2, "nan"))
        for index, value in cases:
            with self.subTest(index=index, value=value):
                row = self.valid_row()
                row[index] = value
                with self.assertRaises(h1.IntegrityFailure):
                    h1.validate_kline_row(row, "ROW", 1)

    def test_high_low_inconsistency_rejected(self) -> None:
        row = self.valid_row()
        row[2] = "0.75"
        with self.assertRaises(h1.IntegrityFailure) as caught:
            h1.validate_kline_row(row, "ROW", 1)
        self.assertEqual("OHLC_RELATION_INVALID", caught.exception.report["code"])

    def test_negative_volume_and_invalid_trade_count_rejected(self) -> None:
        row = self.valid_row()
        row[5] = "-0.1"
        with self.assertRaises(h1.IntegrityFailure) as caught:
            h1.validate_kline_row(row, "ROW", 1)
        self.assertEqual("NEGATIVE_VOLUME", caught.exception.report["code"])

        row = self.valid_row()
        row[8] = "1.5"
        with self.assertRaises(h1.IntegrityFailure) as caught:
            h1.validate_kline_row(row, "ROW", 1)
        self.assertEqual("INTEGER_FIELD_INVALID", caught.exception.report["code"])

        row = self.valid_row()
        row[8] = "-1"
        with self.assertRaises(h1.IntegrityFailure) as caught:
            h1.validate_kline_row(row, "ROW", 1)
        self.assertEqual("NEGATIVE_TRADE_COUNT", caught.exception.report["code"])

    def test_close_time_mismatch_rejected(self) -> None:
        row = self.valid_row()
        row[6] = "60000"
        with self.assertRaises(h1.IntegrityFailure) as caught:
            h1.validate_kline_row(row, "ROW", 1)
        self.assertEqual("CLOSE_TIME_MISMATCH", caught.exception.report["code"])

    def test_duplicate_detected_with_exact_archive_and_day(self) -> None:
        with self.assertRaises(h1.IntegrityFailure) as caught:
            h1.validate_timestamp_sequence(
                [0, 60_000, 60_000], 0, 180_000, "A"
            )
        self.assertEqual("A", caught.exception.report["archive_id"])
        self.assertEqual("DUPLICATE_OPEN_TIME", caught.exception.report["code"])
        self.assertEqual("1970-01-01", caught.exception.report["day_utc"])

    def test_gap_detected(self) -> None:
        with self.assertRaises(h1.IntegrityFailure) as caught:
            h1.validate_timestamp_sequence(
                [0, 120_000], 0, 180_000, "B"
            )
        self.assertEqual("ONE_MINUTE_GAP", caught.exception.report["code"])

    def test_incomplete_day_count_fails_closed(self) -> None:
        times = [index * 60_000 for index in range(1439)]
        with self.assertRaises(h1.IntegrityFailure) as caught:
            h1.validate_timestamp_sequence(times, 0, 86_400_000, "C")
        self.assertEqual("MONTH_ROW_COUNT_MISMATCH", caught.exception.report["code"])

    def test_complete_utc_day_passes(self) -> None:
        times = [index * 60_000 for index in range(1440)]
        self.assertEqual(
            1440,
            h1.validate_timestamp_sequence(times, 0, 86_400_000, "D"),
        )

    def test_zip_slip_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unsafe.zip"
            with zipfile.ZipFile(path, "w") as zf:
                zf.writestr("../escape.csv", "0," + ",".join(["1"] * 11))
            entry = {
                "archive_id": "SAFE",
                "csv_member": "SAFE.csv",
                "month_utc": "2025-09",
            }
            with self.assertRaises(h1.IntegrityFailure) as caught:
                h1.validate_zip_body(path, entry)
            self.assertEqual(
                "ZIP_MEMBER_IDENTITY_OR_PATH_UNSAFE",
                caught.exception.report["code"],
            )


class ResumeAndBudgetTests(unittest.TestCase):
    def test_resume_requires_exact_partial_response(self) -> None:
        self.assertEqual("wb", h1.validate_resume_response(0, 200, None))
        self.assertEqual(
            "wb",
            h1.validate_resume_response(0, 206, "bytes 0-19/20"),
        )
        with self.assertRaises(h1.ContractError):
            h1.validate_resume_response(0, 206, "bytes 10-19/20")
        with self.assertRaises(h1.ContractError):
            h1.validate_resume_response(0, 206, None)
        with self.assertRaises(h1.ContractError):
            h1.validate_resume_response(0, 206, "bytes 0-garbage/20")
        self.assertEqual(
            "ab",
            h1.validate_resume_response(10, 206, "bytes 10-19/20"),
        )
        with self.assertRaises(h1.ContractError):
            h1.validate_resume_response(10, 200, None)
        with self.assertRaises(h1.ContractError):
            h1.validate_resume_response(10, 206, "bytes 9-19/20")

    def test_request_budget_fails_before_overrun(self) -> None:
        budget = h1.Budget(1, 5)
        budget.consume_request()
        with self.assertRaises(h1.BudgetExceeded):
            budget.consume_request()
        budget.consume_bytes(5)
        with self.assertRaises(h1.BudgetExceeded):
            budget.consume_bytes(1)
        self.assertEqual(1, budget.requests)
        self.assertEqual(5, budget.bytes)

    def test_checksum_mismatch_quarantines_candidate_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / "X.zip.part"
            candidate.write_bytes(b"wrong")
            destination = h1.quarantine(
                candidate,
                root,
                {
                    "archive_id": "X",
                    "code": "SHA256_MISMATCH",
                    "expected": hashlib.sha256(b"right").hexdigest(),
                    "actual": hashlib.sha256(b"wrong").hexdigest(),
                },
            )
            self.assertFalse(candidate.exists())
            self.assertTrue(destination.exists())
            reason = json.loads(
                destination.with_name(destination.name + ".reason.json").read_text()
            )
            self.assertEqual("SHA256_MISMATCH", reason["code"])


if __name__ == "__main__":
    unittest.main()
