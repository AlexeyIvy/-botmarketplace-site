# R009 Cross-Asset Structural Synthesis v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Scope:** BTC E001 + ETH X001 + fixed five-asset X002 breadth diagnostic

## 1. Evidence table

| Asset | Evidence role | Formal status | Primary CAGR | Max DD | Calmar |
|---|---|---|---:|---:|---:|
| BTC | original mechanism screen; forward active | PROMISING_SCREEN | 15.02% | -15.73% | 0.95 |
| ETH | pre-frozen second-asset falsification | UNCHANGED_RULE_MIXED | 9.35% | -21.11% | 0.44 |
| BNB | post-ETH breadth diagnostic | SUPPORT | 12.22% | -14.99% | 0.82 |
| LTC | post-ETH breadth diagnostic | MIXED | 4.12% | -22.18% | 0.19 |
| XRP | post-ETH breadth diagnostic | MIXED | 6.21% | -20.69% | 0.30 |
| ADA | post-ETH breadth diagnostic | SUPPORT | 11.53% | -21.96% | 0.53 |
| SOL | post-ETH breadth diagnostic | SUPPORT | 19.66% | -24.44% | 0.80 |

Primary windows differ across assets; this is not a ranking table and cannot be used for winner selection.

## 2. Main conclusion

The broad trend-gated + crisis-state allocation interaction is not unique to BTC. Three of five fixed additional assets pass the full per-asset gate, two are MIXED, and none hits a hard contradiction.

However risk efficiency is uneven and the crisis sleeve's sticky-to-new-ATH rule repeatedly becomes persistent distressed beta on assets that remain below old ATHs for long periods.

Therefore the strongest defensible current claim is:

> **R009 has partial cross-asset structural breadth, but its risk-efficiency and crisis-sleeve behavior are not robustly portable enough to call the architecture universally validated.**

## 3. What breadth evidence does and does not change

It strengthens confidence that the combined mechanism is not purely a BTC backtest coincidence.

It does not change:

- BTC as the current primary forward candidate;
- the frozen BTC R009-E002 rules or inception;
- the prohibition on historical reset/threshold/weight tuning;
- the requirement for forward evidence, capital-granularity realism, demo execution, safe-sleeve design and later real-world risk controls.

## 4. Structural weakness to carry forward

The recurring weakness is not ordinary transaction cost sensitivity. It is regime persistence.

If an asset enters a deep drawdown and does not make a new ATH for years, the crisis sleeve can remain near/full deployment for years. In those regimes R009 can lose the trend-only sleeve's defensive advantage.

This weakness is now treated as a known architectural property, not a parameter-search invitation.

## 5. Next action

No further cross-coin historical sweep is justified now.

The next higher-value evidence is:

1. technically clean initialization of the already-frozen BTC R009 and R003 forward trackers;
2. capital-granularity G001/G002 for BTC R009 after forward plumbing is verified;
3. continued forward accumulation without retuning.
