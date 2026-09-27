# SC001 Current Roadmap and Stop Rules v5.137

Date: 2026-09-27
Status: **B15-P1 W1 accumulation / B14-A DEFER_DATA / B13-C extractor v0.1.2 offline self-test SEALED**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.136.md`

## Final corrected offline self-test candidate

Bundle ID:

`bundle_20260927T080056Z_82f5be3a`

SHA256:

`2b093def1156a8dcf2667b9ea7d53d54e628f1874c93d89a7f8aa9a60ae72c74`

Approval code:

`BM-2B093DEF1156`

Runtime:
`offline-research-v1`

Inputs:
none

Files:
17

Bytes:
1,054,805

Entrypoint:
`research/sc001/sc001_b13c_s0_streaming_price_anchor_extractor_v0_1_2.py`

SHA256:
`abb876276976198be65d049c6269d732dd24c5364c6c496bfeb5ed9d3f1f5be9`

Expected PASS:
`B13C_S0_PRICE_ANCHOR_EXTRACTOR_V011_SELF_TEST_PASS`

## What v0.1.2 fixes

Relative to the failed v0.1:
- Runner launcher positional contract supported;
- self-test becomes safe default when `--mode` absent.

Relative to sealed-but-not-run v0.1.1:
- PASS/REVIEW token naming aligned with freeze/spec.

No research semantics changed.

## Firewalls

This bundle:
- has no network inputs;
- cannot open real price bodies;
- cannot calculate returns;
- cannot calculate threshold outcome;
- cannot calculate PnL.

## Next state

`RUN_B13C_S0_PRICE_ANCHOR_EXTRACTOR_V012_OFFLINE_SELFTEST_AFTER_EXPLICIT_APPROVAL`
