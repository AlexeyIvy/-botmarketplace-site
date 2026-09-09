# R002 Donchian Breakout Validation v0.1

## Purpose

Test whether the broader trend-following thesis survives when the SMA120 signal is replaced by a structurally different trend rule. This is not a parameter hunt and not a modification of the frozen R002 SMA120 rule.

The independent family was fixed before evaluating results:

- Donchian 50-day entry / 25-day exit
- Donchian 100-day entry / 50-day exit (central candidate)
- Donchian 200-day entry / 100-day exit

The key question is not whether one breakout rule beats SMA120 by a few basis points. The question is whether a different trend mechanism also beats buy-and-hold and reduces drawdown across the same point-in-time historical subset.

## Data and controls

Input: `r002_binance_historical_subset_daily.csv`.

Cleaning and portfolio mechanics match the prior point-in-time work as closely as possible:

- post-delisting dead archive tails are removed after the last positive-volume day;
- BTCSTUSDT and COCOSUSDT fail the common 200-day real-history requirement and are excluded;
- 27 symbols remain;
- all variants use a common 200-day eligibility warmup;
- equal sleeve per currently eligible symbol;
- inactive sleeves remain in cash;
- no leverage;
- signal formed on day t is applied to day t+1 return;
- breakout channels use only prior highs/lows via a one-day shift;
- baseline transaction cost: 10 bps per absolute portfolio weight change;
- baseline delisting penalty: 25% of any long sleeve that disappears next day;
- cash return: 0.

The common 200-day warmup is intentional: it puts all breakout variants and the SMA120 comparator onto the same eligibility schedule and therefore the same evaluation start.

## Baseline results

Evaluation period: 2020-07-19 to 2026-08-31.

| Strategy | CAGR | Max DD | Ann. vol | Calmar | Ending multiple | Turnover |
|---|---:|---:|---:|---:|---:|---:|
| Donchian 50/25 | 34.92% | -49.45% | 43.80% | 0.71 | 6.247x | 29.65 |
| **Donchian 100/50** | **46.77%** | **-39.78%** | **43.96%** | **1.18** | **10.453x** | **14.73** |
| Donchian 200/100 | 33.66% | -48.61% | 44.91% | 0.69 | 5.896x | 9.57 |
| SMA120, common warmup | 46.86% | -54.53% | 48.95% | 0.86 | 10.492x | 86.94 |
| Buy & hold | 24.84% | -89.47% | 77.19% | 0.28 | 3.884x | 11.28 |

## Interpretation

The important result is that trend following survives a major change in signal definition.

All three Donchian variants beat the point-in-time buy-and-hold comparator on CAGR and drawdown. That matters more than the fact that the 100/50 rule is the strongest of the three.

The central 100/50 rule is especially notable:

- CAGR is essentially the same as SMA120 under the common-warmup comparison: 46.77% vs 46.86%;
- maximum drawdown is materially lower: -39.78% vs -54.53%;
- turnover is dramatically lower: 14.73 vs 86.94;
- Calmar is higher: 1.18 vs 0.86.

This is evidence that the prior SMA120 results are not merely a moving-average artefact. A stateful breakout rule built from prior highs/lows produces a similar return profile and, for the central rule, a better drawdown/turnover profile.

However, the family is not flat. The 50/25 and 200/100 variants are clearly weaker than 100/50. Therefore this is not a license to optimize Donchian windows more finely around 100/50. Doing so on the same sample would create a new overfitting path.

## Late-period test

Period: 2023-01-01 to 2026-08-31, with indicators and state carried forward from prior history.

| Strategy | CAGR | Max DD | Ann. vol | Calmar | Ending multiple | Turnover |
|---|---:|---:|---:|---:|---:|---:|
| Donchian 50/25 | 14.18% | -42.34% | 34.49% | 0.33 | 1.625x | 16.89 |
| **Donchian 100/50** | **19.19%** | **-36.99%** | **34.19%** | **0.52** | **1.902x** | **7.91** |
| Donchian 200/100 | 1.23% | -47.47% | 35.28% | 0.03 | 1.046x | 5.82 |
| SMA120 | 21.02% | -40.91% | 37.46% | 0.51 | 2.011x | 52.74 |
| Buy & hold | 18.71% | -69.45% | 60.32% | 0.27 | 1.874x | 2.86 |

The late-period result is again useful:

- Donchian 100/50 remains competitive with SMA120;
- its late-period CAGR is slightly lower than SMA120 but drawdown and volatility are also lower;
- Donchian 200/100 weakens substantially, reinforcing the warning against treating every long-horizon breakout as equivalent;
- both SMA120 and Donchian 100/50 remain materially better than buy-and-hold on drawdown.

## Cost stress

Delisting penalty remains fixed at 25%.

| Cost per absolute weight change | Donchian 100/50 CAGR | Donchian Max DD | SMA120 CAGR | SMA120 Max DD |
|---|---:|---:|---:|---:|
| 5 bps | 46.95% | -39.76% | 47.91% | -53.91% |
| 10 bps | 46.77% | -39.78% | 46.86% | -54.53% |
| 25 bps | 46.24% | -39.82% | 43.76% | -56.32% |
| 50 bps | 45.37% | -39.99% | 38.75% | -59.17% |

Donchian 100/50 is much less sensitive to transaction-cost stress because its turnover is far lower. At 25-50 bps it overtakes SMA120 on CAGR by an increasing margin while maintaining a shallower drawdown.

This does **not** mean it should automatically replace frozen SMA120. The frozen SMA120 has already passed a broader chain of BTC, cross-asset, survivorship and forward-preparation tests. Donchian 100/50 is a newer branch and therefore has less accumulated evidence.

## Verdict

**Independent trend thesis: PASS.**

**Donchian 100/50 candidate: PROMISING / ADVANCE, not yet frozen.**

This experiment materially increases confidence in the broader premise that medium/long-horizon trend following in crypto is not specific to SMA120.

The result also changes the priority of the research program slightly: Donchian 100/50 deserves to be carried into the next unified comparison because it offers nearly SMA120-level return with materially lower drawdown and turnover on this point-in-time subset.

## What not to do next

Do not search 80/40, 90/45, 110/55, 120/60, etc. on the same sample.

Do not combine Donchian + SMA + ADX + volatility targeting into a large rule stack yet.

Do not replace frozen SMA120 based on this single branch.

## Recommended next step

Build one unified candidate comparison using identical portfolio mechanics and cost assumptions for:

1. frozen SMA120;
2. SMA120 + ADX20;
3. Donchian 100/50;
4. previously tested volatility-targeting branch as a risk-control reference, not a leading candidate.

Then compare full-period, late-period, survivor/non-survivor behavior, turnover and cost stress side by side. The goal should be to identify whether Donchian 100/50 is a genuinely superior robust candidate or merely a favorable fit to this specific subset.
