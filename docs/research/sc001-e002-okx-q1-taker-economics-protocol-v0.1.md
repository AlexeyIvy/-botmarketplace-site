# SC001-E002 OKX Q1 Taker Execution Economics Protocol v0.1

Date: 2026-09-14  
Status: **FROZEN BEFORE Q1 EXECUTION-ECONOMICS RUN**

Parent confirmation: `SC001-E002-OKX-MIDQUOTE-Q1-CONFIRMATION`  
Required parent verdict: `MIDQUOTE_CONFIRMATION_PASS`

This stage converts the already-confirmed Q1 midquote predictability effect into a causal, taker-only execution-economics test. It is not a new signal search.

## 1. Research firewall

This stage may use only the already-open four non-pilot OKX 2024-Q1 dates:

- 2024-01-14 — ordinary weekend;
- 2024-01-31 — FOMC;
- 2024-02-12 — ordinary weekday;
- 2024-02-13 — CPI.

Still closed:

- 2024-Q2 OKX holdout;
- formal Validation;
- Final;
- maker execution assumptions;
- post-hoc event exclusions;
- post-hoc side selection;
- new signal families;
- horizon/window retuning after observing this stage.

SC001 remains independent from R009/R003/R010/S002.

## 2. Frozen signal

Use the exact E002 signed aggressive trade-flow imbalance already confirmed on OKX:

`TFI = signed aggressive notional / total aggressive notional`

on the 5-second UTC-aligned bucket immediately preceding decision time.

Decision grid, score sign and trade-source semantics must be identical to the frozen midquote confirmation engine.

No new features may be added.

## 3. Causal live entry threshold

The prior descriptive extreme decile is **not** a live trading rule and must not be reused ex post.

Primary live rule:

- maintain the absolute TFI values from the strictly prior **720 valid decisions** on the same day;
- the current decision is never included in its own threshold;
- no trade is eligible until 720 prior valid scores exist;
- compute the empirical nearest-rank **95th percentile** of prior `abs(TFI)` values;
- long candidate if `TFI >= threshold`;
- short candidate if `TFI <= -threshold`;
- otherwise no trade.

Nearest-rank rule for `N=720`:

`index = ceil(q * N) - 1` on the sorted prior absolute scores.

Predeclared diagnostic threshold sensitivities only:

- q90;
- q97.5.

The promotion decision is based on q95 only. q90/q97.5 may not be substituted after results are observed.

## 4. Position-state rule

- maximum one open position;
- no pyramiding;
- no simultaneous long/short positions;
- while a position is open, all new candidates are ignored;
- an opposite signal does not reverse the position early;
- the next decision becomes eligible only after the previous exit execution is complete;
- no overnight carry is allowed.

## 5. Frozen horizon and latency

Signal horizon remains 5 seconds.

Latency scenarios:

- **100 ms BASE**;
- **250 ms STRESS**;
- **500 ms DIAGNOSTIC**.

For a decision timestamp `t`:

- entry target = `t + latency`;
- exit target = `t + latency + 5000 ms`.

This preserves the same target spacing used by the confirmed midquote mechanism.

## 6. Executable L2 state rule

Unlike the prior predictability layer, execution must never use a stale last-known book from before the intended arrival.

For entry and exit:

- reconstruct the qualified 400-level OKX `BTC-USDT-SWAP` L2 book causally;
- group all records sharing the same exchange timestamp and apply the complete timestamp group before exposing that state for execution;
- use the **first valid reconstructed book state with exchange timestamp >= target timestamp**;
- record execution wait = `book_state_ts - target_ts`;
- if no valid state exists before UTC day end, the order is unexecutable;
- no interpolation of book states is allowed.

Execution-wait diagnostics must be reported at minimum at 250 / 500 / 1000 ms thresholds. No post-hoc wait filter may be introduced after results are seen.

## 7. Taker execution and visible-book VWAP

Primary execution is taker-only.

For a long entry:

- consume asks from best ask upward.

For a short entry:

- consume bids from best bid downward.

At exit, consume the opposite side of the book.

For every execution:

- consume visible depth level by level;
- calculate actual visible-book VWAP;
- respect price/size ordering and qualified replay semantics;
- do not fill beyond visible adjusted depth;
- if required quantity cannot be fully filled, mark the execution unfilled for that scenario; partial fills are not promoted into synthetic full trades.

## 8. Depth haircuts

Apply each scenario to every visible level before VWAP consumption:

- 0% haircut: visible size x 1.00 — BASE;
- 25% haircut: visible size x 0.75 — STRESS;
- 50% haircut: visible size x 0.50 — SEVERE DIAGNOSTIC.

The haircut changes available size only, never price levels or signal timing.

## 9. Order-size / capacity grid

Target quote notionals:

- 1,000 USDT — small-size diagnostic;
- **10,000 USDT — PRIMARY**;
- 50,000 USDT — capacity diagnostic.

Before implementation, the period-appropriate OKX `BTC-USDT-SWAP` contract value, lot size, minimum size and tick size for 2024-Q1 must be sourced, archived or otherwise pinned in the experiment metadata.

For each target notional:

- convert target notional to valid contract quantity using information available at entry;
- respect contract/lot discreteness;
- use the largest valid quantity not exceeding the target notional when possible;
- if even one minimum valid lot exceeds the target, use one minimum lot and report the actual resulting notional;
- record actual entry notional for every trade.

This grid is a capacity sensitivity test, not an account-sizing recommendation.

## 10. Fee ledger

No economic PASS may be issued until a period-appropriate OKX taker-fee source for `BTC-USDT-SWAP` is pinned in the run metadata.

Primary fee treatment:

- taker fee on entry;
- taker fee on exit;
- use the predeclared historical/base account tier selected before the economics run;
- report entry fee, exit fee and round-trip fee separately from book cost.

Also calculate a zero-fee decomposition **diagnostic only** to show the split between signal edge and market/book cost. Zero-fee output can never satisfy the economic promotion gate.

Report the break-even round-trip fee implied by pre-fee execution edge.

## 11. Per-trade economic decomposition

All bps must be normalized consistently to entry notional.

For every completed trade report at least:

- decision time;
- direction;
- TFI;
- causal threshold;
- latency;
- depth haircut;
- target and actual notional;
- entry target time / execution-book time / wait;
- exit target time / execution-book time / wait;
- arrival mid at entry;
- arrival mid at exit;
- entry taker VWAP;
- exit taker VWAP;
- gross midquote edge bps;
- pre-fee executable edge bps;
- spread/depth cost bps;
- fee cost bps;
- **net edge per trade after all costs, bps**.

Definitions:

- `gross_midquote_edge_bps` = signed midquote move between executable entry/exit states;
- `pre_fee_executable_edge_bps` = signed entry-to-exit taker VWAP return;
- `spread_depth_cost_bps` = `gross_midquote_edge_bps - pre_fee_executable_edge_bps`;
- `net_edge_bps` = `pre_fee_executable_edge_bps - round_trip_fee_bps`.

The primary economic metric is **NET EDGE PER TRADE AFTER ALL COSTS**.

## 12. Required aggregate outputs

For every date / latency / haircut / size / threshold scenario report:

- candidate count;
- completed non-overlapping trade count;
- skipped-while-open count;
- unfilled count;
- fill/completion rate;
- long / short count;
- mean and median gross midquote edge bps;
- mean and median pre-fee executable edge bps;
- mean and median spread/depth cost bps;
- mean and median fee cost bps;
- **mean and median net edge bps per trade**;
- total net bps-equivalent / notional-normalized result;
- win rate after all costs;
- entry/exit execution-wait percentiles;
- break-even fee.

Also report pooled four-day metrics and event-vs-ordinary splits.

## 13. Multiple-testing ledger

Predeclared dimensions:

- thresholds: q90 / **q95 primary** / q97.5;
- latency: **100 primary** / 250 stress / 500 diagnostic;
- depth haircut: **0% primary** / 25% stress / 50% severe diagnostic;
- target notional: 1k diagnostic / **10k primary** / 50k capacity diagnostic.

No other threshold, latency, haircut, size, side filter, event filter or holding horizon may be added under this version after output is observed.

Only the primary q95 / 10k combination can determine promotion. Diagnostics cannot be substituted for a failed primary result.

## 14. Promotion gates

### Base gate — q95 / 10k / 100 ms / 0% haircut

All must hold:

1. pooled mean net edge per completed trade > 0 bps;
2. median of the four daily mean net edges > 0 bps;
3. positive daily mean net edge on 4 / 4 frozen days;
4. event-day median daily mean net edge > 0;
5. ordinary-day median daily mean net edge > 0;
6. completed-trade rate >= 99% among otherwise eligible non-overlapping entries;
7. no replay/source-integrity failure.

### Stress gate A — latency

At q95 / 10k / 250 ms / 0% haircut:

- pooled mean net edge > 0;
- at least 3 / 4 days have positive daily mean net edge.

### Stress gate B — depth

At q95 / 10k / 100 ms / 25% haircut:

- pooled mean net edge > 0;
- at least 3 / 4 days have positive daily mean net edge.

500 ms and 50% haircut are diagnostic and do not rescue a failure.

### Verdict

- `TAKER_ECONOMICS_PASS`: Base + Stress A + Stress B all pass.
- `TAKER_ECONOMICS_WEAK`: Base passes but one or both stress gates fail.
- `TAKER_ECONOMICS_FAIL`: Base fails.

Only `TAKER_ECONOMICS_PASS` is eligible to freeze an exact executable rule and open the protected 2024-Q2 OKX one-shot holdout.

`WEAK` and `FAIL` keep Q2 closed under this protocol.

## 15. Stop / no-rescue rule

If Base fails, do not rescue E002 using:

- a different percentile threshold;
- a smaller size substituted as primary;
- lower fees than the pinned primary fee ledger;
- event exclusions;
- long-only or short-only filtering;
- slower/faster horizon changes;
- maker assumptions;
- alternate signal normalization;
- relaxed overlap logic;
- Q2 exploration.

A materially different rule requires a separately justified new research branch/version and may not retroactively change this result.

## 16. Interpretation boundary

The preceding Q1 midquote confirmation established measurement robustness, not profitability. Its final summary showed:

- 100 ms positive daily Spearman: 4 / 4;
- 100 ms median daily Spearman: about 0.06474;
- 100 ms positive extreme-spread days: 4 / 4;
- 100 ms median extreme spread: about 0.23678 bps;
- 250 ms positive daily Spearman: 4 / 4;
- 250 ms median daily Spearman: about 0.05864.

The observed predictive effect is small in absolute bps, so observed spread/depth and fee charging are the decisive next falsification layer. No profitability claim is permitted before this protocol completes.
