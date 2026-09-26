# SC001 Current Roadmap and Stop Rules v5.120

Date: 2026-09-26  
Status: **B15-P1 W1 accumulation continues / B14-A P0 state-only diagnostic SEALED**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.119.md`

The original approved B14-A three-input real-data bundle did not reach its Python entrypoint because Runner rejected the declared input materialization.

No B14-A prospective price outcome was opened.

## Exact diagnostic bundle

- ID: `bundle_20260926T202330Z_d853d3a6`
- SHA256: `25a1327b0438b4964501d051188ac5ace0806323abb6b17e31f4c5f7104f5c52`
- approval code: `BM-25A1327B0438`
- runtime: `offline-research-v1`
- package files: 3
- bytes: 6537
- runtime inputs: one file only

Input:
`SC001_B14A_P0_20260925/collector_state.json`

Expected PASS:
`B14A_P0_STATE_ONLY_DIAGNOSTIC_PASS`

The diagnostic reports only collector operational state/counters and reads no raw trades or prices.

## Purpose

Distinguish:
1. missing/nonexistent collector state, from
2. successful collector state with a later raw-trade/connection-file materialization problem.

No threshold, event rule or B14-A hypothesis changes.

## Next state

`RUN_B14A_P0_STATE_ONLY_DIAGNOSTIC_AFTER_EXPLICIT_APPROVAL`
