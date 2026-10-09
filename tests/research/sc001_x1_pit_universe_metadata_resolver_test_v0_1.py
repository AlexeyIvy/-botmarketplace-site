import importlib.util
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/research/sc001_x1_pit_universe_metadata_resolver_v0_1.py"
SPEC = importlib.util.spec_from_file_location("resolver", MODULE_PATH)
resolver = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = resolver
SPEC.loader.exec_module(resolver)


HEX = "0" * 64


def record(symbol, base, onboard_ms, *, classification="ORDINARY_CRYPTO", delist=None):
    item = {
        "venue": "BINANCE",
        "market_type": "USD_M",
        "contract_type": "PERPETUAL",
        "symbol": symbol,
        "pair": symbol,
        "base_asset": base,
        "quote_asset": "USDT",
        "margin_asset": "USDT",
        "onboard_ms": onboard_ms,
        "delist_effective_ms": delist,
        "terminal_status": "CLOSE" if delist is not None else None,
        "multiplier_version": "V1",
        "classification": classification,
        "classification_source_url": "https://www.binance.com/en/support/announcement/detail/classification",
        "listing_notice_url": "https://www.binance.com/en/support/announcement/detail/listing",
        "listing_notice_sha256": HEX,
        "capture_sha256": HEX,
        "captured_at_utc": "2026-10-09T17:00:00Z",
        "delisting_notice_url": None,
        "delisting_notice_sha256": None,
    }
    if delist is not None:
        item["delisting_notice_url"] = "https://www.binance.com/en/support/announcement/detail/delisting"
        item["delisting_notice_sha256"] = HEX
    return item


def ledger(records):
    return {
        "schema": resolver.SCHEMA,
        "cutoff_exclusive_utc": "2026-10-01T00:00:00Z",
        "completeness_attestation": resolver.ATTESTATION,
        "records": records,
        "months": ["2026-09"],
    }


class ResolverContractTest(unittest.TestCase):
    def test_missing_completeness_attestation_fails_closed(self):
        payload = ledger([record("BTCUSDT", "BTC", 1)])
        payload["completeness_attestation"] = "UNKNOWN"
        with self.assertRaisesRegex(resolver.LedgerError, "SOURCE_STRATEGY_ATTENTION_REQUIRED"):
            resolver.validate_ledger(payload)

    def test_current_survivor_only_anchor_set_cannot_pass_pool_minimum(self):
        payload = ledger([
            record("BTCUSDT", "BTC", 1),
            record("ETHUSDT", "ETH", 2),
        ])
        contracts = resolver.validate_ledger(payload)
        with self.assertRaisesRegex(resolver.LedgerError, "fewer than eight"):
            resolver.build_pool(contracts)

    def test_overlapping_relisting_epochs_fail(self):
        records = [
            record("BTCUSDT", "BTC", 1),
            record("ETHUSDT", "ETH", 2),
            record("AAAUSDT", "AAA", 3),
            record("AAAUSDT", "AAA", 4),
        ]
        with self.assertRaisesRegex(resolver.LedgerError, "relisting without terminal predecessor"):
            resolver.validate_ledger(ledger(records))

    def test_nonofficial_evidence_url_fails(self):
        item = record("BTCUSDT", "BTC", 1)
        item["listing_notice_url"] = "https://example.com/listing"
        with self.assertRaisesRegex(resolver.LedgerError, "non-official URL"):
            resolver.validate_ledger(ledger([item]))

    def test_hash_partition_and_month_membership_are_deterministic(self):
        old = 1_500_000_000_000
        records = [record("BTCUSDT", "BTC", old), record("ETHUSDT", "ETH", old + 1)]
        for index in range(12):
            records.append(record(f"A{index:02d}USDT", f"A{index:02d}", old + 10 + index))
        contracts = resolver.validate_ledger(ledger(records))
        first = resolver.build_pool(contracts)
        second = resolver.build_pool(list(reversed(contracts)))
        self.assertEqual(first, second)
        self.assertEqual(len(first["node_reserve"]), 3)
        membership = resolver.month_membership(contracts, first, "2026-09")
        self.assertEqual(len(membership["anchors"]), 2)
        self.assertEqual(len(membership["discovery"]), 9)

    def test_delisted_before_month_is_not_active(self):
        old = 1_500_000_000_000
        records = [record("BTCUSDT", "BTC", old), record("ETHUSDT", "ETH", old + 1)]
        for index in range(9):
            delist = 1_770_000_000_000 if index == 0 else None
            records.append(record(f"B{index:02d}USDT", f"B{index:02d}", old + 10 + index, delist=delist))
        contracts = resolver.validate_ledger(ledger(records))
        pool = resolver.build_pool(contracts)
        membership = resolver.month_membership(contracts, pool, "2026-09")
        ended = next(item.identity for item in contracts if item.symbol == "B00USDT")
        self.assertNotIn(ended, membership["active"])


if __name__ == "__main__":
    unittest.main()
