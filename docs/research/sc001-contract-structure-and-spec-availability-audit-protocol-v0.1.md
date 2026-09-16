# SC001 — Contract Structure & Historical-Spec Availability Audit Protocol v0.1

Date: 2026-09-16  
Status: **FROZEN BEFORE TOP-12 CONTRACT-STRUCTURE AUDIT OUTPUT**  
Scope: **SCALPING RESEARCH / SC001**

## 1. Purpose

Audit whether the provisional top-12 produced by `SC001_PREPERIOD_LIQUIDITY_CALIBRATION_PASS` are structurally comparable OKX linear USDT-margined perpetuals and whether there are obvious continuity/relisting problems before the exact universe is frozen.

This stage does **not** claim that current OKX instrument fields are historical 2024 values.

The distinction is binding:

- current `public/instruments` fields are used only for present-day structural/metadata diagnostics;
- exact historical `tickSz`, `lotSz`, `minSz`, `ctVal` and related spec values remain **UNRESOLVED** unless supported by a separate historical evidence artifact;
- current values must never be silently backfilled into a 2024 execution simulation.

No strategy signal/PnL is calculated.

## 2. Frozen parent universe

Parent calibration must be exact:

`SC001_PREPERIOD_LIQUIDITY_CALIBRATION_PASS`

Observed provisional top-12 before this protocol freeze:

1. BTC
2. ETH
3. SOL
4. DOGE
5. ORDI
6. FIL
7. UNI
8. XRP
9. LTC
10. OP
11. BCH
12. SUI

The runner must verify the parent report reproduces this exact deterministic list. No manual substitution is permitted.

## 3. Required parent continuity evidence

Every provisional symbol must also be present in the exact `both_anchor_symbols` set from:

`SC001_HISTORICAL_UNIVERSE_SEEDED_PROBE_PASS`

The two frozen anchor dates remain:

- 2023-12-30;
- 2024-02-29.

Exact historical trade-archive existence on both anchors is the primary historical continuity evidence at this stage.

## 4. Current OKX structural metadata audit

For each exact `<BASE>-USDT-SWAP`, query official public instrument metadata:

`GET /api/v5/public/instruments?instType=SWAP&instId=<INST>`

Require exactly one exact matching row and validate:

- `instId` exact match;
- `instType == SWAP`;
- `ctType == linear`;
- `settleCcy == USDT`;
- finite positive `tickSz`;
- finite positive `lotSz`;
- finite positive `minSz`;
- finite positive `ctVal`;
- non-empty `ctValCcy`;
- parseable positive `listTime`;
- `listTime < 2023-12-31T00:00:00Z`, consistent with exact archive existence on 2023-12-30;
- current state is recorded diagnostically.

If current `listTime` conflicts with historical archive existence, classify `CONTINUITY_REVIEW` rather than assuming the field is historically comparable.

## 5. Historical spec firewall

This audit must print and record:

`historical_exact_tick_lot_min_ctval_verified = False`

unless a separate historical source is explicitly added under a new frozen protocol.

Therefore:

- current `tickSz/lotSz/minSz/ctVal` are diagnostics only;
- final universe selection may use structural comparability/continuity but not current spec magnitude;
- no execution engine may run promotional PnL until exact historical instrument-spec handling is separately frozen.

This avoids survivorship/spec-drift leakage while keeping universe selection independent from strategy outcomes.

## 6. PASS / REVIEW

Exact PASS token:

`SC001_CONTRACT_STRUCTURE_SPEC_AVAILABILITY_AUDIT_PASS`

PASS requires all 12:

- parent calibration exact PASS;
- exact top-12 parent list unchanged;
- present in both-anchor parent pool;
- current exact instrument row resolved;
- linear USDT-settled SWAP structure;
- valid positive current contract fields;
- no `listTime` contradiction with the early anchor.

Otherwise:

`SC001_CONTRACT_STRUCTURE_SPEC_AVAILABILITY_AUDIT_REVIEW`

Do not manually replace a REVIEW symbol. Any universe alteration requires a new prospectively frozen fallback rule.

## 7. Contamination / access firewall

Allowed:
- public instrument metadata;
- parent reports;
- existing calibration metadata.

Forbidden:
- strategy signals/PnL;
- new L2 bodies;
- broad promotional trade bodies;
- choosing symbols based on later performance;
- treating current spec values as historical 2024 truth.

## 8. After PASS

Only after PASS may SC001 create a separate exact multi-asset universe-freeze artifact using the unchanged top-12.

Before any promotional execution simulation, a later stage must still freeze historical contract-spec handling and cost assumptions for the intended research dates.
