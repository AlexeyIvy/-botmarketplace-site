# SC001-E006 — Same-Venue SPOT/Perpetual Basis-Convergence Executable Protocol v1.0

Date: 2026-09-15  
Status: **FROZEN BEFORE FIRST E006 PRICE COMPARISON / ALPHA OUTPUT**  
Branch: SCALPING RESEARCH / SC001

Parent planning document:

`docs/research/sc001-e006-same-venue-spot-perp-basis-dislocation-research-plan-v0.2.md`

## 1. Scientific question

Does a rare, causally observed positive dislocation of OKX `BTC-USDT-SWAP` above OKX `BTC-USDT` spot subsequently converge enough to support a low-turnover paired taker strategy after allowing meaningful headroom over four-fill transaction costs?

This is a gross paired-economics screen. It is not executable-net-P&L proof and does not yet use L2 spread/depth.

## 2. Independence and firewalls

E006 is independent from terminal E001/E002/E003/E004 and closed E005.

Base E006 uses none of:

- E002 TFI;
- E003 FLOW_IMPULSE;
- E004 compression state;
- post-hoc event/day/hour filters;
- Q2/Validation/Final data.

Discovery performance: `2024-03-01..20`.  
`2024-03-21` is boundary/warm-up only and permanently performance-excluded.  
Future one-time Confirmation candidate interval: `2024-03-22..30`, only after terminal Discovery PASS.

No E006 price comparison or return may occur before implementation preflight PASS under this exact protocol.

## 3. Primary tradable sign

Primary E006 tests only **positive basis dislocation / rich perpetual**:

- LONG `BTC-USDT` spot;
- SHORT `BTC-USDT-SWAP` perpetual;
- equal USDT reference notional on both legs at entry.

Rationale frozen before alpha: this sign is directly implementable without borrowing BTC spot. The opposite sign would require short/borrow spot BTC or an inventory assumption and is not part of primary E006 v1.0.

Negative-basis performance may not be inspected as a rescue of E006 v1.0.

## 4. Causal 10-second paired price statistic

Evaluation boundaries are exact UTC multiples of 10 seconds.

For each boundary `t` and each leg independently, use trades in the half-open window:

`[t - 10 seconds, t)`.

Require at least one trade in the window for each leg. No trade at timestamp `>= t` is admissible.

For each leg calculate size-weighted trade VWAP:

`VWAP = sum(price * size) / sum(size)`.

For the perpetual archive, `size` is contract count; the contract multiplier is constant within this fixed instrument and therefore does not affect its within-leg VWAP.

A paired price observation is valid only if both leg VWAPs are finite and positive.

## 5. Basis definition

For valid paired observation at `t`:

`basis_bps_t = 10,000 * (perp_vwap_t / spot_vwap_t - 1)`.

Positive basis means the perpetual is rich to spot.

## 6. Causal ordinary-basis baseline

Lookback: exactly the previous 6 hours of scheduled 10-second boundaries, excluding current `t`.

There are 2,160 scheduled observations in 6 hours.

Use only valid paired basis observations in `[t-6h, t)`.

Eligibility requires at least 2,052 valid prior observations (95% of 2,160).

Baseline:

`baseline_bps_t = ordinary median(valid prior basis_bps)`.

Current dislocation:

`dislocation_bps_t = basis_bps_t - baseline_bps_t`.

No current observation enters its own baseline.

## 7. Primary trigger

Threshold: `+50.0 bps` dislocation.

A candidate trigger occurs only on a strict below-to-at/above crossing between consecutive scheduled 10-second grid points:

- previous grid point is valid and eligible;
- `previous_dislocation < 50.0`;
- current grid point is valid and eligible;
- `current_dislocation >= 50.0`.

If the immediately previous grid point is invalid/ineligible, no trigger occurs at the current point.

At trigger freeze:

- trigger timestamp;
- baseline basis from that trigger;
- trigger spot/perp VWAP diagnostics.

The frozen baseline never moves for the life of that episode.

## 8. Position and turnover rules

- maximum one pair pending/open;
- no pyramiding;
- no opposite-sign trade;
- ignore triggers while pending/open/cooldown;
- maximum four entry decisions per UTC day;
- after the fourth entry decision, day is locked;
- cooldown after terminal episode = 10 minutes;
- no overnight carry;
- no new entry decision after `23:29:00.000 UTC`.

## 9. Entry proxy

Primary latency: `500 ms` from trigger timestamp.

For each leg independently:

- entry target = trigger timestamp + 500 ms;
- proxy entry = first qualified trade at or after target;
- proxy entry must occur no later than target + 5,000 ms.

Pair entry is complete only if both legs complete.

`pair_open_ts = max(spot_entry_ts, perp_entry_ts)`.

If either leg fails the 5-second tolerance, the episode is incomplete, incurs no gross-edge observation, enters cooldown, and cannot be retried.

The paired legging span is recorded as `abs(spot_entry_ts - perp_entry_ts)`.

## 10. Exit decision

For an open pair, monitor the same causal 10-second paired VWAP statistic at subsequent grid points.

At each valid point calculate dislocation relative to the **frozen trigger baseline**:

`open_dislocation_bps = current_basis_bps - frozen_baseline_bps`.

Convergence exit condition:

`open_dislocation_bps <= +10.0 bps`.

Maximum holding period: 30 minutes from `pair_open_ts`.

Exit-decision timestamp is the earlier of:

1. first valid 10-second grid point after pair open satisfying convergence condition; or
2. first scheduled 10-second grid point at or after `pair_open_ts + 30 minutes` (time exit; does not require a valid basis observation).

No stop-loss, take-profit beyond convergence rule, trailing rule, reversal or pyramiding.

## 11. Exit proxy

Primary exit latency: same 500 ms from exit-decision timestamp.

For each leg independently:

- target = exit decision + 500 ms;
- proxy exit = first qualified trade at or after target;
- must occur no later than target + 5,000 ms;
- must remain inside the same UTC day.

Pair completion requires both legs.

If an exit proxy is incomplete, the pair is marked incomplete and the strategy is locked through the UTC day end for this coarse stage; no later trade that day may be selected.

## 12. Paired gross-edge normalization

Let equal reference notional `N` be allocated LONG spot and SHORT perpetual at entry.

For a completed pair:

`spot_return = spot_exit / spot_entry - 1`

`short_perp_return = 1 - perp_exit / perp_entry`

Paired gross edge normalized to **one reference-leg notional N**:

`paired_gross_edge_bps = 10,000 * (spot_return + short_perp_return)`.

This normalization deliberately makes four taker fills economically visible. Under the prior regular-user fee reference of about 5 bps per taker fill, a paired open/close cycle is approximately 20 bps of fee burden per reference-leg notional before spread/depth/legging/funding/borrow effects.

## 13. Latency stresses

Primary trigger and exit-decision events are frozen first.

Re-evaluate proxy fills with latency changed only to:

- 1,000 ms;
- 2,000 ms.

The same trigger events, frozen baselines, convergence/time exit decisions and position chronology are reused. Stress scenarios may not create different signal events.

## 14. Discovery metrics

For completed primary 500 ms pairs calculate:

- total entry decisions;
- completed pairs;
- completion rate;
- active days;
- paired gross-edge pooled mean;
- pooled median;
- symmetric 10% trimmed mean;
- daily mean and median active-day mean;
- positive active-day share;
- one-sided 95% day-block-bootstrap lower bound for pooled mean using 10,000 resamples and RNG seed `20260915`;
- top-one and top-three absolute daily contribution shares;
- entry legging-span p50/p95/p99/max;
- convergence-exit share vs time-exit share;
- 1,000 ms and 2,000 ms stress metrics;
- maximum decisions/day and invariant checks.

Symmetric trim removes `floor(0.10*n)` observations from each tail.

## 15. DEV-DISCOVERY gates

Discovery PASS requires **every** primary condition:

1. exact matching implementation preflight PASS;
2. at least 20 completed pairs;
3. at least 10 active days;
4. pair completion rate >= 0.98;
5. pooled mean paired gross edge >= 40.0 bps;
6. 10% trimmed mean >= 35.0 bps;
7. pooled median >= 25.0 bps;
8. median active-day mean >= 30.0 bps;
9. positive active-day share >= 0.70;
10. one-sided 95% day-block-bootstrap lower bound > 20.0 bps;
11. top-one absolute day contribution share <= 0.30;
12. top-three absolute day contribution share <= 0.65;
13. 1,000 ms stress pooled mean >= 35.0 bps and trimmed mean >= 30.0 bps;
14. 2,000 ms stress pooled mean >= 30.0 bps and trimmed mean >= 25.0 bps;
15. maximum entry decisions/day <= 4 and one-pair invariant holds;
16. no source/causality/firewall failure.

Any failure => terminal `E006_DISCOVERY_FAIL`.

All gates pass => `E006_DISCOVERY_PASS_OPEN_CONFIRMATION_ONCE`.

On FAIL: no Confirmation, no paired L2 acquisition, no threshold/baseline/hold/sign rescue.

## 16. DEV-CONFIRMATION gates

Only after Discovery terminal PASS may unchanged rules run once on `2024-03-22..30`.

March 21 may be used only as indicator warm-up/boundary data and never as performance.

Confirmation PASS requires every condition:

1. at least 10 completed pairs;
2. at least 5 active days;
3. completion rate >= 0.98;
4. pooled mean >= 40.0 bps;
5. 10% trimmed mean >= 35.0 bps;
6. pooled median >= 25.0 bps;
7. median active-day mean >= 30.0 bps;
8. positive active-day share >= 2/3;
9. one-sided 95% day-block-bootstrap lower bound > 20.0 bps;
10. top-one absolute day contribution share <= 0.40;
11. top-three absolute day contribution share <= 0.75;
12. 1,000 ms stress mean >= 35.0 bps and trimmed mean >= 30.0 bps;
13. 2,000 ms stress mean >= 30.0 bps and trimmed mean >= 25.0 bps;
14. invariants/firewalls hold.

Any failure => terminal `E006_CONFIRMATION_FAIL`.

All pass => `E006_CONFIRMATION_PASS_OPEN_PAIRED_L2_PROTOCOL_FREEZE`.

## 17. Read-only diagnostic neighborhood

Only after the primary terminal verdict is irreversibly written may exactly these one-factor variants be inspected:

- baseline lookback: 3h, 12h;
- trigger: 40 bps, 60 bps;
- convergence exit: 0 bps, 20 bps;
- maximum hold: 15 min, 60 min.

Exactly eight one-factor variants. They cannot alter primary verdict, open Confirmation, or become a replacement E006 strategy on the same Discovery outcomes.

Negative-basis/borrow-required sign is not part of this diagnostic neighborhood.

## 18. Stop rules

No rescue through:

- opposite basis sign;
- different VWAP/grid/window;
- looser freshness;
- lower trigger;
- alternate baseline/lookback beyond read-only diagnostics;
- different exit/hold beyond diagnostics;
- lower/VIP fees;
- maker assumptions;
- TFI/FLOW_IMPULSE/E004 filters;
- day/hour/event exclusions;
- Q2/Validation/Final exploration.

A materially different hypothesis requires a new experiment identifier and protected data.

## 19. Promotion order

`protocol freeze -> implementation + no-alpha preflight -> DEV-DISCOVERY -> unchanged one-time DEV-CONFIRMATION -> paired L2/execution economics -> later protected temporal validation`

No stage may be skipped.
