# SC001-E007 — Extreme Short-Horizon Displacement -> Partial Mean Reversion Research Plan v0.1

Date: 2026-09-15  
Status: **PLANNING DOCUMENT — NO E007 ALPHA AUTHORIZED**

## 1. Purpose

Open a genuinely new SC001 candidate after terminal E001/E002/E003/E004/E006 failures.

E007 is not a rescue of any failed experiment and must not inherit tuned parameters from them.

## 2. Core hypothesis

A sufficiently large short-horizon BTC perpetual price displacement can sometimes be driven partly by temporary liquidity vacuum, forced deleveraging or one-sided aggressive flow.

If the displacement overshoots the short-run clearing price, a subsequent partial mean reversion may be large enough to be economically relevant for a one-leg taker strategy.

Primary direction under consideration:

**trade only reversal against the displacement**, not continuation.

The hypothesis is deliberately narrower than generic large-jump continuation/reversal to avoid choosing the better direction after outcomes.

## 3. Why E007 is now prioritized

The branch-level evidence after E001-E006 is:

- ordinary predictive/microstructure continuation effects are too small for standalone taker economics;
- volatility-compression breakout left near-zero residual edge;
- positive spot/perp basis dislocations of economically large size were too rare and insufficiently profitable;
- repeated post-event continuation families have not produced enough monetizable residual movement.

E007 changes the economic story: the target event is itself a large displacement, and the intended response is a partial liquidity-shock reversal rather than continuation of an already-visible move.

## 4. Economics-first constraint

Before any alpha output, the executable protocol must require an event whose natural movement scale is large enough that a plausible partial reversion can clear the approximately 10 bps single-instrument round-trip regular-user taker-fee reference with material headroom.

A threshold that mechanically produces many small events is unacceptable.

The exact event window, absolute displacement threshold, entry delay, response horizon and reversion target are not frozen by this planning document.

## 5. Data scope

Use only already-qualified OKX `BTC-USDT-SWAP` March-2024 trade archives for the initial Discovery design.

Discovery candidate performance interval remains:

- 2024-03-01..20.

2024-03-21 remains boundary-only/performance-excluded where D+1 reconstruction requires it.

Do not access Q2, formal Validation or Final.

No new L2 acquisition is authorized before trade-tape gross economics justify it.

## 6. Mandatory pre-alpha audit questions

Before freezing the executable protocol, answer from first principles and implementation constraints only:

1. What causal price statistic should define the displacement without future leakage?
2. What absolute bps threshold is economically meaningful before looking at E007 returns?
3. What displacement window is short enough to represent a shock but long enough to avoid single-print noise?
4. Should trigger require a strict crossing from below an absolute threshold?
5. How should duplicate timestamps/order be resolved?
6. What entry latency and tolerance are realistic for taker execution?
7. What fixed exit rule best represents partial mean reversion without using hindsight?
8. What maximum hold prevents the experiment from drifting into a different regime?
9. What no-overlap/cooldown/daily-cap rule prevents clustered cascades from dominating inference?
10. What gross-economics hurdle provides clear margin above approximately 10 bps fees?
11. What day-breadth/concentration/bootstrap/latency-stress gates are required?
12. Which tiny diagnostic neighborhood, if any, may be inspected only after the primary verdict and never rescue it?

## 7. Anti-overfitting firewall

Before first E007 alpha:

- freeze one primary causal mechanism;
- freeze event threshold/window/entry/exit/hold/latency;
- freeze Discovery and Confirmation dates;
- freeze economics and robustness gates;
- freeze output schemas and implementation identity;
- pass a no-alpha implementation preflight.

Do not select parameters from E007 return plots, best days, best hours, event signs or latent winner grids.

## 8. Base-feature firewall

Base E007 must not use:

- E002 TFI;
- E003 FLOW_IMPULSE;
- E004 compression state;
- E006 basis state;
- funding/event/day/hour filters selected after outcomes;
- winner-only long/short selection after alpha.

Any later auxiliary feature requires an independently viable E007 base and a separate experiment identifier.

## 9. Promotion philosophy

Discovery promotion must require both:

- enough event count / active-day breadth to support inference; and
- gross edge materially above taker costs under latency stress.

Mean alone is insufficient. Frozen gates should include at minimum:

- completed trades;
- completion rate;
- active days;
- pooled mean;
- symmetric trimmed mean;
- pooled median;
- median active-day mean;
- positive-day share;
- day-block bootstrap lower bound;
- top-day concentration;
- side/sign balance where applicable;
- latency stress;
- turnover ceiling.

## 10. Stop rules

If the frozen primary fails Discovery:

- terminal E007 Discovery FAIL;
- do not lower the jump threshold;
- do not change reversal to continuation;
- do not retune the hold/exit;
- do not add auxiliary filters;
- do not open Confirmation/L2/Q2/Validation/Final for rescue.

## 11. Immediate next action

Do not run E007 yet.

First perform a critical financial/mathematical/programming review of this plan and freeze the exact causal/economic executable protocol before any E007 price-response output is calculated.
