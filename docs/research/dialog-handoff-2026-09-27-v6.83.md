# SC001 parallel research — dialog handoff v6.83 — 2026-09-27

B13-C extractor v0.1 self-test did not enter research code.

Job:
`job_20260927T075438Z_85b2eb56`

Cause:
mandatory `--mode` conflicted with Runner v1.0.5 launcher contract.

No price body/network/return/PnL was opened.

Corrected entrypoint:
`research/sc001/sc001_b13c_s0_streaming_price_anchor_extractor_v0_1_1.py`

SHA:
`18621a8540d9b2e70f01bf34a0ee103e0eb1dc10fceec33e69a2572d827f1ee0`

Delta is launcher compatibility only. Research semantics remain frozen.

Next:
commit -> seal new v0.1.1 offline self-test bundle -> new explicit approval -> run.
