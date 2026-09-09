# R008-E004 — Accounting & Event-Diagnostic Audit Results v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Candidate:** R008 — Antifragile Crisis-Opportunity Barbell  
**Experiment:** E004  
**Date:** 2026-09-09  
**Status:** formal methodology-audit result  
**Decision:** **ACCOUNTING_CONCLUSION_STABLE**  
**Protocol:** `docs/research/r008-e004-accounting-diagnostic-audit-protocol-v0.1.md`

## 1. Executive decision

E004 confirms that the main negative conclusion from E002/E003 is not an artifact of the old target-weight accounting.

Formal E004 interpretation:

> **ACCOUNTING_CONCLUSION_STABLE**

The self-financing audit charges natural-weight maintenance turnover to static portfolios and still finds no compelling economic advantage for the R008 crisis-only ladder over simple static BTC/cash allocations at comparable risk budgets.

The fixed-horizon diagnostics also weaken the earlier interpretation of the ATH-conditioned crisis-event Benefit10. Deep-drawdown deployment can improve short/medium-horizon recovery capture versus STATIC10 and sometimes STATIC15, but the advantage is small, inconsistent across horizons, and does not remain coherent against STATIC20. At longer horizons the ladder often falls behind STATIC15/20.

Action under the frozen E004 protocol:

- close R008 crisis-only ladder development on this already-inspected history;
- do not add hysteresis, cooldown, nearby recovery levels, alternative drawdown thresholds, or tranche-size tuning;
- proceed to the economically distinct R009 trend-gated dry-powder hypothesis.

R008 v0.1 and v0.2 remain useful research records, not production candidates.

## 2. Data integrity

Data gate: **PASS**.

- source: Blockchain.com daily Bitcoin market-price reference series;
- raw observations: 6,459;
- clean positive observations: 5,867;
- clean period: 2010-08-18 -> 2026-09-09;
- duplicate raw dates before deduplication: 0;
- PRIMARY_LONG observations: 5,000;
- PRIMARY_LONG missing calendar days: 0;
- maximum primary gap: 1 day;
- raw SHA256: `c84bd2a2b68ac13f03af09ab2d089017b15215bdbe1b5e9ca7d8b5bbbe4a422a`;
- clean SHA256: `b4c819d4f1e1f27b2f84ead0c4949f0cf44cda77f384186784350a5ed283cb3b`.

The E004 input is therefore directly comparable with E002/E003.

## 3. Self-financing daily-target accounting

At baseline 10 bps, realistic daily maintenance changes absolute results modestly but not the economic ordering.

### PRIMARY_LONG

| Strategy | CAGR | Max DD | Calmar | Avg BTC | Turnover |
|---|---:|---:|---:|---:|---:|
| R008 v0.1 | 14.70% | -23.11% | 0.64 | 17.08% | 18.689 |
| R008 v0.2 | 12.52% | -20.17% | 0.62 | 15.14% | 23.787 |
| STATIC10 | 9.24% | -13.63% | 0.68 | 10.00% | 11.245 |
| STATIC15 | 13.94% | -19.95% | 0.70 | 15.00% | 15.926 |
| STATIC20 | 18.68% | -25.93% | 0.72 | 20.00% | 19.981 |

R008 v0.2 remains Pareto-dominated by STATIC15 on PRIMARY_LONG: lower CAGR, slightly worse Max DD, and lower Calmar.

R008 v0.1 has somewhat higher CAGR than STATIC15 but requires materially more average BTC exposure and has worse Max DD and Calmar. This is not a clean dynamic-allocation advantage.

### PRE_2020_NEW

| Strategy | CAGR | Max DD | Calmar | Avg BTC | Turnover |
|---|---:|---:|---:|---:|---:|
| R008 v0.1 | 19.50% | -23.11% | 0.84 | 18.35% | 11.226 |
| R008 v0.2 | 17.34% | -20.17% | 0.86 | 16.18% | 13.699 |
| STATIC10 | 13.13% | -13.63% | 0.96 | 10.00% | 6.591 |
| STATIC15 | 20.00% | -19.95% | 1.00 | 15.00% | 9.334 |
| STATIC20 | 27.04% | -25.93% | 1.04 | 20.00% | 11.709 |

STATIC15 still dominates both the intended midpoint-risk interpretation of v0.2 and the pre-2020 v0.1 result on the principal growth/drawdown/Calmar comparison.

Therefore the old conclusion was not created by free static maintenance.

## 4. Practical monthly static benchmarks

Month-end rebalancing changes the static portfolios meaningfully because BTC weight is allowed to drift within each month.

PRIMARY_LONG at 10 bps:

- STATIC10 monthly: CAGR 11.32%, Max DD -15.50%, Calmar 0.73, avg BTC 10.32%;
- STATIC15 monthly: CAGR 16.74%, Max DD -22.30%, Calmar 0.75, avg BTC 15.44%;
- STATIC20 monthly: CAGR 22.04%, Max DD -28.56%, Calmar 0.77, avg BTC 20.52%.

PRE_2020_NEW:

- STATIC15 monthly: CAGR 25.54%, Max DD -22.30%, Calmar 1.15;
- STATIC20 monthly: CAGR 33.80%, Max DD -28.56%, Calmar 1.18.

These are not identical risk budgets to daily fixed targets because realized weights drift upward in strong BTC advances. They should not be used as a mechanical Pareto test against exact-target R008. However, they are useful operational hurdles: a very simple low-frequency allocation remains economically strong.

## 5. Transition-only R008 interpretation

Transition-only accounting reduces trading but allows realized BTC weight to drift materially away from the nominal target between state changes.

Examples:

- R008 v0.1 PRIMARY_LONG average realized BTC weight: 19.86%;
- R008 v0.1 PRE_2020_NEW average realized BTC weight: 21.62%, exceeding the nominal 20% target ceiling on average;
- R008 v0.2 PRIMARY_LONG average realized BTC weight: 15.44%.

Therefore the higher transition-only CAGR is not evidence that execution realism rescues R008. It partly reflects a different and sometimes larger realized beta budget. Transition-only is retained as an implementation diagnostic, not promoted as the canonical R008 strategy.

## 6. Fixed-horizon shock evidence

E004 replaced the next-ATH endpoint with pre-specified 7/30/90/180/365-day horizons after the first breach of -20/-35/-50/-65 within each crisis episode.

There are 43 threshold-breach rows across 19 crisis episodes. At a given trigger level, sample counts are small: 19 at -20%, 10 at -35%, 9 at -50%, and only 5 at -65%. The observations across levels are nested inside the same crises, so the diagnostics are descriptive rather than statistically independent.

### Versus STATIC10 daily

There is a real recovery-capture effect at several short/medium horizons:

- at -50%, v0.1 mean Benefit10 is about +0.99% at 7d, +2.01% at 30d, +2.39% at 90d and +4.46% at 180d;
- at -65%, v0.1 mean Benefit10 is about +2.22% at 7d, +2.02% at 30d and +4.67% at 365d;
- v0.2 shows similar but generally weaker long-horizon behavior.

This supports the narrow statement that increasing BTC exposure after severe drawdowns can improve recovery capture relative to remaining at only 10% BTC.

### Versus STATIC15 daily

The evidence is much weaker once the comparison has a closer beta budget.

Examples for v0.1:

- -20% / 365d: mean Benefit15 about -7.98%;
- -35% / 365d: about -10.49%;
- -50% / 365d: about -10.83%;
- -65% / 365d: only about +0.82%, count 5.

At -50%, v0.1 is modestly positive versus STATIC15 at 7d and 30d, but the mean advantage becomes negative by 90/180/365d.

For v0.2, the same qualitative pattern holds and the -65% / 365d mean Benefit15 is only about +0.25% with a negative median.

### Versus STATIC20 daily

There is no coherent advantage.

- v0.1 at -65% is essentially identical to STATIC20 at 7/30/90/180d because both hold 20% while the sticky crisis sleeve remains fully deployed;
- at -65% / 365d v0.1 mean Benefit20 is about -3.32%;
- v0.2 -65% / 365d mean Benefit20 is about -3.89%;
- most -20/-35/-50 comparisons are also negative in mean against STATIC20.

### Versus STATIC15 monthly

The practical monthly comparator is tougher still at long horizons. For example, at -65% / 365d the mean benefit is negative for both R008 versions.

Thus the original 18/18 positive next-ATH Benefit10 should not be interpreted as independent crisis-timing alpha. It mainly established that higher BTC exposure participates more strongly in eventual recoveries.

## 7. Technical-financial interpretation

The evidence now supports four narrower statements.

1. **The drawdown ladder is a beta-allocation rule, not demonstrated convex alpha.** It changes how much BTC is owned conditional on stress.
2. **The apparent crisis advantage is strongest versus an intentionally low 10% benchmark.** It weakens materially versus STATIC15 and disappears against STATIC20 on many horizons.
3. **v0.1 and v0.2 fail for different reasons.** v0.1 keeps crisis beta too long; v0.2 releases it faster but sacrifices recovery participation. The history does not justify selecting an intermediate release rule without result chasing.
4. **Simple rebalancing policy matters.** Monthly static allocations can be strong because natural weight drift participates in trends. Any future partial-risk strategy must specify self-financing maintenance explicitly.

## 8. Formal E004 gate

Against the frozen protocol:

- realistic accounting materially removes prior STATIC15 domination: **NO**;
- fixed-horizon deep-shock benefit remains coherent against STATIC15/20 rather than only STATIC10: **NO**;
- accounting and event diagnostics point in contradictory directions: **NO**.

Therefore:

> **ACCOUNTING_CONCLUSION_STABLE**

## 9. Closure rule for R008 crisis-only ladder

Do not run further historical rescue searches on this branch:

- no new drawdown levels;
- no different tranche sizes;
- no optimized recovery threshold;
- no hysteresis/cooldown grid;
- no event-specific exits;
- no technical filter added merely to improve R008.

R008 v0.1/v0.2 may be retained as frozen comparators and conceptual building blocks in a genuinely different architecture, but the crisis-only ladder is closed as a standalone candidate on this history.

## 10. Next branch

Proceed to **R009 — Antifragile Trend-Gated Dry-Powder Barbell** as a new economic hypothesis.

The design must use ablations and reuse the already-frozen BTC SMA120 without retuning it. The purpose is not to rescue R008; it is to separate two economic jobs:

- slow trend controls ordinary directional beta and survival;
- a small pre-committed crisis reserve controls temporary distressed-risk deployment.

Because all BTC history through 2026 has already been inspected, the first R009 backtest is only a mechanism screen and cannot receive independent historical PASS.