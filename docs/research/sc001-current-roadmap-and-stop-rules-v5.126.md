# SC001 Current Roadmap and Stop Rules v5.126

Date: 2026-09-26  
Status: **B15-P1 W1 accumulation / B14-A DEFER_DATA / B13-C S0 cluster-census offline self-test SEALED**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.125.md`

## B15-P1

Unchanged:
`W1_7_COMPLETE_UTC_DAY_OBSERVATION_ACCUMULATING`

## B14-A

Unchanged:
`B14A_P0_DEFER_DATA`

Transport root cause is known and no Sep25 price reconstruction is allowed.

## B13-C S0

Price outcome remains closed.

Current public archive metadata:
- all 12 frozen symbols have daily Bybit trade archives Sep19-Sep25;
- Sep26 remains unpublished while the UTC day is still open.

A source-only cluster census implementation has been frozen to enumerate exact required price archive symbol-date pairs without reading price.

## Exact offline self-test bundle

Bundle ID:

`bundle_20260926T214337Z_a25b8bff`

SHA256:

`f6500de6a30e2d97430a29ec047ea85552c284d46f7e7917a794e198f4f2361e`

Approval code:

`BM-F6500DE6A30E`

Runtime:
`offline-research-v1`

Inputs:
none

Files:
5

Bytes:
29732

Expected PASS:

`B13C_S0_SOURCE_ONLY_CLUSTER_CENSUS_V01_SELF_TEST_PASS`

## Self-test coverage

Synthetic validation covers:
- fingerprint deduplication;
- <=5s per-symbol cluster continuation;
- >=3 distinct-event minimum;
- pure-side exclusion;
- source gap/restart censoring with +/-5s padding;
- exact required symbol-date archive derivation;
- price/return/PnL firewalls.

No real B13-C event data or price data are opened by this bundle.

## After PASS

Prepare a separate immutable real source-only cluster-census bundle using:
- collector state;
- connection ledger;
- event JSONL Sep19-Sep26.

The real census still cannot read price or return.

## Next state

`RUN_B13C_S0_CLUSTER_CENSUS_OFFLINE_SELFTEST_AFTER_EXPLICIT_APPROVAL`
