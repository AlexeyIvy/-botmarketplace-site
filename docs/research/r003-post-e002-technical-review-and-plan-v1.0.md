# R003 Post-E002 Technical Review & Plan v1.0

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** E002 IMPLEMENTATION_PROMISING / recent capital efficiency MARGINAL  
**Research posture:** falsification-first; no leverage or funding-threshold rescue

## 1. Executive conclusion

R003-E002 materially strengthened the case that BTCUSDT funding carry has historically been economically real after basis movement, two-leg execution costs, monthly re-hedging and a separately tracked futures-collateral account.

It did **not** prove that the strategy is antifragile, risk-free, or currently attractive enough for live capital.

The correct state is:

> **historically implementation-promising carry mechanism, but recent capital efficiency is marginal and forward evidence is required.**

## 2. What E002 actually established

At the frozen 10 bps/leg baseline on PRIMARY_2020:

- CAGR ~6.60%;
- Max DD ~-1.33%;
- ending multiple ~1.533x;
- no modeled hard margin failure;
- minimum conservative intrahour collateral ratio ~18.45%;
- funding contribution ~+0.5529 NAV;
- pair/basis price P&L ~-0.0022 NAV;
- execution cost ~-0.0175 NAV.

ZERO_FUNDING produced negative CAGR, while realized funding produced positive CAGR. The historical economic source is therefore funding rather than hidden directional BTC beta in the modeled pair.

POST_2023 CAGR fell to ~3.74%, and the latest one-year realized path is substantially weaker than the long-run average. Current economics must therefore be judged separately from the 2020-2021 leverage boom.

## 3. Critical correction: survival is not antifragility

The low modeled drawdown and absence of hard margin failure demonstrate resilience **inside the frozen simulator assumptions**.

They do not demonstrate full real-world survival because E002 still does not model:

- exchange insolvency / withdrawal freeze;
- USDT impairment or depeg;
- exact Binance tiered maintenance-margin and liquidation engine;
- order-book discontinuities beyond the fixed bps execution stress;
- API outage and two-leg execution failure;
- intrahour path ordering beyond the conservative mark-high diagnostic;
- legal/tax/account-access constraints.

Therefore do not say "R003 cannot go bankrupt" or "R003 is antifragile." Say:

> **R003 was low-drawdown and margin-surviving in the historical implementation model.**

## 4. Inflation is contextual, not the primary opportunity-cost hurdle

Inflation measures purchasing-power erosion. It is not the best direct comparator for choosing between R003 and a low-risk cash alternative.

The primary economic hurdle should be a short-duration U.S. Treasury bill yield because the relevant question is:

> Why take Binance/USDT/margin/legging risk if safer short-duration USD capital earns a comparable return?

Inflation remains a secondary real-return diagnostic.

A separate dated hurdle snapshot records the current reference rates before R003 forward evaluation.

## 5. Risk premium above the safe hurdle

Merely beating a Treasury bill by a few basis points is not sufficient compensation for R003-specific tail risks.

Forward reporting will therefore show two non-optimized diagnostics:

1. excess return versus the frozen inception 13-week Treasury-bill reference;
2. excess return versus that reference +2.00 percentage points.

The +2pp level is a conservative research compensation floor, not a claim of theoretically optimal required return and not a tunable parameter.

Interpretation:

- below Treasury hurdle: economically unattractive versus the reference safe alternative;
- Treasury to Treasury+2pp: positive spread but still marginal compensation for venue/collateral risk;
- above Treasury+2pp: economically interesting, subject to forward persistence and operational validation.

No live allocation follows automatically from any tier.

## 6. Critical correction: R003 and R009 are not fully independent risks

R003 funding carry and R009 directional/trend-crisis architecture have different return mechanisms, but they can share correlated operational failure modes if implemented through the same venue/collateral ecosystem.

Potential common-mode risks include:

- Binance access or insolvency;
- USDT impairment;
- crypto-market infrastructure outage;
- transfer restrictions during crisis.

Therefore portfolio diversification must be evaluated on two axes:

- **economic return-source diversification**;
- **operational/custody failure diversification**.

A future combined portfolio must preserve a material off-venue safe reserve. R003 collateral must never be relabeled as the safe sleeve merely because the position is approximately delta-hedged.

## 7. No historical profit enhancement of R003 v0.1

Do not increase historical CAGR by searching:

- leverage;
- lower futures collateral;
- funding-entry thresholds;
- funding moving averages;
- funding forecasts;
- rebalance-frequency grids;
- alternative BTC trend filters;
- selective years;
- venue selection after seeing results.

R003 v0.1 is frozen.

If forward evidence later shows weak economics, the correct conclusion is weak/negative forward evidence, not parameter rescue on the same sample.

## 8. Next evidence stage — R003-E003 forward paper

Open a genuine forward paper record with fixed inception after this review.

Objectives:

- preserve the exact E002 50/50 fully funded construction;
- record future realized Binance funding, basis, margin headroom and execution-cost assumptions;
- compare against frozen safe-capital hurdles;
- accumulate evidence without moving inception or changing rules.

No terminal positive strategy decision before at least 365 calendar days of forward evidence.

Monthly descriptive reviews are allowed because the strategy mechanically rebalances monthly, but no rule may change at a review.

## 9. R009 remains independent forward candidate

R009-E002 remains frozen from its original inception and must be maintained unchanged.

R003 results do not alter R009 parameters, history, or forward clock.

The original frozen BTC SMA120 forward control also continues independently.

## 10. Safe-sleeve implementation priority

Do not optimize safe-sleeve yield yet.

Before live portfolio design require:

1. stress availability;
2. capital survival;
3. off-venue / common-mode failure diversification;
4. transfer reliability;
5. then yield.

The short Treasury yield is currently an **opportunity-cost benchmark**, not yet a production custody recommendation.

## 11. Carry-funded convexity remains conditional

Do not start buying options merely because historical funding was positive.

Only after R003 demonstrates sufficiently attractive forward excess carry should a new protocol evaluate:

> realized carry accumulated and ring-fenced -> bounded premium budget -> long convexity

Expected future funding must never be relied upon as a contemporaneous obligation to fund crash insurance.

## 12. Priority order

1. Start/maintain R009-E002 forward record unchanged.
2. Freeze and start R003-E003 forward paper record.
3. Track R003 against a Treasury safe-capital hurdle and a Treasury+2pp research compensation floor.
4. Maintain original BTC SMA120 forward control.
5. Do not retune R003/R009 on historical BTC data.
6. After sufficient forward evidence, evaluate operationally diversified combined portfolio architecture.
7. Carry-funded long convexity remains a later, separately frozen branch.