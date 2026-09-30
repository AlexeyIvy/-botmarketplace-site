# SC001 — OKX Historical Trade Archive Publication / Resolver Diagnostic v0.1

Date: 2026-09-30
Status: FROZEN SOURCE-TRANSPORT DIAGNOSTIC / NO BODY / NO OUTCOME
Task ID: SC001-NEXT-PRIMARY-PREFREEZE-01

## Trigger

The single authorized forced-flow archive metadata preflight on qualification date 2026-09-29 returned:

FORCED_FLOW_ARCHIVE_METADATA_PREFLIGHT_REVIEW

Observed:
- Bybit exact daily archive identities: 12/12 PASS;
- OKX exact daily SWAP archive URLs: 0/12 resolved through the frozen official historical-data metadata resolver;
- no archive body, trade row, price, basis, return, PnL or S0 outcome was opened.

## Purpose

Distinguish the two cheapest source-transport explanations without opening any market-data body:

1. RECENT_PUBLICATION_LAG — the resolver works for older completed days but not for the immediately preceding day;
2. RESOLVER_CONTRACT_REVIEW — the resolver fails to expose the exact trusted archive even for clearly older completed days.

This diagnostic is source engineering only and has no strategy/outcome role.

## Frozen scope

Instrument:
BTC-USDT-SWAP only.

Why BTC only:
The prior live preflight failed identically across all 12 OKX bases on the same date. One high-liquidity frozen instrument is sufficient to diagnose date-level publication/resolver behavior without multiplying network work.

Dates:
- 2026-09-29 (D-1 relative to the original preflight date);
- 2026-09-28 (D-2);
- 2026-09-23 (D-7).

No extra dates.

Expected exact filenames:
- BTC-USDT-SWAP-trades-2026-09-29.zip
- BTC-USDT-SWAP-trades-2026-09-28.zip
- BTC-USDT-SWAP-trades-2026-09-23.zip

Resolver domains:
- https://www.okx.com
- https://us.okx.com

Resolver contract:
POST /priapi/v5/broker/public/trade-data/download-link

Frozen request family:
- module = "1";
- instType = "SWAP";
- instFamilyList = ["BTC-USDT"];
- dateAggrType = "daily";
- exact UTC date bounds.

Allowed inspection:
- resolver HTTP success/code;
- bounded safe top-level/data schema census;
- exact filename/url keys;
- exact trusted static.okx.com URL count;
- HEAD only if exact trusted URL resolves;
- Content-Length.

Forbidden:
- GET archive body;
- decompression;
- trade rows;
- price values;
- alternate instrument;
- alternate venue;
- third-party source;
- date expansion beyond the three frozen dates;
- returns/PnL/S0.

## Terminal states

If D-2 or D-7 resolves exactly while D-1 does not:

OKX_ARCHIVE_DIAGNOSTIC_RECENT_PUBLICATION_LAG

If none of the three exact dates resolves but the resolver returns structurally valid success payloads:

OKX_ARCHIVE_DIAGNOSTIC_RESOLVER_CONTRACT_REVIEW

If all three exact dates resolve:

OKX_ARCHIVE_DIAGNOSTIC_PASS

If transport/schema is ambiguous:

OKX_ARCHIVE_DIAGNOSTIC_SOURCE_REVIEW

## Consequence

No terminal state authorizes archive-body download.

Any transport repair must be frozen prospectively and requires separate user approval before another live run.
