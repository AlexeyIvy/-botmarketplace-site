# R002 — Point-in-Time Portfolio Diagnostic v0.1

**Strategy:** frozen SMA120 trend following  
**Purpose:** test the signal inside a historical portfolio that does not know future delistings when forming positions.  
**Status:** diagnostic pass, not final production validation.

## Why this test matters

Previous cross-asset and survivorship tests showed that SMA120 works on many current and historical/delisted assets. The next question is harder: what happens when assets enter only after enough real history exists and disappear when trading stops, without using future delisting knowledge in the signal?

This test is therefore more realistic than evaluating each asset separately.

## Dataset

Input: `r002_binance_historical_subset_daily.csv`.

- Fixed research subset chosen before this test: 22 historical/non-survivor candidates + 7 survivor controls.
- 37,821 raw daily rows.
- Dead post-delisting archive tails are removed by cutting each symbol at its last positive-volume day.
- Symbols with fewer than 120 genuinely traded days after cleaning are excluded.
- 27 symbols remain usable; BTCST and COCOS are excluded because their apparent long histories were mostly dead archive tails.

Important limitation: this is point-in-time **inside a pre-specified subset**, not yet a full-market historical universe backtest. The subset itself was constructed retrospectively for survivorship diagnostics, so this test materially reduces but does not completely eliminate universe-selection bias.

## Frozen portfolio rule

For each day:

1. A symbol becomes eligible only after 120 observed daily closes.
2. At close `t`, signal is `close > SMA120`.
3. That signal is applied to the next close-to-close return, eliminating same-close look-ahead.
4. Each currently eligible symbol gets an equal capital sleeve `1/N`.
5. If its signal is ON, the sleeve holds the asset; otherwise that sleeve remains cash.
6. Cash return is 0 in this diagnostic.
7. Transaction cost is charged on absolute changes in target portfolio weights.
8. If an eligible symbol disappears on the following day, no future price is fabricated. Instead the study applies explicit delisting-penalty stress to any long sleeve.

Comparator: same point-in-time eligible universe, equal-weight buy-and-hold, same transaction-cost framework.

## Primary result

Common portfolio period: approximately **2020-04-30 through 2026-08-31**.

At **10 bps cost per absolute target-weight change** and **0% extra delisting penalty**:

- SMA120 CAGR: **~52.25%**
- SMA120 Max DD: **~−51.21%**
- SMA120 annualized vol: **~47.18%**
- SMA120 ending multiple: **~14.34x**

Point-in-time equal-weight buy-and-hold:

- CAGR: **~37.83%**
- Max DD: **~−86.85%**
- annualized vol: **~76.73%**
- ending multiple: **~7.63x**

The result is economically large: the frozen SMA120 portfolio both grows faster and suffers much less severe drawdown than the same eligible-universe buy-and-hold comparator.

## Delisting stress

Because a historical archive can stop without providing a realistic executable next-day exit price, this study deliberately stresses any long exposure present when a symbol disappears.

At 10 bps transaction cost:

| Extra loss applied to long sleeve at disappearance | SMA120 CAGR | SMA120 Max DD | Buy&Hold CAGR | Buy&Hold Max DD |
|---:|---:|---:|---:|---:|
| 0% | ~52.25% | ~−51.21% | ~37.83% | ~−86.85% |
| 10% | ~51.43% | ~−51.47% | ~33.60% | ~−88.00% |
| 25% | ~50.19% | ~−51.85% | ~27.40% | ~−89.58% |
| 50% | ~48.11% | ~−52.49% | ~17.42% | ~−91.83% |
| 100% | ~43.89% | ~−53.78% | ~−1.21% | ~−97.09% |

Even the deliberately extreme 100% residual-sleeve loss assumption does not destroy the SMA120 result. This is a strong robustness signal and directly addresses a major weakness in delisted-token backtests.

## Transaction-cost stress

Using a 25% delisting penalty:

| Cost per absolute weight change | SMA120 CAGR | SMA120 Max DD |
|---:|---:|---:|
| 5 bps | ~51.25% | ~−51.22% |
| 10 bps | ~50.19% | ~−51.85% |
| 25 bps | ~47.07% | ~−53.70% |
| 50 bps | ~42.01% | ~−56.62% |

The strategy remains materially positive even under 50 bps cost stress.

## Interpretation

This is one of the strongest R002 tests so far.

The key finding is not the exact CAGR number. The important result is that the frozen trend rule continues to work when:

- historical non-survivors are included;
- assets enter only after 120 real observations;
- no future delisting information is used for the signal;
- dead archive tails are removed;
- disappearing positions are explicitly penalized;
- costs are stressed heavily.

This makes it much less likely that the earlier BTC/cross-asset results were simply an artefact of selecting today's surviving winners.

## What this test still does NOT prove

- The 29-symbol subset is not the entire Binance historical universe.
- Equal-sleeve daily target weights are a research portfolio construction rule, not yet a final execution specification.
- Funding is not included.
- Cash/stablecoin yield is not included.
- Real delisting settlement mechanics differ by venue and event.
- The strategy still needs true forward/paper evidence after freeze.

## Verdict

**POINT-IN-TIME SUBSET PORTFOLIO: PASS WITH CAVEATS.**

The frozen SMA120 signal remains the primary R002 baseline.

This result strengthens the case for proceeding according to the roadmap rather than adding arbitrary technical indicators.

## Next step from the roadmap

Proceed to **R002.2 Volatility Targeting** while preserving SMA120 v1.0 unchanged as the control.

Pre-specified research family:

- SMA120 control;
- SMA120 + 15% annualized volatility target;
- SMA120 + 20% target;
- SMA120 + 25% target;
- SMA120 + 30% target;
- no leverage above 1x.

The purpose is not to predict direction better. It is to test whether position sizing can reduce drawdown and volatility without destroying the robust trend premium already observed.
