# SC001 / B14-A parallel branch — dialog handoff v6.65 — 2026-09-26

Current state:

`B14A_P0_READOUT_SELFTEST_PASS_REAL_DATA_BUNDLE_PREPARATION`

Self-test:
- job `job_20260926T201402Z_d6253469`
- status `B14A_P0_READOUT_V01_SELF_TEST_PASS`
- exit 0
- package integrity PASS
- stderr empty

Real-data bootstrap:
`research/sc001/sc001_b14a_p0_real_data_readout_bootstrap_v0_1.py`

SHA256:
`99e508d3db6eeb486a19f9b11306eb172891e7f3334e1552079e3a48739dc3b3`

Only three read-only B14-A P0 input files will be materialized from `sc001_data`.

Next: commit, build/seal exact real-data bundle, then stop at fresh Runner approval boundary before opening the prospective P0 outcome.
