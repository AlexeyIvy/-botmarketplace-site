# SC001 — C1-C6 Selection Preflight v0.2 Results v0.1

Date: 2026-09-17  
Status: **PASS — NO-ALPHA PREFLIGHT GATE CLEARED**  
Scope: `SCALPING RESEARCH / SC001`

## 1. Exact terminal result

The corrected no-alpha preflight was rerun on the qualified VPS and returned the exact required token:

`SC001_C1C6_SELECTION_PREFLIGHT_PASS`

Exit code:

`PREFLIGHT_EXIT_CODE=0`

This clears only the mechanical preflight gate. It is not strategy evidence and does not authorize promotional alpha, holdout access, Confirmation access, or live trading.

## 2. Frozen identities observed

Runner Git blob SHA:

`750bcf75ae500a9b4da7643a4e6889658ad6326c`

Protocol Git blob SHA:

`4b0102d82d37e138299b140a55cc2c13624499ec`

Syntax check returned:

`PY_COMPILE_PASS`

## 3. Sandbox integrity results

July E007R1 archive identities reverified:

`128/128`

September E009 archive identities reverified:

`128/128`

Legacy E006 optional state:

`READY_OPTIONAL`

C1 July/September multi-asset SPOT inventory result:

`data_gap_expected = True`

Therefore C1 requires a separately frozen contaminated-date-only SPOT metadata/acquisition stage before C1 sentinel computation.

## 4. Protected-data firewall results

Hard protected market-body hits:

`0`

Legacy E003 March 22-30 BTC perpetual source-presence count:

`9`

Those files were classified as pre-existing E003 source presence only. The corrected preflight reported:

`legacy E003 March 22-30 bodies opened/hashed by this preflight = False`

No E006 Confirmation access event was created.

## 5. Explicit no-alpha results

The preflight reported all of the following false:

- `strategy_signal_calculated`;
- `sentinel_outcome_calculated`;
- `pnl_calculated`;
- `promotional_alpha_accessed`.

## 6. Consequence

The v0.1 false-positive is resolved as an implementation defect, not a research FAIL and not a contamination event.

The next allowed sequence remains:

1. close the C1 contaminated-date SPOT data gap under a separately frozen data-only protocol;
2. implement shared causal trade/bar utilities plus synthetic/golden tests;
3. implement and freeze C1-C6 sentinel runners;
4. preserve the exact frozen first-pass budget of **11 strategy variants**;
5. run only nonpromotional sentinels on the contaminated sandbox.

Protected holdouts and Confirmation periods remain closed.
