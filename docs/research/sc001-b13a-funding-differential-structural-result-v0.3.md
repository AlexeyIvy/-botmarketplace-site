# SC001 — B13-A Funding-Differential Structural Preflight Result v0.3

Date: 2026-09-19
Status: **B13A_REJECT_STRUCTURAL**
Scope: `SCALPING RESEARCH / SC001`

## 1. Exact terminal state

`B13A_REJECT_STRUCTURAL`

B13-A remains a pre-candidate and does not receive a C13 experiment ID.

## 2. Data/source quality

Observed:

- source-eligible symbols: `12 / 12`;
- matched funding settlements: `6,634`;
- matched calendar months: `6 / 6` across 2025-01 through 2025-06;
- matching timestamp skew median: `0 ms`;
- matching timestamp skew p99: `0 ms`.

The source/sample gate passed decisively.

## 3. Frozen structural economics

Frozen four-fill burden:

`40 bps`

Frozen qualifying differential:

`>=50 bps`

Observed funding-differential distribution:

- median: ~`0.4113 bps`;
- p90: ~`1.1656 bps`;
- p99: ~`2.2231 bps`;
- maximum: ~`27.3375 bps`.

Qualifying >=50 bps opportunities:

`0`

Therefore:

- qualifying dates = 0;
- qualifying months = 0;
- qualifying symbols = 0.

All structural opportunity/breadth gates failed.

## 4. Interpretation

The rejection is stronger than merely failing the 50 bps reserve threshold.

Even the maximum observed upper-bound funding differential (~27.34 bps) is below the frozen 40 bps four-fill break-even structural burden.

Therefore the funding transfer itself cannot support the proposed delta-neutral four-fill architecture on the frozen H1-2025 12-symbol universe.

No price convergence, basis return or maker assumption is needed to reach this conclusion.

## 5. What is forbidden

Do not rescue B13-A by:

- reducing four fills;
- lowering fee/spread/model reserve;
- using maker rebates;
- selecting only extreme symbols/months;
- adding basis convergence PnL;
- widening settlement matching;
- adding C1-C12 features.

A materially different funding architecture would be a new mechanism.

## 6. Firewalls preserved

Observed false:

- price accessed;
- basis calculated;
- strategy price PnL;
- promotional evidence;
- candidate ID assigned.

## 7. Final B13-A disposition

`B13A_REJECT_STRUCTURAL`

No further B13-A research is authorized under this architecture.

Next independent mechanism:

`B13-B scheduled new-perpetual launch price-discovery dislocation`

starts with source/event-census feasibility only.
