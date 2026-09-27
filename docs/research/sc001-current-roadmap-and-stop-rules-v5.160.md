# SC001 Current Roadmap and Stop Rules v5.160

Date: 2026-09-27
Status: **B15-P2 PARSER-RESILIENCE V0.1.1 OFFLINE SELFTEST PASS / PREPARE NETWORKED V0.1.2 BOUNDARY**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.159.md`

## Binding governance

`docs/research/sc001-midcourse-research-strategy-audit-and-governance-amendment-v0.2.md`

remains binding.

## Exact self-test result

The sealed parser-resilience v0.1.1 bundle completed successfully:

- bundle: `bundle_20260927T180555Z_bc1ff4ec`
- bundle SHA256: `5aab363e11e57dab6992292176e677542519d0a4ce31ae8be69df2ac7fd252ba`
- approval: `BM-5AAB363E11E5`
- job: `job_20260927T180943Z_cfc1dfaf`
- exit code: `0`
- package integrity: `PASS`
- stderr: empty
- observed token:
  `B15P2_BYBIT_DELISTING_SOURCE_CENSUS_V011_SELF_TEST_PASS`

Canonical result:

`docs/research/sc001-b15p2-bybit-delisting-source-census-v011-offline-selftest-result-v0.1.json`

## What was validated

The self-test explicitly covered the failure class exposed by live Bybit data plus adjacent likely parser hazards:

- legacy/unrelated rows without `publishTime`;
- exact in-scope missing `publishTime` -> fail-closed REVIEW;
- no `dateTimestamp` causal fallback;
- exact-symbol matching;
- current listing-episode lower bound via `launchTime`;
- post-delivery notice exclusion;
- plausible millisecond timestamps;
- bool/string pre-listing normalization;
- PASS and DEFER fixtures;
- type-7 lead-time quantiles.

The live networking path itself remains untested by the offline Runner.

## Research consequence

This is still source-parser engineering validation only.

No:
- mechanism verdict;
- economic outcome;
- evidence maturity change;
- contamination change;
- reusable-block change

occurred.

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
v0.1.1 source parser self-test PASS; next step is to freeze a networked v0.1.2 host boundary using these exact bytes.

## Next state

`PREPARE_NETWORKED_B15P2_SOURCE_ONLY_V012_BOUNDARY_NO_EXECUTION`
