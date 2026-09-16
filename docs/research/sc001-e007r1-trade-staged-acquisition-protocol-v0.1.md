# SC001-E007R1 — Staged Trade Acquisition Protocol v0.1

Date: 2026-09-16
Status: **FROZEN AFTER METADATA PREFLIGHT PASS / BEFORE TRADE BODY ACCESS**

## 1. Parent gate

Required exact parent:

`E007R1_TRADE_METADATA_PREFLIGHT_PASS`

Expected parent identity:
- Discovery assets only: BTC, ETH, DOGE, ORDI, UNI, XRP, OP, BCH;
- archive dates: 2024-06-30 through 2024-07-15 inclusive;
- exact files: 128;
- expected total compressed bytes: 468,108,915;
- asset holdout remains closed;
- August Confirmation remains closed.

## 2. Purpose

Acquire only the frozen E007R1 Discovery trade archives needed for a gross-feasibility screen. This stage performs no strategy signal, alpha, PnL, L2 execution or historical-spec inference.

## 3. Frozen batches

- Batch A: BTC, ETH — 32 files.
- Batch B: DOGE, ORDI — 32 files.
- Batch C: UNI, XRP — 32 files.
- Batch D: OP, BCH — 32 files.

No batch may contain SOL, FIL, LTC or SUI. No August archive is allowed.

## 4. Per-file validation

For every file:
- URL and filename must match the exact parent metadata row;
- final URL host must remain `static.okx.com`;
- downloaded byte count must equal frozen HEAD size;
- SHA256 is recorded;
- ZIP CRC must pass;
- archive must contain exactly one non-directory member;
- CSV header must equal `instrument_name,trade_id,side,price,size,created_time`;
- first data row, when present, must identify the expected instrument.

A failed check deletes the temporary body and fails the batch closed.

## 5. Storage / resumability

Bodies are stored under:
`~/sc001_data/SC001_E007R1_TRADE_ACQUISITION/archives/<SYMBOL>/`

Already completed files may be reused only when their local size, SHA256 and archive/header checks match the recorded batch report. Otherwise they are redownloaded/fail-closed.

Preserve at least 5 GB free-disk reserve after the expected acquisition.

## 6. Batch terminal tokens

- `E007R1_TRADE_ACQUISITION_BATCH_A_PASS`
- `E007R1_TRADE_ACQUISITION_BATCH_B_PASS`
- `E007R1_TRADE_ACQUISITION_BATCH_C_PASS`
- `E007R1_TRADE_ACQUISITION_BATCH_D_PASS`

Each batch requires 32/32 validated bodies.

## 7. Full verification gate

After all four exact batch PASS reports, run local verification across all bodies.

Required terminal:

`E007R1_TRADE_ACQUISITION_VERIFY_PASS`

Required:
- verified_files = 128;
- exact aggregate local bytes = frozen expected total;
- every SHA256 matches its frozen batch acquisition report;
- ZIP/header integrity passes again;
- no holdout or August body access;
- strategy signal/PnL calculated = false.

## 8. Firewalls

This protocol does not authorize:
- E007R1 strategy signal/gross calculation;
- asset-holdout data access;
- August Confirmation data access;
- L2 acquisition;
- exact historical execution/PnL;
- reopening E007.

Only after full local verification PASS may a separate semantic/trade qualification and gross-feasibility stage be considered.