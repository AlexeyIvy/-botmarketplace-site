# SC001-DATA-Q004R — Semantic OKX L2 Replay Qualification v0.1

Status: pre-result freeze.

## Purpose
Q004R is an implementation-correction stage for Q004. Q004 established that the four frozen OKX L2 archive prefixes are accessible by HTTP Range and that the underlying payload is newline-delimited JSON, but its schema-comparison logic treated JSON lines as CSV and therefore produced a misleading `NEEDS_REVIEW`. Q004R does not rewrite Q004; it independently verifies semantic replay.

## Frozen source dates
- 2023-04-15
- 2024-01-15
- 2025-01-15
- 2026-07-15

The archive URLs must be reused from `SC001_DATA_Q003/sc001_data_q003_report.json`. No new dates may be substituted after seeing results.

## Network and storage safety
- HTTP Range only: first 8 MiB per epoch.
- Expected normal network budget: <= 40 MiB total.
- Hard session download cap: 2,000,000,000 bytes.
- Hard workspace cap: 2,000,000,000 bytes.
- Minimum free-storage reserve: 4,000,000,000 bytes.
- Maximum decompressed prefix held in memory: 64 MiB per epoch.
- If the server ignores Range and returns anything other than HTTP 206, close the response without reading the large body.
- Never save or extract a full OKX L2 archive in Q004R.

## Frozen semantic assumptions to test
Each complete JSON line should represent an L2 message with mandatory keys:
`instId`, `action`, `ts`, `asks`, `bids`.

Allowed actions: `snapshot`, `update`.

Each book level must be exactly `[price, size, orders]` with positive price, non-negative size, and a non-negative integer-like order count.

Replay rule:
- `snapshot` replaces the local book state.
- `update` changes only listed price levels.
- `size == 0` removes the price level.
- otherwise the listed price level is replaced with the supplied `(size, orders)` state.

## Mandatory PASS conditions per epoch
- at least 100 complete JSON records parsed from the bounded prefix;
- first parsed action is `snapshot`;
- at least one `snapshot` and one `update`;
- no invalid complete JSON lines;
- no missing mandatory keys;
- no wrong instrument IDs;
- no invalid actions;
- no backward timestamps;
- no malformed levels;
- no empty-book states after applying a valid record;
- no crossed state (`best_bid >= best_ask`) after applying a valid record.

Deleting an already absent level is recorded diagnostically but is not itself a failure because replay is idempotent at price-level semantics.

## Cross-epoch coherence gate
All four epochs must pass and expose the same semantic signature: first action, key-set family, level shape, and instrument ID.

## Interpretation boundary
A Q004R PASS establishes that sampled OKX L2 prefixes can be deterministically replayed at price-level semantics and can support spread/depth/imbalance analysis and conservative taker-execution modeling.

It does **not** establish exact maker queue position, MBO priority, individual-order queue rank, or strategy profitability.

## Research boundary
- No strategy signal generation.
- No P&L.
- No live-trading authorization.
- No modification of frozen R009/R003/R010/S002 branches.
- No expansion to bulk L2 acquisition until Q004R is reviewed.
