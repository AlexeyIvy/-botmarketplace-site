#!/usr/bin/env python3
"""Offline synthetic tests for the SC001-X1-002C capture preparation."""

from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
import urllib.request
from email.message import Message
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
import sys

sys.path.insert(0, str(ROOT / "scripts" / "research"))

import sc001_x1_pit_lineage_capture_v0_1 as capture  # noqa: E402
import sc001_x1_pit_universe_metadata_resolver_v0_1 as resolver  # noqa: E402


ARTICLE_A = "a" * 32
ARTICLE_B = "b" * 32


def index_body(total: int, rows: list[tuple[str, str, int]]) -> bytes:
    return json.dumps(
        {
            "code": "000000",
            "success": True,
            "data": {
                "total": total,
                "catalogs": [
                    {
                        "articles": [
                            {"code": article_id, "title": title, "releaseDate": release_ms}
                            for article_id, title, release_ms in rows
                        ],
                    }
                ]
            },
        },
        separators=(",", ":"),
    ).encode("utf-8")


class FakeResponse(io.BytesIO):
    def __init__(self, raw: bytes, url: str, status: int = 200, content_type: str = "application/json") -> None:
        super().__init__(raw)
        self._url = url
        self._status = status
        self.headers = Message()
        self.headers["Content-Type"] = content_type
        self.headers["Content-Length"] = str(len(raw))
        self.headers["ETag"] = '"synthetic"'

    def geturl(self) -> str:
        return self._url

    def getcode(self) -> int:
        return self._status


class FakeOpener:
    def __init__(self, payloads: dict[str, bytes]) -> None:
        self.payloads = {capture.canonical_url(key): value for key, value in payloads.items()}
        self.calls: list[str] = []

    def open(self, request: urllib.request.Request, timeout: int) -> FakeResponse:
        del timeout
        url = capture.canonical_url(request.full_url)
        self.calls.append(url)
        if url not in self.payloads:
            raise AssertionError(f"unexpected synthetic request: {url}")
        content_type = "application/json" if self.payloads[url].startswith(b"{") else "text/html"
        return FakeResponse(self.payloads[url], url, content_type=content_type)


class CaptureContractTests(unittest.TestCase):
    def test_url_allowlisting_and_canonicalization(self) -> None:
        url = capture.index_url(48, 2)
        validated = capture.canonical_url(url)
        self.assertEqual(capture.classify_url(validated), "announcement_index")
        self.assertIn("catalogId=48", validated)
        with self.assertRaises(capture.SourceIncomplete):
            capture.classify_url(url.replace("www.binance.com", "evil.example"))
        with self.assertRaises(capture.SourceIncomplete):
            capture.classify_url(capture.EXCHANGE_INFO_URL + "?symbol=BTCUSDT")
        with self.assertRaises(capture.SourceIncomplete):
            capture.classify_url("https://www.binance.com/en/support/announcement/detail/not-an-id")

    def test_redirect_rejects_host_change_and_downgrade(self) -> None:
        handler = capture.StrictRedirectHandler()
        request = urllib.request.Request(capture.EXCHANGE_INFO_URL)
        headers = Message()
        with self.assertRaises(capture.SourceIncomplete):
            handler.redirect_request(request, io.BytesIO(), 302, "Found", headers, "https://www.binance.com/elsewhere")
        with self.assertRaises(capture.SourceIncomplete):
            handler.redirect_request(request, io.BytesIO(), 302, "Found", headers, "http://fapi.binance.com/elsewhere")

    def test_pagination_parser_and_unknown_schema_fail_closed(self) -> None:
        raw = index_body(2, [(ARTICLE_A, "Listing A", 1), (ARTICLE_B, "Delisting B", 2)])
        total, articles = capture.extract_index_page(raw, 48)
        rows = capture.normalize_articles(48, articles)
        self.assertEqual(total, 2)
        self.assertEqual([item["detail_id"] for item in rows], [ARTICLE_A, ARTICLE_B])
        with self.assertRaises(capture.SourceIncomplete):
            capture.extract_index_page(b'{"code":"000000","success":true,"data":{"articles":[]}}', 48)
        with self.assertRaises(capture.SourceIncomplete):
            _, invalid = capture.extract_index_page(index_body(1, [("not-a-code", "X", 1)]), 48)
            capture.normalize_articles(48, invalid)

    def test_detail_id_deduplication_and_conflict(self) -> None:
        first = capture.normalize_articles(48, [{"code": ARTICLE_A, "title": "A", "releaseDate": 1}])[0]
        second = capture.normalize_articles(161, [{"code": ARTICLE_A, "title": "A", "releaseDate": 1}])[0]
        self.assertEqual(first["detail_id"], second["detail_id"])
        self.assertNotEqual(first["category_id"], second["category_id"])

    def test_request_and_byte_budgets(self) -> None:
        budget = capture.Budget.empty()
        budget.reserve_request("exchange_info")
        with self.assertRaises(capture.SourceIncomplete):
            budget.reserve_request("exchange_info")
        budget.add_bytes("exchange_info", 8_388_608)
        with self.assertRaises(capture.SourceIncomplete):
            budget.add_bytes("exchange_info", 1)
        with self.assertRaises(capture.SourceIncomplete):
            capture.bounded_read(io.BytesIO(b"12345"), 4, "5")
        self.assertEqual(capture.bounded_read(io.BytesIO(b"1234"), 4, "4"), b"1234")

    def test_response_hash_and_manifest_ordering(self) -> None:
        raw = b"synthetic-response"
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            "59625192f77f79e2b26a5b966ffda6b825fc59cc6bd465b634903ee46b41074e",
        )
        responses = [{"sequence": 1}, {"sequence": 2}]
        self.assertEqual([item["sequence"] for item in responses], list(range(1, len(responses) + 1)))

    def test_full_synthetic_capture_is_deterministically_bounded(self) -> None:
        index_48 = capture.index_url(48, 1)
        index_161 = capture.index_url(161, 1)
        detail_a = capture.DETAIL_PREFIX + ARTICLE_A
        detail_b = capture.DETAIL_PREFIX + ARTICLE_B
        payloads = {
            capture.EXCHANGE_INFO_URL: b'{"timezone":"UTC","symbols":[]}',
            index_48: index_body(1, [(ARTICLE_A, "Listing A", 1)]),
            index_161: index_body(2, [(ARTICLE_A, "Listing A", 1), (ARTICLE_B, "Delisting B", 2)]),
            detail_a: b"<html>A</html>",
            detail_b: b"<html>B</html>",
            capture.DOC_URLS[0]: b"<html>exchange schema</html>",
            capture.DOC_URLS[1]: b"<html>contract schema</html>",
        }
        opener = FakeOpener(payloads)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "capture"
            capture.prepare_output_dir(output)
            manifest, ledger = capture.run_capture(output, opener=opener)
            self.assertEqual(manifest["status"], "CAPTURE_COMPLETE_SOURCE_QUALIFICATION_PENDING")
            self.assertEqual(len(ledger["announcement_candidates"]), 2)
            self.assertEqual(manifest["budget"]["requests_total"], 7)
            disk_manifest = json.loads((output / "capture-manifest.json").read_text(encoding="utf-8"))
            disk_ledger = json.loads((output / "candidate-ledger.json").read_text(encoding="utf-8"))
            self.assertFalse(disk_manifest["completeness_attestation_emitted"])
            self.assertEqual(disk_ledger["completeness_attestation"], "NOT_ATTESTED_SOURCE_CAPTURE_ONLY")
            self.assertEqual(
                [item["sequence"] for item in manifest["response_order"]],
                list(range(1, 8)),
            )
            self.assertEqual(
                [item["detail_id"] for item in ledger["announcement_candidates"]],
                [ARTICLE_A, ARTICLE_B],
            )

    def test_unknown_pagination_shape_writes_source_incomplete(self) -> None:
        payloads = {
            capture.EXCHANGE_INFO_URL: b'{"timezone":"UTC","symbols":[]}',
            capture.index_url(48, 1): b'{"code":"000000","success":true,"data":{"catalogs":[]}}',
        }
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "capture"
            capture.prepare_output_dir(output)
            manifest, _ = capture.run_capture(output, opener=FakeOpener(payloads))
            self.assertEqual(manifest["status"], "SOURCE_INCOMPLETE")
            self.assertIn("SCHEMA", manifest["failure"])

    def test_candidate_ledger_cannot_bypass_offline_resolver_gate(self) -> None:
        payload = {
            "schema": capture.CANDIDATE_SCHEMA,
            "cutoff_exclusive_utc": capture.CUTOFF,
            "completeness_attestation": "NOT_ATTESTED_SOURCE_CAPTURE_ONLY",
            "records": [],
        }
        with self.assertRaisesRegex(resolver.LedgerError, "SOURCE_STRATEGY_ATTENTION_REQUIRED"):
            resolver.validate_ledger(payload)


if __name__ == "__main__":
    unittest.main(verbosity=2)
