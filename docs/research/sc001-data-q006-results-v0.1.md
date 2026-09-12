# SC001-DATA-Q006 Results v0.1

Status: **SCHEMA_REVIEW**  
Stage: `SC001-DATA-Q006-OKX-TRADES`  
Scope: five frozen 2024-Q1 OKX `BTC-USDT-SWAP` trade archives  
Role: data/schema qualification only

## Outcome

All five exact-date ZIP archives were downloaded successfully with the exact HEAD sizes frozen by Q005R. The total network/archive bytes were `30,080,404` and all five archive SHA-256 hashes were recorded.

The stage did **not** reach row-level PASS because the frozen Q006 alias map did not recognize the observed OKX timestamp column name `created_time`. It also did not recognize `instrument_name` as the instrument column. Therefore the parser intentionally stopped each day at `SCHEMA_REVIEW` before calculating row counts, minute coverage, signal features, future returns, or P&L.

Observed common CSV header on all five archives:

`instrument_name, trade_id, side, price, size, created_time`

Resolved by Q006 before stop:
- `trade_id` -> column 1;
- `side` -> column 2;
- `price` -> column 3;
- `size` -> column 4.

Unresolved by the original frozen alias map:
- `timestamp` because `created_time` was absent from timestamp aliases;
- `instrument` because `instrument_name` was absent from instrument aliases.

## Important temporal finding

The first observed `created_time` samples reveal a more important engineering issue than the alias typo alone.

Examples:
- file labelled `2024-01-05` begins with sample timestamps around `1704384000189`, i.e. `2024-01-04 16:00:00.189 UTC`;
- file labelled `2024-01-14` begins around `2024-01-13 16:00 UTC`;
- file labelled `2024-01-31` begins around `2024-01-30 16:00 UTC`;
- file labelled `2024-02-12` begins around `2024-02-11 16:00 UTC`;
- file labelled `2024-02-13` begins around `2024-02-12 16:00 UTC`.

This strongly indicates that OKX daily trade archives are packaged on a non-UTC daily boundary consistent with UTC+8 local-day labelling. This is also consistent with the earlier Q005 discovery response returning both the requested-date archive and the following-date archive for one UTC-day query.

This temporal interpretation is not yet treated as fully qualified from samples alone. The repair stage must prove actual first/last timestamp coverage from complete archives before using these data for any E002 replication.

## Consequence for same-venue replication

The exact-date archive alone must **not** be treated as a complete UTC calendar day. To reconstruct a frozen UTC target day `D`, the repaired data stage must inspect and, if necessary, stitch the relevant portions of:

- archive labelled `D`; and
- archive labelled `D+1`;

then retain only timestamps in `[D 00:00:00 UTC, D+1 00:00:00 UTC)`.

This is an objective data-engineering correction, not a strategy change. No E002 metric has been seen on OKX, so the repair does not contaminate the same-venue hypothesis test.

## Firewall state

- strategy features calculated: **NO**;
- future returns calculated: **NO**;
- strategy P&L calculated: **NO**;
- 2024-Q2 OKX accessed: **NO**;
- formal Validation/Final accessed: **NO**.

## Safety

- network bytes read: `30,080,404`;
- workspace after outputs: about `30.10 MB`;
- free storage after outputs: about `68.39 GB`;
- all frozen caps respected.

## Decision

Do not run the OKX TFI replication yet.

Create a repaired data-only stage `SC001-DATA-Q006R` that:
1. recognizes `created_time` and `instrument_name` explicitly;
2. reuses the five already-downloaded exact-date archives after SHA verification;
3. discovers/downloads only the five corresponding `D+1` neighbor archives under hard caps;
4. proves full timestamp coverage and reconstructs each frozen UTC target day from the two local-day archives;
5. validates row schema, target instrument, buy/sell side, timestamp ordering, trade-ID monotonicity diagnostics, and 1,440 UTC minute buckets;
6. calculates no signal, future-return label, or P&L.

Only a clean Q006R PASS authorizes the same-venue E002 replication.
