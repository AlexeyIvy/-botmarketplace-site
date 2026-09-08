# R001 — E004-S IV-Value Screen v0.1

**Candidate:** Antifragile Convex Barbell (R001)  
**Purpose:** test whether static long-put drag can be reduced by buying convexity only when selected-put implied volatility is relatively cheap versus its own historical distribution.  
**Status:** screening result, not final validation.

## Dataset and execution assumptions

- Free Tardis first-of-month Deribit BTC option snapshots.
- 84 monthly decision snapshots from 2019-10-01 through 2026-09-01.
- 15-delta put selection.
- Target maturity ~90 DTE; primary range 60–120 DTE; fallback 45–150 DTE.
- Buy at executable ask.
- One-month exit/mark at next first-of-month executable bid on the same contract.
- BTC directional sleeve rebalanced monthly.
- Cash return assumed 0 for this screening layer.
- Fractional option notional used for scale-neutral economics; exchange minimum-contract constraints are tracked separately and are not allowed to create artificial alpha.

## Bias control

The volatility gate uses only **prior** selected-put IV observations. No full-sample percentile is used for a decision.

Primary diagnostics:

1. `IV50`: buy only when current selected-put mark IV is at or below the median of the prior rolling 24 observations; minimum 12 prior observations required.
2. `IV33`: buy only when current IV is at or below the 33rd percentile of the prior rolling 24 observations.
3. `IV25`: buy only when current IV is at or below the 25th percentile of the prior rolling 24 observations.
4. `IV50 + spread`: IV50 plus relative bid/ask spread <= 10%.

These thresholds are intentionally coarse and economically interpretable. They are diagnostics, not optimized production thresholds.

## Primary middle-allocation result

For a 15% BTC / 85% cash baseline:

- Baseline CAGR: **~7.945%**
- Baseline max monthly-sampled drawdown: **~−15.805%**

### Annual premium budget = 0.25% NAV

| Rule | CAGR | Max DD | Net option P&L | Purchases |
|---|---:|---:|---:|---:|
| Static monthly | ~7.887% | ~−15.778% | ~−$548 | 83 |
| IV50 | ~7.937% | ~−15.751% | ~−$84 | 48 |
| IV33 | ~7.916% | ~−15.807% | ~−$260 | 35 |
| IV25 | ~7.925% | ~−15.795% | ~−$172 | 31 |
| IV50 + spread<=10% | **~7.940%** | ~−15.751% | ~−$65 | 47 |

### Annual premium budget = 0.50% NAV

| Rule | CAGR | Max DD | Net option P&L | Purchases |
|---|---:|---:|---:|---:|
| Static monthly | ~7.829% | ~−15.750% | ~−$1,095 | 83 |
| IV50 | ~7.930% | ~−15.696% | ~−$168 | 48 |
| IV33 | ~7.887% | ~−15.808% | ~−$521 | 35 |
| IV25 | ~7.905% | ~−15.784% | ~−$343 | 31 |
| IV50 + spread<=10% | **~7.935%** | ~−15.696% | ~−$131 | 47 |

### Annual premium budget = 1.00% NAV

| Rule | CAGR | Max DD | Net option P&L | Purchases |
|---|---:|---:|---:|---:|
| Static monthly | ~7.712% | ~−15.695% | ~−$2,182 | 83 |
| IV50 | ~7.915% | **~−15.586%** | ~−$337 | 48 |
| IV33 | ~7.830% | ~−15.810% | ~−$1,040 | 35 |
| IV25 | ~7.866% | ~−15.762% | ~−$686 | 31 |
| IV50 + spread<=10% | **~7.925%** | **~−15.586%** | ~−$263 | 47 |

## Interpretation

The IV-value filter materially improves the economics relative to static monthly purchasing. The strongest simple diagnostic is the broad `IV50` gate, especially when combined with a basic spread-quality filter.

However, the result still does **not** justify PASS:

- even the best filtered variants remain slightly below the exact no-option baseline in CAGR;
- the drawdown improvement remains small on first-of-month monthly sampling;
- tighter IV thresholds (33rd/25th percentile) are not consistently better, which is useful evidence against simply “optimizing for lowest IV”;
- this dataset cannot observe intramonth crisis protection, so monthly-sampled drawdown understates the potential value of puts in fast crashes;
- selected-put IV alone does not tell us whether volatility is cheap relative to subsequent realized volatility.

## Research verdict

**IV-only value filter: PROMISING REDESIGN SIGNAL, not PASS.**

Static long-put purchasing remains rejected as a default rule. Buying only when protection is relatively cheap appears substantially more economically efficient, but the remaining question is whether the option is cheap **relative to forward/realized risk**, not merely cheap versus its own past IV.

## Next justified experiment

Add free daily BTC data and compute strictly backward-looking realized-volatility features:

- RV20
- RV60
- IV/RV20
- IV/RV60
- IV − RV

Then test a small pre-specified regime family, e.g.:

- buy when IV percentile <= 50% **and** IV/RV not rich;
- compare with IV-only gate;
- preserve strict expanding/rolling historical thresholds and later freeze them for OOS.

No calls, ladders, or complex optimizer should be added before this IV/RV test is complete.
