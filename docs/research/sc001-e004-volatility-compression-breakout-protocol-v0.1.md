# SC001-E004 — Causal Volatility-Compression -> Breakout/Expansion Protocol v0.1

Date: 2026-09-15  
Status: **FROZEN BEFORE FIRST E004 ALPHA / GROSS-EDGE OUTPUT**

Parent planning document: `docs/research/sc001-e004-volatility-compression-breakout-research-plan-v0.1.md`.

This protocol converts the planning hypothesis into one executable, causal, economics-first experiment. No E004 return, edge, P&L, side result, threshold result, candidate-count result or diagnostic neighborhood result may be used to alter this version.

## 1. Independence and research firewall

SC001 remains fully independent from:

- R009-E002;
- R003-E003 Binance;
- R003-X003 Bybit;
- R010-E001;
- Safe-Sleeve S002.

Nothing in E004 changes their frozen rules, decisions, interpretations or forward clocks.

E004 is also independent from failed SC001 E001/E003 and from standalone E002 economics.

Base E004 must not use:

- E002 TFI as a filter, ranker, veto, timing input or sizing input;
- E003 FLOW_IMPULSE as a filter or feature;
- event/day exclusions inferred from prior failures;
- one-sided selection inferred from inspected history.

A later E005 may test TFI only as incremental value on top of an independently viable E004 base strategy.

## 2. Economic hypothesis

The hypothesis is deliberately narrower than the phrase "compression predicts direction".

Compression alone is treated as a state variable for **future expansion potential**, not directional alpha. Direction is supplied only by the subsequent causal breakout of the already-closed compression box.

Frozen hypothesis:

> After an unusually narrow five-minute price box relative to the recent same-day distribution, the first causally confirmed break of that box may be followed by directional expansion over the next several minutes large enough to clear regular-user taker economics.

The intended scale is many basis points, with lower turnover than E002/E003.

## 3. Data boundary

Instrument: OKX `BTC-USDT-SWAP` public historical trades.

Use only the already-qualified March-2024 trade archives and the same Q006R UTC-stitch semantics already used by E003.

### DEV-DISCOVERY

- 2024-03-01 through 2024-03-20 inclusive.

### One-time DEV-CONFIRMATION

- 2024-03-21 through 2024-03-30 inclusive;
- may be opened only after a terminal `E004_DISCOVERY_PASS` from the exact frozen implementation.

Closed:

- all 2024-Q2 raw market-data bodies;
- formal Validation;
- Final;
- new E004 L2 acquisition before gross-hurdle promotion.

No April/Q2 body may be accessed for E004 v0.1.

## 4. UTC trade reconstruction

For target UTC day D:

- read archive D and the already-qualified D+1 neighbor archive as required by OKX historical grouping;
- retain only target-instrument rows with `created_time` in `[D 00:00:00, D+1 00:00:00)` UTC;
- require the source manifest, archive byte sizes and SHA256 values to match the already-qualified March trade stage;
- require monotone target timestamps and strictly increasing target trade IDs under the existing qualified stitch semantics;
- require all 1440 UTC minutes to contain admitted target trades.

All E004 state resets at each UTC day boundary. There is no prior-day signal warm-up and no overnight position carry.

## 5. One-second tape price

Partition each UTC day into left-closed/right-open one-second buckets:

`[s, s+1s)`.

For every second with at least one admitted target trade, define the size-weighted tape VWAP:

`P_s = sum(price_i * size_i) / sum(size_i)`.

For this single fixed SWAP instrument, `size` is used only as a within-instrument positive weight. This is not a quote-notional capacity claim.

A second with no admitted trade has no `P_s` and is invalid for box construction or breakout confirmation.

Decision information from a one-second bucket becomes available only at its right edge `s+1s`.

## 6. Five-minute compression boxes

Partition each UTC day into non-overlapping, UTC-aligned five-minute blocks of exactly 300 one-second buckets.

A five-minute block k is valid only if at least `270 / 300` one-second buckets contain a valid `P_s`.

For valid block k:

- `H_k = max(P_s)` over valid seconds in the block;
- `L_k = min(P_s)` over valid seconds in the block;
- `R_k = 10,000 * ln(H_k / L_k)` basis points.

Require finite positive `H_k`, `L_k` and `R_k >= 0`.

The use of one-second VWAP extrema rather than individual trade extrema is frozen to reduce sensitivity to isolated single-print microstructure noise without introducing L2 data.

## 7. Causal compression statistic

Primary baseline window: exactly the previous `72` valid five-minute blocks from the same UTC day.

This is approximately six hours when blocks are contiguous.

No compression decision is possible until 72 prior valid blocks exist.

For current valid block k, before inserting `R_k` into the rolling baseline, compute the nearest-rank 20th percentile of the strictly prior 72 ranges:

`compression_threshold_k = q20_nearest_rank({R_{k-72}, ..., R_{k-1}})`

with nearest-rank index:

`ceil(0.20 * 72) - 1 = 14` under zero-based indexing.

Primary compression rule uses strict inequality:

`R_k < compression_threshold_k`.

Equality is not a compression event.

After the decision is made, `R_k` is inserted into the rolling baseline.

## 8. Box arming and expiry

When a valid block closes and satisfies the primary compression rule while the scenario is flat and not already armed:

- freeze that block's `H_k` and `L_k` as the breakout box;
- arm the box for exactly the next `300 seconds`;
- the arm interval is `[block_end, block_end + 300s)`.

If no breakout occurs during that interval, the arm expires permanently.

The same box may never be reused.

While an arm is active, no second arm may coexist. The rolling compression baseline continues to update normally from subsequently closed valid five-minute blocks.

If an arm expires with no position opened, the just-closed five-minute watch block may itself be evaluated for compression at its own close using the ordinary causal rules.

## 9. Breakout confirmation and direction

During an active arm, examine valid one-second tape VWAP buckets in chronological order.

The first closed one-second bucket satisfying either strict inequality triggers the only candidate from that box:

- long if `P_s > H_k`;
- short if `P_s < L_k`.

Equality to a boundary is not a breakout.

Because `H_k > L_k`, one one-second VWAP cannot satisfy both directions simultaneously.

Breakout decision timestamp:

`decision_ts = right edge of the first qualifying one-second bucket`.

After a breakout decision, the arm is consumed and may not generate another trade.

## 10. Primary execution proxy

Primary latency:

`250 ms`.

Primary holding horizon:

`600 seconds` (10 minutes), measured from the frozen latency-adjusted decision target.

For a candidate:

- `entry_target = decision_ts + 250 ms`;
- `exit_target = decision_ts + 250 ms + 600 s`;
- entry proxy = first admitted target-day trade at or after `entry_target`;
- exit proxy = first admitted target-day trade at or after `exit_target`.

If multiple trades share a timestamp, preserve qualified archive stream order and use the first admitted row at/after the target.

A candidate is ineligible before fill lookup if `exit_target >= UTC day_end`.

No stop-loss, take-profit, trailing stop, early reversal or discretionary exit is permitted in v0.1.

## 11. Non-overlap and position state

Each frozen scenario is simulated independently.

Maximum one open position.

- no pyramiding;
- no simultaneous long/short;
- no early reversal;
- no new arm while a position is open;
- rolling baseline state continues to update while a position is open;
- after a completed trade, the position remains open until the **actual exit proxy timestamp**, not merely the intended exit target;
- if entry is found but exit cannot be found before day end, the scenario is treated as open through day end and all later candidates are blocked;
- no overnight carry.

After the position is flat, only a subsequently closing five-minute block may create a new arm. A compression block that closed while the position was open cannot be retroactively armed.

## 12. Gross-edge definition

For each completed trade:

`gross_edge_bps = direction * (exit_price / entry_price - 1) * 10,000`.

where direction is `+1` for long and `-1` for short.

This first stage does **not** subtract:

- taker fees;
- bid/ask spread;
- visible-book impact;
- depth haircut;
- funding.

Those belong only to a later L2 executable-economics stage if E004 earns promotion.

## 13. Why the primary gross hurdle is 15 bps

The frozen reference regular-user taker burden remains approximately 10 bps round trip before spread/depth deterioration.

Therefore a 12 bps near-break-even gross screen is not sufficient for E004.

Primary pooled gross-edge hurdle:

**`pooled mean gross edge >= 15 bps`.**

This is only an L2-promotion plausibility hurdle, not a claim of executable profitability.

## 14. Robust aggregation definitions

All completed primary trades are pooled trade-weighted for pooled statistics.

### 14.1 Two-sided 10% trimmed mean

Sort all completed trade gross edges.

Let:

`m = floor(0.10 * N)`.

Remove the lowest m and highest m observations and compute the ordinary mean of the remainder.

### 14.2 Daily means

For each required UTC calendar day with at least one completed primary trade, compute the ordinary mean gross edge of that day's completed primary trades.

A day with zero completed primary trades is **inactive** and cannot be silently removed from the active-day or positive-day breadth gates.

### 14.3 Positive-day contribution concentration

For day d:

`G_d = sum(gross_edge_bps of completed primary trades on day d)`.

`P_d = max(G_d, 0)`.

If `sum(P_d) <= 0`, the concentration gate fails automatically.

Otherwise:

- `top1_positive_day_share = max(P_d) / sum(P_d)`;
- `top3_positive_day_share = sum(three largest P_d) / sum(P_d)`.

This gate is designed to stop one or a few exceptional days from carrying the entire candidate.

### 14.4 Completion rate

`eligible_nonoverlap = breakout_candidates - skipped_while_open - ineligible_day_end`.

`completion_rate = completed / eligible_nonoverlap`.

If `eligible_nonoverlap == 0`, the stage fails.

## 15. DEV-DISCOVERY gates — all mandatory

Primary scenario: q20 / 250 ms / 600 s.

All of the following must pass on 2024-03-01 through 2024-03-20:

1. pooled mean gross edge `>= 15 bps`;
2. two-sided 10% trimmed mean gross edge `>= 12 bps`;
3. pooled median gross edge `> 0 bps`;
4. median daily mean among active days `>= 10 bps`;
5. at least `16 / 20` active days;
6. positive daily mean on at least `14 / 20` required calendar days;
7. completed primary trades `>= 40`;
8. completed primary trades `<= 160`;
9. no UTC day with more than `12` completed primary trades;
10. proxy completion rate `>= 99%`;
11. top-1 positive-day contribution share `<= 30%`;
12. top-3 positive-day contribution share `<= 60%`;
13. mandatory 500 ms stress pooled mean gross edge `>= 13 bps`;
14. mandatory 500 ms stress two-sided 10% trimmed mean gross edge `>= 10 bps`;
15. no source, chronology, causality, integrity or firewall failure.

If any mandatory gate fails:

`E004_DISCOVERY_FAIL`

and DEV-CONFIRMATION remains unopened.

If all pass:

`E004_DISCOVERY_PASS`.

## 16. One-time DEV-CONFIRMATION gates — unchanged mechanism

Only after terminal `E004_DISCOVERY_PASS`, run exact unchanged primary rules on 2024-03-21 through 2024-03-30.

All of the following must pass:

1. pooled mean gross edge `>= 15 bps`;
2. two-sided 10% trimmed mean gross edge `>= 12 bps`;
3. pooled median gross edge `> 0 bps`;
4. median daily mean among active days `>= 10 bps`;
5. at least `8 / 10` active days;
6. positive daily mean on at least `7 / 10` required calendar days;
7. completed primary trades `>= 20`;
8. completed primary trades `<= 80`;
9. no UTC day with more than `12` completed primary trades;
10. proxy completion rate `>= 99%`;
11. top-1 positive-day contribution share `<= 35%`;
12. top-3 positive-day contribution share `<= 70%`;
13. mandatory 500 ms stress pooled mean gross edge `>= 13 bps`;
14. mandatory 500 ms stress two-sided 10% trimmed mean gross edge `>= 10 bps`;
15. no source, chronology, causality, integrity or firewall failure.

If any mandatory gate fails:

`E004_CONFIRMATION_FAIL`.

If all pass:

`E004_CONFIRMATION_PASS`.

Only Discovery PASS + unchanged Confirmation PASS yields:

`E004_GROSS_HURDLE_PASS`.

## 17. Frozen stress and diagnostic neighborhood

Primary:

- compression q20;
- prior valid blocks = 72;
- arm = 300 s;
- breakout confirmation = first closed one-second VWAP strictly outside the frozen box;
- latency = 250 ms;
- hold = 600 s.

Mandatory execution-timing stress:

- q20 / 500 ms / 600 s.

Diagnostics only, one factor changed at a time:

- compression q15 / 250 ms / 600 s;
- compression q25 / 250 ms / 600 s;
- q20 / 250 ms / 300 s hold;
- q20 / 250 ms / 900 s hold;
- q20 / 1000 ms / 600 s.

Diagnostics may be reported only after the primary stage is fully aggregated. They may describe local stability but **cannot replace a failed primary or mandatory 500 ms stress gate**, cannot open Confirmation, and cannot become E004 v0.1.

No full Cartesian grid is authorized.

## 18. Turnover discipline

E004 v0.1 takes every causally eligible primary breakout subject only to the frozen one-position state machine.

There is no post-hoc trade ranking or selective daily cap.

Instead, excessive natural turnover is itself a failure through the predeclared completed-trade ceilings and maximum-per-day gates.

This prevents a high-frequency tiny-edge mechanism from being disguised by arbitrary throttling.

## 19. Multiple-testing and no-rescue ledger

No post-output change may be made to:

- five-minute block length;
- 270/300 valid-second requirement;
- 72-block baseline;
- q20 primary threshold;
- strict inequality semantics;
- one-second VWAP definition;
- breakout arm duration;
- 250 ms primary latency;
- 600 s primary hold;
- state-machine/non-overlap rules;
- turnover gates;
- robust economics gates;
- direction symmetry.

No rescue via:

- q15/q25 substitution;
- 300/900 s horizon substitution;
- lower/VIP fees;
- maker assumptions;
- E002 TFI;
- E003 FLOW_IMPULSE;
- one-sided selection;
- event/day/time-of-day filters;
- excluding losing days;
- changing compression lookback after results;
- Q2 / Validation / Final exploration.

A materially different hypothesis requires a new experiment identifier/version frozen before its data are inspected.

## 20. Promotion order

`frozen protocol -> implementation preflight PASS -> DEV-DISCOVERY -> unchanged DEV-CONFIRMATION -> only if both PASS, L2 taker execution economics -> later protected temporal validation`

No E004 alpha/gross-edge output is authorized until the implementation preflight is completed and recorded as PASS.

## 21. L2 promotion boundary

Only `E004_GROSS_HURDLE_PASS` authorizes a new separately frozen E004 L2 taker-economics stage.

That later stage must include at minimum:

- causal arrival-time L2 state;
- spread crossing;
- visible-book VWAP consumption;
- frozen primary order size;
- depth haircuts;
- explicit regular-user taker fees;
- funding if economically relevant;
- net edge after all costs;
- capacity/completion diagnostics.

No maker/queue claim is allowed from aggregated 400-level L2.
