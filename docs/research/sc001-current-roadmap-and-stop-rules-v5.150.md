# SC001 Current Roadmap and Stop Rules v5.150

Date: 2026-09-27
Status: **B15-P1 W1 accumulation / B14-A future retry wait / B13-C+B14-B terminal with reusable blocks / B15-P2 source-only census next**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.149.md`

## Terminal branches

B13-C S0:
`B13C_S0_SIMPLE_REVERSAL_HEADROOM_REJECT`
Reusable:
`RB021`

B14-B:
`B14B_REJECT_PERSISTENT_CARRY_STRUCTURAL`
Reusable:
`RB022`

No rescue tuning on their completed evidence.

## B15-P1

Unchanged:
W1 accumulation continues under collector operational freeze.

## B14-A

Unchanged:
Sep25 P0 remains DEFER_DATA.
Only a future prospective expiry may retry after transport ACK preflight.

## Next independent source-only branch

Selected:

`B15-P2 SCHEDULED DELISTING / FORCED CLOSE`

Stage:

`SOURCE_ONLY_EVENT_CENSUS_AND_SEMANTIC_AUDIT`

Reason:
official event clocks and forced-close semantics are directly observable before outcomes, while B15-P3 fixed redemption access is not broadly operationally available under the current architecture.

## B15-P2 allowed now

- official announcement/API source access;
- event identity;
- publish time;
- delisting UTC;
- lead time;
- revision/postponement tracking;
- forced-close/settlement semantics;
- source breadth/opportunity rate.

## B15-P2 forbidden now

- affected-contract price;
- external-reference price;
- basis;
- pre/post-delisting return;
- PnL;
- winner-event selection.

## Next state

`DESIGN_B15P2_SOURCE_ONLY_EVENT_CENSUS_PROTOCOL_BEFORE_ANY_PRICE_ACCESS`
