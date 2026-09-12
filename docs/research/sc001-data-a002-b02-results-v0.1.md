# SC001-DATA-A002-B02 Results v0.1

Status: **PASS**  
Batch: **2023-Q3**  
Role: **DEV-DISCOVERY data qualification only**

## Result

All 5 frozen Binance BTCUSDT USD-M `aggTrades` days passed the frozen B02 data-integrity gates:

- 2023-07-12 — CPI
- 2023-07-26 — FOMC
- 2023-07-30 — ordinary weekend
- 2023-08-04 — NFP
- 2023-08-23 — ordinary weekday

The frozen preflight calendar SHA256 matched:

`e6bd2ddfee7d1ea8fbac89f9ae1aa3e038bbac83e0d624c98af14588bf0cbb7b`

No Validation or Final data were accessed. No strategy features or strategy P&L were calculated.

## Integrity summary

Across all five days:

- total aggTrades rows: **4,072,752**
- all 5 days: **1,440 / 1,440 minute buckets observed**
- invalid rows: **0**
- out-of-day rows: **0**
- timestamp-backwards events: **0**
- aggTrade ID gaps: **0**
- aggTrade duplicate/backwards events: **0**
- underlying trade-range overlaps/backwards events: **0**
- cross-selected-day order violations: **0**
- both `is_buyer_maker` states observed on every day

Official live checksum and Content-Length matched the frozen preflight identity for every file, and downloaded SHA256 values matched the frozen expected SHA256 values.

## Underlying trade-ID diagnostic

`underlying_gap_count_diagnostic` was nonzero but small relative to the number of aggTrades:

- 2023-07-12: 23
- 2023-07-26: 9
- 2023-07-30: 17
- 2023-08-04: 17
- 2023-08-23: 20
- total: **86**

These are diagnostic only. They are not treated as corruption because aggTrade IDs remain strictly contiguous and underlying trade-ID ranges never overlap or move backwards. The program must not infer exact global raw-trade counts from underlying trade-ID gaps without separate qualification.

## Storage / safety

- downloaded archive bytes: **53,592,159**
- total network bytes read: **53,592,654**
- workspace after outputs: **53,609,715 bytes**
- free storage after outputs: **68,738,560,000 bytes**
- frozen session cap: **200,000,000 bytes**
- frozen workspace cap: **200,000,000 bytes**
- minimum free-storage reserve: **4,000,000,000 bytes**

All safety constraints were respected.

## Combined DEV-DISCOVERY progress

B01 and B02 now provide **10 frozen DEV-DISCOVERY days** across 2023-Q2 and 2023-Q3. Combined aggTrades rows: **11,055,986**.

This is still data qualification, not evidence of strategy profitability.

## Decision

**PASS.** B02 is accepted as a clean DEV-DISCOVERY batch.

Next planned acquisition step is B03 (2023-Q4), after which acquisition must pause under the frozen Development Firewall so that the first serious sub-minute hypothesis can be designed and frozen before any B04/B05 DEV-confirmation access.
