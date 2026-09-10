# R003-E003 Pandas Datetime-Unit Compatibility Hotfix Note v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** technical compatibility patch before first user forward run  
**Economic engine frozen commit:** `cfc001400008ee4d63a27ad6821dda5cb9354f3e`

## Purpose

The Android/Pydroid environment previously exposed a pandas `merge_asof` failure in R003-X001 when otherwise equivalent timezone-aware datetime columns used different internal units (`ms`, `us`, or `ns`).

R003-E003 contains two `merge_asof` operations with the same class of compatibility risk:

1. funding timestamp -> latest causally closed common market bar;
2. forward close timestamp -> causally available Treasury 13-week quote effective time.

The compatibility launcher therefore normalizes both sides of each merge to explicit `datetime64[ns, UTC]` before calling `merge_asof`.

## Research invariants unchanged

This patch does **not** change:

- R003-E003 inception / decision boundary;
- 50/50 fully funded construction;
- equal-BTC hedge;
- month-end rebalance;
- funding treatment;
- fee assumptions;
- margin diagnostics;
- Treasury hurdle values;
- causal Treasury effective-date rule;
- data source endpoints;
- forward evidence clock or decision gates.

The launcher still downloads the exact frozen economic engine commit and refuses to execute if the expected source anchors are not found exactly once.

## Files

Technical compatibility launcher:

`research/r003/r003_e003_forward_paper_mobile_pandas_hotfix.py`

Commit:

`e610201f346be53371f423f94b0f3f74425ee20a`

Updated combined forward orchestrator:

`research/forward/run_r009_r003_forward_mobile_v0_2.py`

Commit:

`4243588168978eedda197c1ec7c799c57191b43e`

## Interpretation

This is a software compatibility correction made before the first user R003-E003 forward result is inspected. It is not a strategy modification or historical rescue.
