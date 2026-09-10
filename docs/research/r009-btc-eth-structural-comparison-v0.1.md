# R009 BTC vs ETH Structural Comparison v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Purpose:** compare frozen R009 v0.1 behavior on BTC and ETH after the precommitted ETH unchanged-rule test.

## 1. Headline

BTC remains materially stronger on risk efficiency. ETH provides partial mechanism support but fails full unchanged-rule support because the crisis sleeve hurts versus TREND10 in the eligible PRE_2020 period.

| Asset | Primary CAGR | Max DD | Calmar | Avg risky target | Formal status |
|---|---:|---:|---:|---:|---|
| BTC | 15.02% | -15.73% | 0.95 | 12.91% | PROMISING_SCREEN / forward active |
| ETH | 9.35% | -21.11% | 0.44 | 13.54% | UNCHANGED_RULE_MIXED |

The primary periods differ because ETHUSDT begins in 2017; this table is structural, not a same-calendar-period horse race.

## 2. Post-2020 behavior

Both assets show positive combined behavior after 2020. ETH REPLAY_2020 CAGR is ~13.37% with ~-15.09% Max DD. BTC REPLAY_2020 CAGR is ~10.02% with ~-9.87% Max DD.

POST_2023 growth is similar (~9% CAGR), but BTC's historical drawdown is materially smaller (~-4.98% versus ETH ~-11.30%).

This suggests some portability of the return mechanism, but weaker portability of the risk-efficiency profile.

## 3. Crisis sleeve persistence

BTC PRIMARY crisis-active fraction: ~84.44%; fully deployed: ~58.26%.

ETH PRIMARY crisis-active fraction: ~94.01%; fully deployed: ~72.50%.

On ETH PRE_2020 the crisis sleeve is active ~98.08% of the time and fully deployed ~88.49% of the time.

Therefore the sticky-until-new-ATH sleeve is not rare dry powder on either asset and is especially persistent on ETH. It should continue to be described as a state-dependent beta handoff, not proven crisis alpha or true convexity.

## 4. Main falsification lesson

The exact R009 rule set survives many ETH checks, but the prolonged 2018-2020 recovery exposes its core weakness: sticky crisis exposure can remain deployed for years and can materially underperform the trend-only sleeve during a long bear/recovery regime.

This weakness must not be repaired by ETH-specific threshold/reset tuning on inspected history.

## 5. Research decision

- Keep BTC R009-E002 forward unchanged.
- Do not open a broad cross-coin rescue sweep.
- Do not retune R009 from ETH evidence.
- R009 remains the leading BTC candidate but is not validated as a universal crypto architecture.
- After first forward technical initialization, the next practical validation gate for R009 is Capital Granularity & Capacity Audit, not another historical parameter search.
- If forward evidence later weakens R009 materially, return to a genuinely orthogonal candidate family rather than rescue R009 historically.
