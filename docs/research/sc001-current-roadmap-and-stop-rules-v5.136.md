# SC001 Current Roadmap and Stop Rules v5.136

Date: 2026-09-27
Status: **B15-P1 W1 accumulation / B14-A DEFER_DATA / B13-C extractor self-test v0.1.2 ready for final seal**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.135.md`

## v0.1 failure

Job `job_20260927T075438Z_85b2eb56` failed before self-test body because `--mode` was mandatory.

No network/price/return/PnL access occurred.

## v0.1.1 pre-run review

A corrected launcher-compatible v0.1.1 bundle was sealed but intentionally **not run** because static contract review found a PASS-token naming mismatch between Python and freeze/spec.

No research semantics were affected.

## v0.1.2

Entrypoint:
`research/sc001/sc001_b13c_s0_streaming_price_anchor_extractor_v0_1_2.py`

SHA256:
`abb876276976198be65d049c6269d732dd24c5364c6c496bfeb5ed9d3f1f5be9`

Changes relative to v0.1.1:
- self-test PASS/REVIEW token names aligned with v0.1.1 contract.

Unchanged:
- 1,905 exact clusters;
- 76 archives;
- parser/extraction semantics;
- entry/exit buckets;
- network policy;
- S0 hypothesis/thresholds;
- no return/PnL in extraction stage.

Expected offline PASS:
`B13C_S0_PRICE_ANCHOR_EXTRACTOR_V011_SELF_TEST_PASS`

## Next state

`SEAL_FINAL_B13C_S0_PRICE_ANCHOR_EXTRACTOR_V012_OFFLINE_SELFTEST`
