# SC001 — B13-C S0 Networked Price-Anchor Extraction Launch Runbook v0.1

Date: 2026-09-27
Status: **USER APPROVED REAL PRICE-BODY ACCESS / READY FOR VPS LAUNCH**

Approved stage:
`SC001-B13C-S0 / PRICE-ANCHOR EXTRACTION`

The user explicitly approved proceeding to real price-body extraction after the offline extractor self-test PASS.

## Exact implementation

Repository HEAD at preparation:

`74d96052458f6fe9cdd68505852789b1bc4811ef`

Extractor:

`research/sc001/sc001_b13c_s0_streaming_price_anchor_extractor_v0_1_2.py`

SHA256:

`abb876276976198be65d049c6269d732dd24c5364c6c496bfeb5ed9d3f1f5be9`

Protocol:

`docs/research/sc001-b13c-s0-streaming-price-anchor-extraction-protocol-v0.1.md`

Cluster master SHA:

`0636ac25d6b7a484a4a9959f256aa57e0a1ead7f4e228423715f688b194fb87b`

Exact archives:

76

Frozen HEAD total:

2,633,144,445 bytes

## Execution mode

Use a transient systemd oneshot unit so the extraction survives SSH/Termux disconnect.

Unit:

`sc001-b13c-s0-price-anchor-extract-v01.service`

The extractor:
- processes one archive at a time;
- verifies frozen Content-Length;
- calculates compressed SHA256;
- validates gzip/CSV/timestamps;
- extracts only frozen entry/exit buckets;
- removes the compressed archive after successful extraction;
- persists per-archive ledgers and supports safe resume;
- does not calculate returns or PnL.

## Output root

`/home/botmarket/sc001_data/SC001_B13C_S0_PRICE_ANCHORS_V01`

Expected terminal PASS:

`B13C_S0_PRICE_ANCHOR_EXTRACTION_PASS`

## Outcome firewall

This launch authorizes price-body reading and frozen price-anchor extraction only.

Still forbidden:
- signed reversal calculation;
- 30 bps / 55% / 4-of-6 decision;
- per-symbol performance ranking;
- PnL.

A separate offline outcome bundle is required after anchor extraction PASS.
