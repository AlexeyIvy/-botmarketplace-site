# SC001-DATA-Q001 — Free Multi-Venue Qualification Results v0.1

**Project:** BotMarketplace / BotMarketplace.store  
**Branch:** SCALPING RESEARCH / SC001  
**Date:** 2026-09-11  
**Status:** QUALIFICATION COMPLETE — BULK DOWNLOAD NOT YET AUTHORIZED

## Result

The fixed 2025-01-15 qualification succeeded for Binance and Bybit. OKX remains unresolved because the Q001 probe used an invalid historical-market-data parameterization; this is not evidence that OKX historical data are unavailable.

## Binance BTCUSDT USD-M

### 1m klines

- status: PASS
- 1,440 data rows for the UTC day
- compressed size: 63,072 bytes
- SHA-256 matches Binance CHECKSUM
- timestamps monotonic
- zero duplicate open timestamps
- zero 1-minute interval breaks
- fields include OHLC, volume, quote volume, trade count, taker-buy volume and taker-buy quote volume

Conclusion: suitable as the long multi-regime 1m backbone.

### aggTrades

- status: PASS
- 1,681,098 aggregate-trade rows
- compressed size: 21,271,119 bytes
- SHA-256 matches Binance CHECKSUM
- independently rechecked transaction timestamps are monotonic across the full file
- first transaction: 2025-01-15 00:00:05.109 UTC
- last transaction: 2025-01-15 23:59:59.991 UTC

Important validator correction: Q001 inspect_zip_csv assumed column 0 was a timestamp. For aggTrades column 0 is agg_trade_id and the actual timestamp is transact_time. Therefore the Q001 report's aggTrades first_timestamp/last_timestamp/timestamp_duplicates fields describe IDs rather than time. The archive itself is intact; this is a validator metadata bug to correct before bulk collection.

## Bybit BTCUSDT public trades

- status: PASS
- 2,049,441 trade rows
- compressed size: 74,892,440 bytes
- full independent stream check: timestamps monotonic
- first timestamp: 2025-01-15 00:00:00.2335 UTC
- last timestamp: 2025-01-15 23:59:59.999 UTC
- Buy rows: 1,072,896
- Sell rows: 976,545
- schema includes timestamp, side, size, price, tickDirection and trade match ID

Conclusion: useful independent venue-level tick-trade source, but a full multi-year phone download would be very large. Prefer selected regime/event windows or staged collection rather than blindly downloading all days.

## Storage implications from the fixed day

Approximate linearized compressed storage at this one-day activity level (not a promise; crypto activity varies materially):

- Binance 1m: ~23 MB/year
- Binance aggTrades: ~7.4 GB/year
- Bybit trades: ~26 GB/year

Therefore the first long-history backbone should be Binance 1m. Tick data should be staged and/or sampled by frozen calendar windows to avoid allowing storage constraints to create hindsight selection.

## OKX

Q001 returned NEEDS_REVIEW. www.okx.com responded, so this is not a connectivity failure. Modules 1–6 and 11 returned `Parameter dateAggrType error`; modules 7–10 returned module errors. The script used dateAggrType=1D and numeric module probing.

Current OKX documentation still exposes the public historical-market-data endpoint and documents trade/candlestick/funding/order-book historical modules, including deep order-book data. A corrected qualification probe is required using the current exact parameter contract before any OKX bulk download.

No OKX L2 data have been downloaded yet.

## Decision

1. Do not bulk-download all trade archives yet.
2. Freeze Binance 1m as the primary long-history backbone.
3. Correct the Binance aggTrades timestamp validator before bulk use.
4. Run a corrected OKX qualification probe before deciding the L2 calendar.
5. Use Bybit tick trades as an independent cross-venue microstructure source, but collect in frozen windows rather than full multi-year history unless storage/compute justifies it.
6. No strategy/P&L may be tested during data acquisition.

SC001 remains independent of R009/R003/R010/S002.