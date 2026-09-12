# SC001-E002 DEV-Confirmation Results v0.1

Verdict: **CONFIRMATION_PASS**  
Parent experiment: `SC001-E002 — Aggressive Trade-Flow Continuation Screen`  
Confirmation protocol commit: `ed0aa3e6f462421c7b057bb1ab57b903dc541f95`  
Scope: 10 frozen DEV-CONFIRMATION days, 2024-Q1 + 2024-Q2

## Frozen confirmation outcome

The unchanged 5-second signed-notional aggressive trade-flow continuation feature passed the one-time chronological DEV-CONFIRMATION holdout.

Primary 100 ms latency:

- positive daily Spearman: 10 / 10;
- median daily Spearman: `0.07890232206324495`;
- mean daily Spearman: `0.08129879342769537`;
- minimum daily Spearman: `0.03478489360594186`;
- maximum daily Spearman: `0.15922688411693628`;
- one-sided sign-test p-value for 10/10 positives under a 50/50 sign null: `0.0009765625`;
- frozen discovery median: `0.12936691569403583`;
- frozen 50% retention threshold: `0.06468345784701792`;
- observed retention ratio versus discovery median: about `60.99%`;
- positive extreme-decile spread days: 10 / 10;
- median daily extreme-decile spread: `0.27767948805452725` bps;
- 2024-Q1 median Spearman: `0.086705639006201`;
- 2024-Q2 median Spearman: `0.06901694865960636`;
- event-day median Spearman: `0.06444416579106986`;
- ordinary-day median Spearman: `0.09278353124567618`.

Stress / diagnostic latency:

- 250 ms: 10/10 positive days; median daily Spearman `0.07301080901557631`; median extreme spread `0.24929831956077456` bps;
- 500 ms diagnostic: 10/10 positive days; median daily Spearman `0.06696632145281123`; median extreme spread `0.2254090007980556` bps.

All frozen confirmation gates passed.

## Critical interpretation

This is materially stronger evidence than the original DEV-DISCOVERY screen because the exact same feature, horizon, direction, and latency definitions were evaluated once on a chronologically later internal holdout without retuning.

The effect attenuated from discovery: median daily Spearman fell from about `0.1294` to about `0.0789`, retaining roughly 61% of the discovery magnitude. This is compatible with ordinary regression-to-the-mean and still clears the pre-frozen 50% retention gate.

The extreme-decile response spread did not collapse; its confirmation median was about `0.278` bps, slightly above the discovery median of about `0.251` bps. However, this remains a very small gross transaction-price response before observed spread, taker fees, L2 depth consumption, slippage, order-size discreteness, and market impact.

Directional hit rate is not the central strength of the feature. Across the 10 confirmation days the median extreme-decile directional hit rate is about 49.8% and the mean about 49.6%. The feature therefore continues to look more like a return-ranking / conditional-magnitude signal than a high-win-rate directional classifier.

The exact sign-test result is supportive but must not be treated as a universal IID false-positive probability; the frozen UTC day remains the inferential block and market days can share common regimes.

## Status boundary

- strategy P&L calculated: **NO**;
- executable L2 profitability calculated: **NO**;
- official Validation accessed: **NO**;
- Final accessed: **NO**.

Per the frozen protocol, `CONFIRMATION_PASS` does **not** promote E002 to `ROBUST_HISTORICAL_CANDIDATE`. The parent remains `PROMISING_SCREEN`, now with successful internal chronological confirmation.

## Decision / next stage

Do not tune E002 on B04/B05 and do not open formal Validation yet.

The next justified stage is same-venue microstructure qualification: prove that the E002 signal, or an economically equivalent same-venue feature, exists on data compatible with the venue where L2 execution will be simulated; then test conservative taker economics with observed spread/depth, frozen latency scenarios, fees, and depth-haircut robustness.

Any threshold optimization, window/horizon change, event exclusion, side selection, or venue translation is a new experiment and must be frozen separately before evaluation.
