# SC001 Current Roadmap and Stop Rules v5.119

Date: 2026-09-26  
Status: **B15-P1 W1 accumulation continues / B14-A P0 real-data readout blocked at Runner input materialization / state-only diagnostic next**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.118.md`

## B14-A real-data run attempt

Approved exact bundle:

`bundle_20260926T201527Z_e2422a4a`

Run key:

`B14A_P0_REALDATA_READOUT_01`

Runner registered:

`job_20260926T201857Z_e1963e30`

but `run_bundle` returned:

`INVALID_ARGUMENT`

Observed job state:
- systemd result = success;
- unit inactive/dead;
- effective_status = null;
- stdout = empty;
- stderr = empty;
- artifacts = none.

Therefore the Python readout entrypoint did not produce an outcome.

The B14-A prospective result remains unopened.

## Confirmed path semantics

The systemd service writes B14-A to:

`/home/botmarket/sc001_data/SC001_B14A_P0_20260925`

which is under the same `sc001_data` family used successfully by Runner for B15.

The remaining likely materialization causes are:
1. one or more declared files do not exist;
2. a declared file, most plausibly `raw_trades.jsonl`, violates a Runner input/materialization constraint.

## Minimal diagnostic

Next use a separate immutable bundle with only:

`SC001_B14A_P0_20260925/collector_state.json`

No raw trade file and no price data.

Diagnostic code:

`research/sc001/sc001_b14a_p0_state_only_diagnostic_v0_1.py`

SHA256:

`cef2e96f5b5dea8b61c3a5b9e8743a9a63bb5555cb9169a31a210aa3f97c3bcd`

The state-only probe may report operational counters/status only. It must not calculate the P0 outcome.

## Stop rules

- Do not alter the 50 bps rule.
- Do not open alternative data/windows.
- Do not interpret the materialization failure as strategy evidence.
- Do not rerun the three-input bundle until the input-level cause is understood.

## Next state

`SEAL_B14A_P0_STATE_ONLY_DIAGNOSTIC_BUNDLE`
