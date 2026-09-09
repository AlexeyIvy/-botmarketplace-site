# R008-E002 — Long-History Independent Validation Protocol v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Candidate:** R008 — Antifragile Crisis-Opportunity Barbell  
**Experiment:** E002  
**Date:** 2026-09-09  
**Status:** pre-result frozen validation specification  
**Parent result:** `docs/research/r008-e001-results-v0.1.md`  
**Research posture:** falsification-first; no E001 parameter changes

---

## 1. Objective

E001 on Binance BTCUSDT 2020-2026 was PROMISING but cannot receive historical PASS because the sample is short, contains few severe independent crises, and begins with a truncated path-dependent state.

E002 asks:

> Does the exact frozen R008 v0.1 crisis-opportunity architecture remain economically coherent on a substantially longer, independent Bitcoin USD reference-price history that was not used to design or screen E001?

The purpose is independent historical extension and cross-source falsification, not parameter optimization.

---

## 2. Frozen strategy architecture — unchanged from E001

No strategy parameter may change.

- permanent BTC target: **10%**;
- opportunity reserve: **10%**;
- four crisis tranches: **2.5 percentage points each**;
- drawdown thresholds: **-20%, -35%, -50%, -65%**;
- drawdown measured from running daily reference-price all-time high;
- triggered tranche remains active until reset;
- reset only when the daily reference price establishes a new all-time high;
- maximum BTC target: **20%**;
- cash return: **0%**;
- no leverage;
- no shorting;
- no trend/volatility/technical filter;
- signal/state from observation t applies to return t+1;
- fee grid: **5 / 10 / 25 / 50 bps** on absolute target-weight changes under the same E001 accounting convention.

Any changed thresholds, tranche sizes, base weight, reserve size, reset logic, or filters create a new R008 version and are prohibited in E002.

---

## 3. Independent data source

### Primary source

Use Blockchain.com Charts API market-price series:

- chart: `market-price`;
- format: JSON;
- timespan: all;
- sampling disabled where supported;
- timezone: UTC;
- value interpreted as the provider's daily Bitcoin USD market-price reference observation.

This is an independent consolidated/reference market-price series, not Binance BTCUSDT.

### Why this source

E002 needs:

- substantially earlier history than 2020;
- a price series independent from Binance;
- a simple daily USD Bitcoin reference adequate for a drawdown-state architecture screen;
- no option/funding/derivative metadata.

E002 does not treat the reference price as an executable venue close. It is used to test state/path economics.

---

## 4. Data audit before P&L

The E002 engine must record and validate:

- raw number of observations;
- earliest and latest timestamps;
- duplicate dates;
- missing/non-positive prices;
- calendar gaps between observations;
- frequency distribution of gap lengths;
- exact raw-response SHA256;
- exact cleaned-series SHA256.

No interpolation is allowed in the frozen E002 baseline.

If the source returns a sampled rather than daily series, or material unexplained gaps prevent faithful daily-state reconstruction, E002 must stop with DATA_REDESIGN rather than silently fill data.

---

## 5. State initialization

R008 is path-dependent. Therefore:

- calculate the running peak and crisis state from the **earliest valid source observation**;
- do not begin state calculations only at the reporting/evaluation start;
- do not seed an assumed historical ATH manually.

This specifically avoids the truncated-state limitation of E001.

---

## 6. Evaluation slices

The engine must report all of the following.

### A. FULL_AVAILABLE

From the first valid daily source observation through the dataset endpoint.

Use for transparency only because the earliest Bitcoin market may be structurally immature.

### B. PRIMARY_LONG — from 2013-01-01

Primary long-history reporting slice.

Rationale: retain multiple mature Bitcoin bull/bear cycles while avoiding dependence on the very earliest micro-market period. Strategy state must still be initialized from the earlier available observations.

### C. PRE_2020_NEW — 2013-01-01 through 2019-12-31

**Primary new evidence slice.**

This historical segment was not used in E001 and is the key falsification window.

### D. REPLAY_2020 — 2020-01-01 onward

Cross-source replay of the period already inspected in E001.

This is not new OOS evidence. Use it to test whether the architecture behaves qualitatively similarly under a different price source and correctly initialized long-history state.

### E. POST_2023

Retain the E001 late-period diagnostic for continuity.

---

## 7. Frozen benchmarks

Mandatory:

- CASH = 0% BTC;
- STATIC10 = 10% BTC / 90% cash;
- **STATIC15 = 15% BTC / 85% cash**;
- STATIC20 = 20% BTC / 80% cash;
- BTC100 contextual only.

STATIC15 is frozen prospectively for E002 as the midpoint of R008's allowed 10-20% BTC exposure range. It is not set to the exact realized E001 average exposure.

The most important E002 comparisons are R008 vs STATIC10, STATIC15, and STATIC20.

---

## 8. Required metrics

For every strategy, fee and evaluation slice:

- CAGR;
- ending multiple;
- annualized volatility;
- Max Drawdown;
- Calmar;
- worst calendar year;
- worst calendar quarter;
- worst month;
- worst rolling 12 months;
- longest drawdown duration;
- average BTC exposure;
- maximum BTC exposure;
- turnover;
- fee drag.

Also produce calendar-year returns for PRIMARY_LONG and PRE_2020_NEW.

---

## 9. Crisis-event diagnostics

Use the exact E001 event definition.

For every mechanically detected episode:

- prior peak date/value;
- first breach dates for -20/-35/-50/-65%;
- deepest level;
- max drawdown and date;
- reset/new-ATH date if observed;
- status CLOSED or OPEN_CENSORED;
- deployed tranches;
- R008 event return;
- STATIC10 / STATIC15 / STATIC20 event returns;
- benefit versus each causal benchmark.

No named event may be selected or excluded manually.

---

## 10. Antifragility/severity diagnostics

Primary definition:

`Benefit10 = R008 event return - STATIC10 event return`

Secondary:

- Benefit15;
- Benefit20.

Report by deepest threshold level:

- number of closed events;
- mean benefit;
- median benefit;
- fraction positive;
- largest single-event share of total positive benefit.

Desired qualitative structure:

- Benefit10 positive across a broad set of crises;
- deeper completed events show non-deteriorating and preferably increasing Benefit10;
- R008 may lag STATIC20 in shallow recoveries, but should become more competitive or superior in sufficiently deep crises;
- no single event should explain the majority of total positive closed-event Benefit10.

Do not fit a continuous severity curve or threshold regression in E002.

---

## 11. Decision rule

E002 may assign **HISTORICAL PASS / REDESIGN / FAIL** for the R008 v0.1 architecture as a research candidate. Historical PASS does not authorize production; it only permits later implementation-realism and forward stages.

### HISTORICAL PASS

Require all of the following broadly:

1. On PRE_2020_NEW, R008 CAGR exceeds STATIC10.
2. On PRE_2020_NEW, R008 is not economically dominated by STATIC15 or STATIC20; it should offer a clear growth/drawdown or Calmar tradeoff.
3. PRIMARY_LONG result is directionally consistent with PRE_2020_NEW rather than depending only on 2020-2026.
4. R008 Max DD remains materially below STATIC20 on the main long-history slices.
5. Calmar is competitive with or better than STATIC15/STATIC20 on the main slices.
6. 25-50 bps costs do not erase the incremental benefit.
7. Crisis Benefit10 is positive in a broad majority of closed events and is not dominated by one event.
8. Severity-response is economically coherent: deeper shocks do not systematically worsen Benefit10 and preferably improve it.
9. Dry powder remains materially available and the strategy does not spend most of history at 20% BTC.
10. REPLAY_2020 is qualitatively compatible with E001 after allowing for source/initialization differences.

### REDESIGN

Use REDESIGN if:

- crisis benefit exists but static 15% or 20% is economically comparable or superior over the longer history;
- severity response is mixed;
- the architecture remains plausible but long trapped exposure/recovery behavior is problematic;
- source-data limitations weaken confidence;
- pre-2020 evidence is materially weaker than E001 without clearly falsifying the concept.

### FAIL

Fail R008 v0.1 if any central proposition breaks, for example:

- PRE_2020_NEW R008 does not beat STATIC10 on geometric growth;
- R008 is clearly dominated by a simple static causal benchmark;
- Max DD approaches/exceeds STATIC20 without compensating return;
- deeper crises systematically worsen Benefit10;
- positive crisis benefit depends mainly on one event;
- post-2020 success is not reproduced at all in the independent earlier history;
- moderate costs erase the edge.

No threshold/tranche/reset rescue is allowed after E002.

---

## 12. E001 accounting limitation retained deliberately

E002 keeps the same target-weight return convention so that the strategy architecture is compared consistently with E001.

Specifically, daily portfolio return is calculated from the prior day's target weight; trading cost is charged only when the target weight changes.

This is an intentional architecture-level abstraction, not final executable portfolio accounting.

If E002 receives HISTORICAL PASS, the next experiment must test implementation realism, including at minimum:

- spot holdings and natural weight drift;
- explicit rebalance rule;
- realistic trade turnover;
- spread/slippage;
- venue choice;
- cash/stable/custody assumptions;
- perpetual funding if a perp implementation is considered.

No live/forward promotion occurs before that stage.

---

## 13. Research integrity freeze

Before seeing E002 results, freeze:

- data source and raw download endpoint family;
- 10% base / 10% reserve;
- 2.5% x 4 tranches;
- -20/-35/-50/-65 thresholds;
- ATH-only reset;
- state initialization from earliest source observation;
- evaluation slices above;
- STATIC15 addition;
- cost grid;
- decision rules.

If Blockchain.com data is unusable, changing the **data source only** requires a documented data-protocol revision before any strategy result is inspected. Strategy rules remain unchanged.
