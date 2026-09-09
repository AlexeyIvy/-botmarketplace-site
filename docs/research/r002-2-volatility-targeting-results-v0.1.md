# R002.2 — SMA120 + Volatility Targeting Results v0.1

**Status:** completed diagnostic branch; frozen R002 SMA120 v1.0 remains unchanged.

## Purpose

Test whether position-size scaling by recent realised volatility improves the risk/return profile of the already validated SMA120 point-in-time historical-subset portfolio.

## Pre-specified rules

- Base signal: frozen `close > SMA120`, applied next day.
- Equal point-in-time sleeve allocation among currently eligible symbols.
- Realised-volatility estimator: 20-day close-to-close standard deviation, annualised with `sqrt(365)`.
- Per-sleeve scale: `min(1, target_vol / RV20)`.
- No leverage above 1x.
- Targets tested: 15%, 20%, 25%, 30% annualised volatility.
- Transaction cost: 10 bps per absolute portfolio-weight change.
- Primary delisting stress: 25% loss on any still-long sleeve when an instrument disappears.
- Histories are trimmed after the last positive-volume day to remove dead archive tails.
- No future delisting information enters signal or position sizing.

## Primary results

Period: 2020-04-30 through 2026-08-31.

| Variant | CAGR | Max DD | Ann. vol | Calmar | Avg gross exposure | Worst calendar year | Turnover |
|---|---:|---:|---:|---:|---:|---:|---:|
| SMA120 | 50.19% | -51.85% | 47.24% | 0.97 | 46.14% | -27.64% | 88.74 |
| VT 15% | 9.52% | -9.33% | 7.95% | 1.02 | 9.84% | -5.15% | 30.23 |
| VT 20% | 12.75% | -12.29% | 10.59% | 1.04 | 13.11% | -6.83% | 40.13 |
| VT 25% | 15.94% | -15.17% | 13.21% | 1.05 | 16.33% | -8.48% | 49.54 |
| VT 30% | 18.98% | -17.85% | 15.77% | 1.06 | 19.44% | -10.12% | 57.89 |

For reference, with zero delisting penalty the same ordering holds. Calmar improves modestly as target volatility rises from 15% to 30%, but absolute return remains far below unscaled SMA120 because crypto RV is usually much higher than these target levels, so the strategy spends most of its time heavily under-invested.

## Late-period diagnostic

For 2023-01-01 onward, using the same 25% delisting stress:

| Variant | CAGR | Max DD | Ann. vol | Calmar | Avg gross exposure |
|---|---:|---:|---:|---:|---:|
| SMA120 | 21.70% | -40.74% | 37.20% | 0.53 | 45.08% |
| VT 15% | 6.75% | -9.33% | 7.78% | 0.72 | 11.08% |
| VT 20% | 8.99% | -12.29% | 10.36% | 0.73 | 14.76% |
| VT 25% | 11.18% | -15.17% | 12.91% | 0.74 | 18.39% |
| VT 30% | 13.28% | -17.85% | 15.39% | 0.74 | 21.83% |

The qualitative result is stable: volatility targeting materially reduces drawdown and realised volatility, but these low target levels sacrifice too much participation in crypto trends.

## Interpretation

This is **not a failure of risk scaling as a concept**. It is a failure of the pre-specified 15–30% per-asset target range as a candidate replacement for the frozen SMA120 sizing rule.

The diagnostic teaches us something useful:

1. Crypto realised volatility is high enough that 15–30% per-asset targets shrink positions aggressively.
2. Risk-adjusted efficiency (Calmar) improves modestly, but absolute CAGR collapses.
3. The 30% target is the least restrictive and best of the tested targets, suggesting the economically relevant region, if any, is likely above 30% or should be implemented at the **portfolio level** rather than per asset.
4. We should not tune a dense target grid on this same sample. A redesigned test must be small and justified before looking at results.

## Verdict

**R002.2 per-asset RV20 targeting at 15/20/25/30%: REDESIGN, not PASS.**

Frozen SMA120 remains the primary validated candidate.

## Recommended next step under the roadmap

Do not add RSI/MACD or stack more entry indicators. The next useful branch is one of:

- a small, pre-declared portfolio-level volatility cap/target diagnostic; or
- proceed to the already-planned independent breakout-trend test to validate the broader trend-following hypothesis using a different signal family.

Given the strong evidence already accumulated for SMA120, the preferred next research step is the **independent breakout trend test**, while SMA120 continues frozen forward validation.
