# SC001 Current Roadmap and Stop Rules v5.161

Date: 2026-09-27
Status: **B15-P2 NETWORKED SOURCE-ONLY V0.1.2 BOUNDARY FROZEN / AWAITING EXPLICIT APPROVAL**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.160.md`

## Binding governance

`docs/research/sc001-midcourse-research-strategy-audit-and-governance-amendment-v0.2.md`

remains binding.

## Offline prerequisite

The exact parser-resilience implementation passed sealed offline validation:

- implementation SHA256:
  `7da36641ed71e0195320f0cc7cc389d629d4f843a646f64c41c1739fc0cd6b35`
- self-test job:
  `job_20260927T180943Z_cfc1dfaf`
- PASS:
  `B15P2_BYBIT_DELISTING_SOURCE_CENSUS_V011_SELF_TEST_PASS`

Canonical result:

`docs/research/sc001-b15p2-bybit-delisting-source-census-v011-offline-selftest-result-v0.1.json`

## Networked v0.1.2 boundary

Frozen host wrapper:

`scripts/research/run-b15p2-bybit-delisting-source-census-v0.1.2.sh`

SHA256:

`e9727b13cdd5677a369275f2bc433a611849242b41ee38a29826a11548f80c9e`

Launch contract:

`docs/research/sc001-b15p2-networked-bybit-source-only-event-census-launch-contract-v0.1.2.json`

Approval code:

`BM-E9727B13CDD5`

Networked execution is NOT authorized by this roadmap update.

## Additional wrapper safeguards

Before the next live call the wrapper now:

- verifies exact implementation/freeze/self-test SHA values;
- reruns the exact staged synthetic self-test;
- accepts all three frozen terminal states: PASS / DEFER / REVIEW;
- preserves log, exit code and launch marker;
- shows source-integrity and exception diagnostics;
- uses unique v0.1.2 attempt paths;
- bounds the transient systemd job to 900 seconds.

## Research firewalls

Still forbidden:
- price;
- external-reference price;
- index;
- basis;
- spread;
- returns;
- PnL;
- event outcome ranking;
- outcome-driven horizon search;
- threshold rescue;
- trading.

## Strategy review

Preparation of this boundary is implementation work only.

`NO STRATEGY REVIEW TRIGGER`

A meaningful source-level DEFER/REVIEW may trigger the Strategy Manager after the run.

## Current branch states

B15-P1:
W1 accumulation / operational freeze unchanged.

B14-A:
`B14A_P0_DEFER_DATA` retained.

B13-C:
terminal S0 / RB021 retained.

B14-B:
terminal / RB022 retained.

B15-P2:
networked source-only v0.1.2 boundary frozen and unrun.

## Next state

`AWAIT_EXPLICIT_APPROVAL_FOR_NETWORKED_B15P2_V012_BM-E9727B13CDD5`
