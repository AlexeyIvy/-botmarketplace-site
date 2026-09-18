# SC001 Current Roadmap and Stop Rules v4.71

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — C12 CLOSED / C11 V2 FRESH-DIRECTION DESIGN STAGE**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.70.md`

## 1. Binding terminal states

All prior terminal decisions remain immutable.

C12 remains terminal:

`C12_S0_REJECT_PARITY_REVERSION`

No C12 rescue tuning is authorized.

C11-S0 remains:

`C11_S0_EVENT_MOVE_HEADROOM_SURVIVE`

C11-S1 remains:

`C11_S1_DEFER_SAMPLE`

and must not be interpreted as REJECT.

## 2. Three-role review incorporated

Binding expert synthesis:

`docs/research/sc001-c11-c12-three-role-current-state-review-v0.1.md`

Key additions:

- distinguish DATA_INVALID from NO_TRADE;
- preserve opportunity-retention denominators;
- separate C11 residual headroom, direction quality and execution;
- treat C11 as a causal capture/execution problem, not generic signal discovery;
- retain scheduled macro-event risk and stablecoin parity-stress states as operational risk features;
- prefer counts/medians/breadth over fragile high-quantile inference in small-N event samples.

## 3. C11 v2 design plan

Binding design plan:

`docs/research/sc001-c11-direction-rule-v2-research-plan-v0.1.md`

No new price outcome is authorized by the plan itself.

## 4. Preferred minimal-complexity v2 rule

Subject to final fresh-chronology freeze:

- first causal 1-second post-release impulse;
- positive -> LONG;
- negative -> SHORT;
- exactly zero -> NO_TRADE.

This is preferred because it changes semantics rather than searching a new time window.

Do not compare multiple impulse windows on fresh outcomes.

## 5. Required fresh chronology

H1-2025 is contaminated for C11 directional-rule design.

Before any C11-v2 outcome:

- audit candidate periods for prior SC001 use;
- choose chronology prospectively by calendar;
- freeze CPI + Employment event list;
- verify BLS event metadata and BTC archive source availability;
- prospectively split:
  - Selection/Calibration;
  - untouched Confirmation.

No outcome before the split is frozen.

## 6. C11-v2 research sequence

### Stage A — residual post-decision headroom

Measure absolute +1s to +60s move.

Purpose:

Confirm that enough movement remains after the causal decision point.

### Stage B — direction + opportunity retention

Evaluate the frozen direction rule while reporting:

- scheduled count;
- data-valid count;
- actionable count;
- NO_TRADE count;
- actionable share;
- CPI breadth;
- Employment breadth;
- signed continuation economics.

### Stage C — untouched Confirmation

Allowed only if Stage A and Stage B survive.

No rule changes.

### Stage D — event execution

Allowed only after Confirmation survives.

Model event slippage/latency/fills and net economics.

## 7. Research-kernel semantic improvement

Future runners/reports should use:

- DATA_INVALID;
- NO_TRADE;
- LONG;
- SHORT;
- verdict_computed;
- null for metrics that were not computed.

Opportunity funnel:

`scheduled -> valid -> actionable -> executed`

must be explicit.

## 8. C12 reusable state

Retain RB019 as:

`DIRECT_STABLECOIN_PARITY_STRESS_STATE`

Preferred roles:

- risk/collateral warning;
- R2 regime state;
- R3 veto;
- R5 execution context.

No C12 strategy reopening.

## 9. C13+ gate

Do not create C13+ while C11 remains structurally alive and the fresh v2 direction program is unresolved.

## 10. Immediate next action

Perform C11 fresh-chronology contamination/source audit.

Then freeze:

1. Selection/Calibration chronology;
2. untouched Confirmation chronology;
3. residual-headroom gates;
4. direction/opportunity-retention gates.

Only then return to VPS outcome runs.
