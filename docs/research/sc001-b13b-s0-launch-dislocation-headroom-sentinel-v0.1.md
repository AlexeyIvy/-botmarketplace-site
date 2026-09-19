# SC001 — B13-B S0 Launch Dislocation Headroom Sentinel v0.1

Date: 2026-09-19
Status: **FROZEN BEFORE FIRST B13-B PRICE OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-b13b-exact-7-event-launch-set-freeze-v0.1.md`;
- `docs/research/sc001-b13b-historical-launch-census-governance-review-v0.1.md`;
- `docs/research/sc001-edge-to-fill-structural-preflight-v0.1.md`;
- `docs/research/sc001-c8-d1e-strict-coactive-1s-clock-qualification-protocol-v0.1.md`.

## 1. Purpose

Cheapest first price-bearing test for B13-B:

> Do the exact frozen survivor-censored OKX launch events exhibit enough immediate cross-venue relative-price dislocation versus a mature Bybit reference to justify a later convergence study?

This sentinel tests **absolute launch dislocation headroom only**.

It does not test:

- convergence;
- persistence;
- direction profitability;
- entry/exit timing;
- execution;
- PnL.

## 2. Frozen event batch

Exactly the seven events frozen in:

`docs/research/sc001-b13b-exact-7-event-launch-set-freeze-v0.1.md`

Evidence role:

`NONPROMOTIONAL_SURVIVOR_CENSORED_STRUCTURAL_CALIBRATION`

No event may be added, removed or replaced by outcome.

## 3. Frozen source bodies

For each event use exactly:

- frozen OKX launch-day SWAP trade ZIP;
- frozen Bybit same-underlying launch-day public trade GZIP.

Before body access require:

- exact filename;
- re-HEAD positive Content-Length;
- D0 identity consistency.

No alternate venue/reference.

## 4. Source schema semantics

### OKX

Accept exactly:

LEGACY_6:

`instrument_name,trade_id,side,price,size,created_time`

or SOURCE_7:

`instrument_name,trade_id,side,price,size,created_time,source`

For SOURCE_7:

`source in {"0","1"}`

The source field is diagnostic only.

### Bybit

Require the already-qualified public-trade leading schema:

`timestamp,symbol,side,size,price`

Additional trailing columns are allowed only if the first five fields match exactly.

## 5. Frozen clock representation

Inherit:

`STRICT_COACTIVE_1S_NO_CARRY_FORWARD`

For every trade:

`second_id = floor(timestamp_us / 1_000_000)`

A coactive second exists only if both venues have >=1 trade in the same second.

No carry-forward.

No interpolation.

No future trade relative to the second.

## 6. Launch decision bucket

Let `T` be exact frozen OKX listTime.

Search only the five one-second buckets:

- [T, T+1s)
- [T+1s, T+2s)
- [T+2s, T+3s)
- [T+3s, T+4s)
- [T+4s, T+5s)

Use the earliest bucket with activity on both venues.

If none exists:

`launch_price_state = NO_COACTIVE_LAUNCH_PRICE`

The event stays in the scheduled denominator.

For the selected coactive second use the chronologically last trade price from each venue inside that same second.

## 7. Frozen headroom statistic

For a coactive launch price:

`abs_launch_basis_bps = 10000 * abs(ln(price_okx / price_bybit))`

Only absolute magnitude is used for the S0 verdict.

No convergence outcome is calculated.

No later price is consulted.

## 8. Structural burden

Paired relative-value architecture implies four later structural fills.

Retain the pre-frozen B13 architecture:

- four-fill fee floor = 20 bps;
- spread/legging reserve = 10 bps;
- execution/model reserve = 10 bps;
- structural burden = `40 bps`.

Meaningful raw launch headroom threshold:

`50 bps`

The extra 10 bps is minimum reserve above structural break-even.

No maker rebate assumption.

## 9. Sample/data gate

Require all:

- exact scheduled events = 7;
- source/body/schema integrity passes for all seven archive pairs;
- coactive launch prices available for >=6/7 events;
- coactive-valid events span >=3 launch months.

If not:

`B13B_S0_DEFER_SAMPLE`

No headroom verdict.

Events with NO_COACTIVE_LAUNCH_PRICE remain in the seven-event scheduled denominator.

## 10. Headroom SURVIVE gates

SURVIVE only if all:

1. scheduled events with `abs_launch_basis_bps >=50` >= `4 / 7`;
2. median `abs_launch_basis_bps` across coactive-valid events >= `50 bps`;
3. qualifying >=50 bps events span >= `3 launch months`.

Exact survive token:

`B13B_S0_LAUNCH_DISLOCATION_HEADROOM_SURVIVE`

If sample gate passes but any headroom gate fails:

`B13B_S0_REJECT_LAUNCH_DISLOCATION_HEADROOM`

## 11. Diagnostics only

Report but do not gate on:

- first coactive bucket offset seconds;
- median/p90/p99 same-second last-event timestamp skew;
- p75 absolute launch basis;
- maximum absolute launch basis;
- OKX schema type;
- SOURCE_7 source counts.

High quantiles/max are diagnostic only.

## 12. Interpretation

SURVIVE means only:

> initial launch dislocation scale is large and broad enough in this nonpromotional survivor-censored historical calibration set to justify freezing a later convergence sentinel.

It does not establish:

- mean reversion;
- causal tradability;
- fill quality;
- profitability;
- historical opportunity rate.

REJECT means raw launch basis itself lacks enough structural headroom for this four-fill architecture.

## 13. No-rescue rules

After output do not:

- extend first-coactive search beyond 5 seconds;
- use max dislocation over a later window;
- lower 50 bps;
- lower 40 bps burden;
- drop weak events;
- select only April or a specific token;
- switch reference venue;
- use maker rebates;
- add C1-C12 features.

## 14. Confirmation/prospective boundary

This historical S0 is nonpromotional calibration only.

No historical event can become Confirmation.

If S0 survives, the next stage must be separately frozen and future launch events remain the only clean prospective chronological evidence.

## 15. Firewalls

S0 must keep false:

- convergence_calculated;
- relative_return_calculated;
- strategy_signal_calculated;
- execution_model_calculated;
- pnl_calculated;
- candidate_id_assigned;
- promotional_alpha_accessed.
