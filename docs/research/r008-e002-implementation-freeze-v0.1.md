# R008-E002 Implementation Freeze v0.1

**Date:** 2026-09-09  
**Status:** frozen before first E002 result  
**Protocol:** `docs/research/r008-e002-long-history-validation-protocol-v0.1.md`

This note freezes implementation details that were intentionally left operationally ambiguous in the protocol.

## Data gate

For the Blockchain.com daily market-price reference series:

- use `timespan=all`;
- request `sampled=false`;
- keep only parseable positive prices;
- normalize timestamps to UTC calendar dates;
- keep the last observation if duplicate UTC dates appear;
- do not interpolate missing dates.

On and after 2013-01-01, strategy P&L is calculated only if:

1. at least **98%** of consecutive cleaned observations are exactly one calendar day apart; and
2. no consecutive-observation gap exceeds **7 calendar days**.

If either gate fails, output `DATA_REDESIGN` and do not calculate strategy P&L.

## State initialization

- state begins at the earliest positive cleaned source observation;
- first observation initializes the running peak;
- no manually supplied prior ATH is used;
- reporting slices do not reset state.

## Return/accounting convention

Keep E001 convention exactly:

- reference-price percentage return from t-1 to t;
- target decided from state at t-1 becomes held weight for return t;
- first target allocation cost is charged at the first executable return step;
- thereafter transaction cost is charged only on absolute target-weight changes;
- no drift-rebalance turnover is charged in E002;
- cash return remains zero.

This is still an architecture-level proxy. A later implementation-realism experiment is mandatory after any E002 historical PASS.

## Prospective STATIC15 benchmark

STATIC15 is fixed at exactly **15% BTC / 85% cash** because it is the midpoint of the architecture's possible 10-20% target exposure range. It is not set equal to the observed E001 average exposure.

## Crisis event windows

Same convention as E001:

- event begins on the first return after the first threshold-breach observation;
- for a closed event, event diagnostic ends on the first return after the ATH-reset observation where available;
- unresolved final event ends at the data endpoint and is labeled `OPEN_CENSORED`.

No result-dependent changes to these conventions are permitted after E002 output is observed.
