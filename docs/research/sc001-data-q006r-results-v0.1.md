# SC001-DATA-Q006R Results v0.1

Status: **PASS**  
Stage: `SC001-DATA-Q006R-OKX-UTC-STITCH`

## Result

The five frozen 2024-Q1 OKX `BTC-USDT-SWAP` target UTC days were reconstructed successfully by combining archive `D` with archive `D+1` and filtering strictly to UTC `[D, D+1)`.

All five target days passed the frozen data-repair gates.

## Key findings

The historical OKX daily trade archives are aligned to a 16:00 UTC boundary for the sampled dates (consistent with a UTC+8 daily archive convention), not to UTC midnight. Therefore an exact UTC calendar day cannot be represented by a single archive filename alone.

The frozen repair rule is:

`archive D + archive D+1 -> retain only trades with created_time in UTC [D 00:00, D+1 00:00)`.

This finding is data engineering only and was established before any OKX TFI feature, future-return label, strategy P&L, or formal Validation/Final access.

## Reconstructed target days

- 2024-01-05: PASS; admitted rows `1,121,598`; 1440/1440 UTC minute buckets; trade ID gaps `0`.
- 2024-01-14: PASS; admitted rows `585,515`; 1440/1440 UTC minute buckets; trade ID gaps `0`.
- 2024-01-31: PASS; admitted rows `975,333`; 1440/1440 UTC minute buckets; trade ID gaps `0`.
- 2024-02-12: PASS; admitted rows `1,413,275`; 1440/1440 UTC minute buckets; trade ID gaps `0`.
- 2024-02-13: PASS; admitted rows `1,224,315`; 1440/1440 UTC minute buckets; trade ID gaps `0`.

Total admitted target-day trades: `5,320,036`.

Across all five target days:

- source parse errors: 0;
- source timestamp reversals: 0;
- source trade-ID duplicate/backward events: 0;
- target timestamp reversals: 0;
- target trade-ID duplicate/backward events: 0;
- target trade-ID gaps: 0;
- instrument mismatches: 0;
- both buy and sell sides observed;
- all 1,440 UTC minute buckets observed.

## Safety

- network bytes read: `31,828,515`;
- workspace bytes after outputs: `31,854,341`;
- no strategy feature or future-return calculation;
- no P&L;
- no 2024-Q2 OKX access;
- no formal Validation/Final access.

## Decision

Q006R qualifies the stitched OKX Q1 trade stream for a direct same-formula replication of the frozen E002 5-second trade-flow continuation screen.

The next experiment must preserve the E002 economic mechanism and timing:

- 5-second non-overlapping TFI bucket;
- buyer-taker positive / seller-taker negative;
- 5-second future transaction-price response;
- 100 ms primary latency;
- 250 ms stress latency;
- 500 ms diagnostic latency;
- no threshold tuning;
- no event/day exclusions;
- no P&L or L2 execution claim.

The OKX public-trades semantics define `side` as the trade side of the taker and `sz` for SWAP as contract count. For a single instrument, a constant contract multiplier would cancel in the normalized TFI ratio, so the direct screen can use `price * size` weighting without making a P&L/notional-capacity claim.
