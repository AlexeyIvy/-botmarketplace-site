# SC001 — C1-C6 Selection/Calibration Implementation Preflight Protocol v0.1

Date: 2026-09-17  
Status: **FROZEN BEFORE FIRST C1-C6 SENTINEL OUTCOME**  
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-current-roadmap-and-stop-rules-v4.22.md`;
- `docs/research/sc001-c1-c6-selection-calibration-sandbox-sentinel-mde-plan-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.4.json`;
- `docs/research/sc001-c1-c6-feature-indicator-inventory-v0.1.md`.

## 1. Purpose

This stage is a **no-alpha local integrity/inventory preflight** before implementing any C1-C6 sentinel computation.

It must establish that:

1. the already contaminated July E007R1 trade sandbox is locally intact and tied to exact qualified parents;
2. the already contaminated September E009 trade sandbox is locally intact and tied to exact qualified parents;
3. legacy E006 March BTC spot/perpetual engineering artifacts are inventoried where locally present;
4. missing July/September multi-asset SPOT sources needed by C1 are identified as a data gap rather than silently substituted;
5. protected holdout/Confirmation periods have not appeared as local market-body files under the SC001 data root;
6. required runtime dependencies are present;
7. no strategy signal, sentinel outcome, return or PnL is calculated.

A PASS authorizes only implementation of shared causal utilities and the frozen nonpromotional sentinel runners. It does **not** authorize promotional alpha, holdout access or Confirmation access.

## 2. Allowed local inputs

### July contaminated parent

- `~/sc001_data/SC001_E007R1_TRADE_ACQUISITION/`;
- `~/sc001_data/SC001_E007R1_TRADE_SEMANTIC_INTEGRITY/sc001_e007r1_trade_semantic_integrity_report.json`.

Required parent states:

- acquisition verify status `E007R1_TRADE_ACQUISITION_VERIFY_PASS`;
- exactly 128 verified files;
- semantic status `E007R1_TRADE_SEMANTIC_INTEGRITY_PASS`;
- `source_files_qualified = 128`;
- `reconstructed_utc_days_qualified = 120`;
- asset holdout and August Confirmation firewalls remain false.

### September contaminated parent

- `~/sc001_data/SC001_E009_TRADE_ACQUISITION/`;
- `~/sc001_data/SC001_E009_TRADE_SEMANTIC_INTEGRITY/sc001_e009_trade_semantic_integrity_report.json`.

Required parent states:

- acquisition verify status `E009_TRADE_ACQUISITION_VERIFY_PASS`;
- exactly 128 verified files;
- semantic status `E009_TRADE_SEMANTIC_INTEGRITY_PASS`;
- `source_files_qualified = 128`;
- `reconstructed_utc_days_qualified = 120`;
- asset holdout, October Confirmation and August-repurposed firewalls remain false.

### Legacy E006 optional local supplement

If present, inventory and verify consistency of:

- `~/sc001_data/SC001_E006_SPOT_FEASIBILITY/sc001_e006_spot_body_integrity_report.json`;
- `~/sc001_data/SC001_E003_OKX_MARCH_TRADES/sc001_e003_okx_march_trade_stage_report.json`;
- associated March 1-21 BTC spot/perpetual archives.

Missing legacy E006 local artifacts are reported as an optional calibration gap, not a reason to weaken or alter any sentinel.

## 3. Integrity policy

For July and September trade archives the preflight must reconcile the four acquisition batch manifests and verify for every expected archive:

- exact filename identity;
- local existence;
- exact byte count recorded by the batch manifest;
- exact SHA256 recorded by the batch manifest.

It must reconcile to exactly 128 archives per sandbox.

This integrity read is data-engineering only. Archive CSV contents must not be parsed for strategy features or outcomes.

## 4. Protected body firewall

The preflight scans local **market-body file names only** (`.zip`, `.csv`, `.gz`, `.parquet`, `.feather`) under `SC001_DATA_ROOT` for evidence of protected periods.

Forbidden for this stage:

- SOL/FIL/LTC/SUI market bodies on `2024-07-01..2024-07-14`;
- any market body on `2024-07-16..2024-07-30`;
- any market body on `2024-08-01..2024-08-30`;
- SOL/FIL/LTC/SUI market bodies on `2024-09-01..2024-09-14`;
- any market body on `2024-10-01..2024-10-14`;
- BTC spot/perp market bodies on legacy E006 Confirmation `2024-03-22..2024-03-30` when stored inside the E006/E003 March source roots used by this branch.

Boundary dates explicitly allowed by current governance remain allowed (`2024-06-30`, `2024-07-15`, `2024-08-31`, `2024-09-15`, legacy March 21 boundary where already used).

Any forbidden local body hit => preflight FAIL and no sentinel implementation/run until reconciled.

## 5. C1 July/September SPOT gap

C1 needs synchronized same-venue spot and perpetual data. The existing July/September contaminated sandboxes are perpetual-only parents.

The preflight must therefore report whether a dedicated local multi-asset spot-calibration source already exists. Absence is an **expected data gap**, not a preflight failure.

No fresh date may be downloaded to close this gap. Any future acquisition may use only the already contaminated July/September sandbox dates under a separately frozen data-acquisition protocol.

## 6. Runtime

Require:

- Python 3;
- NumPy import succeeds;
- repository is a Git worktree and the runner/protocol identity matches the implementation freeze manifest.

## 7. Required report

Write atomically:

`~/sc001_data/SC001_C1C6_SELECTION_PREFLIGHT/sc001_c1c6_selection_preflight_report.json`

Report at least:

- exact status;
- runner/protocol Git blob identities;
- NumPy version;
- July parent statuses/counts and archive integrity totals;
- September parent statuses/counts and archive integrity totals;
- legacy E006 local readiness/inventory state;
- C1 July/September multi-asset spot-gap state;
- protected-body scan count and paths if any;
- `strategy_signal_calculated = false`;
- `sentinel_outcome_calculated = false`;
- `pnl_calculated = false`;
- `promotional_alpha_accessed = false`;
- all protected-role access flags false.

## 8. Exact terminal token

PASS token:

`SC001_C1C6_SELECTION_PREFLIGHT_PASS`

Any identity/integrity/firewall/runtime failure must terminate without this token.

A PASS does not mean C1-C6 are profitable or even sentinel-eligible. It means only that the contaminated selection sandbox and implementation prerequisites are safe enough to proceed to sentinel engineering.