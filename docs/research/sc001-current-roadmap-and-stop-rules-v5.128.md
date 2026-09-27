# SC001 Current Roadmap and Stop Rules v5.128

Date: 2026-09-27  
Status: **B15-P1 W1 accumulation / B14-A DEFER_DATA / B13-C S0 real event-only cluster census SEALED**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.127.md`

## B15-P1

Unchanged:

`W1_7_COMPLETE_UTC_DAY_OBSERVATION_ACCUMULATING`

## B14-A

Unchanged:

`B14A_P0_DEFER_DATA`

## B13-C S0 self-test

PASS:

`B13C_S0_SOURCE_ONLY_CLUSTER_CENSUS_V01_SELF_TEST_PASS`

Job:

`job_20260927T064523Z_8278bc96`

## Exact real event-only census bundle

Bundle ID:

`bundle_20260927T064727Z_cb2d998a`

SHA256:

`92b1863f8fdce42654da2586de2037daf43698af086ac54258d269251d9a63e2`

Approval code:

`BM-92B1863F8FDC`

Runtime:
`offline-research-v1`

Package files:
8

Package bytes:
36109

Runtime read-only inputs:
10

The real census reads:
- collector state;
- connection ledger;
- normalized liquidation event files Sep19-Sep26.

## Allowed outputs

Only:
- exact-fingerprint unique event count;
- aggregate raw cluster count;
- aggregate under-minimum/mixed-side/gap-censored counts;
- aggregate eligible cluster count;
- whether the frozen >=100 sample gate is ready;
- exact required symbol-date Bybit public-trade archive identities.

## Forbidden

No:
- price body access;
- return calculation;
- per-symbol performance ranking;
- liquidation-size thresholding;
- threshold tuning;
- execution/PnL.

## Consequence

If eligible cluster count >=100:
`QUALIFY_EXACT_REQUIRED_PRICE_ARCHIVES`

If below 100:
`B13C_S0_DEFER_SAMPLE`

Neither state is a profitability result.

## Next state

`RUN_B13C_S0_REAL_EVENT_ONLY_CLUSTER_CENSUS_AFTER_EXPLICIT_APPROVAL`
