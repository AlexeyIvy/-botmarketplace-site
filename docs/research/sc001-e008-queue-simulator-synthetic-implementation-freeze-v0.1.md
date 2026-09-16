# SC001-E008 — Queue Simulator Synthetic Implementation Freeze v0.1

Date: 2026-09-16  
Status: **FROZEN BEFORE SYNTHETIC RUN**

Parent protocol:
`docs/research/sc001-e008-conservative-queue-simulator-mechanics-protocol-v0.1.md`

Frozen executable:
`research/sc001/sc001_e008_queue_simulator_synthetic_v0_1.py`

Git blob SHA:
`bec5d54b63bb632b29dc969173d29504839a8f3f`

## Boundary

This implementation contains synthetic fixtures only. It must not open real market data or calculate real hypothetical fills, spread capture, markout, fees/rebates, inventory P&L or profitability.

## Frozen mechanics

- full displayed best-level size starts ahead;
- compatible aggressive transaction volume is the only source of queue progress;
- cancellations/size decreases give zero progress;
- size increases are pessimistically added ahead;
- same-ms ambiguity gives zero credit;
- level disappearance/book price-through alone never implies fill;
- stale latch cancels live orders and blocks credit until full snapshot recovery;
- partial fills are explicit;
- exact FIFO is never claimed.

Only exact `E008_QUEUE_SIMULATOR_SYNTHETIC_PASS` permits the next non-promotional mechanical-validation stage.
