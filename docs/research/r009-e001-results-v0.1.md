# R009-E001 — Trend-Gated Dry-Powder Barbell Results v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Candidate:** R009 — Antifragile Trend-Gated Dry-Powder Barbell  
**Experiment:** E001  
**Date:** 2026-09-09  
**Status:** formal in-sample mechanism-screen result  
**Decision:** **PROMISING_SCREEN / ADVANCE TO FORWARD PAPER**  
**Protocol:** `docs/research/r009-e001-trend-gated-dry-powder-protocol-v0.1.md`

## 1. Executive decision

R009 v0.1 passes the frozen E001 mechanism-screen gate.

Formal status:

> **PROMISING_SCREEN / ADVANCE TO FORWARD OR NEW-INDEPENDENT VALIDATION**

This is not HISTORICAL PASS. Bitcoin history through 2026 was already inspected during R002/R008 research, so E001 is in-sample for the combined architecture.

The screen is nevertheless economically stronger than the standalone R008 crisis ladder:

- R009 combines a frozen SMA120 0/10% trend sleeve with the frozen 0-10% sticky crisis reserve;
- on PRIMARY_LONG the combined portfolio has higher CAGR and materially lower Max DD than R008 v0.1 while using much less average BTC exposure;
- the combined portfolio is not Pareto-dominated by STATIC15 daily or monthly;
- it beats TREND10 on geometric growth in both pre-2020 and post-2020 regimes;
- the result survives 50 bps cost stress;
- average desired BTC target remains below the prospectively frozen 15% ceiling.

The correct interpretation is not “crisis alpha proven.” E004 already showed the crisis ladder is mainly conditional beta allocation. R009 is promising because the **interaction of two separately frozen jobs** — trend-based ordinary-risk control and crisis-based distressed-risk deployment — improves the observed growth/drawdown frontier.

## 2. Data integrity

Data gate: **PASS**.

- source: Blockchain.com daily Bitcoin market-price reference series;
- raw observations: 6,459;
- clean positive observations: 5,867;
- clean period: 2010-08-18 -> 2026-09-09;
- duplicate raw dates before deduplication: 0;
- PRIMARY_LONG observations: 5,000;
- PRIMARY_LONG missing calendar days: 0;
- PRIMARY_LONG max gap: 1 day;
- raw SHA256: `c84bd2a2b68ac13f03af09ab2d089017b15215bdbe1b5e9ca7d8b5bbbe4a422a`;
- clean SHA256: `b4c819d4f1e1f27b2f84ead0c4949f0cf44cda77f384186784350a5ed283cb3b`.

## 3. Frozen architecture tested

### TREND10

- SMA lookback: 120 observed daily prices;
- ON if `price_t > SMA120_t`;
- target 10% BTC when ON, 0% otherwise;
- state at t applies to t+1.

### CRISIS10

- reserve size: 10% NAV;
- 4 x 2.5pp tranches;
- triggers: -20/-35/-50/-65% drawdown from running ATH;
- sticky until next ATH;
- target 0-10% BTC.

### R009 combined

`combined target = trend target + crisis target`

Target range: 0-20% BTC.

Canonical accounting: self-financing daily target, 10 bps baseline; 5/10/25/50 bps stress grid.

## 4. Baseline headline metrics — 10 bps

### PRIMARY_LONG — 2013-01-01 onward

| Strategy | CAGR | Max DD | Calmar | Avg BTC | Turnover |
|---|---:|---:|---:|---:|---:|
| R009 combined | **15.02%** | **-15.73%** | **0.95** | **12.91%** | 26.185 |
| TREND10 | 9.36% | -10.10% | 0.93 | 5.83% | 18.520 |
| CRISIS10 | 5.36% | -11.55% | 0.46 | 7.08% | 9.105 |
| R008 v0.1 | 14.70% | -23.11% | 0.64 | 17.08% | 18.689 |
| STATIC10 daily | 9.24% | -13.63% | 0.68 | 10.00% | 11.245 |
| STATIC15 daily | 13.94% | -19.95% | 0.70 | 15.00% | 15.926 |
| STATIC20 daily | 18.68% | -25.93% | 0.72 | 20.00% | 19.981 |
| STATIC15 monthly | 16.74% | -22.30% | 0.75 | 15.44% | 4.086 |

Key result: the combined architecture earns more CAGR than STATIC15 daily despite lower average BTC exposure, while also having materially smaller Max DD and higher Calmar.

STATIC15 monthly has higher CAGR, but materially worse Max DD and lower Calmar, so it does not Pareto-dominate R009.

### PRE_2020 — 2013-01-01 through 2019-12-31

| Strategy | CAGR | Max DD | Calmar | Avg BTC |
|---|---:|---:|---:|---:|
| R009 combined | **20.02%** | **-15.73%** | **1.27** | 14.23% |
| TREND10 | 13.39% | -10.10% | 1.33 | 5.88% |
| CRISIS10 | 6.13% | -11.55% | 0.53 | 8.35% |
| R008 v0.1 | 19.50% | -23.11% | 0.84 | 18.35% |
| STATIC15 daily | 20.00% | -19.95% | 1.00 | 15.00% |
| STATIC15 monthly | 25.54% | -22.30% | 1.15 | 15.63% |

The combined portfolio roughly matches STATIC15 daily growth while reducing drawdown by more than four percentage points and increasing Calmar.

### REPLAY_2020 — 2020 onward

| Strategy | CAGR | Max DD | Calmar | Avg BTC |
|---|---:|---:|---:|---:|
| R009 combined | **10.02%** | **-9.87%** | **1.01** | 11.54% |
| TREND10 | 5.29% | -3.63% | 1.46 | 5.79% |
| CRISIS10 | 4.57% | -6.67% | 0.68 | 5.75% |
| R008 v0.1 | 9.90% | -17.75% | 0.56 | 15.75% |
| STATIC15 daily | 7.95% | -17.28% | 0.46 | 15.00% |
| STATIC15 monthly | 8.20% | -16.95% | 0.48 | 15.23% |

This is directionally compatible with the pre-2020 screen. The combined architecture improves growth materially versus TREND10 while keeping drawdown far below simple 15-20% static allocations.

### POST_2023

R009 combined: CAGR **9.12%**, Max DD **-4.98%**, Calmar **1.83**, average BTC exposure ~11.08%.

This is a particularly strong recent regime, but it is not independent evidence.

## 5. Ablation result

### Combined vs TREND10

PRIMARY_LONG CAGR rises from 9.36% to 15.02%. Max DD increases from -10.10% to -15.73%, but Calmar also improves slightly from ~0.93 to ~0.95.

Therefore the crisis sleeve contributes more than simple drawdown inflation in the aggregate screen.

### Combined vs CRISIS10

CRISIS10 alone is positive but weak: PRIMARY_LONG CAGR ~5.36%, Calmar ~0.46.

The trend sleeve supplies most ordinary directional participation and materially improves the standalone crisis architecture.

### Combined vs R008 v0.1

R009 combined has roughly similar full-period growth but much better risk efficiency:

- CAGR: 15.02% vs 14.70%;
- Max DD: -15.73% vs -23.11%;
- Calmar: 0.95 vs 0.64;
- average BTC exposure: 12.91% vs 17.08%.

This is the strongest structural result of E001.

## 6. State diagnostics

PRIMARY_LONG:

- trend ON fraction: **58.34%**;
- crisis active fraction: **84.44%**;
- crisis fully deployed fraction: **58.26%**;
- average trend target: **5.83%**;
- average crisis target: **7.08%**;
- average combined target: **12.91%**.

Joint-state fractions:

- trend ON / crisis inactive: 14.66%;
- trend OFF / crisis inactive: 0.90%;
- trend ON / crisis active: 43.68%;
- trend OFF / crisis active: 40.76%.

Combined desired target occupancy:

- 0%: 0.9%;
- 2.5%: 5.1%;
- 5%: 4.6%;
- 7.5%: 5.4%;
- 10%: 40.3%;
- 12.5%: 5.8%;
- 15%: 2.0%;
- 17.5%: 3.2%;
- 20%: 32.6%.

Important interpretation: the “dry-powder” reserve is not usually dormant. Because the sticky crisis sleeve is active ~84% of PRIMARY_LONG, the economic mechanism is better described as a **state-dependent beta handoff**: ordinary trend beta falls away in weak regimes while crisis beta deploys; during recoveries both sleeves can overlap.

This wording is more precise than treating the 10% crisis sleeve as continuously unused cash waiting for rare crashes.

## 7. Fixed-horizon shock diagnostics

The fixed-horizon evidence remains descriptive and small-sample.

At the deepest -65% trigger, count = 5:

- 365d mean benefit combined vs TREND10: **+4.94pp**;
- vs STATIC15 daily: **+1.88pp**;
- vs STATIC20 daily: **-2.26pp**.

At shallower -20/-35/-50 triggers, combined often beats TREND10 at short/medium horizons but generally trails STATIC15/20 over longer horizons.

Therefore E001 does **not** reverse the E004 conclusion that the crisis sleeve by itself is not demonstrated convex/timing alpha. The value of R009 is the portfolio interaction, not a claim of standalone crisis alpha.

## 8. Cost stress

At 50 bps on PRIMARY_LONG:

- R009 combined CAGR ~**14.14%**, Max DD ~**-16.50%**, Calmar ~**0.86**;
- TREND10 CAGR ~8.77%;
- STATIC15 daily CAGR ~13.41%, Max DD ~-20.41%, Calmar ~0.66;
- STATIC15 monthly CAGR ~16.60%, Max DD ~-22.40%, Calmar ~0.74.

The combined architecture remains economically coherent and is not Pareto-dominated by STATIC15 daily/monthly under the frozen high-cost stress.

## 9. Frozen decision gate

1. Combined CAGR > STATIC10 daily on PRIMARY_LONG, PRE_2020, REPLAY_2020: **PASS**.
2. Combined CAGR > TREND10 on PRIMARY_LONG and both subperiods: **PASS**.
3. Not Pareto-dominated by STATIC15 daily on PRIMARY_LONG or PRE_2020: **PASS**.
4. Not Pareto-dominated by STATIC15 monthly on PRIMARY_LONG: **PASS**.
5. Max DD materially below STATIC20 daily/monthly: **PASS**.
6. Max DD below R008 v0.1: **PASS**.
7. PRIMARY_LONG average desired BTC target <15%: **PASS**, ~12.91%.
8. CRISIS10 ending multiple >1 and adding it improves combined geometric growth: **PASS**.
9. 50 bps stress does not reverse broad conclusions: **PASS**.
10. PRE_2020 and REPLAY_2020 directionally compatible: **PASS**.

Formal result:

> **PROMISING_SCREEN / ADVANCE TO FORWARD PAPER**

## 10. What must not happen next

Do not search on historical BTC data for:

- another SMA lookback;
- another trend sleeve weight;
- another crisis reserve size;
- different crisis thresholds;
- different tranche sizes;
- interaction overrides between sleeves;
- optimized reset/recovery rules;
- rebalance frequencies chosen from a grid.

The exact R009 v0.1 architecture is frozen.

## 11. Next stage

Open R009-E002 as a forward paper record on executable BTC spot daily data.

The forward stage must:

- use only fully closed UTC daily bars;
- initialize SMA120 and crisis state from pre-inception historical bars without assigning pre-inception P&L;
- start the performance clock only after the protocol/engine freeze;
- track R009 combined, TREND10, CRISIS10, STATIC15 and STATIC20 comparators under the same self-financing accounting;
- preserve all E001 parameters exactly;
- model paper cash as zero-yield USD for comparability, while explicitly deferring real safe-sleeve custody/T-bill/stablecoin design to implementation-realism work.

No production promotion occurs from E001 alone.