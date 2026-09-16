# SC001-E008 — Passive Maker Executable Protocol v1.0

Date: 2026-09-16  
Status: **FROZEN BEFORE FIRST PROMOTIONAL E008 P&L**

Prerequisites:
- E008_DATA_INVENTORY_PASS
- E008_STALE_LATCH_MODEL_PASS
- E008_QUEUE_SIMULATOR_SYNTHETIC_PASS
- E008_QUEUE_SIMULATOR_MECHANICAL_PASS
- date freeze v1.0

## 1. Instrument / objective

OKX BTC-USDT-SWAP. Base E008 tests conservative top-of-book passive spread capture with no TFI, FLOW_IMPULSE, compression, basis or displacement feature.

## 2. Queue and stale semantics

Preserve all previously frozen lower-bound rules:
- initial queue-ahead = full displayed size at our resting price;
- only causally compatible aggressive transaction volume advances queue;
- cancellations / size decreases give zero queue progress;
- size additions at our price are added ahead;
- same-ms book/trade ambiguity gives zero fill credit;
- price-level disappearance or book movement alone never implies fill;
- partial fills explicit;
- book age >5000 ms triggers stale latch and cancels live orders;
- only a later full snapshot restores trust;
- exact FIFO is never claimed.

## 3. Strategy state

Inventory is bounded to {-1,0,+1} contract.

Flat state:
- maintain one BUY at current best bid and one SELL at current best ask, each quantity 1 contract;
- each order uses its own conservative queue state;
- first actual fill creates inventory; opposite quote is submitted for cancellation with frozen cancel latency below;
- if both sides causally fill before cancellation completes, inventory may return to zero and both fills are retained.

Inventory +1:
- no new BUY entry quote;
- maintain only a SELL passive exit quote at current best ask.

Inventory -1:
- no new SELL entry quote;
- maintain only a BUY passive exit quote at current best bid.

Maximum absolute inventory = 1 contract.

## 4. Latency / quoting

Primary order-placement latency: 250 ms.
Primary cancel latency: 250 ms.
Stress: 500 ms placement/cancel latency.

Orders are activated only on a trusted, uncrossed book observed causally at activation time. A would-be marketable order is rejected rather than converted to taker.

A live maker quote is cancelled/replaced when:
- it is no longer at the same-side best quote;
- TTL reaches 30 seconds;
- stale latch activates;
- strategy state changes after a fill.

Replacement begins only after the relevant cancel latency and then the placement latency; queue position resets to the full newly displayed size.

## 5. Inventory risk / forced exit

Maximum inventory holding time = 60 seconds from first entry fill.

If inventory is still nonzero at 60 seconds, force-flat with a taker proxy:
- decision at exact max-hold timestamp;
- execution = first causally observed trade at or after decision +250 ms, within 5 seconds;
- stress uses +500 ms;
- if no proxy exists, cycle is unresolved and the UTC day fails the unresolved-inventory gate.

No overnight inventory. No new flat-state cycle after 23:58:00 UTC.

## 6. Funding firewall

To avoid unmodeled perpetual funding transfers, do not initiate a new flat-state cycle during [T-120s, T+120s) around 00:00, 08:00 and 16:00 UTC. Existing inventory still follows the 60-second max-hold rule and must be flat before funding boundary; otherwise unresolved/fail-closed.

## 7. Fees

Frozen regular-user fee reference:
- maker: +0.020% = 2.0 bps per maker fill;
- taker: +0.050% = 5.0 bps per taker fill;
- no VIP tier, no maker rebate rescue.

For a completed cycle:
- gross cycle edge is inventory-direction signed entry-to-exit price return;
- subtract actual modeled fee type on each fill;
- maker-maker cycle carries 4 bps fees;
- maker-taker forced-exit cycle carries 7 bps fees.

Funding cost is excluded only because new cycles are blocked around funding and max hold is 60 s; any cycle crossing a funding boundary is protocol-invalid.

## 8. Discovery chronology

Use only frozen Discovery dates from `sc001-e008-discovery-date-freeze-v1.0.md`.
Confirmation dates remain unopened until Discovery PASS.

## 9. Discovery promotion gates — all mandatory

Across eight Discovery days:
- source/data integrity PASS every day;
- completed cycles >= 100 total;
- active days = 8/8;
- unresolved inventory = 0;
- max absolute inventory <=1;
- forced-taker exits <=10% of completed cycles;
- pooled mean net edge >= +1.0 bps/cycle;
- 10% trimmed mean net edge >= +0.5 bps/cycle;
- pooled median net edge >= 0.0 bps;
- positive-day share >= 6/8;
- median daily mean net edge > 0;
- day-block bootstrap 95% LCB on mean net edge > 0;
- top-1 absolute daily contribution share <=0.30;
- top-3 share <=0.65;
- both long-first and short-first completed cycles >=20 each;
- primary stale-latch / queue invariants exact PASS;
- 500 ms stress pooled mean net edge >=0 and total net P&L >0;
- harsher queue stress with initial displayed queue-ahead multiplied by 2.0 has pooled mean net edge >=0 and unresolved inventory =0.

Any failed gate => `E008_DISCOVERY_FAIL` and blocks Confirmation/Q2/Validation/Final.
Only all gates PASS => `E008_DISCOVERY_PASS_OPEN_CONFIRMATION_ONCE`.

## 10. Stop rules

After Discovery output do not:
- weaken queue-ahead semantics;
- credit cancellations;
- reduce maker/taker fees;
- assume VIP/rebate tiers;
- increase max inventory or max hold;
- tune TTL/latency/quote width/order size;
- add TFI or prior features;
- cherry-pick sides/days/hours;
- replace failed frozen dates using outcomes.

## 11. Next pre-alpha action

Run metadata/HEAD preflight only for the eight frozen Discovery dates and required trade-neighbor labels. Do not download/open promotional L2 bodies until metadata preflight PASS and a data-acquisition protocol is frozen.
