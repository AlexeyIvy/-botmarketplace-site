# R002 Finalist Robustness + Ensemble Results v1.0

**Dataset:** Binance USD-M historical subset, cleaned point-in-time daily OHLCV  
**Finalists:** SMA120 and Donchian 100/50  
**Common warmup:** 200 days  
**Base execution assumption:** 10 bps per absolute weight change  
**Base delisting penalty:** 25% of a disappearing long sleeve  
**Signal timing:** signal formed on day t, applied to day t+1 return  

## 1. Why this audit exists

The candidate tournament produced two viable trend-following finalists. Before freezing a combined model, this audit asks three questions:

1. Do both finalists remain robust under the same harsher diagnostics?
2. Are they sufficiently different to provide diversification?
3. Does a simple combination improve the overall profile without adding unjustified complexity?

No new indicator or parameter search is introduced here.

## 2. Base results

| Variant | CAGR | Max DD | Vol | Calmar | Worst year | Worst rolling 12m | Turnover | Avg exposure |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SMA120 | 46.86% | -54.53% | 48.95% | 0.86 | -28.55% | -42.33% | 86.94 | 46.47% |
| Donchian 100/50 | 46.77% | -39.78% | 43.96% | 1.18 | -16.04% | -30.36% | 14.73 | 40.21% |
| 50/50 blend | 47.39% | -46.88% | 45.69% | 1.01 | -22.40% | -36.17% | 50.79 | 43.34% |
| AND | 39.24% | -44.28% | 40.57% | 0.89 | -16.01% | -31.23% | 39.84 | 33.87% |
| OR | 54.45% | -50.72% | 52.23% | 1.07 | -28.64% | -43.95% | 61.83 | 52.81% |

### Interpretation

- Donchian 100/50 materially dominates SMA120 on drawdown, turnover and Calmar while preserving almost the same full-period CAGR.
- The 50/50 blend is a compromise, but does not dominate Donchian. It raises CAGR only modestly versus each finalist while giving up a meaningful part of Donchian's downside advantage.
- AND reduces exposure and return too much.
- OR produces the highest CAGR, but this is obtained by staying exposed more often and accepting worse volatility / downside. It is not a free diversification benefit.

## 3. Signal overlap / diversification

Across eligible symbol-days:

- both long: **32.80%**;
- both cash: **48.08%**;
- SMA-only long: **12.77%**;
- Donchian-only long: **6.35%**;
- total signal agreement: **80.88%**.

Daily strategy-return correlation is approximately **0.934**.

This is high. The two systems are different formulations of the same medium/long-term trend factor, not independent return engines. The roughly 19% signal-disagreement region is still economically meaningful, but the combination should not be treated as strong diversification in the usual portfolio sense.

## 4. Late-period stress: 2023-01-01 onward

| Variant | CAGR | Max DD |
|---|---:|---:|
| SMA120 | 21.02% | -40.91% |
| Donchian 100/50 | 19.19% | -36.99% |
| 50/50 blend | 20.47% | -38.58% |
| AND | 14.89% | -37.19% |
| OR | 25.29% | -41.21% |

The 50/50 blend again behaves almost exactly as an interpolation between the two finalists. OR increases return, but also gives up the drawdown advantage.

## 5. Transaction-cost stress

CAGR by cost assumption:

| Cost | SMA120 | Donchian 100/50 | 50/50 | AND | OR |
|---|---:|---:|---:|---:|---:|
| 5 bps | 47.91% | 46.95% | 48.00% | 39.69% | 55.23% |
| 10 bps | 46.86% | 46.77% | 47.39% | 39.24% | 54.45% |
| 25 bps | 43.76% | 46.24% | 45.57% | 37.88% | 52.13% |
| 50 bps | 38.75% | 45.37% | 42.58% | 35.66% | 48.34% |

Donchian becomes clearly superior to SMA120 as execution friction rises because its turnover is much lower.

## 6. Delisting-penalty stress

CAGR by assumed loss on disappearing long sleeve:

| Penalty | SMA120 | Donchian 100/50 | 50/50 | AND | OR |
|---|---:|---:|---:|---:|---:|
| 0% | 49.04% | 48.62% | 49.41% | 40.99% | 56.75% |
| 10% | 48.17% | 47.88% | 48.60% | 40.29% | 55.83% |
| 25% | 46.86% | 46.77% | 47.39% | 39.24% | 54.45% |
| 50% | 44.66% | 44.90% | 45.34% | 37.46% | 52.14% |
| 100% | 40.18% | 41.06% | 41.18% | 33.82% | 47.43% |

All variants remain positive under severe penalties. Donchian and the blend are slightly more resilient than SMA120 at the harshest settings.

## 7. Survivor vs historical non-survivor subgroup stress

This audit uncovered the most important new caveat.

### Current-control subset

| Variant | CAGR | Max DD |
|---|---:|---:|
| SMA120 | 58.53% | -55.65% |
| Donchian 100/50 | 65.25% | -46.02% |
| 50/50 blend | 62.53% | -47.95% |
| AND | 48.98% | -52.74% |
| OR | 75.47% | -51.23% |

### Historical / non-survivor subset only

| Variant | CAGR | Max DD |
|---|---:|---:|
| SMA120 | -4.34% | -67.76% |
| Donchian 100/50 | -1.26% | -57.87% |
| 50/50 blend | -1.44% | -62.48% |
| AND | -0.33% | -51.85% |
| OR | -5.40% | -72.64% |

This does **not** invalidate the earlier finding that trend following often protects individual dying assets relative to buy-and-hold. It does show that a portfolio made only from this selected set of non-survivors is not profitable after the common portfolio conventions used here.

Therefore the strong full-subset CAGR is materially supported by the seven current control assets. This is a real limitation of the current 29-symbol subset and must not be hidden by the aggregate result.

## 8. Expert interpretation of the ensemble idea

The proposed combination was worth testing, but the data do not support promoting a combined model yet.

### 50/50 blend

**Verdict: useful diagnostic, not superior finalist.**

It smooths the difference between the two strategies but does not create a new robust edge. Because the return correlation is ~0.93, the blend mostly averages two highly related trend systems.

### AND

**Verdict: reject.**

The additional confirmation cuts exposure and CAGR without a sufficient improvement in overall risk-adjusted behavior.

### OR

**Verdict: do not promote despite high CAGR.**

OR is effectively a higher-exposure version of the trend thesis. It improves CAGR in this sample but worsens volatility, worst rolling outcomes, and non-survivor behavior. Selecting it because its CAGR is highest would be exactly the type of backtest-driven escalation the research process is designed to avoid.

## 9. Finalist status after this audit

### SMA120

**KEEP FROZEN.**

It remains the primary continuity / forward-validation strategy because it has the longest independent validation chain.

### Donchian 100/50

**PROMOTE TO CO-FINALIST / STRONG CHALLENGER.**

On the current evidence it has the cleaner implementation profile: comparable return, lower drawdown, much lower turnover, better high-cost resilience, and somewhat better non-survivor downside.

### Combined model

**DO NOT FREEZE YET.**

No tested combination clearly dominates Donchian 100/50 on a sufficiently broad set of criteria.

## 10. What should happen next

The audit changes the priority slightly.

The biggest remaining uncertainty is no longer signal choice. It is **universe representativeness**. The current historical test contains only a selected 29-symbol subset, and the historical-only portfolio result is weak.

Before choosing a final multi-asset production strategy or ensemble, the next high-value step should be:

1. expand from the selected subset toward a broader point-in-time Binance USD-M historical universe;
2. pre-specify eligibility using only information available at the time;
3. use a simple historical liquidity / turnover screen if necessary, fixed before strategy results are viewed;
4. re-run only the two finalists, not a new indicator search;
5. keep BTC SMA120 forward validation running independently.

This is a more informative falsification test than further combining indicators on the current subset.

## 11. Research verdict

- **Medium/long-term crypto trend thesis:** PASS, still promising.
- **SMA120:** validated finalist, frozen forward control.
- **Donchian 100/50:** stronger implementation challenger.
- **50/50 ensemble:** no clear dominance.
- **AND:** reject.
- **OR:** high-return but riskier / likely exposure-driven; do not promote.
- **Key unresolved issue:** broad point-in-time universe validation.

The project remains aligned with the roadmap: signal discovery is effectively complete; the highest-value next work is broader universe realism and then execution / forward validation, not additional technical indicators.