# R002 — Cross-Asset SMA120 Validation v0.1

**Rule:** frozen long/cash SMA120, identical across assets, no per-asset tuning.  
**Panel:** BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, LTCUSDT, ADAUSDT, BNBUSDT (Bybit linear USDT perpetual daily data).  
**Execution assumption:** signal from fully closed daily bar; applied to next close-to-close return; 10 bps per exposure change.  
**Important limitation:** current-large-liquid panel has survivorship bias. This is a cross-market robustness test, not a historical point-in-time universe test.

## Data quality

14,146 rows across 7 symbols. Each symbol is internally daily-continuous over its available Bybit history, with no duplicate dates, missing OHLC values, or non-positive OHLC prices.

Available starts differ by listing history:
- BTCUSDT: 2020-03-25
- LTCUSDT: 2020-10-21
- ETHUSDT: 2021-03-15
- ADAUSDT: 2021-03-18
- XRPUSDT: 2021-05-13
- BNBUSDT: 2021-06-29
- SOLUSDT: 2021-10-15

## Per-asset maximum available-history result

| Asset | SMA120 CAGR | SMA120 Max DD | Buy & Hold CAGR | Buy & Hold Max DD | Interpretation |
|---|---:|---:|---:|---:|---|
| BTC | 64.2% | -32.3% | 41.1% | -76.7% | strong pass |
| ETH | 16.4% | -58.9% | 4.0% | -79.4% | positive |
| SOL | 17.5% | -64.2% | 1.5% | -93.0% | positive |
| ADA | 5.7% | -69.2% | -28.4% | -95.2% | strong relative improvement |
| BNB | 10.8% | -62.0% | 9.7% | -69.9% | small positive |
| LTC | -28.5% | -92.1% | -23.3% | -89.5% | fail |
| XRP | -17.4% | -88.7% | 5.4% | -76.1% | fail |

The same frozen SMA120 rule improves CAGR and drawdown simultaneously on 5 of 7 assets on their maximum available histories. It clearly fails on LTC and XRP.

BTCUSDT is an important control: its result is close to the earlier BTCUSD inverse-perpetual test, supporting that the BTC finding is not an artifact of one Bybit contract type.

## Common-period comparison

To remove unequal-history advantage, all 7 assets are compared over the shared SMA-valid period 2022-02-12 through 2026-09-08.

| Asset | SMA120 CAGR | SMA120 Max DD | Buy & Hold CAGR | Buy & Hold Max DD |
|---|---:|---:|---:|---:|
| BTC | 33.0% | -27.0% | 14.4% | -66.8% |
| ETH | 9.3% | -49.9% | -3.5% | -71.8% |
| SOL | 17.5% | -64.2% | 1.5% | -93.0% |
| ADA | 4.0% | -69.2% | -29.5% | -88.3% |
| BNB | 10.2% | -50.9% | 14.8% | -58.2% |
| LTC | -27.4% | -80.8% | -16.8% | -70.2% |
| XRP | -14.9% | -86.4% | 14.6% | -72.1% |

Again, BTC/ETH/SOL/ADA show useful trend behavior; BNB mainly improves risk; LTC and XRP remain poor.

## Equal-weight portfolio diagnostic

A conservative fixed-sleeve portfolio was tested: 1/7 capital allocated to each asset sleeve; each sleeve is invested only when that asset is above its SMA120, otherwise its capital is cash. Inactive sleeves are not dynamically reallocated to active assets.

Common period 2022-02-12 through 2026-09-08:

- Equal-weight buy & hold: CAGR **~6.7%**, Max DD **~−68.2%**, annualized vol ~62.8%.
- Equal-weight SMA120 sleeves: CAGR **~8.6%**, Max DD **~−47.2%**, annualized vol ~34.0%.

So the cross-asset portfolio improves both return and risk over the common period, despite two failing assets.

## Cost stress — equal-weight SMA120 portfolio

- 5 bps per exposure change: CAGR ~9.5%, Max DD ~−46.4%
- 10 bps: CAGR ~8.6%, Max DD ~−47.2%
- 25 bps: CAGR ~6.1%, Max DD ~−49.5%
- 50 bps: CAGR ~2.0%, Max DD ~−53.0%

The portfolio remains positive under severe cost assumptions, but much of the return advantage disappears by 25–50 bps because several altcoins whipsaw frequently.

## Late-period diagnostic (2023-01-01 through 2026-09-08)

On the late period, equal-weight SMA120 sleeves return roughly **22.8% CAGR** with Max DD ~**−34.4%**, versus equal-weight buy & hold at roughly **41.0% CAGR** with Max DD ~**−66.1%**.

Interpretation: trend following sacrifices substantial upside in a strong later bull regime, but still cuts portfolio drawdown roughly in half. This is consistent with the intended role of trend following: avoid long bear regimes rather than maximize participation in every bull market.

## Research verdict

**Cross-asset transfer: PARTIAL PASS / ROBUSTNESS CONFIRMED, not universal.**

What is strengthened:
- the BTC SMA120 effect transfers meaningfully to ETH, SOL and ADA;
- BNB shows risk reduction with little return improvement;
- the same frozen parameter works across several unrelated major crypto assets;
- an equal-weight portfolio of frozen SMA120 sleeves improves the return/risk profile over the shared period.

What prevents a stronger PASS:
- LTC and XRP fail materially;
- late-period buy & hold has much higher CAGR, although with much deeper drawdown;
- current-major-asset selection creates survivorship bias;
- altcoin turnover makes results more sensitive to transaction costs.

## Next justified step

Do not tune SMA per asset. The next useful test is a historically defined point-in-time universe (including delisted/dead assets where feasible) plus a simple liquidity eligibility rule chosen before results are seen. In parallel, the already-frozen BTC SMA120 forward clock should continue unchanged.
