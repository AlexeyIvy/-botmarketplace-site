# SC001 — C7-D1 Multi-Asset L2 Body Integrity / 1s Top-of-Book Normalization v0.1

Date: 2026-09-18
Status: **FROZEN BODY/SCHEMA NORMALIZATION AFTER C7-S0 RULE FREEZE**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c7-d0-multi-asset-l2-metadata-pass-result-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.14.json`;
- `docs/research/sc001-c7-s0-multi-asset-spread-headroom-sentinel-v0.1.md`.

## 1. Purpose

Download/open the exact seven 2024-02-12 historical OKX 400-level L2 bodies, verify integrity, and normalize per-asset causal 1-second top-of-book states.

D1 must not calculate quoted spread or C7 eligibility.

## 2. Exact bodies

For each frozen instrument:

`<INST>-L2orderbook-400lv-2024-02-12.tar.gz`

Expected exact Content-Length must match the C7-D0 parent report.

## 3. Acquisition constraints

- sequential downloads only;
- no more than one heavy body transfer at a time;
- per-file cap = 1 GiB;
- total cap = 3 GiB;
- minimum free-disk reserve = 15 GiB;
- exact trusted historical URL identity;
- HEAD size must still match D0 before GET;
- local exact-size files may be reused.

## 4. Body integrity

For each body require:

- tar.gz opens;
- exactly one regular JSONL member;
- exact instrument identity;
- first action snapshot;
- actions only snapshot/update;
- timestamps nondecreasing;
- asks/bids arrays valid;
- each level = [price,size,order_count];
- finite positive price;
- nonnegative size/order_count;
- zero-size deletion implies zero order count;
- duplicate side price within record invalid;
- reconstructed book never empty/crossed;
- delete-missing level invalid.

## 5. Frozen 1-second normalization

For each asset:

- exact UTC grid 00:00:00..23:59:59;
- causal as-of most recent fully applied L2 record <= grid boundary;
- freshness <=1000 ms;
- no future interpolation.

Write normalized CSV:

`normalized/<ASSET>_top1_1s.csv`

Columns exactly:

- second_id;
- l2_ts_ms;
- best_bid;
- best_ask;
- best_bid_size;
- best_ask_size.

Do not calculate spread in D1.

## 6. D1 PASS gates

Per asset require:

- exact source identity/size;
- archive SHA256 recorded;
- zero integrity errors;
- valid sampled seconds >=80,000;
- active UTC hours =24;
- normalized prices/sizes finite positive;
- normalized seconds strictly increasing.

D1 PASS requires all 7 assets PASS.

## 7. Exact terminal states

PASS:

`C7_D1_MULTI_ASSET_L2_INTEGRITY_PASS`

REVIEW:

`C7_D1_MULTI_ASSET_L2_INTEGRITY_REVIEW`

REVIEW is data/implementation only.

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

Only after exact D1 PASS may the already-frozen C7-S0 spread/headroom sentinel be implemented and run.
