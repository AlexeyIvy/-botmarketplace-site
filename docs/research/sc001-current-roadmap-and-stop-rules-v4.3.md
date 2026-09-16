# SC001 Current Roadmap and Stop Rules v4.3

Date: 2026-09-16  
Status: **CURRENT SC001 ROADMAP — LIQUIDITY CALIBRATION PASS / CONTRACT-STRUCTURE AUDIT OPEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.2.md`

## 1. Binding terminal state

E001-E008 remain terminal/closed. E008 remains exact `E008_DISCOVERY_FAIL`.

No prior verdict is reopened. SC001 remains independent from `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` and `Safe-Sleeve S002`.

## 2. Historical universe pipeline status

Completed:

- blank/wildcard historical enumeration -> `SC001_HISTORICAL_UNIVERSE_METADATA_PROBE_REVIEW` (method rejected, no body access);
- seeded historical enumeration -> `SC001_HISTORICAL_UNIVERSE_SEEDED_PROBE_PASS`;
- both-anchor historical candidate pool = `66`;
- pre-period liquidity calibration -> `SC001_PREPERIOD_LIQUIDITY_CALIBRATION_PASS`;
- liquidity-eligible instruments = `50`.

No strategy signal/PnL has been used in universe construction.

## 3. Provisional deterministic top-12

Frozen selection rule in the parent calibration produced:

1. `BTC-USDT-SWAP`
2. `ETH-USDT-SWAP`
3. `SOL-USDT-SWAP`
4. `DOGE-USDT-SWAP`
5. `ORDI-USDT-SWAP`
6. `FIL-USDT-SWAP`
7. `UNI-USDT-SWAP`
8. `XRP-USDT-SWAP`
9. `LTC-USDT-SWAP`
10. `OP-USDT-SWAP`
11. `BCH-USDT-SWAP`
12. `SUI-USDT-SWAP`

This list is still **provisional** until contract-structure/spec-availability audit passes.

## 4. Calibration contamination recorded

Current registry:

`docs/research/sc001-contamination-registry-v0.2.json`

The six liquidity-calibration dates `2024-02-24..2024-02-29` are now permanently engineering/contaminated for redesigned strategy research across the calibrated universe.

They must not later be presented as untouched Discovery/Confirmation evidence for the redesigned system.

## 5. Historical spec caution

OKX current public instrument metadata exposes fields such as `tickSz`, `lotSz`, `minSz`, `ctVal`, `ctType`, `settleCcy` and `listTime`.

Current values are **not historical proof** of 2024 values and may not be silently backfilled into a historical execution simulation.

Therefore the current hard gate separates:

- structural/continuity audit now;
- exact historical execution-spec reconstruction later, before promotional execution/PnL.

## 6. Current hard gate — contract structure/spec availability audit

Protocol:

`docs/research/sc001-contract-structure-and-spec-availability-audit-protocol-v0.1.md`

Runner:

`research/sc001/sc001_contract_structure_spec_availability_audit.py`

Required exact terminal:

`SC001_CONTRACT_STRUCTURE_SPEC_AVAILABILITY_AUDIT_PASS`

PASS requires all 12:

- unchanged parent top-12;
- presence in both historical anchor pool;
- exact current OKX instrument row;
- `SWAP`;
- `linear` contract type;
- `USDT` settlement;
- valid positive current contract fields;
- no current `listTime` contradiction with exact archive existence on 2023-12-30.

The report must still state:

`historical exact tick/lot/min/ctVal verified = False`

This is deliberate and prevents current-spec look-ahead from contaminating historical execution.

## 7. Next sequence after audit PASS

1. freeze exact first-generation multi-asset universe in a separate artifact;
2. freeze fresh chronology roles (engineering / Discovery / asset holdout / chronological Confirmation / forward);
3. backfill exact contamination status for chosen dates/instruments;
4. build common normalized market-data/accounting infrastructure;
5. freeze historical instrument-spec handling for the chosen chronology before execution;
6. build and mechanically validate taker execution kernel under the simulation/accounting standard;
7. run cheap E007 economic-feasibility audit across the frozen universe;
8. only if warranted, open one strict new-ID E007 multi-asset replication.

Passive-maker execution v2 remains a later parallel track and does not block E007.

## 8. Stop rules

Do not:

- manually replace any provisional top-12 symbol after calibration output;
- use current `tickSz/lotSz/minSz/ctVal` as if they were proven 2024 values;
- download broad multi-asset L2 bodies before universe/chronology/execution requirements are frozen;
- calculate strategy PnL during universe governance;
- reuse calibration dates as untouched promotion;
- reopen E001-E008.

## 9. Immediate VPS action

1. `git pull --ff-only`;
2. syntax-check `research/sc001/sc001_contract_structure_spec_availability_audit.py`;
3. run the audit once;
4. report terminal token and any REVIEW symbols/reasons;
5. do not begin strategy simulation until output is reviewed.
