# SC001 — B13-A Funding-Differential Structural Preflight v0.2

Date: 2026-09-19
Status: **ENGINEERING-ONLY OKX METADATA PARSER AMENDMENT / ECONOMICS UNCHANGED**
Scope: `SCALPING RESEARCH / SC001`
Supersedes source-parser implementation semantics only from:
`docs/research/sc001-b13a-funding-differential-structural-preflight-v0.1.md`

Parent review:
`docs/research/sc001-b13a-v0.1-implementation-fail-review-v0.1.md`

## 1. Frozen economics unchanged

All v0.1 research rules remain binding:

- venues: OKX + Bybit;
- frozen 12-symbol universe;
- H1-2025 nonpromotional window;
- same-symbol funding settlements only;
- <=5 minute one-to-one matching;
- 4 structural fills;
- 40 bps burden;
- qualifying differential >=50 bps;
- data-quality and structural breadth gates unchanged.

## 2. OKX source parser amendment

Endpoint remains:

`GET /api/v5/public/market-data-history`

with:

- module=3;
- instType=SWAP;
- exact instrument family;
- monthly aggregation.

Instead of requiring a fixed `data.details` wrapper, recursively walk the returned `data` object.

A node is an admissible funding archive file node only if it has:

- `filename` or `fileName`;
- `url` or `fileUrl` or `downloadUrl`.

For every admitted node require:

- HTTPS;
- exact host `static.okx.com`;
- URL basename exactly equals filename;
- no conflicting URLs for the same filename.

This is the already-qualified C9-D0 v0.2 source parsing pattern.

## 3. No permissive fallback

Do not accept:

- arbitrary URLs without filename identity;
- non-static.okx.com archive hosts;
- inferred filenames;
- alternate module/date aggregation;
- another venue.

If no trusted file node is found:

`B13A_STRUCTURAL_PREFLIGHT_IMPLEMENTATION_FAIL`

not a structural research verdict.

## 4. Firewalls unchanged

Still forbidden:

- market prices;
- basis;
- trade/L2 bodies;
- execution fills;
- strategy price PnL;
- promotional evidence;
- C13 assignment.

## 5. Rerun rule

Run all 12 symbols from the beginning under v0.2.

The final structural report must come from v0.2 alone.
