# SC001 — Historical Execution-Spec Inventory Protocol v0.1

Date: 2026-09-16  
Status: **FROZEN BEFORE HISTORICAL SPEC INVENTORY OUTPUT**

## 1. Purpose

Build a fail-closed evidence inventory for the frozen first-generation universe before any real historical discrete execution/PnL.

This stage does **not** claim that July/August 2024 `tickSz`, `lotSz`, `minSz`, `ctVal` are resolved. It only:

- snapshots current OKX instrument metadata for all 12 frozen instruments;
- records already-known official dated adjustment/listing evidence in a frozen repository evidence pack;
- reports which required historical fields remain unresolved;
- preserves the rule that current metadata is diagnostic only, never historical proof.

No July/August market-data body is opened. No signal/PnL is calculated.

## 2. Parent gates

Require:

- frozen universe `docs/research/sc001-first-generation-multi-asset-universe-freeze-v1.0.json`;
- `SC001_COMMON_ACCOUNTING_CORE_VALIDATION_PASS`, 20/20;
- `SC001_TAKER_KERNEL_SYNTHETIC_VALIDATION_PASS`, 24/24;
- binding evidence standard `docs/research/sc001-historical-execution-spec-evidence-standard-v0.1.md`.

## 3. Frozen universe

Exactly:

`BTC, ETH, SOL, DOGE, ORDI, FIL, UNI, XRP, LTC, OP, BCH, SUI`

all as OKX linear `USDT-SWAP`.

## 4. Required current metadata snapshot

For every exact instrument retrieve from official OKX `GET /api/v5/public/instruments`:

- `instId`;
- `instType`;
- `ctType`;
- `settleCcy`;
- `tickSz`;
- `lotSz`;
- `minSz`;
- `ctVal`;
- `listTime`;
- `state`.

All values are recorded as **CURRENT_REFERENCE_ONLY**.

## 5. Historical evidence pack

A repository JSON pack may contain only explicitly dated official OKX evidence already reviewed before inventory execution. Evidence types may include:

- original listing specification;
- tick-size adjustment announcement;
- minimum-order/step-size adjustment announcement;
- contract-value adjustment announcement;
- historical fee-rule document.

Absence of a known adjustment is **not** proof that no adjustment occurred.

## 6. Field-state taxonomy

Each historical field for each instrument is classified only as:

- `RESOLVED_OFFICIAL_INTERVAL` — official dated evidence brackets the July/August interval sufficiently;
- `PARTIALLY_BRACKETED` — some official evidence exists but exact interval is not yet fully proven;
- `EMPIRICAL_CORROBORATION_NEEDED` — historical venue data can corroborate a grid/value but cannot alone prove all semantics;
- `UNRESOLVED` — insufficient evidence.

Current API values alone can never produce `RESOLVED_OFFICIAL_INTERVAL`.

## 7. Fee state

The inventory may record the regular-user reference `maker 2 bps / taker 5 bps` as a historically supported research reference, but promotional execution must later freeze the exact account-tier assumption and evidence classification.

## 8. Terminal token

Exact inventory success token:

`SC001_HISTORICAL_EXECUTION_SPEC_INVENTORY_PASS`

PASS means:

- all 12 current rows were retrieved and structurally valid;
- evidence pack parsed and matched only frozen-universe instruments;
- unresolved historical fields were reported explicitly;
- no July/August body was opened;
- no strategy signal/PnL was calculated.

PASS does **not** authorize real historical execution/PnL.

## 9. After PASS

Use the gap report to build a separate historical-spec reconstruction stage. That stage may use additional official announcements plus a small, explicitly engineering-only empirical lattice check if needed. Real promotional execution remains blocked until every required field is resolved under the evidence standard.
