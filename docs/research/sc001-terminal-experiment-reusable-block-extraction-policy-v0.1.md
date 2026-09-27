# SC001 — Terminal Experiment Reusable-Block Extraction Policy v0.1

Date: 2026-09-27
Status: **BINDING POSTMORTEM REQUIREMENT**
Scope: `SCALPING RESEARCH / SC001`

## 1. Principle

A strategy verdict and a market-behavior verdict are not the same thing.

A strategy may be terminally rejected because:
- gross effect is too small;
- cost burden is too high;
- event frequency is too low;
- execution is structurally inaccessible;
- source/sample breadth is insufficient;
- latency/capital-lock/counterparty risk dominates.

That does **not** imply every measurement, state definition, event clock, normalization rule, or directional association inside the strategy is useless.

Therefore every terminal/reject/defer postmortem must include an explicit reusable-block review.

## 2. Mandatory postmortem outputs

For every closed experiment, answer separately:

1. **What exact architecture failed?**
2. **Why did it fail?**
   - source/data quality;
   - sample scarcity;
   - directional sign;
   - economic magnitude;
   - costs/fills;
   - execution/latency;
   - risk/capital lock;
   - other frozen gate.
3. **Which components remain empirically valid?**
4. **What role could each surviving component play?**
5. **What claims are forbidden?**
6. **What fresh evidence would be required for reuse?**

## 3. Reusable roles

Use the existing SC001 roles:

- R1 core signal;
- R2 state/regime;
- R3 filter/veto/confirmation;
- R4 sizing/risk;
- R5 execution/timing;
- R6 reference/normalization.

A block may be useful in R2-R6 even when its parent strategy fails as R1.

## 4. Evidence classes

Existing registry evidence classes remain valid.

Add:

`WEAK_BROAD_PROSPECTIVE_DIRECTIONAL_STATE`

Definition:
- directional association observed on protected/prospective evidence;
- breadth is nontrivial across time or sample;
- economic magnitude is insufficient for the tested standalone architecture;
- no claim of standalone tradability.

## 5. Promotion rule

A failed-strategy component may enter the reusable-block registry only when at least one is true:

- measurement/reference semantics were source-qualified;
- a frozen market state/event definition occurred with meaningful breadth;
- a frozen directional association survived sign/breadth checks even though economic headroom failed;
- an execution/risk relationship was directly observed;
- negative structural evidence is useful as a veto or feasibility boundary.

Do not register a block merely because it sounds economically plausible.

## 6. Anti-overfitting rule

A reusable block must preserve the exact evidence scope that created it.

After a parent strategy fails, do not create a "useful block" by:
- searching new thresholds;
- searching new horizons;
- selecting winning symbols;
- selecting only extreme events;
- changing sign;
- adding indicators to the same interval.

Such a block is contaminated post-outcome tuning.

A successor architecture may use the block only when:
- the new role is defined before new outcome evidence;
- interaction count is frozen;
- fresh evidence is collected or assigned;
- the parent interval is not reused as promotional confirmation.

## 7. Registry discipline

The canonical registry is append-only:

`docs/research/sc001-reusable-market-building-blocks-registry-*.md`

A terminal experiment is not considered fully closed until:
- its terminal strategy state is recorded; and
- reusable-block extraction is completed with either:
  - one or more RB entries; or
  - explicit `NO_REUSABLE_BLOCK_IDENTIFIED`.

## 8. Portfolio-level lesson

Research efficiency comes from accumulating:
- rejected architectures;
- validated data semantics;
- reusable market states;
- execution constraints;
- structural impossibility results.

The long-run objective is not a sequence of isolated strategy verdicts. It is a progressively better library of market mechanisms and implementation primitives from which future strategies can be designed prospectively.
