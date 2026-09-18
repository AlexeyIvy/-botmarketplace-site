# SC001 — C1-C6 Nonpromotional Sentinel Batch Execution Protocol v0.1

Date: 2026-09-18  
Status: **FROZEN AFTER MASTER IMPLEMENTATION PREFLIGHT PASS / BEFORE FIRST SENTINEL OUTCOME**  
Scope: `SCALPING RESEARCH / SC001`

## 1. Purpose

Execute the already-frozen C1-C6 Selection/Calibration sentinels as one indivisible first-pass batch, preventing between-result adaptation.

This protocol changes no candidate, parameter, threshold, horizon, feature, asset universe, cost hurdle, chronology, or multiplicity budget.

## 2. Preconditions

Required local master implementation report:

`~/sc001_data/SC001_C1C6_SENTINEL_IMPLEMENTATION_PREFLIGHT/sc001_c1c6_sentinel_implementation_preflight_v0_1.json`

Required exact status:

`SC001_C1C6_SENTINEL_IMPLEMENTATION_PREFLIGHT_PASS`

Required:

- candidate preflights = 6/6;
- total strategy variants = 11;
- no sentinel outcome calculated by master preflight;
- no protected data accessed;
- no promotional alpha accessed.

The frozen C1-C6 implementation freeze must match its exact Git blob identity.

## 3. Fixed execution order

The batch order is frozen:

1. C1;
2. C2;
3. C3;
4. C4;
5. C5;
6. C6.

Order has no interpretive meaning and may not be changed based on results.

## 4. No between-result adaptation

During batch execution:

- each candidate runner is launched exactly once in `run` mode;
- stdout/stderr for each candidate is captured to candidate-specific local log files;
- candidate outcome text is not emitted to the interactive console before all six attempts finish;
- no human/LLM choice is requested between candidates;
- no threshold/horizon/filter/asset/calendar change is allowed;
- a SURVIVE/REJECT/DEFER status never stops the remaining candidates.

## 5. Mechanical failure semantics

A nonzero runner exit code, missing terminal report, unknown terminal status, identity failure, or runtime exception is:

`SC001_C1C6_SENTINEL_BATCH_EXECUTION_FAIL`

This is an implementation/execution failure, **not** a sentinel REJECT and not research evidence.

The batch runner should continue attempting the remaining candidates after a mechanical candidate failure so the fixed order is not adaptively truncated.

No failed implementation may be "rescued" by tuning after partial outcomes.

## 6. Recognized candidate terminal statuses

C1:
- `C1_SENTINEL_SURVIVE`
- `C1_DEFER_SAMPLE_INSUFFICIENT`
- `C1_REJECT_SENTINEL`

C2:
- `C2_SENTINEL_SURVIVE`
- `C2_REJECT_SENTINEL`

C3:
- `C3_SENTINEL_SURVIVE`
- `C3_REJECT_SENTINEL`

C4:
- `C4_SENTINEL_SURVIVE`
- `C4_REJECT_SENTINEL`

C5:
- `C5_SENTINEL_SURVIVE`
- `C5_DEFER_SAMPLE_INSUFFICIENT`
- `C5_REJECT_SENTINEL`

C6:
- `C6_SENTINEL_SURVIVE`
- `C6_REJECT_SENTINEL`

If all six runner executions finish with recognized terminal reports, the batch terminal status is:

`SC001_C1C6_SENTINEL_BATCH_COMPLETE`

This means only that the frozen nonpromotional batch completed. It is not a claim that any candidate survived.

## 7. One-shot guard

Before batch `run`:

- no candidate terminal report may already exist;
- no prior terminal batch report may exist.

The runner must refuse to overwrite terminal evidence.

## 8. Batch report

Write:

`~/sc001_data/SC001_C1C6_SENTINEL_BATCH/sc001_c1c6_sentinel_batch_report_v0_1.json`

The report records:

- frozen identities;
- per-candidate return code;
- per-candidate terminal status after all six attempts;
- per-candidate report/log path;
- execution errors if any;
- total variant budget 11;
- protected/promotional firewalls.

Candidate stdout/stderr remain in local log files for audit.

## 9. Protected-data and evidence semantics

Only the frozen contaminated Selection/Calibration sandbox may be used.

Protected holdouts and Confirmation periods remain closed.

All sentinel outcomes are:

`SELECTION_CALIBRATION_ONLY`

They are nonpromotional and do not authorize live trading.

## 10. After batch completion

Only after all six terminal dispositions are known may the project:

1. inspect the complete batch;
2. assign/confirm selection dispositions;
3. perform MDE/block planning for survivors;
4. freeze a diversified promotional research batch.

No candidate may be promoted merely because it is the first or only survivor.
