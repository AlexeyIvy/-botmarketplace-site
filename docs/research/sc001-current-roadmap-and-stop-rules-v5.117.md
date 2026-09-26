# SC001 Current Roadmap and Stop Rules v5.117

Date: 2026-09-26  
Status: **B15-P1 W1 accumulation continues / B14-A P0 readout self-test PASS / real-data readout prepared**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.116.md`

## B14-A offline validation

Job:
`job_20260926T201402Z_d6253469`

Result:
`B14A_P0_READOUT_V01_SELF_TEST_PASS`

Observed:
- exit code = 0;
- package integrity = PASS;
- stderr empty.

## Real-data readout

Prepared bootstrap:
`research/sc001/sc001_b14a_p0_real_data_readout_bootstrap_v0_1.py`

SHA256:
`99e508d3db6eeb486a19f9b11306eb172891e7f3334e1552079e3a48739dc3b3`

Inputs are restricted to:
- `SC001_B14A_P0_20260925/collector_state.json`
- `SC001_B14A_P0_20260925/raw_trades.jsonl`
- `SC001_B14A_P0_20260925/connection_events.jsonl`

The readout preserves the frozen P0 rule:
- T0 = 2026-09-25T07:30:00Z;
- first coactive second among five frozen seconds;
- no carry-forward/interpolation;
- last captured trade per leg in selected second;
- 50 bps hurdle;
- COMPLETE/subscription/gap fail-closed gate.

## Firewalls

No:
- alternate T0/window/expiry search;
- threshold tuning;
- convergence analysis;
- settlePx analysis;
- execution model;
- PnL.

## Next state

`BUILD_AND_SEAL_B14A_P0_REAL_DATA_READOUT_BUNDLE`
