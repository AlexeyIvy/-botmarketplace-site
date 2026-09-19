# SC001 — B13-A Structural Reject Scope Clarification v0.1

Date: 2026-09-19
Status: **INTERPRETATION NARROWED / ORIGINAL FROZEN VERDICT UNCHANGED**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-b13a-funding-differential-structural-result-v0.3.md`;
- `docs/research/sc001-current-four-role-critical-review-v0.1.md`.

## 1. Original verdict retained

Exact frozen research state remains:

`B13A_REJECT_STRUCTURAL`

No rerun and no parameter change.

## 2. Correct scope

The verdict applies to the tested architecture:

`SINGLE_SETTLEMENT / FOUR_STRUCTURAL_FILL / CROSS_VENUE FUNDING DIFFERENTIAL`

with:

- OKX + Bybit;
- frozen 12-symbol universe;
- H1-2025 structural calibration;
- four-fill burden = 40 bps;
- qualifying funding differential = 50 bps.

Observed maximum upper-bound differential ~27.34 bps was below the frozen 40 bps break-even burden.

## 3. What the verdict does not prove

It does not prove that every possible cross-venue funding-carry architecture is impossible.

A persistent multi-settlement design would differ materially because it changes:

- holding horizon;
- number of funding settlements per entry/exit cycle;
- fill-cost amortization;
- exposure to funding-sign changes;
- cross-venue basis risk;
- liquidation/margin risk;
- collateral/counterparty risk.

Such a design is a new mechanism/architecture.

## 4. Governance

Do not reopen B13-A.

If persistent funding carry is ever reconsidered:

- new base-mechanism ID/card;
- new edge-to-fill statement;
- fresh Selection chronology;
- no reuse of H1-2025 as fresh evidence;
- prospective rules before outcome.

Current priority remains elsewhere.
