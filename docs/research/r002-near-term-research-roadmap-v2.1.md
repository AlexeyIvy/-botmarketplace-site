# R002 Near-Term Research Roadmap v2.1

**Project:** BotMarketplace strategy research  
**Date:** 2026-09-09  
**Status:** post wide-universe falsification  
**Research posture:** falsification-first, no result chasing, no hidden parameter optimization  
**Previous full evidence roadmap:** `docs/research/r002-near-term-research-roadmap-v2.0.md`  
**Wide-universe results:** `docs/research/r002-wide-universe-validation-results-v0.1.md`

---

## 1. Executive decision

The pre-specified complete Binance archive-defined wide-universe point-in-time test is complete.

Input and protocol:

- 864 archive-defined symbols;
- 637,705 daily rows;
- 2020-01-01 -> 2026-08-31;
- 641 symbols ever reached the common 200-observed-bar warmup;
- frozen SMA120;
- frozen Donchian 100/50;
- point-in-time passive comparator;
- equal sleeves;
- signal at close t applied to the next return;
- 5/10/25/50 bps cost stress;
- 0/25/50/100% disappearance stress;
- post-2023 and concentration diagnostics.

Formal result:

- **SMA120 wide-universe status: REDESIGN / NOT PASS**;
- **Donchian 100/50 wide-universe status: REDESIGN / NOT PASS**;
- **neither finalist is promoted as a complete archive-defined broad-universe strategy**.

The underlying trend thesis is not fully rejected because both strategies materially outperform the PTI passive control on full-period downside and remain positive under harsh cost/delisting stress. The failed proposition is the stronger one: simple equal-sleeve deployment across the complete archive-defined Binance USD-M universe is not robustly validated, primarily because late-period economics are weak.

---

## 2. Key wide-universe evidence

Baseline 10 bps + 25% disappearance penalty:

| Strategy | Full CAGR | Full Max DD | Post-2023 CAGR | Post-2023 Max DD | Turnover |
|---|---:|---:|---:|---:|---:|
| SMA120 | 20.64% | -65.84% | 1.20% | -60.95% | 100.19 |
| Donchian 100/50 | 20.08% | -55.61% | -1.51% | -51.92% | 15.58 |
| PTI passive | 4.89% | -92.01% | -11.10% | -86.41% | 12.58 |

Important robustness findings:

- full-period cost stress does not erase either trend effect;
- full-period disappearance stress does not erase either trend effect;
- Donchian remains materially more cost-efficient than SMA120;
- excluding the top five contributors still leaves ~13.5% full-period CAGR for each finalist;
- nevertheless historical/non-survivor aggregate contribution is negative for both;
- both equity curves peaked in May 2021 and remained below that peak at the August 2026 endpoint;
- the post-2023 return profile is not economically convincing relative to drawdown.

Therefore neither candidate meets the pre-specified PASS rule.

---

## 3. Frozen strategy status

### 3.1 SMA120

Exact rule remains frozen:

`close > SMA120 -> long, else cash`

The **existing BTC SMA120 forward validation continues unchanged**.

Do not:

- reset its forward clock;
- change SMA length;
- reinterpret the broad-universe failure as a reason to alter the already frozen BTC record.

The wide-universe result means only that SMA120 is not currently validated for naive equal-sleeve deployment across the complete archive-defined universe.

### 3.2 Donchian 100/50

Exact challenger remains:

- entry above prior 100-day high;
- exit below prior 50-day low;
- prior-data-only channels.

Because the wide-universe test did not pass:

- **do not start a formal Donchian forward clock yet**;
- do not retune 100/50;
- retain it as research evidence of an independent medium/long-term trend formulation.

---

## 4. What is now falsified

The following proposition is **not validated**:

> Apply SMA120 or Donchian 100/50 with equal sleeves across every contract that becomes eligible inside the complete Binance archive-defined USD-M universe and expect robust broad-universe economics.

Reasons:

- strong full-period results are not reproduced in the post-2023 slice;
- SMA120 post-2023 is approximately flat while suffering very large drawdown;
- Donchian post-2023 is negative;
- the later historical universe is much broader than the early sample;
- historical/non-survivor contribution remains negative in aggregate.

This does **not** prove that trend following is useless, nor does it invalidate the independent BTC forward test.

---

## 5. Anti-overfitting freeze remains in force

Do not add or retune now:

- SMA lengths;
- Donchian windows;
- RSI;
- MACD;
- ADX;
- volatility-target thresholds;
- per-asset parameters;
- optimized weights;
- liquidity filters selected after seeing the result;
- leverage;
- shorts;
- machine learning;
- social/on-chain filters.

Do not manually remove bad tickers from this sample.

A poor result is research information, not a prompt to search nearby parameter space.

---

## 6. NEXT STEP — failure decomposition / universe-definition audit

**Priority:** immediate.

The next question is not “which indicator should we try?”

The next question is:

> Is the complete archive-defined Binance USD-M universe the correct economic domain for the strategy hypothesis, and what objectively explains the deterioration as the universe and regime change?

This stage is diagnostic. It must not optimize strategy parameters.

### 6.1 Required diagnostics using existing outputs first

1. Decompose contribution by objective listing/eligibility cohort.
2. Examine breadth expansion through time alongside strategy returns and exposure.
3. Quantify survivor/non-survivor contribution more deeply.
4. Identify whether losses are diffuse across the later universe or concentrated in specific objectively definable instrument classes.
5. Confirm that the poor late period is not an artefact of one execution or disappearance assumption.

### 6.2 Universe-domain audit

The existing full-universe protocol already documented an important caveat: later Binance USD-M archives include exposures beyond traditional crypto tokens, including tokenized/synthetic instruments tied to equities, indices, commodities, or other underlyings.

If a future crypto-native universe test is justified:

- classification must come from an objective metadata source;
- the classification rule must be written and frozen before running strategy results;
- no ticker may be included/excluded because of observed backtest performance;
- the same 200-observed-bar PTI warmup and no-future-information rules should remain unless a genuinely new protocol explicitly says otherwise.

This would be a **new universe hypothesis**, not a rescue filter fitted to the current result.

### 6.3 New data / new hypothesis requirement

If diagnostics do not justify an objective domain revision, stop trying to rescue these broad-universe implementations on the same dataset.

Any next strategy branch must introduce a genuinely new economic hypothesis and/or independent dataset, with a new version and new validation clock.

---

## 7. Decision gates after the audit

### Case A — objective domain mismatch is demonstrated before strategy retest

Create a new, pre-specified universe protocol using performance-independent metadata, then rerun the same frozen signals as a fresh universe-validation branch.

### Case B — no objective domain mismatch is demonstrated

Accept the complete archive-defined broad-universe result as a failure for both finalists. Stop broad-universe rescue work on this sample and return to hypothesis generation / independent data.

### Case C — diagnostics reveal an implementation bug

Fix only the bug, document it before rerunning, version the engine, and rerun the exact frozen protocol. Do not combine a bug fix with parameter or universe tuning.

---

## 8. Current decision hierarchy

1. **BTC SMA120 forward record** — continues independently; frozen.
2. **SMA120 broad-universe deployment** — REDESIGN / not validated.
3. **Donchian 100/50 broad-universe deployment** — REDESIGN / not validated; no formal forward clock.
4. **Donchian vs SMA implementation comparison** — Donchian remains structurally cleaner on drawdown/turnover, but this does not override failed late-period validation.
5. **50/50 / AND / OR ensembles** — remain diagnostic only; do not reopen now.
6. **ADX / volatility targeting branches** — not promoted.
7. **R001 options** — paused in redesign.
8. **New technical indicators / retuning** — explicitly prohibited at this stage.

---

## 9. Immediate execution order

1. Preserve all raw wide-universe result files and frozen engine commit.
2. Record the wide-universe result and verdict in GitHub.
3. Perform failure decomposition using existing outputs.
4. Decide whether an objective universe-domain mismatch exists.
5. Only if independently justified, specify a new universe protocol before any rerun.
6. Otherwise stop broad-universe rescue work and move to a genuinely new hypothesis/data branch.

---

## 10. Plain-language summary

The large full-universe test did what it was supposed to do: it made the earlier result much harder to defend.

Both trend rules still protect capital far better than passively holding the entire historical universe, and Donchian remains notably cheaper and less volatile than SMA120. But neither strategy shows a sufficiently strong post-2023 economic result on the complete archive-defined universe.

So the correct next move is **not** to search for a slightly better moving average or breakout window. The correct next move is to understand whether the tested universe itself matches the intended economic hypothesis. If it does, the broad-universe versions have failed. If it does not, any revised universe must be defined objectively before the strategy is tested again.
