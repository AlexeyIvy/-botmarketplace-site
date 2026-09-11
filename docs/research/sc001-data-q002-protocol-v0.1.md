# SC001-DATA-Q002 — Staged Validation / OKX Qualification Protocol v0.1

**Project:** BotMarketplace / BotMarketplace.store  
**Branch:** SCALPING RESEARCH / SC001  
**Date:** 2026-09-11  
**Status:** FROZEN BEFORE BULK DOWNLOAD  

## Objective

Correct the Q001 validation mistakes, independently revalidate the existing Binance/Bybit qualification samples, and determine the safest documented path for OKX historical data without bulk-downloading tick/L2 archives.

No strategy P&L is calculated in Q002.

## Why Q002 exists

Q001 established that free high-frequency data are practically accessible:

- Binance BTCUSDT USD-M 1m: 1,440 rows/day with checksum validation;
- Binance BTCUSDT USD-M aggTrades: ~1.68M rows on the fixed qualification day;
- Bybit BTCUSDT trades: ~2.05M rows on the same day.

Q001 also revealed two issues:

1. the Binance aggTrades validator incorrectly treated `agg_trade_id` as a timestamp instead of the `transact_time` column;
2. the OKX probe used numeric `module` values against `/api/v5/public/market-data-history`, while the official client/tests use named modules such as `volume`, `openInterest`, and `tradeCount`.

Neither issue corrupts the downloaded market files. Q002 repairs qualification logic before any bulk acquisition.

## Financial/technical critique of the acquisition plan

### Arguments for the current multi-venue plan

- Binance offers inexpensive long 1m history plus checksum-backed aggTrades and is suitable as the primary chronology/backbone.
- Bybit exposes a dense independent tick-trade tape, useful for venue replication and avoiding single-venue conclusions.
- OKX officially advertises tick trades from September 2021 and high-resolution L2 order-book history from March 2023, which is directly relevant to spread/depth/imbalance research.
- Keeping venue roles separate reduces the temptation to select a venue only because it produced prettier P&L.

### Arguments against downloading everything

- One qualification day was already ~20 MB compressed for Binance aggTrades and ~71 MB for Bybit trades; daily size varies materially with market activity, so linear multi-year extrapolation is unsafe.
- L2 can be orders of magnitude larger than trade tapes; downloading several years to a phone before proving the schema and research need is wasteful and risky.
- More microstructure fields increase researcher degrees of freedom and overfitting risk unless hypotheses are frozen before testing.
- Historical spread/book data can be venue- and feed-specific; collecting more venues does not automatically improve causal execution modeling.

### Optimized decision

1. Keep Binance 1m as the long low-storage backbone.
2. Do not bulk-download multi-year aggTrades, Bybit trades, or OKX L2 yet.
3. Freeze representative microstructure windows only after Q002 establishes source behavior and actual sizes.
4. Use the same predeclared windows across venues where possible; do not choose venue/date windows by subsequent P&L.
5. Prefer streaming validation and compressed raw preservation; do not decompress huge archives permanently on the phone.
6. Open a later Q003/bulk calendar only after Q002 review.

## Q002 local validation

Revalidate the existing Q001 samples in place without copying or expanding them:

- `SC001_DATA_Q001/BTCUSDT-aggTrades-2025-01-15.zip` using `transact_time` as the timestamp;
- `SC001_DATA_Q001/BTCUSDT2025-01-15.csv.gz` using the Bybit fractional-second timestamp.

Checks include monotonic time, fixed-day membership, positive price/size, valid side, and aggregate-trade-ID monotonicity.

Repeated trade timestamps are allowed and are not treated as duplicate records.

## OKX qualification

Use documented public endpoints for schema/connectivity qualification:

- `/api/v5/market/history-candles` for historical 1m candles;
- `/api/v5/market/history-trades` only as a recent-trade schema/access probe because official documentation limits this endpoint to the last three months;
- `/api/v5/market/books` only as a current L2 schema/access probe, not historical evidence;
- `/api/v5/public/market-data-history` with named modules (`volume`, `openInterest`, `tradeCount`) to correct the Q001 numeric-module mistake.

Also inspect official OKX historical-data pages for discoverable download URLs, but **never automatically follow bulk file links in Q002**.

Official OKX historical-data claims (to be treated as source availability, not yet locally validated data):

- tick-level trade history from September 2021;
- candlesticks from July 2023;
- funding from March 2022;
- high-resolution L2 order book from March 2023.

## Hard storage/network protections

Q002 uses conservative decimal-byte caps:

- session network download cap: **2,000,000,000 bytes**;
- Q002 workspace cap: **2,000,000,000 bytes**;
- per-file/request cap: **512,000,000 bytes**;
- minimum free-storage reserve after any permitted download: **4,000,000,000 bytes**.

Additional protections:

- check advertised `Content-Length` when available;
- stream/cap unknown-size responses;
- abort before exceeding a cap;
- never follow discovered bulk OKX archive URLs automatically;
- keep decompression streaming/in-memory only for validation;
- delete/avoid partial oversized payloads.

## PASS interpretation

Q002 is a source-qualification stage, not a strategy test.

A venue may advance to the staged bulk calendar only if:

- source semantics are understood;
- validation does not reveal timestamp/price/size corruption;
- storage profile is compatible with staged collection;
- historical depth needed by the intended strategy family can be accessed without violating the 2 GB stage cap.

No Q002 result may modify R009/R003/R010/S002 or resurrect SC001-E001.