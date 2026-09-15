# SC001-E004 — Implementation Freeze v1.0

Date: 2026-09-15  
Status: **IMPLEMENTATION FROZEN BEFORE REAL-DATA PREFLIGHT / BEFORE ANY E004 ALPHA**

Parent financial protocol:

`docs/research/sc001-e004-volatility-compression-breakout-executable-protocol-v1.0.md`

Corrected preflight specification:

`docs/research/sc001-e004-implementation-preflight-spec-v1.1.md`

This freeze occurs before any E004 return, edge, P&L, direction-specific performance result, Discovery aggregate or Confirmation result has been observed.

## 1. Frozen executable files

Frozen implementation commit containing the complete current file set:

`aa2da0de490bf56d1c59b92c872b90b9d255b2a6`

Files and Git blob identities:

- config: `research/sc001/sc001_e004_config_v1_0.json`
  - Git blob SHA: `6cc4a393fd3b0e34b2e21eac2d5b76faedb9f3e1`
- engine: `research/sc001/sc001_e004_volatility_breakout_v1.py`
  - Git blob SHA: `06219ca8810d68e11c35c2819120e934364ffe67`
- preflight runner: `research/sc001/sc001_e004_preflight_v1_1.py`
  - Git blob SHA: `4ece429913a17493fa8801864689351504abfc23`

The authoritative runtime SHA256 values of config, engine and preflight runner must be computed and recorded by the v1.1 preflight report on the qualified VPS. Discovery is fail-closed against the exact config/engine SHA256 values recorded by that report.

## 2. Frozen financial semantics

Primary identifier remains:

`E004_P_W15_Q20_LB1440_B2_ARM15_LAT250_H15_CAP4`

Unchanged:

- 15-minute causal trade-price compression range;
- rolling 1,440-minute nearest-rank q20 threshold;
- compression equality counts as compressed;
- false-to-true compression transition only;
- frozen upper/lower band with 2 bps buffer;
- 15-minute arm;
- 250 ms primary latency;
- 15-minute hold from actual proxy entry;
- 500 ms and 1,000 ms latency stresses reuse the primary decision events;
- maximum one pending/open position;
- 15-minute cooldown;
- maximum four breakout decisions per UTC day;
- no stop, target, trailing exit, pyramiding, reversal or overnight carry;
- no E002 TFI or E003 FLOW_IMPULSE in base E004;
- Discovery/Confirmation economics gates remain exactly those in protocol v1.0.

## 3. Frozen implementation boundary semantics

The following pre-alpha implementation resolutions are now frozen.

### 3.1 UTC source reconstruction

Use the already-qualified Q006R semantics. Target UTC day `D` is reconstructed from archive labels `D` and `D+1`, admitting only rows in:

`[D 00:00:00.000 UTC, D+1 00:00:00.000 UTC)`.

Do not require a single OKX archive label to be UTC-midnight bounded.

### 3.2 Indicator versus trading state at UTC midnight

The 1,440-minute indicator history and previous eligible compression flag carry causally across UTC midnight.

Transient trading state resets at UTC midnight:

- ARMED;
- PENDING/OPEN;
- COOLDOWN;
- DAY_LOCKED;
- daily decision count.

No overnight position is allowed.

### 3.3 Arming timestamp

A trade at exactly the arming timestamp cannot break the newly created band. Breakout inspection begins strictly after arm time.

### 3.4 Arm expiry

Expiry is inclusive:

`arm_ts < breakout_trade_ts <= expiry_ts`.

A strict band crossing exactly at expiry is eligible.

### 3.5 Cooldown

Cooldown is half-open. At exactly `cooldown_end`, the strategy may return to IDLE before evaluating that minute's arming condition.

### 3.6 Entry/exit tolerance

A proxy print exactly 5,000 ms after the target timestamp is eligible. A later print is not.

### 3.7 Daily cap

The four-per-day cap counts breakout decisions whether or not the later proxy entry/exit completes. The fourth decision locks additional decisions for that UTC day.

### 3.8 Confirmation warm-up

If and only if Discovery terminally PASSes, Confirmation decisions begin on 2024-03-21. Indicator-only warm-up begins on 2024-03-19 so the unchanged 15-minute statistic and 1,440-minute threshold are causally available before the protected Confirmation decision interval. No pre-Confirmation return is emitted from warm-up data.

## 4. Gross-edge aggregation semantics

Completed-trade response remains:

`direction * 10,000 * (exit_price / entry_price - 1)` bps.

- pooled metrics are completed-trade weighted;
- active-day metrics use UTC days with at least one completed primary trade;
- 10% symmetric trimmed mean removes `floor(0.10*n)` observations from each tail;
- day concentration uses absolute daily gross-edge contribution shares;
- completion rate is completed trades divided by breakout decisions;
- day-block bootstrap uses 10,000 resamples, active UTC days as blocks, seed `20260915`, and the nearest-rank 5th percentile as the one-sided lower bound.

## 5. Output and gate firewalls

The engine must refuse Discovery unless the exact preflight report status is:

`PREFLIGHT_PASS`

and its config/engine SHA256 identities match the current executable files.

Confirmation additionally requires exact Discovery terminal token:

`E004_DISCOVERY_PASS_OPEN_CONFIRMATION_ONCE`

with matching engine/config identity.

The implementation refuses to overwrite a non-empty completed phase output directory.

Q2, formal Validation, Final and E004 L2 remain closed.

## 6. Preflight test state

A development-side synthetic/metamorphic audit of the frozen logic passed all currently implemented checks (`34/34`) before this implementation freeze.

This is not the authoritative preflight verdict. The authoritative status is produced only by running `sc001_e004_preflight_v1_1.py` on the qualified VPS against the already-qualified March archives.

The VPS run must additionally pass:

- archive SHA/CRC/schema/order checks;
- Q006R UTC-day reconstruction for March 1..20;
- real-data no-alpha state-machine dry run;
- first eligible boundary check;
- no-alpha output firewall scan;
- state invariants;
- disk and <6 GiB peak-memory gates.

## 7. Stop rule

Before exact `PREFLIGHT_PASS`, do not run E004 DEV-DISCOVERY.

If preflight FAILs because of an implementation defect, only the implementation defect may be fixed. Financial formula, gates, parameters and diagnostic neighborhood remain frozen. The new code identity must then be re-frozen and the entire preflight rerun.

No preflight structural count may be used to retune E004.
