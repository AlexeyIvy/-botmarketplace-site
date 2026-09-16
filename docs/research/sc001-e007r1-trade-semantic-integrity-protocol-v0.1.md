# SC001-E007R1 — Trade Semantic Integrity Protocol v0.1

Date: 2026-09-16  
Status: **FROZEN BEFORE E007R1 GROSS-FEASIBILITY OUTPUT**

## Purpose

Qualify the 128 acquired OKX trade archives for E007R1 without calculating the E007 signal, response, fees, execution PnL, asset-holdout results, or August Confirmation.

Parent exact state required:

- `E007R1_TRADE_ACQUISITION_VERIFY_PASS`;
- `verified_files = 128`;
- `verified_total_bytes = 468108915`.

## Frozen reconstruction semantics

Historical OKX daily trade archives use the previously qualified Q006R UTC-stitch rule:

`archive D + archive D+1 -> retain created_time in UTC [D 00:00, D+1 00:00)`.

For each of the 8 Discovery instruments:

- source archives: 2024-06-30 through 2024-07-15 inclusive;
- reconstructed UTC target days: 2024-06-30 through 2024-07-14 inclusive;
- 2024-06-30 is boundary/warm-up only;
- performance days remain 2024-07-01 through 2024-07-14;
- archive 2024-07-15 is D+1 source only.

## Required source-archive checks

For all 128 ZIP files:

- ZIP CRC PASS;
- exactly one non-directory member;
- exact CSV header `instrument_name,trade_id,side,price,size,created_time`;
- every admitted row has exact expected instrument;
- side in `{buy,sell}` case-insensitive;
- finite positive price and size;
- integer nonnegative timestamp;
- integer trade id;
- source timestamp nondecreasing;
- source trade id strictly increasing;
- no malformed rows.

## Required reconstructed UTC-day checks

For all 120 reconstructed instrument-days (8 instruments x 15 UTC days):

- at least one admitted row;
- exact UTC filter `[D,D+1)`;
- target timestamp nondecreasing;
- target trade id strictly increasing;
- target trade-id gaps = 0;
- duplicate/backward events = 0;
- both buy and sell taker sides observed;
- all 1,440 UTC minute buckets observed;
- no instrument mismatch;
- no parse error.

A failure is fail-closed and blocks E007R1 gross-feasibility.

## Firewalls

This stage must not:

- calculate the 80 bps displacement trigger;
- calculate half-reversion targets;
- calculate gross or net returns;
- calculate fees/PnL;
- access SOL/FIL/LTC/SUI asset-holdout bodies;
- access August Confirmation;
- access L2;
- alter E007/E007R1 parameters.

## Exact tokens

Preflight:

`E007R1_TRADE_SEMANTIC_PREFLIGHT_PASS`

Full semantic qualification:

`E007R1_TRADE_SEMANTIC_INTEGRITY_PASS`

Expected summary includes:

- `source_files_qualified = 128 / 128`;
- `reconstructed_utc_days_qualified = 120 / 120`;
- `asset holdout accessed = False`;
- `August Confirmation accessed = False`;
- `strategy signal/PnL calculated = False`.
