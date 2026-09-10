# R003-E003 — Forward Implementation Freeze v0.2

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Protocol:** `docs/research/r003-e003-forward-paper-protocol-v0.1.md`  
**Status:** frozen before first forward P&L  

## 1. Frozen engine

Path:

`research/r003/r003_e003_forward_paper_v0_2.py`

Frozen engine commit:

`cfc001400008ee4d63a27ad6821dda5cb9354f3e`

Mobile launcher:

`research/r003/r003_e003_forward_paper_mobile_v0_2.py`

Launcher commit:

`8367b239795f345d97b09fc9ab957aa3f3d31e57`

## 2. Why v0.2 exists before inception

The initial forward implementation included immutable inception hurdles (3.90% Treasury and 5.90% Treasury+2pp), but a technical review before the first forward trade identified that a one-year fixed safe-capital hurdle could become stale as Treasury rates move.

v0.2 therefore adds a **causal dynamic 13-week Treasury bill opportunity-cost proxy** without changing any R003 trading rule.

No R003 forward P&L existed before this addition.

## 3. Causal Treasury rule

- Source: official U.S. Treasury Daily Treasury Bill Rates CSV.
- Field: 13-week Treasury bill coupon-equivalent yield.
- A quote dated day d becomes available to the benchmark only from day d+1.
- Weekends/holidays use the latest already-available quote.
- The safe-reference NAV accrues hourly from the causally available annualized rate.
- This is an opportunity-cost proxy, not a literal rolling-bill total-return replication.

The immutable 3.90% inception hurdle and 5.90% compensation floor remain unchanged.

## 4. Fixed forward inception

Decision boundary remains:

**2026-09-10 12:00:00 UTC**.

The initial paper position is established at the close of the first fully closed common 1h bar whose open time is at or after that boundary. Funding at or before that establishment close is excluded.

## 5. Frozen R003 mechanics

Unchanged from E002/E003 protocol:

- 50% NAV long spot BTC;
- 50% NAV futures collateral;
- equal-BTC short BTCUSDT perpetual;
- no leverage or borrowing;
- UTC month-end rebalancing only;
- 5/10/25 bps per-leg cost tracks;
- REALIZED / ZERO / ADVERSE funding tracks;
- 10% conservative research headroom threshold;
- no funding threshold or activation filter.

## 6. Output package

Maximum user-facing package remains below 10 files:

1. `r003_e003_run_state.json`
2. `r003_e003_source_audit.json`
3. `r003_e003_forward_hourly_nav.csv`
4. `r003_e003_metrics.csv`
5. `r003_e003_margin.csv`
6. `r003_e003_funding_events.csv`
7. `r003_e003_monthly.csv`
8. `r003_e003_safe_hurdle_daily.csv`
9. `r003_e003_summary.md`

The local `.py` copy does not need to be uploaded.

## 7. Evidence discipline

No terminal positive promotion before 365 calendar days, 1,000 forward funding events and 10 completed month-end rebalance opportunities.

Short-term P&L cannot reset the forward clock or change any rule.