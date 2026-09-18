# SC001 — Strategy Landscape v0.5

Date: 2026-09-18
Status: **CURRENT COVERAGE MAP AFTER C10-S0 / NON-ALPHA GOVERNANCE ARTIFACT**
Supersedes: `sc001-strategy-landscape-v0.4.md`

## 1. Inheritance

All terminal/coverage conclusions from v0.4 remain binding.

C1-C6 remain terminal `REJECT_SENTINEL`.

C9-S1 remains terminal `C9_S1_REJECT_SENTINEL`.

C8B-S0 remains terminal `C8B_S0_REJECT_HEADROOM`.

## 2. C10 — one-sided near-touch L2 liquidity vacuum

Frozen structural sentinel:

`C10-S0 one-sided near-touch liquidity-vacuum headroom`

Terminal state:

`C10_S0_REJECT_HEADROOM`

Observed on the frozen 2024-02-12 BTC OKX L2 calibration day:

- bid-vacuum events: 6,443;
- ask-vacuum events: 6,331;
- all 24 UTC hours represented;
- 19 events with absolute 5-second move >=15 bps;
- those large events span 4 UTC hours;
- p50 absolute move ~0.9543 bps;
- p90 absolute move ~3.5799 bps;
- p99 absolute move ~8.4431 bps;
- max absolute move ~39.0877 bps;
- mean signed move ~+0.5803 bps;
- positive signed-move share ~58.67%.

Coverage implication:

- the exact broad one-sided vacuum -> 5-second directional-headroom mechanism is covered with negative standalone structural evidence;
- event frequency and side breadth were ample;
- rare large-move tails exist, but the frozen p90 gate prevented a tail-only mechanism from being promoted post hoc.

No threshold/horizon/side/C5 rescue is authorized.

## 3. Reusable knowledge retained

C10 contributes:

- causal top-5 near-touch depth state;
- side-specific local depth normalization;
- one-sided depth-vacuum onset as a weak directional/R2 state with rare-tail association.

See:

- `sc001-feature-evidence-registry-v0.5.md`;
- `sc001-reusable-market-building-blocks-registry-v0.4.md`.

## 4. Remaining next-slate gap

The remaining previously defined next-slate direction is:

`C7 — spread-qualified non-BTC/multi-asset passive/hybrid maker universe`.

C7 remains scientifically distinct only if:

- it is not an E008 BTC same-rule retest;
- universe selection is prospective and non-PnL;
- spread/headroom is screened before queue/fill modeling;
- new multi-asset L2 acquisition is staged and bounded.

## 5. Immediate next direction

Proceed to a metadata-only C7 historical L2 availability preflight on the pre-existing non-BTC SC001 asset set.

No spread outcome, body download, queue model, fill simulation or PnL is authorized in the first C7 stage.
