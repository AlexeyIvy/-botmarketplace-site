# SC001 / B15-P2 — Price Experiment Design Review v0.1

Date: 2026-09-29  
Status: **THREE-ROLE DESIGN PASS / NO PRICE OUTCOME ACCESSED**

## Objective

Freeze the smallest useful outcome-bearing experiment before opening any B15-P2 price data.

The selected first experiment is **not a backtest and not a PnL test**.

It is a structural headroom sentinel asking:

> Does absolute perpetual-vs-Bybit-index basis converge specifically during the mechanism-defined 30-minute forced-close window, and is that convergence large enough to justify a later execution study?

## Trader / financial-market review

The 30-minute closing-price rule supplies the mechanism timescale. The experiment therefore uses one primary window derived from the mechanism, not a grid of 5m/10m/30m/60m alternatives.

Primary mechanism window:

- T-30m to T-5m.

Equal-length control:

- T-55m to T-30m.

The last five minutes are intentionally excluded from the primary sentinel because order cancellation, vanishing liquidity and terminal trading-stop mechanics can dominate there.

Future directional architecture is frozen before outcomes:

- positive basis at T-30m -> convergence hypothesis would be short perpetual;
- negative basis -> long perpetual;
- zero basis -> no direction.

P0 does not execute that trade and does not calculate PnL.

## Programmer-trader review

Use only two official Bybit V5 public series:

- affected contract 1-minute kline;
- official index-price 1-minute kline.

Exactly three fully closed minute candles are registered per series: -55m, -30m, -5m.

No interpolation, nearest candle, alternate venue, mark price, premium index or spot proxy is allowed.

The event clock is separately frozen from source-only metadata. The minimum announcement lead in the frozen set is about 4.97 hours, so all registered P0 observations occur after the announcement was already observable.

If delisted symbols are unavailable from the official endpoints, the result is a source DEFER rather than silent substitution.

## Mathematician-statistician review

The 94 events are not treated as 94 IID observations.

There are only 37 unique delisting timestamps, with up to five simultaneous events. Therefore:

- primary inference unit = delivery timestamp cluster;
- constituent events are summarized by cluster median;
- clusters receive equal weight;
- uncertainty is block/bootstrap over delivery clusters;
- month breadth is reported separately.

Only one primary mechanism horizon is allowed. No post-outcome horizon search, symbol filtering or basis-threshold optimization is permitted.

## Frozen primary metrics

For each target time t:

B(t) = 10,000 × (perpetual close / index close − 1) bps.

A(t) = |B(t)|.

Control convergence:

C_control = A(-55m) − A(-30m).

Mechanism-window convergence:

C_event = A(-30m) − A(-5m).

Incremental timing-specific effect:

D = C_event − C_control.

The primary statistical object is the delivery-cluster median D.

## Cost/headroom logic

P0 is deliberately cost-aware without pretending to know realized execution costs.

The official Bybit fee schedule currently lists 5.5 bps/side taker for standard VIP0 perpetual/futures and higher special-zone rates can reach 11 bps/side. The experiment therefore freezes:

- 11 bps as the standard two-taker fee-only floor;
- 22 bps as a high-fee-zone round-trip reference;
- 30 bps as a conservative structural-headroom threshold for deciding whether an expensive L1 execution study is worth building.

Actual user/region/VIP fees are not inferred and are not used as historical PnL in P0.

## Gate interpretation

P0 can end in only five meaningful states:

1. DEFER_SOURCE_COVERAGE — official source coverage is inadequate.
2. REJECT_MECHANISM_TIMING_SPECIFICITY — convergence is not specifically stronger in the forced-close window.
3. REJECT_STRUCTURAL_ECONOMIC_SCALE — median convergence cannot clear even a basic fee-scale screen.
4. DEFER_COST_HEADROOM — effect exceeds the minimal standard fee floor but is too small to justify promotion under the conservative headroom screen.
5. PASS_TO_P1_EXECUTION_FEASIBILITY — timing specificity and >=30 bps gross structural convergence both survive the pre-registered gates.

A PASS still does not mean profitability.

## Price firewall

This review and the frozen specification access no price/index values.

The next action requires separate explicit authorization limited to:

- Bybit affected-contract 1m kline price fields;
- Bybit official index 1m kline price fields;
- derived basis at the three registered snapshots.

Returns, PnL, L1/L2, individual trades, funding values, external venues and trading remain closed.
