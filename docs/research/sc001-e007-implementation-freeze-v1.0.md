# SC001-E007 — Implementation Freeze v1.0

Date: 2026-09-15  
Status: **IMPLEMENTATION FROZEN BEFORE REAL-DATA PREFLIGHT / BEFORE ANY E007 ALPHA**

Parent financial protocol:

`docs/research/sc001-e007-extreme-displacement-mean-reversion-executable-protocol-v1.0.md`

Preflight specification:

`docs/research/sc001-e007-implementation-preflight-spec-v1.0.md`

No E007 real-data displacement, event response, return or P&L was observed before this freeze.

## 1. Frozen executable set

Frozen implementation commit containing the complete current executable set:

`34e0f15ea4b243d534d62bffdee19ccd99416f87`

Files and Git blob identities:

- config: `research/sc001/sc001_e007_config_v1_0.json`
  - Git blob SHA: `4fd29dc7bb0ee1fb650d7eff84989aaf641a1b67`
- engine: `research/sc001/sc001_e007_extreme_reversal_v1.py`
  - Git blob SHA: `275e58ae0954121adbb16e3a27172f600eadec6d`
- preflight runner: `research/sc001/sc001_e007_preflight_v1_0.py`
  - Git blob SHA: `8ec2499a49d6d5e6508118cfbaabe9de4403ebc9`

The authoritative runtime SHA256 values must be computed/recorded by the VPS preflight. Discovery is fail-closed against the exact engine/config SHA256 values in that PASS report.

## 2. Frozen financial semantics

Primary identifier:

`E007_REV_G5_W60_T80_R50_LAT500_H10_CAP4`

Frozen:

- 5-second causal size-weighted VWAP buckets;
- current `[t-5s,t)` versus anchor `[t-65s,t-60s)`;
- 60-second displacement in bps;
- absolute threshold 80 bps;
- below-threshold to at/above-threshold crossing only;
- reversal against both displacement signs;
- frozen arithmetic 50% retracement target;
- primary entry/exit proxy latency 500 ms;
- inclusive 5,000 ms proxy tolerance;
- max hold 10 minutes from actual entry with 5-second grid ceiling;
- one position maximum;
- 10-minute cooldown;
- maximum four decisions per UTC day;
- no new entry after 23:49 UTC;
- no overnight carry;
- 1,000/2,000 ms execution-latency stresses reuse primary accepted events/target/exit-decision;
- no diagnostic parameter grid.

## 3. Frozen implementation boundary semantics

- Current/anchor VWAP windows are half-open and future-proof.
- Previous invalid displacement blocks a trigger.
- Equality at +/-80 bps qualifies on crossing.
- Entry proxy already beyond the frozen retracement target is classified incomplete (`entry_already_reverted`) and is not opened.
- Missing entry begins cooldown from the end of its proxy-tolerance window.
- Missing exit after an opened position locks the remainder of that UTC day.
- Cooldown is half-open; entry at exact cooldown end is allowed.
- Daily cap counts accepted trigger decisions even when later incomplete.
- Displacement chronology carries through UTC midnight; trading state resets without manufacturing a new crossing.

## 4. Economics gates

Discovery gross promotion requires all frozen gates, including:

- 20..80 completed trades;
- >=10 active days;
- completion >=95%;
- mean >=30 bps;
- 10% trimmed mean >=25 bps;
- median >=20 bps;
- median active-day mean >=25 bps;
- positive active-day share >=70%;
- day-block bootstrap 95% LCB >15 bps;
- concentration limits;
- >=5 completed reversals per sign and max one-sign share <=80%;
- 1,000 ms and 2,000 ms latency-stress hurdles.

Frozen Confirmation gates are already stored in config/preflight spec and may not be changed after Discovery.

## 5. Development-side verification

Development-side synthetic/state-machine suite passed `38/38` checks on the implementation logic before this freeze.

This is not the authoritative VPS preflight result.

## 6. Hard gate

DEV-DISCOVERY remains **CLOSED**.

Only exact `E007_PREFLIGHT_PASS` from the qualified VPS, with matching engine/config SHA256, can authorize one frozen Discovery run.

If preflight FAILs, only implementation/data-audit defects may be fixed; financial semantics remain frozen.
