# SC001 — Next Primary Forced-Flow Relative Dislocation Fee Qualification v0.1

Date: 2026-09-29
Status: PRE-OUTCOME FEE QUALIFICATION / CONSERVATIVE COMMON FROZEN-UNIVERSE RATE
Task ID: SC001-NEXT-PRIMARY-PREFREEZE-01
Family: VENUE_LOCAL_FORCED_FLOW_RELATIVE_DISLOCATION

## Purpose

Qualify the regular-user Bybit taker-fee assumption for every frozen execution contract before any S0 price/outcome access.

This qualification is product/zone based and outcome-independent. It does not use price, liquidation outcome, returns, PnL, symbol performance or event frequency.

## Official fee semantics

Bybit official Trading Fee Structure, retrieved 2026-09-29:
https://www.bybit.com/en/help-center/article/Trading-Fee-Structure

For VIP0 / regular users:
- ordinary Perpetual & Futures taker fee: 0.0550% = 5.5 bps/fill;
- Pre-Market Perpetual taker fee: 0.1000% = 10 bps/fill;
- Perpetual Innovation Zone taker fee: 0.1100% = 11 bps/fill.

Bybit official API instrument semantics:
https://bybit-exchange.github.io/docs/v5/market/instrument

Relevant fields include category, symbol, contractType, status, quoteCoin, settleCoin, symbolType and isPreListing.

The frozen B13-C source qualification already requires every frozen symbol to be:
- category = linear;
- exact frozen symbol;
- contractType = LinearPerpetual;
- quoteCoin = USDT;
- status = Trading.

No fee choice is allowed to depend on S0 outcomes.

## Frozen-universe qualification

For the common S0 hurdle, do not rely on the lower ordinary 5.5 bps rate.

Freeze the single conservative maximum product/zone taker rate applicable to the frozen crypto linear-perpetual universe:

regular_user_taker_fee_bps_per_fill = 11.

This covers the ordinary, pre-market and Innovation-Zone retail taker schedules without needing a lower symbol-specific rate to make the candidate feasible.

Per frozen contract:

| Frozen contract | Qualified product | Common frozen taker fee used by S0 |
|---|---|---:|
| BTCUSDT | Bybit linear USDT perpetual | 11 bps/fill |
| ETHUSDT | Bybit linear USDT perpetual | 11 bps/fill |
| SOLUSDT | Bybit linear USDT perpetual | 11 bps/fill |
| DOGEUSDT | Bybit linear USDT perpetual | 11 bps/fill |
| ORDIUSDT | Bybit linear USDT perpetual | 11 bps/fill |
| FILUSDT | Bybit linear USDT perpetual | 11 bps/fill |
| UNIUSDT | Bybit linear USDT perpetual | 11 bps/fill |
| XRPUSDT | Bybit linear USDT perpetual | 11 bps/fill |
| LTCUSDT | Bybit linear USDT perpetual | 11 bps/fill |
| OPUSDT | Bybit linear USDT perpetual | 11 bps/fill |
| BCHUSDT | Bybit linear USDT perpetual | 11 bps/fill |
| SUIUSDT | Bybit linear USDT perpetual | 11 bps/fill |

The table is a conservative S0 cost freeze, not a claim that the actual account fee on every contract equals 11 bps.

If an official account/region rate known before outcome authorization is higher than 11 bps/fill, the hurdle must be revised upward before outcome access. A lower account/VIP rate may not lower this S0 fee freeze.

## Mechanical Edge-to-Fill recomputation

Structural fills = 2.

two_fill_fee_floor_bps = 2 * 11 = 22.

Retain prospectively frozen non-fee reserves:
- conservative spread/depth reference = 10 bps;
- execution/model reserve = 10 bps;
- S0 funding/borrow reference = 0 bps because S0 opens no position/hold/PnL.

two_fill_structural_burden_bps = 22 + 10 + 10 = 42.

H = max(30, 42 + 10) = 52 bps.

Frozen S0 hurdle:

H = 52 bps.

No maker rebate credit. No post-outcome downward fee revision.
