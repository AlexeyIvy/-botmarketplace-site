# SC001-E009 — Trade Staged Acquisition Protocol v0.1

Date: 2026-09-17  
Status: **FROZEN AFTER METADATA PREFLIGHT PASS / BEFORE E009 TRADE BODY ACQUISITION**

## 1. Parent gate

Required exact parent state:

`E009_TRADE_METADATA_PREFLIGHT_PASS`

Observed parent summary:

- expected files = `128`;
- resolved files = `128`;
- expected total bytes = `419552195`;
- trade body downloaded = false;
- asset holdout accessed = false;
- October Confirmation accessed = false;
- August repurposed = false;
- strategy signal/PnL calculated = false.

## 2. Scope

Acquire only the frozen E009 Discovery trade archives for:

- BTC, ETH, DOGE, ORDI, UNI, XRP, OP, BCH;
- archive labels 2024-08-31 through 2024-09-15 inclusive;
- E009 Discovery performance remains 2024-09-01..14 UTC.

No SOL/FIL/LTC/SUI body access. No October body access. August remains unrepurposed except archive label 2024-08-31 as the objectively required D-1 stitch source for September 1 UTC reconstruction.

## 3. Frozen batches

- A: BTC + ETH
- B: DOGE + ORDI
- C: UNI + XRP
- D: OP + BCH

Each batch must contain exactly 32 frozen metadata rows.

## 4. Per-file integrity

For each archive require:

- URL identity inherited from frozen metadata preflight;
- HTTPS host `static.okx.com`;
- exact filename;
- local compressed byte count equals frozen HEAD size;
- SHA256 recorded after acquisition;
- ZIP CRC PASS;
- exactly one non-directory member;
- exact CSV header `instrument_name,trade_id,side,price,size,created_time`;
- first data row instrument equals expected instrument.

Existing local files may be reused only if exact compressed size and archive integrity pass; SHA256 is recomputed.

## 5. Disk guard

Before each batch require at least 5 GB free reserve after expected batch bytes.

## 6. Batch PASS tokens

- `E009_TRADE_ACQUISITION_BATCH_A_PASS`
- `E009_TRADE_ACQUISITION_BATCH_B_PASS`
- `E009_TRADE_ACQUISITION_BATCH_C_PASS`
- `E009_TRADE_ACQUISITION_BATCH_D_PASS`

Each requires exactly 32 verified files and no signal/PnL.

## 7. Final verify

After all four batch PASS reports, verify all 128 local archives again against:

- parent filename identity;
- frozen compressed size;
- recorded SHA256;
- ZIP CRC/member/header/instrument integrity.

Exact final PASS:

`E009_TRADE_ACQUISITION_VERIFY_PASS`

Required:

- verified_files = `128`;
- verified_total_bytes = `419552195`;
- asset holdout accessed = false;
- October Confirmation accessed = false;
- August repurposed = false;
- strategy signal/PnL calculated = false.

## 8. Stop rules

Do not:

- access holdout assets;
- access October;
- access September 16+;
- calculate E009 signal or returns during acquisition;
- access L2;
- infer execution specs from trade bodies;
- proceed to alpha before a separate semantic qualification PASS.
