# R009-E001 — Implementation Freeze v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Candidate:** R009 — Antifragile Trend-Gated Dry-Powder Barbell  
**Experiment:** E001  
**Date:** 2026-09-09  
**Status:** implementation frozen before official result review

## Frozen protocol

`docs/research/r009-e001-trend-gated-dry-powder-protocol-v0.1.md`

Protocol commit:

`eeb90d519f55b13e1ef71ab888ace989a1683e78`

## Frozen engine

`research/r009/r009_e001_trend_gated_dry_powder.py`

Exact engine commit:

`1240a9b9c399a7f7e1e5f6af7ecb33a00de365fa`

The mobile launcher must pin this exact commit.

## Frozen implementation details

- data source: Blockchain.com `market-price`, daily, unsampled;
- SMA lookback: 120 observations, current observation included;
- trend target: 10% when price > SMA120, else 0%;
- trend state at t applies to return t+1;
- crisis reserve: 10%;
- crisis tranches: 2.5pp x4;
- drawdown triggers: -20/-35/-50/-65% from running reference-price ATH;
- crisis tranches sticky until a new ATH;
- combined target = trend target + crisis target;
- total desired BTC target range: 0-20%;
- canonical accounting: self-financing daily target with natural weight drift before rebalance;
- baseline fee: 10 bps;
- stress: 5/10/25/50 bps;
- cash return: 0%;
- monthly STATIC10/15/20 are practical comparator implementations only;
- fixed-horizon diagnostics: 7/30/90/180/365 days after each first crisis-level breach;
- evaluation slices: FULL_AVAILABLE, PRIMARY_LONG 2013+, PRE_2020, REPLAY_2020, POST_2023.

## Code verification performed before freeze

Before committing the engine:

- Python syntax compilation passed;
- synthetic state-machine self-test passed;
- offline smoke test against the already-audited E004 cleaned series completed without runtime error;
- crisis events / breach counts reconciled structurally with prior R008 diagnostics;
- combined desired target remained within 0-20% in the smoke test.

No decision gate or engine rule may be changed after the official run based on its result.

## Evidence status

E001 is an in-sample mechanism screen because this BTC history has already been inspected during R002/R008.

Maximum positive status:

`PROMISING_SCREEN / ADVANCE TO FORWARD OR NEW-INDEPENDENT VALIDATION`

No historical PASS is possible from E001.