#!/usr/bin/env python3
"""Deterministic metadata-only Binance USD-M monthly 1m archive probe.

SC001-H1-004E prepares this implementation only. A later, separately
authorized task may run the network probe. The only executable mode in this
file that does not use the network is --self-test.
"""

from __future__ import annotations

import argparse
import calendar
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence


SCHEMA = "sc001.h1_shared_backbone_source_probe.v0.1"
SOURCE_ENDPOINT = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
SOURCE_PUBLIC_URL_PREFIX = "https://data.binance.vision/"
ROOT_PREFIX = "data/futures/um/monthly/klines/"
INTERVAL = "1m"
CUTOFF_EXCLUSIVE_UTC = "2026-10-01T00:00:00Z"
LAST_ELIGIBLE_MONTH = (2026, 9)
SYMBOL_RE = re.compile(r"^[A-Z0-9]+USDT$")
MAX_H1_SYMBOLS = 12
MIN_H1_SYMBOLS = 6
MIN_H1_CONTIGUOUS_DAYS = 300
MAX_CANDIDATES_SCANNED = 80
ANCHORS = ("BTCUSDT", "ETHUSDT")
MIN_ANCHOR_CONTIGUOUS_MONTHS = 36
MAX_S3_LIST_REQUESTS = 85
MAX_XML_RESPONSE_BYTES = 2_000_000
MAX_TOTAL_NETWORK_BYTES = 50_000_000
MAX_RETRIES_PER_REQUEST = 2
REQUEST_TIMEOUT_SECONDS = 30
USER_AGENT = "BotMarketplace-SC001-H1-source-probe/0.1"


class ProbeError(RuntimeError):
    """Fail-closed source-probe error."""


class BudgetError(ProbeError):
    """A frozen request or byte budget would be exceeded."""


@dataclass
class Budget:
    max_requests: int = MAX_S3_LIST_REQUESTS
    max_xml_bytes: int = MAX_XML_RESPONSE_BYTES
    max_total_bytes: int = MAX_TOTAL_NETWORK_BYTES
    request_count: int = 0
    network_bytes: int = 0

    def begin_request(self) -> None:
        if self.request_count >= self.max_requests:
            raise BudgetError("max_s3_list_requests exceeded")
        self.request_count += 1

    def consume_response(self, payload: bytes) -> None:
        size = len(payload)
        self.network_bytes += size
        if size > self.max_xml_bytes:
            raise BudgetError("max_xml_response_bytes_each exceeded")
        if self.network_bytes > self.max_total_bytes:
            raise BudgetError("max_total_network_bytes exceeded")


@dataclass(frozen=True)
class S3Page:
    keys: tuple[str, ...]
    common_prefixes: tuple[str, ...]
    is_truncated: bool
    next_token: str | None


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(element: ET.Element, name: str) -> str | None:
    for child in element:
        if _local_name(child.tag) == name:
            return child.text
    return None


def parse_s3_page(payload: bytes) -> S3Page:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise ProbeError("invalid S3 XML response") from exc
    if _local_name(root.tag) != "ListBucketResult":
        raise ProbeError("unexpected S3 XML root")

    keys: list[str] = []
    prefixes: list[str] = []
    for child in root:
        name = _local_name(child.tag)
        if name == "Contents":
            key = _child_text(child, "Key")
            if key is None:
                raise ProbeError("S3 Contents entry lacks Key")
            keys.append(key)
        elif name == "CommonPrefixes":
            prefix = _child_text(child, "Prefix")
            if prefix is None:
                raise ProbeError("S3 CommonPrefixes entry lacks Prefix")
            prefixes.append(prefix)

    truncated_text = (_child_text(root, "IsTruncated") or "false").strip().lower()
    if truncated_text not in {"true", "false"}:
        raise ProbeError("invalid IsTruncated value")
    is_truncated = truncated_text == "true"
    next_token = _child_text(root, "NextContinuationToken")
    if is_truncated and not next_token:
        raise ProbeError("truncated S3 response lacks continuation token")
    return S3Page(
        keys=tuple(keys),
        common_prefixes=tuple(prefixes),
        is_truncated=is_truncated,
        next_token=next_token,
    )


class RealFetcher:
    """Serial, budgeted HTTPS fetcher for S3 ListObjectsV2 XML only."""

    def __init__(self, budget: Budget) -> None:
        self.budget = budget

    def __call__(self, url: str) -> bytes:
        expected = SOURCE_ENDPOINT + "?"
        if not url.startswith(expected):
            raise ProbeError("refusing non-canonical source endpoint")
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        if query.get("list-type") != ["2"]:
            raise ProbeError("refusing non-ListObjectsV2 request")

        last_error: BaseException | None = None
        for attempt in range(MAX_RETRIES_PER_REQUEST + 1):
            self.budget.begin_request()
            request = urllib.request.Request(
                url,
                headers={
                    "Accept": "application/xml",
                    "User-Agent": USER_AGENT,
                },
                method="GET",
            )
            try:
                remaining = self.budget.max_total_bytes - self.budget.network_bytes
                if remaining <= 0:
                    raise BudgetError("max_total_network_bytes exhausted")
                read_limit = min(self.budget.max_xml_bytes, remaining)
                with urllib.request.urlopen(
                    request, timeout=REQUEST_TIMEOUT_SECONDS
                ) as response:
                    payload = response.read(read_limit + 1)
                self.budget.consume_response(payload)
                return payload
            except BudgetError:
                raise
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = exc
                if attempt >= MAX_RETRIES_PER_REQUEST:
                    break
                time.sleep(2**attempt)
        raise ProbeError(
            "S3 ListObjectsV2 request failed after frozen retry budget"
        ) from last_error


class StaticFetcher:
    """Offline fixture fetcher used only by the synthetic self-test."""

    def __init__(self, payloads: Sequence[bytes], budget: Budget) -> None:
        self.payloads = list(payloads)
        self.budget = budget
        self.urls: list[str] = []

    def __call__(self, url: str) -> bytes:
        self.budget.begin_request()
        self.urls.append(url)
        if not self.payloads:
            raise ProbeError("synthetic fixture response exhausted")
        payload = self.payloads.pop(0)
        self.budget.consume_response(payload)
        return payload


class S3MetadataClient:
    def __init__(self, fetch: Callable[[str], bytes]) -> None:
        self.fetch = fetch

    @staticmethod
    def _url(
        prefix: str, delimiter: str | None, continuation_token: str | None
    ) -> str:
        params: list[tuple[str, str]] = [
            ("list-type", "2"),
            ("prefix", prefix),
            ("max-keys", "1000"),
        ]
        if delimiter is not None:
            params.append(("delimiter", delimiter))
        if continuation_token is not None:
            params.append(("continuation-token", continuation_token))
        return SOURCE_ENDPOINT + "?" + urllib.parse.urlencode(params)

    def list_objects(
        self, prefix: str, delimiter: str | None = None
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        all_keys: list[str] = []
        all_prefixes: list[str] = []
        token: str | None = None
        seen_tokens: set[str] = set()
        while True:
            page = parse_s3_page(self.fetch(self._url(prefix, delimiter, token)))
            all_keys.extend(page.keys)
            all_prefixes.extend(page.common_prefixes)
            if not page.is_truncated:
                break
            assert page.next_token is not None
            if page.next_token in seen_tokens:
                raise ProbeError("repeated S3 continuation token")
            seen_tokens.add(page.next_token)
            token = page.next_token
        return tuple(all_keys), tuple(all_prefixes)


def symbol_from_common_prefix(prefix: str) -> str | None:
    if not prefix.startswith(ROOT_PREFIX) or not prefix.endswith("/"):
        return None
    remainder = prefix[len(ROOT_PREFIX) : -1]
    if "/" in remainder or not SYMBOL_RE.fullmatch(remainder):
        return None
    return remainder


def parse_monthly_archive_key(key: str, symbol: str) -> tuple[int, int] | None:
    stem = (
        ROOT_PREFIX
        + symbol
        + "/"
        + INTERVAL
        + "/"
        + symbol
        + "-"
        + INTERVAL
        + "-"
    )
    if not key.startswith(stem) or not key.endswith(".zip"):
        return None
    month_text = key[len(stem) : -4]
    match = re.fullmatch(r"(\d{4})-(\d{2})", month_text)
    if match is None:
        return None
    year, month = int(match.group(1)), int(match.group(2))
    if not 1 <= month <= 12:
        return None
    if (year, month) > LAST_ELIGIBLE_MONTH:
        return None
    return year, month


def next_month(value: tuple[int, int]) -> tuple[int, int]:
    year, month = value
    return (year + 1, 1) if month == 12 else (year, month + 1)


def month_label(value: tuple[int, int] | None) -> str | None:
    if value is None:
        return None
    return f"{value[0]:04d}-{value[1]:02d}"


def calendar_days(months: Iterable[tuple[int, int]]) -> int:
    return sum(calendar.monthrange(year, month)[1] for year, month in months)


def longest_contiguous_run(
    months: Iterable[tuple[int, int]],
) -> tuple[tuple[tuple[int, int], ...], int]:
    ordered = sorted(set(months))
    if not ordered:
        return (), 0

    runs: list[list[tuple[int, int]]] = []
    current = [ordered[0]]
    for value in ordered[1:]:
        if value == next_month(current[-1]):
            current.append(value)
        else:
            runs.append(current)
            current = [value]
    runs.append(current)

    scored = [(calendar_days(run), tuple(run)) for run in runs]
    best_days, best_run = min(
        scored,
        key=lambda item: (
            -item[0],
            item[1][0],
            item[1][-1],
        ),
    )
    return best_run, best_days


def archive_key(symbol: str, month: tuple[int, int]) -> str:
    label = month_label(month)
    assert label is not None
    return (
        ROOT_PREFIX
        + symbol
        + "/"
        + INTERVAL
        + "/"
        + symbol
        + "-"
        + INTERVAL
        + "-"
        + label
        + ".zip"
    )


def archive_url(key: str | None) -> str | None:
    if key is None:
        return None
    return SOURCE_PUBLIC_URL_PREFIX + key


def summarize_symbol(
    symbol: str, keys: Iterable[str], h1_candidate: bool
) -> dict[str, object]:
    months = sorted(
        {
            parsed
            for key in keys
            if (parsed := parse_monthly_archive_key(key, symbol)) is not None
        }
    )
    run, run_days = longest_contiguous_run(months)
    first_month = months[0] if months else None
    last_month = months[-1] if months else None
    first_key = archive_key(symbol, first_month) if first_month else None
    last_key = archive_key(symbol, last_month) if last_month else None
    result: dict[str, object] = {
        "symbol": symbol,
        "eligible_archive_month_count": len(months),
        "first_eligible_month": month_label(first_month),
        "last_eligible_month": month_label(last_month),
        "first_archive_key": first_key,
        "first_source_url": archive_url(first_key),
        "last_archive_key": last_key,
        "last_source_url": archive_url(last_key),
        "longest_contiguous_start_month": month_label(run[0]) if run else None,
        "longest_contiguous_end_month": month_label(run[-1]) if run else None,
        "longest_contiguous_months": len(run),
        "longest_contiguous_calendar_days": run_days,
    }
    if h1_candidate:
        result["h1_qualifies"] = run_days >= MIN_H1_CONTIGUOUS_DAYS
    else:
        result["source_class_compatible"] = (
            len(run) >= MIN_ANCHOR_CONTIGUOUS_MONTHS
        )
    return result


def symbol_prefix(symbol: str) -> str:
    return ROOT_PREFIX + symbol + "/" + INTERVAL + "/"


def list_symbol_keys(client: S3MetadataClient, symbol: str) -> tuple[str, ...]:
    keys, _ = client.list_objects(symbol_prefix(symbol))
    return keys


def scan_h1_candidates(
    candidate_symbols: Sequence[str],
    key_provider: Callable[[str], Iterable[str]],
) -> tuple[list[str], list[dict[str, object]]]:
    eligible: list[str] = []
    summaries: list[dict[str, object]] = []
    for symbol in candidate_symbols[:MAX_CANDIDATES_SCANNED]:
        summary = summarize_symbol(symbol, key_provider(symbol), True)
        summaries.append(summary)
        if summary["h1_qualifies"]:
            eligible.append(symbol)
            if len(eligible) == MAX_H1_SYMBOLS:
                break
    return eligible, summaries


def discover_candidates(client: S3MetadataClient) -> list[str]:
    _, common_prefixes = client.list_objects(ROOT_PREFIX, delimiter="/")
    symbols = {
        symbol
        for prefix in common_prefixes
        if (symbol := symbol_from_common_prefix(prefix)) is not None
    }
    return sorted(symbols, key=lambda value: value.encode("utf-8"))


def source_identity() -> dict[str, object]:
    return {
        "provider": "Binance",
        "market": "USD-M futures",
        "object_class": "monthly klines ZIP archive metadata",
        "endpoint": SOURCE_ENDPOINT,
        "public_url_prefix": SOURCE_PUBLIC_URL_PREFIX,
        "root_prefix": ROOT_PREFIX,
        "interval": INTERVAL,
        "metadata_only": True,
    }


def empty_result(budget: Budget) -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "source_identity": source_identity(),
        "cutoff": {
            "exclusive_utc": CUTOFF_EXCLUSIVE_UTC,
            "last_eligible_archive_month": month_label(LAST_ELIGIBLE_MONTH),
        },
        "discovered_symbol_count": 0,
        "scanned_candidate_count": 0,
        "h1_eligible_symbols": [],
        "per_scanned_symbol_month_span": [],
        "btc_anchor_span": None,
        "eth_anchor_span": None,
        "request_count": budget.request_count,
        "network_bytes": budget.network_bytes,
        "terminal_source_status": "SOURCE_PROBE_ERROR",
    }


def run_probe() -> tuple[dict[str, object], int]:
    budget = Budget()
    result = empty_result(budget)
    try:
        client = S3MetadataClient(RealFetcher(budget))
        candidates = discover_candidates(client)
        eligible, summaries = scan_h1_candidates(
            candidates, lambda symbol: list_symbol_keys(client, symbol)
        )

        anchors: dict[str, dict[str, object]] = {}
        for anchor in ANCHORS:
            anchors[anchor] = summarize_symbol(
                anchor, list_symbol_keys(client, anchor), False
            )

        h1_sufficient = len(eligible) >= MIN_H1_SYMBOLS
        anchors_compatible = all(
            bool(anchors[name]["source_class_compatible"]) for name in ANCHORS
        )
        if not h1_sufficient:
            terminal_status = "INSUFFICIENT_H1_SOURCE_COVERAGE"
            exit_code = 2
        elif not anchors_compatible:
            terminal_status = "H1_SOURCE_COMPATIBLE_X1_ANCHOR_INSUFFICIENT"
            exit_code = 2
        else:
            terminal_status = "H1_X1_SOURCE_METADATA_COMPATIBLE"
            exit_code = 0

        result.update(
            {
                "discovered_symbol_count": len(candidates),
                "scanned_candidate_count": len(summaries),
                "h1_eligible_symbols": eligible,
                "per_scanned_symbol_month_span": summaries,
                "btc_anchor_span": anchors["BTCUSDT"],
                "eth_anchor_span": anchors["ETHUSDT"],
                "request_count": budget.request_count,
                "network_bytes": budget.network_bytes,
                "terminal_source_status": terminal_status,
            }
        )
        return result, exit_code
    except Exception as exc:
        result["request_count"] = budget.request_count
        result["network_bytes"] = budget.network_bytes
        result["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
        return result, 1


def _xml_page(
    *,
    prefixes: Sequence[str] = (),
    keys: Sequence[str] = (),
    truncated: bool = False,
    token: str | None = None,
) -> bytes:
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">',
    ]
    parts.extend(
        "<CommonPrefixes><Prefix>"
        + prefix
        + "</Prefix></CommonPrefixes>"
        for prefix in prefixes
    )
    parts.extend("<Contents><Key>" + key + "</Key></Contents>" for key in keys)
    parts.append("<IsTruncated>" + str(truncated).lower() + "</IsTruncated>")
    if token is not None:
        parts.append("<NextContinuationToken>" + token + "</NextContinuationToken>")
    parts.append("</ListBucketResult>")
    return "".join(parts).encode("utf-8")


def run_self_test() -> dict[str, object]:
    checks: list[str] = []

    page1 = _xml_page(
        prefixes=(ROOT_PREFIX + "AAAUSDT/",),
        truncated=True,
        token="next page",
    )
    page2 = _xml_page(prefixes=(ROOT_PREFIX + "BBBUSDT/",))
    fixture_budget = Budget()
    fixture_fetcher = StaticFetcher((page1, page2), fixture_budget)
    fixture_client = S3MetadataClient(fixture_fetcher)
    _, prefixes = fixture_client.list_objects(ROOT_PREFIX, delimiter="/")
    assert prefixes == (
        ROOT_PREFIX + "AAAUSDT/",
        ROOT_PREFIX + "BBBUSDT/",
    )
    assert fixture_budget.request_count == 2
    assert "continuation-token=next+page" in fixture_fetcher.urls[1]
    checks.append("s3_pagination_and_delimiter")

    assert symbol_from_common_prefix(ROOT_PREFIX + "BTCUSDT/") == "BTCUSDT"
    assert symbol_from_common_prefix(ROOT_PREFIX + "BTC-USDT/") is None
    valid_key = archive_key("BTCUSDT", (2026, 9))
    assert parse_monthly_archive_key(valid_key, "BTCUSDT") == (2026, 9)
    assert parse_monthly_archive_key(valid_key + ".CHECKSUM", "BTCUSDT") is None
    assert (
        parse_monthly_archive_key(
            archive_key("BTCUSDT", (2026, 10)), "BTCUSDT"
        )
        is None
    )
    checks.append("symbol_and_monthly_key_parsing")

    leap_run, leap_days = longest_contiguous_run(
        ((2024, 1), (2024, 2), (2024, 3))
    )
    assert len(leap_run) == 3 and leap_days == 91
    gap_run, gap_days = longest_contiguous_run(
        ((2024, 1), (2024, 3), (2024, 4))
    )
    assert gap_run == ((2024, 3), (2024, 4)) and gap_days == 61
    checks.append("contiguous_month_and_day_computation")

    ten_months = tuple((2025, month) for month in range(1, 11))
    qualifying_keys = lambda symbol: tuple(
        archive_key(symbol, month) for month in ten_months
    )
    ordered = [f"A{index:02d}USDT" for index in range(20)]
    eligible, summaries = scan_h1_candidates(ordered, qualifying_keys)
    assert eligible == ordered[:MAX_H1_SYMBOLS]
    assert len(summaries) == MAX_H1_SYMBOLS
    checks.append("lexicographic_first_12_rule")

    many = [f"B{index:03d}USDT" for index in range(100)]
    eligible, summaries = scan_h1_candidates(many, lambda symbol: ())
    assert eligible == [] and len(summaries) == MAX_CANDIDATES_SCANNED
    checks.append("candidate_scan_cap_80")

    anchor_months: list[tuple[int, int]] = []
    value = (2023, 1)
    for _ in range(MIN_ANCHOR_CONTIGUOUS_MONTHS):
        anchor_months.append(value)
        value = next_month(value)
    anchor_summary = summarize_symbol(
        "BTCUSDT",
        (archive_key("BTCUSDT", month) for month in anchor_months),
        False,
    )
    assert anchor_summary["source_class_compatible"] is True
    checks.append("anchor_36_month_check")

    request_budget = Budget(max_requests=1)
    request_fetcher = StaticFetcher((_xml_page(), _xml_page()), request_budget)
    request_fetcher("first")
    try:
        request_fetcher("second")
        raise AssertionError("request cap did not fail closed")
    except BudgetError:
        pass

    byte_budget = Budget(max_xml_bytes=8, max_total_bytes=8)
    try:
        StaticFetcher((b"123456789",), byte_budget)("oversize")
        raise AssertionError("byte cap did not fail closed")
    except BudgetError:
        pass
    checks.append("request_and_byte_caps")

    return {
        "schema": SCHEMA,
        "self_test": "PASS",
        "checks": checks,
        "network_accessed": False,
    }


def emit(payload: dict[str, object]) -> None:
    sys.stdout.write(
        json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Metadata-only Binance USD-M monthly 1m archive probe; "
            "network execution requires separate authorization."
        )
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run deterministic synthetic fixtures without network access",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        emit(run_self_test())
        return 0

    result, exit_code = run_probe()
    emit(result)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
