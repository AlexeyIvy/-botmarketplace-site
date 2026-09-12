# SC001-E002 — OKX Q1 Midquote Falsification Pilot v0.1

Status: **FROZEN BEFORE MIDQUOTE RESPONSE CALCULATION**

Parent signal: `SC001-E002 — Aggressive Trade-Flow Continuation Screen`
Parent same-venue replication: `SC001-E002-OKX-Q1-REPLICATION`
Parent L2 engineering qualification: `SC001-DATA-Q008-OKX-L2-FULL-DAY-PILOT`

## 1. Purpose

Test whether the already-confirmed 5-second OKX trade-flow imbalance predicts subsequent **L2 midquote movement**, rather than only subsequent transaction prices.

This is a one-day predetermined falsification pilot on `2024-01-05` only. It is intended to decide whether downloading the remaining four Q1 L2 archives is scientifically justified.

It is not a trading P&L test and cannot establish executable profitability.

## 2. Fixed date and data

Target UTC date: `2024-01-05`.

Trade-flow source: the already-qualified Q006/Q006R OKX `BTC-USDT-SWAP` trades, reconstructed on exact UTC `[2024-01-05, 2024-01-06)`.

L2 source: the Q008-qualified full-day archive:

`BTC-USDT-SWAP-L2orderbook-400lv-2024-01-05.tar.gz`

Expected compressed size: `500060536` bytes.
Expected SHA256:

`7279d6b87021ea64982449f5a7c86e298a5c46c1c107ac41a368debeaaf5929a`

No additional date may be substituted after seeing this pilot.

## 3. Signal — unchanged

For each non-overlapping 5-second bucket `[t-5s,t)`:

`TFI_5s(t) = sum(sign_i * price_i * size_i) / sum(price_i * size_i)`

where OKX taker side is mapped:
- `buy` -> `+1`;
- `sell` -> `-1`.

Decision grid: every 5 seconds at the right edge of a completed bucket.

No threshold is used. No top/bottom decile is used to create a trade rule.

The pilot must reproduce the known valid-decision count from the frozen OKX transaction-price replication for this date: `17109` decisions, unless a data-integrity error is raised.

## 4. L2 replay and midquote

Replay the full Q008 archive from the first snapshot through the end of the UTC day.

At every valid book state:

`midquote = (best_bid + best_ask) / 2`.

For any requested target timestamp `T`, use the **last valid replayed book state with exchange timestamp <= T**.

This is an as-of/causal construction. The engine must not use the first future book update after `T`.

For each sampled target, record book-state age:

`age_ms = T - state_timestamp`.

Age is diagnostic only and is not used to exclude observations post hoc.

## 5. Frozen response definitions

Latencies: `100 ms`, `250 ms`, `500 ms`.

For decision time `t` and latency `L`:
- entry midquote = as-of midpoint at `t + L`;
- exit midquote = as-of midpoint at `t + L + 5000ms`;
- response = `log(exit_mid / entry_mid) * 10000` bps.

Primary latency: `100 ms`.
Stress latency: `250 ms`.
Diagnostic latency: `500 ms`.

No zero-latency result is permitted.

## 6. Statistics

For each frozen latency calculate:
- number of valid decisions;
- Spearman correlation between TFI and future midquote response;
- mean and median response bps;
- bottom-decile mean response;
- top-decile mean response;
- top-minus-bottom decile spread;
- directional hit rate for top/bottom deciles;
- entry and exit book-state age median, p95, p99, max.

The decile statistics remain diagnostics, not trading thresholds.

## 7. Frozen pilot verdict

This single-day pilot has no claim of statistical significance.

`MIDQUOTE_PILOT_PASS` requires at 100 ms:
1. Spearman > 0;
2. top-minus-bottom extreme-decile spread > 0;
3. valid decision count = `17109`.

`MIDQUOTE_PILOT_WEAK` if Spearman > 0 but extreme spread <= 0, or vice versa.

`MIDQUOTE_PILOT_FAIL` if both primary Spearman <= 0 and primary extreme spread <= 0.

Any L2/trade data-integrity mismatch produces `ERROR/REVIEW`, not a performance verdict.

250 ms and 500 ms cannot rescue a failed 100 ms primary verdict.

## 8. Anti-rescue rule

After the pilot is opened, do not under the same experiment ID:
- change the 5s lookback/grid/horizon;
- change continuation to reversal;
- change the TFI formula;
- select one side only;
- choose a TFI threshold;
- exclude event windows;
- exclude stale-book observations based on their realized response;
- switch from as-of midquote to future-update midquote because results look better.

Any such change requires a new experiment ID.

## 9. Book-state age interpretation

The Q008 full-day replay observed a maximum inter-record timestamp gap of `87720 ms`. Therefore the pilot must report state age instead of assuming that the book is freshly updated at every target.

A large maximum age alone is not an automatic failure because an unchanged book state can legitimately persist. However unusually large median/p95/p99 age would materially weaken the interpretation and must be discussed before bulk L2 acquisition.

## 10. Economic boundary

This pilot deliberately does not include:
- taker entry/exit at bid/ask;
- spread cost;
- visible-depth consumption;
- commissions;
- slippage;
- order-size discreteness;
- capital sizing;
- maker fills or queue position.

The only question is whether predictive content survives when the response variable is the L2 midpoint.

## 11. Promotion rule

If `MIDQUOTE_PILOT_PASS`, freeze the exact same midquote method and acquire/replay the remaining four already-selected 2024-Q1 L2 dates in storage-safe batches. Those four dates become the next multi-day confirmation layer for this midquote mechanism.

If `MIDQUOTE_PILOT_FAIL`, do not spend ~2.10 GB downloading the remaining four Q1 L2 archives for this mechanism before a documented expert review.

OKX Q2, formal Validation, and Final remain unopened in either case.
