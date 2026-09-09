# R002 Wide-Universe Failure Decomposition v0.1

**Project:** BotMarketplace strategy research  
**Date:** 2026-09-09  
**Status:** diagnostic analysis after wide-universe REDESIGN verdict  
**Inputs:** existing wide-universe output files only; no new strategy backtest  
**Research posture:** falsification-first; no signal retuning or performance-selected universe filters

---

## 1. Purpose

Decompose why the complete Binance archive-defined point-in-time test failed to earn a PASS for frozen SMA120 and Donchian 100/50.

This stage does **not** modify:

- SMA120;
- Donchian 100/50;
- the 200-observed-bar warmup;
- transaction-cost assumptions;
- disappearance assumptions;
- portfolio weights.

The analysis uses only the already-produced diagnostics:

- `r002_wide_universe_metrics.csv`;
- `r002_wide_universe_yearly_returns.csv`;
- `r002_wide_universe_breadth.csv`;
- `r002_wide_universe_baseline_equity.csv`;
- `r002_wide_universe_contributions_baseline.csv`;
- `r002_wide_universe_concentration_summary.csv`;
- `r002_wide_universe_exclusion_diagnostics.csv`;
- `r002_wide_universe_symbol_meta.csv`.

---

## 2. Cohort decomposition is more important than single-asset concentration

The strongest new diagnostic is contribution by **point-in-time eligibility year**.

### 2.1 Number of symbols first becoming eligible

| Eligibility year | Symbols first eligible |
|---|---:|
| 2020 | 25 |
| 2021 | 89 |
| 2022 | 35 |
| 2023 | 50 |
| 2024 | 92 |
| 2025 | 198 |
| 2026* | 152 |

`*` through 2026-08-31.

### 2.2 Terminal wealth contribution by eligibility cohort

| Eligibility cohort | SMA120 net contribution | Donchian 100/50 net contribution |
|---|---:|---:|
| 2020 | **+2.7454** | **+2.4431** |
| 2021 | -0.0009 | +0.0252 |
| 2022 | +0.0786 | +0.0668 |
| 2023 | +0.3463 | +0.1429 |
| 2024 | **-0.8262** | **-0.6385** |
| 2025 | **-0.3432** | **-0.0591** |
| 2026* | +0.1506 | +0.0826 |

Total terminal net portfolio P&L:

- SMA120: **+2.1506**;
- Donchian 100/50: **+2.0630**.

Therefore the 25-symbol 2020 eligibility cohort contributes approximately:

- **127.7% of total SMA120 net P&L**;
- **118.4% of total Donchian net P&L**.

All eligibility cohorts from 2021 onward combined are net negative:

- SMA120: **-0.5948**;
- Donchian 100/50: **-0.3801**.

A useful split is:

- 2021-2023 cohorts: SMA **+0.4240**, Donchian **+0.2350**;
- 2024+ cohorts: SMA **-1.0188**, Donchian **-0.6150**.

This is a stronger concentration warning than the earlier top-five-asset diagnostic. The broad-universe headline profit is not dependent on one ticker, but it is heavily dependent on the **earliest eligibility cohort / early market regime**.

---

## 3. 2024 eligibility cohort is the clearest failure cohort

The 2024 cohort contains 92 symbols and has enough subsequent history to be informative.

Baseline contribution:

### SMA120

- gross wealth contribution before disappearance and fees: **-0.7662**;
- disappearance drag: **0.0168**;
- fee drag: **0.0432**;
- net contribution: **-0.8262**;
- positive contributors: **15.2%** of the cohort.

### Donchian 100/50

- gross wealth contribution before disappearance and fees: **-0.6134**;
- disappearance drag: **0.0207**;
- fee drag: **0.0044**;
- net contribution: **-0.6385**;
- positive contributors: **10.9%** of the cohort.

Therefore this cohort is already negative **before** transaction costs and disappearance penalties. Execution stress is not the explanation.

Cross-strategy agreement is also strong:

- **72.8%** of 2024-cohort symbols are negative under both SMA120 and Donchian 100/50;
- only **6.5%** are positive under both;
- Pearson correlation of asset-level net contribution between the two signals inside this cohort is about **0.65**.

This points toward a common cohort/domain/regime problem rather than a defect unique to one signal formulation.

---

## 4. Survivor status does not explain the 2024 cohort failure

Of the 92 symbols first eligible in 2024:

- **74** are still archive survivors at 2026-08;
- **18** are historical/non-survivors.

Yet the survivor subset itself is strongly negative.

### SMA120, 2024 eligibility cohort

- survivor contribution: **-0.7206**;
- historical/non-survivor contribution: **-0.1056**.

### Donchian 100/50, 2024 eligibility cohort

- survivor contribution: **-0.5479**;
- historical/non-survivor contribution: **-0.0906**.

Thus the key later-cohort deterioration is not simply a delisting/survivorship problem.

---

## 5. Broader survivor/non-survivor result

Across all 641 ever-eligible symbols:

### SMA120

- 513 archive survivors: **+2.2335** net contribution;
- 128 historical/non-survivors: **-0.0829**.

### Donchian 100/50

- 513 archive survivors: **+2.2115**;
- 128 historical/non-survivors: **-0.1485**.

However the difference is not driven only by disappearance penalties. The 2024 survivor cohort is already deeply negative, and the full-period disappearance stress grid barely changes the qualitative result.

---

## 6. The two trend formulations fail on many of the same assets

Across all 641 ever-eligible symbols:

- asset-level net contribution Pearson correlation between SMA120 and Donchian 100/50 is about **0.88**;
- Spearman rank correlation is about **0.64**;
- approximately **34.5%** of eligible symbols are negative under both signals;
- approximately **22.3%** are positive under both.

This reinforces the earlier conclusion that both finalists express the same broad medium/long-term trend factor. Later-universe deterioration is therefore not solved by simply choosing the other finalist.

---

## 7. Breadth expansion is associated with weaker rolling returns, but causality is not established

Average eligible breadth increased materially:

- 2020: ~20;
- 2021: ~75;
- 2022: ~126;
- 2023: ~154;
- 2024: ~222;
- 2025: ~318;
- 2026 through August: ~458.

Descriptively, 365-day rolling strategy return is negatively associated with 365-day average eligible breadth:

- SMA120 Pearson correlation: approximately **-0.48**;
- Donchian Pearson correlation: approximately **-0.47**.

This is **not causal evidence** because breadth and calendar time/regime move together. It is a diagnostic reason to examine listing/eligibility cohorts, not a basis for a breadth filter.

---

## 8. Late-period weakness survives the full execution stress grid

Across the 16 pre-specified post-2023 stress scenarios:

### SMA120

- positive CAGR in only **7 / 16** scenarios;
- best post-2023 CAGR: about **+2.44%**;
- worst: about **-6.29%**;
- Max DD remains roughly **-60% to -66%**.

### Donchian 100/50

- positive CAGR in **0 / 16** scenarios;
- best post-2023 CAGR: about **-0.90%**;
- worst: about **-3.83%**;
- Max DD remains roughly **-51% to -55%**.

Therefore the late-period problem is not an artefact of a single fee or disappearance assumption.

---

## 9. Domain caveat: TradFi contamination is real, but cannot explain the 2024 cohort failure

The archive-defined universe visibly expands into traditional-finance-linked contracts in 2026. Binance officially announced the launch of TradFi perpetual contracts in January 2026, with XAUUSDT (gold) available from 2026-01-05 and XAGUSDT from 2026-01-07.

This confirms that the full archive-defined universe is not a pure crypto-only domain.

However the largest negative eligibility cohort is **2024**, and the 2025 cohort is also negative. Therefore 2026 TradFi expansion cannot by itself explain the broad-universe failure.

A crypto-only retest must not be introduced as a rescue filter without objective metadata and a frozen classification protocol.

---

## 10. Newly identified PTI availability risk

A more serious implementation/domain issue emerged during the audit.

In `r002_wide_universe_symbol_meta.csv`:

- `XAUUSDT` archive first date = **2025-12-11**;
- archive-based 200-bar eligibility date = **2026-06-28**.

Binance's official TradFi launch announcement states that XAUUSDT became available to eligible markets on **2026-01-05**.

Therefore the public daily archive can contain bars **before actual contract availability**.

Implication:

> `archive first bar` is not guaranteed to equal `tradable onboard date`.

The wide-universe engine used observed archive bars to start the 200-bar eligibility clock. For any symbol with pre-onboard/backfilled bars, eligibility may be earlier than a strict tradability-based PTI clock.

This is a potential **Case C implementation/availability bug** under roadmap v2.1. It must be quantified before treating the current wide-universe result as final.

No strategy result should be rerun yet.

---

## 11. Next required action

Run a metadata-only **availability/domain audit** against official Binance contract metadata.

For every currently resolvable USD-M symbol, collect at minimum:

- `symbol`;
- `onboardDate`;
- `status`;
- `contractType`;
- `underlyingType`;
- `underlyingSubType`;
- archive first date;
- number of archive bars before onboard date;
- archive-based 200-bar eligibility date;
- onboard-adjusted 200-observed-bar eligibility date.

The audit must **not** calculate strategy P&L.

Decision gate:

- if availability mismatches are rare and immaterial, keep the REDESIGN conclusion and continue domain audit;
- if many eligible symbols entered materially before their official onboard-based warmup, version and fix the PTI engine, document the bug, then rerun the exact frozen protocol with no parameter changes;
- independently, use `underlyingType` / official Binance metadata to quantify TradFi vs crypto domain composition without manual ticker classification.
