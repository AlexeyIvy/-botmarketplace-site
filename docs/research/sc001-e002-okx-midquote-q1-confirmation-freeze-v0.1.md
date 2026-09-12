# SC001-E002 OKX Q1 Midquote Confirmation Freeze v0.1

Status: **FROZEN BEFORE REMAINING-Q1 MIDQUOTE ACCESS**  
Parent pilot: `SC001-E002 OKX Midquote Falsification Pilot`  
Pilot date already opened: `2024-01-05`

## Purpose

Confirm whether the frozen E002 5-second aggressive trade-flow continuation relationship generalizes from the one opened OKX midquote pilot day to the four remaining preselected 2024-Q1 OKX days.

This remains predictive research, not execution P&L.

## Frozen confirmation dates

Only these four already preselected Q1 dates are permitted:
- `2024-01-14` — ordinary weekend;
- `2024-01-31` — FOMC;
- `2024-02-12` — ordinary weekday;
- `2024-02-13` — CPI.

No replacement dates are permitted.

## Feature — unchanged

For each non-overlapping UTC-aligned 5-second bucket `[t-5s,t)`:

`TFI_5s = sum(side_sign * price * size) / sum(price * size)`

OKX taker side:
- buy = +1;
- sell = -1.

Lookback/grid/horizon remain 5s/5s/5s.

## L2 response — unchanged from pilot

For latency L in `{100,250,500}` ms:
- entry target = `t + L`;
- exit target = `t + L + 5000ms`;
- use the most recent valid L2 book state with timestamp `<= target`;
- midquote = `(best_bid + best_ask)/2`;
- response bps = `log(midquote_exit/midquote_entry)*10000`.

No look-ahead to the first future book record is allowed.

No book-state-age filter is applied to the primary result.

## Primary daily statistic

`Spearman(TFI_5s, future_midquote_response_5s_at_100ms)`.

Expected sign: positive.

UTC day is the inferential block.

## Frozen confirmation gates

### 100 ms primary
1. positive daily Spearman = **4/4**;
2. median daily Spearman > 0;
3. positive extreme-decile spread = **4/4**;
4. median extreme-decile spread > 0;
5. event-day median Spearman > 0;
6. ordinary-day median Spearman > 0.

### 250 ms stress
7. positive daily Spearman >= **3/4**;
8. median daily Spearman > 0.

500 ms is diagnostic only and cannot rescue a failed primary result.

For four independent 50/50 signs, 4/4 has one-sided sign probability `0.0625`; therefore this confirmation alone is not claimed as a standalone 5% significance result. It is interpreted together with the earlier frozen Binance discovery/confirmation and OKX transaction-price replication evidence.

## Mandatory diagnostics

For each day and latency report:
- n;
- Spearman;
- top/bottom decile means and spread;
- directional hit rate;
- entry/exit book-state-age median, p95, p99, maximum;
- L2 full-day replay integrity;
- spread distribution diagnostics if available, but spread is not yet charged as execution cost.

The rare large book-state-age values are not filtered after the fact. Any age-conditioned analysis requires a separately frozen robustness ID.

## Sequential-testing firewall

The four-day confirmation verdict must not be calculated or interpreted until all four L2 days have been acquired and full-day replay-qualified.

Acquisition may occur in two phone-safe batches, but those batches are data-only. No partial-batch TFI, midquote-response, ranking, or P&L result may be inspected between batches.

## Status mapping

- `MIDQUOTE_CONFIRMATION_PASS`: all gates 1-8 pass.
- `MIDQUOTE_CONFIRMATION_WEAK`: gates 1-6 pass but gate 7 or 8 fails.
- `MIDQUOTE_CONFIRMATION_FAIL`: any gate 1-6 fails.

No outcome here is `ROBUST_HISTORICAL_CANDIDATE` or `ADVANCE_TO_FORWARD`.

## Economic boundary

Even PASS does not establish executable alpha. This stage still excludes:
- bid/ask crossing for actual orders;
- taker fees;
- depth consumption/VWAP;
- market impact;
- capital sizing;
- order-size discreteness.

If the four-day midquote confirmation passes, the next justified stage is conservative same-venue taker execution economics using observed L2 spread/depth under frozen latency and depth-haircut scenarios.

## Holdout boundary

2024-Q2 OKX remains unopened. Formal Validation and Final remain unopened.
