# SC001-E002 Hypothesis Review v0.1

Status: **PRE-TEST DESIGN REVIEW**  
Branch: SC001  
Purpose: select and stress-test the first serious sub-minute hypothesis after DEV-DISCOVERY acquisition completed.

## Starting point

Qualified discovery data now consists of 15 frozen Binance BTCUSDT USD-M aggTrades days across 2023-Q2/Q3/Q4, approximately 18.19 million aggTrades. B04/B05 remain unopened DEV-CONFIRMATION. Validation and Final remain unopened.

The task is not to assume a profitable scalping strategy exists. The task is to test one economically coherent, falsifiable feature hypothesis with minimal degrees of freedom.

## Candidate families considered

### A. Raw aggressive trade-flow continuation
Large buyer-initiated notional imbalance should predict positive short-horizon price response; large seller-initiated imbalance should predict negative response.

Pros:
- directly measurable from qualified aggTrades;
- economically coherent through order-flow persistence / adverse-selection pressure;
- simple enough to falsify cleanly;
- no order-book reconstruction required for the first screen.

Cons:
- same-window order flow and price are mechanically related, so contemporaneous association can masquerade as prediction;
- transaction-price labels contain bid/ask bounce and are not executable mid/ask/bid prices;
- trade-flow relationships can be unstable across regimes;
- Binance trade-flow evidence cannot be treated as an OKX executable strategy without separate same-venue qualification.

Conclusion: viable only as a **predictive feature screen**, not as a backtest or profitability claim.

### B. Extreme-flow exhaustion / reversal
Very large aggressive flow with weak price response may indicate absorption and subsequent reversal.

Pros:
- plausible liquidity-absorption mechanism;
- may outperform naive continuation after transient price impact.

Cons:
- requires at least two jointly chosen features (flow extremity + impact efficiency), additional thresholds, and therefore materially more researcher degrees of freedom;
- substantially higher overfitting risk on only 15 discovery days;
- cleaner as a later, separate hypothesis if simple continuation is falsified.

Conclusion: reject as the first experiment; reserve for a new experiment ID if needed.

### C. L2 imbalance / microprice first
Order-book imbalance and microprice are closer to the primary OKX execution venue.

Pros:
- stronger microstructure link to short-horizon price formation;
- supports same-venue execution modeling later.

Cons:
- full-day OKX L2 is expensive on the phone;
- using it before a cheaper signal-family screen would spend much more engineering/storage budget before knowing whether aggressive-flow pressure deserves further work.

Conclusion: do not start here. Use the cheap Binance screen as a kill/advance gate, then move to same-venue OKX only if the family survives.

## First critique result

The initial idea of immediately defining a thresholded long/short scalp from Binance aggTrades was rejected.

Reasons:
1. arbitrary threshold choice would create hidden tuning freedom;
2. a trade-price backtest would falsely imply executable spread/depth information that aggTrades do not contain;
3. a Binance signal executed on OKX would become a cross-venue latency strategy, explicitly outside the first-candidate scope;
4. sweeping multiple lookbacks/horizons would inflate false-discovery risk.

## Optimized hypothesis

Use a **continuous predictive screen** rather than a thresholded strategy.

Feature at decision time `t`:

`TFI_5s(t) = sum(sign_i * price_i * qty_i) / sum(price_i * qty_i)`

for trades in the immediately preceding non-overlapping 5-second bucket `[t-5s, t)`.

Aggressor sign:
- `is_buyer_maker = false` -> buyer is taker -> `+1`
- `is_buyer_maker = true` -> seller is taker -> `-1`

Decision grid: every 5 seconds.

Primary label:
- simulated observation latency = 100 ms;
- entry reference = first transaction price at or after `t + 100ms`;
- exit reference = first transaction price at or after `t + 5100ms`;
- response = log(exit / entry) in basis points.

This is explicitly a **future transaction-price response**, not P&L and not an execution fill model.

Primary directional hypothesis:

`Spearman(TFI_5s, future_5s_response) > 0` consistently across days.

## Why 5s / 5s

The 5-second formation and 5-second response horizon are frozen because they:
- are genuinely sub-minute;
- avoid millisecond-scale claims unsupported by this data layer;
- reduce micro-noise relative to 100-500 ms windows;
- remain short enough to represent a scalping feature;
- allow a non-overlapping 5-second decision grid, sharply reducing pseudo-replication.

No alternate 1s/2s/10s grid is searched under E002.

## Statistical design

The primary inferential unit is the **UTC day**, not individual 5-second observations.

For each of the 15 days calculate:
- daily Spearman correlation between TFI and future response;
- top-decile minus bottom-decile future-response spread;
- extreme-decile directional hit rate.

Primary sign gate:
- at least 12 of 15 daily Spearman correlations must be positive.

Under a 50/50 null, a one-sided exact sign test for 12/15 or more positives has `p = 0.017578125`.

Additional mandatory robustness gates:
- median daily Spearman > 0;
- median Spearman > 0 in each of 2023-Q2, Q3, Q4;
- event-day median > 0;
- ordinary-day median > 0;
- extreme-decile spread positive on at least 10/15 days;
- median extreme-decile spread > 0;
- at 250 ms stress latency: positive Spearman on at least 10/15 days and median > 0.

500 ms is diagnostic only.

## Multiple-testing control

E002 counts as one tested hypothesis family and one frozen primary parameterization:
- lookback = 5s;
- grid = 5s;
- response horizon = 5s;
- direction = continuation;
- primary latency = 100ms.

No parameter grid and no post-result threshold optimization are permitted under E002.

## Second critique

### Objection: Binance is not the primary OKX execution venue
Valid. Therefore E002 cannot become an executable strategy by itself.

Resolution: E002 is a cheap **feature-family screen**. If it fails, we avoid expensive OKX acquisition for this family. If it passes, the next experiment must qualify/construct the same feature on a same-venue dataset before any executable OKX claim.

### Objection: transaction prices contain bid/ask bounce
Valid. Therefore only cross-day monotonic predictability is tested here. Net profitability, spread crossing, depth, fees and latency execution remain untested.

### Objection: 15 days are too few
They are too few for a final claim, but sufficient for a development screen because the test uses 15 day-level blocks across three quarters and five frozen day strata per quarter. B04/B05, formal Validation and Final remain untouched.

### Objection: positive correlation may be statistically real but economically tiny
Valid. Therefore `PROMISING_SCREEN` means only that the feature family survives predictive screening. It never means profitable or tradable. Economic viability is deferred to same-venue execution/cost analysis.

## Final design decision

Proceed with `SC001-E002 — Aggressive Trade-Flow Continuation Screen` exactly as above.

Possible outcomes:
- `PROMISING_SCREEN`: all primary and 250ms robustness gates pass;
- `WEAK`: primary association gates pass but 250ms robustness fails;
- `FAIL`: primary association gates fail.

If E002 is `FAIL`, no rescue by changing lookback, horizon, sign, threshold, day subset, event subset or latency under the same experiment ID.
