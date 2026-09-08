# R001 — E004-S IV/RV Screen Results v0.2

**Candidate:** Antifragile Convex Barbell (R001)  
**Status:** screening result, not final validation.  
**Purpose:** test whether long-put economics improve when implied volatility is cheap relative to backward-looking BTC realised volatility.

## Data validation

Daily BTC source: free Bybit V5 `BTCUSD` inverse perpetual daily klines.

- 2,565 daily rows.
- Continuous coverage from 2019-09-01 through 2026-09-08.
- No missing calendar days.
- No duplicate dates.
- No missing OHLC values.
- No non-positive closes.

Options source: free Tardis first-of-month Deribit BTC option snapshots.

- 84 monthly decision snapshots from 2019-10-01 through 2026-09-01.
- 54,329 option rows.
- 15-delta put selection, target ~90 DTE.
- Primary DTE 60–120; fallback 45–150.
- 80 primary selections, 4 fallback selections.

## Critical no-look-ahead correction

Monthly option decisions occur at 12:00 UTC on the first day of each month. The Bybit daily candle for that same UTC date is still incomplete at decision time and therefore MUST NOT be used.

RV20 and RV60 in this experiment end on the **previous UTC calendar day**. This is a hard causal rule.

Annualisation: `rolling std(log daily returns) * sqrt(365)`.

## Features

For each selected put:

- `RV20`
- `RV60`
- `IV/RV20`
- `IV/RV60`
- `IV - RV20`
- `IV - RV60`

Observed selected-put IV/RV diagnostics over the full monthly sample:

- median IV/RV20: ~1.26
- median IV/RV60: ~1.15
- mean IV/RV60: ~1.18

This confirms that the selected OTM put IV is usually richer than recent realised spot volatility, as expected from skew / insurance premium.

## Execution and portfolio assumptions

Same as E004-S v0.1:

- 15% BTC / 85% cash baseline.
- BTC sleeve rebalanced monthly.
- Cash return = 0 for this screening layer.
- Buy put at ask.
- One-month exit/mark at next first-of-month bid on the same contract.
- Fractional option size for scale-neutral economics.
- Primary annual premium budget for comparison: 0.50% NAV/year.
- Spread-quality gate: relative bid/ask spread <= 10%.

Baseline full-sample CAGR is ~7.94%, max monthly-sampled drawdown ~-15.81%.

## Pre-specified diagnostic rule family

No large threshold search was performed. The small family was chosen for economic interpretability:

1. `IV50 + spread`: current selected-put IV <= rolling median of prior 24 selected-put IV observations, minimum 12 prior observations.
2. `Ratio50 + spread`: current IV/RV60 <= rolling median of prior 24 IV/RV60 observations.
3. `IV50 + Ratio50 + spread`.
4. `IV50 + IV/RV60 <= 1.25 + spread`.
5. `IV50 + IV/RV20 <= 1.25 + spread`.

Rolling medians use prior observations only.

## Full-sample diagnostics — 0.50% annual premium budget

| Rule | CAGR | Max DD | Net option P&L | Purchases |
|---|---:|---:|---:|---:|
| No-option baseline | ~7.942% | ~-15.805% | $0 | 0 |
| IV50 + spread | ~7.933% | ~-15.696% | ~-$131 | 47 |
| Ratio50 + spread | ~7.904% | ~-15.700% | ~-$464 | 33 |
| IV50 + Ratio50 + spread | **~7.954%** | ~-15.671% | **~+$29** | 22 |
| IV50 + IV/RV60<=1.25 + spread | ~7.937% | ~-15.691% | ~-$130 | 28 |
| IV50 + IV/RV20<=1.25 + spread | **~7.955%** | ~-15.696% | **~+$72** | 21 |

At first glance, the combined IV/RV filters appear to cross the no-option baseline by a small amount. That is not sufficient for PASS.

## Chronological robustness split

To test whether the apparent full-sample improvement is stable rather than concentrated in the early market, results were split chronologically:

- Early regime: 2019-10 through 2022-12.
- Later regime / holdout diagnostic: 2023-01 through 2026-09.

This is a diagnostic holdout, not a pristine untouched OOS set, because the rule family was inspected after the full-sample research process. It is nevertheless useful for falsification.

### Early regime — 0.50% annual budget

No-option baseline CAGR: ~7.61%.

- IV50 + spread: ~7.71%, net option P&L ~+$400.
- IV50 + Ratio50 + spread: ~7.73%, net option P&L ~+$474.
- IV50 + IV/RV60<=1.25 + spread: ~7.72%, net option P&L ~+$440.
- IV50 + IV/RV20<=1.25 + spread: ~7.71%, net option P&L ~+$399.

The value filters helped in the early sample.

### 2023-01 through 2026-09 diagnostic holdout

No-option baseline CAGR: **~8.58%**.

- IV50 + spread: ~8.48%, net option P&L ~-$399, 35 purchases.
- Ratio50 + spread: ~8.45%, net option P&L ~-$564, 20 purchases.
- IV50 + Ratio50 + spread: ~8.50%, net option P&L ~-$329, 14 purchases.
- IV50 + IV/RV60<=1.25 + spread: ~8.48%, net option P&L ~-$430, 19 purchases.
- IV50 + IV/RV20<=1.25 + spread: ~8.51%, net option P&L ~-$260, 15 purchases.

**Every tested IV/RV overlay underperformed the exact no-option baseline in the later period.**

The `IV50 + Ratio50 + spread` rule was positive in 2021–2022 but then produced negative incremental results in each calendar segment 2023, 2024, 2025, and 2026 YTD.

## Interpretation

The IV/RV idea is economically sensible, and the early sample shows that relative-value timing can substantially reduce or even temporarily reverse static-put carry drag. However, the effect does not survive the later-period diagnostic.

This is stronger evidence than the previous IV-only result:

- static puts remain rejected;
- IV-only timing reduces drag but does not establish value;
- IV/RV timing can look profitable in one regime and fail in the later regime;
- therefore the apparent full-sample positive result is not robust enough to justify production or added complexity.

The likely explanations include one or more of:

1. structural evolution / maturation of BTC options markets;
2. persistent downside-skew insurance premium not captured by spot RV alone;
3. monthly first-of-month sampling misses intramonth convexity value;
4. backward-looking RV is an incomplete proxy for forward crash risk;
5. small-sample tail-event dependence makes apparent edge unstable.

## Research verdict

**E004-S IV/RV timing: FAIL TO VALIDATE / REDESIGN.**

Do not promote the put sleeve to production. Do not optimize additional IV/RV thresholds on this same sample.

## Next justified step

The next experiment should not be a larger parameter grid. Two paths are justified:

### Path A — falsify/quantify the missing intramonth convexity hypothesis

Seek free denser option history around a small set of crisis windows and measure whether monthly snapshot testing materially understates put value. This is a data-quality question, not a strategy optimization question.

Priority windows:

- March 2020 COVID crash,
- May 2021 liquidation wave,
- June 2022 deleveraging,
- November 2022 FTX,
- one or two later high-volatility windows.

### Path B — keep R001 as a research concept but advance the simpler control strategy R002

R002 BTC Trend Following is a better control because it requires only spot/perpetual data, can be validated with dense free history, and provides a benchmark for whether complexity in R001 is earning its keep.

Recommended sequencing: perform a small crisis-window data check for Path A, then advance R002 in parallel. Do not add calls, ladders, dynamic optimizers, or production integration before R001 demonstrates a robust economic advantage.

## Reproducibility

Reference implementation: `research/r001/iv_rv_screen.py`.
