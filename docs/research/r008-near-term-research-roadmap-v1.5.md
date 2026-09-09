# R008 / R009 Near-Term Research Roadmap v1.5

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-09  
**Status:** E004 complete; R008 crisis-only ladder closed; R009 next  
**Research posture:** antifragility-first, falsification-first, no hidden tuning

## 1. Current decisions

- R008 v0.1: REDESIGN under E002.
- R008 v0.2 symmetric recovery: REDESIGN / DO NOT ADVANCE under E003.
- R008-E004: **ACCOUNTING_CONCLUSION_STABLE**.
- R008 crisis-only ladder development is now closed on this already-inspected BTC history.
- BTC SMA120 frozen forward record continues independently and is not reset.
- R002 broad-universe rescue remains closed.
- R001 tested options implementations remain paused/redesign.

Canonical E004 result:

`docs/research/r008-e004-results-v0.1.md`

## 2. What E004 added

E004 showed that the main R008 conclusion survives a stricter financial-accounting audit.

Self-financing daily target accounting charges real natural-weight maintenance turnover to static portfolios. STATIC15 still remains economically stronger than R008 v0.2 on the main long-history slices, and v0.1's extra CAGR is accompanied by higher beta, deeper drawdown and weaker Calmar.

Fixed-horizon diagnostics also show that the earlier next-ATH Benefit10 overstates the strength of the crisis-timing interpretation:

- recovery capture is positive versus STATIC10 in many deep-shock windows;
- the edge weakens materially versus STATIC15;
- it is not coherent versus STATIC20;
- at long horizons many comparisons turn negative.

Therefore the drawdown ladder is best interpreted as a conditional beta-allocation rule, not demonstrated crisis alpha or true convexity.

## 3. R008 closure

No more historical rescue work on R008 crisis-only rules:

- no threshold grid;
- no tranche-size grid;
- no new exit/recovery levels;
- no hysteresis/cooldown search;
- no RSI/MACD/ADX/volatility rescue filter;
- no event-specific exits.

R008 v0.1 may still be used as a frozen **component** in a genuinely different architecture if its role is changed and that architecture is specified before testing.

## 4. Immediate next branch — R009

Open **R009 — Antifragile Trend-Gated Dry-Powder Barbell**.

Economic decomposition:

1. slow trend handles ordinary directional BTC risk / survival;
2. crisis reserve handles pre-committed distressed deployment;
3. the combined portfolio is tested against each component separately and against simple static BTC/cash allocations.

The frozen BTC SMA120 lookback must be reused exactly and never retuned.

## 5. R009 design principles

The first R009 experiment must be deliberately low-dimensional.

### Trend sleeve

Use the already-frozen BTC SMA120 rule:

- after a fully observed day t, calculate SMA120 including t;
- trend ON if `close_t > SMA120_t`;
- state applies to t+1;
- no same-close execution;
- no alternative moving-average length.

The trend sleeve target is 10% BTC when ON and 0% when OFF.

### Crisis sleeve

Reuse the frozen R008 v0.1 crisis **reserve only**, without its permanent 10% BTC base:

- reserve size 10%;
- 2.5pp tranches at -20/-35/-50/-65% drawdown from running ATH;
- triggered tranches remain deployed until a new ATH;
- crisis sleeve target ranges 0-10%.

Why v0.1 component rather than v0.2: E003 showed symmetric release materially weakens recovery capture. The v0.1 standalone failure was mainly that a permanent 10% base plus sticky reserve kept total risk too high for too long. In R009 the ordinary base is instead trend-gated, so the same frozen crisis sleeve plays a different portfolio role without changing its own historical parameters.

### Combined target

`R009 target = Trend10 target + Crisis10 target`

Total BTC target therefore ranges from 0% to 20%.

During a deep bear market the trend sleeve can be OFF while the crisis reserve deploys gradually. During a confirmed recovery the trend sleeve can turn back ON while crisis tranches remain active, increasing recovery participation. At a new ATH the crisis sleeve resets while the trend sleeve remains independently governed by SMA120.

## 6. Accounting standard for R009

Use the E004 self-financing daily-target model as the canonical accounting model:

- natural BTC weight drift occurs first;
- rebalance to the day's desired target;
- charge transaction cost on actual traded notional;
- desired target applies to the next daily return.

Reason: this preserves the explicit 0-20% risk budget and treats all partial-weight strategies consistently.

Also report deterministic calendar-month-end STATIC10/15/20 benchmarks as practical low-frequency hurdles, but do not create multiple R009 implementation variants in the first screen.

Fee grid remains 5/10/25/50 bps; baseline 10 bps. Cash return remains 0% in the first mechanism screen.

## 7. Mandatory ablations

R009-E001 must report:

- CASH;
- BTC100 contextual;
- STATIC10 daily and monthly;
- STATIC15 daily and monthly;
- STATIC20 daily and monthly;
- TREND10 — frozen SMA120 sleeve only;
- CRISIS10 — frozen sticky drawdown reserve only, with no permanent BTC base;
- R008_V01 — frozen historical 10% permanent base + sticky crisis reserve, reference only;
- **R009_COMBINED** — TREND10 + CRISIS10.

No additional strategy variant is allowed in E001.

## 8. Evidence status

All Bitcoin history through 2026 has already been inspected while developing R002/R008.

Therefore R009-E001 is an **in-sample economic mechanism screen**, not independent validation.

Maximum positive result:

> **PROMISING_SCREEN / ADVANCE TO FORWARD OR NEW-INDEPENDENT VALIDATION**

No historical PASS can be assigned from this dataset.

## 9. Required diagnostics

For PRIMARY_LONG 2013+, PRE_2020, REPLAY_2020 and POST_2023 report:

- CAGR, ending multiple, annualized vol, Max DD, Calmar;
- worst year/quarter/month/rolling12m;
- longest DD;
- average and max realized BTC weight;
- turnover and fee drag;
- 1%/5% VaR/CVaR;
- trend ON fraction;
- crisis-active fraction;
- joint state occupancy;
- time at combined targets 0/2.5/.../20%;
- calendar-year returns.

Ablation diagnostics must show whether the combined architecture improves the risk/growth frontier rather than merely increasing average beta.

Fixed-horizon crisis diagnostics should compare R009_COMBINED with TREND10, STATIC15 daily and STATIC20 daily over the same 7/30/90/180/365-day horizons used in E004.

## 10. R009-E001 decision gate

### PROMISING_SCREEN / ADVANCE

Require all of the following broadly:

1. R009_COMBINED CAGR > STATIC10 daily on PRIMARY_LONG, PRE_2020 and REPLAY_2020.
2. R009_COMBINED CAGR > TREND10 on PRIMARY_LONG and in at least one of PRE_2020 / REPLAY_2020, while not being materially worse in the other.
3. R009_COMBINED is not Pareto-dominated by STATIC15 daily on PRIMARY_LONG or PRE_2020.
4. R009_COMBINED is not Pareto-dominated by STATIC15 monthly on PRIMARY_LONG.
5. R009_COMBINED Max DD is materially smaller in magnitude than STATIC20 daily and STATIC20 monthly on PRIMARY_LONG.
6. R009_COMBINED Max DD is smaller than frozen R008_V01 on PRIMARY_LONG.
7. Average BTC target on PRIMARY_LONG is below 15%, preserving a genuinely cash-heavy profile rather than recreating STATIC15/20 by another route.
8. CRISIS10 ending multiple is >1 on PRIMARY_LONG and its addition to TREND10 improves combined geometric growth rather than only drawdown depth.
9. At 50 bps the main conclusions above do not reverse.
10. PRE_2020 and REPLAY_2020 do not point in opposite economic directions.

### REDESIGN / CLOSE

Do not advance if:

- STATIC15 daily/monthly still clearly dominates;
- combined performance is explained mainly by higher average BTC exposure;
- crisis sleeve adds little or negative geometric value to TREND10;
- Max DD approaches STATIC20 without compensating improvement;
- costs materially erode the combination;
- one historical regime carries the entire result.

No SMA length, drawdown threshold, tranche size, sleeve weight or reset-rule tuning is allowed after E001.

## 11. If R009 screen is promising

Do not run another nearby historical parameter search.

Next steps:

1. freeze exact R009 v0.1;
2. begin forward paper tracking on executable BTC data;
3. optionally pre-specify a cross-asset structural falsification test, clearly labelled non-temporal-OOS;
4. model the safe sleeve explicitly: fiat/T-bills/custody, cash yield, stablecoin/depeg risk, transfer availability, venue concentration;
5. test execution realism and slippage.

## 12. If R009 screen fails

Close this family rather than adding more indicators.

Move to a genuinely different antifragility source:

- carry-funded dry powder;
- true option convexity with better chain data;
- basis/funding carry financing a bounded long-convexity sleeve.

BTC SMA120 frozen forward tracking continues regardless.