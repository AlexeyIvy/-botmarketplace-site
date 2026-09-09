# R003-E001 — Implementation Freeze v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Experiment:** R003-E001  
**Date:** 2026-09-09  
**Status:** frozen before result  
**Protocol:** `docs/research/r003-e001-funding-premium-structural-audit-protocol-v0.1.md`

## 1. Frozen engine

Engine path:

`research/r003/r003_e001_funding_premium_audit.py`

Frozen engine commit:

`e0b61f25df36b8edf8272551dd1ed75f8518bdbf`

Mobile launcher path:

`research/r003/r003_e001_funding_premium_audit_mobile.py`

Mobile launcher commit:

`fa50a01009377ba9894251da1620b2dbdfc7a3a3`

## 2. Frozen sources

Funding:

- Binance USD-M `BTCUSDT`;
- `https://fapi.binance.com/fapi/v1/fundingRate`;
- realized funding history;
- no API key;
- pagination from 2019-10-01.

Spot stress state:

- Binance Spot `BTCUSDT`;
- `https://data-api.binance.vision/api/v3/klines`;
- interval `1d`;
- only fully closed bars.

No silent venue/source substitution is allowed if the user's network blocks the USD-M endpoint.

## 3. Frozen calculations

- normalized short-side funding carry = published realized `fundingRate`;
- no entry filter;
- no funding threshold;
- no SMA/volatility/price filter;
- cumulative simple and compounded normalized funding;
- 7/30/90/365-day rolling funding diagnostics;
- calendar-year decomposition;
- causal spot-drawdown classification using only already-closed daily bars;
- drawdown buckets: 0-10 / 10-20 / 20-35 / 35-50 / 50+%;
- decision rule exactly as specified in protocol.

## 4. Important scope limit

The engine intentionally does **not** simulate a long-spot / short-perpetual portfolio.

Therefore it does not model:

- spot/perp basis P&L;
- margin/liquidation;
- collateral transfer;
- fees/spreads/slippage;
- legging;
- exchange/custody failure.

E001 only determines whether the realized funding premium is structurally interesting enough to justify R003-E002.

## 5. Output package

The engine produces at most eight result files, plus the `.py` engine copy:

1. `r003_e001_funding_raw.json`
2. `r003_e001_funding_clean.csv`
3. `r003_e001_spot_daily.csv`
4. `r003_e001_metrics.csv`
5. `r003_e001_yearly.csv`
6. `r003_e001_drawdown_buckets.csv`
7. `r003_e001_summary.md`
8. `r003_e001_run_state.json`

The `.py` copy may be omitted when uploading results.

## 6. Error behavior

If a funding/spot source request or engine step fails, the engine writes `r003_e001_run_state.json` with status `SOURCE_OR_ENGINE_ERROR` before re-raising the exception where possible.

A source failure is not a strategy result.

## 7. Post-result rule

- `STRUCTURAL_SIGNAL_PRESENT` -> design/freeze R003-E002 full self-financing cash-and-carry implementation before any further P&L result.
- `STRUCTURAL_SIGNAL_MIXED` -> no threshold tuning; decide between forward-only observation or closure.
- `STRUCTURAL_SIGNAL_ABSENT` -> close the current funding-premium premise without building a complex execution model to rescue it.

The crisis-financing classification is separate and determines whether contemporaneous funding can plausibly support a later convexity-financing concept.