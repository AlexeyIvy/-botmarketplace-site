# SC001 — C1 Selection SPOT Metadata Preflight Results v0.1

Date: 2026-09-17  
Status: **PASS — FROZEN MANIFEST READY FOR DATA-ONLY BODY ACQUISITION**

## 1. Exact result

The frozen metadata-only runner returned:

`C1_SPOT_METADATA_PREFLIGHT_PASS`

Exit code:

`C1_SPOT_METADATA_EXIT_CODE=0`

## 2. Coverage

All eight frozen SPOT candidates returned `COMPLETE_METADATA` with all 32 permitted archive labels:

- BTC-USDT;
- ETH-USDT;
- DOGE-USDT;
- ORDI-USDT;
- UNI-USDT;
- XRP-USDT;
- OP-USDT;
- BCH-USDT.

Result:

- `complete_asset_count = 8`;
- each asset = `32/32` archives;
- `expected_complete_asset_body_bytes = 273358764`;
- `disk_pass = True`;
- `metadata_query_days_all_whitelisted = True`.

## 3. Frozen local manifest identity

Authoritative local manifest:

`~/sc001_data/SC001_C1_SPOT_SELECTION_CALIBRATION/sc001_c1_spot_metadata_preflight_v0_1.json`

Observed identity:

- SHA256: `bfa403c5b53b2a95c0df28fd41d3382667fe0c6ced223b65f451e7b99ecd1023`;
- bytes: `118273`.

The next downloader/integrity stage is bound to this exact identity and may not rediscover or substitute archive identities.

## 4. Firewalls observed

The metadata run reported:

- `market_data_body_downloaded = False`;
- strategy signal = false;
- sentinel outcome = false;
- basis = false;
- returns = false;
- PnL = false;
- promotional alpha accessed = false.

No protected-data or promotional evidence was authorized by this PASS.

## 5. Consequence

The metadata gate is cleared for the exact contaminated-date SPOT manifest only.

Next allowed stage is the separately frozen body acquisition / integrity / UTC qualification protocol. The frozen C1-C6 first-pass sentinel budget remains exactly 11 variants, with C1 exactly one variant.