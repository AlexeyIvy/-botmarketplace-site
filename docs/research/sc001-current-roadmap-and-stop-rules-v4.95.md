# SC001 Current Roadmap and Stop Rules v4.95

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B13-C HISTORICAL DATA DEFER / PROSPECTIVE LIQUIDATION COLLECTION NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.94.md`

## 1. Binding prior states

C11:
`C11_TERMINAL_REJECT_DIRECTION_CAPTURE`

C12:
`C12_S0_REJECT_PARITY_REVERSION`

B13-A:
`B13A_REJECT_STRUCTURAL`

B13-B historical:
`B13B_S0_DEFER_SAMPLE`

B13-B future:
prospective admission only.

No active C13+ strategy ID.

## 2. B13-C source/data audit

Binding:

`docs/research/sc001-b13c-liquidation-source-data-feasibility-audit-v0.1.md`

Historical state:

`B13C_DEFER_HISTORICAL_DATA_FEASIBILITY`

Reason:

`NO_FREE_QUALIFIED_LONG_EVENT_LEVEL_EXPLICIT_LIQUIDATION_HISTORY`

## 3. Venue conclusions

OKX:

- live liquidation channel exists;
- historical public liquidation REST was discontinued;
- no long liquidation archive in official historical download categories.

Bybit:

- public `allLiquidation.{symbol}` stream exposes explicit live events;
- suitable for prospective collection;
- no qualified long official liquidation archive identified.

Binance:

- old public all-market liquidation REST discontinued;
- current force-order history is not a complete long public market-history source.

## 4. B13-C is not rejected economically

The branch is deferred for historical data, not mechanism economics.

No alpha/headroom conclusion exists.

## 5. Prospective collection path

Freeze and begin:

`BYBIT_ALL_LIQUIDATION_PROSPECTIVE_RAW_COLLECTION`

using the pre-existing 12-symbol universe, subject only to source-availability qualification.

Raw stream role:

`PROTECTED_PROSPECTIVE_RAW_LIQUIDATION_STREAM`

## 6. Protected-collection rules

During protected collection do not calculate:

- returns;
- continuation/reversal;
- threshold grids;
- per-symbol alpha ranking;
- execution;
- PnL.

Allowed:

- uptime/gap diagnostics;
- schema/source validation;
- raw event counts for sufficiency planning.

## 7. New kernel gate applies

Any later B13-C outcome-bearing experiment must first pass:

`docs/research/sc001-preoutcome-semantic-implementation-gate-v0.1.md`

## 8. Parallel research

After prospective collector starts, SC001 may explore another independent-base design in parallel.

The protected B13-C stream must not be inspected for strategy design.

## 9. Immediate next action

Create and freeze the Bybit prospective liquidation collector protocol + implementation.

No liquidation alpha test yet.
