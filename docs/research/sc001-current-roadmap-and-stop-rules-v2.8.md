# SC001 Current Roadmap and Stop Rules v2.8

Date: 2026-09-16  
Status: **CURRENT SC001 ROADMAP SNAPSHOT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v2.7.md`

## 1. Terminal history

E001-E007 remain terminal/closed exactly as previously recorded. SC001 remains independent from R009-E002, R003-E003 Binance, R003-X003 Bybit, R010-E001 and Safe-Sleeve S002. Q2 / formal Validation / Final remain closed.

## 2. E008 data-model state

- `E008_DATA_INVENTORY_PASS`.
- Queue-feasibility v0.1 remains terminal data-model `REVIEW`; it is not relabeled.
- Feb-13 forensic category: `CONCENTRATED_SOURCE_GAPS`.
- Fail-closed stale-latch v0.2 returned exact `E008_STALE_LATCH_MODEL_PASS` on all 4/4 engineering days.

Observed stale-latch engineering facts:
- 2024-01-14: gaps=0, episodes=0;
- 2024-01-31: gaps=3, episodes=3;
- 2024-02-12: gaps=0, episodes=0;
- 2024-02-13: gaps=9, episodes=8;
- recovery after a latch is full-snapshot-only.

No real maker fill/P&L/profitability has been calculated.

## 3. Frozen stale-book safety rule

For all later E008 work:
- book age >5,000 ms => stale latch;
- no quoting/queue progress/fill credit while latched;
- incremental updates do not restore trust;
- only a later full snapshot restores trusted state.

The failed v0.1 5-second coverage gate remains unchanged historically.

## 4. Current hard gate: synthetic queue simulator mechanics

Protocol:
`docs/research/sc001-e008-conservative-queue-simulator-mechanics-protocol-v0.1.md`

Implementation freeze:
`docs/research/sc001-e008-queue-simulator-synthetic-implementation-freeze-v0.1.md`

Executable:
`research/sc001/sc001_e008_queue_simulator_synthetic_v0_1.py`

The simulator mechanics are deliberately pessimistic:
- initial queue-ahead = full displayed size at resting best quote;
- only compatible aggressive trade volume advances queue;
- cancellation/size decrease gives zero progress;
- displayed-size additions are added ahead;
- same-ms ambiguity gives zero credit;
- level disappearance/book move alone never implies fill;
- stale latch cancels live synthetic orders;
- partial fills explicit; no exact FIFO claim.

## 5. Synthetic gate

Only exact terminal token:

`E008_QUEUE_SIMULATOR_SYNTHETIC_PASS`

opens the next step.

Any synthetic failure blocks real-data mechanical validation until the implementation defect is fixed without weakening the frozen conservative semantics.

## 6. Real-data firewall

Before synthetic PASS, do not:
- create real-data hypothetical maker orders;
- report real fill count/rate;
- calculate spread capture or markout;
- select quote width/order size/TTL/inventory rule;
- apply maker fees/rebates;
- calculate maker P&L/profitability;
- add TFI or prior strategy features;
- open Q2/Validation/Final.

The four Q009A/Q009B engineering days remain contaminated/non-promotional and may later be used only for mechanical simulator validation under a separately frozen protocol.

## 7. Immediate next action

On the qualified VPS:
1. `git pull --ff-only`;
2. syntax-check `research/sc001/sc001_e008_queue_simulator_synthetic_v0_1.py`;
3. run only the synthetic suite;
4. require exact `E008_QUEUE_SIMULATOR_SYNTHETIC_PASS`;
5. do not run any real-data maker simulation yet.
