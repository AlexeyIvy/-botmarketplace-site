# SC001 — C1 Selection SPOT Metadata & Acquisition Protocol v0.1

Date: 2026-09-17  
Status: **FROZEN DATA-ONLY SELECTION/CALIBRATION PROTOCOL — NO SENTINEL OUTCOME AUTHORIZED**  
Scope: `SCALPING RESEARCH / SC001`  
Parent: `docs/research/sc001-c1-c6-selection-calibration-sandbox-sentinel-mde-plan-v0.1.md`

## 1. Purpose

Close the known C1 multi-asset same-venue SPOT data gap using only already contaminated Selection/Calibration dates and their explicitly allowed boundary-neighbor dates.

This protocol is data engineering only. It must not calculate basis signals, convergence outcomes, returns, PnL, sentinel dispositions, feature rankings, or promotional alpha.

## 2. Candidate and universe

Candidate: C1 — E006R1 strict multi-asset same-venue spot/perpetual basis convergence.

Perpetual sandbox universe is already frozen to:

- BTC-USDT-SWAP;
- ETH-USDT-SWAP;
- DOGE-USDT-SWAP;
- ORDI-USDT-SWAP;
- UNI-USDT-SWAP;
- XRP-USDT-SWAP;
- OP-USDT-SWAP;
- BCH-USDT-SWAP.

Corresponding SPOT candidates are exactly:

- BTC-USDT;
- ETH-USDT;
- DOGE-USDT;
- ORDI-USDT;
- UNI-USDT;
- XRP-USDT;
- OP-USDT;
- BCH-USDT.

No historical winner selection is permitted.

## 3. Frozen date scope

Performance-role dates are only the already contaminated sandbox:

- 2024-07-01..2024-07-14 UTC;
- 2024-09-01..2024-09-14 UTC.

Boundary/source-support labels allowed only for causal reconstruction are:

- 2024-06-30;
- 2024-07-15;
- 2024-08-31;
- 2024-09-15.

Therefore the only permitted SPOT archive-label windows are:

- 2024-06-30..2024-07-15 inclusive;
- 2024-08-31..2024-09-15 inclusive.

The four boundary labels can never contribute performance observations.

No body from July 16-30, August 1-30, October, protected asset holdouts, or legacy E006 March Confirmation may be accessed by this stage.

## 4. Source

Venue: OKX.  
Instrument type: SPOT.  
Historical public trade-history module: `module=1`.  
Expected archive identity:

`ASSET-USDT-trades-YYYY-MM-DD.zip`

Trusted body host must resolve to exactly:

`static.okx.com`

The metadata stage may use the OKX public market-data-history API and HEAD requests only. It must not download market-data bodies.

## 5. Metadata-only preflight

Runner:

`research/sc001/sc001_c1_selection_spot_metadata_preflight_v0_1.py`

Required report:

`~/sc001_data/SC001_C1_SPOT_SELECTION_CALIBRATION/sc001_c1_spot_metadata_preflight_v0_1.json`

For every candidate SPOT instrument and every permitted label, the preflight attempts to establish:

- exact filename;
- unique trusted URL;
- trusted host;
- exact Content-Length;
- source metadata domain;
- performance versus boundary role.

The runner must never issue a market-body GET.

Metadata queries themselves are restricted to the same whitelist of 32 permitted archive labels. A fallback query to the previous date is allowed only when that previous date is itself in the same whitelist. This prevents the metadata code from silently probing August 30 or other protected/non-whitelisted dates.

## 6. Complete-asset definition

A SPOT candidate is `COMPLETE_METADATA` only if all 32 permitted archive labels are uniquely resolved and have valid positive Content-Length values.

Partial assets remain recorded but may not be downloaded or used by the C1 sentinel under this protocol.

The metadata stage returns exact PASS only when:

- at least 4 of the 8 candidate SPOT instruments are `COMPLETE_METADATA`;
- expected body bytes for all complete instruments fit on disk with a 20 GiB reserve;
- no scope/firewall violation occurs.

Exact PASS token:

`C1_SPOT_METADATA_PREFLIGHT_PASS`

If fewer than 4 complete assets are available, or identity/disk checks fail, return REVIEW rather than changing the universe, dates, thresholds, or mechanism.

## 7. Body acquisition rule after metadata PASS

No body acquisition is authorized before exact metadata PASS and a frozen implementation identity for the downloader/integrity runner.

Any later downloader must:

1. consume only archive identities from the frozen metadata report;
2. download only `COMPLETE_METADATA` instruments;
3. use only the exact 32 permitted labels per admitted instrument;
4. perform no network metadata rediscovery that substitutes another identity;
5. require exact expected filename, HTTPS, `static.okx.com`, and frozen Content-Length before body acceptance;
6. write resumably/atomically where practical;
7. compute and record SHA256;
8. require ZIP CRC and exact trade CSV schema;
9. reconstruct qualified UTC days with causal boundary stitching;
10. mark all bodies permanently `NONPROMOTIONAL_SELECTION_CALIBRATION`.

If a body or identity changes, stop for REVIEW. Do not substitute a clean date.

## 8. UTC reconstruction requirement for later body stage

For each performance UTC day D:

- use only causally required rows from permitted source labels;
- exclude boundary labels from performance attribution;
- require nondecreasing timestamps and no duplicate/backward trade IDs;
- require both trade sides and adequate minute coverage under the same qualified SC001 trade semantics used by prior verified stages.

The body stage may qualify data quality only. It still may not calculate C1 basis/convergence outcomes until the sentinel runner itself is separately frozen.

## 9. Explicit firewalls

Metadata and acquisition reports must state, as applicable:

- `market_data_body_downloaded = false` for metadata stage;
- `strategy_signal_calculated = false`;
- `sentinel_outcome_calculated = false`;
- `basis_calculated = false`;
- `returns_calculated = false`;
- `pnl_calculated = false`;
- `promotional_alpha_accessed = false`;
- `protected_holdout_body_accessed = false`;
- `july_gap_body_accessed = false`;
- `august_protected_body_accessed = false`;
- `october_confirmation_body_accessed = false`;
- `legacy_e006_confirmation_body_accessed = false`.

## 10. Sentinel budget unchanged

This data-gap closure changes no strategy variant, threshold, cost hurdle, MDE rule, feature budget, or candidate definition.

The frozen first-pass C1-C6 sentinel budget remains exactly **11 variants**, with C1 still exactly **1 strict legacy-mechanism variant**.

## 11. Promotion rule

A metadata or body-integrity PASS only establishes data readiness for the nonpromotional C1 sentinel.

It is not evidence that C1 is profitable, executable, or promotable, and it does not authorize protected holdout or Confirmation access.
