# SC001 Current Roadmap and Stop Rules v4.91

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B13-B EXACT 7-EVENT SET + S0 HEADROOM IMPLEMENTATION FROZEN**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.90.md`

## 1. Binding prior states

C11:
`C11_TERMINAL_REJECT_DIRECTION_CAPTURE`

C12:
`C12_S0_REJECT_PARITY_REVERSION`

B13-A:
`B13A_REJECT_STRUCTURAL`

B13-B remains:
`B13-B_NOT_YET_C13`

## 2. Exact historical launch set frozen

Binding:

`docs/research/sc001-b13b-exact-7-event-launch-set-freeze-v0.1.md`

Canonical D0 SHA256:

`82012a614a1f5652c483df87fb70f811f66b56e9035e41f8d146f7accd81e2f6`

Historical role:

`NONPROMOTIONAL_SURVIVOR_CENSORED_STRUCTURAL_CALIBRATION`

## 3. S0 protocol

Binding:

`docs/research/sc001-b13b-s0-launch-dislocation-headroom-sentinel-v0.1.md`

Purpose:

initial launch-dislocation magnitude only.

No convergence.

No strategy PnL.

## 4. Frozen clock

`STRICT_COACTIVE_1S_NO_CARRY_FORWARD`

Search only first five one-second launch buckets.

Use earliest second with real trades on both venues.

No carry-forward/interpolation.

## 5. Frozen S0 metric

`abs_launch_basis_bps = 10000 * abs(ln(price_okx / price_bybit))`

Structural burden:

`40 bps`

Headroom threshold:

`50 bps`

## 6. Sample gate

Require:

- >=6/7 coactive-valid events;
- >=3 launch months represented among valid events.

Otherwise:

`B13B_S0_DEFER_SAMPLE`

## 7. Headroom gate

SURVIVE only if:

- >=4/7 scheduled events have abs launch basis >=50 bps;
- median valid abs launch basis >=50 bps;
- qualifying >=50 bps events span >=3 launch months.

SURVIVE:

`B13B_S0_LAUNCH_DISLOCATION_HEADROOM_SURVIVE`

REJECT:

`B13B_S0_REJECT_LAUNCH_DISLOCATION_HEADROOM`

## 8. Implementation

Runner:

`research/sc001/sc001_b13b_s0_launch_dislocation_headroom_v0_1.py`

Freeze:

`docs/research/sc001-b13b-s0-implementation-freeze-v0.1.json`

Contamination registry:

`docs/research/sc001-contamination-registry-v0.24.json`

## 9. Hard boundaries

This run may calculate only the first-coactive-second absolute launch basis.

It may not calculate:

- later convergence;
- relative return;
- strategy signal;
- execution;
- PnL;
- promotional alpha.

No candidate ID assignment.

## 10. Consequence

If REJECT:

B13-B closes structurally; no convergence study.

If SURVIVE:

do not assign C13 automatically.

Next step is a separately frozen convergence/mechanism review plus prospective-event architecture.

## 11. Immediate next action

Run exact seven-event B13-B S0 once.

Do not interpret partial event output.
