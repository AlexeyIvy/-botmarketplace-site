# SC001 — B13-C S0 Reusable-Block Extraction Addendum v0.1

Date: 2026-09-27
Status: **POSTMORTEM REUSABLE-BLOCK EXTRACTION COMPLETE**

Parent terminal result:

`B13C_S0_SIMPLE_REVERSAL_HEADROOM_REJECT`

## Strategy layer

Closed architecture:

`pure-side >=3-event liquidation cluster -> wait 1s -> 30s reversal`

Reason:

economic magnitude failure.

Observed median signed reversal:

`+1.3682 bps`

Frozen gross-headroom requirement:

`30 bps`

## Reusable layer

Retain:

`RB021 — Explicit pure-side liquidation-burst reversal state v0.1`

because the protected evidence still showed:
- positive-cluster share 55.884%;
- 5/6 positive complete-day medians;
- stable sign direction across most days.

Do not retain:
- 30-second standalone strategy;
- any post-hoc size threshold;
- any post-hoc symbol subset;
- any alternate horizon from this interval.

## Future use

RB021 may be tested prospectively as:
- R2 state;
- R3 confirmation/veto;
- R5 event-time execution context.

Any successor B13-C S1 must be frozen before fresh post-definition liquidation outcomes are read.
