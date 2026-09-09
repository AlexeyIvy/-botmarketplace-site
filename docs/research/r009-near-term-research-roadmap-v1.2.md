# R009 / R003 Near-Term Research Roadmap v1.2

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-09  
**Status:** R009 forward frozen; R003-E001 structural funding signal present; R003-E002 implementation study next  
**Research posture:** antifragility-first, falsification-first, orthogonal-edge priority

## 1. Primary forward candidate — R009

R009 v0.1 remains the primary active strategy candidate.

Formal E001 status:

> **PROMISING_SCREEN / ADVANCE TO FORWARD PAPER**

R009-E002 forward inception remains fixed at 2026-09-10 00:00 UTC. It must not be reset or retuned because of R003 results.

The original BTC SMA120 forward control also continues unchanged.

## 2. R003-E001 result

Canonical result:

`docs/research/r003-e001-results-v0.1.md`

Formal structural conclusion:

> **STRUCTURAL_SIGNAL_PRESENT**

Separate stress compatibility classification:

> **CRISIS_FINANCING_COMPATIBLE, WITH MATERIAL STRESS COMPRESSION**

Key facts:

- 7,608 realized BTCUSDT funding observations from 2019-10-01 to 2026-09-09;
- FULL_AVAILABLE normalized short-funding simple sum ~+80.54%;
- completed years 2020-2025 all positive;
- largest completed positive year share ~39.77%, below the frozen 50% concentration ceiling;
- all qualifying rolling 365d funding windows positive;
- POST_2023 funding remains positive but substantially lower than 2020-2022;
- worst historical 30d normalized short funding about -1.31%;
- longest negative-funding streak 24 events, roughly eight days;
- deep-drawdown average funding remains positive, but at a much lower level than calm-market funding.

Interpretation discipline:

E001 establishes a structural historical funding premium, **not** executable strategy alpha.

## 3. Immediate parallel step — R003-E002

Protocol:

`docs/research/r003-e002-self-financing-cash-carry-protocol-v0.1.md`

Implementation freeze:

`docs/research/r003-e002-implementation-freeze-v0.1.md`

Frozen engine commit:

`84ab935899b22b8610d7184b192a1b5e8e6df36d`

Mobile launcher commit:

`b159199cc93bff3205eaf68741ebb19f3acdfc53`

E002 tests a conservative unconditional implementation:

- 50% NAV long BTC spot;
- 50% NAV USDT futures collateral;
- equal-BTC BTCUSDT perpetual short;
- no external borrowing;
- no cross-margin assumption;
- 1h spot / perpetual / mark-price data;
- actual historical basis movement;
- realized funding;
- UTC month-end rebalance only;
- two-leg execution costs;
- separately tracked futures-margin headroom;
- ZERO_FUNDING and ADVERSE_FUNDING ablations;
- explicit 0/2.5/5% capital-efficiency hurdles.

No funding threshold or leverage optimization is allowed.

## 4. Why recent carry matters

The E001 premium is not stationary in magnitude.

2020-2022 carry was much stronger than POST_2023, and 2026 YTD is weaker again.

Therefore E002 must not be judged mainly by the 2021 leverage boom. The key implementation question is whether POST_2023 fully funded net carry still earns enough after basis, margin and costs to justify risky exchange capital.

A positive historical funding sum is insufficient if the fully funded strategy earns less than a reasonable safe-capital hurdle.

## 5. R003-E002 decision path

### IMPLEMENTATION_PROMISING

If the conservative fully funded portfolio remains positive across PRE_2023 and POST_2023, survives cost/adverse-funding stress, keeps Max DD below the frozen 10% threshold, and never breaches the 10% conservative futures-collateral headroom:

- preserve R003 v0.1 unchanged;
- if POST_2023 capital efficiency is STRONG (>=5% CAGR), prepare a separate forward/shadow execution protocol;
- if only MARGINAL (2.5-5%), do not deploy merely because it is positive; compare against explicit safe-sleeve opportunity cost first.

### IMPLEMENTATION_MIXED

If carry is positive but margin/capital-efficiency/cost conditions are weak:

- no funding-threshold or leverage rescue on the same history;
- document whether forward-only observation is worth maintaining;
- otherwise close the implementation branch.

### IMPLEMENTATION_FAIL

If PRIMARY_2020 or POST_2023 net CAGR is non-positive, or canonical fully funded margin hard-fails:

- close unconditional fully funded BTC spot/perp carry as currently framed;
- do not optimize entry funding or leverage to rescue the same sample.

## 6. Carry-funded convexity remains conditional

Do not start option-combination research merely because E001 funding is positive.

Carry-funded convexity only becomes justified if R003 survives E002 implementation realism.

Even then, use:

> **realized accumulated carry -> ring-fenced premium budget -> bounded long-convexity spend**

not expected contemporaneous funding.

## 7. Safe-sleeve requirements remain separate

`docs/research/safe-sleeve-risk-requirements-v0.1.md`

Safe-sleeve priority remains:

1. availability in stress;
2. capital survival;
3. independence from crypto/exchange joint failure;
4. transfer reliability;
5. yield only afterward.

Do not contaminate R003 historical conclusions by assuming an idealized risk-free high-yield collateral asset.

## 8. Secondary work deliberately deferred

Still deferred:

- R005 breakout + volatility expansion;
- R006 cross-timeframe regime mining;
- R007 regime-filtered mean reversion;
- R008 threshold/recovery rescue;
- R009 parameter retuning;
- broad multi-coin search for a better-looking R009 result.

The unchanged-rule ETH R009 structural falsification remains useful later but is secondary to completing R003 implementation realism.

## 9. Priority hierarchy

1. **R009-E002 forward paper** — start/maintain at fixed inception.
2. **R003-E002 self-financing cash-and-carry implementation study** — run now.
3. **Original BTC SMA120 forward control** — continue unchanged.
4. **Safe-sleeve requirements** — maintain as a risk constraint.
5. If R003-E002 is genuinely promising, open forward/shadow R003 and only then consider ring-fenced carry-funded convexity.
6. ETH unchanged-rule R009 structural falsification can follow as a secondary test.
7. No nearby historical parameter rescue in R008/R009/R003.