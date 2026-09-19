# SC001 — Strategy Landscape v0.8

Date: 2026-09-19
Status: **CURRENT COVERAGE MAP AFTER C11 FINAL DIRECTION-CAPTURE REJECT**
Supersedes: `sc001-strategy-landscape-v0.7.md`

## 1. Binding terminal states

All prior terminal decisions remain binding.

C1-C10 remain terminal/closed.

C12 remains terminal:

`C12_S0_REJECT_PARITY_REVERSION`

C11 trading candidate is now terminal:

`C11_TERMINAL_REJECT_DIRECTION_CAPTURE`

Historical C11 sub-states remain preserved:

- `C11_S0_EVENT_MOVE_HEADROOM_SURVIVE`;
- `C11_S1_DEFER_SAMPLE`;
- `C11_V2_SC_REJECT_DIRECTION_RETENTION`.

## 2. C11 final interpretation

C11 established strong event opportunity scale:

- H1 raw median abs 60s move ~45.26 bps;
- fresh Selection median abs residual +1s -> +60s ~24.11 bps;
- 14/24 fresh events retained >=20 bps absolute residual movement.

But Direction Rule v2 failed:

- median signed continuation ~3.63 bps;
- only 6/24 scheduled events reached >=20 bps in the selected direction;
- among 14 large-residual events, 8 had wrong-or-zero direction.

Therefore:

`LARGE_EVENT_MOVEMENT_PRESENT / TESTED_CAUSAL_DIRECTION_EXTRACTOR_INADEQUATE`

No Confirmation or execution/PnL.

## 3. Reusable C11 knowledge

Retain:

- F027 scheduled macro-event movement/risk state;
- F028 first-1s impulse sign rejected as standalone direction extractor;
- RB020 scheduled macro-event risk state.

Do not convert these into directional trading claims.

## 4. C12 remains closed

C12 still provides:

- RB019 direct stablecoin parity-stress state;
- rare stress/collateral-risk information.

No strategy reopening.

## 5. Current research frontier

There is no active surviving trading candidate after C11 terminalization.

The next step is not C11 rescue.

Return to independent-base opportunity design.

Any new candidate must explain why its expected economic scale can plausibly exceed fill/cost burden.

## 6. C13+ gate

The previous block on C13+ was conditional on C11 being unresolved.

That condition is now cleared.

C13+ may proceed to **non-alpha design and structural feasibility only**.

Before any outcome:

- candidate ID;
- mechanism;
- edge-to-fill review;
- feature inventory;
- contamination audit;
- fresh chronology;
- cheapest frozen sentinel.

No automatic promotion from C11/C12 reusable states.
