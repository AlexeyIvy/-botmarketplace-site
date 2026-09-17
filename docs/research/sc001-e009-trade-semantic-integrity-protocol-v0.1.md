# SC001-E009 — Trade Semantic Integrity Protocol v0.1

Date: 2026-09-17  
Status: **FROZEN AFTER E009 ACQUISITION VERIFY / BEFORE ANY E009 GROSS OUTPUT**

## Purpose

Qualify the 128 acquired E009 OKX trade archives without calculating the E009 volatility-normalized signal, returns, fees, execution PnL, asset-holdout results, or October Confirmation.

Parent exact state required:

- `E009_TRADE_ACQUISITION_VERIFY_PASS`;
- `verified_files = 128`;
- `verified_total_bytes = 419552195`.

## Frozen reconstruction semantics

Use the already-qualified OKX UTC-stitch rule:

`archive D + archive D+1 -> retain created_time in UTC [D 00:00, D+1 00:00)`.

For each Discovery instrument BTC, ETH, DOGE, ORDI, UNI, XRP, OP, BCH:

- source archive labels: `2024-08-31..2024-09-15`;
- reconstructed UTC target days: `2024-08-31..2024-09-14`;
- `2024-08-31` is boundary/warm-up only;
- performance days are `2024-09-01..14`;
- `2024-09-15` is D+1 source only.

## Hard source checks

For all 128 ZIPs require:

- ZIP CRC PASS;
- exactly one non-directory CSV member;
- exact expected header;
- exact expected instrument on every row;
- side in `{buy,sell}`;
- finite positive price and size;
- integer nonnegative timestamp and trade ID;
- nondecreasing timestamps;
- strictly increasing source trade IDs;
- no malformed rows.

## Hard reconstructed-day checks

For all 120 instrument-days require:

- at least one admitted row;
- exact UTC filter `[D,D+1)`;
- target timestamps nondecreasing;
- target trade IDs strictly increasing;
- target trade-ID gaps = 0;
- both taker sides observed;
- no instrument/schema/parse error.

Minute coverage is **diagnostic, not a completeness proof**. A day with fewer than 1440 active minute buckets is allowed only when all hard continuity checks above pass; it is labeled `SPARSE_BUT_ID_CONTINUOUS`, with exact missing minute indexes and maximum inter-trade gap recorded.

No forward-fill of empty 5-second strategy buckets is permitted later.

## Firewalls

This stage must not:

- calculate the E009 MAD volatility scale or Z-score;
- calculate the reversal trigger/target or gross/net returns;
- access SOL/FIL/LTC/SUI asset holdout bodies;
- access October Confirmation;
- repurpose August as promotional evidence;
- access L2;
- calculate PnL or infer historical execution specs.

## Exact tokens

Preflight:

`E009_TRADE_SEMANTIC_PREFLIGHT_PASS`

Full semantic qualification:

`E009_TRADE_SEMANTIC_INTEGRITY_PASS`

Expected summary:

- `source_files_qualified = 128 / 128`;
- `reconstructed_utc_days_qualified = 120 / 120`;
- `sparse_but_id_continuous_days = ...`;
- holdout/October/August-repurpose = false;
- strategy signal/PnL = false.
