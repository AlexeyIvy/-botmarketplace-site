# BotMarketplace Strategy-First Research Roadmap v2.0

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** R003 Bybit X001 completed MIXED; R009 ETH X001 frozen and ready; forward clocks unchanged  
**Research posture:** falsification-first, forward-aware, anti-overfitting, implementation-realism before real capital

## 1. Active forward records remain unchanged

### R009-E002

- BTC forward paper remains active from its original fixed inception;
- no parameter reset, rule change, or history restart;
- first snapshots are technical/plumbing checks only.

### R003-E003

- Binance BTC carry forward remains active from the fixed 2026-09-10 12:00 UTC decision boundary;
- exact 50/50 fully funded equal-BTC implementation unchanged;
- fixed and causal Treasury opportunity-cost benchmarks unchanged;
- no funding-threshold, leverage, collateral-split, or rebalance-frequency rescue.

### Original BTC SMA120 control

Continue independently and unchanged.

## 2. R003 Bybit X001 remains formally MIXED

Canonical result:

`docs/research/r003-bybit-x001-results-v0.1.md`

Formal conclusion:

> **STRUCTURAL_SIGNAL_MIXED**

Do not open Bybit X002 under the current decision because the prospectively frozen completed-year concentration gate failed. Do not relax the gate or shop for another venue.

R003 remains alive only through its already-frozen Binance forward record and as a qualitatively cross-venue-supported carry mechanism whose recent capital efficiency is still uncertain.

## 3. Immediate historical falsification — R009 ETH X001

Protocol frozen before result inspection:

`docs/research/r009-x001-eth-unchanged-rule-structural-falsification-protocol-v0.1.md`

Protocol commit:

`1cd6e91791c739a5a7bc27bfefcfedc074e22030`

Frozen engine:

`research/r009/r009_x001_eth_structural_falsification.py`

Engine commit:

`70994fac3023a9662f538208bd3fce7fba3051e6`

Implementation freeze:

`docs/research/r009-x001-eth-implementation-freeze-v0.1.md`

Mobile launcher:

`research/r009/r009_x001_eth_structural_falsification_mobile.py`

Launcher commit:

`d17151a3178687bbafac0884655312dae7cc65ab`

Purpose:

> determine whether the exact R009 BTC architecture retains useful growth/drawdown structure on ETH without any ETH-specific parameter change.

Frozen invariants:

- ETHUSDT only;
- Binance Spot daily fully closed bars;
- SMA120 trend sleeve 0/10%;
- crisis sleeve 0-10% in 2.5pp tranches;
- -20/-35/-50/-65% running-ATH triggers;
- sticky until new ATH;
- additive sleeves;
- maximum target 20%;
- self-financing daily-target accounting;
- 5/10/25/50 bps cost grid;
- zero cash yield;
- no leverage/funding/staking/lending;
- no broad coin sweep.

Maximum positive result is `UNCHANGED_RULE_SUPPORT`; this is historical structural evidence only.

## 4. R009 ETH interpretation rule

If X001 SUPPORTS:

- R009 gains evidence of cross-asset structural portability;
- do not retune it;
- compare BTC/ETH state behavior and risk efficiency;
- keep BTC forward primary;
- proceed toward capital-granularity and demo-readiness assessment only after forward plumbing is technically stable.

If X001 is MIXED:

- document exactly which frozen gates fail;
- do not tune ETH parameters;
- retain BTC forward and treat R009 portability as uncertain.

If X001 FAILS:

- do not search SOL/XRP/other coins for a positive replacement;
- keep the independent BTC forward record unchanged;
- downgrade the claim from broad architecture to BTC-specific candidate until forward evidence says otherwise.

## 5. Forward execution today remains mandatory

At the already scheduled time run the combined R009-E002 + R003-E003 forward launcher.

The first output is for:

- inception verification;
- causal state initialization;
- funding/price mapping;
- output persistence;
- data-source integrity.

Do not judge strategy quality from the first hours/days.

## 6. After ETH X001

Next decision is based on evidence, not a preselected desire to continue a family.

- Compare R009 BTC and ETH unchanged-rule evidence.
- Keep R003 forward accumulating regardless of Bybit MIXED.
- Do not open new R003 historical rescue variants.
- Do not open a broad cross-asset sweep for R009.
- If R009 remains the strongest candidate, next practical gate is Capital Granularity & Capacity Audit followed by minimal demo execution planning.
- If R009 cross-asset evidence materially weakens the case, return to the candidate registry and open a genuinely orthogonal edge hypothesis rather than retuning R009.

## 7. Safe sleeve

Safe-Sleeve S001 architecture remains valid but detailed S002 remains deferred until a leading candidate approaches demo/implementation eligibility.

The safe sleeve becomes mandatory before real-capital promotion and must preserve stress availability, off-venue survival, transfer reliability, and independence from exchange/collateral common-mode failure.

## 8. Capital granularity / capacity

Before demo/tiny-live promotion of a surviving candidate quantify:

- minimum mechanically executable capital;
- minimum economically sensible capital;
- minQty/minNotional/qtyStep effects;
- residual target/hedge error;
- skipped trades;
- fees/slippage by capital tier;
- margin headroom where relevant;
- maximum prudent capacity and venue concentration.

## 9. Demo and platform freeze

Demo may begin as a parallel execution-validation channel only after a candidate has strong historical implementation evidence, independent falsification evidence, and technically stable forward initialization.

Broad BotMarketplace development remains frozen. Only minimal one-strategy demo tooling is allowed when justified by a surviving candidate.

## 10. Current execution order

1. Run R009-X001 ETH unchanged-rule structural falsification now.
2. At the scheduled time run the combined R009-E002 + R003-E003 forward tracker.
3. Inspect ETH X001 with the prospectively frozen decision gate; no rescue tuning.
4. Inspect the first forward outputs technically only.
5. Compare R009 BTC/ETH structural evidence.
6. If R009 remains leading, prepare Capital Granularity & Capacity Audit and then minimal demo execution validation.
7. Continue R003 forward; no Bybit X002 under the current MIXED X001 result.
8. Open Safe-Sleeve S002 before any real-capital implementation.
9. Tiny live and broad platform development remain later explicit gates.

## 11. Explicit prohibitions

Do not:

- retune R009 for ETH;
- search multiple coins and select the prettiest result;
- relax Bybit R003 X001 gates;
- open Bybit X002 despite the frozen MIXED result;
- reset R009/R003 forward clocks;
- infer profitability from the first forward snapshot;
- add leverage merely to raise return;
- restart broad BotMarketplace feature development;
- call any current candidate proven antifragile or production-safe.
