# SC001-E009 — Volatility-Normalized Extreme Displacement Reversal Research Plan v0.1

Date: 2026-09-17  
Status: **PLANNING / FROZEN HYPOTHESIS BEFORE E009 MARKET-BODY ACCESS**

## 1. Purpose

Open a genuinely new SC001 candidate after terminal E007R1 gross-feasibility failure.

E009 is not E007 rescue-tuning. It tests a different mechanism definition: an extreme 60-second displacement measured relative to the instrument's own recent robust short-horizon volatility may identify temporary overshoot more consistently across heterogeneous perpetual markets than one fixed absolute 80-bps threshold.

E007/E007R1 verdicts remain immutable.

## 2. Motivation from prior evidence

E007R1 showed:

- a real event-level reversal effect in part of the sample;
- pooled statistics materially stronger than equal-weight cross-market statistics;
- only 4/8 positive instruments;
- best/worst instrument means separated by more than 40 bps;
- sample/activity and contribution concentration were not the main problem.

Therefore the next hypothesis should test whether **scale non-comparability across instruments** is one structural reason the absolute-threshold reversal failed to transfer.

This motivation is hypothesis generation only. July E007R1 data are contaminated engineering evidence and may not be reused as E009 promotional proof.

## 3. Frozen first-generation universe

Use the already frozen SC001 first-generation OKX linear USDT-SWAP universe.

Discovery assets remain the same eight for clean comparability of breadth rules:

- BTC-USDT-SWAP
- ETH-USDT-SWAP
- DOGE-USDT-SWAP
- ORDI-USDT-SWAP
- UNI-USDT-SWAP
- XRP-USDT-SWAP
- OP-USDT-SWAP
- BCH-USDT-SWAP

Asset holdout remains:

- SOL-USDT-SWAP
- FIL-USDT-SWAP
- LTC-USDT-SWAP
- SUI-USDT-SWAP

No symbol may be selected or removed from E009 based on E007R1 profitability.

## 4. Fresh chronology

E009 must not reuse July 1-14 E007R1 performance evidence.

Frozen proposed E009 roles before any new body access:

- Discovery performance: `2024-09-01..2024-09-14` UTC on the eight Discovery assets;
- boundary source/warm-up as objectively required by archive/stitch semantics;
- asset-holdout replication: same September performance window, four holdout assets, CLOSED until Discovery PASS;
- chronological Confirmation: `2024-10-01..2024-10-14` UTC, all 12 assets, CLOSED until prior gates PASS;
- August 2024 remains untouched and is not repurposed by E009 v0.1.

## 5. Frozen signal family

Evaluation grid: exact UTC 5-second boundaries.

For instrument i at boundary t:

1. current 5-second VWAP `C_t` uses `[t-5s,t)`;
2. anchor 5-second VWAP `A_t` uses `[t-65s,t-60s)`;
3. 60-second log displacement:

`r60_t = ln(C_t / A_t)`.

No forward fill is allowed. Missing current or anchor VWAP makes the observation invalid.

## 6. Causal robust volatility normalization

Construct 5-second log returns from consecutive valid 5-second VWAP buckets.

At boundary t, use only returns whose right edge is strictly <= t and which lie in the prior 30 minutes, excluding the current 60-second displacement interval itself where required to avoid overlap leakage.

Require at least 240 valid 5-second returns in the 30-minute lookback; otherwise the normalized observation is invalid.

Robust 5-second scale:

`MAD5_t = median(|r5 - median(r5)|)` over the valid lookback returns.

Convert to robust 60-second scale:

`sigma60_t = 1.4826 * MAD5_t * sqrt(12)`.

Require finite `sigma60_t > 0`.

Normalized displacement:

`Z_t = r60_t / sigma60_t`.

This is a prospective causal normalization and is not estimated from future or cross-sectional strategy outcomes.

## 7. Frozen trigger

One threshold only:

`|Z_t| >= 3.0`.

Trigger only on a strict crossing:

- previous valid observation has `|Z| < 3.0`;
- current valid observation has `|Z| >= 3.0`.

Direction is reversal:

- `Z_t >= +3.0` -> SHORT;
- `Z_t <= -3.0` -> LONG.

No threshold grid is authorized in E009 v0.1.

## 8. Frozen target and timing

To isolate the normalization hypothesis, retain the old E007 execution timing/target family unchanged:

- arithmetic 50% retracement from current VWAP toward the frozen anchor;
- primary trade-proxy latency `500 ms` for gross-feasibility only;
- stress latencies `1000 ms` and `2000 ms`;
- proxy tolerance `5000 ms`;
- maximum hold `10 minutes`;
- one pending/open position maximum;
- daily decision cap `4` per instrument;
- cooldown `10 minutes` after completed exit;
- no new entry decision after `23:49:00 UTC`;
- no per-asset retuning.

Exact historical discrete execution, fees and promoted PnL remain blocked until later execution/spec gates.

## 9. Gross-feasibility philosophy

E009 should first run a cheap gross-only feasibility screen before expensive L2/spec work.

Use all eight Discovery instruments in equal-weight denominators; an inactive instrument contributes `0 bps` rather than disappearing.

Reuse the same high economic-headroom philosophy as E007R1 so the normalization is not allowed to pass merely by producing tiny positive returns.

Exact PASS/FAIL gates must be frozen in a separate executable protocol before first E009 gross output.

## 10. Controls and diagnostics

Mandatory diagnostics for the later frozen protocol should include:

- candidate/decision/completed counts by instrument;
- valid normalized-observation coverage;
- distribution of `sigma60` and `|Z|` at triggers;
- long/short breadth;
- equal-weight instrument mean and median;
- pooled robust statistics;
- instrument-day and calendar-day breadth;
- latency robustness;
- concentration;
- event-rate comparability across instruments.

A matched/null diagnostic may be added only if its construction is frozen before E009 Discovery output and does not alter the trading rule.

## 11. Firewalls

Do not:

- reuse July 1-14 as E009 Discovery/Confirmation;
- select only E007R1-positive instruments;
- tune the z-threshold, lookback, MAD formula, retracement, hold or latency after E009 output;
- add E002 TFI or other SC001 features to E009 v0.1;
- open asset holdout or October Confirmation before authorized gates;
- claim exact executable PnL from trade proxies;
- use unresolved historical specs as if proven.

Any material change after Discovery creates a new experiment ID.

## 12. Why E009 precedes E006R1 in the immediate queue

E006 multi-asset basis convergence remains the next orthogonal legacy family, but it requires a new spot-accounting/multi-leg execution stack and faces a four-taker-fill cost hurdle.

E009 can test one sharply defined portability hypothesis using the already validated trade-data/taker research infrastructure at much lower engineering cost. This ordering is an efficiency decision, not evidence that E009 is superior.

If E009 fails the frozen gross-feasibility gate, do not rescue it; return to the E006R1 multi-asset basis program.
