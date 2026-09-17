# SC001 — C1-C6 Selection/Calibration Implementation Preflight Protocol v0.2

Date: 2026-09-17  
Status: **FROZEN AFTER V0.1 FALSE-POSITIVE / BEFORE ANY C1-C6 SENTINEL OUTCOME**  
Scope: `SCALPING RESEARCH / SC001`

Supersedes the executable use of `sc001-c1-c6-selection-preflight-protocol-v0.1.md` while preserving v0.1 as audit history.

## 1. Reason for v0.2

The first v0.1 preflight correctly re-verified all July E007R1 and September E009 archive identities, but then emitted `SC001_C1C6_SELECTION_PREFLIGHT_FAIL` because it treated the **local presence** of legacy `2024-03-22..30` BTC perpetual archives inside `SC001_E003_OKX_MARCH_TRADES` as evidence that E006 Confirmation had been accessed.

That inference was invalid. Those swap archives pre-existed as part of the independent legacy E003 March source inventory. Their presence on disk does not mean that the E006 branch read or used the E006 Confirmation period.

No strategy signal, sentinel outcome or PnL was calculated by the failed v0.1 preflight. Therefore a purely mechanical preflight correction and rerun is permitted.

## 2. Unchanged purpose

This stage remains a **no-alpha local integrity/inventory preflight** before any C1-C6 sentinel computation.

It must establish that:

1. July E007R1 contaminated trade sandbox is locally intact and tied to qualified parents;
2. September E009 contaminated trade sandbox is locally intact and tied to qualified parents;
3. legacy E006 March BTC spot/perpetual calibration artifacts for March 1-21 are inventoried where present;
4. C1 July/September multi-asset SPOT gaps are inventoried without opening fresh dates;
5. protected periods are not used by the current selection stage;
6. runtime and implementation identities are valid;
7. no strategy signal, sentinel outcome, return or PnL is calculated.

## 3. Integrity policy

For July and September, reconcile exact acquisition/semantic PASS parents and re-verify every expected archive against recorded filename, byte count and SHA256.

Expected totals remain exactly 128 archives for July and 128 for September.

Archive CSV contents are not parsed for alpha or outcomes.

## 4. Corrected protected-body semantics

The filesystem scan is a **presence/reconciliation aid**, not proof of branch usage by itself.

### 4.1 Hard protected hits that remain FAIL

The current preflight must fail if it finds local market-body files indicating unresolved access to:

- SOL/FIL/LTC/SUI bodies on `2024-07-01..2024-07-14`;
- any body on `2024-07-16..2024-07-30`;
- any body on `2024-08-01..2024-08-30` except already-governed boundary `2024-08-31`;
- SOL/FIL/LTC/SUI bodies on `2024-09-01..2024-09-14`;
- any body on `2024-10-01..2024-10-14`;
- BTC spot bodies for legacy E006 Confirmation `2024-03-22..2024-03-30` inside `SC001_E006_SPOT_FEASIBILITY`.

Such hits require explicit reconciliation before sentinel work.

### 4.2 Legacy E003 swap presence is not an E006 access event

BTC perpetual archives dated `2024-03-22..2024-03-30` under:

`SC001_E003_OKX_MARCH_TRADES`

are permitted to exist locally because they belong to the pre-existing E003 March source set.

The v0.2 preflight must **not open or hash those March 22-30 bodies**. It may only observe their filenames while scanning. Their presence must be reported separately as:

`legacy_e003_march_confirmation_source_presence_only`

and must not set `legacy_e006_confirmation_accessed=true`.

For optional E006 calibration verification, only March 1-21 files may be opened/hashed.

## 5. C1 SPOT gap

C1 still requires same-venue spot/perpetual data. Absence of July/September multi-asset spot bodies is expected and is not a preflight failure.

Any future spot acquisition must be separately frozen and limited to already contaminated July/September sandbox dates.

## 6. Runtime and identity

Require Python 3, NumPy import, Git worktree, and exact runner/protocol identities from the v1.1 implementation freeze.

## 7. Required report

Write atomically:

`~/sc001_data/SC001_C1C6_SELECTION_PREFLIGHT/sc001_c1c6_selection_preflight_report_v0_2.json`

Report at least:

- exact status;
- runner/protocol Git blob identities;
- Python/NumPy versions;
- July and September parent/integrity totals;
- legacy E006 March 1-21 readiness;
- C1 multi-asset spot-gap state;
- hard protected-body hit count/paths;
- legacy E003 March 22-30 source-presence count/paths;
- all current-stage protected access flags false;
- `strategy_signal_calculated=false`;
- `sentinel_outcome_calculated=false`;
- `pnl_calculated=false`;
- `promotional_alpha_accessed=false`.

## 8. Exact token

PASS:

`SC001_C1C6_SELECTION_PREFLIGHT_PASS`

Any actual identity, integrity, runtime or hard-firewall failure must terminate without this token.

A PASS authorizes only sentinel engineering on the contaminated sandbox; it is not evidence of profitability.