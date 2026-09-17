# SC001-E007R1 — Trade Semantic Integrity Protocol v0.2

Date: 2026-09-17  
Status: **FROZEN AFTER DATA-QUALITY REVIEW / BEFORE ANY E007R1 GROSS-FEASIBILITY OUTPUT**  
Supersedes: `sc001-e007r1-trade-semantic-integrity-protocol-v0.1.md`

## 1. Why v0.2 exists

The first full semantic run stopped fail-closed on:

`DOGE-USDT-SWAP 2024-06-30: 1439/1440 UTC minute buckets`

No E007R1 trigger, response, gross return, fee, execution PnL, asset-holdout result, or August Confirmation output had been calculated when this occurred.

Review showed that v0.1 incorrectly promoted a BTC-specific diagnostic (`1440/1440 minute buckets observed`) into a universal multi-asset integrity requirement.

A minute with zero trades is not evidence of missing data when the admitted trade stream remains causally ordered and trade IDs remain contiguous. For a multi-asset trade tape, forcing at least one trade in every UTC minute would confuse **market inactivity** with **data loss**.

Therefore v0.2 corrects the semantic integrity rule before any strategy/economic output is viewed. It does not change E007/E007R1 strategy parameters, dates, assets, or economic gates.

## 2. Parent exact state

Required:

- `E007R1_TRADE_ACQUISITION_VERIFY_PASS`;
- `verified_files = 128`;
- `verified_total_bytes = 468108915`.

## 3. Reconstruction semantics unchanged

Historical OKX trade archives retain the previously qualified Q006R rule:

`archive D + archive D+1 -> retain created_time in UTC [D 00:00, D+1 00:00)`.

Discovery instruments remain:

BTC, ETH, DOGE, ORDI, UNI, XRP, OP, BCH.

Source archives remain 2024-06-30..2024-07-15 inclusive.

Reconstructed UTC target days remain:

- 2024-06-30 boundary/warm-up only;
- 2024-07-01..2024-07-14 Discovery performance;
- 120 instrument-days total.

## 4. Required source-archive checks

For all 128 ZIP files:

- ZIP CRC PASS;
- exactly one non-directory member;
- exact CSV header;
- exact expected instrument on every admitted row;
- side in `{buy,sell}`;
- finite positive price and size;
- nonnegative integer timestamp and trade ID;
- source timestamps nondecreasing;
- source trade IDs strictly increasing;
- no malformed rows.

## 5. Required reconstructed UTC-day checks

For all 120 reconstructed instrument-days:

- at least one admitted row;
- exact UTC filter `[D,D+1)`;
- target timestamps nondecreasing;
- target trade IDs strictly increasing;
- target trade-ID gaps = 0;
- duplicate/backward events = 0;
- both buy and sell taker sides observed;
- no instrument mismatch;
- no parse error.

### Minute coverage semantics

`minute_buckets_observed` is now **diagnostic**, not a hard integrity requirement.

For every target day the report must record:

- observed UTC minute bucket count;
- exact missing minute bucket indexes;
- maximum inter-trade gap in milliseconds;
- first and last admitted timestamps.

Classification:

- `COMPLETE_1440` when all minute buckets contain at least one trade;
- `SPARSE_BUT_ID_CONTINUOUS` when one or more minute buckets contain no trade but all hard integrity conditions above, especially zero trade-ID gaps, remain satisfied.

A sparse minute by itself is not a data-integrity failure. The later strategy engine must naturally treat any 5-second VWAP window with no trades as invalid under the already frozen E007 rule; it may not fabricate prices or forward-fill trades.

## 6. Boundary-day handling

2024-06-30 remains warm-up/boundary only and contributes no performance observation.

The same hard causal/ID integrity rules apply. Missing minute buckets are diagnostic only. The E007 engine later decides whether individual 5-second warm-up windows are valid from actual trade presence; no boundary trade is fabricated.

## 7. Fail-closed conditions

The stage still fails on any:

- CRC/member/header failure;
- malformed row;
- instrument mismatch;
- timestamp reversal;
- duplicate/backward trade ID;
- trade-ID gap in the reconstructed UTC stream;
- missing buy/sell side breadth;
- empty reconstructed day.

It no longer fails solely because a valid market has a minute with zero trades.

## 8. Firewalls

This stage must not calculate:

- the 80 bps displacement trigger;
- half-reversion targets;
- gross/net returns;
- fees/PnL;
- SOL/FIL/LTC/SUI holdout results;
- August Confirmation;
- L2 execution.

## 9. Exact tokens

Preflight:

`E007R1_TRADE_SEMANTIC_PREFLIGHT_PASS`

Full qualification:

`E007R1_TRADE_SEMANTIC_INTEGRITY_PASS`

Expected summary:

- `source_files_qualified = 128 / 128`;
- `reconstructed_utc_days_qualified = 120 / 120`;
- `sparse_but_id_continuous_days = N`;
- `asset holdout accessed = False`;
- `August Confirmation accessed = False`;
- `strategy signal/PnL calculated = False`.

## 10. Scientific interpretation

This amendment strengthens rather than weakens the test: it replaces an activity proxy with direct integrity evidence. Continuous trade IDs and causal ordering test whether trade records are missing; `1440/1440` only tests whether every minute happened to contain a trade.

Because the correction occurred before any E007R1 economic output, it does not constitute outcome-driven rescue tuning.
