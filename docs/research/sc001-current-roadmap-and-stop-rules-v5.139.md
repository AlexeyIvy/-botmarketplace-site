# SC001 Current Roadmap and Stop Rules v5.139

Date: 2026-09-27
Status: **B15-P1 W1 accumulation / B14-A DEFER_DATA / B13-C S0 price-anchor extraction PASS / offline dataset freeze next**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.138.md`

## B13-C networked price-anchor extraction

Operator-run VPS stage completed:

`B13C_S0_PRICE_ANCHOR_EXTRACTION_PASS`

Observed:
- clusters = 1,905;
- archives = 76;
- valid price clusters = 1,793;
- missing entry only = 25;
- missing exit only = 75;
- missing both = 12;
- valid-price coverage = 1,793 / 1,905 ~= 94.12%;
- returns/PnL = CLOSED.

Partition integrity:
`1793 + 25 + 75 + 12 = 1905`.

This is source/extraction evidence only. It is not the S0 strategy outcome.

## Offline price-anchor dataset freeze

Prepared verifier:

`research/sc001/sc001_b13c_s0_price_anchor_dataset_freeze_v0_1.py`

SHA256:

`b45388ad453623a3a8bdd0a2893f31552b89b1bea090b0bbda475099e61a2d40`

Runtime inputs:
- `SC001_B13C_S0_PRICE_ANCHORS_V01/price_anchor_extraction_manifest.json`;
- `SC001_B13C_S0_PRICE_ANCHORS_V01/price_anchors.jsonl`.

The verifier will independently bind:
- extraction manifest status/firewalls;
- actual anchor-file SHA;
- canonical 1,905-cluster master/chunks;
- exact cluster metadata;
- frozen bucket membership;
- exact valid/missing partition;
- 76 archive SHA map.

No return is calculated.

## Stop rule

Do not calculate the signed 30-second S0 reversal metric until:

`B13C_S0_PRICE_ANCHOR_DATASET_FREEZE_PASS`

has been obtained and persisted.

## Next state

`BUILD_AND_SEAL_B13C_S0_PRICE_ANCHOR_DATASET_FREEZE_BUNDLE`
