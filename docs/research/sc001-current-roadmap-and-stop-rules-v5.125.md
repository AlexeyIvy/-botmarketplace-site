# SC001 Current Roadmap and Stop Rules v5.125

Date: 2026-09-26  
Status: **B15-P1 W1 accumulation / B14-A DEFER_DATA with root cause closed / B13-C S0 source-only cluster census prepared**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.124.md`

## B15-P1

Unchanged:
`W1_7_COMPLETE_UTC_DAY_OBSERVATION_ACCUMULATING`

## B14-A

Sep25 P0 remains:
`B14A_P0_DEFER_DATA`

Root cause is closed as OKX WebSocket request-id grammar error. No retroactive reconstruction.

## B13-C source state

Protected prospective source census:
- 32,381 normalized explicit liquidation events;
- 7.5958 days;
- 12/12 symbols;
- invalid=0;
- connection gap fraction ~=0.0413%;
- process gap fraction ~=0.00277%.

## B13-C price archive metadata state

Official Bybit public directories currently contain all frozen symbol archives from Sep19 through Sep25.

The Sep26 archive is not yet published for any of the 12 while the UTC day remains open.

Current naive availability:
- present = 84/96 full-calendar symbol-day files;
- pending = 12/96 (Sep26).

No price body has been opened for B13-C S0.

## Source-ingestion optimization

Binding amendment:

`docs/research/sc001-b13c-s0-source-ingestion-amendment-v0.1.md`

First run the frozen source-only cluster census. It will enumerate only exact symbol-date price archives actually touched by eligible clusters.

This is allowed because it uses no price or return.

## Cluster census implementation

`research/sc001/sc001_b13c_s0_source_only_cluster_census_v0_1.py`

SHA256:

`601252728e8fa7caf2d9c467d99e61296268a78879a42323725b67bac223db5b`

It reads:
- collector state;
- connection ledger;
- event JSONL Sep19-Sep26.

It does not read:
- price archives;
- returns;
- liquidation sizes for selection;
- per-symbol performance;
- PnL.

## Next state

`BUILD_AND_SEAL_B13C_S0_CLUSTER_CENSUS_OFFLINE_SELFTEST`
