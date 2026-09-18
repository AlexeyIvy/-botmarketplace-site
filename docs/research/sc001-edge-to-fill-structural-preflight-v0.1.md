# SC001 — Edge-to-Fill Structural Preflight v0.1

Date: 2026-09-18
Status: **BINDING NON-ALPHA PREFLIGHT FOR ALL C11+ CANDIDATES**
Scope: `SCALPING RESEARCH / SC001`

## 1. Purpose

Prevent expensive outcome-bearing experiments when the proposed economic architecture is implausible before backtesting.

This preflight is required before assigning a new C11+ candidate ID.

## 2. Required inputs

For every proposed candidate record prospectively:

- independent base mechanism;
- who/what economically pays for the edge;
- expected informational-edge scale;
- signal horizon;
- expected hold;
- number of structural fills;
- maker/taker mix;
- conservative fee floor;
- spread/depth exposure;
- funding/borrow exposure;
- execution/model reserve;
- break-even gross move;
- minimum economic reserve;
- expected opportunity rate;
- capital-time utilization;
- capacity/liquidity concerns;
- fresh evidence availability.

## 3. Edge-scale prior

Unless a separate mechanism explains otherwise, use the SC001 empirical design prior:

`ordinary liquid-crypto conditional information often appears in the ~0.5-4 bps range`.

This is not a universal law and must not replace mechanism-specific reasoning.

If a candidate requires >10-30 bps of gross edge to work, its card must explain prospectively why such scale is economically plausible.

## 4. Structural fill accounting

Count fills before outcome:

- one-sided entry + exit = 2 fills;
- paired relative-value entry + exit = 4 fills;
- additional hedge/rebalance legs count unless already mandatory for the independent base opportunity.

Do not ignore fills because they are expected to be maker.

## 5. Conservative burden

Define:

`structural_burden_bps = fee_floor + spread/depth_cost_reference + execution/model_reserve + funding/borrow_reference`

No single historical best-case fee tier may be used to justify feasibility.

## 6. Required edge-to-fill statement

Every card must explicitly state:

`expected_information_scale_bps / structural_burden_bps`

and classify:

- `CLEARLY_PLAUSIBLE`;
- `PLAUSIBLE_IF_EXECUTION_IMPROVES`;
- `MARGINALLY_PLAUSIBLE`;
- `STRUCTURALLY_IMPLAUSIBLE`;
- `UNKNOWN_NEEDS_NON_ALPHA_DATA`.

## 7. Hard structural stop

Reject before backtest if any:

- no independent source of economic edge;
- expected information scale is materially below conservative burden;
- edge only becomes plausible after lowering fees/reserves post hoc;
- architecture adds new fills solely to monetize a weak feature;
- required opportunity count is incompatible with capital-time use;
- only historical winner assets make the arithmetic plausible;
- candidate is a disguised rescue of a terminal C1-C10 mechanism.

Disposition:

`REJECT_STRUCTURAL`

## 8. Weak-feature exception

A weak feature may proceed as auxiliary R2/R3/R5 only if:

- an independent base opportunity already exists;
- the feature adds no new structural fills;
- its role is prospectively frozen;
- evaluation is incremental BASE vs BASE+FEATURE on the same opportunities;
- retained-opportunity share, turnover and risk are reported.

## 9. Fresh-evidence requirement

Anything used to choose:

- feature role;
- threshold;
- interaction;
- horizon;
- asset subset;
- execution mode;

becomes nonpromotional for that implementation.

## 10. Governance consequence

No C11+ ID may be assigned until:

1. candidate card v0.2 is complete;
2. Edge-to-Fill preflight is complete;
3. non-alpha feasibility review disposition is one of:
   - `HOLD_INFORMATION_VALUE`;
   - `ELIGIBLE_FOR_BATCH`;
   - `SELECTED_FOR_FROZEN_EXPERIMENT`.

Only `SELECTED_FOR_FROZEN_EXPERIMENT` authorizes experiment-ID assignment and later sentinel freeze.
