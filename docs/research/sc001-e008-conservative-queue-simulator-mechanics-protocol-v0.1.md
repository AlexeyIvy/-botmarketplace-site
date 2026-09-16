# SC001-E008 — Conservative Queue Simulator Mechanics Protocol v0.1

Date: 2026-09-16  
Status: **FROZEN SYNTHETIC-MECHANICS PROTOCOL — NO REAL-DATA FILLS / NO P&L**

Prerequisites:
- `E008_DATA_INVENTORY_PASS`;
- queue-feasibility v0.1 remains `E008_QUEUE_MODEL_FEASIBILITY_REVIEW`;
- `E008_STALE_LATCH_MODEL_PASS`.

## 1. Purpose

Freeze and prove deterministic lower-bound passive-fill mechanics on hand-built synthetic event streams before any real-data hypothetical maker fill is calculated.

This stage is simulator engineering only. It must not open or evaluate real E008 profitability.

## 2. Order representation

A synthetic passive order has:

- side: BUY or SELL;
- resting price `P`;
- order quantity `Q > 0`;
- placement timestamp;
- `queue_ahead >= 0`;
- `remaining_qty`;
- status in `{RESTING, PARTIAL, FILLED, CANCELLED_UNFILLED, STALE_CANCELLED}`.

No order ID/FIFO priority from the historical exchange is assumed.

## 3. Placement rule

At placement on a trusted book state:

- BUY may rest only at the observed best bid;
- SELL may rest only at the observed best ask;
- the order starts behind the entire displayed aggregate size at that price:

`queue_ahead = displayed_size_at_P`.

Its own synthetic quantity is not inserted into the historical book.

If the book is stale/latched, crossed, empty, or the requested price is not the relevant best quote, placement is rejected.

## 4. Queue-progress rule

Only compatible aggressive transaction volume may reduce `queue_ahead`.

For a resting BUY at `P`:
- only sell-aggressor transactions with trade price `<= P` are compatible.

For a resting SELL at `P`:
- only buy-aggressor transactions with trade price `>= P` are compatible.

Transaction volume is applied in chronological order:

1. consume `queue_ahead` first;
2. any remaining compatible transaction volume may fill `remaining_qty`;
3. partial fills are explicit;
4. no fill can exceed order quantity.

A transaction at the exact same millisecond as an unordered book update is ambiguous and receives zero queue/fill credit.

## 5. Cancellation and displayed-size changes

Historical displayed-size decreases or level deletion **never** advance queue by themselves.

If displayed size at the resting price increases while the order is live, the increase is treated pessimistically as new quantity ahead of us:

`queue_ahead += displayed_size_increase`.

Displayed-size decreases without compatible transactions leave `queue_ahead` unchanged.

This intentionally overstates queue burden rather than understating it.

## 6. Price-level disappearance

If the synthetic resting price disappears from the trusted historical book before compatible transaction volume has filled the synthetic order:

- do not infer a fill;
- terminate the order as `CANCELLED_UNFILLED` unless it was already partially filled, in which case preserve the filled quantity and terminate the remainder unfilled;
- no extra queue progress is credited.

Price-through by book movement alone is insufficient to infer a fill.

## 7. Stale-latch interaction

If the fail-closed stale latch activates while an order is resting:

- immediately terminate all live synthetic orders as `STALE_CANCELLED`;
- no trade volume during latch may advance queue or fill;
- incremental updates do not restore trust;
- only the next full snapshot may restore a trusted book for future placements.

## 8. Explicit cancellation/TTL

A strategy-level cancellation or TTL expiry may terminate a resting/partial order at a supplied timestamp.

Cancellation itself creates no fill and no queue progress.

No primary TTL, quote width, order size, inventory rule or fee is selected in this mechanics protocol.

## 9. Required synthetic fixtures

The synthetic suite must assert at least:

1. BUY placement starts behind full displayed bid size;
2. SELL placement starts behind full displayed ask size;
3. compatible trade smaller than queue-ahead reduces queue only;
4. compatible trade exactly exhausting queue-ahead produces zero own fill;
5. excess compatible trade after queue-ahead creates partial fill;
6. enough compatible volume creates full fill but never overfills;
7. incompatible trade gives zero progress;
8. same-ms ambiguous trade gives zero progress;
9. displayed-size decrease without trade gives zero progress;
10. displayed-size increase adds to queue-ahead;
11. level deletion without enough compatible volume does not imply fill;
12. price-through book move alone does not imply fill;
13. stale latch cancels live order with zero extra fill;
14. trades during stale latch give zero credit;
15. incremental update after latch does not restore trust;
16. later full snapshot restores future placement eligibility;
17. partial fill remains recorded if remainder is later cancelled;
18. explicit TTL cancellation creates no fill;
19. cumulative compatible trade accounting is deterministic under chunked versus one-shot replay;
20. repeated identical run returns byte-identical synthetic result artifact except allowed runtime metadata.

## 10. PASS token

Synthetic mechanics PASS requires all frozen fixtures and invariants to pass and no real-data fill/P&L path to execute.

Exact terminal token:

`E008_QUEUE_SIMULATOR_SYNTHETIC_PASS`

Any failure yields:

`E008_QUEUE_SIMULATOR_SYNTHETIC_FAIL`

## 11. Firewall

This stage may not:

- open real E008 hypothetical orders;
- calculate real fill rates;
- calculate spread capture or markouts;
- choose order size/TTL/quote width from real outcomes;
- apply maker fees/rebates;
- calculate inventory P&L or profitability;
- use TFI or prior strategy features;
- open Q2/Validation/Final.

## 12. Next step after PASS

Only after exact synthetic PASS may the four contaminated engineering days be used for **mechanical simulator validation** under a separately frozen, non-promotional protocol. They still may not be used as sole E008 Discovery evidence or for parameter selection by profitability.
