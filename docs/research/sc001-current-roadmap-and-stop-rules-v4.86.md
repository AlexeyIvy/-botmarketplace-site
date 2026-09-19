# SC001 Current Roadmap and Stop Rules v4.86

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B13-A V0.2 FREEZE-HANDSHAKE FAIL / V0.3 RUN READY**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.85.md`

## 1. Prior terminal history unchanged

C11 remains terminal:

`C11_TERMINAL_REJECT_DIRECTION_CAPTURE`

C12 remains terminal:

`C12_S0_REJECT_PARITY_REVERSION`

C1-C10 remain closed.

## 2. B13-A v0.2 did not produce a research verdict

Observed:

`B13A_STRUCTURAL_PREFLIGHT_IMPLEMENTATION_FAIL`

Reason:

`freeze status mismatch`

The run stopped before BTC source/funding processing.

No funding differential or structural gate was computed.

## 3. Root cause

v0.2 runner expected the stale v0.1 freeze-status literal.

Classification:

`ENGINEERING_FREEZE_STATUS_LITERAL_MISMATCH`

Binding review:

`docs/research/sc001-b13a-v0.2-freeze-handshake-fail-review-v0.1.md`

## 4. v0.3 implementation

Runner:

`research/sc001/sc001_b13a_funding_differential_structural_preflight_v0_3.py`

Freeze:

`docs/research/sc001-b13a-funding-differential-implementation-freeze-v0.3.json`

Protocol remains:

`docs/research/sc001-b13a-funding-differential-structural-preflight-v0.2.md`

Only implementation handshake/version identity changed.

## 5. Economics unchanged

Still frozen:

- H1-2025;
- 12 symbols;
- OKX + Bybit;
- <=5 minute one-to-one settlement matching;
- 40 bps structural burden;
- >=50 bps qualifying differential;
- same sample/breadth/concentration gates.

## 6. Hard firewalls unchanged

No prices.

No basis.

No trade/L2 bodies.

No execution fills.

No strategy price PnL.

No C13 assignment.

## 7. Immediate next action

Syntax-check and run B13-A v0.3 across all 12 symbols.

Do not interpret partial per-symbol output.
