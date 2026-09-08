# R002 — BTC Trend Following Screen v0.1

**Purpose:** establish a simple, falsifiable control strategy to compare with R001's options complexity.

**Status:** first coarse screen, not final validation.

## Data

- Bybit `BTCUSD` inverse perpetual daily klines.
- 2019-09-01 through 2026-09-08.
- Screening starts from a common date of 2020-05-11 so every candidate has enough warm-up history.
- Cash return assumed 0 in this first pass.

## Bias / execution discipline

Signals are computed using a day's completed close and then shifted one day before being applied to returns. Therefore the strategy never uses a close to trade the same close.

A fixed 10 bps cost is charged for each absolute exposure change (`0->1` or `1->0`). This is intentionally simple and conservative enough for a first screen, but not a final live execution model.

## Pre-specified coarse family

No parameter optimization was run. Only four broad and interpretable rules were tested:

1. `SMA100`: long BTC when prior close > prior 100-day SMA.
2. `SMA200`: long BTC when prior close > prior 200-day SMA.
3. `MOM252`: long BTC when prior 252-day absolute momentum > 0.
4. `SMA50 > SMA200`: long BTC when prior 50-day SMA > prior 200-day SMA.

## Full common period: 2020-05-11 through 2026-09-08

| Rule | CAGR | Max DD | Annualized vol | Exposure | Exposure changes |
|---|---:|---:|---:|---:|---:|
| Buy & hold | ~41.5% | ~-76.7% | ~57.4% | 100% | n/a |
| SMA100 | **~49.7%** | **~-38.5%** | ~42.1% | ~57.1% | 90 |
| MOM252 | **~51.9%** | ~-53.1% | ~48.7% | ~71.2% | 34 |
| SMA200 | ~40.5% | ~-64.1% | ~43.4% | ~59.2% | 52 |
| SMA50 > SMA200 | ~34.3% | ~-56.8% | ~44.9% | ~58.7% | 12 |

The two strongest coarse rules are `SMA100` and `MOM252`. Both exceed buy-and-hold CAGR over the common period while materially reducing drawdown, although their risk profiles differ.

## Chronological robustness split

### Early: 2020-05-11 through 2022-12-31

| Rule | CAGR | Max DD |
|---|---:|---:|
| Buy & hold | ~27.4% | ~-76.7% |
| SMA100 | ~68.3% | ~-38.5% |
| MOM252 | ~73.3% | ~-53.1% |
| SMA200 | ~43.9% | ~-64.1% |
| SMA50 > SMA200 | ~60.6% | ~-52.9% |

Trend following was extremely valuable in the early sample, largely because it avoided substantial portions of the 2022 bear market.

### Late: 2023-01-01 through 2026-09-08

| Rule | CAGR | Max DD |
|---|---:|---:|
| Buy & hold | **~52.6%** | ~-53.1% |
| MOM252 | ~38.2% | **~-35.4%** |
| SMA200 | ~38.2% | ~-31.8% |
| SMA100 | ~37.7% | ~-36.8% |
| SMA50 > SMA200 | ~18.2% | ~-37.4% |

All trend rules lag buy-and-hold CAGR in the later sample, but still reduce drawdown materially. This is not a failure in the same sense as R001's static put sleeve: the strategy is explicitly designed to trade upside participation for bear-market protection.

## Interpretation

R002 passes the first plausibility screen better than R001's static options overlay:

- the effect is large enough to survive coarse rules rather than one tuned threshold;
- several independent trend definitions show the same broad behavior;
- the mechanism is economically interpretable: remain exposed in persistent uptrends and move to cash during sustained downtrends;
- transaction count is low to moderate;
- late-period underperformance is expected in a strong bull regime and is paired with substantially smaller drawdowns.

However, this is not yet a production PASS.

## Main risks / next tests

1. **Parameter robustness:** test broad neighborhoods only, e.g. SMA 80/100/120 and momentum 9/12/15 months. The goal is plateau detection, not best-point selection.
2. **Cost stress:** 5, 10, 25, and 50 bps per exposure change.
3. **Execution timing:** next-day open rather than close-to-close proxy.
4. **Cash/carry sleeve:** add realistic cash/carry assumption separately rather than silently embedding yield.
5. **Walk-forward / frozen-rule OOS:** select a simple family using early data, freeze it, then evaluate late data without re-tuning.
6. **Whipsaw diagnostics:** quantify losses around short-lived crossovers and sideways regimes.
7. **Benchmark against BTC buy-and-hold and fixed-risk BTC exposure**, not only CAGR.

## Current verdict

**R002 BTC Trend Following: PROMISING CONTROL CANDIDATE / ADVANCE TO ROBUSTNESS.**

The strongest next step is not to optimize the apparent winner. It is to test whether `SMA100` and `MOM252` sit inside broad robust plateaus and whether their drawdown advantage survives stricter execution and cost assumptions.

R001 remains open only for a crisis-window diagnostic with denser option data; static and IV/RV-timed put purchasing have not validated as a default overlay.
