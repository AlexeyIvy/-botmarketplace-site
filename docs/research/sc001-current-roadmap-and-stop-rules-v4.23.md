# SC001 Current Roadmap and Stop Rules v4.23

Date: 2026-09-17  
Status: **CURRENT SC001 ROADMAP — C1-C6 SELECTION PREFLIGHT IMPLEMENTATION FROZEN / ONE NO-ALPHA PREFLIGHT RUN NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.22.md`

## 1. Binding terminal states

E001-E008 remain terminal/closed.  
E007R1 remains terminal `E007R1_GROSS_FEASIBILITY_FAIL`.  
E009 remains terminal `E009_GROSS_FEASIBILITY_FAIL`.  
E009 read-only postmortem remains complete.

No prior strategy is reopened.

## 2. Binding selection-stage parents

- `docs/research/sc001-strategy-selection-time-horizon-mechanism-and-feature-framework-v0.3.md`;
- `docs/research/sc001-feature-indicator-research-governance-v0.1.md`;
- `docs/research/sc001-c1-c6-feature-indicator-inventory-v0.1.md`;
- `docs/research/sc001-c1-c6-selection-calibration-sandbox-sentinel-mde-plan-v0.1.md`;
- `docs/research/sc001-selection-research-ledger-v0.1.json`;
- `docs/research/sc001-contamination-registry-v0.4.json`.

## 3. New frozen implementation

Protocol:

`docs/research/sc001-c1-c6-selection-preflight-protocol-v0.1.md`

Runner:

`research/sc001/sc001_c1c6_selection_preflight.py`

Identity freeze:

`docs/research/sc001-c1-c6-selection-preflight-implementation-freeze-v1.0.json`

Exact required token:

`SC001_C1C6_SELECTION_PREFLIGHT_PASS`

Runner blob SHA:

`03ca5185bc1977c11d0dd2efebb22d3820185a6c`

Protocol blob SHA:

`d5eb318ea7ddbe757d1b2ea28d579a2b39e788f7`

## 4. What this preflight does

The preflight is local/integrity-only and calculates no strategy outcome.

It will:

1. verify exact E007R1 July acquisition/semantic parents;
2. re-hash all 128 July trade archives against frozen acquisition batch manifests;
3. verify exact E009 September acquisition/semantic parents;
4. re-hash all 128 September trade archives against frozen acquisition batch manifests;
5. inventory/verify legacy E006 March spot/perp local artifacts when present;
6. scan local SC001 market-body filenames for protected holdout/Confirmation periods;
7. identify the expected C1 July/September multi-asset SPOT source gap;
8. verify Python/NumPy and Git identity;
9. write an atomic preflight report.

No archive CSV is parsed for alpha/signal/PnL in this stage.

## 5. Protected-data firewall

Still forbidden:

- July SOL/FIL/LTC/SUI holdout;
- July 16-30 gap;
- August protected dates 1-30;
- September SOL/FIL/LTC/SUI holdout;
- October 1-14 Confirmation;
- legacy E006 March 22-30 Confirmation.

Any protected local body hit causes preflight FAIL and blocks sentinel work until reconciled.

## 6. Expected C1 data gap

The July/September sandbox currently has qualified perpetual archives. C1 requires synchronized spot/perpetual pairs.

The preflight may report:

`C1 multi-asset spot data gap expected = True`

This is **not** a preflight failure. It means a later separately frozen acquisition stage may acquire SPOT bodies only for the already contaminated July/September dates.

No fresh date may be used to close this gap.

## 7. One-run rule for this stage

The preflight is a deterministic local integrity check and may be rerun after a purely mechanical dependency/path fix, but it must never be modified to hide missing/corrupt/protected data.

No C1-C6 sentinel outcome may be computed before exact preflight PASS.

## 8. After exact PASS

Next engineering sequence:

1. inspect preflight report and C1 spot-gap state;
2. if C1 SPOT data are missing, freeze a contaminated-date-only SPOT metadata/acquisition protocol before any download;
3. implement shared causal trade -> bar/return utilities with synthetic/golden tests;
4. implement six separate sentinel runners under the already frozen 11-variant budget;
5. freeze runner/config identities before first sentinel outcome;
6. run all C1-C6 nonpromotional sentinels on the contaminated sandbox;
7. assign terminal selection dispositions;
8. perform MDE/block planning for survivors;
9. only after all dispositions freeze the small diversified promotional batch.

## 9. Current hard gate

**NO NEW PROMOTIONAL ALPHA.**  
**NO C1-C6 SENTINEL OUTCOME BEFORE `SC001_C1C6_SELECTION_PREFLIGHT_PASS`.**

Immediate next action: run syntax check, then the frozen selection preflight on the VPS.