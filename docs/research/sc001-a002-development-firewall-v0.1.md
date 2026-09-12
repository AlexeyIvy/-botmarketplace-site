# SC001 A002 Development Firewall v0.1

Status: **FROZEN BEFORE SUB-MINUTE STRATEGY FEATURES/P&L**  
Branch: **SC001**  
Date: 2026-09-12

## Purpose

This document tightens the SC001 Development workflow after A001 PASS, A002-PREFLIGHT PASS, and A002-B01 PASS. It does not alter the frozen calendar, the Development/Validation/Final date ranges, or any prior experiment result.

The goal is to avoid doing acquisition work merely because the data are available and to reduce researcher degrees of freedom before a sub-minute strategy candidate exists.

## Important interpretation boundary

A001, A002-PREFLIGHT, and A002-B01 are **data/infrastructure qualification stages**, not profitability tests. Their PASS status does not mean that a scalping strategy has passed historical performance tests.

The only completed SC001 strategy experiment so far is SC001-E001, and its frozen verdict is **FAIL**. No current sub-minute strategy has yet earned PROMISING_SCREEN, ROBUST_HISTORICAL_CANDIDATE, or ADVANCE_TO_FORWARD status.

## Frozen DEV structure

The existing DEV period remains 2023-04-01 through 2024-06-30. For the sub-minute research workflow it is now divided internally, without changing the official split:

### DEV-DISCOVERY

- 2023-Q2 — A002-B01 — 5 frozen days
- 2023-Q3 — A002-B02 — 5 frozen days
- 2023-Q4 — A002-B03 — 5 frozen days

Total: **15 frozen days**.

These days may later be used for exploratory feature research and candidate design, but only after a separate screening protocol is frozen.

### DEV-CONFIRMATION

- 2024-Q1 — A002-B04 — 5 frozen days
- 2024-Q2 — A002-B05 — 5 frozen days

Total: **10 frozen days**.

These days are reserved as an internal chronological holdout inside Development. They must not be used to tune a candidate that is subsequently judged on them.

## Acquisition rule

Immediate acquisition is authorized only for B02 and then B03, using the already frozen calendar and the same data-only integrity gates proven in B01.

B04/B05 are deliberately deferred until after:

1. B02 and B03 complete their data qualification;
2. a finite sub-minute screening protocol is frozen;
3. DEV-DISCOVERY screening identifies at most a small, explicitly counted candidate set.

This avoids downloading and mentally opening later DEV data before they are needed.

## Strategy research firewall

Before any strategy feature, predictive score, threshold search, or P&L is calculated on A002 data, create and freeze a new screening protocol (planned name: `SC001-E002-SCREEN-v0.1`). That protocol must define at minimum:

- economic hypothesis/family;
- permitted input fields;
- aggressor-side interpretation;
- feature formulas;
- lookback windows;
- prediction/holding horizons;
- threshold/search budget;
- event-vs-ordinary treatment;
- day-level/block inference;
- multiple-testing ledger;
- promotion and rejection rules;
- explicit prohibition on using B04/B05, Validation, or Final for tuning.

No strategy feature/P&L is authorized merely because B02/B03 data have been acquired.

## Why this is stricter than the previous sequence

The earlier acquisition plan allowed all 25 DEV trade-level days to be collected before candidate design. That is technically valid, but it leaves unnecessary room for accidental inspection and creates work before it is known whether a promising sub-minute effect exists.

The new firewall keeps the same frozen dates while creating a stronger chronological internal holdout:

`DEV-DISCOVERY (15 days) -> candidate freeze -> DEV-CONFIRMATION (10 days) -> later execution/L2 qualification -> official Validation -> Final`

This reduces overfitting risk and avoids unnecessary B04/B05 acquisition if the discovery family is already falsified.

## Statistical interpretation

Millions of aggTrades are not millions of independent observations. Primary inference remains day/block based, consistent with `sc001-microstructure-pretest-v0.1.md`.

The quarterly calendar intentionally over-represents CPI/NFP/FOMC relative to natural calendar frequency. Event and ordinary strata must therefore be reported separately; raw-row pooling must not be presented as naturally weighted market performance.

## aggTrades limitations retained

Binance aggTrades can support trade-flow and short-horizon predictive diagnostics but do not provide historical bid/ask spread, depth, queue position, or exact passive fill probability.

Underlying `first_trade_id`/`last_trade_id` gaps observed in B01 remain diagnostic only. Do not infer an exact global raw-trade count from those ranges without a separate raw-trades qualification.

No maker-fill claim and no final net-execution claim may be made from aggTrades alone.

## Next action

Proceed with **A002-B02 / 2023-Q3**, exactly five frozen DEV-DISCOVERY days, data qualification only, no strategy features and no P&L.

If B02 passes, proceed to B03 under the same firewall. After B03, stop acquisition and freeze `SC001-E002-SCREEN-v0.1` before any strategy analysis.
