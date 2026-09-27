# SC001 Current Roadmap and Stop Rules v5.158

Date: 2026-09-27
Status: **B15-P2 PUBLISHTIME ROOT CAUSE IDENTIFIED / PARSER-RESILIENCE V0.1.1 FROZEN / OFFLINE SELFTEST PENDING**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.157.md`

## Binding governance

`docs/research/sc001-midcourse-research-strategy-audit-and-governance-amendment-v0.2.md`

remains binding.

No price/economic methodology changes are introduced.

## Root cause

The improved host wrapper preserved the actual live exception:

`RuntimeError: announcement publishTime missing`

Bybit documents `publishTime` today, while its changelog records that this field was added to Get Announcement in March 2024. The observed live response contained at least one announcement row without `publishTime`; the age/relevance of that specific row was not yet established.

The research implementation required numeric `publishTime` while normalizing every returned announcement row, before establishing whether that row was relevant to an in-scope 2026 exact symbol.

That global parser requirement was too strict.

## Correct causal rule

`publishTime` remains the only allowed causal publication timestamp.

`dateTimestamp` is NOT substituted for it.

The corrected sequencing is:

1. historical endpoint rows may be parsed even when `publishTime` is absent;
2. exact-symbol and listing-episode relevance is determined;
3. an exact in-scope relevant row without numeric `publishTime` causes fail-closed `REVIEW`;
4. unrelated legacy rows without `publishTime` do not abort the census.

Thus causal standards are not relaxed.

## Proactive engineering hardening

The v0.1.1 implementation additionally freezes:

- plausible millisecond timestamp validation;
- `launchTime` lower-bound protection against previous listing episodes;
- robust string/boolean pre-listing handling;
- defensive pagination de-duplication;
- safe pagination when announcement `total` is absent;
- transient-only HTTP/network retries;
- immediate deterministic schema/retCode failure;
- persisted source-only REVIEW report on live exceptions.

## Frozen implementation

`research/sc001/sc001_b15p2_bybit_delisting_source_census_v0_1_1.py`

SHA256:

`7da36641ed71e0195320f0cc7cc389d629d4f843a646f64c41c1739fc0cd6b35`

Implementation freeze:

`docs/research/sc001-b15p2-bybit-delisting-source-census-implementation-freeze-v0.1.1.json`

Offline self-test spec:

`docs/research/sc001-b15p2-bybit-delisting-source-census-offline-selftest-spec-v0.1.1.json`

No network retry is authorized yet.

## Strategy review

This remains a source-parser engineering correction.

No economic/source-feasibility verdict, contamination change, reusable-block change, evidence-maturity change, or mechanism change occurred.

Therefore:

`NO STRATEGY REVIEW TRIGGER`

## Current branch states

B15-P1:
W1 accumulation / operational freeze unchanged.

B14-A:
`B14A_P0_DEFER_DATA` retained.

B13-C:
terminal S0 / RB021 retained; no same-evidence rescue.

B14-B:
terminal / RB022 retained; no same-window rescue.

B15-P2:
parser-resilience v0.1.1 frozen; exact sealed offline self-test must pass before another networked attempt.

## Next state

`PREPARE_AND_SEAL_B15P2_V011_OFFLINE_SELFTEST_NO_EXECUTION`
