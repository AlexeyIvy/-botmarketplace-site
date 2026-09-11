# SC001 — Free Multi-Venue Data Acquisition Protocol v0.1

**Project:** BotMarketplace / BotMarketplace.store  
**Branch:** SCALPING RESEARCH / SC001  
**Date:** 2026-09-11  
**Status:** FROZEN BEFORE MICROSTRUCTURE STRATEGY TESTING  
**Parent results:** `docs/research/sc001-e001-results-v0.1.md`

---

## 1. Purpose

SC001-E001 falsified the first 1-hour extreme-move mean-reversion hypothesis. The next step is **not** to rescue E001. The purpose of this protocol is to acquire data whose temporal and execution resolution is genuinely appropriate for future scalping research.

No paid dataset is authorized at this stage.

The acquisition branch remains independent from R009/R003/R010/S002 and cannot change any frozen rule, forward clock, venue record, or decision in those branches.

No real-money deployment is authorized.

---

## 2. Source audit — current free/public options

### Binance public archive

Official public bulk archive: `data.binance.vision` / `binance/binance-public-data`.

Useful free data:

- daily and monthly files;
- USD-M futures 1-minute klines;
- individual trades;
- aggregate trades;
- kline fields include volume, quote volume, number of trades and taker-buy aggregates;
- SHA-256 checksum files are published alongside archives.

Long-history role for SC001:

- best/easiest **multi-year 1-minute backbone**;
- stable static URLs and checksums;
- suitable for broad multi-regime signal research and causal bar execution at minute resolution.

Limitation:

- the official bulk archive located in this audit does not provide a comparable multi-year historical L2/order-book archive for the required period;
- therefore Binance 1m/trade history alone is not sufficient to reconstruct historical spread, depth or queue position exactly.

### Bybit public archive

Official Bybit documentation points to downloadable archived historical public trades. The public directory `https://public.bybit.com/trading/BTCUSDT/` contains daily compressed BTCUSDT trade CSV files continuously from 2020-03-25 through at least 2026-09-10 as of this audit.

Useful role for SC001:

- long independent venue history;
- tick-level public trades;
- strong candidate for signed/taker-flow, trade-intensity and short-horizon cross-venue replication;
- convenient daily files.

Limitation:

- no equivalently long official historical L2 archive was located in this audit;
- exact historical spread/depth cannot be reconstructed from trades alone.

### OKX historical market data

Official OKX historical-data page currently advertises:

- tick-level trade history from September 2021;
- candlestick history from July 2023;
- perpetual funding history from March 2022;
- high-resolution L2 order-book history from March 2023.

OKX added a public batch `Get historical market data` endpoint in September 2025 supporting trade history, candlesticks, funding and 50/400/5000-level order-book modules with daily/monthly aggregation. In August 2026 its maximum query range was reduced to 10 days for daily aggregation and 10 months for monthly aggregation.

Useful role for SC001:

- strongest free source found for **true historical microstructure**;
- can support contemporaneous spread, depth, imbalance and execution-friction research on the same venue as trades.

Limitation:

- L2 files can be extremely large;
- full-history phone download is not justified before schema/size qualification;
- module/file schema and practical Android transfer throughput must be validated first.

---

## 3. Acquisition decision

No single venue is selected post hoc as a P&L winner. The sources are assigned different research roles **before any new microstructure strategy P&L is inspected**.

### Layer A — long minute backbone

**Venue:** Binance USD-M  
**Instrument:** BTCUSDT perpetual  
**Data:** 1m klines  
**Target historical window:** 2020-01-01 through 2026-08-31 using completed monthly archives where available.

Purpose:

- multi-regime 1m history;
- initial short-horizon family screens;
- time-of-day/volatility/regime diagnostics;
- no claim of exact historical bid/ask execution.

### Layer B — long tick-trade replication

**Venue:** Bybit  
**Instrument:** BTCUSDT linear perpetual trade archive  
**Data:** individual public trades  
**Coverage available:** from 2020-03-25 onward.

Purpose:

- signed taker-flow / trade-intensity features;
- reconstruction of 1s/5s/1m trade bars;
- independent cross-venue falsification of signal mechanisms.

Bulk retention policy will be decided only after measuring one fixed-day file size and schema. Full raw tick history is not automatically downloaded to a phone.

### Layer C — execution/microstructure layer

**Venue:** OKX  
**Instrument:** BTC-USDT-SWAP  
**Data:** trades + historical L2, initially 50 levels  
**Coverage available:** trades from Sep-2021; L2 from Mar-2023.

Purpose:

- historical best bid/ask;
- spread distribution;
- top-of-book and depth imbalance;
- liquidity / slippage stress;
- true microstructure-family experiments on OKX itself.

Do **not** download the full L2 archive before the qualification gate.

---

## 4. Q001 — source qualification gate

Before bulk acquisition, run a deterministic one-day qualification sample.

**Fixed qualification date:** `2025-01-15 UTC`.

This date is selected before inspecting any SC001 microstructure P&L and is used only for schema/access/storage qualification.

Q001 actions:

1. Binance: download BTCUSDT USD-M 1m daily kline archive + checksum.
2. Binance: download BTCUSDT USD-M daily aggregate-trade archive + checksum.
3. Bybit: download `BTCUSDT2025-01-15.csv.gz` from the official public trade archive.
4. OKX: query the public historical-market-data endpoint for the fixed day and record which documented/available modules return metadata for `BTC-USDT-SWAP`; do not bulk-download L2 during the probe.
5. Record HTTP status, compressed size, SHA-256, schema/header/first rows, row count where practical, and any errors.

No strategy statistics or P&L may be calculated in Q001.

---

## 5. Qualification PASS/FAIL gates

### Binance PASS

- 1m archive downloads without authentication;
- checksum verifies;
- 1,440 expected minute slots are present or any discrepancy is explicitly explained;
- timestamps parse monotonically;
- OHLCV/trade-count/taker-buy fields are usable.

### Bybit PASS

- fixed-day trade archive downloads without authentication;
- gzip is valid;
- timestamp, price, size and aggressor/taker-side semantics can be identified and validated;
- timestamps are monotonic after any documented sorting/deduplication step.

### OKX PASS

- the public history interface can be accessed without paid data;
- at least trade and historical L2 metadata/download capability for BTC-USDT-SWAP is confirmed;
- file/schema size is measurable enough to design a phone-safe collector.

If OKX L2 cannot be accessed programmatically from the user's network/account region, use the official historical-data download page as a fallback without changing the research calendar.

---

## 6. Storage discipline

Android storage is a binding implementation constraint.

Rules:

- qualification samples are retained intact;
- no full multi-year tick/L2 download before measuring real compressed size;
- bulk raw files must be resumable and checksum/hash tracked;
- derive compact 1s/5s/1m research tables where possible;
- do not delete verified raw data automatically in v0.1;
- if later raw-file deletion is proposed after derivation, require an explicit separate decision and preserve source URL + SHA-256 + processing manifest.

---

## 7. Anti-overfitting boundary

Data-source choice must not be made by subsequent strategy P&L.

- Binance is the long-minute backbone because of free depth of history and archive ergonomics.
- Bybit is the long tick-trade replication source because of its free daily trade archive.
- OKX is the microstructure source because it provides historical L2.

These roles are frozen before new strategy testing.

A future strategy may be tested on more than one venue, but venue disagreement must be preserved rather than choosing the prettier result.

---

## 8. Next action

Run `SC001-DATA-Q001` on Android/Pydroid. Upload the generated qualification report and summary. Only after reviewing actual schemas, sizes and OKX access should the full collector calendar and storage policy be frozen.