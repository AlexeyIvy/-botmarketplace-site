# SC001 Current Roadmap and Stop Rules v4.30

Date: 2026-09-18  
Status: **CURRENT SC001 ROADMAP — C1-C6 SENTINEL BATCH COMPLETE / 0 SURVIVORS / NEXT-SLATE DESIGN ACTIVE**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.29.md`

## 1. Binding terminal strategy states

E001-E008 remain terminal/closed.  
E007R1 remains terminal `E007R1_GROSS_FEASIBILITY_FAIL`.  
E009 remains terminal `E009_GROSS_FEASIBILITY_FAIL`.

C1-C6 first-pass Selection/Calibration sentinel states are now also frozen:

- C1 `C1_REJECT_SENTINEL`;
- C2 `C2_REJECT_SENTINEL`;
- C3 `C3_REJECT_SENTINEL`;
- C4 `C4_REJECT_SENTINEL`;
- C5 `C5_REJECT_SENTINEL`;
- C6 `C6_REJECT_SENTINEL`.

No direct rescue-tuning is authorized.

## 2. Batch integrity

The all-six frozen batch completed exact:

`SC001_C1C6_SENTINEL_BATCH_COMPLETE`

with:

- all six attempted;
- all six recognized terminal reports;
- total variants = 11;
- no between-result adaptation;
- protected data false;
- promotional alpha false;
- batch exit code 0.

Therefore the six rejections are research outcomes, not runtime failures.

## 3. Read-only postmortem

Binding result record:

`docs/research/sc001-c1-c6-sentinel-batch-results-readonly-postmortem-v0.1.md`

Key failure classes:

- C1: event scarcity under strict frozen basis mechanism;
- C2: abundant sample but negative mean-reversion effect;
- C3: abundant sample but no continuation headroom;
- C4: broad residual sign but sub-1-bps effect;
- C5: abundant broad sign but sub-1-bps effect;
- C6: positive low-single-digit spread but insufficient four-fill headroom.

## 4. MDE consequence

There are no `ELIGIBLE_FOR_BATCH` survivors.

Therefore:

- no C1-C6 MDE/block planning is required;
- no promotional batch is opened from C1-C6;
- no protected holdout or Confirmation period is opened;
- no candidate is rescued by changing thresholds, horizons, filters, assets, or features.

## 5. Feature evidence and landscape updated

Current feature registry:

`docs/research/sc001-feature-evidence-registry-v0.2.md`

Current strategy landscape:

`docs/research/sc001-strategy-landscape-v0.2.md`

The central cross-candidate lesson is that several mechanisms contain weak directional structure, but their gross magnitude is far below structural execution reserves.

## 6. Current research phase

SC001 now enters:

`NEXT-SLATE LANDSCAPE REALLOCATION / NON-ALPHA DESIGN`

The next candidates must be materially different from C1-C6, not parameter-neighbor repackaging.

## 7. Priority information gaps for next-slate design

Potentially valuable under-covered areas include:

1. passive/hybrid liquidity provision on a prospectively spread/fee-eligible non-BTC universe;
2. cross-venue relative value or information transfer using independent venue clocks and execution;
3. derivative-state mechanisms materially different from strict C1 basis convergence, such as funding/mark/index state if historical data and cost mechanics are cleanly available;
4. low-directional-beta mechanisms with fewer structural fills than C6;
5. execution-structure edges where the economic mechanism is not a sub-bps directional prediction.

These are research directions, not yet frozen candidates and not claims of profitability.

## 8. Hard exclusions for next slate

Do not create a nominally new candidate by:

- lowering C1 threshold;
- adding a trend/volatility veto to C2;
- adding ADX/MACD/volume/flow to C3;
- grid-searching C4 lags/leaders/targets;
- adding L2 to rescue C5;
- adding factors/volatility scaling/winner assets to C6.

A new candidate must materially change mechanism, execution architecture, market relationship, information source, risk signature, or non-neighbor horizon logic.

## 9. Protected data remain closed

Still closed:

- July SOL/FIL/LTC/SUI holdout;
- July 16-30 gap;
- August 1-30 protected period;
- September SOL/FIL/LTC/SUI holdout;
- October Confirmation;
- legacy E006 March 22-30 SPOT Confirmation.

## 10. Immediate next sequence

1. complete next-slate landscape review;
2. create non-alpha feasibility cards for a small number of materially orthogonal candidates;
3. score only structural/data feasibility, not historical profitability;
4. define cheapest falsification sentinel for each;
5. freeze a new variant budget before any outcome;
6. use only already contaminated selection/calibration data or separately governed newly contaminated calibration sources;
7. keep promotional alpha closed until a new diversified batch is prospectively frozen.

Immediate next action: design the next candidate slate from the updated landscape and feature registry. No new alpha run yet.
