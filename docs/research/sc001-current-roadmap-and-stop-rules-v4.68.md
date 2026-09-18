# SC001 Current Roadmap and Stop Rules v4.68

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — C11-S1 DEFER DUE ZERO 1s IMPULSE / C12-D3 ACTIVE**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.67.md`

## 1. Binding prior strategy states

All prior terminal strategy states remain immutable.

C11-S0 remains:

`C11_S0_EVENT_MOVE_HEADROOM_SURVIVE`

No C11 execution/PnL claim is authorized.

## 2. C11-S1 result

Exact:

`C11_S1_DEFER_SAMPLE`

Observed:

- valid events = 11/12;
- sole invalid event = Employment Situation 2025-05-02;
- exit code = 0.

The runner did not calculate a continuation verdict because the frozen sample gate failed.

Therefore printed zero continuation counts and None median/p75 are not negative mechanism evidence.

## 3. C11-S1 diagnostic

Binding diagnostic:

`docs/research/sc001-c11-s1-2025-05-02-zero-first-impulse-diagnostic-v0.1.md`

For 2025-05-02:

- pre anchor valid, staleness 122 ms;
- +1s anchor valid, staleness 117 ms;
- +60s anchor valid, staleness 30 ms;
- first post-event trade latency 134 ms;
- first impulse = exactly 0.0 bps.

Classification:

`VALID_SOURCE_AND_ANCHORS / ZERO_DIRECTION_UNDER_FROZEN_1S_RULE`

## 4. C11 consequence

The exact C11-S1 v0.1 one-second direction rule remains unresolved and must not be rescued inside the same experiment.

Do not:

- exclude the zero event;
- run the 11-event subset as the frozen verdict;
- lengthen the one-second impulse window;
- infer direction from later trades;
- switch to reversal.

A materially different direction rule requires fresh prospective evidence and a new experiment ID/rule set.

## 5. What C11 still established

The C11 base mechanism remains interesting because S0 showed decisive raw event move headroom:

- 11/12 events >=20 bps absolute 60s move;
- median ~45.26 bps;
- p75 ~88.17 bps;
- max ~162.75 bps.

The unresolved problem is causal directional extraction after the release.

## 6. C12 current stage

C12-D3 remains the active engineering stage.

Expected PASS:

`C12_D3_H1_BODY_INTEGRITY_PASS`

No peg-deviation outcome is authorized before exact D3 PASS.

## 7. Immediate next action

Inspect C12-D3 progress/terminal state.

Do not launch another C11 directional experiment yet.
