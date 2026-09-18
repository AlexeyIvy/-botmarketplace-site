# SC001 Current Roadmap and Stop Rules v4.57

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — C7-D0 PASS / C7-S0 RULES FROZEN / C7-D1 BODY INTEGRITY NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.56.md`

## 1. Binding terminal strategy states

C1-C6 remain terminal `REJECT_SENTINEL`.

C9-S1 remains terminal `C9_S1_REJECT_SENTINEL`.

C8B-S0 remains terminal `C8B_S0_REJECT_HEADROOM`.

C10-S0 remains terminal `C10_S0_REJECT_HEADROOM`.

No rescue tuning is authorized.

## 2. C7-D0 result

Exact:

`C7_D0_MULTI_ASSET_L2_METADATA_PASS`

Observed:

- assets passed = 7/7;
- fixed date = 2024-02-12;
- combined HEAD Content-Length = 1,652,514,627 bytes;
- no L2 body downloaded/opened;
- no spread/depth/maker/fill/queue/adverse-selection/PnL;
- exit code 0.

Binding result:

`docs/research/sc001-c7-d0-multi-asset-l2-metadata-pass-result-v0.1.md`

## 3. C7 price/L2 calibration role declared before body access

Current contamination registry:

`docs/research/sc001-contamination-registry-v0.14.json`

The exact seven 2024-02-12 non-BTC L2 bodies are now:

`NONPROMOTIONAL_SELECTION_CALIBRATION`

for C7.

## 4. C7-S0 frozen before first historical spread outcome

Protocol:

`docs/research/sc001-c7-s0-multi-asset-spread-headroom-sentinel-v0.1.md`

Frozen identity:

`22c61a2e23939db6709b198eab1c7463fb4d404c`

Key prospective rules:

- candidate = C7 passive/hybrid maker universe;
- maker entry + taker fail-safe exit reference;
- maker fee reference = 2 bps;
- taker fee reference = 5 bps;
- adverse/model reserve = 3 bps;
- gross quoted-spread hurdle = 10 bps;
- high-spread persistence = 5 consecutive valid seconds;
- per-asset eligibility:
  - p75 spread >=10 bps;
  - >=20% valid seconds spread >=10 bps;
  - >=100 persistent high-spread episodes;
  - episodes span >=12 UTC hours;
- C7-S0 survives only if >=2/7 assets qualify.

No post-outcome threshold or architecture changes are allowed.

## 5. C7-D1 stage

D1 performs body integrity and per-asset 1-second top-of-book normalization only.

It does not calculate quoted spread or asset eligibility.

Protocol:

`docs/research/sc001-c7-d1-multi-asset-l2-body-integrity-normalization-v0.1.md`

Runner:

`research/sc001/sc001_c7_d1_multi_asset_l2_integrity_v0_1.py`

Freeze:

`docs/research/sc001-c7-d1-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `03793b3cf06a7ed26b5175b413103e65bf2589a7`;
- runner: `7c2c8301a98689873773677a8b37e0d2bb927cec`;
- registry: `aca492af3589aa2783262c7b3c903c5d9e83977f`;
- D0 result: `279a9c6a88455fc401eaa6e1cb3a55867f6e8079`;
- future S0 protocol: `22c61a2e23939db6709b198eab1c7463fb4d404c`.

## 6. D1 acquisition constraints

- sequential heavy downloads;
- one file at a time;
- per-file cap 1 GiB;
- total cap 3 GiB;
- keep at least 15 GiB free disk;
- exact HEAD size must still match D0;
- exact-size local files may be reused.

## 7. D1 normalized output

For each asset write:

`normalized/<ASSET>_top1_1s.csv`

with:

- second_id;
- l2_ts_ms;
- best_bid;
- best_ask;
- best_bid_size;
- best_ask_size.

No spread is calculated in D1.

## 8. Exact D1 states

PASS:

`C7_D1_MULTI_ASSET_L2_INTEGRITY_PASS`

REVIEW:

`C7_D1_MULTI_ASSET_L2_INTEGRITY_REVIEW`

REVIEW remains data/implementation state only.

## 9. Consequence of D1 PASS

Only after exact D1 PASS may the already-frozen C7-S0 spread/headroom runner be implemented and run.

## 10. Immediate next action

Run frozen C7-D1 sequential multi-asset L2 body integrity/normalization on VPS.
