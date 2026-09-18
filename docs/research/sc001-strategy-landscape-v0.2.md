# SC001 — Strategy Landscape v0.2

Date: 2026-09-18  
Status: **CURRENT COVERAGE MAP AFTER C1-C6 SENTINEL BATCH / NON-ALPHA GOVERNANCE ARTIFACT**  
Supersedes: `sc001-strategy-landscape-v0.1.md`

## 1. Purpose

This document updates the SC001 horizon/mechanism/execution coverage map after the frozen C1-C6 Selection/Calibration sentinel batch.

It is descriptive, not a profitability ranking.

## 2. Prior terminal evidence remains immutable

E001-E009 and E007R1 remain terminal/closed exactly as previously recorded.

No old FAIL is reopened by this landscape update.

## 3. C1-C6 selection evidence now completed

### C1 — multi-asset same-venue spot/perp basis convergence

- mechanism/execution: M5 / T3;
- signal/position: S2-S4 / P2-P4;
- selection state: `REJECT_SENTINEL`;
- dominant limitation: zero frozen +50 bps dislocation triggers across the qualified multi-asset sandbox;
- coverage implication: strict E006-style basis-convergence scarcity is now tested beyond BTC and remains unfavorable under the frozen rule;
- no direct threshold/hold/filter rescue.

### C2 — multi-minute local-reference mean reversion

- mechanism/execution: M3 / T1;
- signal/position: S3 / P3;
- variants: two frozen local-reference representations;
- selection state: `REJECT_SENTINEL`;
- dominant limitation: abundant sample but negative signed reversion effect in both variants;
- coverage implication: simple multi-minute local-reference reversion is now directly covered with negative selection evidence;
- no volatility/trend/oscillator rescue under C2.

### C3 — 5m/10m continuation / volatility expansion

- mechanism/execution: M4 / T1;
- signal/position: S3-S4 / P3-P4;
- selection state: `REJECT_SENTINEL`;
- dominant limitation: abundant sample but near-zero/slightly negative continuation economics;
- coverage implication: basic completed-bar expansion/breakout continuation is now covered in the previously under-covered multi-minute region;
- no ADX/MACD/volume/flow/time filter rescue under C3.

### C4 — BTC/ETH -> alt lead/lag

- mechanism/execution: M6 / T1;
- signal/position: S1-S2 / P1-P2;
- selection state: `REJECT_SENTINEL`;
- dominant limitation: very large sample and broad positive residual signs, but residual magnitude only sub-1-bps versus 15 bps screen;
- 30-second raw-positive variants were consistent with common-beta rather than a viable residual lead/lag edge;
- coverage implication: simple same-venue BTC/ETH-to-alt short-lag transfer is now covered with negative economic evidence;
- no lag grid or target cherry-picking.

### C5 — large aggressive-flow / forced-flow exhaustion

- mechanism/execution: M7+M3 / T1;
- signal/position: S0-S2 / P1-P2;
- selection state: `REJECT_SENTINEL`;
- dominant limitation: >10k events and broad sign, but only sub-1-bps mean effect;
- coverage implication: trade-only forced-flow exhaustion is now covered and does not justify L2 rescue under the same mechanism.

### C6 — cross-sectional short-horizon dispersion/reversion

- mechanism/execution: M5/M6 / portfolio/T3-like;
- signal/position: S3-S4 / P3-P4;
- selection state: `REJECT_SENTINEL`;
- dominant limitation: good day breadth/concentration and positive tendency, but only low-single-digit gross spread versus 30 bps four-fill screen;
- coverage implication: simple equal-weight common-factor top1/bottom1 dispersion reversion is now covered with negative economic evidence;
- no factor/volatility/asset-selection rescue under C6.

## 4. Updated coverage diagnosis

### Relatively well covered with terminal/negative evidence

- ultra-short to 60-second order-flow and displacement families;
- short-horizon taker continuation/reversal;
- BTC passive maker/spread capture;
- multi-minute local-reference mean reversion;
- 5m/10m volatility-expansion continuation;
- strict same-venue spot/perp basis convergence;
- same-venue BTC/ETH -> alt short-lag transfer;
- trade-only forced-flow exhaustion;
- simple cross-sectional 5m dispersion/reversion.

The main new lesson is that many mechanisms show abundant activity or even directional sign consistency, but not enough raw magnitude to clear realistic structural execution reserves.

### Still materially under-covered or not yet cleanly tested

- M2 passive/hybrid liquidity provision on a **prospectively spread/fee-eligible non-BTC universe**;
- cross-venue relative value / cross-venue information transfer with genuinely independent venue clocks and execution;
- derivative-state mechanisms materially different from strict C1 basis convergence, e.g. funding/mark/index state, subject to exact data availability and cost mechanics;
- low-directional-beta mechanisms with fewer fills than C6's four-fill cycle;
- mechanisms whose economic edge arises from execution structure rather than tiny directional prediction;
- longer micro-intraday state changes that are not parameter-neighbor versions of C2/C3/C6.

Under-covered means only information gap, not expected profitability.

## 5. C7 reserve candidate

C7 — wider-spread maker family remains scientifically distinct from failed BTC E008 only if:

- universe is selected prospectively by spread/fee feasibility, not historical PnL;
- no BTC same-rule rescue is attempted;
- queue model is treated as execution uncertainty/scenario rather than exact FIFO truth;
- candidate receives a new ID and fresh selection evidence.

C7 is not automatically promoted merely because C1-C6 failed.

## 6. Next-slate design constraints

The next non-alpha slate must not be:

- C1 with lower basis threshold;
- C2 with a trend veto or different nearby hold;
- C3 with ADX/MACD/volume rescue;
- C4 with a lag/target grid;
- C5 with L2 added to rescue the same trade-only mechanism;
- C6 with factor/volatility/asset-selection tuning.

A new candidate must materially change at least one of:

- economic mechanism;
- execution architecture;
- market relationship;
- information source;
- risk signature;
- or horizon in a way that is not merely a neighboring parameter search.

## 7. Immediate next action

Before any new outcome:

1. append C1-C6 scoped evidence to the feature registry;
2. design a new candidate landscape from the remaining under-covered cells;
3. create non-alpha feasibility cards;
4. prioritize cheapest structural falsification;
5. freeze a new variant budget before any new sentinel output.

Protected holdout and Confirmation data remain closed.
