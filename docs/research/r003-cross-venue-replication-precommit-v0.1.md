# R003 — First Cross-Venue Replication Precommit v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** venue choice frozen before inspecting replication results

## 1. Purpose

Reduce venue-selection bias after the positive Binance R003 result.

The first external replication venue is prospectively fixed as:

> **Bybit**

This precommit is made before downloading or evaluating Bybit R003 performance results.

## 2. Why Bybit is selected

Selection is based on methodological comparability and public data access, not expected profitability.

Current public Bybit documentation exposes:

- historical realized funding-rate endpoint for perpetuals;
- spot and linear-contract historical klines;
- historical mark-price klines.

This allows a close structural and implementation replication of Binance R003-E001/E002 mechanics.

OKX remains a later possible third-venue check, but its current official downloadable archive advertises funding history from March 2022 and OHLC history from July 2023, reducing first-replication window comparability.

## 3. Replication sequence

Do not jump directly to a tuned Bybit strategy.

### X001 — Structural funding replication

Reuse the conceptual R003-E001 question:

- BTC perpetual funding only;
- no funding threshold;
- no trend/volatility filter;
- realized funding as published;
- regime and stress diagnostics;
- data window = all common reliable source history available under the frozen Bybit source protocol.

### X002 — Self-financing implementation replication

Only if X001 supports a structural premium:

- long BTC spot;
- equal-BTC short linear perpetual;
- conservative fully funded collateral convention;
- actual spot/perp/mark path;
- funding cashflows;
- deterministic rebalance;
- execution-cost stress;
- separately tracked margin headroom.

Any Bybit-specific contract mechanics must be documented before result inspection rather than silently forced into Binance assumptions.

## 4. Interpretation

Cross-venue confirmation would strengthen evidence that R003 captures a broader derivatives-demand premium rather than a Binance-only artifact.

Cross-venue failure would not justify venue shopping. The next venue may only be opened under a new documented protocol explaining why the test is informative.

## 5. Prohibitions

Before and during the first Bybit replication do not:

- search multiple venues and report the winner;
- tune a funding-entry threshold;
- change leverage/collateral to rescue results;
- change BTC to a better-looking altcoin;
- use Binance result periods to select Bybit subperiods;
- discard early or adverse Bybit history without a pre-specified data-quality reason.

## 6. Current priority

This replication is prospectively frozen now but executes **after Safe-Sleeve S001 architecture/failure analysis** and after the forward infrastructure has technically initialized.
