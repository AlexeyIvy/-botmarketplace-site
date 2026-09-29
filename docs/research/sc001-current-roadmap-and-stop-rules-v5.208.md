# SC001 Current Roadmap and Stop Rules v5.208

Date: 2026-09-29
Status: **B15-P2 P0S 2025 HOLDOUT SOURCE CENSUS REVIEW / SOURCE-STRUCTURE AUDIT NEXT**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.206.md`

## Frozen original P0

Original B15-P2 P0 remains:
`DEFER_SOURCE_COVERAGE`

No same-94-event rescue is authorized.

## Fresh successor source-only attempt

Protocol:
`docs/research/sc001-b15p2-p0s-2025-holdout-source-census-protocol-v0.1.md`

Implementation freeze:
`docs/research/sc001-b15p2-p0s-2025-holdout-source-census-implementation-freeze-v0.1.json`

Live execution:
`job_20260929T152635Z_c6d1faee`

Canonical result:
`docs/research/sc001-b15p2-p0s-2025-holdout-source-census-result-v0.1.json`

SHA256:
`706cc5696e863ad7cd6e81efabe1629b2f9013e2ad9cbeacad46345f17ee1c36`

Review:
`docs/research/sc001-b15p2-p0s-2025-holdout-source-census-review-v0.1.md`

SHA256:
`b85b713ff4981ed00cbf8fb159e5059fdd64557917fe99d7b85d07c5d879fefb`

## Result

`B15P2_P0S_2025_HOLDOUT_SOURCE_CENSUS_REVIEW`

Source-only metrics:
- 154 closed in-scope 2025 USDT LinearPerpetual instruments;
- 120 admitted causal events;
- match coverage = 77.9220779221%;
- all 12 delivery months represented;
- one matched-source timestamp integrity issue;
- 34 unmatched symbols.

The frozen 80% match-coverage gate is not met and must not be relaxed.

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
- trading.

## Next allowed action

`DESIGN_OFFICIAL_BYBIT_2025_UNMATCHED_ANNOUNCEMENT_STRUCTURE_AUDIT_NO_PRICE`

The audit must:
1. use official Bybit announcement material only;
2. inspect source structure/metadata/body identity for the 34 unmatched instruments;
3. treat `dateTimestamp` as noncausal unless a new separately frozen source-semantics rule explicitly proves an admissible use;
4. preserve numeric `publishTime` as the causal announcement-time requirement;
5. keep the 80% census gate unchanged;
6. remain fully price-blind.

A new source-census rerun is allowed only after a corrected source parser is separately frozen and offline validated.

## Operational rate state

After the completed source-only live run, Test Executor daily usage reached 10/10. Do not bypass the executor or use another execution plane for a replacement run.
