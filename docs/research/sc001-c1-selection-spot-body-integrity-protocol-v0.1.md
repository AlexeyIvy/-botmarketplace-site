# SC001 — C1 Selection SPOT Body Acquisition / Integrity / UTC Qualification Protocol v0.1

Date: 2026-09-17  
Status: **FROZEN DATA-ONLY SELECTION/CALIBRATION PROTOCOL — NO SENTINEL OUTCOME AUTHORIZED**  
Scope: `SCALPING RESEARCH / SC001`

Parent:
`docs/research/sc001-c1-selection-spot-metadata-and-acquisition-protocol-v0.1.md`

## 1. Purpose

Acquire and qualify only the exact C1 multi-asset OKX SPOT trade archives already resolved by the successful contaminated-date metadata preflight.

This stage is data engineering only. It must not calculate basis signals, convergence outcomes, returns, PnL, sentinel dispositions, feature rankings, promotional alpha, holdout evidence, or Confirmation evidence.

## 2. Frozen parent manifest identity

Authoritative manifest:

`~/sc001_data/SC001_C1_SPOT_SELECTION_CALIBRATION/sc001_c1_spot_metadata_preflight_v0_1.json`

Required terminal parent state:

`C1_SPOT_METADATA_PREFLIGHT_PASS`

Required exact local parent identity:

- SHA256: `bfa403c5b53b2a95c0df28fd41d3382667fe0c6ced223b65f451e7b99ecd1023`;
- bytes: `118273`;
- complete assets: `8/8`;
- expected complete-asset body bytes: `273358764`.

Any mismatch is fail-closed. No metadata rediscovery or substitution is permitted.

## 3. Frozen universe and labels

SPOT instruments exactly:

- BTC-USDT;
- ETH-USDT;
- DOGE-USDT;
- ORDI-USDT;
- UNI-USDT;
- XRP-USDT;
- OP-USDT;
- BCH-USDT.

Permitted archive-label windows exactly:

- `2024-06-30..2024-07-15` inclusive;
- `2024-08-31..2024-09-15` inclusive.

Therefore exactly `8 × 32 = 256` archive identities are admissible.

Performance-role dates remain only:

- `2024-07-01..2024-07-14`;
- `2024-09-01..2024-09-14`.

Boundary labels are source-support only:

- `2024-06-30`;
- `2024-07-15`;
- `2024-08-31`;
- `2024-09-15`.

No body from July 16-30, August 1-30, October, protected asset holdouts, or legacy E006 March Confirmation may be accessed.

## 4. Download identity and resume rules

Runner:

`research/sc001/sc001_c1_selection_spot_body_integrity_v0_1.py`

Workspace:

`~/sc001_data/SC001_C1_SPOT_SELECTION_CALIBRATION/`

Archive root:

`archives/<ASSET>/`

For every body require:

- exact filename from the frozen manifest;
- exact frozen URL from the manifest;
- HTTPS;
- final host exactly `static.okx.com`;
- exact frozen Content-Length;
- no network metadata rediscovery;
- no alternate date or instrument substitution.

Downloads may resume from `.part` only when HTTP Range semantics are unambiguous. If the server answers ambiguously, restart that file rather than append blindly.

## 5. Archive integrity

Every admitted archive must pass:

1. exact byte size;
2. SHA256 recorded after download/reuse;
3. ZIP CRC;
4. exactly one non-directory CSV member;
5. exact header `instrument_name,trade_id,side,price,size,created_time`;
6. every nonempty row has six fields;
7. instrument equals the expected SPOT instrument;
8. side is `buy` or `sell`;
9. price and size are finite and strictly positive;
10. timestamp scale resolves causally to milliseconds;
11. source timestamps never move backward;
12. source trade IDs are strictly increasing.

Trade-ID gaps and duplicate timestamps are recorded diagnostically. Duplicate/backward trade IDs are hard failures.

No row may be removed because of price movement, volatility, basis, apparent dislocation, return, or any strategy-related quantity.

## 6. UTC reconstruction qualification

For causal reconstruction, qualify target UTC days:

- `2024-06-30..2024-07-14`;
- `2024-08-31..2024-09-14`.

For each target day `D`, reconstruct only from archive label `D` plus archive label `D+1`, retaining rows in `[D 00:00 UTC, D+1 00:00 UTC)`.

This yields exactly `8 × 30 = 240` reconstructed UTC asset-days, of which:

- 224 are contaminated performance-role asset-days;
- 16 are boundary warm-up/source-support asset-days.

A reconstructed day qualifies only if:

- admitted row count > 0;
- timestamps never move backward;
- trade IDs never duplicate or move backward;
- both buy and sell sides are present;
- all admitted timestamps lie inside the target UTC interval.

Record diagnostically:

- minute-bucket coverage;
- missing-minute count;
- maximum inter-trade gap;
- trade-ID gap count;
- first/last admitted timestamp.

Minute coverage and forward trade-ID gaps are diagnostic, not alpha filters.

## 7. Preflight mode

Before any body GET, `preflight` must verify:

- exact manifest SHA256 and byte count;
- exact parent PASS state;
- exact 8 complete assets;
- exact 256 frozen archive rows;
- exact body byte total `273358764`;
- all URLs/filenames/labels remain inside the frozen scope;
- sufficient disk for frozen body total plus 20 GiB reserve;
- all no-alpha/protected-data firewalls in the manifest are false.

Exact preflight PASS token:

`C1_SPOT_BODY_PREFLIGHT_PASS`

No download is permitted if preflight does not PASS.

## 8. Run-mode terminal state

After all 256 archives and 240 reconstructed UTC asset-days qualify, write:

`~/sc001_data/SC001_C1_SPOT_SELECTION_CALIBRATION/sc001_c1_spot_body_integrity_report_v0_1.json`

Exact terminal PASS token:

`C1_SPOT_BODY_INTEGRITY_PASS`

The report must include:

- frozen manifest identity;
- per-archive filename/bytes/SHA256/source diagnostics;
- per-asset archive counts;
- reconstructed UTC-day diagnostics;
- exact downloaded/reused byte facts;
- explicit scope/protected-data flags;
- explicit no-alpha flags.

Any identity, archive, runtime, scope, or UTC-qualification failure returns REVIEW/FAIL and does not authorize sentinel work.

## 9. Explicit firewalls

The report must state:

- `strategy_signal_calculated=false`;
- `sentinel_outcome_calculated=false`;
- `basis_calculated=false`;
- `returns_calculated=false`;
- `pnl_calculated=false`;
- `promotional_alpha_accessed=false`;
- `protected_holdout_body_accessed=false`;
- `july_gap_body_accessed=false`;
- `august_protected_body_accessed=false`;
- `october_confirmation_body_accessed=false`;
- `legacy_e006_confirmation_body_accessed=false`.

## 10. Sentinel budget unchanged

This stage changes no candidate, threshold, feature, cost hurdle, MDE rule, chronology, universe, or selection logic.

The frozen first-pass C1-C6 sentinel budget remains exactly **11 variants**, with C1 still exactly **1 strict legacy-mechanism variant**.

## 11. Promotion rule

`C1_SPOT_BODY_INTEGRITY_PASS` establishes only contaminated-sandbox SPOT data readiness.

It does not establish profitability or executability and does not authorize protected holdout, Confirmation, promotional alpha, or live trading.

After exact body-integrity PASS, the next allowed work is shared causal trade/bar utility engineering plus synthetic/golden causality tests, followed by frozen C1-C6 sentinel implementation.