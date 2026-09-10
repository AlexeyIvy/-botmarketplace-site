# R009-X001 — ETH Unchanged-Rule Structural Falsification Protocol v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Candidate:** R009 — Trend-Gated Crisis Barbell  
**Experiment:** X001 — cross-asset structural falsification  
**Date:** 2026-09-10  
**Status:** frozen before ETH result inspection  
**Parent:** `docs/research/r009-e001-trend-gated-dry-powder-protocol-v0.1.md`  
**Research posture:** falsification-first; no ETH parameter tuning; no broad coin sweep

## 1. Objective

Test whether the exact R009 v0.1 mechanism that screened positively on BTC remains economically coherent on a different major crypto asset without changing any strategy parameter.

Primary question:

> Does the frozen R009 architecture preserve a useful growth/drawdown trade-off on ETHUSDT, or was the BTC result materially BTC-specific?

This is structural cross-asset falsification, not temporal OOS. ETH history is historical and may contain market regimes already known generally.

Maximum positive status:

> **UNCHANGED_RULE_SUPPORT**

X001 cannot be a production, demo, live, OOS, or antifragility PASS.

## 2. Frozen asset and source

- Asset: ETH.
- Venue/data reference: Binance Spot `ETHUSDT`.
- Daily klines: `https://data-api.binance.vision/api/v3/klines`.
- Interval: `1d`.
- Use only fully closed UTC daily bars before a first-run fixed UTC cutoff.
- Positive prices only.
- No interpolation.
- Earliest retained source history is used to initialize ATH and SMA state.
- The first-run cutoff is persisted locally; restart/resume may not move it.

The venue/asset/source is frozen before result inspection. Do not substitute another ETH series after seeing the result.

## 3. Evaluation slices

Because ETHUSDT begins later than the BTC reference series, the primary start is determined prospectively:

- `FULL_AVAILABLE`: all retained fully closed ETHUSDT daily bars.
- `PRIMARY_FULL_YEARS`: from January 1 of the first full calendar year after the first retained ETHUSDT observation.
- `PRE_2020`: PRIMARY through 2019-12-31, only if at least 365 observations exist.
- `REPLAY_2020`: 2020-01-01 onward.
- `POST_2023`: 2023-01-01 onward.

State is always initialized from FULL_AVAILABLE history, so PRIMARY does not artificially restart ATH or SMA state.

## 4. Frozen TREND10

Exactly preserve R009 v0.1:

- SMA lookback = 120 observed daily closes, including day `t`;
- trend ON iff `price_t > SMA120_t`;
- before 120 valid observations trend target = 0%;
- ON target = 10% ETH;
- OFF target = 0%;
- state at `t` applies to return `t+1`;
- no band, slope, confirmation, volatility filter, or alternate lookback.

## 5. Frozen CRISIS10

Exactly preserve R009 v0.1:

- reserve = 10% NAV;
- four equal 2.5 percentage-point tranches;
- triggers at drawdown from running daily closing ATH of -20%, -35%, -50%, -65%;
- first breach activates that tranche;
- active tranches remain active until a strictly new ATH;
- new ATH resets all crisis tranches;
- target range = 0%, 2.5%, 5%, 7.5%, 10%;
- state at `t` applies to return `t+1`.

No symmetric release, hysteresis, cooldown, alternate thresholds, or ETH-specific recovery rule.

## 6. Frozen combined architecture

`COMBINED = TREND10 + CRISIS10`

Allowed desired ETH weights:

`{0, 2.5, 5, 7.5, 10, 12.5, 15, 17.5, 20}%`

No interaction override.

Reference architecture `PERMANENT10_PLUS_CRISIS10_REF` uses 10% permanent ETH plus the same frozen crisis sleeve. It is a diagnostic reference only.

## 7. Accounting and costs

Preserve the R009 E001 self-financing daily-target accounting:

1. prior target participates in the next daily ETH return;
2. weight drifts with the realized return;
3. rebalance at the daily close to the newly observed target;
4. charge fee on actual traded notional;
5. new target is held for the next daily interval.

Fee grid:

- 5 bps;
- 10 bps baseline;
- 25 bps;
- 50 bps stress.

Cash return = 0%. No leverage, funding, staking, lending, or collateral yield.

## 8. Mandatory comparators

Dynamic:
- `TREND10_DAILY`
- `CRISIS10_DAILY`
- `R009_COMBINED_DAILY`
- `PERMANENT10_PLUS_CRISIS10_REF`

Static daily:
- `STATIC10_DAILY`
- `STATIC15_DAILY`
- `STATIC20_DAILY`

Static monthly:
- `STATIC10_MONTHLY`
- `STATIC15_MONTHLY`
- `STATIC20_MONTHLY`

Context:
- `CASH`
- `ETH100`

No other weight or implementation variant.

## 9. Required diagnostics

For strategy / fee / slice report at minimum:

- CAGR;
- ending multiple;
- annualized volatility;
- Max Drawdown;
- Calmar;
- worst calendar year/quarter/month;
- worst rolling 365d return;
- longest drawdown duration;
- average and maximum held risky-asset weight;
- turnover;
- fee drag;
- 1% and 5% VaR/CVaR.

Also report:

- trend ON fraction;
- crisis-active and fully-deployed fractions;
- average trend/crisis/combined targets;
- combined-target occupancy;
- SMA ON/OFF transition count;
- crisis episode/reset counts;
- joint trend/crisis state occupancy;
- first-breach fixed-horizon diagnostics at 7/30/90/180/365 days.

## 10. Frozen structural decision gate

At the 10 bps baseline, define eligible `PRE_2020` only if it contains at least 365 daily observations.

Central checks:

1. COMBINED CAGR > STATIC10_DAILY on PRIMARY.
2. COMBINED CAGR > TREND10_DAILY on PRIMARY.
3. COMBINED CAGR > STATIC10_DAILY on REPLAY_2020.
4. COMBINED CAGR > TREND10_DAILY on REPLAY_2020.
5. If PRE_2020 is eligible, COMBINED CAGR > STATIC10_DAILY on PRE_2020.
6. If PRE_2020 is eligible, COMBINED CAGR > TREND10_DAILY on PRE_2020.
7. COMBINED is not Pareto-dominated by STATIC15_DAILY on PRIMARY.
8. COMBINED is not Pareto-dominated by STATIC15_MONTHLY on PRIMARY.
9. COMBINED Max DD is smaller in magnitude than STATIC20_DAILY on PRIMARY.
10. COMBINED Max DD is smaller in magnitude than STATIC20_MONTHLY on PRIMARY.
11. COMBINED Max DD is smaller in magnitude than PERMANENT10_PLUS_CRISIS10_REF on PRIMARY.
12. PRIMARY average combined desired target <15%.
13. CRISIS10 ending multiple >1 on PRIMARY.
14. At 50 bps, COMBINED CAGR > STATIC10_DAILY on PRIMARY.
15. At 50 bps, COMBINED CAGR > TREND10_DAILY on PRIMARY.
16. At 50 bps, COMBINED is not Pareto-dominated by STATIC15_DAILY on PRIMARY.

Decision:

- `UNCHANGED_RULE_SUPPORT` only if every applicable central check passes.
- `UNCHANGED_RULE_FAIL` if a hard contradiction occurs: PRIMARY COMBINED CAGR <=0; PRIMARY COMBINED CAGR <= STATIC10; PRIMARY COMBINED CAGR <= TREND10; CRISIS10 ending multiple <=1; PRIMARY average combined target >=15%; PRIMARY COMBINED Max DD is as bad as or worse than STATIC20_DAILY; or 50 bps PRIMARY COMBINED CAGR <=0.
- otherwise `UNCHANGED_RULE_MIXED`.

A FAIL/MIXED result may not be rescued by ETH-specific parameter changes.

## 11. Interpretation discipline

A positive ETH result strengthens the case that R009 represents a broader state-dependent beta-allocation architecture rather than a BTC-only historical coincidence.

A negative/mixed result weakens portability but does not reset or invalidate the already-frozen BTC forward record.

Do not search SOL/XRP/other coins to find a replacement positive result.

## 12. Anti-overfitting freeze

After X001 output is inspected, do not change within X001:

- ETHUSDT;
- source;
- SMA120;
- 10% trend sleeve;
- 10% crisis reserve;
- 2.5% tranche size;
- -20/-35/-50/-65 triggers;
- sticky-to-new-ATH reset;
- additive combination;
- fee grid;
- cash yield;
- benchmark weights/frequencies;
- slice rules;
- decision gate.

Any material change is a new candidate/version and cannot overwrite X001.
