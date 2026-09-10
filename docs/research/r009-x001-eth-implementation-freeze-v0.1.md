# R009-X001 ETH — Implementation Freeze v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** frozen before ETH result inspection  
**Protocol:** `docs/research/r009-x001-eth-unchanged-rule-structural-falsification-protocol-v0.1.md`  
**Protocol commit:** `1cd6e91791c739a5a7bc27bfefcfedc074e22030`  
**Frozen engine commit:** `70994fac3023a9662f538208bd3fce7fba3051e6`

## 1. Purpose

Remove implementation ambiguity before any ETH X001 result is inspected.

## 2. Exact strategy invariants

The engine preserves the BTC R009 v0.1 economic rules without ETH-specific tuning:

- SMA120 including day t;
- 10% trend sleeve when price > SMA120, else 0%;
- 10% crisis sleeve in four 2.5pp tranches;
- -20/-35/-50/-65% drawdown triggers from running daily closing ATH;
- sticky crisis tranches until strictly new ATH;
- additive trend + crisis target;
- state at t applies to return t+1;
- self-financing daily-target accounting;
- 5/10/25/50 bps cost grid;
- zero cash yield;
- no leverage, funding, staking, or lending.

## 3. Data implementation

- Binance Spot ETHUSDT daily klines.
- First-run UTC cutoff persisted in `snapshot.json`.
- Only fully closed daily bars before the cutoff are retained.
- Download pages are cached with SHA256 checksums and reused after interruption.
- No interpolation.
- State is initialized from earliest retained ETHUSDT history.
- PRIMARY begins at the first full calendar year after source start, without resetting ATH/SMA state.

## 4. Comparison set

Exactly:

- TREND10_DAILY;
- CRISIS10_DAILY;
- R009_COMBINED_DAILY;
- PERMANENT10_PLUS_CRISIS10_REF;
- STATIC10/15/20_DAILY;
- STATIC10/15/20_MONTHLY;
- CASH;
- ETH100.

No additional ETH-specific comparator or parameter grid.

## 5. Decision implementation

The engine implements the prospectively frozen SUPPORT / MIXED / FAIL gate in the protocol. A positive state can never be stronger than `UNCHANGED_RULE_SUPPORT`.

Any result may be interpreted only as historical cross-asset structural evidence. It does not reset or alter R009 BTC forward E002.

## 6. Output package

Nine user-facing result files under `R009_X001_ETH/results`:

1. `r009_x001_eth_run_state.json`
2. `r009_x001_eth_source_audit.json`
3. `r009_x001_eth_price_clean.csv`
4. `r009_x001_eth_state_daily.csv`
5. `r009_x001_eth_metrics.csv`
6. `r009_x001_eth_state_diagnostics.csv`
7. `r009_x001_eth_crisis_events.csv`
8. `r009_x001_eth_shock_diagnostics.csv`
9. `r009_x001_eth_summary.md`

Local cache/snapshot/engine files do not need to be uploaded.

## 7. Pre-result technical checks

Before publication, the engine source was syntax-compiled locally and its state/simulation/metrics functions were exercised on a synthetic positive daily price path. No ETH market result was inspected during this check.

## 8. No-result-chasing rule

After X001 output inspection, do not rescue it by changing asset, source, SMA, sleeve sizes, crisis thresholds, reset rule, comparator set, costs, slice construction, or decision gate. Do not open a broad coin sweep to find a positive replacement.
