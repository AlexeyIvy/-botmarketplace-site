# SC001 / B14-A parallel branch — dialog handoff v6.67 — 2026-09-26

Current state:

`B14A_P0_REAL_DATA_READOUT_INPUT_MATERIALIZATION_DIAGNOSTIC`

The approved real-data bundle did not reach the Python entrypoint.

Registered job:
`job_20260926T201857Z_e1963e30`

Observed:
- run_bundle returned INVALID_ARGUMENT;
- unit ended success/inactive;
- effective_status null;
- stdout/stderr empty;
- no artifacts.

No B14-A price outcome was opened.

Confirmed B14-A systemd data root:
`/home/botmarket/sc001_data/SC001_B14A_P0_20260925`.

Next diagnostic is deliberately state-only:
`SC001_B14A_P0_20260925/collector_state.json`

Probe:
`research/sc001/sc001_b14a_p0_state_only_diagnostic_v0_1.py`

SHA:
`cef2e96f5b5dea8b61c3a5b9e8743a9a63bb5555cb9169a31a210aa3f97c3bcd`

It reads no raw trades/prices and cannot calculate P0 headroom. Use it only to distinguish collector/data absence from a larger-file materialization issue.
