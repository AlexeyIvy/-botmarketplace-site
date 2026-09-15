# SC001-E003 Flow-Impulse Implementation Freeze v0.1

Date: 2026-09-15  
Status: **FROZEN BEFORE FIRST E003 ALPHA / GROSS-EDGE OUTPUT**

Parent protocol: `docs/research/sc001-e003-flow-impulse-continuation-protocol-v0.2.md`.

This document resolves implementation details that were intentionally left implicit in the economic protocol. It does not change the E003 hypothesis, thresholds, latencies, horizons, dates or PASS/FAIL gates.

## 1. Source boundary

Use only the already-qualified March 2024 OKX `BTC-USDT-SWAP` trade archives from:

`~/sc001_data/SC001_E003_OKX_MARCH_TRADES/archives/`

For UTC day D, reconstruct the target day by reading archive D and archive D+1 and retaining only rows with `created_time` in UTC `[D 00:00:00, D+1 00:00:00)`.

The download-stage report is authoritative for archive byte size and SHA256. The discovery engine must verify every required local archive before any feature or response calculation.

No April/Q2 body may be accessed.

## 2. Day-local causal state

All rolling E003 state resets at each UTC day boundary.

Rationale: no pre-2024-03-01 warm-up archive was authorized for E003, and the frozen protocol defines no overnight position carry. A day-local reset is conservative and avoids introducing an unplanned pre-sample dependency.

A five-second bucket is valid only when its `total_notional > 0`.

## 3. Notional proxy

The archived SWAP `size` is contract count. For the single fixed instrument `BTC-USDT-SWAP`, the contract-value multiplier is constant and would multiply both numerator and activity denominator by the same positive constant.

Therefore E003 uses the frozen `price * size` weighting exactly as written in the protocol. This preserves `FLOW_IMPULSE` numerically up to a constant that cancels in the ratio and does not make a quote-notional capacity claim.

## 4. Double causal warm-up

For valid bucket j:

1. `activity_scale_j` uses exactly the previous 720 valid `total_notional` observations and excludes bucket j;
2. `FLOW_IMPULSE_j` is then computed;
3. a candidate threshold is available only after exactly 720 prior valid `abs(FLOW_IMPULSE)` observations exist;
4. the current `FLOW_IMPULSE_j` is compared with that prior-score threshold before the current score is inserted into the threshold window.

Thus the first possible live candidate requires both causal warm-ups. No shortened warm-up is allowed.

## 5. Median and nearest-rank definitions

The 720-observation activity median is the ordinary even-sample median: average of sorted elements 359 and 360 under zero-based indexing.

For threshold q, nearest-rank index is:

`ceil(q * 720) - 1`

Primary q is `0.995`; diagnostics are `0.99` and `0.9975`.

Candidate inequality is strictly:

`abs(FLOW_IMPULSE_j) > threshold_j`

Equality is not a candidate.

## 6. Decision timestamp

Five-second buckets are UTC-aligned and left-closed/right-open. A bucket beginning at t covers `[t, t+5000ms)`.

Its decision timestamp is exactly the bucket end `t+5000ms`, after that bucket is fully closed.

## 7. Trade-price execution proxy

For each scenario:

- entry target = `decision_ts + latency`;
- exit target = `decision_ts + latency + horizon`;
- entry price = first admitted target-day trade at or after entry target;
- exit price = first admitted target-day trade at or after exit target.

If multiple trades share the same millisecond, preserve qualified archive stream order; the first admitted row is the proxy fill.

A candidate is ineligible before execution lookup if intended exit target is `>= day_end`.

## 8. Non-overlap semantics

Non-overlap is applied independently to every `(threshold, latency, horizon)` scenario.

Candidates are processed in decision-time order.

- if `decision_ts < open_until`, candidate is skipped;
- if entry cannot be found, candidate is unfilled and does not open a position;
- if entry is found but exit cannot be found before day end, the scenario is treated as open through day end and all later candidates that day are blocked;
- after a completed trade, `open_until` equals the actual exit proxy timestamp, not the intended exit target.

No pyramiding, reversal or simultaneous positions are allowed.

## 9. Gross edge and aggregation

Completed-trade gross edge:

`direction * (exit_price / entry_price - 1) * 10_000` bps.

No fee subtraction, spread model, L2 depth or P&L sizing is introduced in this coarse stage.

Pooled mean/median are trade-weighted across completed trades. Daily mean is computed separately for each UTC day. The gate `median daily mean` is the median of the required calendar-day means; a required day with zero completed primary trades makes the stage fail rather than being silently omitted.

Completion rate is:

`completed / eligible_nonoverlap`

where `eligible_nonoverlap = raw_candidates - skipped_while_open - ineligible_day_end`.

## 10. Frozen scenario set

Primary gate scenario:

- q99.5;
- 250 ms;
- 60 s.

Mandatory stress gate:

- q99.5;
- 500 ms;
- 60 s.

Diagnostics only:

- q99.0 and q99.75 at 250 ms / 60 s;
- 1000 ms at q99.5 / 60 s;
- 30 s and 120 s at q99.5 / 250 ms.

No diagnostic can replace a failed primary or 500 ms stress gate.

## 11. Chronological firewall

`discovery` mode may inspect only 2024-03-01 through 2024-03-20 for signal/response output.

`confirmation` mode must refuse to run unless the terminal discovery report exists and its verdict is exactly `E003_DISCOVERY_PASS` with all firewalls intact.

Discovery FAIL permanently keeps 2024-03-21 through 2024-03-30 confirmation outputs unopened under E003 v0.2, despite their raw archives already having been acquired in the pre-output data stage.

## 12. Parallelism

Independent UTC days may be processed in separate OS processes, up to four workers on the qualified VPS. Partial day reports are computational checkpoints only and must not be interpreted until the required stage aggregates all days.

## 13. Firewalls

Throughout E003 trade-price screening:

- no L2 acquisition;
- no Q2 raw body access;
- no formal Validation / Final access;
- no E002 TFI filter;
- no side/event/time-of-day selection;
- no retuning after output.

The first E003 alpha/gross-edge output is authorized only after this implementation freeze and the engine file are committed.