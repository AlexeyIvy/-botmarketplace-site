# R002 — BTC Trend Following Robustness v0.2

**Candidate:** R002 BTC Trend Following  
**Purpose:** test whether the promising coarse-screen result survives nearby parameter changes, cost stress, execution-delay stress, and chronological validation.  
**Status:** robustness result; not yet final OOS validation.

## Dataset

- Bybit BTCUSD inverse perpetual daily OHLC.
- Continuous daily history from 2019-09-01 through 2026-09-08.
- No missing calendar days in the supplied dataset.
- Long/cash only; no leverage; no shorting; cash return assumed 0 at this layer.

## Bias / execution control

- Signals use the daily close only after that close exists.
- Standard screen applies the signal to the next close-to-close return (`signal.shift(1)`).
- A separate next-day-open stress applies the signal only from the following daily open (`signal.shift(2)` against open-to-open returns).
- Bybit crypto trading is 24/7, so next-day open is normally extremely close to the prior close; the two implementations should therefore be nearly identical if indexing is correct.
- Transaction costs are charged on every absolute 0↔1 exposure change.

## Common comparison period

To compare SMA and 315-day momentum on the same sample, the common window is:

- **2020-07-12 → 2026-09-08**

Chronological diagnostic split:

- Early: 2020-07-12 → 2022-12-31
- Late: 2023-01-01 → 2026-09-08

Important: the late period is **not pristine untouched OOS**, because it was already inspected in the earlier R002 screen. It is a chronological validation layer only. A genuine OOS/forward period must be frozen from a future date.

## Buy & hold benchmark

Common full period:

- CAGR: **~41.57%**
- Max drawdown: **~−76.72%**
- Calmar: **~0.54**
- Ending multiple: **~8.50x**

Early period:

- CAGR: **~26.60%**
- Max drawdown: **~−76.72%**

Late period:

- CAGR: **~52.62%**
- Max drawdown: **~−53.06%**

## SMA plateau — 10 bps per exposure change

| Rule | Full CAGR | Full Max DD | Full Calmar | Exposure changes | Early CAGR | Late CAGR | Late Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| SMA80 | ~42.56% | ~−52.66% | ~0.81 | 100 | ~49.99% | ~37.83% | ~−38.98% |
| SMA90 | ~44.58% | ~−50.51% | ~0.88 | 96 | ~49.71% | ~41.28% | ~−33.38% |
| SMA100 | ~49.96% | ~−38.53% | ~1.30 | 90 | ~70.45% | ~37.67% | ~−36.76% |
| SMA110 | **~65.64%** | **~−29.00%** | **~2.26** | 66 | **~104.06%** | ~44.08% | ~−29.00% |
| SMA120 | ~63.92% | ~−32.30% | ~1.98 | 52 | ~98.58% | **~44.20%** | ~−28.41% |
| SMA130 | ~59.60% | ~−35.01% | ~1.70 | 44 | ~91.64% | ~41.23% | **~−26.01%** |
| SMA140 | ~54.93% | ~−40.46% | ~1.36 | 44 | ~82.08% | ~39.08% | ~−27.77% |
| SMA150 | ~53.09% | ~−44.27% | ~1.20 | 42 | ~74.82% | ~40.11% | ~−26.58% |

### Interpretation

The attractive behavior is not confined to one exact moving-average length. There is a broad **~110–130 day plateau** with materially higher CAGR and dramatically lower drawdown than buy & hold on the common full period.

This is much stronger evidence than a single SMA100 result. It reduces, but does not eliminate, parameter-selection risk.

The exact winner changes by metric:

- SMA110 has the highest full-period CAGR/Calmar.
- SMA120 has the highest late-period CAGR among this plateau.
- SMA130 has the lowest late-period drawdown.

Therefore the research should **not** select SMA110 simply because it is the numerical full-sample winner. A robust representative parameter near the center of the plateau is preferable.

## Momentum plateau — 10 bps

| Rule | Full CAGR | Full Max DD | Full Calmar | Exposure changes | Early CAGR | Late CAGR |
|---|---:|---:|---:|---:|---:|---:|
| MOM189 (~9m) | ~34.56% | ~−73.36% | ~0.47 | 44 | ~40.37% | ~30.82% |
| MOM252 (~12m) | **~57.49%** | ~−53.15% | **~1.08** | 28 | **~91.41%** | **~38.24%** |
| MOM315 (~15m) | ~41.13% | ~−56.34% | ~0.73 | 18 | ~56.01% | ~32.00% |

The 12-month momentum rule is clearly stronger than the 9- and 15-month neighbors. Unlike the SMA result, this is **not a broad plateau**, so MOM252 carries more parameter-specific risk and should remain a secondary comparator rather than the primary frozen R002 rule.

## Transaction-cost stress

### SMA120

| Cost per exposure change | CAGR | Max DD | Ending multiple |
|---|---:|---:|---:|
| 5 bps | ~64.61% | ~−32.13% | ~21.52x |
| 10 bps | ~63.92% | ~−32.30% | ~20.97x |
| 25 bps | ~61.86% | ~−32.80% | ~19.40x |
| 50 bps | ~58.47% | ~−33.67% | ~17.03x |

Even at a very punitive **50 bps per switch**, SMA120 remains well above buy & hold CAGR on the common sample while keeping drawdown far lower.

For comparison, the more reactive SMA80 degrades substantially with costs because it changes exposure about twice as often. This supports preferring the slower 110–130 day region on implementation grounds as well as backtest metrics.

## Next-day-open execution stress

At 10 bps, next-day-open results are almost identical to standard close-to-close alignment:

- SMA80 CAGR ~42.60%
- SMA100 CAGR ~49.99%
- SMA120 CAGR ~63.96%
- MOM252 CAGR ~57.31%

This is expected for a 24/7 instrument where the next daily open is essentially the prior daily close, and it also serves as a useful alignment sanity check.

## Chronological robustness

The late 2023–2026 regime is a strong BTC bull period. Buy & hold therefore has a higher CAGR (~52.6%) than all long/cash trend rules. This is not a failure by itself; the economic function of trend following is to reduce exposure during prolonged bear phases, which necessarily creates opportunity cost in persistent bull markets.

The stronger test is whether protection persists without destroying compounding. The 110–130 SMA region does:

- late CAGR remains ~41–44%;
- late max drawdown is reduced from buy & hold ~−53.1% to roughly ~−26% to −29%;
- full-period CAGR is still higher than buy & hold despite materially lower exposure and much lower drawdown.

That profile is qualitatively more robust than R001's static/filtered put sleeve, whose protection required a recurring premium stream and failed to validate consistently in the later regime.

## Research verdict

**R002 BTC Trend Following: ROBUSTNESS PASS, advance to rule freeze + validation.**

The strongest evidence is the broad SMA110–130 plateau, not the exact SMA110 optimum.

### Proposed frozen research rule

For the next stage, freeze **SMA120 long/cash** as the primary R002 rule because:

1. it sits near the center of the robust 110–130 plateau;
2. it has lower turnover than SMA100/110;
3. it performs strongly in both early and late chronological slices;
4. it remains strong under 50 bps switching costs;
5. it avoids choosing the full-sample numerical winner.

Freeze specification:

- Market: BTC daily close.
- Indicator: 120-calendar-day rolling simple moving average over daily observations.
- If prior completed daily close > prior completed SMA120: target BTC exposure = 1.0.
- Else: target BTC exposure = 0.0 cash.
- No leverage; no short position.
- Trade no earlier than the next available execution point after signal formation.
- Primary research cost assumption: 10 bps per full exposure change.
- Stress assumptions: 25 and 50 bps.

## Next stage

Do **not** tune SMA120 further.

Next justified work:

1. Freeze SMA120 now in the registry/spec.
2. Add an explicit benchmark set: BTC buy & hold, cash, and SMA120.
3. Run rolling / expanding walk-forward diagnostics without parameter re-selection.
4. Add trade-level diagnostics: average holding period, whipsaw clusters, worst false exits/re-entries, time in cash, and return contribution by regime.
5. Start genuine forward/OOS tracking from the freeze date; future observations must not modify the frozen rule.
6. Only after that, evaluate whether a small cash-yield/carry sleeve improves economics without changing the signal.

No leverage, shorts, volatility targeting, multi-indicator ensemble, or optimizer should be added before the frozen simple rule survives these tests.
