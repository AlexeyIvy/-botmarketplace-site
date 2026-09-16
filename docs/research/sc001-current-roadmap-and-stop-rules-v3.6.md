# SC001 Current Roadmap and Stop Rules v3.6

Date: 2026-09-16  
Status: **CURRENT SC001 ROADMAP — E008 TERMINAL FAIL / READ-ONLY POSTMORTEM OPEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v3.5.md`

## 1. Independence / terminal state

SC001 remains fully independent from `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` and `Safe-Sleeve S002`.

E001-E008 are terminal/closed. E008 exact terminal status remains:

`E008_DISCOVERY_FAIL`

Do not rescue-tune or rerun E008 for promotion.

Confirmation / Q2 / formal Validation / Final remain CLOSED.

## 2. Why a read-only postmortem is now allowed

The terminal E008 result is materially negative, but mechanism diagnosis is still useful for designing a new independent experiment.

A read-only forensic stage is therefore opened under:

`docs/research/sc001-e008-readonly-postmortem-protocol-v1.0.md`

Runner:

`research/sc001/sc001_e008_readonly_postmortem.py`

The runner consumes only already-produced reports. It does not replay the strategy, create orders/fills, change parameters or promotion gates, or access Confirmation/Q2/Validation/Final.

## 3. First forensic questions

The postmortem must quantify:

- exact mean gross edge before fees;
- exact realized fee drag;
- maker-only vs forced-taker cycle economics;
- passive-exit completion rate;
- per-day forced-taker share;
- level-disappearance cancels;
- best-move cancel requests;
- placement/replacement churn;
- snapshot frequency;
- stale-gap relevance;
- same-ms zero-credit scale;
- invalid/unresolved reasons.

## 4. Static implementation risks already identified for investigation

Without changing E008, future design must explicitly address:

1. hypothetical own orders are not inserted into the reconstructed exogenous book;
2. historical price-level disappearance cancels our hypothetical order, although a real resting order would itself keep the level present;
3. best-price comparisons ignore our own resting liquidity;
4. the queue lower bound is deliberately extreme: zero cancellation credit + all additions ahead + full queue reset;
5. forced-taker proxy uses the next arbitrary public trade rather than side-specific executable bid/ask depth;
6. separate trade/book timestamps do not provide exact cross-feed event ordering;
7. price-through trade quantity is not a level-exact FIFO reconstruction;
8. snapshot resync can cancel live hypothetical quotes even though a feed snapshot is not itself a venue order cancellation;
9. future experiments must freeze historical `lotSz`, `minSz`, `tickSz`, `ctVal`, and fee basis explicitly.

These are possible model limitations/biases, not reasons to reopen E008.

## 5. Interpretation of earlier PASS stages

Earlier PASS stages validated data identity, semantic integrity and state-machine mechanics. They did not predict profitability.

Therefore `E008_DISCOVERY_FAIL` does not contradict those PASS stages.

## 6. Immediate next action

On VPS:

1. `git pull --ff-only`;
2. syntax-check `research/sc001/sc001_e008_readonly_postmortem.py`;
3. run the read-only postmortem once;
4. require exact `E008_READONLY_POSTMORTEM_PASS`;
5. inspect the printed gross/fee/net decomposition and lifecycle counters;
6. only after review, design a new independent experiment family with a new predeclared protocol.

No E008 strategy command may be executed.