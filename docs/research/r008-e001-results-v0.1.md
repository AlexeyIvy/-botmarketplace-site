# R008-E001 — Crisis-Opportunity Barbell Sanity Screen Results v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Candidate:** R008 — Antifragile Crisis-Opportunity Barbell  
**Experiment:** E001  
**Date:** 2026-09-09  
**Status:** **PROMISING / ADVANCE TO LONGER-DATA VALIDATION**  
**Protocol:** `docs/research/r008-antifragile-crisis-opportunity-barbell-protocol-v0.1.md`  
**Frozen engine commit:** `70700adc936ea59f245a11804f9a576ba4572460`

---

## 1. Scope and integrity

E001 used only BTCUSDT daily close data from the already-audited Binance archive dataset.

Frozen architecture:

- 10% permanent BTC sleeve;
- 10% opportunity reserve;
- four equal 2.5 percentage-point crisis tranches;
- drawdown triggers: -20%, -35%, -50%, -65%;
- once triggered, a tranche stays deployed until a new closing all-time high;
- reset to 10% BTC only after a new closing ATH;
- no leverage, no shorts, no technical indicators;
- cash return 0%;
- signal formed on close t and applied to t+1;
- fee stress 5 / 10 / 25 / 50 bps.

Input:

- 2,435 BTC daily rows;
- 2020-01-01 -> 2026-08-31;
- 8 mechanically detected crisis episodes.

No strategy parameter was changed after observing the result.

---

## 2. Baseline result — 10 bps

| Strategy | Full CAGR | Full Max DD | Full Calmar | Ending | Avg BTC | Post-2023 CAGR | Post-2023 Max DD | Post-2023 Calmar |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| R008 | **9.01%** | **-17.66%** | **0.51** | 1.777x | 14.79% | **10.30%** | **-8.38%** | **1.23** |
| CASH | 0.00% | 0.00% | n/a | 1.000x | 0.00% | 0.00% | 0.00% | n/a |
| STATIC10 | 5.42% | -11.72% | 0.46 | 1.422x | 10.00% | 5.37% | -6.59% | 0.81 |
| STATIC20 | 10.73% | -22.42% | 0.48 | 1.972x | 20.00% | 10.78% | -12.88% | 0.84 |
| BTC100 | 43.12% | -76.67% | 0.56 | 10.902x | ~100% | 53.01% | -52.98% | 1.00 |

Interpretation:

- R008 clearly exceeds STATIC10 on geometric growth;
- R008 gives up ~1.7 percentage points of full-period CAGR versus STATIC20 while reducing Max DD by ~4.8 percentage points;
- full-period Calmar is slightly better than both STATIC10 and STATIC20;
- post-2023, R008 retains almost the same CAGR as STATIC20 while reducing Max DD from ~12.9% to ~8.4%, producing a much stronger Calmar;
- the late-period result therefore supports rather than contradicts the full-period result.

This satisfies the E001 sanity-screen growth/drawdown requirement broadly enough to advance.

---

## 3. Cost robustness

R008 full-period CAGR:

| Cost | CAGR | Max DD | Calmar |
|---|---:|---:|---:|
| 5 bps | 9.02% | -17.65% | 0.511 |
| 10 bps | 9.01% | -17.66% | 0.510 |
| 25 bps | 8.99% | -17.67% | 0.509 |
| 50 bps | 8.95% | -17.69% | 0.506 |

Post-2023 CAGR remains ~10.27% even at 50 bps.

The reason is structural: turnover is very low (~0.875 full-period; ~0.275 post-2023 under the engine convention). Moderate/high fee stress therefore does not erase the incremental result.

---

## 4. Crisis-event evidence

Eight mechanically detected episodes were retained; seven are closed and one is open/censored at the endpoint.

Benefit is defined exactly as pre-specified:

`Benefit = R008 event return - STATIC10 event return`

All eight observed episodes have positive benefit versus STATIC10.

Closed-event benefit by deepest level:

| Deepest level | Number of closed events | Mean benefit vs STATIC10 | Mean benefit vs STATIC20 |
|---|---:|---:|---:|
| Level 1 (-20% to -35%) | 4 | **+0.81%** | -2.43% |
| Level 3 (-50% to -65%) | 2 | **+5.53%** | **+0.91%** |
| Level 4 (<= -65%) | 1 | **+9.41%** | **+4.94%** |

There were no Level-2-only closed episodes in this short sample.

Important qualitative pattern:

- in shallow crises, always holding 20% BTC often wins because there is little reason to have preserved dry powder;
- in deep crises, R008 catches up and exceeds STATIC20 because the extra exposure is added only after substantially lower prices are reached;
- versus STATIC10, incremental benefit increases strongly with crisis severity in the closed sample;
- the single open/censored Level-3 event is still positive versus STATIC10 and STATIC20 at the endpoint, but it must not be treated as a completed recovery observation.

This is the most important antifragility-style result from E001: greater shock severity produced larger incremental recovery benefit in the completed episodes rather than accelerating relative damage.

The largest single closed-event benefit versus STATIC10 accounts for less than half of the sum of positive closed-event benefits, so the observed incremental effect is not literally explained by one event alone.

---

## 5. Dry-powder behavior

Fraction of observed days by BTC target:

- 10.0% BTC: 28.6%;
- 12.5% BTC: 18.4%;
- 15.0% BTC: 11.6%;
- 17.5% BTC: 15.6%;
- 20.0% BTC: 25.9%.

Average BTC exposure: ~14.79%.

Average unused opportunity reserve: ~5.2 percentage points of NAV.

Therefore the state machine is neither trivial nor permanently maxed out:

- dry powder is genuinely available for substantial portions of history;
- crisis capital is also deployed often enough to matter economically.

---

## 6. Calendar behavior

Baseline 10 bps R008 returns:

- 2020: +25.36%;
- 2021: +14.44%;
- 2022: -13.51%;
- 2023: +22.55%;
- 2024: +16.10%;
- 2025: +0.47%;
- 2026 through August: +0.19%.

Worst full-period calendar year: 2022 at about -13.5%.

The 2023-2026 slice is particularly encouraging because the architecture remains useful after the large 2020-2021 bull phase and does not rely only on the first COVID-era event.

---

## 7. Important caveats

### 7.1 Short sample

2020-2026 contains only eight mechanically detected crisis episodes and only one completed Level-4 episode. This is insufficient for a historical PASS.

### 7.2 Path-dependent initialization

R008 is explicitly path-dependent because the active tranches depend on the prior all-time high and unresolved drawdown episode.

The E001 dataset starts on 2020-01-01, so its initial running peak is necessarily initialized inside the truncated sample rather than from Bitcoin's full earlier history. The first 2020 episode therefore cannot be treated as a fully initialized live-strategy path from inception.

This is not repaired post hoc in E001. It is a reason the next validation must start from a substantially longer independent historical series.

### 7.3 Portfolio accounting abstraction

E001 is an architecture screen. It models daily target-weight exposure and charges transaction cost on target changes. It is not yet a venue-specific executable spot/perpetual implementation with drift-aware rebalance costs, funding, spreads, or custody/cash yield.

Those details become relevant only if the architecture survives longer-history validation.

### 7.4 R008 is not mathematical convexity

The strategy remains a cash-heavy path-dependent deployment rule, not an option payoff. The result supports continued antifragility research, not a claim of true convexity.

---

## 8. Post-hoc diagnostic — not part of the decision rule

Because realized average R008 BTC exposure is ~14.8%, a coarse 15% static BTC/cash portfolio is a natural additional diagnostic benchmark.

Under the same E001 daily-return convention and 10 bps initial cost, an approximate STATIC15 diagnostic gives:

- full CAGR ~8.09%;
- full Max DD ~-17.20%;
- full Calmar ~0.47;
- post-2023 CAGR ~8.07%;
- post-2023 Max DD ~-9.77%;
- post-2023 Calmar ~0.83.

R008 is therefore not obviously explained solely by having ~15% average BTC exposure: it adds ~0.9 percentage points of full CAGR at roughly similar drawdown and performs materially better in the post-2023 slice.

This benchmark was not pre-specified for E001 and must not be used to retroactively change the formal E001 acceptance rule. A fixed STATIC15 benchmark should be frozen prospectively in E002.

---

## 9. Formal E001 decision

**R008-E001 STATUS: PROMISING / ADVANCE TO LONGER-DATA VALIDATION.**

Why it advances:

- net CAGR clearly exceeds STATIC10;
- Max DD remains materially below STATIC20;
- Calmar is better than both pre-specified causal benchmarks;
- post-2023 behavior is coherent and stronger on risk-adjusted terms;
- 25-50 bps cost stress is immaterial;
- all observed crisis episodes show positive benefit vs STATIC10;
- completed deeper events show increasing benefit with severity;
- the result is not explained by a single event alone;
- dry powder remains economically meaningful through time.

Why it is not PASS:

- the sample is short and event-poor;
- path-dependent initial state is truncated at 2020;
- only one completed Level-4 event exists;
- execution accounting remains an architecture proxy;
- independent longer BTC history is mandatory under the frozen protocol.

No E001 parameter rescue or tuning is permitted.

---

## 10. Required next step

Proceed to R008-E002 using an independent long-history Bitcoin USD reference series.

E002 must:

1. keep the exact R008 v0.1 architecture unchanged;
2. initialize state from the earliest available historical observation;
3. report a pre-2020 slice as the main new historical evidence;
4. retain 2020-2026 only as a cross-source replay / consistency slice;
5. add a prospectively frozen STATIC15 benchmark;
6. repeat mechanical crisis-event and severity-response diagnostics;
7. retain the same fee stress grid;
8. issue PASS / REDESIGN / FAIL only under the separately frozen E002 protocol.
