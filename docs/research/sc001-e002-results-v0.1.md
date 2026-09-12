# SC001-E002 Results v0.1

Status: **PROMISING_SCREEN**

Experiment: `SC001-E002 — Aggressive Trade-Flow Continuation Screen`
Protocol commit: `4022da85f5ffb873d558ccda74d20b8c16272ba7`
Scope: DEV-DISCOVERY only, B01+B02+B03 = 15 preselected days

## Result

The frozen 5-second signed-notional aggressive trade-flow imbalance screen produced a positive same-direction future transaction-price response on all 15 Development-discovery days.

Primary 100 ms latency:

- positive daily Spearman: 15 / 15;
- median daily Spearman: 0.12936691569403583;
- mean daily Spearman: 0.11265265577411476;
- one-sided sign-test p-value for 15/15 positives under a 50/50 sign null: 3.0517578125e-05;
- positive extreme-decile spread days: 15 / 15;
- median daily top-minus-bottom extreme-decile response: 0.2511011965119265 bps;
- all three quarter medians positive;
- event-day median Spearman positive;
- ordinary-day median Spearman positive.

Stress robustness:

- 250 ms median daily Spearman: 0.12283039200743287, 15/15 positive days;
- 500 ms diagnostic median daily Spearman: 0.11271420141383104, 15/15 positive days;
- median extreme-decile spread declines from 0.2511 bps at 100 ms to 0.2333 bps at 250 ms and 0.2056 bps at 500 ms.

All frozen E002 screen gates passed.

## Critical interpretation

This is a strong **predictive-screen** result, not a trading-profitability result.

The positive sign is unusually consistent across the 15 preselected days and across all three quarters, including event and ordinary strata. The effect also degrades gradually rather than disappearing when latency rises from 100 ms to 250/500 ms, which supports the claim that the measured continuation is not solely an instantaneous timestamp artifact.

However, the economic magnitude remains small. The median 100 ms extreme-decile response spread is only about 0.251 bps, falling to about 0.206 bps at 500 ms. No L2 spread, depth impact, exchange fee, or realizable taker fill model is included in E002. Therefore the result does **not** establish that a 5-second taker strategy is net profitable; realistic round-trip trading costs may easily exceed the measured response magnitude.

The extreme-decile directional hit-rate is not itself strong: most days are below 50%, while the conditional mean return spread remains positive. This indicates that the signal's predictive content is primarily in return ranking/magnitude rather than a high-probability directional classifier. It must not be marketed as a high-win-rate strategy.

The one-sided sign-test p-value is a useful frozen diagnostic, but the 15 days are stratified market days rather than guaranteed IID Bernoulli trials. It should not be interpreted as an exact universal false-positive probability. The later holdout stages remain necessary.

## Firewall state

- strategy P&L calculated: **NO**;
- execution/L2 profitability calculated: **NO**;
- B04/B05 accessed: **NO**;
- official Validation accessed: **NO**;
- Final accessed: **NO**.

B04/B05 remain the internal DEV-CONFIRMATION holdout.

## Decision

Classification remains `PROMISING_SCREEN`.

The next justified step is **not** to optimize the 5-second window, choose a threshold, add filters, or open official Validation. Freeze a separate internal confirmation protocol that repeats the exact E002 feature/response definition on B04/B05 without retuning. Only if the predictive effect replicates should SC001 spend additional effort on same-venue L2/execution economics and a candidate trading rule.

Any attempt to change the lookback, horizon, latency, imbalance formula, event filter, direction, or threshold after this result is a new hypothesis/experiment and must be counted separately.
