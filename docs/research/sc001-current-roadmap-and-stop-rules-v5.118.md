# SC001 Current Roadmap and Stop Rules v5.118

Date: 2026-09-26  
Status: **B15-P1 W1 accumulation continues / B14-A P0 real-data readout SEALED**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.117.md`

## B14-A P0 self-test

Official Runner self-test PASS:

`B14A_P0_READOUT_V01_SELF_TEST_PASS`

Job:

`job_20260926T201402Z_d6253469`

## Exact real-data bundle

Bundle ID:

`bundle_20260926T201527Z_e2422a4a`

SHA256:

`c4a04547462b2ca0eb92ae205d005ed5e7287e23a1cc620e5dfab229ad774a73`

Approval code:

`BM-C4A04547462B`

Package files: 7  
Package bytes: 29151  
Runtime: `offline-research-v1`

Read-only runtime inputs:
- `SC001_B14A_P0_20260925/collector_state.json`
- `SC001_B14A_P0_20260925/raw_trades.jsonl`
- `SC001_B14A_P0_20260925/connection_events.jsonl`

## Frozen outcome rule

The real-data readout may use only:
- T0 = 2026-09-25T07:30:00Z;
- first coactive one-second bucket among five frozen seconds;
- no carry-forward;
- no interpolation;
- chronologically last captured trade in selected second for each leg;
- BTC and ETH frozen pairs only;
- 50 bps hurdle.

State/subscription/gap validity is checked before any outcome is accepted.

Allowed result:
- STRONG 2/2;
- MIXED 1/2;
- WEAK 0/2;
- DEFER_DATA.

## Hard boundaries

No:
- alternative T0/window/expiry search;
- threshold tuning;
- convergence;
- settlePx analysis;
- execution model;
- PnL.

## Next state

`RUN_B14A_P0_REAL_DATA_READOUT_AFTER_EXPLICIT_APPROVAL`
