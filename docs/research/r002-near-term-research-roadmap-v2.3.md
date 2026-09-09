# BotMarketplace Research Roadmap v2.3 — Transition to R008

**Project:** BotMarketplace strategy research  
**Date:** 2026-09-09  
**Status:** R002 broad-universe falsification complete; new antifragility branch opened  
**Research posture:** falsification-first, no result chasing, no hidden parameter optimization

## 1. R002 canonical status

Canonical corrected wide-universe result:

`docs/research/r002-wide-universe-validation-results-v0.2.md`

Final broad-universe decisions:

- SMA120 complete archive-defined equal-sleeve deployment: **FINAL REDESIGN / NOT PASS**;
- Donchian 100/50 complete archive-defined equal-sleeve deployment: **FINAL REDESIGN / NOT PASS**;
- episode correction did not materially change the result;
- no broad-universe rescue tuning is permitted on the same sample.

The existing frozen BTC SMA120 forward record continues independently and is not reset.

Donchian 100/50 remains useful research evidence about slow trend/downside control but does not start a formal forward clock.

## 2. R001 status

R001 Antifragile Convex Barbell remains **REDESIGN / PAUSED**.

What survived conceptually:

- cash-heavy / low-beta capital preservation is economically meaningful;
- true long convexity can provide crisis benefit;
- antifragility must be assessed by how benefit changes with shock magnitude, not by CAGR alone.

What did not validate in the tested implementation:

- static option protection had excessive premium drag;
- volatility-value filters did not establish robust late-period economics.

Do not restart the same option implementation without genuinely better option/carry data or a new pre-specified hypothesis.

## 3. New active branch — R008

New research candidate:

**R008 — Antifragile Crisis-Opportunity Barbell**

Frozen protocol:

`docs/research/r008-antifragile-crisis-opportunity-barbell-protocol-v0.1.md`

Why R008 instead of R004:

The existing strategy registry already reserves R004 for `IV-RV / Volatility Risk Premium`. The new crisis-opportunity architecture therefore receives the next new candidate ID rather than overwriting historical registry semantics.

## 4. R008-E001 purpose

R008-E001 is a narrow Stage-3 sanity screen.

It asks:

> Does a cash-heavy BTC portfolio that starts with 10% BTC and deploys another pre-budgeted 10% in four equal tranches as closing drawdown reaches -20%, -35%, -50%, and -65% improve geometric growth and crisis behavior relative to simpler static BTC/cash allocations?

Frozen architecture:

- 10% permanent BTC exposure;
- 10% opportunity reserve;
- 80% core cash;
- four 2.5 percentage-point crisis tranches;
- thresholds: -20/-35/-50/-65% from running closing ATH;
- each tranche triggers once per drawdown episode;
- all crisis tranches remain deployed until a new closing ATH;
- then reset to 10% BTC and rebuild the full reserve;
- no leverage;
- no shorting;
- cash return = 0 in E001;
- signal at close t applies to return t+1;
- costs: 5/10/25/50 bps, 10 bps baseline.

## 5. Mandatory E001 benchmarks

- CASH 100%;
- STATIC10: 10% BTC / 90% cash;
- STATIC20: 20% BTC / 80% cash;
- BTC100 contextual benchmark.

R008 must justify its state-machine complexity relative to STATIC10 and STATIC20.

## 6. Antifragility diagnostics

Do not judge E001 by CAGR alone.

Required:

- full-period and post-2023 metrics;
- per-year returns;
- mechanically detected crisis episodes;
- deepest threshold reached per episode;
- R008 benefit vs STATIC10 and STATIC20 during each crisis episode;
- dry-powder utilization;
- exposure distribution;
- cost stress;
- whether deeper stress creates coherent incremental benefit or merely increases damage.

## 7. E001 decision gate

### PROMISING

Only means: worth acquiring longer independent BTC history and conducting stronger validation.

A promising result should broadly show:

- CAGR above STATIC10;
- Max DD materially below STATIC20;
- better Calmar / Pareto tradeoff than both simple controls;
- post-2023 consistency;
- cost robustness;
- crisis benefit not dominated by one event;
- meaningful use of dry powder.

### REDESIGN

Use if crisis behavior is partly useful but static allocations are economically comparable/better, the recovery/reset mechanism is problematic, or the 2020-2026 event sample is too thin for a conclusion.

### FAIL

Use if the architecture does not beat STATIC10 geometrically, takes STATIC20-like drawdown without compensating growth, deeper crises worsen incremental outcomes, or the result depends almost entirely on one crash/recovery.

No E001 parameter rescue after results.

## 8. Research sequence from here

1. Preserve R002 v0.2 as final broad-universe evidence.
2. Freeze R008 v0.1 protocol before results — complete.
3. Implement and synthetic-test one reproducible R008-E001 engine.
4. Run E001 on BTCUSDT from the already validated Binance archive dataset.
5. Review full, post-2023, costs, yearly and crisis-event diagnostics.
6. Assign PROMISING / REDESIGN / FAIL.
7. If PROMISING, acquire longer independent BTC spot history before stronger claims.
8. Only after a longer-history pass consider separate branches such as trend + dry powder, carry-financed convexity, or true option convexity.

## 9. Anti-overfitting freeze remains active

Do not use R008-E001 results to tune:

- crisis thresholds;
- tranche sizes;
- permanent BTC weight;
- reset rule;
- technical indicators;
- volatility filters;
- per-crisis overrides.

A changed architecture requires a new R008 version and a new pre-result protocol.
