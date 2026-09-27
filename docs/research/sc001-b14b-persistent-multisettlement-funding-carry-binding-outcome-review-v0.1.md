# SC001 — B14-B Persistent Multi-Settlement Funding Carry Binding Outcome Review v0.1

Date: 2026-09-27
Status: **B14B_REJECT_PERSISTENT_CARRY_STRUCTURAL / TERMINAL FOR THIS FROZEN ARCHITECTURE**

## 1. Technical result

The networked VPS run completed normally under systemd.

Terminal classification:

`B14B_REJECT_PERSISTENT_CARRY_STRUCTURAL`

Valid non-overlapping seven-day cycles:

`110`

All frozen data/sample gates passed.

## 2. Frozen economics

Pooled seven-day gross funding carry:
- p25 = `-2.5951 bps`;
- median = `+1.3863 bps`;
- p75 = `+3.6405 bps`;
- positive cycles = `67 / 110 = 60.9091%`.

Breadth:
- positive-median symbols = `8`;
- positive-median cycle-start months = `3`.

Frozen structural gates:

PASS:
- positive cycle share >=60%;
- >=6 positive-median symbols;
- >=2 positive-median months.

FAIL:
- median gross carry >=50 bps.

Observed median / hurdle:

`1.3863 / 50 = 2.77%`

## 3. Interpretation

The frozen 3-confirmation funding-differential signal shows a broad directional persistence property:
- positive cycle share exceeds 60%;
- 8 symbols have positive median carry;
- all 3 represented cycle-start months have positive median carry.

However, the accumulated seven-day funding transfer is economically tiny.

This is therefore:
- not a source-quality failure;
- not a sample-size failure;
- not a direction-sign failure;
- an **economic magnitude failure**.

The 75th percentile is only about 3.64 bps, still far below the 40 bps four-fill structural burden, before adding capital lock, basis drift, liquidation buffer, or venue risk.

Therefore no price/basis/PnL stage is warranted.

## 4. Binding consequence

Close the exact architecture:

`3 same-sign matched funding differentials -> fixed direction -> 7-day non-overlapping cross-venue carry`

Do not rescue it on the same fresh window by:
- longer or shorter holds;
- larger funding thresholds;
- choosing only certain symbols;
- changing confirmation count;
- using only extreme differential episodes;
- adding basis convergence PnL.

Those would be post-outcome tuning.

## 5. Reusable information

The parent strategy fails, but one market-behavior block remains supported:

`RB022 — Persistent cross-venue funding-differential direction state v0.1`

The useful part is **directional persistence**, not economic carry magnitude.

Potential future roles:
- R2 derivative/funding regime state;
- R3 confirmation/veto for another independently valid mechanism;
- R4 capital/risk context when funding alignment materially changes holding cost;
- R6 cross-venue funding-state reference.

Reuse requires a new prospectively frozen mechanism and fresh evidence.
