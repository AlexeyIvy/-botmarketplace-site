#!/usr/bin/env python3
"""Bounded, fail-closed one-shot capture for the SC001 X1 PIT lineage attempt.

This program is standard-library only.  It captures official Binance metadata
responses and produces an evidence manifest plus a deliberately unattested
candidate ledger for the offline PIT resolver.  It never requests market
prices, trades, klines, funding, open interest, or websocket data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


TOOL_SCHEMA = "sc001.x1_pit_lineage_capture.v0.1"
MANIFEST_SCHEMA = "sc001.x1_pit_lineage_capture_manifest.v0.1"
CANDIDATE_SCHEMA = "sc001.x1_pit_universe_metadata_ledger.v0.1"
CUTOFF = "2026-10-01T00:00:00Z"
USER_AGENT = "BotMarketplace-SC001-X1-PIT-Lineage-Capture/0.1"

EXCHANGE_INFO_URL = "https://fapi.binance.com/fapi/v1/exchangeInfo"
CATEGORIES = (48, 161)
PAGE_SIZE = 20
MAX_PAGES_PER_CATEGORY = 64
INDEX_URL = (
    "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
    "?{query}"
)
DETAIL_PREFIX = "https://www.binance.com/en/support/announcement/detail/"
DOC_URLS = (
    "https://developers.binance.com/docs/derivatives/usds-margined-futures/"
    "market-data/rest-api/Exchange-Information",
    "https://developers.binance.com/docs/derivatives/usds-margined-futures/"
    "websocket-market-streams/Contract-Info-Stream",
)

CLASS_LIMITS = {
    "exchange_info": (1, 8_388_608),
    "announcement_index": (128, 16_777_216),
    "announcement_detail": (1_024, 134_217_728),
    "definition_page": (2, 2_097_152),
}
TOTAL_REQUEST_CAP = 1_155
TOTAL_BYTE_CAP = 161_480_704
ALLOWED_HOSTS = frozenset({"fapi.binance.com", "www.binance.com", "developers.binance.com"})
DETAIL_ID_RE = re.compile(r"^[0-9a-f]{32}$")


class SourceIncomplete(RuntimeError):
    """The bounded source contract could not be proved."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def canonical_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise SourceIncomplete("URL_OUTSIDE_ALLOWLIST")
    if parsed.username or parsed.password or parsed.fragment:
        raise SourceIncomplete("UNSAFE_URL")
    host = parsed.hostname
    if parsed.port not in (None, 443):
        raise SourceIncomplete("NON_STANDARD_PORT")
    query = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True) if parsed.query else {}
    encoded = urlencode(sorted((key, item) for key, values in query.items() for item in values))
    return urlunsplit(("https", host, parsed.path or "/", encoded, ""))


def classify_url(value: str) -> str:
    url = canonical_url(value)
    parsed = urlsplit(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    if parsed.hostname == "fapi.binance.com":
        if parsed.path == "/fapi/v1/exchangeInfo" and not query:
            return "exchange_info"
        raise SourceIncomplete("UNAUTHORIZED_FAPI_PATH")
    if parsed.hostname == "www.binance.com":
        if parsed.path == "/bapi/composite/v1/public/cms/article/list/query":
            expected_keys = {"type", "catalogId", "pageNo", "pageSize"}
            if set(query) != expected_keys or any(len(values) != 1 for values in query.values()):
                raise SourceIncomplete("UNKNOWN_INDEX_QUERY")
            try:
                category = int(query["catalogId"][0])
                page_no = int(query["pageNo"][0])
                page_size = int(query["pageSize"][0])
            except ValueError as exc:
                raise SourceIncomplete("INVALID_INDEX_QUERY") from exc
            if query["type"] != ["1"] or category not in CATEGORIES:
                raise SourceIncomplete("UNAUTHORIZED_INDEX_CATEGORY")
            if not 1 <= page_no <= MAX_PAGES_PER_CATEGORY or page_size != PAGE_SIZE:
                raise SourceIncomplete("INDEX_PAGE_OUTSIDE_FREEZE")
            return "announcement_index"
        detail_prefix = "/en/support/announcement/detail/"
        if parsed.path.startswith(detail_prefix) and not query:
            detail_id = parsed.path.removeprefix(detail_prefix)
            if DETAIL_ID_RE.fullmatch(detail_id) and parsed.path == detail_prefix + detail_id:
                return "announcement_detail"
        raise SourceIncomplete("UNAUTHORIZED_SUPPORT_PATH")
    if parsed.hostname == "developers.binance.com" and not query and url in DOC_URLS:
        return "definition_page"
    raise SourceIncomplete("UNAUTHORIZED_OFFICIAL_URL")


def index_url(category: int, page_no: int) -> str:
    query = urlencode(
        (("type", "1"), ("catalogId", str(category)), ("pageNo", str(page_no)), ("pageSize", str(PAGE_SIZE)))
    )
    return INDEX_URL.format(query=query)


class StrictRedirectHandler(HTTPRedirectHandler):
    def redirect_request(
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> Request | None:
        destination = canonical_url(urljoin(req.full_url, newurl))
        source_class = classify_url(req.full_url)
        if classify_url(destination) != source_class:
            raise SourceIncomplete("REDIRECT_CHANGED_REQUEST_CLASS")
        return super().redirect_request(req, fp, code, msg, headers, destination)


@dataclass
class Budget:
    requests: dict[str, int]
    response_bytes: dict[str, int]

    @classmethod
    def empty(cls) -> "Budget":
        return cls({name: 0 for name in CLASS_LIMITS}, {name: 0 for name in CLASS_LIMITS})

    def reserve_request(self, request_class: str) -> None:
        if request_class not in CLASS_LIMITS:
            raise SourceIncomplete("UNKNOWN_REQUEST_CLASS")
        if sum(self.requests.values()) >= TOTAL_REQUEST_CAP:
            raise SourceIncomplete("TOTAL_REQUEST_CAP_EXHAUSTED")
        class_cap, _ = CLASS_LIMITS[request_class]
        if self.requests[request_class] >= class_cap:
            raise SourceIncomplete(f"{request_class.upper()}_REQUEST_CAP_EXHAUSTED")
        self.requests[request_class] += 1

    def remaining_bytes(self, request_class: str) -> int:
        _, class_cap = CLASS_LIMITS[request_class]
        return min(class_cap - self.response_bytes[request_class], TOTAL_BYTE_CAP - sum(self.response_bytes.values()))

    def add_bytes(self, request_class: str, count: int) -> None:
        remaining = self.remaining_bytes(request_class)
        if count > remaining:
            raise SourceIncomplete(f"{request_class.upper()}_BYTE_CAP_EXHAUSTED")
        self.response_bytes[request_class] += count


class Capture:
    def __init__(self, output_dir: Path, opener: Any | None = None) -> None:
        self.output_dir = output_dir
        self.raw_dir = output_dir / "raw"
        self.opener = opener or build_opener(StrictRedirectHandler())
        self.budget = Budget.empty()
        self.responses: list[dict[str, Any]] = []

    def request(self, url: str) -> bytes:
        requested_url = canonical_url(url)
        request_class = classify_url(requested_url)
        self.budget.reserve_request(request_class)
        remaining = self.budget.remaining_bytes(request_class)
        if remaining <= 0:
            raise SourceIncomplete(f"{request_class.upper()}_BYTE_CAP_EXHAUSTED")

        requested_at = utc_now()
        request = Request(
            requested_url,
            headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity", "Accept": "*/*"},
            method="GET",
        )
        try:
            response = self.opener.open(request, timeout=60)
        except HTTPError as exc:
            response = exc
        with response:
            final_url = canonical_url(response.geturl())
            if classify_url(final_url) != request_class:
                raise SourceIncomplete("FINAL_URL_CHANGED_REQUEST_CLASS")
            content_length = response.headers.get("Content-Length")
            body = bounded_read(response, remaining, content_length)
            received_at = utc_now()
            self.budget.add_bytes(request_class, len(body))
            digest = hashlib.sha256(body).hexdigest()
            sequence = len(self.responses) + 1
            raw_name = f"{sequence:04d}-{request_class}-{digest}.bin"
            atomic_write(self.raw_dir / raw_name, body)
            status = int(response.getcode())
            entry = {
                "sequence": sequence,
                "request_class": request_class,
                "requested_url": requested_url,
                "final_url": final_url,
                "requested_at_utc": requested_at,
                "received_at_utc": received_at,
                "http_status": status,
                "content_type": response.headers.get("Content-Type"),
                "etag": response.headers.get("ETag"),
                "last_modified": response.headers.get("Last-Modified"),
                "response_bytes": len(body),
                "raw_response_sha256": digest,
                "raw_path": f"raw/{raw_name}",
            }
            self.responses.append(entry)
            if status != 200:
                raise SourceIncomplete(f"HTTP_STATUS_{status}")
            return body


def bounded_read(stream: Any, remaining: int, content_length: str | None) -> bytes:
    """Read without crossing a response budget, failing closed at an unproved EOF."""
    if remaining <= 0:
        raise SourceIncomplete("RESPONSE_BYTE_CAP_EXHAUSTED")
    declared: int | None = None
    if content_length is not None:
        try:
            declared = int(content_length)
        except ValueError as exc:
            raise SourceIncomplete("INVALID_CONTENT_LENGTH") from exc
        if declared < 0 or declared > remaining:
            raise SourceIncomplete("DECLARED_RESPONSE_EXCEEDS_BYTE_CAP")

    chunks: list[bytes] = []
    total = 0
    while total < remaining:
        chunk = stream.read(min(65_536, remaining - total))
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
    if total == remaining and declared != remaining:
        raise SourceIncomplete("RESPONSE_REACHED_CAP_WITHOUT_EOF_PROOF")
    if declared is not None and total != declared:
        raise SourceIncomplete("CONTENT_LENGTH_MISMATCH")
    return b"".join(chunks)


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def parse_json(body: bytes, context: str) -> dict[str, Any]:
    try:
        value = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceIncomplete(f"{context}_INVALID_JSON") from exc
    if not isinstance(value, dict):
        raise SourceIncomplete(f"{context}_UNKNOWN_SCHEMA")
    return value


def extract_index_page(body: bytes, category: int) -> tuple[int, list[dict[str, Any]]]:
    payload = parse_json(body, "INDEX")
    if payload.get("success") is not True or payload.get("code") not in ("000000", 0):
        raise SourceIncomplete("INDEX_UNSUCCESSFUL_RESPONSE")
    data = payload.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("total"), int) or data["total"] < 0:
        raise SourceIncomplete("INDEX_UNKNOWN_PAGINATION_SCHEMA")
    catalogs = data.get("catalogs")
    if not isinstance(catalogs, list) or len(catalogs) != 1 or not isinstance(catalogs[0], dict):
        raise SourceIncomplete("INDEX_UNKNOWN_CATALOG_SCHEMA")
    catalog = catalogs[0]
    observed_id = catalog.get("catalogId", catalog.get("id"))
    if observed_id is not None and str(observed_id) != str(category):
        raise SourceIncomplete("INDEX_CATEGORY_MISMATCH")
    articles = catalog.get("articles")
    if not isinstance(articles, list) or any(not isinstance(item, dict) for item in articles):
        raise SourceIncomplete("INDEX_UNKNOWN_ARTICLE_SCHEMA")
    if len(articles) > PAGE_SIZE:
        raise SourceIncomplete("INDEX_PAGE_SIZE_EXCEEDED")
    return data["total"], articles


def normalize_articles(category: int, articles: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for article in articles:
        code = article.get("code")
        title = article.get("title")
        release_date = article.get("releaseDate")
        if not isinstance(code, str) or not DETAIL_ID_RE.fullmatch(code):
            raise SourceIncomplete("INDEX_INVALID_DETAIL_ID")
        if not isinstance(title, str) or not title.strip():
            raise SourceIncomplete("INDEX_INVALID_TITLE")
        if not isinstance(release_date, int) or isinstance(release_date, bool) or release_date < 0:
            raise SourceIncomplete("INDEX_INVALID_RELEASE_DATE")
        normalized.append(
            {
                "category_id": category,
                "detail_id": code,
                "detail_url": DETAIL_PREFIX + code,
                "published_ms": release_date,
                "title": title.strip(),
            }
        )
    return normalized


def extract_current_contracts(body: bytes) -> list[dict[str, Any]]:
    payload = parse_json(body, "EXCHANGE_INFO")
    symbols = payload.get("symbols")
    if not isinstance(symbols, list) or any(not isinstance(item, dict) for item in symbols):
        raise SourceIncomplete("EXCHANGE_INFO_UNKNOWN_SCHEMA")
    records: list[dict[str, Any]] = []
    required = (
        "symbol", "pair", "contractType", "deliveryDate", "onboardDate", "status",
        "baseAsset", "quoteAsset", "marginAsset",
    )
    string_fields = (
        "symbol", "pair", "contractType", "status",
        "baseAsset", "quoteAsset", "marginAsset",
    )
    timestamp_fields = ("deliveryDate", "onboardDate")
    for item in symbols:
        if any(key not in item for key in required):
            raise SourceIncomplete("EXCHANGE_INFO_SYMBOL_SCHEMA_MISSING")
        if any(not isinstance(item[key], str) or not item[key].strip() for key in string_fields):
            raise SourceIncomplete("EXCHANGE_INFO_INVALID_STRING_FIELD")
        if any(
            not isinstance(item[key], int) or isinstance(item[key], bool) or item[key] < 0
            for key in timestamp_fields
        ):
            raise SourceIncomplete("EXCHANGE_INFO_INVALID_TIMESTAMP_FIELD")
        if item["contractType"] != "PERPETUAL" or item["quoteAsset"] != "USDT" or item["marginAsset"] != "USDT":
            continue
        records.append(
            {
                "venue": "BINANCE",
                "market_type": "USD_M",
                "contract_type": "PERPETUAL",
                "symbol": item["symbol"],
                "pair": item["pair"],
                "base_asset": item["baseAsset"],
                "quote_asset": item["quoteAsset"],
                "margin_asset": item["marginAsset"],
                "onboard_ms": item["onboardDate"],
                "current_delivery_ms": item["deliveryDate"],
                "current_status": item["status"],
                "multiplier_version": "UNRESOLVED",
                "classification": "AMBIGUOUS",
                "delist_effective_ms": None,
                "terminal_status": None,
                "listing_notice_url": None,
                "listing_notice_sha256": None,
                "delisting_notice_url": None,
                "delisting_notice_sha256": None,
            }
        )
    return sorted(records, key=lambda row: (str(row["symbol"]), int(row["onboard_ms"])))


def response_ref(capture: Capture, request_class: str, url: str | None = None) -> dict[str, Any]:
    for item in reversed(capture.responses):
        if item["request_class"] == request_class and (url is None or item["requested_url"] == canonical_url(url)):
            return {
                "sequence": item["sequence"],
                "url": item["final_url"],
                "sha256": item["raw_response_sha256"],
                "captured_at_utc": item["received_at_utc"],
            }
    raise SourceIncomplete("CAPTURE_REFERENCE_MISSING")


def build_candidate_ledger(
    capture: Capture,
    current_contracts: list[dict[str, Any]],
    announcements: list[dict[str, Any]],
) -> dict[str, Any]:
    exchange_ref = response_ref(capture, "exchange_info", EXCHANGE_INFO_URL)
    records = []
    for row in current_contracts:
        candidate = dict(row)
        candidate.update(
            {
                "classification_source_url": exchange_ref["url"],
                "capture_sha256": exchange_ref["sha256"],
                "captured_at_utc": exchange_ref["captured_at_utc"],
                "candidate_only": True,
            }
        )
        records.append(candidate)
    return {
        "schema": CANDIDATE_SCHEMA,
        "status": "SOURCE_INCOMPLETE",
        "cutoff_exclusive_utc": CUTOFF,
        "completeness_attestation": "NOT_ATTESTED_SOURCE_CAPTURE_ONLY",
        "records": records,
        "announcement_candidates": announcements,
        "limitations": [
            "Current exchangeInfo is not a historical contract master.",
            "Announcement presence does not prove exhaustive or immutable coverage.",
            "Listing, terminal time, identity continuity, multiplier, and classification remain unresolved.",
            "The offline resolver must fail closed on this unattested candidate ledger.",
        ],
    }


def run_capture(output_dir: Path, opener: Any | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    capture = Capture(output_dir, opener=opener)
    status = "SOURCE_INCOMPLETE"
    failure: str | None = None
    ledger: dict[str, Any] = {
        "schema": CANDIDATE_SCHEMA,
        "status": status,
        "cutoff_exclusive_utc": CUTOFF,
        "completeness_attestation": "NOT_ATTESTED_SOURCE_CAPTURE_ONLY",
        "records": [],
        "announcement_candidates": [],
    }
    try:
        exchange_body = capture.request(EXCHANGE_INFO_URL)
        current_contracts = extract_current_contracts(exchange_body)

        announcements: list[dict[str, Any]] = []
        totals: dict[int, int] = {}
        for category in CATEGORIES:
            first_body = capture.request(index_url(category, 1))
            total, articles = extract_index_page(first_body, category)
            totals[category] = total
            pages = max(1, math.ceil(total / PAGE_SIZE))
            if pages > MAX_PAGES_PER_CATEGORY:
                raise SourceIncomplete("INDEX_REQUEST_CAP_CANNOT_PROVE_TERMINATION")
            expected = max(0, min(PAGE_SIZE, total))
            if len(articles) != expected:
                raise SourceIncomplete("INDEX_NON_CANONICAL_PAGE_LENGTH")
            category_articles = normalize_articles(category, articles)
            for page_no in range(2, pages + 1):
                page_body = capture.request(index_url(category, page_no))
                observed_total, page_articles = extract_index_page(page_body, category)
                if observed_total != total:
                    raise SourceIncomplete("INDEX_TOTAL_CHANGED_DURING_CAPTURE")
                expected = max(0, min(PAGE_SIZE, total - (page_no - 1) * PAGE_SIZE))
                if len(page_articles) != expected:
                    raise SourceIncomplete("INDEX_NON_CANONICAL_PAGE_LENGTH")
                category_articles.extend(normalize_articles(category, page_articles))
            category_ids = [item["detail_id"] for item in category_articles]
            if len(category_articles) != total or len(set(category_ids)) != total:
                raise SourceIncomplete("INDEX_PAGINATION_DID_NOT_REPRODUCE_TOTAL")
            announcements.extend(category_articles)

        deduplicated: dict[str, dict[str, Any]] = {}
        for candidate in announcements:
            prior = deduplicated.get(candidate["detail_id"])
            if prior is None:
                deduplicated[candidate["detail_id"]] = candidate
            elif prior["title"] != candidate["title"] or prior["published_ms"] != candidate["published_ms"]:
                raise SourceIncomplete("DETAIL_ID_METADATA_CONFLICT")
            else:
                prior_categories = prior["category_id"] if isinstance(prior["category_id"], list) else [prior["category_id"]]
                categories = sorted(set(prior_categories) | {candidate["category_id"]})
                prior["category_id"] = categories

        normalized = [deduplicated[key] for key in sorted(deduplicated)]
        if len(normalized) > CLASS_LIMITS["announcement_detail"][0]:
            raise SourceIncomplete("DETAIL_REQUEST_CAP_CANNOT_COVER_INDEX")
        for candidate in normalized:
            capture.request(candidate["detail_url"])
            candidate["capture"] = response_ref(capture, "announcement_detail", candidate["detail_url"])
        for url in DOC_URLS:
            capture.request(url)

        ledger = build_candidate_ledger(capture, current_contracts, normalized)
        ledger["index_totals"] = {str(key): totals[key] for key in sorted(totals)}
        status = "CAPTURE_COMPLETE_SOURCE_QUALIFICATION_PENDING"
        ledger["status"] = status
    except SourceIncomplete as exc:
        failure = str(exc)
        ledger["failure"] = failure
    finally:
        manifest = {
            "schema": MANIFEST_SCHEMA,
            "tool_schema": TOOL_SCHEMA,
            "status": status,
            "failure": failure,
            "response_order": capture.responses,
            "budget": {
                "requests_by_class": capture.budget.requests,
                "response_bytes_by_class": capture.budget.response_bytes,
                "requests_total": sum(capture.budget.requests.values()),
                "response_bytes_total": sum(capture.budget.response_bytes.values()),
                "hard_request_cap": TOTAL_REQUEST_CAP,
                "hard_response_byte_cap": TOTAL_BYTE_CAP,
            },
            "outcome_accessed": False,
            "market_body_accessed": False,
            "completeness_attestation_emitted": False,
        }
        atomic_write(output_dir / "candidate-ledger.json", json_bytes(ledger))
        atomic_write(output_dir / "capture-manifest.json", json_bytes(manifest))
    return manifest, ledger


def prepare_output_dir(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise SourceIncomplete("OUTPUT_DIRECTORY_NOT_EMPTY")
    path.mkdir(parents=True, exist_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        prepare_output_dir(args.output_dir)
        manifest, _ = run_capture(args.output_dir)
    except (OSError, SourceIncomplete) as exc:
        print(json.dumps({"status": "SOURCE_INCOMPLETE", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps({"status": manifest["status"], "manifest": str(args.output_dir / "capture-manifest.json")}, sort_keys=True))
    return 0 if manifest["status"] == "CAPTURE_COMPLETE_SOURCE_QUALIFICATION_PENDING" else 2


if __name__ == "__main__":
    raise SystemExit(main())
