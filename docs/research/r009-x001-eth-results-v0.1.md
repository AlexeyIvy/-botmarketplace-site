# R009-X001 — ETH Unchanged-Rule Structural Falsification Results v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** completed historical cross-asset falsification  
**Decision:** **UNCHANGED_RULE_MIXED**  
**Protocol:** `docs/research/r009-x001-eth-unchanged-rule-structural-falsification-protocol-v0.1.md`

## 1. Executive conclusion

The exact frozen R009 v0.1 architecture transfers to ETH only partially.

Formal decision:

> **UNCHANGED_RULE_MIXED**

All hard contradiction checks pass, but one applicable central robustness check fails: on eligible PRE_2020 ETH history, R009_COMBINED CAGR does not exceed TREND10 CAGR.

Therefore do not retune ETH-specific parameters, do not sweep other coins, and do not promote R009 as a broadly cross-asset validated architecture. The BTC forward record remains unchanged.

## 2. Data integrity

Data gate: **PASS**.

- Binance Spot ETHUSDT daily klines;
- clean period: 2017-08-17 -> 2026-09-09;
- clean rows: 3,311;
- first full calendar year: 2018;
- PRIMARY rows: 3,174;
- primary one-day gap share: 100%;
- primary missing days: 0;
- primary max gap: 1 day;
- duplicate dates: 0.

## 3. Baseline 10 bps results

| Strategy | PRIMARY CAGR | Max DD | Calmar | Ending |
|---|---:|---:|---:|---:|
| R009_COMBINED | 9.35% | -21.11% | 0.44 | 2.173x |
| TREND10 | 4.67% | -9.29% | 0.50 | 1.487x |
| CRISIS10 | 4.72% | -18.45% | 0.26 | 1.493x |
| PERMANENT10+CRISIS10 | 9.02% | -34.57% | 0.26 | 2.118x |
| STATIC10 daily | 4.69% | -21.04% | 0.22 | 1.490x |
| STATIC15 daily | 6.84% | -30.09% | 0.23 | 1.777x |
| STATIC20 daily | 8.85% | -38.25% | 0.23 | 2.088x |
| STATIC15 monthly | 7.34% | -28.80% | 0.26 | 1.851x |

R009 remains economically coherent on the full primary history: it beats TREND10 and STATIC10 in CAGR and has far smaller drawdown than static 15-20% exposure and the permanent-10-plus-crisis reference.

## 4. Regime split

### PRE_2020 — 2018-2019

- R009_COMBINED CAGR: **-3.10%**;
- TREND10: **+2.00%**;
- CRISIS10: **-4.83%**;
- STATIC10: **-4.49%**.

This is the decisive failed central check. The crisis sleeve improved the result relative to static 10% exposure but materially worsened the trend-only sleeve during ETH's prolonged post-2017 bear market.

### REPLAY_2020

- R009_COMBINED CAGR: **13.37%**;
- TREND10: **5.49%**;
- CRISIS10: **7.75%**;
- STATIC10: **7.60%**;
- R009 Max DD: **-15.09%**.

### POST_2023

- R009_COMBINED CAGR: **9.00%**;
- TREND10: **3.63%**;
- CRISIS10: **5.33%**;
- STATIC10: **3.74%**;
- R009 Max DD: **-11.30%**.

The post-2020 mechanism is strong, but the cross-regime inconsistency prevents full unchanged-rule support.

## 5. Cost stress

At 50 bps on PRIMARY:

- R009_COMBINED CAGR: **8.38%**;
- TREND10: **4.05%**;
- STATIC10: **4.28%**;
- STATIC15 daily: **6.24%**;
- STATIC15 monthly: **7.21%**.

The MIXED result is not caused by ordinary fee sensitivity.

## 6. State diagnostics

PRIMARY:

- trend ON: ~50.76%;
- crisis active: ~94.01%;
- crisis fully deployed: ~72.50%;
- average combined target: ~13.54%.

PRE_2020:

- trend ON: ~30.14%;
- crisis active: ~98.08%;
- crisis fully deployed: ~88.49%;
- average crisis target: ~9.32%;
- average combined target: ~12.33%.

The crisis sleeve is therefore even less like rare dry powder on ETH than on BTC. It behaves as persistent distressed beta during long recovery periods.

Notable crisis episodes include the 2018 drawdown episode, which did not reset to a new ATH until 2021-01-24, and the 2021-2025 episode, which remained active for multiple years. This explains the PRE_2020 weakness versus TREND10 and reinforces the interpretation of R009 as a state-dependent beta handoff rather than proven crisis alpha.

## 7. Frozen gate audit

All hard checks pass. The only applicable central check that fails is:

> PRE_2020 R009_COMBINED CAGR > PRE_2020 TREND10 CAGR — **FAIL**.

All other central checks reported by the frozen engine pass, including PRIMARY and REPLAY_2020 growth comparisons, static benchmark Pareto tests, drawdown comparisons, average target <15%, crisis sleeve positive on PRIMARY, and 50 bps cost stress.

## 8. Interpretation

The ETH test provides **partial cross-asset support** for the economic mechanism but does not establish robust portability.

Correct state:

> **R009 remains the leading BTC candidate in forward testing, while cross-asset portability is uncertain.**

Do not search SOL/XRP or alter SMA120, sleeve weights, thresholds or reset rules to rescue ETH.
