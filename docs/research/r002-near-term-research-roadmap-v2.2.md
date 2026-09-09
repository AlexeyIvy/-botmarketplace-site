# R002 Near-Term Research Roadmap v2.2

**Project:** BotMarketplace strategy research  
**Date:** 2026-09-09  
**Status:** post episode-corrected wide-universe falsification  
**Research posture:** falsification-first, no result chasing, no hidden parameter optimization  
**Canonical wide-universe result:** `docs/research/r002-wide-universe-validation-results-v0.2.md`

---

## 1. Executive status

The complete archive-defined Binance USD-M wide-universe point-in-time test has now been rerun with listing-episode identity correction.

Final corrected baseline (10 bps + 25% disappearance penalty):

| Strategy | Full CAGR | Full Max DD | Post-2023 CAGR | Post-2023 Max DD | Turnover |
|---|---:|---:|---:|---:|---:|
| SMA120 | 20.55% | -65.99% | 1.16% | -60.95% | 100.43 |
| Donchian 100/50 | 20.05% | -55.74% | -1.53% | -51.92% | 15.61 |
| PTI passive | 5.15% | -91.89% | -10.47% | -86.41% | 12.67 |

Formal decision:

- **SMA120 broad-universe status: FINAL REDESIGN / NOT PASS**;
- **Donchian 100/50 broad-universe status: FINAL REDESIGN / NOT PASS**;
- listing-episode correction does not change the conclusion.

The trend thesis is weakened but not fully rejected: both signals still materially improve downside behavior versus naive passive exposure, and full-period profitability survives harsh cost/disappearance stress.

---

## 2. Data-identity audit outcome

A metadata/domain audit found that current Binance `onboardDate` can refer to a newer listing episode for symbols that had older historical episodes. A separate episode audit then froze the rule:

> Any gap greater than 7 calendar days between observed daily bars starts a new instrument episode.

The archive contained:

- 864 base symbols;
- 867 listing episodes;
- only 3 multi-episode symbols: BNXUSDT, ICPUSDT, TLMUSDT;
- 3 long-gap events total.

The corrected rerun fully reset warmup, rolling history and signal state at each new episode.

Result: the correction changed headline metrics only minimally. Therefore the original failure was not caused by a systemic symbol-identity bug.

---

## 3. Frozen strategy status

### SMA120

Frozen rule remains:

`close > SMA120 -> long, else cash`

The existing BTC SMA120 forward record continues independently. Do not reset it.

Do not retune SMA length because of the broad-universe result.

### Donchian 100/50

Frozen challenger remains:

- entry above prior 100-day high;
- exit below prior 50-day low;
- prior-data-only channels.

Because the corrected wide-universe test still fails:

- do not start a formal Donchian forward clock;
- do not retune 100/50;
- retain the result as independent evidence about the same medium/long-term trend factor.

---

## 4. What is now considered falsified

Not validated:

> Naively deploy SMA120 or Donchian 100/50 with equal sleeves across every eligible contract in the complete archive-defined Binance USD-M universe and expect robust broad-universe economics through the later sample.

Reasons:

- corrected post-2023 SMA120 CAGR is only ~1.16% with ~-61% Max DD;
- corrected post-2023 Donchian CAGR is ~-1.53% with ~-52% Max DD;
- late-period results remain weak before extreme execution stress;
- episode correction does not materially change the result;
- later cohorts remain the main unresolved economic problem.

This does not invalidate the independent frozen BTC forward record.

---

## 5. Anti-overfitting freeze

Do not add or retune now:

- SMA windows;
- Donchian windows;
- RSI;
- MACD;
- ADX;
- volatility-target thresholds;
- liquidity filters chosen after results;
- manual ticker exclusions;
- optimized weights;
- per-asset parameters;
- leverage;
- shorts;
- machine learning;
- social/on-chain filters.

No broad-universe rescue tuning on this sample.

---

## 6. NEXT STEP — economic-domain / cohort decomposition decision

**Priority:** immediate.

The remaining question is no longer an implementation-debug question. The corrected engine is sufficiently stable for the current research decision.

The next question is:

> Why do later listing/eligibility cohorts have much weaker economics, and does an objective economic universe definition exist that was conceptually intended by the original hypothesis?

Required work:

1. preserve the corrected wide-universe run as canonical;
2. decompose performance by listing/eligibility cohort using corrected episode identities;
3. compare later cohort contribution with breadth expansion and market regime;
4. use performance-independent metadata only when studying instrument classes;
5. determine whether the complete archive-defined Binance USD-M universe is broader than the intended economic domain.

Important: identifying a weak cohort after the fact is diagnostic evidence, not permission to exclude it.

---

## 7. Decision gates

### Case A — objective domain mismatch is demonstrated

Only if an economically motivated, performance-independent classification rule can be written before a new run:

1. create a new universe protocol;
2. freeze the rule;
3. rerun the exact frozen SMA120 and Donchian 100/50 signals as a new universe-validation branch;
4. treat it as a new hypothesis, not a rescue filter.

### Case B — no objective domain mismatch is demonstrated

Accept the corrected broad-universe REDESIGN as final and stop trying to rescue these broad-universe implementations on the same sample.

Move to a genuinely new economic hypothesis and/or independent dataset.

### Case C — a new implementation bug is discovered

Fix only the bug, document it before rerunning and version the engine. Do not combine bug fixes with parameter or universe tuning.

---

## 8. Current decision hierarchy

1. **BTC SMA120 forward record** — continues independently; frozen.
2. **SMA120 complete archive-defined broad-universe deployment** — FINAL REDESIGN / not validated.
3. **Donchian 100/50 complete archive-defined broad-universe deployment** — FINAL REDESIGN / not validated; no formal forward clock.
4. **Donchian structural comparison** — still cleaner than SMA on drawdown/turnover, but not sufficient for promotion.
5. **50/50 / AND / OR ensembles** — remain diagnostic only; do not reopen.
6. **ADX / volatility targeting branches** — not promoted.
7. **R001 options** — paused in redesign.
8. **New technical indicators / retuning** — prohibited at this stage.

---

## 9. Immediate execution order

1. Preserve all episode-corrected result files and commits.
2. Treat `r002-wide-universe-validation-results-v0.2.md` as the canonical wide-universe result.
3. Continue corrected cohort/domain decomposition.
4. Decide whether an objective economic-domain mismatch exists.
5. Only if independently justified, write a new universe protocol before any rerun.
6. Otherwise stop broad-universe rescue work and move to a new hypothesis/data branch.
