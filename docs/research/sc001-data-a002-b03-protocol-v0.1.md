# SC001-DATA-A002-B03 Protocol v0.1

Status: **FROZEN BEFORE DOWNLOAD**

Purpose: acquire and validate the third and final `DEV-DISCOVERY` Binance BTCUSDT USD-M `aggTrades` batch for 2023-Q4. This stage is data qualification only: no strategy features, no P&L, no VALIDATION/FINAL.

## Frozen role

B01 (2023-Q2) and B02 (2023-Q3) are already qualified. B03 completes the 15-day `DEV-DISCOVERY` layer. After B03, acquisition must STOP before B04/B05. The next action is to design/freeze the first serious sub-minute discovery hypothesis using only B01+B02+B03.

## Frozen dates

- 2023-10-06 — EVENT/NFP
- 2023-10-25 — ORDINARY_WEEKDAY
- 2023-12-03 — ORDINARY_WEEKEND
- 2023-12-12 — EVENT/CPI
- 2023-12-13 — EVENT/FOMC

Frozen calendar SHA256: `e6bd2ddfee7d1ea8fbac89f9ae1aa3e038bbac83e0d624c98af14588bf0cbb7b`.

Expected compressed bytes: `91,449,749`.

## Identity freeze

For each date, the collector must re-check live `.CHECKSUM` and `Content-Length` against the A002-PREFLIGHT frozen values before accepting the archive. Any change is an ERROR/REVIEW condition; do not silently accept a republished object.

## Integrity gates per day

- ZIP CRC clean;
- exactly one expected CSV member;
- expected 7-column aggTrades schema;
- positive finite price and quantity parsed with `Decimal`;
- all rows inside the target UTC day;
- nondecreasing timestamps;
- strict contiguous `agg_trade_id` sequence;
- underlying trade-ID ranges non-overlapping/non-backward;
- all 1,440 minute buckets observed;
- both maker-flag values observed;
- zero malformed rows.

`underlying_gap_count_diagnostic` remains diagnostic only and must not be promoted post hoc to a hard gate.

## Safety

- session download cap: 200,000,000 bytes;
- workspace cap: 200,000,000 bytes;
- single file cap: 256,000,000 bytes;
- minimum free-storage reserve: 4,000,000,000 bytes;
- max uncompressed member: 2,000,000,000 bytes.

## Firewall

`strategy_pnl_calculated=false`, `strategy_features_calculated=false`, `validation_or_final_accessed=false` are mandatory. B03 is `DEV_DISCOVERY_ONLY`.

## Decision

PASS requires all five frozen days to pass every hard gate and no cross-selected-day forward-order violation. A PASS completes the acquisition side of DEV-DISCOVERY and triggers a STOP before B04/B05.