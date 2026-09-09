# R002 — Historical Universe / Survivorship-Bias Protocol v0.1

## Why this test is necessary

The current cross-asset panel (BTC, ETH, SOL, XRP, LTC, ADA, BNB) was selected from large liquid assets that still exist today. That creates survivorship bias: assets that disappeared, were delisted, or structurally failed are underrepresented.

A trend-following rule can look better than reality if it is tested only on survivors.

## Objective

Test whether the frozen R002 logic remains useful when the universe is reconstructed from historical exchange archives rather than from today's active-symbol list.

Primary frozen rule remains unchanged:

- long-only;
- close > SMA120 => long;
- otherwise cash;
- signal formed on a fully closed daily bar;
- applied no earlier than the next bar;
- no per-asset parameter tuning.

R002.1 (SMA120 + ADX14 > 20) remains a separate research branch and must never retroactively replace R002 v1.0.

## Data-source choice

Primary source for the next stage: Binance public USD-M archive (`data.binance.vision`).

Reason:

- free public archive;
- monthly historical kline ZIPs;
- archive indexing is independent of today's active-symbol list;
- historical/delisted symbols can remain represented in the archive;
- suitable for building a point-in-time symbol inventory before downloading candles.

The first step is manifest discovery only. We do not download the full historical candle warehouse until the archive inventory has been inspected.

## Stage H1 — Archive manifest

Run `research/r002/binance_historical_universe_mobile.py`.

Outputs:

1. `r002_binance_um_1d_manifest.csv` — one row per symbol/month archive.
2. `r002_binance_um_symbol_summary.csv` — first month, last month, month count, and whether a symbol appears in the latest archive month.

Important: absence from the latest archive month is only a historical/delisting candidate flag. It is not by itself proof of why a market disappeared.

## Stage H2 — Pre-specified eligibility

Before looking at strategy performance, freeze simple eligibility rules. Proposed default:

- USDT-margined USD-M contracts only;
- at least 180 calendar days of archived history;
- at least 120 closed daily observations before the strategy may trade the symbol;
- no selection based on future return;
- no removal of symbols because they later delist;
- delisting/end-of-history must be treated as an observable market event, not silently dropped.

Liquidity rules, if added, must be based only on information available at the time and must be frozen before strategy performance is inspected.

## Stage H3 — Point-in-time portfolio construction

At each date:

1. determine which symbols were actually eligible from historical data available by that date;
2. compute SMA120 using only past closed bars;
3. allocate only across that date's eligible universe;
4. keep each inactive signal allocation in cash;
5. never backfill a future survivor into earlier dates.

Primary portfolio diagnostic: equal capital weight per eligible symbol slot. More complex ranking/volatility sizing is out of scope until the simple version is validated.

## Delisting handling

This is load-bearing.

If a symbol's archived history ends:

- do not delete its prior history;
- do not pretend it never existed;
- record the final available bar and exit treatment explicitly;
- run a conservative stress assumption for unresolved delisting gaps if exact final execution cannot be recovered.

The goal is to bias against the strategy rather than accidentally reward missing data.

## Comparison set

For the historical universe we will compare:

- buy-and-hold equal-weight point-in-time universe;
- frozen SMA120 point-in-time universe;
- separate diagnostic: SMA120 + ADX20;
- cash benchmark.

Key metrics:

- CAGR / ending multiple;
- max drawdown;
- worst calendar year;
- turnover and cost stress;
- fraction of symbols where trend beats their own buy-and-hold;
- contribution from later-delisted symbols;
- portfolio result with and without later-delisted symbols (diagnostic only, to quantify survivorship distortion).

## Decision rule

A strong result is not "every coin wins."

We want evidence that:

- the portfolio-level risk reduction survives inclusion of failed/delisted markets;
- performance is not carried only by today's survivors;
- no narrow symbol subset or threshold explains the result;
- R002 remains economically useful after conservative execution and delisting treatment.

Until this is complete, cross-asset robustness remains **PARTIAL PASS**, not full validation.
