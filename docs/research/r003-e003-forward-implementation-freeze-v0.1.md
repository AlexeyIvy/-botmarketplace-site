# R003-E003 — Forward Implementation Freeze v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Protocol:** `docs/research/r003-e003-forward-paper-protocol-v0.1.md`  
**Status:** frozen before any forward P&L is available

## 1. Frozen engine

Path:

`research/r003/r003_e003_forward_paper.py`

Frozen engine commit:

`a0bbdb4a5deff9854f162ed7ad2a3c6f848cd5cc`

## 2. Fixed inception

Immutable decision boundary:

**2026-09-10 12:00:00 UTC**.

The initial paper position is established at the close of the first fully closed common 1h bar with open time >= that boundary.

Funding at or before that actual establishment close is excluded.

The first forward pair P&L begins with the next complete common hourly interval.

## 3. Frozen economic rules

- 50% NAV spot BTC;
- 50% NAV futures collateral;
- equal-BTC short BTCUSDT perpetual;
- no external borrowing;
- no cross/portfolio-margin assumption;
- UTC calendar month-end rebalance only;
- 5/10/25 bps per-leg execution-cost tracks;
- REALIZED / ZERO / ADVERSE funding treatments;
- 10% research collateral-headroom threshold;
- zero collateral yield;
- no funding threshold;
- no leverage or parameter optimization.

## 4. Frozen safe-capital references

From `safe-sleeve-hurdle-snapshot-2026-09-10.md`:

- 13-week Treasury bill inception hurdle = **3.90% annualized**;
- research compensation floor = **5.90% annualized**.

These remain visible throughout the forward record and are not moved to make the strategy look better.

## 5. Short-sample discipline

- annualized return/volatility are not reported as meaningful before 30 elapsed days;
- no terminal promotion decision before 365 days, 1,000 funding events and 10 completed month-end rebalance opportunities;
- short-term positive or negative P&L cannot reset inception;
- source/data failure requires explicit protocol revision rather than silent source substitution.

## 6. User-facing output package

The engine targets <=8 files:

1. `r003_e003_run_state.json`
2. `r003_e003_source_audit.json`
3. `r003_e003_forward_hourly_nav.csv`
4. `r003_e003_metrics.csv`
5. `r003_e003_margin.csv`
6. `r003_e003_funding_events.csv`
7. `r003_e003_monthly.csv`
8. `r003_e003_summary.md`

## 7. Accounting note

The persistent forward path uses going-concern NAV. A hypothetical terminal two-leg close cost is applied only to review metrics, preventing repeated tracker runs from pretending that the strategy actually liquidates every time it is inspected.

This is a forward-reporting clarification, not a strategy-rule change.

## 8. Interpretation guardrail

R003-E003 remains a paper model. Even positive forward results do not by themselves validate:

- Binance solvency/access;
- USDT redemption/depeg risk;
- exact exchange liquidation rules;
- real order-book fills;
- taxes or legal access.

Operational validation is a later stage.