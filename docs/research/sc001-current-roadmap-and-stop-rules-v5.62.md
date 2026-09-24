# SC001 Current Roadmap and Stop Rules v5.62

Date: 2026-09-24  
Status: **B15-P1 STAGE C PASS / 15-SECOND NON-PRICE COLLECTOR DESIGN SEALED**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.61.md`

## Stage C

`B15_P1_FULL_CYCLE_EDGE_TO_FILL_STRUCTURAL_PREFLIGHT_PASS`

Frozen structural floor remains:
- 61 bps before transfer costs/headroom;
- 71 bps including minimum economic headroom but before transfer costs.

## Collector design

Fast lane:
- cadence = 15 seconds;
- phase-aligned to UTC epoch multiples of 15s;
- 12-second per-venue request deadline;
- no catch-up burst;
- no overlapping fast request per venue;
- Bybit and OKX source calls independent/concurrent;
- no carry-forward across a failed source poll.

Endpoints:
- Bybit `/v5/asset/coin/query-info`;
- OKX `/api/v5/asset/currencies`.

Designed fast rate:
- 0.066666... request/s per venue;
- Bybit endpoint limit reference = 5/s => 75x safety factor;
- OKX endpoint limit reference = 6/s => 90x safety factor.

Slow account-fee lane:
- refresh every 6 hours;
- stale after 8 hours;
- max 1 request/s per venue;
- exact pair binding;
- fast lane priority.

Operational guards:
- heartbeat <= 30 seconds;
- systemd required before launch;
- restart backoff = 15 seconds;
- process/reboot gaps explicit;
- no missed-poll backfill;
- append-only raw/normalized evidence;
- atomic persistent state;
- poll hash chain + daily hash manifest;
- storage warning below 20 GiB or 25%;
- fail-closed stop below 10 GiB or 15%;
- no automatic protected-evidence deletion.

Protected collection:
- open-ended background collection;
- first source-only operational review after 7 complete UTC days;
- no price/PnL during protected collection.

## Sealed design-preflight

Bundle:

`bundle_20260924T101653Z_04b3927c`

SHA256:

`abd2de854537e8d886e472a46fcf5bb97eee0c4407b15cf406e3733b54a154d0`

Approval code:

`BM-ABD2DE854537`

State:

`SEALED_RUN_PENDING`

The preflight is offline and performs no exchange calls.

## Boundary

A PASS authorizes only:

`PREPARE_B15P1_COLLECTOR_IMPLEMENTATION_SELF_TEST`

It does not authorize:
- collector launch;
- price collection;
- spread/PnL;
- live execution.

## Next state

`RUN_B15P1_15_SECOND_NONPRICE_COLLECTOR_DESIGN_PREFLIGHT_AFTER_USER_APPROVAL`
