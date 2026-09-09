# R008-E002 — Long-History Independent Validation Results v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Candidate:** R008 — Antifragile Crisis-Opportunity Barbell  
**Experiment:** E002  
**Date:** 2026-09-09  
**Status:** formal result after reviewing frozen E002 protocol  
**Decision:** **REDESIGN**  
**Protocol:** `docs/research/r008-e002-long-history-validation-protocol-v0.1.md`

---

## 1. Executive decision

R008 v0.1 does **not** receive HISTORICAL PASS.

Formal status:

> **REDESIGN**

The core crisis-opportunity mechanism remains economically interesting: incremental benefit versus STATIC10 is positive across all closed crisis events, scales strongly with crisis depth, survives 50 bps cost stress, and reproduces qualitatively on both pre-2020 and post-2020 history.

However, the frozen v0.1 architecture fails two central PASS requirements on the independent long-history evidence:

1. on `PRE_2020_NEW` a simple STATIC15 portfolio economically dominates R008 on the main CAGR / Max DD / Calmar comparison;
2. ATH-only reset leaves R008 at its maximum 20% BTC target for most of the long history, so the design ceases to behave like a cash-heavy barbell for extended periods.

This is exactly the protocol's REDESIGN case: crisis benefit exists, but a simple static benchmark is comparable or superior and long trapped exposure is problematic.

No threshold, tranche-size, base-weight or reset rescue is allowed inside R008 v0.1.

---

## 2. Data audit

Source: Blockchain.com `market-price` daily reference series.

Audit result: **PASS**.

- raw values: 6,459;
- clean positive observations: 5,867;
- clean range: 2010-08-18 -> 2026-09-09;
- duplicate clean dates: 0;
- all-history max gap: 1 day;
- PRIMARY_LONG start: 2013-01-01;
- PRIMARY_LONG observations: 5,000;
- PRIMARY_LONG one-day-gap share: 100%;
- PRIMARY_LONG long gaps >1 day: 0;
- PRIMARY_LONG missing calendar days: 0.

The state machine was initialized from the earliest valid source observation, as frozen before the run.

---

## 3. Frozen architecture

Unchanged from E001:

- permanent BTC target: 10%;
- crisis reserve: 10%;
- 4 x 2.5 percentage-point tranches;
- drawdown triggers: -20%, -35%, -50%, -65%;
- once triggered, tranche remains active until a new reference-price ATH;
- max BTC target: 20%;
- cash return: 0%;
- no leverage or shorts;
- no technical/trend/volatility filter;
- t state applies to t+1 return;
- fee stress: 5 / 10 / 25 / 50 bps.

STATIC15 was prospectively frozen before E002 as the midpoint causal benchmark.

---

## 4. Baseline headline metrics — 10 bps

### PRE_2020_NEW — primary new evidence, 2013-01-01 through 2019-12-31

| Strategy | CAGR | Max DD | Calmar | Ending | Avg BTC |
|---|---:|---:|---:|---:|---:|
| R008 | **19.67%** | **-22.99%** | **0.86** | 3.512x | 18.35% |
| STATIC10 | 13.24% | -13.54% | 0.98 | 2.386x | 10.00% |
| STATIC15 | **20.16%** | **-19.83%** | **1.02** | 3.613x | 15.00% |
| STATIC20 | 27.25% | -25.79% | 1.06 | 5.396x | 20.00% |

Key result: R008 beats STATIC10 on growth, but STATIC15 has **higher CAGR, smaller drawdown and higher Calmar simultaneously**. Therefore R008 is economically dominated by STATIC15 on the primary new evidence slice.

STATIC20 also has much higher CAGR and higher Calmar, with only a modestly deeper Max DD than R008.

### PRIMARY_LONG — 2013-01-01 onward

| Strategy | CAGR | Max DD | Calmar | Ending | Avg BTC |
|---|---:|---:|---:|---:|---:|
| R008 | **14.85%** | **-22.99%** | **0.65** | 6.649x | 17.08% |
| STATIC10 | 9.33% | -13.54% | 0.69 | 3.391x | 10.00% |
| STATIC15 | 14.08% | -19.83% | 0.71 | 6.064x | 15.00% |
| STATIC20 | 18.85% | -25.79% | 0.73 | 10.633x | 20.00% |

R008 has a small CAGR advantage over STATIC15, but gives it back through worse Max DD and worse Calmar. STATIC20 again has higher CAGR and Calmar with only moderately deeper drawdown.

### REPLAY_2020 — cross-source replay

| Strategy | CAGR | Max DD | Calmar |
|---|---:|---:|---:|
| R008 | **10.01%** | **-17.65%** | **0.57** |
| STATIC10 | 5.40% | -11.72% | 0.46 |
| STATIC15 | 8.05% | -17.19% | 0.47 |
| STATIC20 | 10.67% | -22.41% | 0.48 |

This is qualitatively compatible with E001 and confirms the post-2020 behavior was not a Binance-only artifact.

### POST_2023

| Strategy | CAGR | Max DD | Calmar |
|---|---:|---:|---:|
| R008 | **10.22%** | **-8.40%** | **1.22** |
| STATIC10 | 5.32% | -6.61% | 0.81 |
| STATIC15 | 8.00% | -9.80% | 0.82 |
| STATIC20 | 10.69% | -12.92% | 0.83 |

This remains a strong regime for the mechanism. It does not override the weaker independent pre-2020 economics.

---

## 5. Crisis-benefit evidence

Across all **18 closed** mechanically detected crisis events:

- Benefit10 positive fraction: **100%**;
- mean Benefit10 by deepest level:
  - Level 1: **+0.81%**;
  - Level 2: **+2.52%**;
  - Level 3: **+6.98%**;
  - Level 4: **+12.78%**.

This is a strong severity-response ordering.

On `PRE_2020_NEW` specifically:

- 7 closed events;
- Benefit10 positive in **7/7**;
- Level 1 mean Benefit10: **+0.85%**;
- Level 2: **+2.52%**;
- Level 4: **+14.36%**.

No single event explains the majority of positive Benefit10:

- largest positive-event share across all closed events: ~16%;
- largest positive-event share inside PRE_2020_NEW: ~32%.

The anti-fragility-style event mechanism therefore survives the independent earlier history.

Secondary comparisons are also coherent:

- shallow crises generally lag STATIC15/STATIC20;
- Level 4 crises produce positive mean benefit versus STATIC15 and STATIC20;
- on PRE_2020_NEW Level 4 mean benefit is about +8.95% vs STATIC15 and +3.73% vs STATIC20.

Thus the problem is not failure to buy deep crises. The problem is what happens **after** the crisis exposure is deployed.

---

## 6. Long trapped exposure — primary failure mode

ATH-only reset causes crisis tranches to remain deployed for extremely long periods.

Examples in PRE_2020_NEW:

- 2013-12-07 breach -> 2017-02-24 reset: **1,175 days**;
- 2017-12-23 breach -> 2020-12-01 reset: **1,074 days**.

As a result, target BTC exposure equals the maximum 20% for:

- ~58.4% of all source observations;
- ~58.3% of PRIMARY_LONG;
- **~76.2% of PRE_2020_NEW**.

Average BTC target on PRE_2020_NEW is ~18.35%.

This directly violates the intended barbell property that meaningful dry powder should remain available and the strategy should not spend most of history at maximum exposure.

The long-history result therefore reveals that R008 v0.1 behaves much more like a delayed transition toward STATIC20 than a persistent cash-heavy crisis-opportunity barbell.

---

## 7. Cost stress

Costs are not the failure mode.

R008 PRE_2020_NEW CAGR:

- 5 bps: 19.68%;
- 10 bps: 19.67%;
- 25 bps: 19.65%;
- 50 bps: 19.62%.

R008 PRIMARY_LONG CAGR:

- 5 bps: 14.85%;
- 10 bps: 14.85%;
- 25 bps: 14.83%;
- 50 bps: 14.79%.

Turnover is low, so even 50 bps does not erase the incremental mechanism.

---

## 8. Calendar-year interpretation

PRE_2020_NEW annual returns illustrate why the static midpoint benchmark matters.

| Year | R008 | STATIC10 | STATIC15 | STATIC20 |
|---|---:|---:|---:|---:|
| 2013 | +103.44% | +63.11% | +106.76% | +160.79% |
| 2014 | -10.75% | -5.99% | -9.03% | -12.10% |
| 2015 | +10.95% | +5.59% | +8.31% | +10.95% |
| 2016 | +19.82% | +9.60% | +14.63% | +19.82% |
| 2017 | +44.62% | +34.73% | +55.85% | +79.87% |
| 2018 | -14.63% | -8.29% | -12.41% | -16.48% |
| 2019 | +17.87% | +8.84% | +13.33% | +17.87% |

R008 often converges toward STATIC20 after deep drawdowns and then remains there through long recoveries. The static midpoint therefore captures much of the growth with a cleaner risk profile.

---

## 9. Formal decision against frozen criteria

### Criteria that pass

- PRE_2020_NEW R008 CAGR exceeds STATIC10: **PASS**.
- PRIMARY_LONG directionally consistent: **PASS**.
- Max DD remains below STATIC20: **PASS**.
- 25-50 bps cost stress does not erase the edge: **PASS**.
- Benefit10 positive across broad majority of events: **strong PASS, 100% closed events**.
- no single event dominates Benefit10: **PASS**.
- severity-response economically coherent: **strong PASS**.
- REPLAY_2020 compatible with E001: **PASS**.

### Criteria that fail for HISTORICAL PASS

- not dominated by STATIC15/20 on PRE_2020_NEW: **FAIL** — STATIC15 dominates R008 on CAGR, Max DD and Calmar.
- Calmar competitive with STATIC15/20 on main slices: **FAIL**.
- dry powder materially available / not most history at 20% BTC: **FAIL** — 20% target ~58% of PRIMARY_LONG and ~76% of PRE_2020_NEW.

### Final

**R008 v0.1 = REDESIGN.**

This is not a FAIL of the broader antifragility thesis. The data supports a narrower statement:

> Pre-committed crisis buying produces a robust, severity-ordered incremental benefit versus low static exposure, but an ATH-only release rule keeps the added risk deployed too long and destroys the intended cash-heavy barbell advantage over simple midpoint allocation.

---

## 10. What must not happen next

Do not tune within v0.1:

- -20/-35/-50/-65 thresholds;
- 2.5% tranche sizes;
- 10% base;
- 10% reserve;
- ATH reset threshold by searching nearby values;
- event-specific exits;
- indicator filters chosen to improve these results.

The v0.1 record is closed as REDESIGN.

---

## 11. Recommended next research direction

If R008 continues, create a **new version**, not a rescue tweak.

The cleanest economically motivated hypothesis is a recovery-release / symmetric drawdown ladder:

- retain the same 10% base, 10% reserve and same four drawdown thresholds for comparability;
- deploy tranches as stress deepens;
- release tranches again as the current drawdown recovers back through the same pre-specified thresholds, instead of waiting for a new ATH;
- add no new numerical thresholds in the first redesign test.

This changes the economic mechanism from `buy crisis and hold until ATH` to `temporarily increase risk while stress is extreme, rebuild dry powder as stress normalizes`.

It directly addresses the failure mode without optimizing a new parameter grid.

Any such test must receive a new R008 version/protocol and be frozen before results.

Alternative economically distinct branches remain possible later: trend + dry powder, carry-funded reserve, or true option convexity. They should not be mixed into the first redesign experiment.
