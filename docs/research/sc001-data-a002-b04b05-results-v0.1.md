# SC001-DATA-A002-B04B05 Results v0.1

Status: **PASS**

Stage: `SC001-DATA-A002-B04B05`
Role: DEV-CONFIRMATION acquisition/qualification only

## Summary

All 10 frozen 2024-Q1/Q2 DEV-CONFIRMATION Binance BTCUSDT USD-M aggTrades days passed acquisition and integrity qualification before any E002 confirmation feature or return metric was calculated.

No strategy features, confirmation metrics, strategy P&L, Validation, or Final data were accessed during this stage.

## Independent audit

- Days passed: 10 / 10
- Total aggTrades rows: 15,050,402
- All days observed 1,440 / 1,440 UTC minute buckets
- aggTrade ID gaps: 0 on all days
- aggTrade duplicate/backward events: 0
- timestamp backwards: 0
- invalid rows: 0
- out-of-day rows: 0
- underlying trade range overlap/backward events: 0
- cross-selected-day order violations: 0
- live SHA256 = frozen preflight SHA256 = downloaded archive SHA256 for all 10 files
- live Content-Length = frozen expected bytes = downloaded archive bytes for all 10 files
- Underlying trade-ID gap diagnostic total: 2,531 (diagnostic/non-fatal)

## Size and safety

- Frozen archive bytes total: 194,145,949
- Network bytes read: 194,146,939
- Difference: 990 bytes, consistent with ten small checksum responses of 99 bytes each
- Workspace after outputs: 194,179,453 bytes
- Free space after outputs: 68,423,458,816 bytes
- Session/workspace cap: 300,000,000 bytes
- Minimum reserve: 4,000,000,000 bytes

## Firewall status

The holdout was acquired without opening E002 confirmation metrics. This preserves the pre-frozen combined 10-day DEV-CONFIRMATION test.

The next permitted action is one execution of the already frozen `SC001-E002-CONFIRMATION` engine, with no threshold/window/direction retuning. Its frozen gates include at least 9/10 positive 100ms daily Spearman values and 100ms median Spearman retention >= 0.06468345784701792, plus quarter/stratum/extreme-spread and 250ms stress gates.

This acquisition PASS is not evidence of net profitability and does not authorize L2/execution or real-money trading claims.
