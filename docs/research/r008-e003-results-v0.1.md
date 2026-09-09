# R008-E003 — Symmetric Recovery-Release Redesign Screen Results v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Candidate:** R008 — Antifragile Crisis-Opportunity Barbell  
**Version:** v0.2  
**Experiment:** E003  
**Date:** 2026-09-09  
**Protocol:** `docs/research/r008-v0.2-symmetric-recovery-protocol-v0.1.md`  
**Decision:** **REDESIGN / DO NOT ADVANCE**

---

## 1. Executive decision

R008 v0.2 successfully fixes the primary structural defect of v0.1 — long trapped maximum exposure — but does not pass the prospectively frozen E003 gate.

Formal status:

> **REDESIGN / DO NOT ADVANCE TO FORWARD AS THE CURRENT v0.2 IMPLEMENTATION**

The symmetric current-drawdown release rule materially rebuilds dry powder faster, sharply reduces time spent at 20% BTC and preserves positive crisis Benefit10 across all closed events.

However, two central criteria fail:

1. STATIC15 Pareto-dominates R008 v0.2 on both PRE_2020_NEW and PRIMARY_LONG at baseline;
2. the same STATIC15 dominance remains at 50 bps, so E003 criterion 10 also fails.

The redesign also weakens crisis-event returns versus v0.1 in every closed crisis event, although Benefit10 remains positive.

Per the frozen protocol, do not add hysteresis, cooldown, nearby thresholds or other release tuning on the same history.

---

## 2. Data audit

Data gate: **PASS**.

- source: Blockchain.com `market-price` daily reference series;
- clean rows: 5,867;
- range: 2010-08-18 -> 2026-09-09;
- duplicate raw dates before dedup: 0;
- max gap: 1 day;
- PRIMARY_LONG rows: 5,000;
- PRIMARY_LONG one-day-gap share: 100%;
- long gaps >1 day: 0;
- missing calendar days: 0;
- raw SHA256: `c84bd2a2b68ac13f03af09ab2d089017b15215bdbe1b5e9ca7d8b5bbbe4a422a`;
- clean CSV SHA256: `b4c819d4f1e1f27b2f84ead0c4949f0cf44cda77f384186784350a5ed283cb3b`.

The E003 source is identical to E002 by hash, as intended.

---

## 3. Frozen v0.2 rule

Unchanged architecture:

- 10% permanent BTC base;
- 10% opportunity reserve;
- 4 x 2.5 percentage-point tranches;
- thresholds -20 / -35 / -50 / -65%;
- no leverage, shorts or technical filters.

Only release logic changed from v0.1:

- target exposure is a deterministic function of current drawdown;
- the same thresholds govern deployment and release;
- no sticky tranche memory;
- no hysteresis;
- no cooldown.

---

## 4. Baseline result — 10 bps

| Strategy | Slice | CAGR | Max DD | Calmar | Avg BTC | Turnover |
|---|---|---:|---:|---:|---:|---:|
| R008_V02 | PRIMARY_LONG | **12.65%** | **-20.05%** | **0.63** | 15.14% | 8.175 |
| STATIC10 | PRIMARY_LONG | 9.33% | -13.54% | 0.69 | 10.00% | 0.000 |
| STATIC15 | PRIMARY_LONG | **14.08%** | **-19.83%** | **0.71** | 15.00% | 0.000 |
| STATIC20 | PRIMARY_LONG | 18.85% | -25.79% | 0.73 | 20.00% | 0.000 |
| R008_V02 | PRE_2020_NEW | **17.50%** | **-20.05%** | **0.87** | 16.18% | 4.250 |
| STATIC10 | PRE_2020_NEW | 13.24% | -13.54% | 0.98 | 10.00% | 0.000 |
| STATIC15 | PRE_2020_NEW | **20.16%** | **-19.83%** | **1.02** | 15.00% | 0.000 |
| STATIC20 | PRE_2020_NEW | 27.25% | -25.79% | 1.06 | 20.00% | 0.000 |
| R008_V02 | REPLAY_2020 | 7.80% | -17.08% | 0.46 | 14.06% | 3.925 |
| STATIC15 | REPLAY_2020 | 8.05% | -17.19% | 0.47 | 15.00% | 0.000 |
| R008_V02 | POST_2023 | **8.37%** | **-8.18%** | **1.02** | 13.28% | 1.700 |
| STATIC15 | POST_2023 | 8.00% | -9.80% | 0.82 | 15.00% | 0.000 |

### Pareto test

On PRE_2020_NEW, STATIC15 has:

- higher CAGR: 20.16% vs 17.50%;
- smaller absolute Max DD: 19.83% vs 20.05%;
- higher Calmar: 1.02 vs 0.87.

Therefore STATIC15 Pareto-dominates v0.2.

On PRIMARY_LONG, STATIC15 again has:

- higher CAGR: 14.08% vs 12.65%;
- slightly smaller absolute Max DD: 19.83% vs 20.05%;
- higher Calmar: 0.71 vs 0.63.

Criterion 2 of the frozen PROMISING gate therefore fails on both required slices.

---

## 5. Dry-powder objective — strong improvement

The release redesign does solve the v0.1 trapped-exposure problem.

### PRIMARY_LONG

- v0.2 time at 20% BTC: **20.9%**;
- v0.1 time at 20% BTC: **58.3%**;
- v0.2 average target: **15.14%**;
- v0.1 average target: **17.08%**.

### PRE_2020_NEW

- v0.2 time at 20% BTC: **30.1%**;
- v0.1 time at 20% BTC: **76.2%**;
- v0.2 average target: **16.18%**;
- v0.1 average target: **18.35%**.

Both <50% occupancy criteria pass comfortably.

20%-exposure spells also improve materially:

- v0.1: 5 spells, median 630 days, mean 685.6 days, max 1,050 days;
- v0.2: 38 spells, median 8 days, mean 38.7 days, max 371 days.

So the redesigned mechanism restores dry powder much faster.

---

## 6. Churn and costs

Symmetric release increases state changes substantially:

- v0.2 transitions: **365** total, 183 up / 182 down;
- v0.1 transitions: 59 total, 41 up / 18 down.

Despite this, the 5-50 bps stress does not destroy geometric growth versus STATIC10.

At 50 bps:

| Strategy | Slice | CAGR | Max DD | Calmar |
|---|---|---:|---:|---:|
| R008_V02 | PRIMARY_LONG | 12.38% | -20.29% | 0.61 |
| STATIC10 | PRIMARY_LONG | 9.33% | -13.54% | 0.69 |
| STATIC15 | PRIMARY_LONG | **14.08%** | **-19.83%** | **0.71** |
| R008_V02 | PRE_2020_NEW | 17.21% | -20.29% | 0.85 |
| STATIC10 | PRE_2020_NEW | 13.24% | -13.54% | 0.98 |
| STATIC15 | PRE_2020_NEW | **20.16%** | **-19.83%** | **1.02** |

Thus costs are not the main failure mode, but criterion 10 fails because STATIC15 still Pareto-dominates v0.2 on PRIMARY_LONG at 50 bps.

---

## 7. Crisis-benefit evidence

There are 19 mechanically detected events, 18 closed.

Across all 18 closed events:

- Benefit10 positive fraction: **100%**;
- mean Benefit10: ~**+3.07%**;
- largest single positive Benefit10 share: **23.1%**;
- no single event dominates positive Benefit10.

Mean Benefit10 by deepest level:

- Level 1: **+0.39%**;
- Level 2: **+1.07%**;
- Level 3: **+3.34%**;
- Level 4: **+8.14%**.

The desired severity ordering remains present.

However, v0.2 underperforms v0.1 in every closed crisis event:

- fraction of closed events with `v0.2 - v0.1 > 0`: **0%**;
- mean v0.2-minus-v0.1 event return: about **-2.18%**;
- Level 1 mean difference: -0.41%;
- Level 2: -1.45%;
- Level 3: -3.63%;
- Level 4: -4.64%.

This is the economic tradeoff introduced by faster release: dry powder recovers sooner, but less of the post-crisis recovery is captured.

Benefit versus STATIC15 is positive in only ~27.8% of all closed events; Benefit versus STATIC20 is positive in only ~11.1%. Level 4 is the only group with positive mean Benefit15 (+3.69%), while mean Benefit20 remains slightly negative (-0.60%).

---

## 8. Frozen E003 decision gate

### Passes

1. CAGR > STATIC10 on PRE_2020_NEW and REPLAY_2020 — PASS.
2. Max DD smaller than STATIC20 on PRE_2020_NEW and PRIMARY_LONG — PASS.
3. PRIMARY_LONG 20% occupancy <50% — PASS.
4. PRE_2020_NEW 20% occupancy <50% — PASS.
5. Less time at 20% than v0.1 on both slices — PASS.
6. >=75% closed events positive Benefit10 — PASS, 100%.
7. Deep Level 3/4 mean Benefit10 positive and above Level 1 — PASS.
8. No single event >=50% positive Benefit10 — PASS, largest ~23%.
9. 50 bps CAGR remains > STATIC10 on PRE_2020_NEW — PASS.
10. Post-2020 behavior does not wholly contradict earlier direction — broadly PASS.

### Fails

1. Not Pareto-dominated by STATIC15 on PRE_2020_NEW and PRIMARY_LONG — **FAIL**.
2. At 50 bps, not Pareto-dominated by STATIC15 on PRIMARY_LONG — **FAIL**.

These are central PROMISING requirements, so E003 cannot advance.

---

## 9. Formal conclusion

**R008 v0.2 symmetric recovery-release = REDESIGN / DO NOT ADVANCE.**

The experiment teaches two robust-looking but incomplete facts:

1. crisis exposure produces a positive, severity-ordered incremental benefit versus low static exposure;
2. deterministic same-threshold recovery release solves trapped exposure but gives away enough recovery participation that a simple static 15% BTC allocation remains superior on the main historical risk/return comparison.

The current same-threshold state machine therefore does not justify forward promotion.

This does not invalidate the broader antifragility research thesis. It closes this specific recovery-release implementation.

---

## 10. Research-integrity closure

Do not now add:

- hysteresis;
- cooldown;
- optimized recovery thresholds;
- nearby crisis thresholds;
- different tranche sizes;
- different base/reserve weights;
- SMA/RSI/ADX/volatility filters to rescue v0.2.

Per the frozen E003 protocol, the next active research branch should be economically distinct rather than another release-rule tweak.
