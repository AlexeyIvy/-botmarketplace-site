# R002 — Historical Survivorship Subset Protocol v0.1

## Purpose

Test whether the frozen R002 trend rules generalize beyond today's surviving large-cap crypto assets.

The key bias being addressed is survivorship bias: a strategy can look artificially good if it is tested only on assets that are still alive, liquid, and prominent today.

## Data source

Binance public USD-M monthly 1d kline archive manifest collected on 2026-09-09.

Manifest facts used to pre-specify the subset:

- 864 USDT symbols with 1d monthly archives.
- 31 symbols absent from the latest archive month (2026-08).
- 22 of those absent symbols have at least 12 archived months.

## Historical/non-survivor subset

All symbols absent from the latest archive month with at least 12 archived months:

SXPUSDT, EOSUSDT, BTCSTUSDT, MATICUSDT, HNTUSDT, SRMUSDT, TOMOUSDT, BTSUSDT, AUDIOUSDT, ANTUSDT, GALUSDT, AERGOUSDT, FOOTBALLUSDT, YFIIUSDT, BLUEBIRDUSDT, RNDRUSDT, AKROUSDT, LUNAUSDT, BZRXUSDT, DODOUSDT, COCOSUSDT, FRONTUSDT.

This threshold is deliberately simple and set before seeing strategy returns. Twelve monthly archives are comfortably longer than the 120-day SMA warm-up requirement and avoid placing too much weight on extremely short-lived listings.

## Survivor controls

Use the same seven current-large-liquid controls from the prior Bybit cross-asset validation:

BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, LTCUSDT, ADAUSDT, BNBUSDT.

## Frozen rules

No parameter tuning is permitted inside this test.

Primary control rule:

- SMA120 long-only: hold the asset when prior closed daily close > prior closed SMA120; otherwise cash.

Research variant:

- SMA120 + ADX14 > 20, with the same next-day signal discipline.

The existing frozen BTC SMA120 forward candidate remains unchanged regardless of this test's outcome.

## Execution assumptions

- Daily closed candles only.
- Signal formed after a daily close and applied from the next day.
- No same-day close look-ahead.
- Same cost assumptions as prior R002 robustness work, with sensitivity checks later.
- No leverage and no shorting.

## Required reporting

Report historical/non-survivors and survivor controls separately before any pooled result.

For each group and rule report at minimum:

- CAGR distribution across symbols;
- max-drawdown distribution;
- fraction of symbols beating buy-and-hold CAGR;
- fraction improving max drawdown;
- fraction improving both;
- turnover and exposure;
- equal-weight portfolio diagnostic using only assets with available data at each date;
- cost sensitivity.

## Interpretation rule

A positive result requires broad cross-symbol evidence, not one or two exceptional winners.

Strong evidence would look like:

- risk reduction surviving across both survivors and non-survivors;
- a meaningful share of non-survivors improving both return and drawdown;
- pooled/equal-weight results not being dominated by a tiny number of assets;
- the conclusion surviving reasonable transaction-cost stress.

If the effect collapses on non-survivors, the earlier large-cap result must be downgraded as materially affected by survivorship bias.

## Status

Protocol frozen before downloading the selected daily candles or evaluating strategy returns on this historical subset.
