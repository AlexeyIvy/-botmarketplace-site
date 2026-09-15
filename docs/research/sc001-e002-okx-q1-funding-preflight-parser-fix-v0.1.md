# SC001-E002 OKX Q1 Funding Preflight Parser Fix v0.1

Date: 2026-09-15  
Status: **INFRASTRUCTURE/PARSER-ONLY FIX BEFORE ANY EXECUTION-ECONOMICS OUTPUT**

## Context

The v0.2 funding/metadata preflight reached the official public OKX endpoint
`GET /api/v5/public/market-data-history` successfully (`code=0`) but failed closed because the implementation assumed the older private-download response shape `data.details[].groupDetails[]`.

No funding archive body was accepted, no alpha was calculated, no execution P&L was calculated, and Q2 / Validation / Final remained closed.

## Change

`research/sc001/sc001_e002_okx_q1_execution_metadata_preflight_v0_3.py`

is a thin wrapper around v0.2. It changes only response-shape parsing:

- keeps all v0.2 historical contract constants;
- keeps the Lv1 taker-fee freeze;
- keeps the same January/February 2024 funding-archive range;
- keeps module `3`, `SWAP`, `BTC-USDT`, monthly aggregation;
- keeps the same trusted-host and filename checks;
- keeps the same archive/CSV integrity gates;
- keeps the exact three-funding-events-per-frozen-day requirement;
- keeps Q2 / Validation / Final closed;
- keeps alpha and execution P&L disabled.

The parser now walks the public endpoint's returned `data` structure generically and accepts only nodes that contain a filename plus download URL, after which the existing trusted static-OKX identity checks remain mandatory.

## Research semantics

No financial rule, statistical rule, promotion gate, signal definition, threshold, latency, haircut, size, fee, funding treatment, or stop rule changes.

This fix therefore does not consume any execution-economics result and does not constitute retuning.
