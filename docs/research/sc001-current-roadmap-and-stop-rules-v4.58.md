# SC001 Current Roadmap and Stop Rules v4.58

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — C7-D1 v0.1 DOGE SEMANTIC REVIEW / v0.2 TARGETED REPAIR FROZEN**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.57.md`

## 1. Binding strategy states

C1-C6 remain terminal `REJECT_SENTINEL`.

C9-S1 remains terminal `C9_S1_REJECT_SENTINEL`.

C8B-S0 remains terminal `C8B_S0_REJECT_HEADROOM`.

C10-S0 remains terminal `C10_S0_REJECT_HEADROOM`.

C7 has no strategy verdict yet.

## 2. C7-D1 v0.1 result

Exact:

`C7_D1_MULTI_ASSET_L2_INTEGRITY_REVIEW`

Observed:

- assets passed = 6/7;
- all 7 bodies downloaded;
- six assets normalized successfully;
- only DOGE failed;
- DOGE error = `first action not snapshot`;
- no quoted spread or asset eligibility calculated;
- no maker/fill/queue/adverse-selection/PnL;
- exit code 2.

Classification:

`MULTI_ASSET_L2_LEADING_ACTION_SEMANTICS_REVIEW / NOT_RESEARCH_FAIL`

## 3. DOGE diagnostic

Read-only diagnostic established:

- leading updates before first snapshot = 3609;
- first snapshot index = 3610;
- first snapshot timestamp = 1707696060009;
- first snapshot UTC ≈ 2024-02-12T00:01:00.009Z;
- result = `FIRST_SNAPSHOT_FOUND`.

Binding diagnostic:

`docs/research/sc001-c7-d1-doge-leading-update-diagnostic-result-v0.1.md`

## 4. Replay semantics repair

C7-D1 v0.2 freezes:

`discard leading updates until first snapshot`

Rules:

- validate leading records but do not apply them to an empty book;
- begin reconstruction from the first full snapshot;
- leave earlier grid seconds missing;
- do not synthesize/backfill the initial book;
- preserve all later snapshot/update semantics.

This is source-semantics repair only.

## 5. No research-rule changes

Unchanged:

- 7-asset frozen universe;
- 2024-02-12 date;
- 1-second causal grid;
- 1000 ms freshness;
- >=80,000 valid seconds per asset;
- 24 UTC hours;
- frozen C7-S0 protocol and 10 bps spread hurdle.

No spread outcome has been opened.

## 6. Efficient v0.2 inheritance

The six v0.1 PASS assets may be inherited only after local identity re-verification of:

- source archive bytes + SHA256;
- normalized CSV bytes + SHA256;
- original valid-second and 24-hour gates.

Only DOGE is replayed under the repaired semantics.

This avoids repeating six unnecessary full L2 replays while preserving source integrity.

## 7. C7-D1 v0.2 frozen implementation

Protocol:

`docs/research/sc001-c7-d1-multi-asset-l2-body-integrity-normalization-v0.2.md`

Runner:

`research/sc001/sc001_c7_d1_v02_multi_asset_l2_integrity.py`

Freeze:

`docs/research/sc001-c7-d1-v0.2-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `b30cafe0a926c9d67ace9ef826c773a007bc517a`;
- runner: `39ae25ef13b4d03569cb87d7cf66ced9b522a742`;
- registry: `aca492af3589aa2783262c7b3c903c5d9e83977f`;
- DOGE diagnostic: `b06edcf8088f4f89e9137a6257b93c81acf9d308`.

## 8. Exact v0.2 states

PASS:

`C7_D1_V02_MULTI_ASSET_L2_INTEGRITY_PASS`

REVIEW:

`C7_D1_V02_MULTI_ASSET_L2_INTEGRITY_REVIEW`

REVIEW remains data/implementation only.

## 9. Firewalls

Must remain false:

- quoted spread;
- C7 asset eligibility;
- maker simulation;
- fill model;
- queue model;
- adverse-selection outcome;
- PnL;
- promotional alpha.

## 10. Consequence of PASS

Only after exact v0.2 PASS may the already-frozen C7-S0 spread/headroom sentinel be implemented and run.

## 11. Immediate next action

Run targeted frozen C7-D1 v0.2 on VPS.
