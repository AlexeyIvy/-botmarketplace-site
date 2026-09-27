# SC001 Current Roadmap and Stop Rules v5.140

Date: 2026-09-27
Status: **B15-P1 W1 accumulation / B14-A DEFER_DATA / B13-C price-anchor extraction PASS / dataset-freeze bundle SEALED**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.139.md`

## Networked extraction result

Observed terminal state:

`B13C_S0_PRICE_ANCHOR_EXTRACTION_PASS`

Counts:
- clusters = 1,905;
- archives = 76;
- valid price clusters = 1,793;
- missing entry only = 25;
- missing exit only = 75;
- missing both = 12;
- returns/PnL = CLOSED.

Valid price coverage:

`1793 / 1905 ~= 94.12%`

This is still source/data readiness, not the S0 strategy outcome.

## Exact dataset-freeze bundle

Bundle ID:

`bundle_20260927T083221Z_90a5a578`

SHA256:

`8b498bd030176e9ae2e21c12033b0e42d8db9119c7f3e7cca23747a3fba6f8ba`

Approval code:

`BM-8B498BD03017`

Runtime:

`offline-research-v1`

Package files:
15

Package bytes:
1,008,048

Runtime read-only inputs:
1. `SC001_B13C_S0_PRICE_ANCHORS_V01/price_anchor_extraction_manifest.json`
2. `SC001_B13C_S0_PRICE_ANCHORS_V01/price_anchors.jsonl`

Expected PASS:

`B13C_S0_PRICE_ANCHOR_DATASET_FREEZE_PASS`

The verifier binds the extracted dataset to the canonical 1,905-cluster master and verifies exact bucket membership and SHA integrity.

## Hard boundary

No signed reversal / S0 decision may be calculated before dataset-freeze PASS.

## Next state

`RUN_B13C_S0_PRICE_ANCHOR_DATASET_FREEZE_AFTER_EXPLICIT_APPROVAL`
