# SC001 Current Roadmap and Stop Rules v4.85

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B13-A V0.1 SOURCE-PARSER FAIL / V0.2 IMPLEMENTATION FROZEN**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.84.md`

## 1. Terminal history unchanged

C11 remains terminal:

`C11_TERMINAL_REJECT_DIRECTION_CAPTURE`

C12 remains terminal:

`C12_S0_REJECT_PARITY_REVERSION`

C1-C10 remain closed.

## 2. B13-A v0.1 result

The first B13-A run stopped before any research verdict:

`B13A_STRUCTURAL_PREFLIGHT_IMPLEMENTATION_FAIL`

at BTC with:

`OKX funding metadata details missing for BTC`

No funding differential or structural gate was computed.

## 3. Root cause

v0.1 assumed a fixed OKX response wrapper:

`data.details -> groupDetails`

The already-qualified C9-D0 v0.2 implementation uses a recursive exact-file-node walk under `data`.

Classification:

`ENGINEERING_OKX_METADATA_RESPONSE_SHAPE_PARSER_DEFECT`

## 4. v0.2 implementation

Protocol:

`docs/research/sc001-b13a-funding-differential-structural-preflight-v0.2.md`

Runner:

`research/sc001/sc001_b13a_funding_differential_structural_preflight_v0_2.py`

Freeze:

`docs/research/sc001-b13a-funding-differential-implementation-freeze-v0.2.json`

The parser now recursively admits only exact file nodes with trusted archive identity.

## 5. Economics unchanged

No change to:

- 12-symbol universe;
- H1-2025 window;
- OKX/Bybit venues;
- <=5 minute settlement matching;
- 40 bps structural burden;
- >=50 bps qualifying funding differential;
- sample/breadth/concentration gates.

## 6. Firewalls unchanged

No market prices.

No basis.

No trade/L2 bodies.

No execution fills.

No strategy price PnL.

No C13 assignment.

## 7. Immediate next action

Syntax-check and rerun B13-A v0.2 across all 12 symbols.

Do not interpret partial per-symbol output.
