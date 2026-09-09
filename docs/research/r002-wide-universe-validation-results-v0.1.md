# R002 Wide-Universe Point-in-Time Validation Results v0.1

**Project:** BotMarketplace strategy research  
**Date:** 2026-09-09  
**Engine:** `research/r002/wide_universe_point_in_time_finalists.py`  
**Frozen engine commit:** `9275d50e321dd24f5eabe83cc20dd340cfda6350`  
**Research posture:** falsification-first; no parameter changes after observing results  
**Final verdict:** neither finalist earns a broad-universe PASS; both move to **REDESIGN / hypothesis reassessment** for broad-universe use.

---

## 1. Dataset and run validation

The run completed on the full archive-defined Binance USD-M daily dataset.

Validated input:

- raw symbols: **864**;
- raw rows: **637,705**;
- date range: **2020-01-01 -> 2026-08-31**;
- duplicate symbol-date rows: **0**;
- missing core OHLCV rows: **0**;
- non-positive price rows: **0**;
- negative-volume rows: **0**;
- invalid OHLC rows: **0**;
- state validation: **PASS**;
- state version: `unicode-repair-0.2`;
- symbols ever reaching the common 200-observed-bar warmup: **641**;
- evaluation period: **2020-07-19 -> 2026-08-31**.

The full pre-specified stress grid was run:

- transaction costs: **5 / 10 / 25 / 50 bps**;
- disappearance penalties: **0 / 25 / 50 / 100%**;
- baseline: **10 bps + 25% disappearance penalty**.

No signal parameters, universe filters, or weighting rules were changed after seeing the result.

---

## 2. Baseline full-period result

| Strategy | CAGR | Max DD | Ann. vol | Calmar | Ending | Turnover | Avg gross exposure | Worst rolling 12m |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SMA120 | **20.64%** | **-65.84%** | 48.81% | 0.31 | 3.151x | 100.19 | 38.41% | -58.32% |
| Donchian 100/50 | **20.08%** | **-55.61%** | 38.68% | 0.36 | 3.063x | 15.58 | 29.07% | -48.98% |
| PTI passive | **4.89%** | **-92.01%** | 84.58% | 0.05 | 1.339x | 12.58 | 99.98% | -83.25% |

Interpretation:

- both frozen trend rules remain materially better than the broad PTI passive control on full-period downside and full-period CAGR;
- Donchian 100/50 preserves roughly the same full-period CAGR as SMA120 with substantially lower drawdown, volatility, exposure, and turnover;
- the broad-universe result is far weaker than the earlier 29-symbol finalist tournament, where both finalists were around 47% CAGR;
- full-period headline positivity alone is not sufficient for promotion because the pre-specified late-period test is weak.

---

## 3. Late-period test from 2023-01-01 — key falsification

Baseline 10 bps + 25% disappearance penalty:

| Strategy | CAGR | Max DD | Ann. vol | Calmar | Ending | Turnover | Avg gross exposure |
|---|---:|---:|---:|---:|---:|---:|---:|
| SMA120 | **1.20%** | **-60.95%** | 37.44% | 0.02 | 1.045x | 58.79 | 35.40% |
| Donchian 100/50 | **-1.51%** | **-51.92%** | 32.03% | -0.03 | 0.946x | 7.67 | 27.58% |
| PTI passive | **-11.10%** | **-86.41%** | 71.69% | -0.13 | 0.650x | 3.88 | 99.97% |

This is the decisive weakness.

The strategies still reduce damage dramatically versus passive, but neither produces an economically convincing late-period return profile:

- SMA120 is approximately flat after more than 3.5 years while experiencing roughly a 61% drawdown;
- Donchian 100/50 is negative over the same late period with roughly a 52% drawdown;
- therefore the strong full-period CAGR is not representative of the later regime.

Both baseline equity curves reached their all-time high on **2021-05-09** and did not recover that peak by 2026-08-31:

- SMA120 peak ~8.063x, ending ~3.151x;
- Donchian peak ~6.247x, ending ~3.063x.

The reported longest drawdown duration for both is **1,939 days**.

---

## 4. Calendar-year behavior at baseline

| Year | SMA120 | Donchian 100/50 | PTI passive |
|---|---:|---:|---:|
| 2020* | +23.83% | +34.66% | +67.42% |
| 2021 | **+249.22%** | **+193.52%** | +467.65% |
| 2022 | -30.25% | -18.06% | -78.32% |
| 2023 | +46.39% | +18.80% | +111.88% |
| 2024 | +19.39% | +8.65% | +18.20% |
| 2025 | **-38.55%** | **-26.84%** | -71.15% |
| 2026* | -2.74% | +0.15% | -10.07% |

`*` partial years.

Important pattern:

- the full-period CAGR is heavily helped by the extraordinary 2021 trend/bull regime;
- 2023 and 2024 remain positive, so there is not a simple immediate post-2021 collapse;
- however 2025 is deeply negative for both finalists, and 2026 through August is approximately flat/negative;
- the resulting post-2023 compound outcome is economically weak.

Worst baseline diagnostics:

### SMA120

- worst calendar year: **2025, -38.55%**;
- worst quarter: **2024-Q2, -27.07%**;
- worst month: **2021-05, -33.68%**;
- worst rolling 12 months: **-58.32%**.

### Donchian 100/50

- worst calendar year: **2025, -26.84%**;
- worst quarter: **2024-Q2, -30.51%**;
- worst month: **2024-04, -29.31%**;
- worst rolling 12 months: **-48.98%**.

---

## 5. Transaction-cost stress

At the baseline 25% disappearance penalty, full-period CAGR is:

| Cost | SMA120 | Donchian 100/50 |
|---|---:|---:|
| 5 bps | 21.63% | 20.24% |
| 10 bps | 20.64% | 20.08% |
| 25 bps | 17.71% | 19.63% |
| 50 bps | 12.99% | 18.87% |

Full-period interpretation:

- neither effect is erased by high transaction-cost stress;
- Donchian is much more cost-robust because turnover is far lower;
- cost sensitivity is therefore **not** the main reason for failure.

Late-period CAGR under the same 25% disappearance penalty:

| Cost | SMA120 post-2023 | Donchian post-2023 |
|---|---:|---:|
| 5 bps | +2.01% | -1.41% |
| 10 bps | +1.20% | -1.51% |
| 25 bps | -1.21% | -1.82% |
| 50 bps | -5.10% | -2.33% |

This reinforces the late-period problem:

- SMA120 is only marginally positive at low costs and turns negative by 25 bps;
- Donchian is negative even at 5 bps.

---

## 6. Disappearance / delisting stress

At 10 bps transaction cost, full-period CAGR is:

| Disappearance penalty | SMA120 | Donchian 100/50 | PTI passive |
|---|---:|---:|---:|
| 0% | 20.94% | 20.45% | 6.86% |
| 25% | 20.64% | 20.08% | 4.89% |
| 50% | 20.34% | 19.72% | 2.95% |
| 100% | 19.73% | 18.98% | -0.84% |

Interpretation:

- the trend-following result does **not** depend on an optimistic delisting assumption;
- disappearance stress only modestly reduces full-period finalist CAGR;
- passive is much more vulnerable;
- disappearance handling is therefore not the main failure mode.

Post-2023 at 10 bps:

- SMA120 moves from about +1.62% CAGR at 0% disappearance penalty to about -0.07% at 100%;
- Donchian moves from about -1.00% to about -3.02%.

Again, the late-period result remains weak before applying extreme disappearance assumptions.

---

## 7. Breadth and exposure

Across the full evaluation period:

- average eligible assets: **197.6**;
- median eligible assets: **150**;
- SMA120 average active assets: **60.7**; median **32**;
- Donchian average active assets: **45.3**; median **26**;
- SMA120 average exposure: **38.4%**;
- Donchian average exposure: **29.1%**.

The universe expands substantially through time. Average eligible breadth by calendar year is approximately:

- 2020: 20;
- 2021: 75;
- 2022: 126;
- 2023: 154;
- 2024: 222;
- 2025: 318;
- 2026 through August: 458.

At 2026-08-31, **513** instruments are currently eligible, although **641** instruments became eligible at some point in history.

The poor 2025-2026 performance occurs while the eligible universe is much broader than in the early sample. This is an important diagnostic association, but it does **not** by itself prove that growing breadth causes the deterioration.

---

## 8. Concentration diagnostics

Baseline concentration summary:

### SMA120

- top contributor: `DOGEUSDT`;
- top-5 symbols: `DOGEUSDT, BNBUSDT, ETHUSDT, ETCUSDT, SOLUSDT`;
- top-5 share of all positive asset gains: **20.82%**;
- top-5 gains as a fraction of net portfolio P&L: **65.56%**;
- excluding top contributor: CAGR **17.91%**, Max DD **-65.33%**;
- excluding top 5: CAGR **13.63%**, Max DD **-65.79%**.

### Donchian 100/50

- top contributor: `BNBUSDT`;
- top-5 symbols: `BNBUSDT, DOGEUSDT, ETHUSDT, ADAUSDT, SOLUSDT`;
- top-5 share of all positive asset gains: **22.85%**;
- top-5 gains as a fraction of net portfolio P&L: **56.06%**;
- excluding top contributor: CAGR **18.74%**, Max DD **-55.75%**;
- excluding top 5: CAGR **13.46%**, Max DD **-57.60%**.

Interpretation:

- neither finalist is literally explained by only one or two assets;
- excluding the five best contributors still leaves positive full-period CAGR around 13.5%;
- nevertheless the best assets materially improve the final economics, and removing them does not solve the drawdown problem.

---

## 9. Survivor vs historical/non-survivor attribution

Baseline net wealth contribution:

| Strategy | Archive-survivor contribution | Historical/non-survivor contribution |
|---|---:|---:|
| SMA120 | +2.2335 | **-0.0829** |
| Donchian 100/50 | +2.2115 | **-0.1485** |

Among the 641 ever-eligible instruments:

- 513 are archive survivors at the August 2026 archive endpoint;
- 128 are historical/non-survivors.

The non-survivor group remains net negative for both finalists. Therefore all aggregate net profit is supplied by instruments that are still present in the latest archive snapshot, with non-survivors subtracting from that profit.

This does not mean the result is a simple five-asset survivorship artefact, because the top-5 exclusion test remains positive. It does mean the full-universe test fails to show that trend following makes the broad historical/non-survivor population independently profitable as a group.

---

## 10. Finalist comparison

### SMA120 strengths

- materially beats passive over the full period;
- remains positive under severe disappearance stress;
- remains positive full-period even at 50 bps cost;
- top-5 exclusion remains positive;
- existing BTC forward clock is independent and remains frozen.

### SMA120 weaknesses

- post-2023 CAGR only ~1.2% at baseline;
- post-2023 Max DD ~-61%;
- 25 bps costs make post-2023 CAGR negative;
- extremely long unresolved drawdown from the 2021 peak;
- much higher turnover and worse cost robustness than Donchian;
- historical/non-survivor aggregate contribution is negative.

### Donchian 100/50 strengths

- approximately same full-period CAGR as SMA120;
- lower Max DD and volatility;
- far lower turnover;
- excellent full-period cost robustness;
- top-5 exclusion remains positive;
- disappearance stress does not erase the effect.

### Donchian 100/50 weaknesses

- post-2023 CAGR is negative even at baseline;
- post-2023 remains negative at 5 bps;
- unresolved drawdown from the 2021 peak;
- historical/non-survivor aggregate contribution is more negative than for SMA120;
- therefore the cleaner risk/cost profile does not rescue the late-period economic result.

---

## 11. Formal verdict

### SMA120 — **REDESIGN / NOT A BROAD-UNIVERSE PASS**

The signal shows real full-period downside protection relative to passive and survives cost/delisting stress. It is not falsified as a BTC-specific or narrower-universe trend rule. However, the complete archive-defined wide-universe implementation does not pass because late-period economics are too weak relative to the drawdown burden.

The existing frozen BTC SMA120 forward validation continues independently and must **not** be reset or rewritten because of this broad-universe research result.

### Donchian 100/50 — **REDESIGN / NOT A BROAD-UNIVERSE PASS**

Donchian has the stronger full-period implementation profile: lower drawdown, lower volatility, much lower turnover, and much better cost robustness than SMA120. But the pre-specified post-2023 slice is negative. Therefore it does not satisfy the promotion rule and should **not** start a formal forward clock at this stage.

### Combined conclusion

**Neither finalist passes the complete archive-defined broad-universe validation.**

This is not the same as saying medium/long-term trend following has no evidence. The full-period trend portfolios remain vastly better than passive on downside and retain positive CAGR under harsh execution/delisting assumptions. The falsified proposition is stronger and more specific:

> A simple equal-sleeve application of frozen SMA120 or Donchian 100/50 across the complete Binance archive-defined universe is not yet validated as a robust broad-universe strategy.

---

## 12. Anti-overfitting consequence

Do **not** respond to this result by trying:

- SMA110/115/125/130;
- Donchian 90/45 or 120/60;
- RSI / MACD / ADX rescue filters;
- liquidity thresholds chosen from this result;
- per-asset parameters;
- optimized weighting;
- leverage or shorting;
- manual removal of poor contracts.

Those would amount to fitting the same failed sample.

---

## 13. Next research step

Because neither finalist passes, follow Case C of the roadmap:

1. keep frozen BTC SMA120 forward validation unchanged;
2. do not start Donchian formal forward tracking yet;
3. pause finalist promotion;
4. perform a **failure-decomposition / universe-definition audit**, not signal retuning;
5. determine whether the archive-defined Binance USD-M universe is economically the intended domain, including the pre-existing caveat that later archives contain non-traditional/tokenized/synthetic exposures;
6. any narrower future universe must be defined by an objective, performance-independent metadata rule before rerunning strategy results;
7. any new strategy research must be treated as a genuinely new hypothesis/version, not an in-sample rescue of SMA120 or Donchian 100/50.

The next unknown is now **domain/universe validity and regime robustness**, not which nearby indicator parameter performs best.
