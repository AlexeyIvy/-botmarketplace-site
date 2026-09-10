# R009-X002 — Fixed Cross-Asset Breadth Panel Results v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** completed post-ETH breadth diagnostic  
**Decision:** **CROSS_ASSET_BREADTH_MIXED**  
**Protocol:** `docs/research/r009-x002-cross-asset-breadth-panel-protocol-v0.1.md`

## 1. Executive conclusion

The fixed five-asset panel produces **3 SUPPORT / 2 MIXED / 0 FAIL**.

Formal panel decision under the prospectively frozen rule is:

> **CROSS_ASSET_BREADTH_MIXED**

The threshold for `CROSS_ASSET_BREADTH_SUPPORT` was at least 4 SUPPORT and zero FAIL, so the panel does not earn full breadth support.

At the same time, the result materially weakens the idea that R009 is purely a BTC-history artifact. The exact unchanged architecture passes all hard contradiction checks on all five additional assets and earns full per-asset SUPPORT on BNB, ADA and SOL.

This remains a post-ETH breadth diagnostic, not independent confirmation and not a basis for selecting the best-performing coin.

## 2. Data integrity

All five source gates pass.

| Asset | Clean rows | Start | End | First full year | One-day gap share | Max gap |
|---|---:|---|---|---:|---:|---:|
| BNB | 3,230 | 2017-11-06 | 2026-09-09 | 2018 | 100% | 1d |
| LTC | 3,193 | 2017-12-13 | 2026-09-09 | 2018 | 100% | 1d |
| XRP | 3,051 | 2018-05-04 | 2026-09-09 | 2019 | 100% | 1d |
| ADA | 3,068 | 2018-04-17 | 2026-09-09 | 2019 | 100% | 1d |
| SOL | 2,221 | 2020-08-11 | 2026-09-09 | 2021 | 100% | 1d |

No asset was dropped or substituted.

## 3. Baseline 10 bps headline results

| Asset | Decision | R009 CAGR | Max DD | Calmar | Avg risky weight |
|---|---|---:|---:|---:|---:|
| BNB | SUPPORT | 12.22% | -14.99% | 0.82 | 12.45% |
| LTC | MIXED | 4.12% | -22.18% | 0.19 | 13.72% |
| XRP | MIXED | 6.21% | -20.69% | 0.30 | 13.06% |
| ADA | SUPPORT | 11.53% | -21.96% | 0.53 | 13.16% |
| SOL | SUPPORT | 19.66% | -24.44% | 0.80 | 13.37% |

Do not compare these as a winner table: primary windows differ and the panel was not designed for asset selection.

## 4. Why LTC is MIXED

LTC passes all hard contradiction checks and most central checks.

The applicable PRE_2020 comparison fails:

- R009_COMBINED CAGR ~0.52%;
- TREND10 CAGR ~3.95%.

The crisis sleeve is nearly permanently active on LTC:

- PRIMARY crisis active ~99.68%;
- fully deployed ~95.78%;
- POST_2023 crisis active/full = 100% / 100%.

The crisis episode beginning 2021-05-15 is still open/censored at the sample endpoint.

This is consistent with the ETH failure mode: sticky-to-new-ATH can become prolonged distressed beta rather than rare dry powder.

## 5. Why XRP is MIXED

XRP passes all hard contradiction checks but fails several central robustness checks.

At baseline 10 bps:

- PRIMARY R009 CAGR ~6.21% versus STATIC10 ~6.13% — only a narrow growth edge;
- PRE_2020 R009 ~-4.44%, below TREND10 ~-0.71% and below STATIC10 ~-3.56%;
- R009 is Pareto-dominated by STATIC15 daily/monthly on PRIMARY under the frozen rule.

At 50 bps:

- R009 PRIMARY CAGR ~4.92%;
- STATIC10 ~5.70%.

The crisis sleeve is again highly persistent: ~97.40% active on PRIMARY and ~81.88% fully deployed.

## 6. SUPPORT assets

BNB, ADA and SOL pass every applicable central check.

This matters because their unchanged-rule support appears despite materially different histories and volatility paths. It is evidence that the broad interaction between trend gating and crisis-state allocation can be economically coherent outside BTC.

However this does not imply these assets should replace BTC or be added to production. SOL, for example, has the highest panel CAGR but also a ~-24.44% Max DD and a shorter available history; it may not be selected as a new preferred asset from this diagnostic.

## 7. Repeated structural limitation across assets

Crisis-active fractions on PRIMARY:

- BNB ~88.41%;
- LTC ~99.68%;
- XRP ~97.40%;
- ADA ~96.05%;
- SOL ~92.83%.

Fully deployed fractions:

- BNB ~48.49%;
- LTC ~95.78%;
- XRP ~81.88%;
- ADA ~86.54%;
- SOL ~64.29%.

This confirms that sticky-until-new-ATH is not merely an ETH anomaly. Across most altcoin histories it behaves as long-duration distressed beta.

Therefore the right economic description remains **state-dependent beta handoff**, not proven crisis alpha, true convexity, or rare dry-powder deployment.

## 8. Cross-asset inference after BTC + ETH + breadth panel

Evidence now supports two simultaneous statements:

1. R009 is not obviously BTC-only: the unchanged architecture remains coherent across a broad fixed panel and produces no hard failures.
2. Its crisis sleeve has a systematic portability weakness: on assets with long failure to regain prior ATH, it can remain fully deployed for years and degrade the trend-only advantage.

These observations strengthen the case for continuing the already-frozen BTC forward, but they do not justify historical reset-rule tuning.

## 9. Research decision

- Preserve BTC R009-E002 as the primary forward candidate unchanged.
- Do not select SOL/BNB/ADA as replacement winners.
- Do not expand the altcoin panel further.
- Do not tune crisis thresholds/reset using inspected cross-asset results.
- Record the sticky crisis persistence as a known structural weakness to be judged by future forward evidence and any genuinely new prospectively defined architecture, not by rescue fitting.
- Proceed with the already scheduled R009 + R003 forward technical initialization.
- After a clean forward initialization, continue to R009 capital granularity G001/G002 as precommitted.

## 10. Evidence status

This experiment is a post-ETH fixed breadth diagnostic only.

It does not provide temporal OOS evidence, does not prove antifragility, does not authorize demo/live trading, and does not alter the original BTC forward clock.
