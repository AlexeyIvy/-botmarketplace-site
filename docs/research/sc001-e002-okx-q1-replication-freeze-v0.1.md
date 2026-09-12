# SC001-E002 OKX Q1 Replication Freeze v0.1

Status: **FROZEN BEFORE OKX FEATURE/RETURN CALCULATION**  
Experiment ID: `SC001-E002-OKX-Q1-REPLICATION`  
Parent feature family: `SC001-E002 — Aggressive Trade-Flow Continuation Screen`

## 1. Purpose

Test whether the already confirmed Binance E002 feature family exists independently on OKX `BTC-USDT-SWAP` using the same five frozen 2024-Q1 UTC dates and the same feature/timing logic.

This is a cross-venue feature replication on OKX and still **not** an executable strategy backtest or profitability claim.

## 2. Frozen source data

Only the five Q006R-qualified UTC days are allowed:

- 2024-01-05 — NFP
- 2024-01-14 — ordinary weekend
- 2024-01-31 — FOMC
- 2024-02-12 — ordinary weekday
- 2024-02-13 — CPI

Each target UTC day must be reconstructed from the already qualified Q006R `D + D+1` source archives and filtered to UTC `[D,D+1)`.

2024-Q2 OKX is forbidden in this experiment and remains the intended same-venue chronological holdout.

Formal Validation and Final are forbidden.

## 3. Side semantics

OKX historical/public trade rows contain:

`instrument_name, trade_id, side, price, size, created_time`

The OKX public-trades API documentation defines `side` as the **trade side of taker**:

- `buy` -> buyer taker -> `+1`
- `sell` -> seller taker -> `-1`

For SWAP, `size` is contract count.

Because the screen is a normalized ratio on one fixed instrument,

`sum(sign * price * size) / sum(price * size)`,

a constant contract-value multiplier cancels algebraically. This permits the predictive screen without making a notional, capacity, depth, or P&L claim.

## 4. Frozen feature — unchanged economic mechanism

For each non-overlapping 5-second bucket `[t-5s,t)`:

`TFI_5s(t) = sum(sign_i * price_i * size_i) / sum(price_i * size_i)`

Decision time is the right edge `t` of the completed bucket.

No threshold is used.

## 5. Frozen future response

Primary latency: **100 ms**.

At each decision time `t`:

- entry reference = first OKX transaction price at or after `t+100ms`;
- exit reference = first OKX transaction price at or after `t+5100ms`;
- response = `log(exit/entry) * 10,000` bps.

Stress latency: **250 ms** with the same 5-second horizon.

Diagnostic latency: **500 ms** with the same 5-second horizon.

Zero-latency is forbidden.

This remains **transaction-price response**, not executable fill/P&L.

## 6. Primary statistic

For each UTC day:

`Spearman(TFI_5s, future_response_5s_at_100ms)`.

Expected sign: positive.

The day is the primary inference block. Individual 5-second observations are not treated as IID primary evidence.

## 7. Frozen primary gates

All of the following are required for `OKX_REPLICATION_PASS`:

1. 100 ms daily Spearman positive on **5/5** days;
2. median 100 ms daily Spearman > 0;
3. event-day median 100 ms Spearman > 0;
4. ordinary-day median 100 ms Spearman > 0;
5. 100 ms extreme-decile top-minus-bottom response spread positive on **5/5** days;
6. median 100 ms extreme-decile spread > 0;
7. 250 ms daily Spearman positive on at least **4/5** days;
8. median 250 ms daily Spearman > 0.

For n=5 under a 50/50 sign null, 5/5 positives has one-sided probability `0.03125`.

The 500 ms result is diagnostic only and cannot rescue a failed primary/stress result.

## 8. Cross-venue magnitude diagnostics

Report, but do **not** gate on:

- OKX median daily Spearman relative to the Binance 2024-Q1 confirmation median `0.086705639006201`;
- OKX median extreme-decile spread relative to Binance Q1;
- same-day OKX-vs-Binance Spearman direction and magnitude.

No 50% retention gate is imposed across venues because venue microstructure and trade aggregation differ. The primary replication claim is directional/monotonic reproducibility, not equality of effect size.

## 9. Lag diagnostics

For every latency/day, report the actual time from target entry timestamp to the first observed trade and the corresponding exit lag:

- median;
- p95;
- p99;
- maximum.

These lags are diagnostics only. Observations are not removed post hoc based on lag. Any future lag filter requires a new experiment ID.

## 10. Extreme-decile diagnostics

For each day/latency report:

- bottom decile mean response;
- top decile mean response;
- top-minus-bottom spread;
- directional hit rate.

Deciles are day-relative diagnostics only and are not a tradable live threshold.

## 11. Anti-overfitting rule

Forbidden after seeing the result under this experiment ID:

- changing 5s lookback/grid/horizon;
- threshold tuning;
- selecting buy-only or sell-only;
- dropping event classes or ordinary days;
- choosing a subset of dates;
- changing the primary latency;
- changing TFI weighting;
- using 2024-Q2 OKX to tune this result.

Any material change is a new experiment and must be counted separately.

## 12. Status mapping

- `OKX_REPLICATION_PASS`: all gates 1-8 pass.
- `OKX_REPLICATION_WEAK`: gates 1-6 pass but gate 7 or 8 fails.
- `OKX_REPLICATION_FAIL`: any gate 1-6 fails.

Even `OKX_REPLICATION_PASS` leaves the parent family at `PROMISING_SCREEN`. It does not establish `ROBUST_HISTORICAL_CANDIDATE`.

## 13. Economic boundary

This experiment still excludes:

- observed bid/ask spread;
- executable L2 depth;
- historical fee schedule;
- market-impact beyond transaction-price response;
- maker queue assumptions;
- capital sizing/discreteness.

Therefore it cannot establish net edge after costs.

## 14. Promotion rule

If OKX replication passes, the next justified step is **OKX L2 execution-economics qualification** on the same Q1 research dates under the already frozen taker-only latency/depth framework, while preserving 2024-Q2 OKX as a later same-venue holdout.

If it fails, do not rescue the feature with OKX-specific tuning under this experiment ID.
