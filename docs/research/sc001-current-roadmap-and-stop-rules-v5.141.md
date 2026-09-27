# SC001 Current Roadmap and Stop Rules v5.141

Date: 2026-09-27
Status: **B15-P1 W1 accumulation / B14-A DEFER_DATA / B13-C price-anchor dataset freeze PASS / S0 outcome analyzer frozen before returns**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.140.md`

## Price-anchor dataset freeze

Runner job:

`job_20260927T084007Z_e2824e69`

PASS:

`B13C_S0_PRICE_ANCHOR_DATASET_FREEZE_PASS`

Frozen file identities:
- extraction manifest SHA256 = `79db43a19249c8f56f886cf01616f3e56704d4a8fc8e5c5e03609254b2de1acf`;
- price anchors SHA256 = `5f84f40a91c3a7bc57bf3c4e878a53130ef696a28be162c014c10f8253223a1e`.

Counts:
- cluster rows = 1,905;
- valid price clusters = 1,793;
- missing entry = 25;
- missing exit = 75;
- missing both = 12;
- archive SHA count = 76.

No return was calculated.

## S0 outcome semantics frozen

Protocol:

`docs/research/sc001-b13c-s0-offline-outcome-computation-protocol-v0.1.md`

SHA256:

`b01ef69f6dcfe224f55841dd3ef4b9440bba8f76d3bb1a5f317bf6ae033e90a3`

Analyzer:

`research/sc001/sc001_b13c_s0_outcome_analyzer_v0_1.py`

SHA256:

`45724b5670caa1b264b1d8c455e9dc6271b4e9bb600320f25c25a76f28202cdb`

Frozen mathematics:
- `signed_reversal_bps = reversal_sign * 10000 * ln(P_exit/P_entry)`;
- pooled p25/median/p75 = deterministic type-7 linear quantiles;
- positive cluster iff signed reversal > 0;
- complete days = Sep20..Sep25 UTC;
- day assignment = UTC date of cluster_end_ms;
- positive day iff day median > 0.

Frozen gates:
- n >=100;
- pooled median >=30 bps;
- positive share >=55%;
- >=4/6 complete days positive.

## Hard boundary

Real signed returns remain unopened.

Before reading the frozen price-anchor dataset, run the no-input synthetic outcome-analyzer self-test.

Expected:

`B13C_S0_OUTCOME_ANALYZER_V01_SELF_TEST_PASS`

Only after PASS may the exact real outcome bundle be assembled and presented for a new explicit approval.

## Next state

`BUILD_AND_SEAL_B13C_S0_OUTCOME_ANALYZER_OFFLINE_SELFTEST`
