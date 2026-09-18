# SC001 Current Roadmap and Stop Rules v4.70

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — C12-S0 TERMINAL RARE/CLUSTERED REJECT / C11 DIRECTIONAL DESIGN NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.69.md`

## 1. Binding terminal strategy states

All prior terminal states remain immutable.

C12-S0 is now terminal:

`C12_S0_REJECT_PARITY_REVERSION`

No C12 rescue tuning is authorized.

## 2. C12-S0 result

Data:

- target days with trades = 181/181;
- target months = 6/6;
- failed data gates = none.

Episodes:

- total = 3;
- evaluable = 3;
- successful reversion = 2;
- episode dates = 3;
- episode months = 1.

Economics:

- success share within 30m ≈66.7%;
- median gross favorable reversion ≈25.94 bps;
- p75 ≈29.93 bps.

Failed frozen gates:

- evaluable episodes >=12;
- episode dates >=6;
- episode months =6.

Passed frozen economic magnitude gates:

- success share >=60%;
- median >=15 bps;
- p75 >=20 bps.

Classification:

`ECONOMICALLY_LARGE_WHEN_PRESENT_BUT_TOO_RARE_AND_REGIME_CLUSTERED`

## 3. C12 consequence

Do not:

- lower 30 bps entry threshold;
- widen 10 bps band;
- extend 30m hold;
- select successful episodes;
- select the active month;
- extend the H1 period to manufacture frequency.

No execution/PnL stage.

Binding postmortem:

`docs/research/sc001-c12-s0-parity-reversion-result-readonly-postmortem-v0.1.md`

Current feature registry:

`docs/research/sc001-feature-evidence-registry-v0.7.md`

Current reusable-block registry:

`docs/research/sc001-reusable-market-building-blocks-registry-v0.6.md`

Current landscape:

`docs/research/sc001-strategy-landscape-v0.7.md`

## 4. C11 remains the active survivor

C11-S0:

`C11_S0_EVENT_MOVE_HEADROOM_SURVIVE`

remains binding.

C11-S1:

`C11_S1_DEFER_SAMPLE`

remains unresolved due one exact zero first-impulse event.

Do not reinterpret C11-S1 as REJECT.

## 5. Current research question

For C11 the remaining question is:

`Can a prospectively defined causal direction rule leave enough post-entry continuation after the scheduled macro release?`

This is now the priority SC001 research question.

## 6. Fresh-evidence requirement

H1-2025 is contaminated for C11 directional-rule design because:

- raw move headroom was inspected;
- the one-second direction rule was run;
- the zero-impulse failure was diagnosed.

Any materially different C11 direction rule must use fresh Selection/Calibration chronology.

## 7. Next non-alpha design task

Create a C11 Direction Rule v2 feasibility protocol that:

- explicitly allows `NO_TRADE` when the chosen causal direction statistic is zero/non-actionable;
- remains independent of macro surprise values;
- does not search multiple impulse windows;
- freezes exactly one direction statistic/window;
- freezes opportunity-retention accounting;
- freezes continuation/headroom gates;
- selects a fresh chronology before price outcome.

No new directional outcome is authorized until that design is frozen.

## 8. C13+ gate

Do not open another independent base candidate while C11 remains structurally alive and unresolved.

Only if the fresh C11 direction design is structurally impossible or later fails may new base-candidate expansion resume.

## 9. Immediate next action

No VPS run required immediately.

Prepare and critically review C11 Direction Rule v2 + fresh chronology protocol before any new price-bearing test.
