# R008 Near-Term Research Roadmap v1.3

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-09  
**Status:** E003 complete; R008 v0.2 REDESIGN / do not advance  
**Research posture:** antifragility-first, falsification-first, no serial rescue tuning

---

## 1. Current decision hierarchy

R008 v0.1 and v0.2 are now both closed as REDESIGN for their tested implementations.

- v0.1: crisis deployment worked, but ATH-only release trapped risk for years and was dominated by STATIC15 on independent pre-2020 evidence.
- v0.2: symmetric same-threshold release fixed trapped exposure, but STATIC15 still Pareto-dominated the strategy on PRE_2020_NEW and PRIMARY_LONG; crisis-event capture also weakened materially versus v0.1.

Canonical E003 result:

`docs/research/r008-e003-results-v0.1.md`

The broader antifragility thesis remains open because crisis Benefit10 stayed positive across all 18 closed long-history events and increased strongly with shock severity.

R002 broad-universe trend remains FINAL REDESIGN / NOT PASS. The BTC SMA120 frozen forward record continues independently as a control.

R001 tested option implementations remain paused/redesign.

---

## 2. What E003 established

The specific symmetric recovery rule achieved its structural goal:

- PRIMARY_LONG time at 20% BTC fell from ~58.3% to ~20.9%;
- PRE_2020_NEW time at 20% BTC fell from ~76.2% to ~30.1%;
- median maximum-exposure spell fell from ~630 days to ~8 days.

But the economic tradeoff was unfavorable:

- PRE_2020_NEW v0.2: CAGR ~17.50%, Max DD ~-20.05%, Calmar ~0.87;
- PRE_2020_NEW STATIC15: CAGR ~20.16%, Max DD ~-19.83%, Calmar ~1.02;
- PRIMARY_LONG v0.2: CAGR ~12.65%, Max DD ~-20.05%, Calmar ~0.63;
- PRIMARY_LONG STATIC15: CAGR ~14.08%, Max DD ~-19.83%, Calmar ~0.71.

STATIC15 therefore Pareto-dominates v0.2 on both required slices.

At 50 bps the same PRIMARY_LONG domination remains, so the failure is not an artifact of baseline cost assumptions.

---

## 3. What remains economically supported

Across all 18 closed crisis events under v0.2:

- Benefit10 positive fraction = 100%;
- mean Benefit10 rises with deepest level from ~+0.39% at Level 1 to ~+8.14% at Level 4;
- no single event explains >=50% of positive Benefit10.

This supports a narrower reusable research insight:

> Preserving cash before stress and increasing BTC exposure during deeper drawdowns can create an incremental crisis benefit relative to low constant exposure.

What has not yet been solved is how to combine that event benefit with superior whole-path economics versus simple static risk budgets.

---

## 4. Anti-overfitting closure

Do not create R008 v0.3 by immediately adding:

- hysteresis;
- cooldown;
- alternate recovery thresholds;
- nearby deployment thresholds;
- different tranche weights;
- different base/reserve weights;
- technical filters chosen to improve the already inspected historical result.

The release-rule family has now received two clean implementations and both fail to beat a simple static midpoint benchmark strongly enough for promotion.

---

## 5. Recommended next candidate — economically distinct branch

The next branch should change the economic architecture, not micro-tune R008 release logic.

Primary recommendation:

### R009 — Antifragile Trend-Gated Dry-Powder Barbell

Conceptual hypothesis only; not yet a frozen strategy:

- use a slow, pre-existing/frozen BTC trend mechanism as a **risk-state control**, not as a newly optimized alpha indicator;
- preserve substantial cash when the long-term state is adverse;
- allow a separately budgeted crisis-opportunity sleeve to deploy during severe drawdowns;
- separate survival logic from crisis-opportunity logic;
- compare against the same static BTC/cash controls and against each component separately.

Why this is economically distinct:

- R008 v0.1/v0.2 tried to solve both buying and release using drawdown state alone;
- R009 would use slow trend only to determine whether ordinary directional risk should remain active, while crisis buying remains a separate pre-budgeted mechanism;
- the frozen BTC SMA120 rule already exists independently, reducing freedom to invent a new technical parameter after seeing E003.

Important: this still requires a new pre-result protocol before any combined backtest. No combined rules are yet authorized.

---

## 6. Alternative later antifragility branches

If R009 is not pursued or fails, economically distinct candidates remain:

- carry-funded dry powder / carry-financed convexity using funding or basis history;
- true long-option convexity with denser historical option-chain data;
- cash-heavy portfolio with explicit non-directional carry and separately budgeted crisis exposure.

These require new data and independent protocols; they should not be mixed into R009 screening.

---

## 7. Immediate execution order

1. Preserve E003 output and `r008-e003-results-v0.1.md` as canonical closure of R008 v0.2.
2. Stop release-rule tuning on R008.
3. Keep the BTC SMA120 forward record running unchanged.
4. If continuing immediately, write a pre-result R009 economic/specification protocol before calculating combined P&L.
5. In R009, use ablations: static controls, frozen trend-only control, crisis-only control, then combined architecture.
6. Treat same-history R009 testing initially as a mechanism screen because components and historical BTC behavior are already known; require future/independent evidence before any strong PASS.

---

## 8. Plain-language interpretation

R008 taught us that the crisis-buying idea itself was not the main problem. Buying more during large drawdowns repeatedly helped relative to keeping only a small BTC allocation.

The first exit rule held that extra risk too long. The second exit rule released it faster but also gave away too much recovery return. A simple 15% BTC allocation still beat the state machine on the main long-history tradeoff.

That is enough evidence to stop tuning exit bands.

The next useful question should therefore be broader:

> Can we combine a simple survival mechanism for ordinary market regimes with a separately budgeted crisis-opportunity mechanism, rather than asking drawdown thresholds alone to manage the entire portfolio lifecycle?
