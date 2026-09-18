# SC001 — C11-S1 2025-05-02 Zero First-Impulse Diagnostic v0.1

Date: 2026-09-18
Status: **DIAGNOSTIC COMPLETE — ZERO FIRST IMPULSE / SOURCE AND ANCHORS VALID**
Scope: `SCALPING RESEARCH / SC001`

Parent:

`docs/research/sc001-c11-s1-v0.1-sample-defer-review-v0.1.md`

## 1. Diagnostic target

Frozen event:

`Employment Situation — 2025-05-02 12:30:00 UTC`

Archive:

`BTC-USDT-SWAP-trades-2025-05-02.zip`

## 2. Source integrity

Observed:

- ZIP CRC: PASS;
- regular member count: 1;
- exact CSV header: true;
- rows scanned through +60s anchor: 1,412,480.

No source/schema failure was identified.

## 3. Frozen anchors

### Pre-event
- timestamp: 2025-05-02T12:29:59.878000Z;
- staleness: 122 ms;
- trade_id: 1501751448;
- validity: PASS.

### +1 second
- timestamp: 2025-05-02T12:30:00.883000Z;
- staleness: 117 ms;
- trade_id: 1501751459;
- validity: PASS.

### +60 seconds
- timestamp: 2025-05-02T12:30:59.970000Z;
- staleness: 30 ms;
- trade_id: 1501764462;
- validity: PASS.

First post-event trade latency:

`134 ms`

## 4. Exact failure cause

All frozen temporal validity checks passed.

The sole failure was:

`first_impulse_bps = 0.0`

Therefore:

`first_impulse_nonzero = false`

The C11-S1 v0.1 sample gate required all 12 frozen events to have a nonzero first 1-second impulse.

Hence the exact terminal state remains:

`C11_S1_DEFER_SAMPLE`

## 5. Interpretation

This is not missing data, stale data, or a timestamp problem.

It is a genuine no-direction state under the prospectively frozen one-second signal definition: the +1s trade price equals the pre-event anchor price.

The frozen rule therefore produces no long/short direction for this event.

## 6. Research consequence

Do not:

- drop 2025-05-02;
- infer a direction from later trades;
- extend the impulse window to 2s/5s/10s inside C11-S1;
- convert zero impulse into long or short;
- calculate the 11-event continuation verdict as if it were the frozen 12-event test.

Any alternative signal rule such as:

- first nonzero post-release price change;
- longer first-impulse window;
- explicit no-trade on zero impulse;

is a materially different directional decision rule and requires a new prospectively frozen experiment on fresh evidence.

## 7. What remains valid

C11-S0 remains a binding survivor:

`C11_S0_EVENT_MOVE_HEADROOM_SURVIVE`

Thus scheduled macro events still have strong raw 60-second move headroom.

What remains unresolved is the exact v0.1 one-second direction rule.
