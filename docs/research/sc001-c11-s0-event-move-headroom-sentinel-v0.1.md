# SC001 — C11-S0 Scheduled Macro Release Move-Headroom Sentinel v0.1

Date: 2026-09-18
Status: **FROZEN BEFORE FIRST C11 BTC EVENT-MOVE OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c11-d1-h1-event-archive-metadata-pass-result-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.16.json`;
- `docs/research/sc001-edge-to-fill-structural-preflight-v0.1.md`.

## 1. Purpose

Cheapest first price-bearing test for C11:

> Do scheduled CPI / Employment releases produce broad enough 60-second BTC repricing to justify later causal first-impulse direction and event-execution research?

This sentinel tests **absolute event-move headroom only**.

It does not test direction, continuation, macro surprise, entry timing or PnL.

## 2. Frozen calibration batch

Exactly the 12 H1-2025 events qualified in C11-D1.

No event may be added, removed, reclassified or selected by outcome.

## 3. Frozen source

BTC-USDT-SWAP historical trades.

For each event date, use the exact D archive qualified by C11-D1.

Because all frozen release timestamps are 12:30 or 13:30 UTC, the event window is contained inside the qualified OKX D archive under previously established archive-boundary semantics.

## 4. Frozen event-price anchors

For event timestamp `T`:

### Pre-event anchor
Use the chronologically last BTC trade with:

`trade_ts < T`

and require:

`T - trade_ts <= 1000 ms`.

### +60s anchor
Use the chronologically last BTC trade with:

`trade_ts <= T + 60s`

and require:

`(T + 60s) - trade_ts <= 1000 ms`.

No interpolation.

No future trade relative to either anchor.

## 5. Frozen move statistic

`abs_move_60s_bps = 10000 * abs(ln(price_60s / price_pre))`

No sign is used for the strategy verdict.

Family labels CPI/Employment are reported descriptively only.

No family-specific gate or winner selection.

## 6. Structural burden reference

Prospective later directional architecture:

- taker entry;
- taker exit;
- two structural fills.

Frozen reference:

- 5 bps/fill fee reference = 10 bps;
- event spread/slippage/model reserve = 10 bps;
- structural burden reference = `20 bps`.

S0 does not claim this is an exact executable cost estimate.

## 7. Sample gates

Require:

- all 12 event archives pass source/schema/order checks;
- all 12 events have valid pre-event and +60s anchors.

Otherwise:

`C11_S0_DEFER_SAMPLE`

No event may be dropped.

## 8. Structural headroom gates

SURVIVE only if all:

- events with `abs_move_60s_bps >=20` >= `6 of 12`;
- median `abs_move_60s_bps >=20`;
- p75 `abs_move_60s_bps >=30`;
- maximum `abs_move_60s_bps >=50`.

Exact survive token:

`C11_S0_EVENT_MOVE_HEADROOM_SURVIVE`

If sample gates pass but any headroom gate fails:

`C11_S0_REJECT_EVENT_MOVE_HEADROOM`

## 9. Interpretation

SURVIVE means only that scheduled macro events create enough raw one-minute repricing scale to justify a later **causal first-impulse continuation/reversal** test and event-execution modeling.

It does not establish:

- usable direction;
- continuation after the first second;
- executable event fills;
- net profitability.

## 10. No-rescue rules

After output do not:

- add FOMC;
- remove weak CPI or Employment events;
- split by event family to rescue;
- lower 20 bps;
- change 60 seconds;
- use release surprise values;
- use C5/C10 execution vetoes;
- search entry delay.

A materially different event mechanism requires a new ID.

## 11. Firewalls

Must remain false:

- macro_release_value_accessed;
- macro_surprise_calculated;
- first_impulse_direction_calculated;
- continuation_outcome_calculated;
- strategy_signal_calculated;
- execution_fill_model_calculated;
- pnl_calculated;
- promotional_alpha_accessed.
