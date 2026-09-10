# R003-X003 — Bybit Forward Venue Replication Protocol v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Candidate:** R003 — Funding / Basis Carry  
**Experiment:** X003 — parallel Bybit forward venue replication  
**Date:** 2026-09-10  
**Status:** frozen before any Bybit X003 forward P&L  
**Research posture:** prospective venue replication; no rescue of Binance or Bybit X001; no parameter optimization

## 1. Objective

Open a second, independent forward data/implementation channel for the same fully funded delta-neutral carry idea on Bybit while the original Binance R003-E003 forward record remains unchanged.

Primary question:

> Does the same 50/50 equal-BTC spot/perpetual carry implementation remain operationally coherent and economically positive on future Bybit data without changing leverage, funding thresholds, rebalance cadence or capital split?

This experiment is not a replacement for Binance R003-E003 and does not overwrite the earlier Bybit X001 `STRUCTURAL_SIGNAL_MIXED` result. It is a low-cost prospective venue replication.

## 2. Venue and instruments

Venue: **Bybit**.

Use public V5 market data only:

- spot: `BTCUSDT`, category `spot`, endpoint `GET /v5/market/kline`, interval `60`;
- linear perpetual: `BTCUSDT`, category `linear`, endpoint `GET /v5/market/kline`, interval `60`;
- mark price: `BTCUSDT`, category `linear`, endpoint `GET /v5/market/mark-price-kline`, interval `60`;
- realized funding: `BTCUSDT`, category `linear`, endpoint `GET /v5/market/funding/history`;
- current instrument metadata: `GET /v5/market/instruments-info`.

Do not silently substitute another venue, symbol, contract type or price source.

## 3. Frozen portfolio

At initial establishment NAV = 1.0:

- 50% NAV long Bybit Spot BTCUSDT;
- 50% NAV in a separate USDT perpetual-collateral bookkeeping account;
- short Bybit linear BTCUSDT perpetual in equal BTC quantity to the spot holding;
- no external borrowing;
- no leverage optimization;
- no spot lending/staking yield;
- no collateral yield;
- no portfolio-margin/cross-margin benefit assumed.

BTC quantities remain equal between month-end rebalances.

## 4. Frozen rebalance

Rebalance only at the final fully closed common 1h bar of each UTC calendar month.

At rebalance:

- compute pre-cost NAV;
- reset spot market value to 50% NAV;
- set short perpetual BTC quantity equal to spot BTC quantity;
- charge execution cost on both changed legs.

No threshold, weekly/daily rebalance or adaptive hedge rule is permitted.

## 5. Forward inception

This protocol is frozen before **2026-09-10 16:00:00 UTC**.

Immutable Bybit X003 decision boundary:

> **2026-09-10 16:00:00 UTC**

The paper position is first established at the close of the first fully closed common Bybit 1h bar whose open time is >= the boundary. Under normal continuity this is approximately **2026-09-10 16:59:59.999 UTC**.

The first realized pair-price P&L is the next complete common hourly interval.

Funding events with timestamp <= the actual initial establishment close are excluded.

If the first tracker run occurs later, the record must reconstruct causally from this same fixed boundary and may not move inception forward.

## 6. Funding accounting and causality

Bybit positive funding means longs pay shorts; therefore for this short perpetual position:

`funding income = + funding_rate × BTC quantity × funding mark proxy`.

Funding-event application rule:

- an event enters P&L only after its actual timestamp has occurred and only if the paper position was already established;
- at hourly accounting resolution, attribute the event to the first fully closed common hourly row whose close time is at or after the event timestamp;
- never credit an event to a row ending before the event timestamp.

Funding mark proxy is frozen as:

- latest causally available Bybit hourly mark-price close at or before the funding timestamp.

This is an hourly research approximation, not a claim of exact exchange settlement-price reconstruction.

Bybit funding frequency may change dynamically; do not assume an immutable 8h cadence. Record actual event timestamps.

## 7. Price accounting

Per hour:

- spot value follows Bybit spot close;
- short perpetual P&L follows Bybit mark-price change;
- spot/mark divergence remains pair/basis P&L;
- futures collateral is tracked separately from spot value;
- funding cash is added only at causally eligible event timestamps.

## 8. Execution-cost tracks

For cross-venue comparability, retain the same abstract research cost grid as Binance E003, per traded notional per leg:

- 5 bps;
- **10 bps baseline**;
- 25 bps stress.

Charge costs on initial establishment, month-end quantity adjustments, and hypothetical terminal close for review metrics only.

These are research stress assumptions, not a statement of the user's actual Bybit fee tier.

## 9. Margin diagnostics

Preserve the same conservative research proxy as Binance E003:

- close collateral ratio;
- intrahour collateral ratio using mark-price high;
- `LOW_HEADROOM` below 10%;
- hard failure if futures bookkeeping collateral <= 0.

This is not Bybit's exact liquidation engine and does not prove live liquidation safety.

## 10. Safe-capital opportunity cost

Retain the same 2026-09-10 frozen references for comparability:

- 13-week Treasury inception hurdle: **3.90% annualized**;
- diagnostic Treasury +2pp compensation floor: **5.90% annualized**.

Also maintain the same causal dynamic official U.S. Treasury 13-week bill coupon-equivalent proxy, where quote date `d` is usable only from `d+1`.

## 11. Funding ablations

Track on the same Bybit path:

- `REALIZED_FUNDING`;
- `ZERO_FUNDING`;
- `ADVERSE_FUNDING`: positive realized rates ×0.5, negative realized rates ×2.0.

No adaptive switching is allowed.

## 12. Source/data gate

Use only fully closed common hourly bars.

Before 24 common hours, status may be `EARLY_FORWARD_SAMPLE`.

After 24 hours, require:

- spot hourly coverage >=99.5%;
- linear contract hourly coverage >=99.5%;
- mark-price hourly coverage >=99.5%;
- common-bar coverage >=99.5%;
- maximum retained hourly gap <=6 hours;
- positive retained prices.

Funding cadence irregularity is diagnostic, not automatically a data failure.

## 13. Evidence thresholds

No terminal positive promotion before all are met:

- at least 365 calendar days;
- at least 1,000 realized funding events, if the realized cadence produces that many; if Bybit cadence structurally yields fewer, continue until 365 days plus at least 10 month-end opportunities and separately review whether the funding-event-count criterion is applicable;
- at least 10 completed month-end rebalance opportunities.

Short-term P&L may never be used to move inception or retune rules.

## 14. Forward interpretation

Possible mature-review outcomes:

- `FORWARD_SUPPORTIVE`;
- `FORWARD_NEUTRAL_CONTINUE`;
- `FORWARD_NEGATIVE`.

Broadly require for positive support:

- realized-funding implementation positive after costs;
- no modeled hard margin failure;
- funding materially improves economics versus ZERO_FUNDING;
- 25 bps stress remains economically coherent;
- economics compare favorably with the causal Treasury opportunity-cost proxy;
- no operational/source mismatch invalidates the path.

## 15. Relationship to existing R003 evidence

- Binance R003-E003 remains the canonical original forward record and must continue when Binance access is available.
- Bybit X001 remains `STRUCTURAL_SIGNAL_MIXED`; X003 does not retroactively change that result.
- X003 does **not** authorize the previously prohibited Bybit historical X002 implementation rescue.
- Similar future behavior across Binance and Bybit would strengthen venue portability prospectively; disagreement would be informative and must not be resolved by choosing the prettier venue.

## 16. Required outputs

Keep user-facing package <=10 files:

1. `r003_x003_bybit_run_state.json`
2. `r003_x003_bybit_source_audit.json`
3. `r003_x003_bybit_forward_hourly_nav.csv`
4. `r003_x003_bybit_metrics.csv`
5. `r003_x003_bybit_margin.csv`
6. `r003_x003_bybit_funding_events.csv`
7. `r003_x003_bybit_monthly.csv`
8. `r003_x003_bybit_safe_hurdle_daily.csv`
9. `r003_x003_bybit_summary.md`

## 17. Anti-overfitting freeze

Do not change inside X003:

- venue/symbol/product;
- 50/50 split;
- equal-BTC hedge;
- month-end rebalance;
- funding sign;
- 5/10/25 bps cost grid;
- funding treatments;
- margin proxy;
- fixed inception boundary;
- Treasury references;
- no funding threshold;
- no leverage;
- no trend/volatility filter.

Any material change creates a new version and cannot overwrite X003.
