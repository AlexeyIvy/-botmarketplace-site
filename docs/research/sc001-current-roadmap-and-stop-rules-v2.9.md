# SC001 Current Roadmap and Stop Rules v2.9

Date: 2026-09-16  
Status: **CURRENT SC001 ROADMAP SNAPSHOT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v2.8.md`

## 1. Terminal history

E001-E007 remain terminal/closed exactly as previously recorded. SC001 remains independent from R009-E002, R003-E003 Binance, R003-X003 Bybit, R010-E001 and Safe-Sleeve S002. Q2 / formal Validation / Final remain closed.

## 2. E008 completed gates

- `E008_DATA_INVENTORY_PASS`.
- historical queue-feasibility v0.1 remains `E008_QUEUE_MODEL_FEASIBILITY_REVIEW` and is not relabeled.
- Feb-13 forensic: `CONCENTRATED_SOURCE_GAPS`.
- fail-closed stale-latch v0.2: `E008_STALE_LATCH_MODEL_PASS` on 4/4 engineering days.
- synthetic queue simulator mechanics: exact `E008_QUEUE_SIMULATOR_SYNTHETIC_PASS`, 22/22 tests.

No promotional maker profitability has been calculated.

## 3. Frozen queue/stale semantics

All later E008 work must preserve:
- initial queue-ahead = full displayed size;
- compatible aggressive transaction volume only advances queue;
- cancellation/size decrease gives zero progress;
- size additions are pessimistically added ahead;
- same-ms ambiguity gives zero credit;
- level disappearance/book movement alone never implies fill;
- partial fills explicit;
- book age >5,000 ms => stale latch;
- stale latch gives no queue/fill credit and cancels live orders;
- incremental updates do not restore trust after latch;
- only a later full snapshot restores trusted book state;
- exact FIFO is never claimed.

## 4. Current hard gate: non-promotional real-data mechanical validation

Protocol:
`docs/research/sc001-e008-realdata-mechanical-validation-protocol-v0.1.md`

Implementation freeze:
`docs/research/sc001-e008-realdata-mechanical-validation-implementation-freeze-v0.1.md`

Runner:
`research/sc001/sc001_e008_realdata_mechanical_validation.py`

Engineering scope only:
- 2024-01-14;
- 2024-01-31;
- 2024-02-12;
- 2024-02-13.

Deterministic probes:
- 96/day at 15-minute boundaries;
- alternating BUY/SELL;
- quantity 1.0 historical size unit;
- placement lag <=1 s;
- TTL 60 s;
- no overlap.

The stage may report mechanical fill/cancellation state counts only. It must not calculate spread capture, markout, fees/rebates, inventory P&L or profitability.

Allowed terminal states:
- `E008_QUEUE_SIMULATOR_MECHANICAL_PASS`;
- `E008_QUEUE_SIMULATOR_MECHANICAL_REVIEW`.

## 5. Contamination firewall

The four engineering days were already used in prior E002 work and remain non-promotional.

Do not:
- optimize quote width/order size/TTL using these days;
- infer E008 profitability from mechanical fill counts;
- calculate maker P&L on these days for promotion;
- add TFI or prior strategy features;
- open Q2/Validation/Final.

## 6. Next step after mechanical PASS

Only after exact mechanical PASS:
1. freeze an untouched Q1 E008 Discovery date set before opening/downloading its L2 bodies;
2. freeze the actual passive strategy/execution/fee/inventory protocol before any promotional output;
3. acquire only the frozen Discovery data under data-only integrity gates;
4. run one E008 Discovery;
5. only a full Discovery PASS may open a separately frozen untouched Confirmation set.

## 7. Immediate next action

On the qualified VPS:
1. `git pull --ff-only`;
2. syntax-check `research/sc001/sc001_e008_realdata_mechanical_validation.py`;
3. run only the non-promotional mechanical validation;
4. inspect exact terminal result;
5. do not calculate spread capture/markout/fees/P&L/profitability yet.
