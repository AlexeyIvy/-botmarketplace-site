# SC001 Current Roadmap and Stop Rules v5.151

Date: 2026-09-27
Status: **B15-P1 W1 accumulation / B14-A future retry wait / B13-C+B14-B terminal with reusable blocks / B15-P2 Bybit source-only census frozen**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.150.md`

## Terminal evidence retained

B13-C S0:
`B13C_S0_SIMPLE_REVERSAL_HEADROOM_REJECT`
Reusable block:
`RB021`

B14-B:
`B14B_REJECT_PERSISTENT_CARRY_STRUCTURAL`
Reusable block:
`RB022`

No same-interval rescue tuning.

## Active background state

B15-P1:
W1 accumulation continues under operational freeze.

B14-A:
waits for a future prospective expiry after transport repair/preflight.

## New independent source-only branch

`B15-P2 SCHEDULED PERPETUAL DELISTING / FORCED CLOSE`

First event-census venue:

`BYBIT`

Why:
- public announcements API exists;
- public closed-instrument metadata exists;
- perpetual `deliveryTime` gives an event clock;
- source/event census can be done without opening prices.

## Frozen census window

`2026-01-01T00:00:00Z <= deliveryTime < 2026-09-27T00:00:00Z`

This historical interval is source-only. No price outcome is authorized.

## Exact event scope

Admit:
- Bybit;
- LinearPerpetual;
- USDT quote;
- Closed;
- deliveryTime inside window;
- exclude isPreListing=true identities;
- exact symbol match to official pre-event delisting announcement.

Primary unit:

`BYBIT x EXACT_USDT_PERPETUAL_SYMBOL x DELIVERY_TIME`

## Frozen source gates

PASS requires:
- >=5 closed in-scope perpetuals;
- >=5 admitted events;
- announcement match coverage >=80%;
- every admitted event has positive causal notice lead;
- >=3 distinct delivery calendar months.

Expected real terminal states:
- `B15P2_BYBIT_DELISTING_SOURCE_CENSUS_PASS`;
- `B15P2_BYBIT_DELISTING_SOURCE_CENSUS_DEFER`;
- `B15P2_BYBIT_DELISTING_SOURCE_CENSUS_REVIEW`.

## Implementation

Protocol:
`docs/research/sc001-b15p2-bybit-delisting-source-only-event-census-protocol-v0.1.md`

Implementation:
`research/sc001/sc001_b15p2_bybit_delisting_source_census_v0_1.py`

SHA256:
`da047f6dba6881fdfa04db187616b851e1ed35af7af9b33ed6921daed807f8ef`

Static review corrections completed before seal:
- exact alphanumeric symbol boundaries;
- pre-market-only exclusion when `isPreListing=true`.

## Hard firewall

This stage may not read:
- affected-contract price;
- external-reference price;
- index level;
- basis;
- spread;
- PnL.

## Next state

`SEAL_B15P2_BYBIT_SOURCE_CENSUS_OFFLINE_SELFTEST`
