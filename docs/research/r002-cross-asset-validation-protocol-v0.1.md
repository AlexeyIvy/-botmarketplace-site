# R002 — Cross-Asset Validation Protocol v0.1

**Frozen rule under test:** long when prior daily close > prior SMA120; otherwise cash.  
**Purpose:** test whether the R002 trend effect generalizes beyond BTC without tuning per asset.

## Fixed panel

Initial large/liquid panel:

- BTCUSDT
- ETHUSDT
- SOLUSDT
- XRPUSDT
- LTCUSDT
- ADAUSDT
- BNBUSDT

Data source: Bybit V5 daily linear-USDT perpetual klines, using only fully closed UTC candles.

BTC is included again as a venue/product normalization control against the earlier BTCUSD inverse-perpetual research series.

## No-tuning rule

The SMA120 parameter is frozen before looking at cross-asset results. We will **not** select a different moving-average length for each asset.

Execution convention:

1. compute close and SMA120 from a fully closed UTC candle;
2. the resulting signal is applied only from the next daily bar;
3. long-only, 0% or 100% exposure;
4. no leverage;
5. cash return = 0 for screening;
6. transaction-cost sensitivity at 10 bps per 0→1 or 1→0 exposure change, with 25 and 50 bps stress checks.

## Two evaluation clocks

### A. Per-asset available-history test

Each asset is evaluated from the first day where SMA120 can be formed through the common dataset end. This maximizes evidence for each market but periods differ.

### B. Common-overlap test

All assets are evaluated over one identical date range beginning only after every included asset has at least 120 observations. This is the fair apples-to-apples comparison.

Both must be reported; neither substitutes for the other.

## Metrics

For each asset compare frozen SMA120 with exact same-asset buy-and-hold:

- CAGR
- max drawdown
- annualized volatility
- ending multiple
- market exposure
- number of exposure changes
- worst calendar year / best calendar year where sample allows
- late-period result where sample length allows

Primary success question is **not** whether SMA120 beats buy-and-hold CAGR on every coin. The generalization signal is stronger if it consistently reduces major drawdowns and improves risk-adjusted / return-to-drawdown behavior across multiple independent assets without retuning.

## Portfolio diagnostic

After individual-asset results, test one simple equal-weight trend portfolio:

- fixed asset universe above;
- each eligible asset receives equal strategic weight;
- an asset's sleeve is invested only when its own frozen SMA120 signal is long;
- otherwise that sleeve remains cash;
- no ranking, momentum selection, leverage, or optimized weights.

This portfolio is diagnostic only until survivorship bias is addressed.

## Bias warning

This panel consists of assets that are large/liquid **today**. That introduces survivorship / selection bias: failed or delisted historical assets are absent. Therefore:

- PASS here means cross-market robustness among surviving liquid assets;
- it does **not** prove a historically unbiased crypto-universe strategy.

If results are promising, a later test must use a point-in-time historical universe or include delisted/failed assets where reliable data can be obtained.

## Decision rule

Advance cross-asset R002 only if:

1. the frozen rule works reasonably across several assets rather than one isolated winner;
2. drawdown reduction is broad and economically meaningful;
3. behavior survives cost stress;
4. the common-overlap portfolio is not dependent on one coin;
5. BTCUSDT control remains directionally consistent with the prior BTCUSD result.

No parameter changes are permitted based on these results. Any changed lookback becomes a new candidate/version.
