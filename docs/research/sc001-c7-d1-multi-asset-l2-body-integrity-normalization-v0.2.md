# SC001 — C7-D1 Multi-Asset L2 Integrity / 1s Top-of-Book Normalization v0.2

Date: 2026-09-18
Status: **FROZEN LEADING-UPDATE REPLAY REPAIR AFTER DOGE SEMANTIC DIAGNOSTIC / NO SPREAD OUTCOME**
Scope: `SCALPING RESEARCH / SC001`
Supersedes: `sc001-c7-d1-multi-asset-l2-body-integrity-normalization-v0.1.md`

Parents:

- `docs/research/sc001-c7-d1-v0.1-doge-leading-action-review-v0.1.md`;
- `docs/research/sc001-c7-d1-doge-leading-update-diagnostic-result-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.14.json`;
- `docs/research/sc001-c7-s0-multi-asset-spread-headroom-sentinel-v0.1.md`.

## 1. Trigger

C7-D1 v0.1 returned:

`C7_D1_MULTI_ASSET_L2_INTEGRITY_REVIEW`

with six of seven assets passing.

Only DOGE failed before normalization because the archive began with `update` rather than `snapshot`.

Read-only diagnostic established:

- leading updates before first snapshot = `3609`;
- first snapshot record index = `3610`;
- first snapshot timestamp = `1707696060009`;
- first snapshot UTC ≈ `2024-02-12T00:01:00.009Z`.

No spread or C7 eligibility was calculated.

## 2. Frozen replay-semantics repair

For any historical L2 archive:

1. scan records from the beginning;
2. validate instrument, action, timestamp monotonicity, side-array shape and level syntax;
3. if records before the first snapshot are `update`, do **not** apply them to an empty book;
4. discard those leading updates from book reconstruction;
5. initialize the reconstructed book only when the first full `snapshot` arrives;
6. all later `snapshot` records remain full resyncs;
7. all later `update` records mutate the reconstructed book causally;
8. grid seconds before the first snapshot remain missing;
9. no synthetic/backfilled initial book is permitted.

If no snapshot exists in the archive, the asset is REVIEW.

## 3. Why this is a source-semantics repair, not strategy tuning

The repair changes no C7 market rule.

Unchanged:

- seven-asset universe;
- date 2024-02-12;
- exact source bodies;
- 1-second grid;
- 1000 ms freshness limit;
- >=80,000 valid sampled seconds per asset;
- 24 UTC-hour coverage;
- all already-frozen C7-S0 spread/headroom rules.

No spread value has yet been inspected.

## 4. Efficient inherited-pass rule

C7-D1 v0.2 may inherit the six v0.1 PASS assets without re-replaying their ~1.5 GB of bodies only if it re-verifies locally:

- v0.1 terminal status is REVIEW;
- v0.1 assets_passed = 6;
- DOGE is the sole failed asset;
- each inherited source archive exists and matches the v0.1 stored byte size and SHA256;
- each inherited normalized CSV exists and matches the v0.1 stored byte size and SHA256;
- each inherited normalization had >=80,000 valid sampled seconds and 24 UTC hours.

DOGE must be reprocessed under the new leading-update rule.

## 5. DOGE source re-verification

Before replaying DOGE:

- re-resolve the exact trusted historical URL;
- require HEAD size still equals the frozen D0 Content-Length;
- local exact-size body may be reused;
- compute SHA256 and record it.

No new asset/date/source is permitted.

## 6. DOGE normalization

Write a new repaired normalized file:

`~/sc001_data/SC001_C7_D1_V02_MULTI_ASSET_L2/normalized/DOGE_top1_1s.csv`

Columns unchanged:

- second_id;
- l2_ts_ms;
- best_bid;
- best_ask;
- best_bid_size;
- best_ask_size.

Require:

- leading updates skipped, not applied;
- first snapshot found;
- zero integrity/replay errors after snapshot;
- valid sampled seconds >=80,000;
- active UTC hours =24.

## 7. Master PASS semantics

PASS:

`C7_D1_V02_MULTI_ASSET_L2_INTEGRITY_PASS`

requires:

- six inherited v0.1 PASS assets re-verified by identity;
- DOGE repaired normalization PASS;
- total assets passed = 7/7.

REVIEW:

`C7_D1_V02_MULTI_ASSET_L2_INTEGRITY_REVIEW`

remains a data/implementation state only.

## 8. Firewalls

Must remain false:

- quoted_spread_calculated;
- c7_asset_eligibility_calculated;
- maker_order_simulated;
- fill_model_calculated;
- queue_model_calculated;
- adverse_selection_outcome_calculated;
- pnl_calculated;
- promotional_alpha_accessed.

## 9. Consequence of PASS

Only after exact v0.2 PASS may the already-frozen C7-S0 spread/headroom sentinel be implemented and run.
