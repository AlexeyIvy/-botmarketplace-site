# R009 Cross-Asset Second-Pass Diagnostics v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** retrospective mechanism diagnostics only; no promotion authority  
**Scope:** BTC + ETH + fixed five-asset breadth panel (BNB/LTC/XRP/ADA/SOL)

## 1. Purpose

Re-read the already observed R009 evidence to identify recurring structural relationships that may guide future hypothesis generation without modifying or rescuing frozen R009 v0.1.

This document is not a new validation test. Any relationship discovered here is retrospective and may not be used as independent evidence for a redesigned strategy.

## 2. Main finding: crisis persistence is associated with weaker risk efficiency

Primary crisis-active fractions are approximately:

- BTC 84.44%
- BNB 88.41%
- ETH 94.01%
- ADA 96.05%
- XRP 97.40%
- SOL 92.83%
- LTC 99.68%

Primary Calmar ratios are approximately:

- BTC 0.95
- BNB 0.82
- SOL 0.80
- ADA 0.53
- ETH 0.44
- XRP 0.30
- LTC 0.19

Across these seven heterogeneous primary samples, the descriptive cross-sectional Pearson correlation between crisis-active fraction and Calmar is about **-0.92**; Spearman rank correlation is about **-0.96**.

This is a very small, non-independent sample with different start dates. It is not a statistical proof. It is nevertheless a strong mechanism clue: the more nearly permanent the crisis sleeve becomes, the worse the observed risk efficiency tends to be.

The same direction appears for fully-deployed fraction and Calmar (Pearson about -0.88).

## 3. Crisis sleeve is not robust standalone alpha

At 10 bps on each asset's primary period, CRISIS10 has lower CAGR than STATIC10 on five of seven observed assets: BTC, BNB, XRP, ADA and SOL. It exceeds STATIC10 on LTC and only marginally on ETH.

This reinforces the earlier R008 conclusion: drawdown-triggered sticky exposure is better interpreted as conditional/distressed beta than as demonstrated crisis alpha or convexity.

The combined R009 architecture does raise CAGR relative to TREND10 across the observed primary samples, but its Calmar exceeds TREND10 on only four of seven assets. Therefore the crisis sleeve frequently purchases extra geometric growth by accepting additional drawdown rather than consistently improving the return/risk frontier.

## 4. Common-mode state concentration

Using the overlapping 2021-01-01 through 2026-09-09 daily history of ETH + BNB/LTC/XRP/ADA/SOL:

- all six crisis sleeves are active simultaneously on about **80.5%** of common days;
- at least four of six are active on about **95.5%** of days;
- at least four of six are fully deployed on about **63.7%** of days;
- the average number of active crisis sleeves is about **5.61 of 6**.

This is important for future portfolio construction. Running the same R009 logic on many crypto assets is unlikely to create a truly independent antifragile sleeve; crisis states are heavily synchronized because the assets share the same broad crypto cycle and many remain below old ATHs for long periods.

## 5. Return-correlation diagnostic

On the same 2021-2026 overlap, the average pairwise Pearson correlation of daily R009 strategy returns across ETH/BNB/LTC/XRP/ADA/SOL is about **0.52**, versus about **0.60** for the underlying raw asset returns.

Trend gating and variable exposure reduce common-factor correlation somewhat, but do not remove it. A multi-coin R009 portfolio would therefore still carry substantial shared crypto beta/common-mode risk.

This is descriptive only; it is not a portfolio-allocation recommendation.

## 6. Important recovery-state clue

A gross contribution diagnostic was calculated for the crisis sleeve using state at day t and next-day asset return.

For five of six non-BTC assets, most cumulative gross crisis-sleeve contribution occurred while the existing SMA120 trend state was already ON:

- BNB ~64%
- LTC ~78%
- ADA >100% because the trend-OFF crisis contribution was negative
- SOL ~69%
- ETH ~81%

XRP is the notable exception, where most contribution occurred while trend was OFF.

This is retrospective and cannot justify a rule change by itself. But it suggests a coherent future hypothesis: **drawdown may be more useful as an arming condition for later recovery exposure than as permission for persistent full exposure while the trend state remains weak.**

## 7. Structural duration problem

Observed crisis episodes can remain open for years:

- LTC longest observed/censored episode ~1,943 days;
- ADA ~1,818 days;
- ETH ~1,348 days;
- XRP ~1,322 days;
- SOL ~1,157 days;
- BNB ~1,114 days.

The reset condition 'strictly new ATH' therefore embeds an unbounded time-under-water state. This is a structural property of the rule, not merely a bad threshold choice.

## 8. What this does and does not imply

These diagnostics support three conclusions:

1. Keep frozen BTC R009 v0.1 forward unchanged; its positive BTC evidence remains valid as evidence for that exact candidate.
2. Do not create a multi-altcoin R009 portfolio merely for diversification; state synchronization is too high to assume orthogonality.
3. A future redesign should attack the **state-duration / recovery-confirmation problem**, not re-optimize the existing drawdown thresholds.

These diagnostics do **not** authorize:

- changing SMA120, crisis levels, weights or reset in R009 v0.1;
- selecting SOL/BNB/ADA as winners;
- claiming the observed correlations are statistically proven;
- backfitting a new reset rule and calling it validated on these already inspected histories.

## 9. Research implication

If a new candidate is opened, the cleanest low-degree-of-freedom hypothesis is to separate:

- **arming:** drawdown breach records that distressed opportunity exists;
- **deployment permission:** an independent recovery/regime confirmation determines whether armed capital is actually exposed;
- **release:** should not require a return to the old ATH by construction.

A candidate using only already-frozen primitives (the existing drawdown ladder and SMA120 state) can be defined with no new numerical parameter. It must be versioned separately from R009 and validated prospectively; old data may only be used for mechanism sanity checks, not promotion.
