# R003-E002 — Implementation Freeze v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Experiment:** R003-E002  
**Date:** 2026-09-09  
**Status:** frozen before result inspection  
**Protocol:** `docs/research/r003-e002-self-financing-cash-carry-protocol-v0.1.md`  
**Frozen engine commit:** `84ab935899b22b8610d7184b192a1b5e8e6df36d`

## 1. Purpose

This note removes remaining implementation ambiguity before any E002 output is inspected.

## 2. Exact canonical portfolio

- Fresh NAV = 1.0 for each reported slice.
- Long BTC spot market value = 50% of fresh NAV at inception.
- Remaining capital is USDT futures collateral.
- Short BTCUSDT perpetual quantity equals long spot BTC quantity exactly.
- No external borrowing.
- No portfolio-margin or cross-collateral assumption.
- Month-end UTC rebalance only.
- Between rebalances, equal BTC quantities remain fixed.

## 3. Exact hourly accounting order

For each fully closed common 1h bar after inception:

1. carry prior equal-BTC quantities through the hour;
2. mark the spot sleeve to spot close;
3. mark short perpetual P&L with the USD-M mark-price close;
4. compute conservative intrahour futures-collateral headroom using the mark-price high and no assumed intrahour transfer of offsetting spot gains;
5. if this bar is the last common fully closed hour of a UTC calendar month and is not the terminal slice bar, rebalance both legs to the frozen 50/50 equal-BTC convention and charge two-leg costs;
6. apply funding events mapped causally to that close boundary using the position quantity in force at the funding timestamp;
7. record NAV and margin diagnostics.

At the terminal bar charge hypothetical close costs on both legs.

## 4. Funding timestamp mapping

A funding observation is attached to the latest fully closed common hourly bar whose close timestamp is <= the funding timestamp.

Published positive `markPrice` is used for funding notional where available. If absent/nonpositive, use the latest causally available 1h mark-price close at or before the funding timestamp.

No future bar is allowed.

## 5. Exact cost grid

Per traded notional, separately on spot and perpetual legs:

- 5 bps;
- 10 bps baseline;
- 25 bps stress.

No fee-tier optimization.

## 6. Exact funding treatments

- `REALIZED_FUNDING`: published rate unchanged.
- `ZERO_FUNDING`: funding cash flow = 0.
- `ADVERSE_FUNDING`: positive rates x0.5, negative rates x2.0.

## 7. Exact margin gate

For the PRIMARY_2020 baseline portfolio:

- hard failure if futures collateral <= 0 at any point;
- conservative headroom failure if intrahour collateral ratio <10% at any point;
- the 10% level is a research buffer, not Binance's exact maintenance-margin tier.

## 8. Exact interpretation of previously qualitative gate phrases

For E002 decision logic:

- “REALIZED_FUNDING materially improves results versus ZERO_FUNDING” means PRIMARY_2020 realized-funding CAGR is at least **1.00 percentage point** higher than ZERO_FUNDING CAGR under the same 10 bps/leg accounting.
- “completed-year results are not dominated by a single year” means among completed calendar years from 2020 onward:
  - a strict majority have positive portfolio returns; and
  - the largest positive year's share of the sum of positive completed-year returns is <50%.
- “recent economics remain positive” is implemented separately by the POST_2023 baseline CAGR >0 and >=2.5% capital-efficiency gate already specified in the protocol.

## 9. Data gate implementation

From 2020-01-01 onward:

- source hourly coverage >=99.5% for spot, contract and mark series;
- common hourly coverage >=99.5%;
- no source/common gap >6 hours;
- no interpolation;
- at least 1,000 causally aligned funding observations.

Failure returns `DATA_REDESIGN` with no strategy interpretation.

## 10. Output package

Engine emits 9 result files, keeping the user-facing package within the 10-file attachment limit:

1. `r003_e002_source_audit.json`
2. `r003_e002_hourly_clean.csv`
3. `r003_e002_basis_diagnostics.csv`
4. `r003_e002_metrics.csv`
5. `r003_e002_margin_diagnostics.csv`
6. `r003_e002_primary_hourly_nav.csv`
7. `r003_e002_yearly.csv`
8. `r003_e002_summary.md`
9. `r003_e002_run_state.json`

The launcher also stores a local `.py` engine copy, which does not need to be uploaded.

## 11. Synthetic self-test

Before downloading data the engine verifies on a flat synthetic spot/mark path that:

- positive funding produces positive ending NAV;
- flat basis contributes zero pair-price P&L;
- no synthetic margin failure occurs.

## 12. No-result-chasing rule

After E002 output is inspected, do not rescue the same sample by changing:

- funding threshold;
- leverage/collateral fraction;
- month-end rebalance frequency;
- cost grid;
- margin buffer;
- adverse-funding stress;
- venue.

Any such change is a separately versioned hypothesis.

## 13. Pre-result mobile reliability revision

Before any R003-E002 output was inspected, the Android launcher was revised for interruption safety. This revision **does not change the frozen economic engine or any research rule**.

The launcher:

- keeps the exact frozen economic engine at commit `84ab935899b22b8610d7184b192a1b5e8e6df36d`;
- uses persistent workspace `/storage/emulated/0/Download/R003_E002_WORKSPACE`;
- fixes a first-run UTC data cutoff in `snapshot.json` so a resumed run cannot silently move the historical endpoint forward;
- atomically caches each downloaded API page as compressed JSON under `_cache/`;
- resumes from already cached pages after Pydroid/Android interruption rather than restarting network downloads;
- keeps cache separate from the 9 user-facing result files;
- warns on low free storage before the heavy download begins.

Initial resumable launcher commit: `76f5b0ff110c14008efb44ef5c7b8b2c60c9be32`.

If interruption occurs after downloads are complete but during calculation, the next run reuses the complete source cache and recomputes the deterministic analysis from the beginning. This is acceptable because no source bytes need to be re-downloaded and the frozen data cutoff remains unchanged.

### Post-success cache compaction

A subsequent pre-result usability revision keeps the same frozen engine and snapshot but reduces file clutter after a successful run:

- while a run is incomplete, page-level checkpoint files remain untouched because they are the resume mechanism;
- only after the full engine run returns successfully, the launcher verifies and packs the entire `_cache/` tree into one `_cache_bundle.zip` archive and removes the page directories;
- the 9 result files remain individually available under `results/` for audit/upload;
- if the launcher is ever rerun later, it automatically restores `_cache/` from `_cache_bundle.zip`, reuses the same snapshot/cutoff, and can recompute deterministically;
- no market data, page hashes, economic accounting, parameters, or decision rules are changed by this compaction.

Cache-compacting launcher commit: `8ac2f52600e5ee1994d0956352a3be54bea926c6`.
