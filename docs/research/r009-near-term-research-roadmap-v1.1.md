# R009 Near-Term Research Roadmap v1.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-09  
**Status:** R009 forward frozen; R003 structural carry audit opened in parallel  
**Research posture:** antifragility-first, falsification-first, orthogonal-edge priority

## 1. Current primary candidate

R009 v0.1 remains the primary active strategy candidate.

Formal E001 status:

> **PROMISING_SCREEN / ADVANCE TO FORWARD PAPER**

The frozen R009-E002 forward record begins at the already-fixed inception and must not be reset or retuned because of any parallel research result.

The original BTC SMA120 forward control also continues independently.

## 2. Why parallel research is justified now

Forward evidence accumulates slowly. It is inefficient to stop all research while waiting, but parallel work should avoid another nearby BTC price-rule search.

Priority is therefore given to **orthogonal economic mechanisms** rather than additional SMA/breakout/regime variants.

The next branch is R003 Funding / Basis Carry because its potential payer is structurally different from directional BTC beta: leveraged derivatives demand and funding imbalance.

## 3. Technical-review correction before R003

Do not assume `long spot + short perpetual` is automatically market-neutral or safe.

Even with offsetting directional delta it still has:

- basis risk;
- margin/liquidation risk;
- collateral-transfer risk;
- legging/execution risk;
- counterparty/default risk;
- funding sign reversal.

Therefore R003 begins with a cheaper structural-premium falsification stage rather than a full portfolio backtest.

## 4. Immediate parallel experiment — R003-E001

Protocol:

`docs/research/r003-e001-funding-premium-structural-audit-protocol-v0.1.md`

Implementation freeze:

`docs/research/r003-e001-implementation-freeze-v0.1.md`

Frozen engine commit:

`e0b61f25df36b8edf8272551dd1ed75f8518bdbf`

Mobile launcher commit:

`fa50a01009377ba9894251da1620b2dbdfc7a3a3`

E001 tests only whether realized BTCUSDT short-side funding premium is persistent across regimes and whether it remains supportive or becomes adverse during deep BTC drawdowns.

It does **not** yet claim executable cash-and-carry P&L.

## 5. R003-E001 decision path

### STRUCTURAL_SIGNAL_PRESENT

Proceed to R003-E002, but freeze a full self-financing implementation protocol first.

E002 must then model:

- long spot + equal-BTC short perpetual;
- spot/perp basis P&L;
- actual fee/spread/slippage assumptions;
- funding cashflows at correct timestamps;
- collateral allocation and transfers;
- margin/liquidation stress;
- legging risk;
- exchange/counterparty scenarios;
- no hidden leverage increase.

### STRUCTURAL_SIGNAL_MIXED

Do not optimize a positive-funding threshold from inspected history. Prefer forward-only observation or close the branch.

### STRUCTURAL_SIGNAL_ABSENT

Close the current BTC funding-premium premise before spending effort on a complex execution engine.

## 6. Carry-funded convexity correction

Do not assume contemporaneous funding can pay option premium during crises.

Funding can compress or reverse exactly when market stress rises.

If R003 later survives implementation realism, the preferred future convexity architecture is:

> **realized accumulated carry -> ring-fenced premium budget -> bounded long-convexity spend**

not an open-ended dependence on expected future funding.

Any option implementation remains a separate later protocol and must not be retrofitted into R003.

## 7. Safe-sleeve track

Cross-strategy requirements are frozen in:

`docs/research/safe-sleeve-risk-requirements-v0.1.md`

Safe-sleeve research is currently a **requirements track**, not a product/yield optimization.

Priority order:

1. availability during stress;
2. capital survival;
3. independence from crypto/exchange joint failure;
4. transfer reliability;
5. yield only after the above.

No specific Treasury/stablecoin/custodian allocation is chosen until a candidate reaches implementation design.

## 8. Work deliberately deferred

Do not currently prioritize:

- R005 breakout + volatility expansion;
- R006 cross-timeframe regime mining;
- R007 regime-filtered mean reversion;
- another BTC SMA/lookback search;
- another R008 drawdown/recovery variant.

These add price-series degrees of freedom while R009 is already in forward validation.

## 9. Cross-asset R009 falsification

An unchanged-rule ETH structural test remains useful later, but it is secondary to R003.

If performed:

- choose ETH prospectively as the only first cross-asset test;
- do not sweep many coins and report winners;
- reuse R009 v0.1 parameters exactly;
- treat result as structural falsification, not temporal OOS.

## 10. Priority hierarchy

1. **R009-E002 forward paper** — wait for first closed forward bar, then maintain unchanged record.
2. **R003-E001 funding-premium structural audit** — immediate parallel research.
3. **Original BTC SMA120 forward control** — continue unchanged.
4. **Safe-sleeve requirements** — maintain as implementation constraint, no premature yield optimization.
5. If R003 structural signal is present, freeze and run R003-E002 realistic cash-and-carry.
6. Only after carry survives realism, evaluate ring-fenced carry-funded convexity as a new branch.
7. ETH unchanged-rule R009 structural test may follow as a secondary falsification exercise.
8. No nearby R008/R009 technical tuning on inspected BTC history.