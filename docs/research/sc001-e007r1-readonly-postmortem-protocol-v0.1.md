# SC001-E007R1 — Read-Only Gross-Feasibility Postmortem Protocol v0.1

Date: 2026-09-17  
Status: **FROZEN AFTER TERMINAL E007R1 GROSS FAIL / READ-ONLY DIAGNOSTIC ONLY**

## 1. Purpose

Explain the already-observed terminal result:

`E007R1_GROSS_FEASIBILITY_FAIL`

without rerunning E007R1, changing any parameter, opening asset-holdout bodies, opening August Confirmation, accessing L2, resolving historical execution specs, or calculating discrete/net PnL.

This postmortem is diagnostic only. It cannot reopen E007R1 and cannot convert any post-hoc pattern into a tradable filter without a new experiment ID and untouched data.

## 2. Frozen parent result

The parent gross-feasibility report must be exact terminal FAIL and must retain:

- 8/8 Discovery assets attempted;
- pooled completed events = 161;
- equal-weight mean instrument gross edge ~= 5.5936 bps;
- median instrument mean ~= 3.5978 bps;
- positive instruments = 4/8;
- pooled 10% trimmed mean ~= 15.1079 bps;
- pooled median ~= 30.8807 bps;
- 1000 ms equal-weight mean ~= 5.3177 bps;
- 2000 ms equal-weight mean ~= 5.0698 bps;
- top absolute contribution share ~= 0.18183;
- failed mandatory gates exactly preserved from the parent report.

The parent protocol remains `sc001-e007r1-multiasset-gross-feasibility-protocol-v0.1.md`.

## 3. Allowed calculations

Read only the existing JSON report:

`~/sc001_data/SC001_E007R1_GROSS_FEASIBILITY/sc001_e007r1_gross_feasibility_report.json`

Allowed diagnostics:

- per-instrument completed count, active-day count and completion rate;
- per-instrument mean, median and trimmed gross edge;
- per-instrument positive-event and positive-day share;
- long/short counts and mean gross edge;
- 500/1000/2000 ms per-instrument mean comparison;
- per-instrument absolute/signed gross contribution;
- event-count weights and concentration;
- cross-instrument dispersion of means;
- pooled mean versus equal-weight mean versus median-instrument mean;
- calendar-day breadth using already-stored `day_means` only;
- identification of strongest/weakest instruments strictly as explanatory diagnostics;
- classification of whether the failure is mainly breadth, average-headroom, latency, sample/activity, or concentration related.

## 4. Prohibited calculations/actions

Do not:

- rerun the gross engine;
- change threshold, target, hold, latency, cooldown, cap or signs;
- exclude losing instruments;
- open SOL/FIL/LTC/SUI bodies;
- open August Confirmation;
- open July 16..30;
- access L2;
- calculate net PnL or historical fee-adjusted PnL;
- use current contract specs as historical proof;
- declare a profitable subset as a strategy;
- create a post-hoc regime/token filter from this result.

## 5. Interpretation rule

The postmortem must distinguish:

1. **event-level effect exists somewhere** — pooled median/trimmed statistics can be positive;
2. **cross-market portability is insufficient** — equal-weight/median-instrument breadth gates failed;
3. **latency robustness is insufficient** — 1000/2000 ms equal-weight gates failed;
4. **concentration was not the principal failure** when the frozen top-contribution gate passed.

A subset of positive instruments is evidence for mechanism heterogeneity, not permission to drop the negative instruments after seeing outcomes.

## 6. Exact terminal token

Successful read-only analysis prints:

`E007R1_READONLY_POSTMORTEM_PASS`

and must also print:

- `strategy rerun performed = False`;
- `E007R1 terminal decision changed = False`;
- `asset holdout accessed = False`;
- `August Confirmation accessed = False`;
- `discrete/net PnL calculated = False`.
