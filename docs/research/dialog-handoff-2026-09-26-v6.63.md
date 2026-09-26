# SC001 / B14-A parallel branch — dialog handoff v6.63 — 2026-09-26

B15-P1 continues unchanged in W1 accumulation.

Parallel branch now active:

`B14A_P0_FROZEN_PROSPECTIVE_HEADROOM_READOUT_PREPARED`

Frozen P0 event occurred on 2026-09-25. Readout rules were fixed beforehand:
- T0 07:30:00Z;
- BTC-USD-260925 vs BTC-USD-SWAP;
- ETH-USD-260925 vs ETH-USD-SWAP;
- earliest coactive second among five frozen seconds;
- no carry-forward/interpolation;
- chronologically last captured trade per leg in selected second;
- 50 bps hurdle.

Readout analyzer:
`research/sc001/sc001_b14a_p0_headroom_readout_v0_1.py`

SHA256:
`919c0d75e3459c0039f63915fd55347eb09590d22b29a10d4070bdcad5622279`

Real data path expected through Runner allowlisted `sc001_data`:
`SC001_B14A_P0_20260925/{collector_state.json,raw_trades.jsonl,connection_events.jsonl}`

Analyzer suppresses outcome calculation if COMPLETE/subscription or critical gap/restart gate fails.

Next:
commit preparation -> build/seal no-input offline self-test bundle -> exact approval -> self-test PASS -> build/seal read-only real-data P0 bundle.
