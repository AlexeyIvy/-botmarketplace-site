# R002 Candidate Tournament — v1.0

Date: 2026-09-09

## Purpose

Compare the four already-defined R002 branches under one common point-in-time protocol before doing any further indicator search or parameter tuning.

Candidates:

1. **SMA120** — frozen baseline.
2. **SMA120 + ADX14 > 20** — R002.1 trend-strength filter.
3. **Donchian 100/50** — independent breakout trend-following challenger.
4. **SMA120 + RV20 volatility target 30%** — R002.2 risk-scaling reference, no leverage.

No parameter was re-optimised for this tournament.

## Common protocol

- Historical subset dataset previously collected from Binance USD-M monthly 1d archives.
- Dead archive tails after the last positive-volume day are removed.
- Common eligibility warmup: **200 observed daily rows** for every candidate.
- Signal uses information available at day `t`; portfolio return is taken on day `t+1`.
- Equal capital sleeve for each currently eligible asset; inactive sleeves remain cash.
- Cash return: 0.
- Baseline transaction cost: **10 bps per absolute portfolio-weight change**.
- Baseline disappearance/delisting penalty: **25% of any long sleeve that disappears on the next day**.
- No leverage.
- Common evaluation period: **2020-07-19 through 2026-08-31**.
- Late-period robustness: **2023-01-01 through 2026-08-31**.

27 assets survive the common 200-day cleaning/warmup rule.

## Full-period results

| Candidate | CAGR | Max DD | Ann. vol | Calmar | Sharpe | Worst year | Turnover | Avg exposure | Ending multiple |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SMA120 | 46.86% | -54.53% | 48.95% | 0.86 | 1.04 | -28.55% | 86.94 | 46.47% | 10.49x |
| SMA120 + ADX20 | 35.80% | -40.85% | 39.80% | 0.88 | 0.97 | -22.54% | 89.20 | 32.54% | 6.50x |
| **Donchian 100/50** | **46.77%** | **-39.78%** | 43.96% | **1.18** | 1.10 | **-16.04%** | **14.73** | 40.21% | **10.45x** |
| SMA120 + VT30 | 20.84% | **-18.56%** | **16.46%** | 1.12 | **1.23** | **-10.40%** | 57.18 | 19.63% | 3.18x |

## Late-period results (from 2023-01-01)

| Candidate | CAGR | Max DD | Ann. vol | Calmar | Sharpe | Worst year | Turnover | Avg exposure | Ending multiple |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SMA120 | **21.02%** | -40.91% | 37.46% | 0.51 | 0.70 | -16.43% | 52.74 | 45.40% | **2.01x** |
| SMA120 + ADX20 | 15.69% | -34.81% | 29.50% | 0.45 | 0.64 | -5.79% | 52.83 | 31.15% | 1.71x |
| Donchian 100/50 | 19.19% | -36.99% | 34.19% | 0.52 | 0.68 | -11.81% | **7.91** | 39.80% | 1.90x |
| SMA120 + VT30 | 13.35% | **-18.56%** | **15.56%** | **0.72** | **0.88** | **-1.70%** | 39.10 | 22.04% | 1.58x |

## Cost stress

CAGR by transaction cost, keeping the 25% disappearance penalty:

| Candidate | 5 bps | 10 bps | 25 bps | 50 bps |
|---|---:|---:|---:|---:|
| SMA120 | 47.91% | 46.86% | 43.76% | 38.75% |
| SMA120 + ADX20 | 36.79% | 35.80% | 32.86% | 28.11% |
| **Donchian 100/50** | **46.95%** | **46.77%** | **46.24%** | **45.37%** |
| SMA120 + VT30 | 21.41% | 20.84% | 19.16% | 16.41% |

Donchian is the clear turnover/cost-robustness winner. Its full-period turnover is only ~14.7 versus ~86.9 for SMA120 and ~89.2 for SMA120+ADX20.

## Disappearance/delisting penalty stress

CAGR at 10 bps transaction cost:

| Candidate | 0% penalty | 25% | 50% | 100% |
|---|---:|---:|---:|---:|
| SMA120 | 49.04% | 46.86% | 44.66% | 40.18% |
| SMA120 + ADX20 | 37.80% | 35.80% | 33.77% | 29.66% |
| **Donchian 100/50** | **48.62%** | **46.77%** | **44.90%** | **41.06%** |
| SMA120 + VT30 | 21.38% | 20.84% | 20.31% | 19.23% |

All branches survive this stress qualitatively. Donchian retains slightly more CAGR than SMA120 under the harshest penalty because it is less often exposed when a symbol disappears.

## Interpretation

### 1. SMA120 remains validated, but it no longer stands alone

The frozen baseline still has the best late-period CAGR and nearly the best full-period CAGR. Nothing here invalidates it. Its main weakness versus Donchian is turnover and drawdown.

### 2. Donchian 100/50 is the strongest challenger

Donchian produces essentially the same full-period CAGR as SMA120 (46.77% vs 46.86%) while improving Max DD from -54.53% to -39.78%, improving worst year from -28.55% to -16.04%, and reducing turnover by roughly 83%.

Its advantage strengthens as trading costs rise. This is economically important and is not just a cosmetic backtest improvement.

The late period is also acceptable: 19.19% CAGR versus 21.02% for SMA120, with modestly lower drawdown.

### 3. ADX20 does not win the tournament

ADX20 cuts risk but gives up too much return while leaving turnover slightly higher than the SMA120 baseline. Donchian dominates it on the main combination of CAGR, drawdown, worst year, and turnover.

**Decision: do not promote SMA120+ADX20. Keep it as a documented research branch, not a production candidate.**

### 4. VT30 is useful as a risk-control reference, not as the core strategy

VT30 has by far the lowest drawdown and volatility, and the highest late-period risk-adjusted metrics, but its absolute CAGR is much lower. This confirms that volatility scaling can control risk, but the tested 30% per-asset target is too restrictive to replace the core trend strategy.

**Decision: keep VT30 as a risk-control benchmark. Do not promote it as the core alpha strategy.**

## Tournament verdict

### Core candidate A — SMA120

**Status: KEEP FROZEN / CONTINUE FORWARD VALIDATION.**

Reason: longest validation chain, robust BTC and cross-asset history, survivorship tests, point-in-time portfolio pass, and strongest late-period CAGR in this tournament.

### Core candidate B — Donchian 100/50

**Status: PROMOTE TO CHALLENGER / FREEZE PARAMETERS FOR FORWARD TEST.**

Reason: independent trend definition, almost identical historical CAGR to SMA120, materially lower drawdown and turnover, and excellent cost robustness.

The tournament does **not** justify replacing SMA120 with Donchian yet because Donchian has a shorter validation history and has just been selected from a small pre-specified breakout family. It should now be frozen and evaluated forward alongside SMA120 rather than further tuned.

## Next actions

1. Freeze **Donchian 100/50** exactly as tested. No lookback changes without creating a new strategy version and resetting its forward clock.
2. Add Donchian to the same paper/forward tracking process used for SMA120.
3. Stop searching for additional technical indicators for now. The marginal value is lower than the risk of overfitting.
4. Next research priority: execution realism and portfolio implementation assumptions for the two finalists, especially fees, slippage, funding/perpetual-vs-spot differences, asset eligibility, and handling of listings/delistings.
5. Preserve VT30 only as a risk-budget/reference branch and ADX20 as a documented rejected challenger.
6. Do not modify frozen SMA120 v1.0 based on this tournament.

## Overall conclusion

The strongest result of the tournament is not that one exact parameter set won. It is that **two materially different medium/long-term trend definitions — SMA120 and Donchian 100/50 — independently produce similar return profiles on the same point-in-time historical subset.** That strengthens the underlying trend-following thesis and reduces dependence on a single indicator formulation.

The research program should now move away from indicator proliferation and toward forward validation and execution realism.
