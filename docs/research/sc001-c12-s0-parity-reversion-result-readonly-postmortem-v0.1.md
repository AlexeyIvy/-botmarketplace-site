# SC001 — C12-S0 Parity Reversion Result & Read-Only Postmortem v0.1

Date: 2026-09-18
Status: **C12_S0_REJECT_PARITY_REVERSION — DATA COMPLETE / REVERSION MAGNITUDE ADEQUATE / OPPORTUNITY TOO RARE AND CLUSTERED**
Scope: `SCALPING RESEARCH / SC001`

## 1. Execution integrity

Exact terminal state:

`C12_S0_REJECT_PARITY_REVERSION`

Technical completion:

- exit code: `0`;
- target days with trades: `181 / 181`;
- target months with trades: `6 / 6`;
- failed data gates: none;
- fill/queue/PnL: not calculated;
- promotional alpha: not accessed.

Therefore the result is not a data-quality failure.

## 2. Frozen episode result

Observed:

- total episodes: `3`;
- evaluable episodes: `3`;
- successful reversion episodes: `2`;
- distinct episode UTC dates: `3`;
- distinct episode UTC months: `1`;
- success share within 30 minutes: `2/3 = 0.6667`;
- median gross favorable reversion: about `25.94 bps`;
- p75 gross favorable reversion: about `29.93 bps`.

Frozen structural reference:

- entry threshold: 30 bps;
- parity re-arm/exit band: 10 bps;
- max hold: 30 minutes;
- structural burden reference: 15 bps.

## 3. Which gates failed

Failed:

- `evaluable_episodes_gte12`;
- `episode_dates_gte6`;
- `episode_months_eq6`.

Passed:

- data-day coverage;
- six-month data coverage;
- success share >=60%;
- median gross reversion >=15 bps;
- p75 gross reversion >=20 bps.

## 4. Economic interpretation

Primary failure class:

`ECONOMICALLY_LARGE_WHEN_PRESENT_BUT_TOO_RARE_AND_REGIME_CLUSTERED`

This is materially different from C7/C8/C10-style headroom failure.

C12 did **not** fail because reversion magnitude was too small.

On the three frozen H1 episodes:

- two reverted to the <=10 bps parity band within 30 minutes;
- gross favorable reversion magnitude exceeded the 15 bps structural burden in median and p75 terms.

However:

- only three episodes existed in 181 days;
- they occurred on only three dates;
- all occurred within a single month.

Therefore the exact C12 strategy lacks opportunity breadth and regime robustness.

## 5. No-rescue rule

Do not:

- lower the 30 bps entry threshold;
- widen the 10 bps parity band;
- extend the 30-minute hold;
- select only the successful two episodes;
- choose the active month as a preferred regime;
- add famous depeg dates;
- extend the H1 calibration window post hoc to increase event count;
- choose one deviation sign.

Any rare-event stablecoin-stress strategy must be a new prospective candidate with fresh chronology.

## 6. Feature-level interpretation

C12 produces a useful reusable state:

`DIRECT_STABLECOIN_CROSS_PARITY_STRESS`

Characteristics in H1-2025:

- very rare;
- strongly regime-clustered;
- economically large when present;
- often mean-reverting toward parity within 30 minutes in the tiny observed sample.

Appropriate future roles:

- R2 risk/regime state;
- R3 veto / capital-preservation state;
- R5 execution/collateral warning;
- rare-event trigger only under a separately designed candidate with fresh evidence.

Not appropriate:

- ordinary high-frequency standalone base opportunity under current H1 evidence.

## 7. Statistical caution

Three episodes are far too few for a stable estimate of:

- 66.7% success probability;
- median/p75 economic effect;
- sign symmetry;
- regime persistence.

The magnitude evidence is descriptive and useful for design, not confirmatory.

The strongest robust conclusion is frequency/breadth:

`3 episodes / 181 days / 1 month`

which is decisively below the frozen opportunity-breadth requirements.

## 8. Candidate disposition

C12-S0:

`REJECT_PARITY_REVERSION`

No execution-model stage.
No PnL stage.
No promotional confirmation.

Retain the parity-stress state in the feature/building-block registries.

## 9. Next project consequence

C11 remains the only new-generation base mechanism with demonstrated broad raw headroom.

C11 directional extraction remains unresolved due the zero first-impulse event under S1 v0.1.

The next project step should therefore be:

1. preserve C12 as rare-event feature evidence;
2. design a fresh, prospectively defined C11 direction rule on fresh evidence rather than rescue S1 on H1;
3. keep C11-S0 headroom result read-only and binding.
