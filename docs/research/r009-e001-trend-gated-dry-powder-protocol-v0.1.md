# R009-E001 — Trend-Gated Dry-Powder Barbell Protocol v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Candidate:** R009 — Antifragile Trend-Gated Dry-Powder Barbell  
**Experiment:** E001  
**Date:** 2026-09-09  
**Status:** pre-result frozen mechanism-screen specification  
**Parents:** R002 frozen BTC SMA120; R008 v0.1 crisis reserve; R008-E004 accounting audit  
**Research posture:** antifragility-first, falsification-first, no parameter rescue

## 1. Objective

R008 showed that a crisis-only drawdown ladder mainly reallocates BTC beta and does not demonstrate robust exposure-controlled crisis alpha against simple STATIC15/20 benchmarks.

R009 asks a different economic question:

> Does separating ordinary directional risk from crisis-opportunity risk produce a better cash-heavy portfolio architecture than either mechanism alone or simple static BTC/cash allocation?

The architecture deliberately assigns different jobs to two sleeves:

- **TREND10** controls ordinary directional BTC exposure using the already-frozen SMA120 rule;
- **CRISIS10** uses a separate 10% dry-powder reserve, deployed only after pre-specified drawdowns and held through recovery until a new ATH;
- **R009_COMBINED** is the sum of those sleeves.

This is not a rescue of R008 by adding an indicator to the same strategy. It is a new portfolio decomposition using two previously frozen mechanisms.

## 2. Evidence-status limitation

Bitcoin history through 2026 has already been inspected during R002 and R008 research.

Therefore E001 is an **in-sample mechanism screen**.

Maximum positive status:

> **PROMISING_SCREEN / ADVANCE TO FORWARD OR NEW-INDEPENDENT VALIDATION**

E001 cannot assign HISTORICAL PASS.

## 3. Data source

Use the same independent Blockchain.com daily Bitcoin USD reference-price series:

`https://api.blockchain.info/charts/market-price?timespan=all&format=json&sampled=false`

Requirements:

- UTC daily observations;
- positive prices only;
- no interpolation;
- state initialized from earliest valid positive observation;
- repeat E004 data audit and record raw/clean SHA256;
- stop as DATA_REDESIGN if primary daily continuity gate fails.

Evaluation slices:

- PRIMARY_LONG: 2013-01-01 onward;
- PRE_2020: 2013-01-01 through 2019-12-31;
- REPLAY_2020: 2020-01-01 onward;
- POST_2023: 2023-01-01 onward;
- FULL_AVAILABLE for transparency only.

## 4. Frozen TREND10 sleeve

Reuse the frozen BTC SMA120 rule exactly.

For daily observation t:

- compute simple moving average over the latest 120 observed daily prices including t;
- trend signal is ON if `price_t > SMA120_t`;
- signal determined after observation t applies to return t+1;
- no same-observation execution;
- before 120 valid observations, trend target is 0%;
- trend sleeve target = 10% BTC when ON, 0% when OFF.

No alternative lookback, band, slope, confirmation, or volatility filter is permitted.

## 5. Frozen CRISIS10 sleeve

Reuse the R008 v0.1 crisis reserve logic but **without** its permanent 10% BTC base.

- reserve size: 10% of NAV;
- four equal tranches: 2.5 percentage points each;
- drawdown thresholds from running daily reference-price ATH: -20%, -35%, -50%, -65%;
- first breach of a level deploys its tranche;
- once deployed, a tranche remains active until the next new ATH;
- at a new ATH all crisis tranches reset to cash;
- crisis sleeve target range: 0%, 2.5%, 5%, 7.5%, 10%;
- state at t applies to return t+1.

No symmetric release, hysteresis, cooldown, optimized recovery threshold, or alternative trigger is allowed.

## 6. R009_COMBINED target

`combined_target_t = trend_target_t + crisis_target_t`

Total desired BTC target therefore belongs to:

`{0, 2.5, 5, 7.5, 10, 12.5, 15, 17.5, 20}%`

Interpretation:

- normal bull regime: trend sleeve may hold 10%, crisis sleeve 0%;
- weakening market: trend sleeve can turn OFF while crisis sleeve begins deploying only after drawdown thresholds;
- deep bear: trend sleeve can remain OFF while crisis sleeve reaches up to 10%;
- confirmed recovery: trend sleeve can turn ON while crisis tranches remain active, allowing up to 20% recovery exposure;
- new ATH: crisis sleeve resets while trend sleeve remains independently governed by SMA120.

No interaction override is allowed. The sleeves are simply additive.

## 7. Canonical accounting

Use E004 **SELF_FINANCING_DAILY_TARGET** accounting for TREND10, CRISIS10, R008_V01 reference, R009_COMBINED and daily static benchmarks.

At each daily close:

1. existing BTC weight drifts with realized BTC return;
2. compute pre-trade BTC portfolio weight;
3. rebalance to today's desired target;
4. charge fee on actual traded notional;
5. resulting target is the starting allocation for the next daily return.

This maintains the stated risk budget and gives all partial-weight targets identical treatment.

Fee grid:

- 5 bps;
- 10 bps baseline;
- 25 bps;
- 50 bps.

Cash return: 0%.

No funding or leverage.

## 8. Mandatory comparators and ablations

E001 must calculate exactly these strategy/accounting variants.

### Dynamic components

- **TREND10_DAILY** — frozen SMA120 sleeve only;
- **CRISIS10_DAILY** — frozen sticky crisis reserve only;
- **R009_COMBINED_DAILY** — TREND10 + CRISIS10;
- **R008_V01_DAILY** — 10% permanent BTC + frozen sticky crisis reserve, reference only.

### Static daily benchmarks

- STATIC10_DAILY;
- STATIC15_DAILY;
- STATIC20_DAILY.

### Practical static monthly benchmarks

- STATIC10_MONTHLY;
- STATIC15_MONTHLY;
- STATIC20_MONTHLY.

### Context

- CASH;
- BTC100.

No other sleeve weight, SMA length, trigger set, or implementation variant is permitted in E001.

## 9. Required metrics

For every strategy, fee and evaluation slice:

- CAGR;
- ending multiple;
- annualized volatility;
- Max Drawdown;
- Calmar;
- worst calendar year;
- worst quarter;
- worst month;
- worst rolling 12 months;
- longest drawdown duration;
- average realized BTC weight;
- maximum realized BTC weight;
- turnover;
- fee drag;
- daily 1% and 5% VaR;
- daily 1% and 5% CVaR.

Report baseline calendar-year returns.

## 10. State and architecture diagnostics

Report:

- trend ON fraction by slice;
- crisis-active fraction by slice;
- crisis fully deployed fraction;
- average trend target;
- average crisis target;
- average combined target;
- fraction of days at each combined desired target;
- number of SMA ON/OFF transitions;
- number of crisis tranche deployments/resets;
- number of days in joint states:
  - trend ON / crisis inactive;
  - trend OFF / crisis inactive;
  - trend ON / crisis active;
  - trend OFF / crisis active.

These diagnostics are required to determine whether the portfolio remains genuinely cash-heavy.

## 11. Ablation interpretation

R009 is useful only if the combination adds economic value beyond the frozen components.

Required comparisons:

### Combined vs TREND10

Ask whether the crisis reserve increases geometric growth without destroying the trend sleeve's drawdown advantage.

### Combined vs CRISIS10

Ask whether the trend sleeve supplies useful ordinary-risk participation and reduces the long trapped-beta weakness of crisis-only exposure.

### Combined vs R008 v0.1

Ask whether replacing the permanent 10% base with a trend-gated 0/10% sleeve improves the growth/drawdown frontier.

### Combined vs STATIC15/20

Ask whether the architecture earns a better dynamic risk/growth tradeoff rather than merely recreating a similar average BTC beta through more complex rules.

## 12. Fixed-horizon shock diagnostics

Reuse E004 trigger levels and horizons for descriptive continuity.

For first breach of each -20/-35/-50/-65 level within each ATH-defined crisis episode, calculate next-interval portfolio returns over:

- 7 days;
- 30 days;
- 90 days;
- 180 days;
- 365 days.

For R009_COMBINED report benefit versus:

- TREND10_DAILY;
- STATIC15_DAILY;
- STATIC20_DAILY;
- STATIC15_MONTHLY.

Also report the same horizons for CRISIS10_DAILY to isolate the reserve component.

These observations are descriptive and overlapping; no significance claim is allowed.

## 13. Decision gate

### PROMISING_SCREEN / ADVANCE

Assign only if all central requirements broadly hold:

1. R009_COMBINED CAGR > STATIC10_DAILY on PRIMARY_LONG, PRE_2020 and REPLAY_2020.
2. R009_COMBINED CAGR > TREND10 on PRIMARY_LONG and at least one of PRE_2020 / REPLAY_2020, without material deterioration in the other.
3. R009_COMBINED is not Pareto-dominated by STATIC15_DAILY on PRIMARY_LONG or PRE_2020.
4. R009_COMBINED is not Pareto-dominated by STATIC15_MONTHLY on PRIMARY_LONG.
5. R009_COMBINED Max DD is materially smaller in magnitude than STATIC20_DAILY and STATIC20_MONTHLY on PRIMARY_LONG.
6. R009_COMBINED Max DD is smaller in magnitude than R008_V01_DAILY on PRIMARY_LONG.
7. PRIMARY_LONG average desired BTC target is <15%.
8. CRISIS10 has ending multiple >1 on PRIMARY_LONG and adding it to TREND10 improves combined geometric growth rather than only increasing drawdown.
9. At 50 bps the broad conclusions above do not reverse.
10. PRE_2020 and REPLAY_2020 are directionally compatible rather than one carrying the entire result.

### REDESIGN / CLOSE

Do not advance if any central failure dominates:

- STATIC15 daily/monthly clearly dominates the combined architecture;
- combined advantage is mainly explained by higher average BTC exposure;
- CRISIS10 adds little or negative geometric value to TREND10;
- combined Max DD approaches STATIC20 without compensating growth/Calmar improvement;
- costs materially erode the combination;
- pre-2020 and post-2020 evidence conflict materially.

Because E001 is in-sample, a positive screen does not authorize production or historical PASS.

## 14. Anti-overfitting freeze

Before any E001 result is inspected, freeze:

- SMA lookback = 120;
- trend sleeve weight = 10%;
- crisis reserve = 10%;
- crisis tranche size = 2.5% x4;
- drawdown levels = -20/-35/-50/-65%;
- sticky-to-new-ATH crisis reset;
- additive sleeve rule;
- self-financing daily-target accounting;
- static monthly comparator frequency;
- fee grid;
- cash return = 0%;
- data source;
- evaluation slices;
- decision rules.

Any changed sleeve weight, SMA length, threshold, reset rule, interaction rule, or accounting policy creates a new version and is prohibited as E001 rescue.

## 15. After E001

### If PROMISING_SCREEN

- freeze R009 v0.1 exactly;
- start forward paper tracking on executable BTC data;
- do not run a nearby historical parameter grid;
- model the safe sleeve explicitly before implementation promotion;
- only later consider a separately pre-specified cross-asset structural falsification test.

### If REDESIGN / CLOSE

Close the trend+drawdown family on this history and move to a genuinely different source of antifragility, prioritizing:

- carry-funded dry powder;
- basis/funding carry financing bounded long convexity;
- true option convexity using higher-quality historical option-chain data.