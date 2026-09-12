# SC001-DATA-A002-B01 — Results v0.1

Status: `PASS`

Stage: data qualification only. No strategy/P&L, no strategy features, no VALIDATION/FINAL access, no maker-queue inference, no L2 execution model.

## Scope

- Venue: Binance USD-M Futures
- Symbol: BTCUSDT
- Dataset: aggTrades
- Split: DEV only
- Frozen batch: 2023-Q2
- Frozen calendar SHA256: `e6bd2ddfee7d1ea8fbac89f9ae1aa3e038bbac83e0d624c98af14588bf0cbb7b`
- Dates: 2023-04-12 (CPI), 2023-04-23 (ordinary weekend), 2023-05-01 (ordinary weekday), 2023-05-05 (NFP), 2023-06-14 (FOMC)

## Batch result

All 5/5 frozen days passed. Total parsed aggTrades rows: 6,983,234.

For every day:

- live checksum matched the frozen preflight SHA256;
- live HEAD Content-Length matched the frozen preflight size;
- downloaded ZIP SHA256 matched the expected checksum;
- ZIP/CSV structure validated;
- exactly one expected CSV member was present;
- all parsed rows were inside the target UTC day;
- all 1,440 minute buckets were observed;
- timestamps were monotonic nondecreasing;
- aggTrade IDs were strictly contiguous with zero gaps, duplicates, or backwards moves;
- underlying raw-trade ID ranges never overlapped or moved backwards;
- invalid rows = 0;
- both buyer-maker states were observed.

## Per-day metrics

| Date | Type | Rows | Agg ID gaps | Timestamp backwards | Invalid rows | Out-of-day | Underlying gap diagnostic |
|---|---|---:|---:|---:|---:|---:|---:|
| 2023-04-12 | CPI | 1,406,402 | 0 | 0 | 0 | 0 | 562 |
| 2023-04-23 | Ordinary weekend | 929,918 | 0 | 0 | 0 | 0 | 19 |
| 2023-05-01 | Ordinary weekday | 1,723,347 | 0 | 0 | 0 | 0 | 194 |
| 2023-05-05 | NFP | 1,667,536 | 0 | 0 | 0 | 0 | 345 |
| 2023-06-14 | FOMC | 1,256,031 | 0 | 0 | 0 | 0 | 1,214 |

## Important diagnostic boundary

`underlying_gap_count_diagnostic` is non-zero on all five days (2,334 gaps total), while aggTrade IDs themselves are perfectly contiguous and underlying ID ranges never overlap or move backwards. Under the frozen B01 protocol this is diagnostic only, not a FAIL condition.

Interpretation must remain conservative: the first/last underlying trade IDs carried by adjacent aggTrades must not be assumed to form one globally contiguous raw-trade sequence without a separate semantic proof. Do not use `last_trade_id - first_trade_id + 1` as an exact raw-trade-count proxy across adjacent aggregates unless that assumption is independently validated.

This does not weaken the qualification of the aggTrades stream itself: the archived aggregate IDs are complete and contiguous for each selected day.

## Safety

- Network bytes read: 91,819,571
- Workspace after outputs: ~91.84 MB
- Session cap: 300 MB
- Workspace cap: 300 MB
- Per-file cap: 256 MB
- Minimum free-storage reserve: 4 GB
- Free bytes after outputs: 68,797,640,704

## Decision

`SC001-DATA-A002-B01 = PASS`.

The B01 acquisition/validation design is accepted for reuse on the next frozen DEV quarterly batch, subject to preserving all gates and the diagnostic-only treatment of underlying raw-trade ID gaps.

No strategy hypothesis or P&L is authorized by this result alone.
