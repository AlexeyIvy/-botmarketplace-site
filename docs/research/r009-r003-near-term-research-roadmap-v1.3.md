# R009 / R003 Near-Term Research Roadmap v1.3

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** R009 forward frozen; R003-E002 implementation promising with marginal recent capital efficiency  
**Research posture:** antifragility-first, falsification-first, forward evidence priority

## 1. R009

R009 v0.1 remains the primary directional/portfolio candidate.

- E001 status: PROMISING_SCREEN.
- E002 forward inception remains fixed at 2026-09-10 00:00 UTC.
- No parameter reset or retuning because of R003.
- Original BTC SMA120 forward control continues independently.

## 2. R003-E002 canonical result

Canonical result:

`docs/research/r003-e002-results-v0.1.md`

Formal status:

> **IMPLEMENTATION_PROMISING**

Qualifier:

> **POST_2023 CAPITAL EFFICIENCY = MARGINAL**

Baseline 10 bps/leg:

- PRIMARY_2020 CAGR ~6.60%, Max DD ~-1.33%, ending ~1.533x;
- PRE_2023 CAGR ~10.14%;
- POST_2023 CAGR ~3.74%, Max DD ~-1.10%;
- PRIMARY minimum conservative intrahour collateral ratio ~18.45%;
- no low-headroom or hard-margin failure.

Funding is the economic source: ZERO_FUNDING PRIMARY CAGR is ~-0.23%, while REALIZED_FUNDING is ~+6.60%.

## 3. Important caution

Recent funding economics are much weaker than 2020-2021.

- POST_2023 baseline CAGR is only ~3.74%;
- POST_2023 adverse-funding CAGR is ~1.41%;
- descriptive trailing-365-day canonical NAV return at the frozen endpoint is only ~1.50%;
- 2026 YTD through the historical cutoff is ~0.80% cumulative.

Therefore R003 is preserved, but historical success does not justify immediate capital deployment or option-premium spending.

## 4. Next R003 stage

Open a forward/shadow R003 record only with the exact frozen implementation economics.

Forward work should record:

- live BTCUSDT spot and perpetual prices;
- mark price and realized funding;
- actual/executable bid-ask snapshots where available;
- intended equal-BTC hedge quantities;
- futures collateral and liquidation headroom;
- modeled versus executable two-leg entry/rehedge/exit costs;
- cumulative funding, pair/basis P&L and NAV;
- contemporaneous safe-sleeve opportunity-cost benchmark.

No positive-funding activation threshold, leverage tuning or collateral optimization is allowed.

## 5. Safe-sleeve comparison becomes mandatory

Because recent fully funded carry is only marginal, R003 must now be judged against a real safe-capital opportunity cost before production promotion.

This comparison is an implementation/economic hurdle, not a historical rescue parameter.

Priority order for the safe sleeve remains:

1. stress availability;
2. capital survival;
3. independence from crypto/exchange joint failure;
4. transfer reliability;
5. yield.

## 6. Carry-funded convexity remains deferred

Do not yet open a production-style carry-funded option strategy.

Only if R003 forward/shadow evidence remains economically useful after safe-sleeve opportunity cost should a new candidate be specified as:

> accumulated realized carry -> ring-fenced premium budget -> bounded long convexity

The premium budget may not depend on contemporaneous future funding remaining positive in a crash.

## 7. Immediate priority hierarchy

1. Start/maintain R009-E002 forward paper from its already frozen inception.
2. Freeze R003 forward/shadow protocol before counting any new R003 performance.
3. Continue original BTC SMA120 forward control.
4. Compare R003 economics with explicit safe-sleeve opportunity cost.
5. Do not retune R003/R008/R009 on inspected history.
6. Carry-funded convexity remains conditional on forward R003 support.
7. ETH unchanged-rule R009 structural falsification remains secondary.