# SC001-E002 Confirmation-Step Expert Review v0.1

Status: **REVIEWED AFTER DEV-DISCOVERY, BEFORE DEV-CONFIRMATION ACCESS**  
Parent experiment: `SC001-E002 — Aggressive Trade-Flow Continuation Screen`  
Discovery verdict: `PROMISING_SCREEN`

## 1. What is actually established

E002 established a robust predictive association on the 15 frozen DEV-DISCOVERY days, not an executable strategy.

At 100 ms latency the discovery screen produced:

- positive daily Spearman on 15/15 days;
- median daily Spearman = `0.12936691569403583`;
- positive extreme-decile spread on 15/15 days;
- median daily top-minus-bottom extreme-decile spread = `0.2511011965119265` bps;
- positive quarter medians in 2023-Q2, Q3, Q4;
- positive event-day and ordinary-day medians.

The effect also remained positive on all 15 days at 250 ms and 500 ms.

This is sufficient to justify an internal holdout confirmation. It is not sufficient to claim net profitability because no historical spread, L2 depth, exchange fee, or executable fill model was applied.

## 2. Financial critique

### 2.1 Statistical strength is stronger than economic magnitude

The discovery association is unusually consistent by sign, but the measured transaction-price response is small in economic units.

The median top-minus-bottom decile differential is only about `0.2511` bps at 100 ms. For an equal-count directional interpretation (long top decile, short bottom decile), the gross average directional response per trade is approximately half of the long-short differential, about `0.1256` bps before spread, fees, depth impact, and execution uncertainty.

Therefore the correct interpretation is: **useful predictive feature family, not yet a standalone tradable edge**.

### 2.2 Trade-price response can differ from executable return

E002 labels use first transaction prices after frozen latencies. They do not use bid/ask quotes or book depth. Persistence in aggressive order flow can produce a positive predictive relationship while still being economically consumed by crossing costs.

Thus the next step must remain a prediction confirmation, not a P&L backtest.

### 2.3 Do not tune after the 15/15 result

Because discovery was exceptionally clean, the largest current methodological risk is researcher overreaction: changing the window, selecting stronger event classes, creating a threshold from the discovery deciles, or choosing only the best side.

All such modifications are rejected before confirmation. The exact 5s/5s/100ms continuation construction is carried forward unchanged.

## 3. Statistical critique of the confirmation design

The 10 reserved DEV-CONFIRMATION days are a chronological internal holdout: 2024-Q1 and 2024-Q2, five frozen strata per quarter.

They must be evaluated together. No feature result may be calculated on B04 alone and used to decide whether/how to process B05.

The UTC day remains the inferential block. Individual 5-second observations are not treated as IID evidence.

For 10 independent sign blocks, an exact one-sided sign test gives:

- `P[X >= 8] = 0.0546875`;
- `P[X >= 9] = 0.0107421875`;
- `P[X = 10] = 0.0009765625`.

Therefore the primary confirmation sign gate is frozen at **>=9 positive days out of 10**. An 8/10 outcome is not treated as a clean confirmation.

## 4. Effect-size retention

A sign-only test could pass with a nearly zero effect. To guard against that, the confirmation median daily Spearman must retain at least 50% of the discovery median.

Frozen discovery median: `0.12936691569403583`.

Frozen 50% retention threshold: `0.06468345784701792`.

The 50% rule is deliberately simple and fixed before the confirmation data are accessed. It allows substantial regression to the mean while rejecting a collapse to a negligible association.

This threshold is a confirmation-quality gate, not a claim that Spearman `0.0647` is economically tradeable.

## 5. Frozen confirmation gates

At the unchanged 100 ms primary latency:

1. positive daily Spearman on at least 9/10 days;
2. median daily Spearman > 0;
3. median daily Spearman >= `0.06468345784701792`;
4. median daily Spearman > 0 in both 2024-Q1 and 2024-Q2;
5. event-day median Spearman > 0;
6. ordinary-day median Spearman > 0;
7. extreme-decile spread positive on at least 8/10 days;
8. median extreme-decile spread > 0.

At the unchanged 250 ms stress latency:

9. positive daily Spearman on at least 8/10 days;
10. median daily Spearman > 0.

The 500 ms result remains diagnostic only and cannot rescue a failed primary result.

## 6. Verdict mapping

- `CONFIRMATION_PASS`: all gates 1-10 pass. Parent feature family remains `PROMISING_SCREEN`, now internally confirmed.
- `CONFIRMATION_WEAK`: primary sign and median gates 1-2 pass, but any of gates 3-10 fails.
- `CONFIRMATION_FAIL`: gate 1 or gate 2 fails.

No confirmation result may be called `ROBUST_HISTORICAL_CANDIDATE` because executable same-venue L2 economics have not yet been demonstrated.

## 7. Acquisition/peek firewall

The 10 frozen DEV-CONFIRMATION days must first be acquired and data-qualified with **no E002 feature calculation and no P&L**.

Both B04 and B05 must pass data integrity before the frozen confirmation screen is run once on the combined 10-day set.

Forbidden before the combined confirmation run:

- inspecting TFI correlations on B04 alone;
- selecting or dropping days because of market behavior;
- changing the 5s lookback, 5s horizon, 100/250/500ms latencies, continuation sign, decile construction, or gates;
- opening formal Validation or Final.

## 8. Second-pass critique and decision

A stricter alternative would require 10/10 positive days. That was rejected as unnecessarily brittle for only 10 blocks and is not required to establish replication. A looser 8/10 primary gate was also rejected because its exact one-sided sign probability is `0.0546875`, slightly above 5%.

A direct P&L test on Binance aggTrades was rejected because the data do not contain historical executable spread/depth. Immediate OKX L2 acquisition was also rejected because it would skip the cheap internal replication step and spend resources before determining whether the feature survives a chronological holdout.

Final decision: **freeze the exact E002 feature, acquire all 10 DEV-CONFIRMATION days data-only, then run one combined confirmation screen.**

If confirmation passes, the next stage is same-venue feature/execution qualification (preferably using replayable L2 plus same-venue trade-flow evidence) before any net-profitability claim.