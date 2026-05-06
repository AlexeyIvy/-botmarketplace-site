# 54. Flagship Rollout — Baseline Results (DCA / MTF / SMC)

> **Status:** template ready, awaiting filled-in runs
> **Plan:** `docs/54-flagship-rollout.md`
> **Last updated:** _populate when filling in_

Companion-doc for the three remaining non-funding flagships, mirroring
`docs/53-baseline-results.md` structure but compacted into one file.
Each section gets filled in as `54-T1` (DCA), `54-T2` (MTF Scalper) and
`54-T3` (SMC Liquidity Sweep) close. Visibility flip via
`publishPreset.ts` is gated on the `Acceptance: PASS` marker per
preset.

The smoke harness itself is preset-agnostic
(`apps/api/scripts/demoSmoke.ts` — see `docs/53-baseline-results.md §2`
for invocation shape). All three sections below reuse the same
acceptance criteria as `docs/53-T3`.

---

## DCA Momentum

Status: PENDING

### Walk-forward acceptance (54-T1)

Evidence: `walkForwardRunId = …`

Notes: _populate after run_

### Demo smoke run (54-T1)

Invocation: `--preset dca-momentum --duration-min 30`.

| Field | Value |
| ----- | ----- |
| Run timestamp |  |
| Duration (min) |  |
| Final run state |  |
| Intent count |  |
| Failed intents |  |
| Error events |  |
| Acceptance | PASS \| FAIL |
| Report file | `apps/api/scripts/.smoke-output/<ts>-dca-momentum.json` |

### Visibility flip (54-T1)

Acceptance: PENDING

Flip log: _populate after `publishPreset.ts --slug dca-momentum --visibility PUBLIC`_

---

## MTF Scalper

Status: PENDING

### Walk-forward acceptance (54-T2)

Evidence: `walkForwardRunId = …`

Notes: _populate after run_

### Demo smoke run (54-T2)

Invocation: `--preset mtf-scalper --duration-min 30`.

| Field | Value |
| ----- | ----- |
| Run timestamp |  |
| Duration (min) |  |
| Final run state |  |
| Intent count |  |
| Failed intents |  |
| Error events |  |
| Acceptance | PASS \| FAIL |
| Report file | `apps/api/scripts/.smoke-output/<ts>-mtf-scalper.json` |

### Visibility flip (54-T2)

Acceptance: PENDING

Flip log: _populate after `publishPreset.ts --slug mtf-scalper --visibility PUBLIC`_

---

## SMC Liquidity Sweep

Status: PENDING

### Walk-forward acceptance (54-T3)

Evidence: `walkForwardRunId = …`

Notes: _populate after run_

### Demo smoke run (54-T3)

Invocation: `--preset smc-liquidity-sweep --duration-min 30`.

| Field | Value |
| ----- | ----- |
| Run timestamp |  |
| Duration (min) |  |
| Final run state |  |
| Intent count |  |
| Failed intents |  |
| Error events |  |
| Acceptance | PASS \| FAIL |
| Report file | `apps/api/scripts/.smoke-output/<ts>-smc-liquidity-sweep.json` |

### Visibility flip (54-T3)

Acceptance: PENDING

Flip log: _populate after `publishPreset.ts --slug smc-liquidity-sweep --visibility PUBLIC`_

---

## Final decision

Decision: PENDING

Rationale: _populate when all three flagships PASS — feeds into
`docs/54-go-no-go-gate.md §1` for the consolidated live gate_
