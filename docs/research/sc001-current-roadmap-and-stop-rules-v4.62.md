# SC001 Current Roadmap and Stop Rules v4.62

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — INDEPENDENT BASE REVIEW COMPLETE / C11-C12 IDS ASSIGNED / METADATA-ONLY D0 PREFLIGHTS NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.61.md`

## 1. Binding terminal strategy states

All prior terminal states remain immutable.

- C1-C6: `REJECT_SENTINEL`;
- C9-S1: `C9_S1_REJECT_SENTINEL`;
- C8B-S0: `C8B_S0_REJECT_HEADROOM`;
- C10-S0: `C10_S0_REJECT_HEADROOM`;
- C7-S0: `C7_S0_REJECT_SPREAD_HEADROOM`.

No rescue tuning is authorized.

## 2. Independent base pool reviewed

Three base concepts were reviewed prospectively:

### B1 — Scheduled Tier-1 US Macro Release Impulse
Disposition:

`SELECTED_FOR_FROZEN_EXPERIMENT`

### B2 — Same-Venue Triangular Spot Parity
Disposition:

`REJECT_STRUCTURAL`

Reason:

Three-fill fee floor plus extreme legging/latency requirements are incompatible with the current public-data/non-colocated SC001 architecture.

No backtest is authorized.

### B3 — Stablecoin Parity Dislocation Reversion
Disposition:

`SELECTED_FOR_FROZEN_EXPERIMENT`

Binding review:

`docs/research/sc001-independent-base-b1-b3-comparative-review-v0.1.md`

## 3. New candidate IDs

Assigned:

### C11
`SCHEDULED_TIER1_US_MACRO_RELEASE_IMPULSE`

Assignment freeze:

`docs/research/sc001-c11-candidate-assignment-freeze-v0.1.md`

### C12
`USDC_USDT_STABLECOIN_PARITY_DISLOCATION_REVERSION`

Assignment freeze:

`docs/research/sc001-c12-candidate-assignment-freeze-v0.1.md`

No outcome-bearing run is authorized by ID assignment alone.

## 4. C11 independence

C11 base event is external:

- official U.S. CPI releases;
- official U.S. Employment Situation releases.

Initial market:

- BTC-USDT-SWAP.

C11 does not use:

- C3 range/expansion selection;
- C5 flow labels;
- C10 L2 vacuum labels;
- any RB001-RB018 auxiliary block.

## 5. C12 independence

C12 base mechanism:

- direct USDC-USDT spot cross-rate;
- external stablecoin parity/redemption anchor;
- one-sided two-fill spot architecture.

C12 is not:

- C2 local-reference mean reversion;
- C8B cross-venue paired convergence.

No moving-average/local-reference rescue is authorized.

## 6. Edge-to-Fill status

### C11
Preliminary structural burden:

- two taker fills;
- fee reference ~10 bps;
- event slippage/model reserve ~10 bps;
- provisional burden ~20 bps.

Classification:

`UNKNOWN_NEEDS_NON_ALPHA_HEADROOM_SENTINEL`

Mechanism has a credible exogenous reason for tens-of-bps moves.

### C12
Preliminary structural burden:

- two spot fills;
- fee reference ~10 bps;
- spread/slippage/model reserve ~5 bps;
- provisional burden ~15 bps.

Classification:

`UNKNOWN_NEEDS_NON_ALPHA_HEADROOM_SENTINEL`

Mechanism has a fixed external parity anchor and potential stress-scale deviations.

## 7. C11-D0 frozen metadata-only stage

Protocol:

`docs/research/sc001-c11-d0-source-calendar-preflight-protocol-v0.1.md`

Runner:

`research/sc001/sc001_c11_d0_source_calendar_preflight_v0_1.py`

Freeze:

`docs/research/sc001-c11-d0-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `5d2ae42f6f90875947d6b285d57954139a8b41fa`;
- runner: `f0f4b2a414596d959f62da2304f3a198718c8bd4`;
- freeze: `a5df9975af5f5b854948e2951b91ce98637098f7`.

D0 verifies:

- official BLS schedule metadata for one CPI and one Employment representative;
- current BTC-USDT-SWAP semantics;
- exact historical BTC trade-archive metadata/HEAD for those representative dates.

No trade body or post-release move is opened.

## 8. C12-D0 frozen metadata-only stage

Protocol:

`docs/research/sc001-c12-d0-source-parity-preflight-protocol-v0.1.md`

Runner:

`research/sc001/sc001_c12_d0_source_parity_preflight_v0_1.py`

Freeze:

`docs/research/sc001-c12-d0-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `7744528ae6bf0d17dcc816fa1484e7bde6a70189`;
- runner: `7236aea35b83fa83df9a03dd8b91c0a9fe4dafc0`;
- freeze: `d92ff1328e08d1c9a8bae567368867955662d184`.

D0 verifies:

- current USDC-USDT spot semantics;
- external parity-source availability;
- exact historical USDC-USDT trade-archive metadata/HEAD for 2025-01-15.

No historical price body or peg deviation is opened.

## 9. Exact D0 states

C11 PASS:

`C11_D0_SOURCE_CALENDAR_PREFLIGHT_PASS`

C11 REVIEW:

`C11_D0_SOURCE_CALENDAR_PREFLIGHT_REVIEW`

C12 PASS:

`C12_D0_SOURCE_PARITY_PREFLIGHT_PASS`

C12 REVIEW:

`C12_D0_SOURCE_PARITY_PREFLIGHT_REVIEW`

REVIEW states are engineering/source states only.

## 10. Hard firewalls

C11-D0 must keep false:

- trade body access;
- macro release value/surprise;
- post-release move;
- direction signal;
- PnL;
- promotional alpha.

C12-D0 must keep false:

- trade body access;
- peg deviation;
- reversion outcome;
- threshold selection;
- PnL;
- promotional alpha.

## 11. Immediate next action

Run C11-D0 and C12-D0 metadata-only preflights on VPS.

Only after exact PASS may each candidate separately freeze its Selection/Calibration chronology and cheapest outcome-bearing sentinel.

No C11/C12 price outcome is authorized yet.
