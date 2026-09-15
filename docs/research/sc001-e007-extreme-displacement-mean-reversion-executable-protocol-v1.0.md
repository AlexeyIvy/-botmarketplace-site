# SC001-E007 — Extreme Displacement -> Partial Mean Reversion Executable Protocol v1.0

Date: 2026-09-15  
Status: **FROZEN BEFORE FIRST E007 ALPHA**

Parent planning document: `docs/research/sc001-e007-extreme-displacement-mean-reversion-research-plan-v0.1.md`

## 1. Hypothesis and scope

Test one mechanism only: an extreme short-horizon BTC perpetual displacement may contain temporary liquidity-vacuum / forced-flow overshoot, followed by partial mean reversion.

Instrument: OKX `BTC-USDT-SWAP` only.

Base E007 contains no E002 TFI, E003 FLOW_IMPULSE, E004 compression, E006 basis, funding/event/day/hour filters, L2, Q2, Validation or Final information.

Primary direction is **reversal against the displacement** for both signs. Continuation is not an allowed alternative after output.

## 2. Chronology

Discovery performance: `2024-03-01..2024-03-20` UTC.

`2024-03-21` is D+1 boundary-neighbor only and is permanently performance-excluded for E007.

If and only if Discovery terminally PASSes all gates, one unchanged Confirmation may use performance dates `2024-03-22..2024-03-30`; `2024-03-21` may be read only as warm-up/boundary history and `2024-03-31` only as D+1 reconstruction neighbor.

Q2 / formal Validation / Final remain closed.

## 3. Causal 5-second VWAP statistic

Evaluation grid: exact UTC 5-second boundaries.

For boundary `t`, define:

- current VWAP `C_t`: size-weighted trade-price VWAP over `[t-5s, t)`;
- anchor VWAP `A_t`: size-weighted trade-price VWAP over `[t-65s, t-60s)`.

Trade `size` from the qualified OKX tape is used only as the deterministic VWAP weight.

Both windows are half-open and use no trade at timestamp `>=` their right boundary. Both must contain at least one valid trade. Missing either window makes the observation invalid.

The 60-second displacement is:

`D_t = 10,000 * (C_t / A_t - 1)` bps.

## 4. Extreme-displacement trigger

Frozen absolute threshold:

`H = 80 bps`.

A trigger occurs only on a strict state transition from the previous valid grid observation:

- previous valid `|D| < 80`;
- current valid `|D| >= 80`.

If the immediately previous grid observation is invalid, no trigger is allowed.

Both signs are primary and frozen:

- `D_t >= +80`: enter SHORT reversal;
- `D_t <= -80`: enter LONG reversal.

Equality at exactly +/-80 qualifies on the crossing grid point.

The event freezes `A_t`, `C_t`, trigger sign and the 50% retracement target.

## 5. Frozen partial-reversion target

At trigger, freeze arithmetic half-retracement level:

`R_t = A_t + 0.5 * (C_t - A_t)`.

For an upward displacement, the short exits for convergence when a later causal current 5-second VWAP is `<= R_t`.

For a downward displacement, the long exits when a later causal current 5-second VWAP is `>= R_t`.

The anchor and target never roll after trigger.

## 6. Entry execution proxy

Primary latency: `500 ms` after trigger timestamp.

Entry proxy = first target-instrument trade at or after `trigger_ts + 500 ms`, no later than `5,000 ms` after that target time.

A trade exactly at the 5,000 ms tolerance boundary is eligible.

If no proxy trade exists, the decision is incomplete and produces no gross return.

If the proxy entry price has already crossed the frozen half-retracement target in the reversal direction, the event is classified `entry_already_reverted` and is incomplete; the strategy must not enter after its frozen target is already achieved.

## 7. Exit decision and proxy

After an actual entry, inspect causal 5-second grid observations strictly after the actual entry timestamp.

Exit decision is the earlier of:

1. first valid current VWAP satisfying the frozen half-retracement target;
2. maximum hold of `10 minutes` from actual entry, rounded up to the first 5-second grid boundary at or after `entry_ts + 600,000 ms`.

Exit execution proxy uses the same scenario latency after the exit-decision timestamp and the same inclusive `5,000 ms` tolerance.

If exit proxy is unavailable, the event is incomplete and the UTC day is locked against further entries because exposure cannot be causally resolved from the tape proxy.

No overnight carry is allowed.

## 8. State machine and turnover

Maximum one pending/open position.

Daily entry-decision cap: `4` per UTC day. The cap counts accepted trigger decisions whether or not execution later completes.

Cooldown after a completed exit: `10 minutes`, half-open `[exit_ts, exit_ts+10m)`.

After an incomplete entry, apply a 10-minute cooldown from the end of the entry-proxy tolerance window.

After incomplete exit, lock the remainder of that UTC day.

No new entry decision after `23:49:00.000 UTC`.

Indicator/displacement chronology may carry across UTC midnight; transient trading state and daily decision count reset at UTC midnight. No artificial midnight trigger is created by resetting the previous displacement state.

## 9. Gross-return normalization

Completed-trade gross edge:

`gross_edge_bps = direction * 10,000 * (exit_price / entry_price - 1)`

where `direction = +1` for LONG reversal after a negative displacement and `-1` for SHORT reversal after a positive displacement.

This is trade-tape gross edge before fees, spread, depth and slippage.

Regular-user one-leg taker round-trip reference remains approximately `10 bps`; promotion therefore requires material gross headroom rather than mere positivity.

## 10. Latency robustness

Primary: `500 ms`.

Frozen stress scenarios: `1,000 ms` and `2,000 ms`.

Stress scenarios reuse the exact accepted primary trigger events, frozen anchor/target and primary exit-decision timestamp. They change execution-proxy latency only. If the stressed entry occurs after the frozen primary exit-decision time or after target completion is already implied, the stressed event is incomplete rather than re-optimized.

## 11. Discovery gates — all mandatory

Primary completed trades:

- minimum `20`;
- maximum `80` (consistent with the four-per-day cap).

Active UTC days with at least one completed primary trade: `>=10`.

Completion rate: `>=0.95`.

Gross economics:

- pooled mean `>=30 bps`;
- symmetric 10% trimmed mean `>=25 bps`;
- pooled median `>=20 bps`;
- median active-day mean `>=25 bps`;
- positive active-day share `>=0.70`;
- day-block bootstrap 95% lower bound on pooled mean strictly `>15 bps`.

Concentration:

- top-1 absolute daily gross-edge contribution share `<=0.25`;
- top-3 share `<=0.55`.

Sign breadth:

- at least `5` completed LONG reversals;
- at least `5` completed SHORT reversals;
- maximum one-sign share `<=0.80`.

Latency robustness:

- 1,000 ms mean `>=25 bps`;
- 1,000 ms 10% trimmed mean `>=20 bps`;
- 2,000 ms mean `>=20 bps`;
- 2,000 ms 10% trimmed mean `>=15 bps`.

State invariants:

- max decisions/day `<=4`;
- max concurrent positions `<=1`;
- no overnight completion/carry.

Any failed gate yields exact terminal token:

`E007_DISCOVERY_FAIL`

and blocks Confirmation/L2/Q2/Validation/Final.

Only all gates PASS yields:

`E007_DISCOVERY_PASS_OPEN_CONFIRMATION_ONCE`.

## 12. Confirmation

Confirmation, if opened, uses the identical frozen financial and execution protocol on `2024-03-22..30` with March 21 as non-performance warm-up/boundary history.

Confirmation gates must be frozen in config before Discovery and may not be changed after seeing Discovery. They use the same economics philosophy with lower sample-count minima appropriate to nine days but no weaker per-trade economics hurdle.

## 13. Diagnostics

No E007 v1.0 diagnostic parameter grid is authorized.

A failed primary may not be rescued by lowering the 80 bps threshold, changing the 60-second displacement window, changing 50% retracement, changing hold, choosing only one sign, or switching reversal to continuation.

## 14. Firewalls

E007 v1.0 may not use:

- E002 TFI;
- E003 FLOW_IMPULSE;
- E004 compression;
- E006 basis;
- L2;
- Q2;
- formal Validation/Final;
- post-hoc day/hour/event/news filters;
- maker/VIP-fee rescue assumptions.

## 15. Preflight gate

Before first E007 alpha, freeze implementation and pass a no-alpha preflight proving exact window boundaries, trigger crossing, sign, half-retracement target, proxy tolerances, state/cap/cooldown semantics, latency replay, data identity and output firewall.

Only exact matching `E007_PREFLIGHT_PASS` may authorize one DEV-DISCOVERY run.
