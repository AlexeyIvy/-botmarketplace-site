# R002 Survivorship-Bias Validation v0.1

## Purpose

Test whether the frozen SMA120 effect survives when historical/non-survivor Binance USD-M contracts are included, rather than evaluating only current large-liquid winners.

## Dataset

Downloaded fixed subset:

- 22 historical/non-survivor candidates selected before strategy evaluation;
- 7 survivor controls: BTC, ETH, SOL, XRP, LTC, ADA, BNB;
- 37,821 raw daily rows total.

Collector state reported all 29 symbols complete, no failed or missing symbols.

## Critical data-quality finding

Binance monthly archives can continue to contain flat, zero-volume daily rows long after a contract stopped trading. Treating those rows as live market history materially corrupts backtests and can make delisted contracts appear to remain tradable.

Examples:

- BTCSTUSDT: only 9 positive-volume daily observations, followed by roughly 1,936 flat zero-volume days in the downloaded archive;
- BTSUSDT: roughly 649 trailing zero-volume days;
- SRMUSDT: roughly 560 trailing zero-volume days;
- HNTUSDT: roughly 435 trailing zero-volume days;
- COCOSUSDT: roughly 369 trailing zero-volume days.

Therefore the authoritative validation truncates each symbol at its **last positive-volume day**. BTCSTUSDT and COCOSUSDT are then excluded because they do not have 120 tradable daily observations for SMA120 warm-up.

This stale-tail cleaning is mandatory for all future Binance historical-universe work.

## Execution assumptions

- signal formed on fully closed daily data;
- signal shifted one day before applying return;
- long/cash only;
- 10 bps per 0↔1 exposure change;
- conservative final liquidation cost if long on the final tradable day;
- no per-asset parameter tuning.

## Historical/non-survivor results

After stale-tail cleaning, 20 historical symbols have enough tradable history for evaluation.

### Frozen SMA120

Against each asset's own buy-and-hold benchmark:

- CAGR higher on **16 / 20** historical assets;
- max drawdown better on **19 / 20**;
- both CAGR and max drawdown better on **16 / 20**;
- median SMA120 CAGR: about **+3.1%**;
- median buy-and-hold CAGR: about **−4.5%**;
- median SMA120 max drawdown: about **−60.0%**;
- median buy-and-hold max drawdown: about **−87.7%**.

The key result is not that SMA120 turns every failed token into a profitable investment. Several remain negative. Rather, it substantially reduces exposure to prolonged collapses and often converts catastrophic buy-and-hold outcomes into materially smaller losses or positive results.

Notable examples:

- LUNAUSDT: buy-and-hold over the post-warm-up window effectively collapses (~−99.99% max drawdown), while SMA120 exits the destructive regime much earlier; strategy max drawdown is ~−46.8% and ending multiple ~5.1x over the tested window. The extremely high CAGR is a short-window artifact and must not be extrapolated.
- SRMUSDT: buy-and-hold CAGR ~−50%, SMA120 ~+88%, with max drawdown improving from ~−99% to ~−61%.
- HNTUSDT: buy-and-hold CAGR ~−16%, SMA120 ~+106%, with max drawdown improving from ~−97% to ~−73%.
- AUDIOUSDT: buy-and-hold CAGR ~−60%, SMA120 approximately flat/slightly positive, with max drawdown improving from ~−94% to ~−51%.

Failures matter too:

- EOSUSDT, YFIIUSDT, BZRXUSDT, and FRONTUSDT do not beat buy-and-hold on CAGR under SMA120;
- YFII is also slightly worse on max drawdown;
- this confirms the rule is not universal and does not eliminate whipsaw risk.

## SMA120 + ADX20 research variant

On the same 20 historical assets:

- CAGR higher than buy-and-hold on **14 / 20**;
- max drawdown better on **20 / 20**;
- both improved on **14 / 20**;
- median strategy CAGR approximately **+0.25%**;
- median buy-and-hold CAGR approximately **−4.5%**;
- median max drawdown approximately **−61.0%** vs buy-and-hold ~−87.7%.

Interpretation: ADX20 is a stronger drawdown filter, but it sacrifices too much upside on several assets. It is useful as a separate portfolio research variant, but this test does **not** justify replacing frozen SMA120 with ADX20.

## Survivor controls

On the seven current controls, the Binance dataset broadly reproduces earlier conclusions:

Frozen SMA120 improves both CAGR and drawdown on BTC, ETH, SOL, and ADA, while LTC, BNB and XRP remain weaker cases. This consistency across Bybit and Binance sources materially increases confidence that the BTC result is not an artifact of one venue or contract type.

## Research verdict

**SMA120 survivorship-bias stress test: PASS WITH IMPORTANT CAVEATS.**

This is a meaningful strengthening of R002. The trend effect is not confined to today's surviving winners: it also improves the majority of a deliberately selected historical/non-survivor stress set, especially by avoiding large portions of terminal declines.

However:

1. the subset is not yet a fully point-in-time investable universe; it is a fixed stress panel constructed from archive history;
2. futures delisting mechanics, settlement, liquidity decay, funding and execution around delisting are not fully modelled;
3. some very high annualized results occur over short windows and must not be extrapolated;
4. the result does not prove future profitability.

## Decision

- Keep **R002 v1.0 = frozen SMA120** unchanged and in forward validation.
- Keep **R002.1 = SMA120 + ADX20** as a separate experimental portfolio variant; do not promote it yet.
- Do not add a third indicator now.
- Next high-value step: build a simple point-in-time portfolio protocol that admits symbols only after sufficient live history and removes them at their last tradable day, then test equal-weight portfolio behavior without knowing future delisting status.
