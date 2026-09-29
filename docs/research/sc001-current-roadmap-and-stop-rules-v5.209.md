# SC001 Current Roadmap and Stop Rules v5.209

Date: 2026-09-29
Status: **B15-P2 P0S CROSS-TYPE SOURCE AUDIT PREFROZEN / EXECUTOR DAILY LIMIT WAIT**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.208.md`

## Original P0

The 2026 frozen P0 remains:
`DEFER_SOURCE_COVERAGE`

No same-evidence rescue is authorized.

## Fresh 2025 source-only successor state

Canonical 2025 source census:
`docs/research/sc001-b15p2-p0s-2025-holdout-source-census-result-v0.1.json`

SHA256:
`706cc5696e863ad7cd6e81efabe1629b2f9013e2ad9cbeacad46345f17ee1c36`

State:
`P0S_2025_HOLDOUT_SOURCE_CENSUS_REVIEW`

Observed:
- 154 in-scope closed USDT LinearPerpetual instruments;
- 120 admitted causal exact-symbol events;
- coverage 77.9220779221%;
- 34 unmatched symbols;
- one source timestamp integrity issue in a legacy BNXUSDT row;
- price/index/basis/returns/PnL remained closed.

## Next source hypothesis

The original source census used `type=delistings` on the official Bybit announcement index.

A source-only cross-type audit is now frozen at the protocol level to determine whether exact causal matches for the 34 unmatched symbols exist under other official Bybit announcement type partitions.

Protocol:
`docs/research/sc001-b15p2-p0s-2025-unmatched-announcement-index-cross-type-audit-protocol-v0.1.md`

SHA256:
`0bb6b61988041a54873dace0c68ce253e3dc246e7b4e197e5c8def61a0297e1d`

Implementation prefreeze:
`docs/research/sc001-b15p2-p0s-2025-cross-type-index-audit-implementation-prefreeze-v0.1.json`

Implementation:
`research/sc001/sc001_b15p2_p0s_2025_cross_type_index_audit_v0_1.py`

SHA256:
`2ab1203788747e857d1fb89a3e849e0d8eb47b6cdd000e13875cf683811fb2a2`

Design review:
`docs/research/sc001-b15p2-p0s-2025-cross-type-index-audit-design-review-v0.1.md`

## Frozen source rule

Still required:
- exact uppercase symbol identity;
- official Bybit source;
- numeric plausible-ms `publishTime`;
- `publishTime >= launchTime` when launchTime exists;
- `publishTime < deliveryTime`;
- 2025 holdout delivery window;
- unchanged 80% match-coverage gate.

`dateTimestamp` remains diagnostic only.

## Decision arithmetic

Current admitted = 120 of 154.

80% requires at least 124 admitted.

Therefore the audit needs at least 4 distinct valid causal recoveries to justify designing a corrected source parser. This is source-count arithmetic only and is not a price-outcome threshold.

## Firewalls

Still CLOSED:
- affected-contract price;
- observed index values;
- basis;
- returns;
- PnL;
- L1/L2;
- individual trades;
- funding;
- mark/premium/spot;
- external venues;
- article-body adaptive fallback in this audit version;
- trading.

## Execution state

Test Executor at the latest check:
- rolling-hour: 2 / 3;
- UTC-day: 10 / 10;
- running: 0.

Therefore no audit self-test or live run is launched now.

No alternate execution plane and no rate-limit bypass.

## Next allowed action

`WAIT_FOR_TEST_EXECUTOR_DAILY_SLOT_THEN_OFFLINE_VALIDATE_CROSS_TYPE_INDEX_AUDIT_V01`

After a legal slot opens:
1. refresh Test Executor to current canonical main;
2. run exactly one offline self-test;
3. if PASS, canonicalize the validation;
4. create a separate source-only one-run public-research approval;
5. re-check rate counters;
6. only then run the cross-type audit once.
