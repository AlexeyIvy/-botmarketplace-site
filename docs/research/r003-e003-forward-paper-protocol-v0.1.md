# R003-E003 — Forward Paper Protocol v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Candidate:** R003 — Funding / Basis Carry  
**Experiment:** E003  
**Date:** 2026-09-10  
**Status:** pre-forward frozen specification  
**Parent result:** `docs/research/r003-e002-results-v0.1.md`  
**Technical review:** `docs/research/r003-post-e002-technical-review-and-plan-v1.0.md`

## 1. Objective

R003-E002 produced an IMPLEMENTATION_PROMISING historical implementation result, but recent capital efficiency was MARGINAL and the history was already inspected.

E003 creates a genuine forward-only paper record for the exact frozen implementation.

Primary question:

> Does the unconditional, fully funded BTC spot/perpetual carry continue to earn positive and sufficiently compensated excess return on future data, without leverage, funding thresholds or rule changes?

## 2. Frozen portfolio

At forward inception NAV = 1.0:

- 50% NAV long Binance Spot BTCUSDT;
- 50% NAV USDT futures-collateral bookkeeping account;
- short Binance USD-M BTCUSDT perpetual in equal BTC quantity to the spot position;
- no external borrowing;
- no cross-margin / portfolio-margin assumption;
- no collateral yield;
- no spot lending yield;
- no leverage optimization.

Between rebalances BTC quantities remain equal and fixed.

## 3. Frozen rebalance

Rebalance only at the final fully closed common 1h bar of each UTC calendar month.

At rebalance:

- recompute NAV;
- reset spot market value to 50% of pre-cost NAV;
- set short perpetual BTC quantity equal to spot BTC quantity;
- transfer bookkeeping cash between spot and futures collateral as required;
- charge execution costs on both traded legs.

No other rebalance frequency is allowed.

## 4. Forward data sources

Use the same Binance public data families as E002:

- spot BTCUSDT 1h klines: `https://data-api.binance.vision/api/v3/klines`;
- USD-M BTCUSDT 1h contract klines: `https://fapi.binance.com/fapi/v1/klines`;
- USD-M BTCUSDT 1h mark-price klines: `https://fapi.binance.com/fapi/v1/markPriceKlines`;
- realized funding: `https://fapi.binance.com/fapi/v1/fundingRate`.

Only fully closed common hourly bars count.

Do not silently switch venues or sources. A permanent source change requires a versioned protocol revision before using the replacement for forward conclusions.

## 5. Fixed forward inception

The protocol is frozen during 2026-09-10 UTC.

Set the immutable forward decision boundary to:

> **2026-09-10 12:00:00 UTC.**

To avoid using an unclosed bar as an execution price, the paper portfolio is first established at the **close of the first fully closed common 1h bar whose open time is >= 2026-09-10 12:00 UTC**. Under normal hourly continuity this is the bar closing at approximately 12:59:59.999 UTC.

The first realized forward pair P&L is therefore the next complete common hourly interval after that initial establishment close.

Funding events with timestamp <= the actual initial establishment close are excluded from forward P&L. Only funding events occurring after the paper portfolio is already established may contribute.

The inception boundary and initial-establishment rule may never move forward because the first tracker run occurs later.

If the tracker is first run days or months later, it must reconstruct the record causally from this fixed boundary.

## 6. Price and funding accounting

Preserve E002 self-financing mechanics:

- spot value follows spot price;
- short perpetual P&L is marked with mark-price movement;
- funding uses published realized rate and published positive funding mark price where available, otherwise latest causally available mark close;
- positive funding is income to the short; negative funding is a cost;
- spot/perpetual mark divergence remains in pair/basis P&L;
- futures collateral is tracked separately from spot value.

Funding at a timestamp is included only if the portfolio was already open before that funding event.

## 7. Execution-cost tracks

Per traded notional per leg:

- 5 bps;
- **10 bps baseline**;
- 25 bps stress.

Charge costs on:

- initial spot and perpetual establishment;
- month-end quantity adjustments;
- hypothetical terminal close for review metrics only.

No fee-tier optimization.

## 8. Margin diagnostics

Preserve E002 conservative research diagnostics:

- close collateral ratio;
- intrahour collateral ratio using mark-price high and no assumed transfer of offsetting spot gains during the hour;
- `LOW_HEADROOM` below 10%;
- hard failure if futures collateral <=0.

The 10% threshold is a research buffer, not Binance's exact liquidation formula.

No claim of live liquidation safety may be made from this proxy alone.

## 9. Safe-capital hurdles

Frozen benchmark snapshot:

`docs/research/safe-sleeve-hurdle-snapshot-2026-09-10.md`

Forward dashboard must retain both immutable inception references:

- 13-week Treasury-bill inception hurdle: **3.90% annualized**;
- research compensation floor: **5.90% annualized** (= Treasury inception rate +2pp).

These fixed references may not be changed after observing forward results.

### Causal dynamic Treasury reference

Also maintain a non-tunable, time-varying opportunity-cost proxy from the official U.S. Treasury **13-week Treasury bill coupon-equivalent** daily series.

Causality rule:

- a Treasury quote dated calendar day `d` becomes usable by the forward benchmark only on calendar day `d+1`;
- weekends/holidays forward-fill the latest already-available quote;
- accrue an hourly safe-reference NAV from the causally available annualized rate;
- never backfill a newly published quote into earlier forward hours.

This dynamic series is an opportunity-cost proxy, not an exact investable rolling-bill total-return index.

If the Treasury source is temporarily unavailable, Binance forward P&L may still be recorded, but the safe-hurdle comparison must be flagged incomplete and no final capital-efficiency conclusion may be issued until the benchmark is reconstructed.

Inflation is contextual only and is not the primary hurdle.

## 10. Funding ablations

Track the same three treatments on the same forward market path:

- `REALIZED_FUNDING`;
- `ZERO_FUNDING`;
- `ADVERSE_FUNDING`: positive realized rates x0.5, negative rates x2.0.

These are diagnostics. No adaptive switching among treatments is allowed.

## 11. Required outputs

Keep the user-facing package <=10 files.

Required outputs:

1. `r003_e003_run_state.json`
2. `r003_e003_source_audit.json`
3. `r003_e003_forward_hourly_nav.csv`
4. `r003_e003_metrics.csv`
5. `r003_e003_margin.csv`
6. `r003_e003_funding_events.csv`
7. `r003_e003_monthly.csv`
8. `r003_e003_safe_hurdle_daily.csv`
9. `r003_e003_summary.md`

## 12. Review cadence

The tracker may be run at any time; only fully closed bars count.

Allowed formal descriptive reviews:

- monthly, after each completed UTC calendar month;
- interim technical checks at any time for data integrity only.

No parameter changes at reviews.

## 13. Evidence threshold

No terminal positive promotion decision before at least:

- **365 calendar days** after inception; and
- at least **1,000 realized forward funding events** if the historical ~8h cadence remains broadly similar; and
- at least 10 completed month-end rebalance opportunities.

If one condition is not met, continue the record.

Early operational/data failure may invalidate the forward record and require a documented protocol revision, but short-term P&L must not be used as an excuse to reset inception.

## 14. Forward decision framework

### FORWARD_SUPPORTIVE

Broadly require after sufficient evidence:

- baseline realized-funding return positive;
- no modeled hard margin failure;
- no persistent breach of the 10% research headroom buffer;
- 25 bps/leg stress remains economically viable;
- realized funding materially improves results versus ZERO_FUNDING;
- forward economics exceed the causally accrued dynamic 13-week Treasury opportunity-cost proxy;
- the frozen 3.90% inception hurdle remains visible as an anti-benchmark-moving reference;
- preferably the result is also consistent with the frozen 5.90% compensation floor;
- no single short regime explains nearly all gains;
- basis/operational behavior remains consistent with implementation assumptions.

### FORWARD_NEUTRAL / CONTINUE

Use if:

- sample is still too short;
- return is positive but only marginal versus Treasury;
- the dynamic Treasury comparison is incomplete;
- or comparisons are mixed.

### FORWARD_NEGATIVE

Use after sufficient evidence if:

- net carry is persistently below the causal dynamic Treasury hurdle;
- adverse funding/cost stress erases economics;
- margin headroom becomes unacceptable;
- or funding no longer materially compensates basis/execution drag.

No historical funding threshold or leverage rescue may follow directly from a negative result.

## 15. Operational common-mode warning

R003 and R009 may have different economic return sources but share venue/collateral failure risk if both depend on Binance/USDT.

Do not count R003 as diversification of the safe sleeve.

Any future portfolio combination requires separate off-venue reserve and common-mode failure analysis.

## 16. Anti-overfitting freeze

During E003 do not change:

- BTCUSDT;
- 50/50 capital split;
- equal-BTC hedge;
- month-end rebalance;
- 5/10/25 bps cost tracks;
- funding treatments;
- margin diagnostics;
- fixed inception;
- frozen Treasury inception references;
- causal dynamic Treasury rule;
- no funding activation threshold;
- no leverage;
- no trend/volatility filter;
- no venue switch without protocol revision.

Any material change creates a new candidate/version and does not overwrite this forward record.