# R003-E001 — Funding Premium Structural Audit Results v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Candidate:** R003 — Funding / Basis Carry  
**Experiment:** E001  
**Date:** 2026-09-09  
**Status:** formal structural-premium audit result  
**Decision:** **STRUCTURAL_SIGNAL_PRESENT / ADVANCE TO E002 IMPLEMENTATION STUDY**  
**Crisis classification:** **CRISIS_FINANCING_COMPATIBLE, WITH MATERIAL STRESS COMPRESSION**  
**Protocol:** `docs/research/r003-e001-funding-premium-structural-audit-protocol-v0.1.md`

## 1. Executive decision

R003-E001 passes the frozen structural-premium gate.

Formal result:

> **STRUCTURAL_SIGNAL_PRESENT**

This is **not a strategy PASS** and is not an executable cash-and-carry return. E001 measures only the normalized realized BTCUSDT perpetual funding stream paid to the short side. Basis P&L, spot/perpetual execution, margin, liquidation, collateral transfers, legging, spreads/slippage and counterparty risk remain unmodeled.

The correct action is therefore to advance to a full self-financing implementation study rather than to production or forward capital deployment.

## 2. Data integrity

The run completed with `status=PASS`.

- funding source: Binance USD-M `BTCUSDT` realized funding history;
- funding observations: 7,608 raw / 7,608 clean;
- funding period: 2019-10-01 00:00 UTC -> 2026-09-09 16:00 UTC;
- observed cadence: effectively 8 hours, with only millisecond timestamp jitter;
- causal spot-state source: Binance Spot BTCUSDT daily closed bars;
- spot observations: 2,535;
- spot period: 2019-10-01 -> 2026-09-08 at run time;
- maximum spot calendar gap: 1 day;
- funding rows without a causally available prior closed spot bar: 3 initial observations only.

The causal stress classification therefore passes the intended data audit.

## 3. Structural funding result

### FULL_AVAILABLE

- simple normalized short-funding sum: **+80.54%**;
- descriptive compounded funding index gain: **+123.71%**;
- positive funding observations: **85.62%**;
- median rolling-365d funding sum: **+8.78%**;
- positive rolling-365d share: **100%**;
- worst qualifying rolling-365d sum: **+3.27%**.

### PRIMARY_2020

- simple sum: **+78.85%**;
- descriptive compounded: **+119.96%**;
- positive funding observations: **85.92%**;
- median rolling-365d sum: **+8.34%**;
- positive rolling-365d share: **100%**.

### Regime split

PRE_2023 (2020-2022):

- simple sum: **+52.01%**;
- median rolling-365d sum: **+21.95%**.

POST_2023:

- simple sum: **+26.84%** through 2026-09-09;
- median rolling-365d sum: **+7.17%**;
- positive rolling-365d share: **100%**.

The premium therefore persists after 2023 but is materially smaller than in the 2020-2022 leverage boom. This decay is economically important and must be carried into E002. E001 does not justify assuming the early-period funding level is the long-run expectation.

## 4. Calendar-year stability and concentration

Completed calendar years 2020-2025 were all positive in normalized short funding:

| Year | Simple funding sum | Positive observations |
|---|---:|---:|
| 2020 | +17.24% | 85.70% |
| 2021 | +30.61% | 92.69% |
| 2022 | +4.16% | 77.90% |
| 2023 | +7.87% | 89.86% |
| 2024 | +11.96% | 91.62% |
| 2025 | +5.13% | 87.12% |

2021 is the largest positive completed year and contributes about **39.77%** of total positive completed-year funding, below the prospectively frozen 50% concentration ceiling.

2026 through the run date is also positive (+1.89%) but is incomplete and is not used as a completed-year gate. Its lower mean funding rate is nevertheless a warning that recent carry has compressed further.

## 5. Negative-funding risk is real

The structural premium is positive but not monotonic.

Across FULL_AVAILABLE:

- worst single funding observation: **-0.30%**;
- worst rolling 7d cumulative funding: **-1.01%**;
- worst rolling 30d: **-1.31%**;
- worst rolling 90d: **-0.39%**;
- longest consecutive negative-funding streak: **24 funding observations**, roughly eight days at the standard cadence.

The largest historical negative streak occurred during the March 2020 crash region. Therefore future implementation must be able to survive a period in which the short perpetual both consumes funding and experiences adverse margin/basis dynamics.

## 6. Drawdown-state result

Causally classified funding by BTC closing drawdown:

| BTC drawdown state | Obs | Mean funding | Median funding | Positive fraction |
|---|---:|---:|---:|---:|
| 0 to -10% | 2,154 | 0.0228% | 0.0100% | 95.40% |
| -10 to -20% | 1,170 | 0.0095% | 0.0100% | 86.67% |
| -20 to -35% | 1,143 | 0.0067% | 0.0092% | 84.78% |
| -35 to -50% | 1,467 | 0.0039% | 0.0056% | 74.10% |
| -50% or worse | 1,671 | 0.0041% | 0.0050% | 82.94% |

Under the frozen E001 rule, the combined deep-drawdown region is classified:

> **CRISIS_FINANCING_COMPATIBLE**

because the weighted mean and representative median sign are non-negative.

However, the stronger economic interpretation is narrower: **funding compresses sharply in stress**. Mean funding in the deepest buckets is only a small fraction of the calm-market mean, and historical crash windows can temporarily turn funding materially negative. Therefore contemporaneous funding must not be relied upon to pay for protection exactly when a crisis occurs.

Any later carry-funded convexity design must use a pre-earned, ring-fenced premium budget.

## 7. Frozen gate evaluation

1. FULL_AVAILABLE cumulative short funding positive: **PASS**.
2. PRE_2023 positive: **PASS**.
3. POST_2023 positive: **PASS**.
4. Majority of completed calendar years positive: **PASS** (6/6).
5. Median rolling-365d funding positive: **PASS**.
6. More than half of rolling-365d windows positive: **PASS** (100%).
7. No single positive completed year >=50% of total positive completed-year funding: **PASS** (largest ~39.77%).

Formal structural result:

> **STRUCTURAL_SIGNAL_PRESENT**

## 8. What E001 proves and does not prove

E001 supports the existence of a persistent historical BTCUSDT funding premium paid to the normalized short-perpetual side across multiple regimes.

It does **not** prove that a realizable long-spot / short-perpetual portfolio has attractive net returns. In particular, an apparently delta-offset pair can still lose or fail operationally through:

- spot/perpetual basis divergence;
- futures margin depletion / liquidation before offsetting spot gains can be mobilized;
- collateral-transfer constraints;
- two-leg execution costs and legging;
- funding sign reversal;
- exchange/custody or stablecoin failure;
- opportunity cost of capital tied up in spot and collateral.

## 9. Next step — R003-E002

Advance to a frozen **self-financing cash-and-carry implementation study**.

E002 must not optimize a funding-entry threshold after seeing E001. The first implementation test remains unconditional / always-on once initialized.

The implementation study must explicitly include:

- equal-BTC long spot and short USD-M perpetual legs;
- a fully funded capital convention rather than hidden leverage;
- actual spot/perpetual price divergence and basis P&L;
- realized funding cash flows;
- explicit two-leg trading costs;
- periodic deterministic re-hedging / capital rebalancing specified before results;
- separate futures margin-account tracking and intraperiod margin-headroom diagnostics;
- stress for negative funding, basis widening and execution costs;
- recent-period economics, because funding has compressed materially after 2021;
- a capital-efficiency / safe-yield hurdle rather than treating tied-up capital as free.

Only after E002 can R003 be classified as an implementation candidate, redesign, or reject.