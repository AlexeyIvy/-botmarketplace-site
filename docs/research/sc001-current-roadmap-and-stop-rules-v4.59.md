# SC001 Current Roadmap and Stop Rules v4.59

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — C7-D1 v0.2 PASS / C7-S0 SPREAD-HEADROOM SENTINEL FROZEN NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.58.md`

## 1. Binding terminal strategy states

C1-C6 remain terminal `REJECT_SENTINEL`.

C9-S1 remains terminal `C9_S1_REJECT_SENTINEL`.

C8B-S0 remains terminal `C8B_S0_REJECT_HEADROOM`.

C10-S0 remains terminal `C10_S0_REJECT_HEADROOM`.

C7 still has no strategy verdict.

## 2. C7-D1 v0.2 result

Exact:

`C7_D1_V02_MULTI_ASSET_L2_INTEGRITY_PASS`

Observed:

- assets passed = 7/7;
- inherited v0.1 PASS assets = 6;
- DOGE leading updates skipped = 3609;
- DOGE first snapshot index = 3610;
- DOGE first snapshot timestamp = 1707696060009;
- DOGE valid sampled seconds = 86,338;
- DOGE active UTC hours = 24;
- quoted spread / C7 asset eligibility remained false;
- no maker/fill/queue/adverse-selection/PnL;
- exit code 0.

Binding result:

`docs/research/sc001-c7-d1-v0.2-multi-asset-l2-integrity-pass-result-v0.1.md`

## 3. C7-S0 remains prospectively frozen

Protocol:

`docs/research/sc001-c7-s0-multi-asset-spread-headroom-sentinel-v0.1.md`

Runner:

`research/sc001/sc001_c7_s0_multi_asset_spread_headroom_v0_1.py`

Freeze:

`docs/research/sc001-c7-s0-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `22c61a2e23939db6709b198eab1c7463fb4d404c`;
- runner: `d8d315ee62b5e543b705787931a49a0196e6c2a2`;
- registry: `aca492af3589aa2783262c7b3c903c5d9e83977f`;
- D1 v0.2 result: `5428d0bf3003f56c7348cb83d8f07fcbb635afee`.

## 4. Frozen structural architecture

C7 eligibility reference:

- maker entry;
- taker fail-safe exit;
- maker fee reference 2 bps;
- taker fee reference 5 bps;
- adverse/model reserve 3 bps;
- gross quoted-spread hurdle = 10 bps.

No exact execution claim is implied.

## 5. Frozen persistence and per-asset gates

High-spread regime:

- quoted spread >=10 bps;
- at least 5 consecutive valid wall-clock seconds.

Per-asset structural eligibility requires all:

- data: >=80,000 valid seconds and 24 UTC hours;
- p75 quoted spread >=10 bps;
- share of valid seconds spread >=10 bps >=0.20;
- >=100 persistent high-spread episodes;
- episodes span >=12 UTC hours.

Percentiles use nearest-rank semantics.

## 6. Universe survival rule

C7-S0 survives only if:

- at least 2 of 7 frozen assets satisfy all per-asset structural gates.

Exact states:

- `C7_S0_SPREAD_HEADROOM_SURVIVE`;
- `C7_S0_REJECT_SPREAD_HEADROOM`;
- `C7_S0_DEFER_DATA_QUALITY`.

## 7. What S0 does not calculate

S0 must keep false:

- maker-order simulation;
- fill model;
- queue model;
- adverse-selection outcome;
- PnL;
- promotional alpha.

SURVIVE only authorizes a later exact fee/queue/adverse-selection research stage.

## 8. Hard no-rescue rules

After S0 output do not:

- lower 10 bps;
- lower 5-second persistence;
- change p75/share/episode gates;
- change date;
- add BTC;
- select a historical winner subset outside the frozen universe;
- switch architecture merely because hybrid screen fails.

Any materially different maker mechanism requires a new ID.

## 9. Immediate next action

Run frozen C7-S0 exactly once on the seven qualified 2024-02-12 normalized top-of-book series.
