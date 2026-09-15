# SC001-E002 OKX Q1 Taker Economics — Implementation Freeze v0.1

Date: 2026-09-15  
Status: **FROZEN BEFORE FIRST ECONOMICS RUN**

## 1. Parent protocol

Authoritative economics protocol:

`docs/research/sc001-e002-okx-q1-taker-economics-protocol-v0.2.md`

Required parent result:

`MIDQUOTE_CONFIRMATION_PASS`

Q2 OKX / formal Validation / Final remain closed.

## 2. Frozen implementation

Engine:

`research/sc001/sc001_e002_okx_q1_taker_economics.py`

Pinned Git commit containing the initial implementation:

`2a983a2dd8f8198cd88e6de58e40a234ca69acb9`

The engine records its own runtime SHA256 in every completed day checkpoint and in the terminal report.

Frozen signal-library dependency:

- pilot engine commit: `94c77febc73601c76976da4ab71bedecc69a485a`;
- path: `research/sc001/sc001_e002_okx_midquote_pilot.py`;
- only its already-frozen `build_scores` trade-flow construction is reused.

## 3. External metadata / funding prerequisites

Required PASS metadata preflight:

`~/sc001_data/SC001_E002_OKX_Q1_EXECUTION_METADATA/sc001_e002_okx_q1_execution_metadata_preflight_v0_2.json`

Required funding file:

`~/sc001_data/SC001_E002_OKX_Q1_EXECUTION_METADATA/sc001_e002_okx_q1_funding_rates_v0_2.json`

Pinned Q1 execution constants:

- `BTC-USDT-SWAP`;
- contract value `0.01 BTC`;
- minimum size `1 contract`;
- size step `1 contract`;
- tick `0.1 USDT`;
- Lv1 taker fee `0.0005` per fill = 5 bps per fill;
- conservative funding cost from absolute historical realized/archive funding rate when a trade spans an official funding timestamp.

## 4. Frozen causal threshold implementation

For every valid E002 decision:

- maintain only the strictly prior 720 valid absolute TFI scores from the same day;
- current score never enters its own threshold;
- nearest-rank q90/q95/q97.5 uses `ceil(q*720)-1` on the sorted prior window;
- q95 is primary; q90/q97.5 remain diagnostics;
- a zero score never opens a position, including the degenerate case of a zero empirical threshold.

This zero-score tie rule prevents an arbitrary long/short choice if both threshold inequalities would otherwise hold simultaneously.

## 5. Frozen L2 execution-state semantics

The historical 400-level book is replayed sequentially by exchange timestamp.

- all records sharing one exchange timestamp are applied as one timestamp group before that state can be exposed;
- execution uses the first **valid** fully-applied timestamp group with `book_ts >= target_ts`;
- crossed or empty states are never executable and the request remains pending until a later valid state;
- no stale pre-arrival state and no interpolation are allowed;
- every historical execution price must lie exactly on the pinned 0.1 tick grid under decimal arithmetic;
- any timestamp reversal, malformed level, off-grid price, crossed/empty source failure that compromises requested execution, or source identity mismatch is a hard integrity failure.

## 6. Frozen quantity / VWAP semantics

For each candidate and target quote notional:

`contracts = max(1, floor(target_notional / (0.01 * arrival_mid_entry)))`

Quantity is an integer and is fixed at entry for the entire round trip.

Visible-book depth is consumed level-by-level in executable price order. The L2 size field is treated as derivative contract quantity for `BTC-USDT-SWAP`; depth haircuts multiply visible quantity only. A scenario is filled only if the full integer contract quantity can be consumed inside the qualified 400-level book.

No partial fill is promoted into a synthetic full trade.

## 7. Frozen non-overlap edge cases

Each threshold / latency / haircut / size scenario is simulated independently.

- if a prior completed/attempted position has an exit execution timestamp strictly later than the current decision timestamp, the current candidate is skipped while open;
- if a new decision timestamp equals the previous exit execution timestamp, it is eligible because its new taker entry arrives only after the frozen latency;
- if the entry cannot be fully filled, no position is opened and subsequent candidates remain eligible;
- if entry fills but the exit cannot be fully filled at the first valid exit state, that candidate is counted unfilled and the scenario remains blocked through that exit-state timestamp;
- if no valid exit state exists before day end, the scenario remains blocked through day end;
- these rules may not be changed after economics output is observed.

## 8. Cost ledger

Per completed trade:

- gross midquote edge = signed move between executable-state mids;
- pre-fee executable edge = signed taker-VWAP round-trip return;
- spread/depth cost = gross midquote edge minus pre-fee executable edge;
- entry fee = entry executable notional × 0.0005;
- exit fee = exit executable notional × 0.0005;
- fee cost is normalized to entry executable notional;
- primary funding cost = sum of absolute frozen historical funding rates crossed, normalized to entry notional;
- net edge = pre-fee executable edge − fee cost − funding cost.

Primary metric remains **net edge per completed trade after all costs**.

## 9. Parallelism / withholding rule

The qualified 4-vCPU VPS may process the four frozen days in four independent OS processes.

Each worker:

- receives immutable frozen parameters;
- reads only its own day market data plus common frozen metadata;
- writes a complete day checkpoint and completed-trade CSV;
- exposes no day result for interpretation before all four workers finish.

Only the final parent aggregation writes the terminal verdict.

Complete day checkpoints with an identical runtime implementation SHA may be reused after a technical interruption; partial files without a terminal day report are not interpreted.

## 10. Promotion gates

Unchanged from protocol v0.2:

- Base: q95 / 10k / 100ms / 0% haircut;
- Stress A: q95 / 10k / 250ms / 0%;
- Stress B: q95 / 10k / 100ms / 25%;
- 500ms / 50% haircut / q90 / q97.5 / 1k / 50k are diagnostics only.

Verdicts:

- Base + both stress gates pass → `TAKER_ECONOMICS_PASS`;
- Base passes but a stress gate fails → `TAKER_ECONOMICS_WEAK`;
- Base fails → `TAKER_ECONOMICS_FAIL`.

Only PASS may proceed to freezing the exact executable rule before the protected Q2 one-shot holdout. WEAK/FAIL keep Q2 closed. No rescue tuning.

## 11. Required execution order

1. `python3 research/sc001/sc001_e002_okx_q1_taker_economics.py preflight`
2. inspect only the non-economic integrity/preflight output;
3. if PASS, run the same pinned implementation in `run` mode inside tmux;
4. do not inspect day checkpoint economics until all four workers complete;
5. interpret only the terminal report/verdict.
