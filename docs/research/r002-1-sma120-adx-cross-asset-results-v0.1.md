# R002.1 — SMA120 + ADX14 Cross-Asset Results v0.1

**Status:** diagnostic redesign test. The frozen R002 SMA120 v1.0 remains unchanged.

## Hypothesis

ADX may reduce SMA120 whipsaw by requiring a minimum trend-strength regime before holding an asset. We test only three coarse thresholds: ADX14 > 15, > 20, > 25. The same thresholds are used for every asset; no per-asset tuning is allowed.

## Data and execution

- Bybit linear USDT perpetual daily OHLC.
- Assets: BTC, ETH, SOL, XRP, LTC, ADA, BNB.
- Common comparison period: 2022-02-12 through 2026-09-08.
- Late diagnostic: 2023-01-01 through 2026-09-08.
- Base rule: long if prior fully closed daily close > prior SMA120, else cash.
- ADX variants additionally require prior ADX14 above threshold.
- Signals shifted one day; no same-close look-ahead.
- 10 bps cost charged on each absolute exposure change.

## Common-period individual results

Approximate CAGR / max drawdown:

| Asset | SMA120 | ADX>15 | ADX>20 | ADX>25 |
|---|---:|---:|---:|---:|
| BTC | 33.0% / -27.0% | 25.5% / -29.9% | 29.1% / -30.1% | 26.1% / -24.5% |
| ETH | 9.3% / -49.9% | 5.8% / -50.8% | 8.0% / -42.5% | 13.0% / -33.2% |
| SOL | 17.4% / -64.2% | -0.9% / -69.0% | 19.7% / -60.0% | 0.5% / -67.7% |
| XRP | -14.9% / -86.4% | -12.6% / -82.7% | 1.2% / -70.5% | 18.3% / -45.1% |
| LTC | -27.4% / -80.8% | -30.2% / -86.8% | -26.5% / -79.8% | -25.4% / -76.9% |
| ADA | 4.0% / -69.2% | 9.3% / -61.3% | 6.7% / -61.0% | 2.8% / -60.8% |
| BNB | 10.2% / -50.9% | 5.2% / -49.3% | 17.7% / -36.0% | 10.1% / -35.7% |

Interpretation: there is no universal per-asset improvement. ADX helps some assets materially, especially XRP, BNB, ETH and partly ADA, but it hurts BTC and can badly hurt SOL depending on threshold. LTC remains structurally weak under all tested variants.

## Equal-weight portfolio result

Common period 2022-02-12 to 2026-09-08:

- SMA120: CAGR ~8.6%, max DD ~-47.2%.
- SMA120 + ADX>15: CAGR ~4.3%, max DD ~-47.6%.
- SMA120 + ADX>20: CAGR ~11.7%, max DD ~-30.9%.
- SMA120 + ADX>25: CAGR ~9.4%, max DD ~-24.7%.

Late period 2023-01-01 to 2026-09-08:

- SMA120: CAGR ~22.8%, max DD ~-34.4%.
- SMA120 + ADX>15: CAGR ~18.0%, max DD ~-35.8%.
- SMA120 + ADX>20: CAGR ~23.0%, max DD ~-30.9%.
- SMA120 + ADX>25: CAGR ~18.7%, max DD ~-24.7%.

## Verdict

**ADX20 is a promising portfolio-level diagnostic, not a new frozen rule.**

The strongest broad result is ADX>20: on the equal-weight portfolio it improves common-period CAGR and materially reduces drawdown, while also roughly matching SMA120 CAGR in the late period with lower drawdown. However, the improvement is not universal across assets, BTC itself gets worse, and the test was proposed after inspecting SMA120 results. Therefore this is discovery evidence, not validation.

ADX>25 reduces drawdown even more but sacrifices too much return in several assets. ADX>15 is clearly weak and should be rejected.

## Research decision

1. Keep R002 SMA120 v1.0 frozen and unchanged for forward validation.
2. Keep **R002.1 = SMA120 + ADX14>20** as a separate candidate only.
3. Do not tune ADX separately by asset.
4. Do not add a third indicator yet.
5. Next validate R002.1 on a different universe / historical point-in-time panel, and compare forward with R002 v1.0.

This preserves the simple validated baseline while allowing one controlled attempt to improve cross-asset risk efficiency.
