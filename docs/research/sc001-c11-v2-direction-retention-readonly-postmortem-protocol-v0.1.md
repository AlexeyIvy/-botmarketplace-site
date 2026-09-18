# SC001 — C11 v2 Direction-Retention Read-Only Postmortem Protocol v0.1

Date: 2026-09-19
Status: **FROZEN READ-ONLY DIAGNOSTIC AFTER TERMINAL SELECTION REJECT**
Scope: `SCALPING RESEARCH / SC001`

Parent:

`docs/research/sc001-c11-v2-selection-stage-ab-result-v1.1.md`

## 1. Purpose

Explain the structure of:

`C11_V2_SC_REJECT_DIRECTION_RETENTION`

using only the already-generated v1.1 Selection report.

No market archive may be reopened.

No new market outcome may be calculated.

## 2. Allowed inputs

Only:

`~/sc001_data/SC001_C11_V2_SELECTION_AB/sc001_c11_v2_selection_stage_ab_report_v1_1.json`

The parent report must have exact terminal state:

`C11_V2_SC_REJECT_DIRECTION_RETENTION`

## 3. Allowed descriptive diagnostics

May report:

- Stage A residual-headroom count and median already present;
- Stage B signed-continuation count and median already present;
- positive signed-continuation share;
- among events with absolute residual >=20 bps:
  - count;
  - count with signed continuation >0;
  - count with signed continuation >=20 bps;
  - count with signed continuation <=0;
- descriptive CPI vs Employment:
  - median signed continuation;
  - positive signed count;
  - >=20 bps signed count;
- median absolute first impulse;
- LONG/SHORT counts already frozen;
- worst/best frozen signed continuation values;
- schema counts.

These are descriptive only.

## 4. Forbidden diagnostics

Do not calculate:

- reversal strategy returns;
- sign-flipped outcomes;
- alternative impulse windows;
- alternative entry delays;
- alternative continuation horizons;
- nonzero impulse thresholds;
- CPI-only or Employment-only strategy verdicts;
- event-subset strategy scores;
- macro surprise relationships;
- execution/PnL;
- optimized thresholds.

## 5. Required conclusion categories

The postmortem may classify the observed failure structure using non-promotional labels such as:

- `RESIDUAL_HEADROOM_EXISTS_DIRECTION_CAPTURE_WEAK`;
- `FAILURE_CONCENTRATED_IN_WRONG_SIGN`;
- `FAILURE_CONCENTRATED_IN_TOO_SMALL_SAME_SIGN_MOVE`;
- `MIXED_DIRECTION_CAPTURE_FAILURE`.

It must not invent a replacement rule.

## 6. Consequence

After the postmortem, perform a three-role review and decide one of:

1. terminalize C11 as a trading-strategy candidate while retaining scheduled macro-event risk state;
2. justify a genuinely new direction-extractor candidate with a new experiment ID and fresh evidence.

No Confirmation and no C13+ before that disposition is recorded.
