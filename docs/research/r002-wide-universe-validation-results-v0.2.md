# R002 Wide-Universe Point-in-Time Validation Results v0.2

**Project:** BotMarketplace strategy research  
**Date:** 2026-09-09  
**Status:** final after listing-episode correction  
**Frozen signal engine commit:** `9275d50e321dd24f5eabe83cc20dd340cfda6350`  
**Episode-corrected launcher commit:** `6fa268fc764f8db69809f0b7bf79edf3f79d14bc`  
**Research posture:** falsification-first; no parameter changes after observing results

## 1. Why v0.2 exists

The initial wide-universe run grouped history by ticker symbol. A subsequent metadata/domain audit and listing-episode audit showed that three symbols contained long gaps (>7 calendar days) consistent with distinct listing episodes:

- BNXUSDT: 2023-01-31 -> 2023-02-22;
- ICPUSDT: 2022-08-31 -> 2022-09-27;
- TLMUSDT: 2023-02-28 -> 2023-03-30.

The corrected rerun therefore treats each post-gap episode as a separate instrument identity and fully resets warmup, rolling indicator history and signal state. No strategy parameter, cost assumption, disappearance assumption or portfolio rule changed.

## 2. Corrected dataset identities

Base archive input remains:

- 864 base symbols;
- 637,705 daily rows;
- 2020-01-01 -> 2026-08-31.

After episode segmentation:

- 867 episode identities;
- 3 long-gap events;
- 644 episode identities independently reach the common 200-observed-bar warmup;
- evaluation remains 2020-07-19 -> 2026-08-31.

## 3. Corrected baseline result

Baseline remains 10 bps cost + 25% disappearance penalty.

| Strategy | Full CAGR | Full Max DD | Full Vol | Calmar | Ending | Turnover | Post-2023 CAGR | Post-2023 Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SMA120 | **20.55%** | **-65.99%** | 48.86% | 0.31 | 3.137x | 100.43 | **1.16%** | **-60.95%** |
| Donchian 100/50 | **20.05%** | **-55.74%** | 38.70% | 0.36 | 3.058x | 15.61 | **-1.53%** | **-51.92%** |
| PTI passive | **5.15%** | **-91.89%** | 84.68% | 0.06 | 1.359x | 12.67 | **-10.47%** | **-86.41%** |

The episode correction changes the headline result only minimally relative to v0.1.

## 4. Corrected calendar-year baseline

| Year | SMA120 | Donchian 100/50 | PTI passive |
|---|---:|---:|---:|
| 2020* | +23.83% | +34.66% | +67.42% |
| 2021 | +249.22% | +193.52% | +467.65% |
| 2022 | -30.46% | -18.13% | -78.55% |
| 2023 | +46.20% | +18.69% | +117.44% |
| 2024 | +19.39% | +8.65% | +18.20% |
| 2025 | -38.55% | -26.84% | -71.15% |
| 2026* | -2.74% | +0.15% | -10.07% |

`*` partial year.

The correction affects mainly 2022-2023 and does not alter the dominant regime pattern: very strong 2021, weak 2022, recovery in 2023-2024, then severe deterioration in 2025 and weak 2026 YTD.

## 5. Corrected cost stress

At 25% disappearance penalty, full-period CAGR:

| Cost | SMA120 | Donchian 100/50 |
|---|---:|---:|
| 5 bps | 21.55% | 20.20% |
| 10 bps | 20.55% | 20.05% |
| 25 bps | 17.62% | 19.59% |
| 50 bps | 12.89% | 18.83% |

Post-2023 CAGR:

| Cost | SMA120 | Donchian 100/50 |
|---|---:|---:|
| 5 bps | +1.98% | -1.43% |
| 10 bps | +1.16% | -1.53% |
| 25 bps | -1.25% | -1.84% |
| 50 bps | -5.15% | -2.36% |

The prior conclusion is unchanged: transaction cost sensitivity is not the main failure mode, and Donchian remains much more cost-efficient.

## 6. Corrected disappearance stress

At 10 bps transaction cost, full-period CAGR:

| Disappearance penalty | SMA120 | Donchian 100/50 | PTI passive |
|---|---:|---:|---:|
| 0% | 20.86% | 20.42% | 7.24% |
| 25% | 20.55% | 20.05% | 5.15% |
| 50% | 20.25% | 19.68% | 3.10% |
| 100% | 19.64% | 18.95% | -0.90% |

Post-2023:

- SMA120 ranges from +1.59% at 0% penalty to -0.11% at 100%;
- Donchian ranges from -1.03% to -3.04%;
- passive remains materially worse.

The late-period weakness is therefore still present before extreme disappearance stress.

## 7. Listing-episode correction magnitude

The episode audit found only three long-gap symbols out of 864 base symbols. This is not a systemic dataset-identity failure.

The episode-corrected rerun confirms that resetting those histories does not materially change:

- full-period CAGR;
- full-period Max DD;
- post-2023 CAGR;
- post-2023 Max DD;
- cost robustness;
- disappearance robustness;
- concentration structure.

Therefore the initial broad-universe REDESIGN conclusion was not created by the listing-episode bug.

## 8. Final verdict after correction

### SMA120

**FINAL STATUS: REDESIGN / NOT PASS for naive complete archive-defined broad-universe deployment.**

Reasons:

- full-period trend effect remains positive and much better than passive on downside;
- but post-2023 CAGR is only ~1.16% with ~-60.95% Max DD;
- late-period performance turns negative at 25 bps cost;
- the episode correction does not rescue the result.

The existing BTC SMA120 forward record continues independently and must not be reset.

### Donchian 100/50

**FINAL STATUS: REDESIGN / NOT PASS for naive complete archive-defined broad-universe deployment.**

Reasons:

- full-period CAGR remains ~20% with materially better drawdown, volatility and turnover than SMA120;
- but post-2023 CAGR remains negative even at low transaction costs;
- the episode correction does not rescue the result.

Do not start a formal Donchian forward clock yet.

## 9. What remains supported

The corrected evidence still supports a weaker statement:

> Medium/long-term trend following materially improves downside behavior relative to naive equal-sleeve passive exposure across the archive-defined Binance USD-M universe.

What is not validated is the stronger production proposition:

> Deploy either frozen signal with equal sleeves across the complete archive-defined universe and expect robust broad-universe economics through the later sample.

## 10. Next research step

Do not retune SMA or Donchian windows and do not add new indicators.

The next step remains a failure-decomposition / economic-domain decision:

1. preserve the episode-corrected run as the canonical wide-universe result;
2. continue objective decomposition of later cohorts and instrument-domain composition;
3. decide whether a performance-independent universe definition can be justified economically;
4. only if such a domain rule is justified before rerunning, create a new universe protocol;
5. otherwise stop broad-universe rescue work on this dataset and move to a genuinely new hypothesis or independent dataset.
