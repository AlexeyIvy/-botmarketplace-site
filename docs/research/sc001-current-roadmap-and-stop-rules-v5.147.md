# SC001 Current Roadmap and Stop Rules v5.147

Date: 2026-09-27
Status: **B15-P1 W1 accumulation / B14-A P0 DEFER_DATA / B13-C S0 terminal REJECT with RB021 retained / B14-B offline self-test SEALED**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.146.md`

## Reusable-block discipline

Binding policy:

`docs/research/sc001-terminal-experiment-reusable-block-extraction-policy-v0.1.md`

B13-C reusable state:

`RB021 — Explicit pure-side liquidation-burst reversal state v0.1`

Parent S0 remains terminal and cannot be rescued on the same interval.

## B14-B exact offline self-test bundle

Bundle ID:

`bundle_20260927T091925Z_389f482b`

SHA256:

`563919504e09b4c2ee866f45a71cabe776c72d40fbd5c36d0f46c8df5418aad4`

Approval code:

`BM-563919504E09`

Runtime:

`offline-research-v1`

Inputs:
none

Package files:
7

Package bytes:
37,021

Entrypoint:
`research/sc001/sc001_b14b_persistent_multisettlement_funding_carry_v0_1.py`

SHA256:
`cb288810ef8871ea1de3bfe9decf6e372cb525c1c62d0123969d4f7f459793f4`

Expected PASS:

`B14B_PERSISTENT_CARRY_V01_SELF_TEST_PASS`

## What the self-test validates

- Runner launcher contract;
- one-to-one matched settlement pairing for the signal;
- three same-sign causal confirmations;
- positive and negative venue-direction mapping;
- signal settlement excluded from future cycle cashflow;
- exact seven-calendar-day hold;
- all realized venue funding events in the hold counted;
- non-overlapping cycles per symbol;
- funding-history coverage gate;
- 50 bps structural headroom gate;
- synthetic SURVIVE fixture;
- synthetic REJECT fixture.

It has no network and cannot access the fresh Jul-Sep 2026 funding values.

## After PASS

Freeze a separate networked launch contract for the fresh funding window:

`2026-07-01 .. 2026-09-27 exclusive`

The real funding screen will still use no prices, basis or PnL.

## Next state

`RUN_B14B_PERSISTENT_CARRY_OFFLINE_SELFTEST_AFTER_EXPLICIT_APPROVAL`
