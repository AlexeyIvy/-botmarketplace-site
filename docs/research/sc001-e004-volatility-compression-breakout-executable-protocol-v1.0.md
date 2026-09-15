# SC001-E004 — Causal Volatility-Compression Breakout Executable Protocol v1.0

Date: 2026-09-15  
Status: **FROZEN BEFORE FIRST E004 ALPHA OUTPUT**  
Branch: SCALPING RESEARCH / SC001  
Parent plan: `sc001-e004-volatility-compression-breakout-research-plan-v0.1.md`

## 1. Scientific question

Does a rare, causally detected transition from a compressed BTC-USDT-SWAP trade-price range into a directional breakout produce a gross post-latency move large and robust enough to justify later L2 taker-economics work?

This is a mechanism and gross-economics screen. It is not a profitability claim and it does not model executable depth, spread, fees, funding or queue position.

## 2. Firewalls

- E004 is independent from E001, E002 and E003.
- Base E004 uses neither E002 TFI nor E003 FLOW_IMPULSE.
- It does not alter R009-E002, R003-E003 Binance, R003-X003 Bybit, R010-E001 or Safe-Sleeve S002.
- DEV-DISCOVERY is 2024-03-01..20. Because 24 hours of causal warm-up are required, the first eligible minute is 2024-03-02 00:15 UTC because the first complete 15-minute statistic is at 2024-03-01 00:15 and 1,440 prior minute statistics are then required.
- DEV-CONFIRMATION is 2024-03-21..30 and stays unopened until terminal Discovery PASS.
- Q2, formal Validation and Final remain closed.
- No E004 return, trade, aggregate alpha metric or direction-specific result may be emitted before implementation preflight PASS.

## 3. Input and ordering

Instrument: OKX BTC-USDT-SWAP.  
Input: already-qualified March 2024 public trade archives only.

For every trade retain at least exchange timestamp, price and a deterministic original-row sequence. Sort by `(timestamp_ms, original_sequence)`. Price must be finite and positive; timestamps must be UTC and nondecreasing after sorting. Duplicate handling must match the qualified raw archive semantics; no undocumented deduplication.

All comparisons and calculations use IEEE-754 double precision. Reported values may be rounded only after decisions and metrics are calculated.

## 4. Causal minute statistic

Evaluation times `t` are exact UTC minute boundaries.

Let `P(u)` be the last observed trade price strictly before `u`. An evaluation is eligible only when all required windows contain trades and a full 24-hour historical threshold window exists.

For every minute boundary `t`, define the 15-minute compression window:

`W_t = {trades with timestamp in [t - 15 minutes, t)}`

and

- `H_t = max(price in W_t)`
- `L_t = min(price in W_t)`
- `M_t = (H_t + L_t) / 2`
- `C_t = 10,000 * (H_t - L_t) / M_t` bps.

No trade at or after `t` enters `C_t`, `H_t` or `L_t`.

The adaptive compression threshold is the nearest-rank 20th percentile of the 1,440 prior minute statistics:

`Q_t = percentile_NR_20({C_u : u = t-1440m, ..., t-1m})`.

Nearest-rank means: sort the 1,440 values ascending and select 1-based rank `ceil(0.20 * 1440) = 288`. No interpolation. Eligibility requires all 1,440 prior `C_u` values to exist.

Compression flag: `Z_t = 1[C_t <= Q_t]`.

This distribution is continuous enough to audit explicitly, but the implementation must still report threshold-tie counts.

## 5. Frozen state machine

States: `WARMUP`, `IDLE`, `ARMED`, `PENDING_ENTRY`, `OPEN`, `COOLDOWN`, `DAY_LOCKED`.

### Arming

While `IDLE`, arm only on a false-to-true transition: `Z_t = 1` and `Z_{t-1} = 0`.

At arming time freeze:

- upper band `U = H_t * (1 + 0.0002)`;
- lower band `D = L_t * (1 - 0.0002)`;
- expiry `t + 15 minutes`.

The band never moves after arming. A compression episode cannot re-arm or update its band while `ARMED`.

No arm may be created after 23:29:00 UTC.

### Breakout decision

Inspect raw trades chronologically after arming time and no later than expiry.

- LONG decision at the first trade with `price > U`;
- SHORT decision at the first trade with `price < D`.

Strict inequality is mandatory. Equality is not a breakout. If simultaneous timestamps contain candidates on both sides, original-row sequence decides which occurs first. The decision timestamp is the exchange timestamp of that first qualifying trade.

A decision later than 23:44:54.999 UTC is ineligible. If no decision occurs by expiry, cancel the arm and enter cooldown.

### Entry proxy

Primary latency is 250 ms. Target entry time is `decision_timestamp + 250 ms`. Entry price is the price of the first raw trade at or after target entry time, ordered by `(timestamp_ms, original_sequence)`.

If no entry trade is available within 5,000 ms after target entry time, the trade is incomplete. The episode still enters cooldown and may not be retried.

### Exit proxy

Frozen holding horizon is 15 minutes from actual proxy entry timestamp. Target exit time is `entry_timestamp + 900,000 ms`. Exit price is the first raw trade at or after target exit time.

If no exit trade is available within 5,000 ms, or the target/actual exit crosses the UTC day boundary, the trade is incomplete. No overnight carry or forced use of an earlier print is allowed.

There is no stop-loss, take-profit, trailing exit, pyramiding or reversal during the frozen holding period.

### Non-overlap, cooldown and daily cap

Maximum one pending/open position. All breakouts while pending/open are ignored.

After exit, incomplete episode or untriggered arm expiry, cooldown lasts 15 minutes. No arming occurs in cooldown.

Maximum four entry decisions per UTC day. After the fourth decision the state becomes `DAY_LOCKED` through the day boundary. Skipped later events cannot be selected.

## 6. Gross response

For direction `s = +1` LONG or `s = -1` SHORT:

`gross_edge_bps = s * 10,000 * (exit_price / entry_price - 1)`.

This is a trade-price, post-latency gross proxy. It is deliberately not called executable P&L.

Primary configuration identifier:

`E004_P_W15_Q20_LB1440_B2_ARM15_LAT250_H15_CAP4`.

## 7. Latency robustness

Re-run the exact same decision events and state-machine chronology with entry latency changed only to:

- 500 ms;
- 1,000 ms.

For each latency, the holding horizon begins at its actual entry timestamp. Latency variants are robustness tests, not alternate candidates and cannot rescue a failed 250 ms primary.

## 8. Predeclared read-only diagnostic neighborhood

After the primary verdict is irreversibly written, diagnostics may change one dimension at a time:

- compression window: 10 or 30 minutes;
- compression percentile: 10% or 30%;
- breakout buffer: 0 or 5 bps;
- holding horizon: 10 or 30 minutes.

All other primary rules remain unchanged. There are exactly eight one-factor variants. They cannot promote E004, change the primary verdict, choose a new primary, or open Confirmation. Any later candidate inspired by them requires a new identifier and new protected data.

Long-only, short-only, hour-of-day and day-level summaries are descriptive only and cannot exclude observations or rescue the candidate.

## 9. Metrics

For completed primary trades calculate:

- total decisions, completed trades and completion rate;
- completed trades per day and active days;
- pooled mean, median and symmetric 10% trimmed mean gross edge;
- daily mean gross edge and median across active days;
- positive-active-day count/share;
- LONG and SHORT counts and metrics;
- maximum side share;
- sum of gross edge by day;
- top-one and top-three day shares of total absolute day contribution;
- threshold-tie count/share;
- 500 ms and 1,000 ms stress metrics.

Symmetric trimming removes `floor(0.10*n)` observations from each tail after sorting.

The one-sided 95% lower confidence bound for pooled mean is calculated by a day-block bootstrap with 10,000 resamples, sampling active UTC days with replacement, retaining every completed trade within each selected day, and RNG seed `20260915`. It is a robustness metric, not a substitute for the deterministic gates.

## 10. Terminal DEV-DISCOVERY gates

Discovery is PASS only if every condition holds for the primary 250 ms configuration:

1. implementation preflight is PASS;
2. completed trades are between 30 and 80 inclusive;
3. at least 12 active eligible days;
4. proxy completion rate >= 0.99;
5. pooled mean gross edge >= 20.0 bps;
6. 10% trimmed mean >= 15.0 bps;
7. pooled median >= 10.0 bps;
8. median active-day mean >= 12.0 bps;
9. at least 70% of active days have positive daily mean;
10. one-sided 95% day-block-bootstrap lower bound for pooled mean > 10.0 bps;
11. top-one absolute day contribution share <= 0.25;
12. top-three absolute day contribution share <= 0.55;
13. each direction has at least 8 completed trades and maximum side share <= 0.75;
14. 500 ms pooled mean >= 15.0 bps and trimmed mean >= 10.0 bps;
15. 1,000 ms pooled mean >= 12.0 bps and trimmed mean >= 8.0 bps;
16. hard four-decisions/day cap and all state invariants are respected.

Any failed gate gives terminal `E004_DISCOVERY_FAIL`. Diagnostics cannot alter it. On FAIL: do not open Confirmation, acquire E004 L2, or rescue-tune E004.

If all gates pass, verdict is `E004_DISCOVERY_PASS_OPEN_CONFIRMATION_ONCE`.

## 11. Terminal DEV-CONFIRMATION gates

Confirmation runs once, unchanged, on 2024-03-21..30. It PASSes only if:

1. completed primary trades are between 15 and 40 inclusive;
2. at least 6 active days;
3. proxy completion rate >= 0.99;
4. pooled mean >= 20.0 bps;
5. 10% trimmed mean >= 15.0 bps;
6. pooled median >= 10.0 bps;
7. median active-day mean >= 12.0 bps;
8. at least 70% of active days have positive daily mean;
9. one-sided 95% day-block-bootstrap lower bound > 10.0 bps;
10. top-one absolute day contribution share <= 0.35;
11. top-three absolute day contribution share <= 0.70;
12. each direction has at least 4 completed trades and maximum side share <= 0.80;
13. 500 ms pooled mean >= 15.0 bps and trimmed mean >= 10.0 bps;
14. 1,000 ms pooled mean >= 12.0 bps and trimmed mean >= 8.0 bps;
15. all frozen state invariants hold.

Any failure is terminal `E004_CONFIRMATION_FAIL`. Only a complete PASS permits a separately frozen L2 taker-execution study. It does not itself establish net profitability.

## 12. Economics interpretation

The ~10 bps regular-user round-trip taker fee is the reference burden. The 20 bps primary mean gate deliberately demands about 10 bps of mean headroom before spread, depth and model error. Median, trimmed mean, day breadth, latency and concentration gates prevent a few outliers from manufacturing that headroom.

These are promotion plausibility gates, not estimates of future net return.

## 13. Required artifacts

Preflight must produce a machine-readable report without alpha. Discovery, if authorized, must produce:

- immutable configuration JSON and its SHA256;
- input manifest with file SHA256 values;
- event/trade CSV;
- daily metrics CSV;
- aggregate metrics JSON;
- run-state JSON;
- human-readable summary;
- code commit SHA and runtime/environment record.

No partial alpha output may be interpreted. The terminal verdict is evaluated only after the run completes and all artifacts pass integrity checks.

## 14. Freeze rule

Any change to formula, windows, percentile, bands, timing, state handling, gates or diagnostics after the first E004 alpha output creates a new experiment identifier. E004 v1.0 itself remains frozen.
