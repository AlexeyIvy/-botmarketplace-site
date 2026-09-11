# SC001-E001 — BTCUSDT 1h Extreme-Move Mean-Reversion — Results v0.1

**Project:** BotMarketplace / BotMarketplace.store  
**Branch:** SCALPING RESEARCH / SC001  
**Experiment:** SC001-E001  
**Date:** 2026-09-11  
**Status:** `FAIL` — FROZEN HISTORICAL RESULT  
**Classification:** short-horizon intraday research; NOT true scalping  
**Protocol:** `docs/research/sc001-e001-pretest-freeze-v0.1.md`

---

## 1. Independence boundary

This result is strictly isolated from R009-E002, R003-E003 Binance, R003-X003 Bybit, R010-E001, and Safe-Sleeve S002. It must not be used to retune, reset, reinterpret, merge, or move any of their frozen forward clocks or rules.

No real-money deployment is authorized.

---

## 2. Data / implementation verification

The uploaded SC001-E001 outputs were independently cross-checked against each other.

Data audit:

- retained BTCUSDT USD-M perpetual bars: **58,652**;
- frozen period: **2020-01-01 00:00 UTC through 2026-09-09 19:00 UTC**;
- expected bars: **58,652**;
- coverage: **100.000000%**;
- duplicates after deduplication: **0**;
- non-1h gaps: **0**;
- maximum gap: **1 hour**;
- monotonic UTC ordering: PASS;
- close time after open time: PASS;
- exact frozen start/end: PASS;
- source mode: `_cache_bundle.zip`;
- retained funding rows: **7,332**.

Causality / signal execution:

- primary K=2.00 signals: **4,122**;
- primary executed: **4,122**;
- skipped due to gaps: **0**;
- same-bar violations: **0**;
- latency variant executed: **4,122**;
- K=1.75 executed: **5,433**;
- K=2.25 executed: **3,236**.

Result: **data/causality gate PASS**. No evidence was found that the FAIL verdict is caused by missing bars, timestamp disorder, same-bar look-ahead, or an incomplete run.

---

## 3. Primary frozen result

Primary rule: K=2.00, one-hour reversal, enter at next-hour open, exit at that hour close.

BASE round-trip cost proxy: **16 bps**.

### Development 2020-2022

- trades: **1,783**;
- average net edge/trade: **-17.53 bps**;
- profit factor: **0.588**;
- compounded normalized total return: **-96.11%**.

### Validation 2023-2024

- trades: **1,275**;
- average net edge/trade: **-15.57 bps**;
- profit factor: **0.515**;
- compounded normalized total return: **-86.80%**.

### Final 2025-2026-09-09

- trades: **1,064**;
- average net edge/trade: **-18.00 bps**;
- profit factor: **0.430**;
- compounded normalized total return: **-85.63%**.

### Combined OOS 2023 onward

- trades: **2,339**;
- average net edge/trade: **-16.68 bps**;
- profit factor: **0.477**;
- compounded normalized total return: **-98.10%**.

The large compounded losses are a consequence of the normalized 100%-NAV-per-signal research sizing and are not the main decision metric. The decisive quantities are net edge/trade, profit factor, temporal consistency, and cost/statistical robustness.

---

## 4. Gross edge versus cost drag

Independent inspection of the primary trades shows that the strategy did not possess a meaningful gross reversal edge before transaction costs.

Average gross price edge per trade:

- FULL: about **-1.04 bps**;
- DEVELOPMENT: about **-1.51 bps**;
- VALIDATION: about **+0.42 bps**;
- FINAL: about **-2.00 bps**;
- combined OOS: about **-0.68 bps**.

Average OOS funding contribution was approximately **+0.006 bps/trade**, economically negligible.

Therefore the BASE 16-bps round-trip cost assumption is not hiding a strong raw signal. The underlying one-hour reversal effect is approximately flat/slightly adverse, while realistic transaction friction is an order of magnitude larger.

Even the frozen LOW-cost track (12 bps round-trip) remains materially negative OOS, with average net edge about **-12.68 bps/trade**. STRESS (30 bps round-trip) produces about **-30.68 bps/trade** OOS.

---

## 5. Statistical evidence

Frozen UTC-calendar-week block bootstrap on combined OOS BASE trades:

- weeks: **194**;
- requested replications: **10,000**;
- valid replications: **10,000**;
- discarded zero-trade draws: **0**;
- point estimate: **-16.68 bps/trade**;
- 95% percentile interval: **[-19.28, -14.10] bps/trade**.

The entire confidence interval is below zero. This is strong evidence against a positive BASE-cost edge for the frozen E001 hypothesis.

---

## 6. Robustness diagnostics

All mandatory gates except data integrity failed.

- D — data integrity: **PASS**;
- N — net edge magnitude: **FAIL**;
- C — cost robustness: **FAIL**;
- S — bootstrap uncertainty: **FAIL**;
- PF — trade quality / count: **FAIL**;
- L — one-hour latency robustness: **FAIL**;
- P — parameter neighborhood: **FAIL**;
- M — missed-trade robustness: **FAIL**;
- Y — temporal breadth: **FAIL**.

Combined OOS BASE sensitivity:

- K=1.75: average net edge about **-15.58 bps/trade**;
- K=2.00: **-16.68 bps/trade**;
- K=2.25: about **-17.83 bps/trade**;
- one-hour delayed entry: about **-16.49 bps/trade**;
- randomly omit 10%: about **-16.45 bps/trade**;
- randomly omit 25%: about **-16.93 bps/trade**.

Thus the failure is not a single-point threshold accident.

---

## 7. Temporal and regime diagnostics

No completed OOS year 2023/2024/2025 produced positive net P&L under the frozen BASE implementation. Partial 2026 is also negative.

Primary BASE net edge was negative in all reported directional regimes (bull, bear, sideways), volatility regimes represented in the sample, and both crisis / non-crisis states.

These regime tables are diagnostics only and must **not** be used to create hindsight entry filters to rescue E001.

---

## 8. Decision

### Formal verdict

**SC001-E001 = FAIL.**

This is a valid falsification result, not a data failure.

The current multi-year 1h dataset was sufficient to test this frozen hypothesis. Downloading finer data must **not** be used to rescue or retune E001.

### What is falsified

The specific frozen proposition that a >=2-sigma one-hour BTCUSDT perpetual move can be faded for the next single hour with economically meaningful net edge is not supported.

### What is not falsified

This result does not prove that:

- every short-horizon mean-reversion mechanism is impossible;
- every momentum or volatility-expansion mechanism is impossible;
- true minute/tick scalping is impossible;
- microstructure/order-flow strategies are impossible.

Those are different hypotheses and require separate frozen experiments / data.

---

## 9. Next research action

Do **not** add RSI, moving averages, volume filters, time-of-day filters, regime filters, stop-losses, or alternative thresholds to E001 after seeing this result.

Proceed only with a genuinely independent hypothesis under a new experiment identifier.

The predeclared next family is short-horizon momentum / continuation (Family B). Before any P&L is inspected, create `SC001-E002` with its own economic hypothesis, exact holding rule, execution cost model, validation split, and PASS/FAIL gates.

A separate minute/trade/bid-ask data-acquisition gate should be opened only when we deliberately move from the current 1h short-horizon research program to **true scalping / microstructure** research. Start with free/public sources; paid datasets remain unauthorized unless explicitly approved later.
