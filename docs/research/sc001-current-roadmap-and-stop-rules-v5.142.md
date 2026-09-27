# SC001 Current Roadmap and Stop Rules v5.142

Date: 2026-09-27
Status: **B15-P1 W1 accumulation / B14-A DEFER_DATA / B13-C dataset freeze PASS / outcome analyzer synthetic self-test SEALED**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.141.md`

## Price-anchor dataset freeze

PASS:

`B13C_S0_PRICE_ANCHOR_DATASET_FREEZE_PASS`

Frozen identities:
- extraction manifest SHA256 = `79db43a19249c8f56f886cf01616f3e56704d4a8fc8e5c5e03609254b2de1acf`;
- price anchors SHA256 = `5f84f40a91c3a7bc57bf3c4e878a53130ef696a28be162c014c10f8253223a1e`;
- valid price clusters = 1,793.

No return has yet been calculated.

## Frozen outcome semantics

Protocol SHA256:

`b01ef69f6dcfe224f55841dd3ef4b9440bba8f76d3bb1a5f317bf6ae033e90a3`

Analyzer SHA256:

`45724b5670caa1b264b1d8c455e9dc6271b4e9bb600320f25c25a76f28202cdb`

Frozen statistics:
- signed reversal = stored reversal_sign * 10,000 * ln(exit/entry);
- type-7 p25/median/p75;
- positive iff >0;
- daily grouping by UTC date of cluster_end_ms;
- complete days Sep20..Sep25;
- sample >=100;
- median >=30 bps;
- positive share >=55%;
- >=4/6 positive complete-day medians.

## Exact synthetic self-test bundle

Bundle ID:

`bundle_20260927T084255Z_e8542274`

SHA256:

`9bc4936a61dabe2806049ff098bb85409232017fd619e27bae9fc6ad15f30fe2`

Approval code:

`BM-9BC4936A61DA`

Runtime:
`offline-research-v1`

Inputs:
none

Files:
5

Bytes:
22,876

Expected PASS:

`B13C_S0_OUTCOME_ANALYZER_V01_SELF_TEST_PASS`

The self-test uses synthetic prices only and cannot open the real 1,793 valid-price outcomes.

## Next state

`RUN_B13C_S0_OUTCOME_ANALYZER_SYNTHETIC_SELFTEST_AFTER_EXPLICIT_APPROVAL`
