# SC001 — Forced-Flow Historical Trade Archive Metadata Preflight v0.1

Date: 2026-09-30
Status: FROZEN SOURCE-TRANSPORT PREFLIGHT / NO ARCHIVE BODY / NO OUTCOME
Task ID: SC001-NEXT-PRIMARY-PREFREEZE-01

## Purpose

Verify that the frozen 12-symbol Bybit/OKX perpetual universe can be materialized from official historical daily trade archives after the S0 fresh window closes.

This is source/transport engineering only. It must not open archive bodies, trade rows, prices, basis, returns, clusters or PnL.

Qualification date:

2026-09-29 UTC

This completed date is outside the frozen S0 outcome window and is used only to verify exact archive transport/identity patterns.

## Frozen universe

BTC, ETH, SOL, DOGE, ORDI, FIL, UNI, XRP, LTC, OP, BCH, SUI.

Bybit expected path pattern:

https://public.bybit.com/trading/{SYMBOL}USDT/{SYMBOL}USDT2026-09-29.csv.gz

OKX expected filename pattern:

{SYMBOL}-USDT-SWAP-trades-2026-09-29.zip

resolved only through the official OKX historical-data metadata resolver.

## Allowed network access

Bybit:
- HEAD exact expected archive URL only.

OKX:
- POST official historical-data metadata resolver only;
- parse exact trusted static.okx.com URL for the expected filename;
- HEAD exact resolved archive URL only.

## Forbidden

- no GET of archive bodies;
- no decompression;
- no trade-row parsing;
- no price values;
- no cross-venue ratio;
- no event/cluster mapping;
- no returns/PnL;
- no symbol substitution;
- no fallback third-party source.

## PASS

PASS only if all 12 Bybit archive identities and all 12 OKX archive identities resolve with:
- HTTPS;
- exact trusted host;
- exact expected basename;
- HTTP 200 HEAD;
- positive Content-Length.

Exact PASS token:

FORCED_FLOW_ARCHIVE_METADATA_PREFLIGHT_PASS

Otherwise:

FORCED_FLOW_ARCHIVE_METADATA_PREFLIGHT_REVIEW

A PASS establishes only source-transport feasibility for later post-window materialization. It does not authorize body download or S0.
