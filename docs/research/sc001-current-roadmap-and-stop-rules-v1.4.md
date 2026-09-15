# SC001 Current Roadmap and Stop Rules v1.4

Date: 2026-09-15  
Status: **CURRENT SC001 ROADMAP SNAPSHOT**

Supersedes for current SC001 execution order: `sc001-current-roadmap-and-stop-rules-v1.3.md`.

## 1. Preserved terminal decisions

Unchanged:

- E001: terminal `FAIL`; no rescue tuning.
- E002: terminal standalone `TAKER_ECONOMICS_FAIL`; TFI is retained only as a future auxiliary/filter/ranking/execution-timing/meta-model feature.
- E003: terminal `E003_DISCOVERY_FAIL`; no E003 Confirmation, no E003 L2 and no rescue tuning.
- Q2, formal Validation and Final remain closed.

SC001 remains fully independent from R009-E002, R003-E003 Binance, R003-X003 Bybit, R010-E001 and Safe-Sleeve S002. Nothing in SC001 changes their rules, decisions or forward clocks.

## 2. Canonical E004 financial protocol

Canonical financial protocol remains:

`docs/research/sc001-e004-volatility-compression-breakout-executable-protocol-v1.0.md`

Primary identifier:

`E004_P_W15_Q20_LB1440_B2_ARM15_LAT250_H15_CAP4`

The frozen base strategy remains independent of E002 TFI and E003 FLOW_IMPULSE.

The primary Discovery gross-economics hurdle remains deliberately materially above the approximately 10 bps regular-user round-trip taker fee reference, with robust median, trimmed-mean, daily breadth, concentration, side-balance, turnover and latency gates.

## 3. Preflight specification correction

The active implementation preflight specification is now:

`docs/research/sc001-e004-implementation-preflight-spec-v1.1.md`

v1.1 supersedes preflight-spec v1.0 only because v1.0 incorrectly required individual OKX archive labels to be bounded by the same UTC calendar date.

The qualified Q006R source semantics instead require target UTC day `D` to be reconstructed from archive labels `D` and `D+1`, retaining only `[D 00:00 UTC, D+1 00:00 UTC)` rows.

This correction was made before any E004 alpha and does not alter the E004 financial protocol or gates.

## 4. E004 implementation status

Implementation is now frozen before real-data preflight:

`docs/research/sc001-e004-implementation-freeze-v1.0.md`

Frozen executable set:

- `research/sc001/sc001_e004_config_v1_0.json`
- `research/sc001/sc001_e004_volatility_breakout_v1.py`
- `research/sc001/sc001_e004_preflight_v1_1.py`

Implementation freeze document records the Git blob identities and boundary semantics.

A development-side synthetic/metamorphic audit passed `34/34` implemented checks. This is not the authoritative preflight result.

## 5. Current hard gate

E004 DEV-DISCOVERY is **NOT YET AUTHORIZED**.

The next mandatory action is to run the complete v1.1 preflight on the qualified Timeweb VPS against the already-qualified March trade archives.

The preflight must remain no-alpha and must verify:

- exact source manifest identities and SHA256;
- ZIP/CSV/schema/order integrity;
- Q006R D + D+1 UTC reconstruction;
- all required synthetic/metamorphic checks;
- real-data March 1..20 state-machine dry run with return calculation/export disabled;
- first eligible boundary = 2024-03-02 00:15 UTC;
- state invariants and four-decisions/day cap;
- forbidden-output firewall;
- free-disk reserve;
- peak memory < 6 GiB.

Only exact terminal token:

`PREFLIGHT_PASS`

with matching engine/config SHA256 authorizes DEV-DISCOVERY.

## 6. After preflight

### If `PREFLIGHT_FAIL`

- do not run Discovery;
- inspect only implementation/data-audit failure reasons;
- financial formula, parameters, gates and diagnostic neighborhood remain frozen;
- if a software defect is fixed, assign a new implementation identity/freeze and rerun the complete preflight.

No structural preflight count may be used for retuning.

### If `PREFLIGHT_PASS`

Run exactly one E004 DEV-DISCOVERY on 2024-03-01..20 under the frozen protocol and implementation.

Discovery terminal PASS requires every frozen gate. Any one gate failure gives terminal:

`E004_DISCOVERY_FAIL`

and blocks Confirmation, E004 L2, Q2, Validation and Final.

Only exact terminal:

`E004_DISCOVERY_PASS_OPEN_CONFIRMATION_ONCE`

opens unchanged one-time DEV-CONFIRMATION 2024-03-21..30.

## 7. Diagnostics firewall

The eight one-factor diagnostic variants remain read-only and may run only after the primary terminal verdict is written.

They cannot:

- rescue a failed E004;
- alter the primary verdict;
- select a replacement primary;
- open Confirmation;
- justify Q2/Validation/Final.

Any new candidate inspired by a diagnostic requires a new experiment identifier and protected data.

## 8. Infrastructure

Primary heavy compute remains the qualified Timeweb Cloud VPS:

- Ubuntu 24.04;
- 4 vCPU;
- 8 GB RAM;
- 80 GB NVMe;
- non-root `botmarket`;
- SSH key authentication;
- tmux.

Android/Termux remains the control client.

Never store server IP, passwords, private SSH keys, API keys or credentials in GitHub.

## 9. Immediate next action

Run `sc001_e004_preflight_v1_1.py` on the qualified VPS only.

Do **not** run `sc001_e004_volatility_breakout_v1.py discovery` until the generated report returns exact `PREFLIGHT_PASS` and its code/config identities match the frozen executable set.
