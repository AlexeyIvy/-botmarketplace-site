# SC001 parallel research — dialog handoff v6.78 — 2026-09-27

Current:
- B15-P1 W1 accumulation continues.
- B14-A remains DEFER_DATA.
- B13-C S0 source-only sample gate PASS with 1,905 eligible clusters.
- Exact 76 price archives HEAD-preflight PASS.
- Total compressed size = 2,633,144,445 bytes = 2.452 GiB.

Price bodies and returns remain CLOSED.

Prepared exact cluster freeze:

`research/sc001/sc001_b13c_s0_exact_cluster_freeze_v0_1.py`

SHA256:
`0f7c27e84c960d41a7dcbd1a058ba4b8b1b3b6865aabe97493a4ea810c7cb9d4`

It must reproduce the official source-only aggregate counts exactly before emitting the 1,905 cluster identities and frozen entry/exit bucket times.

After this manifest is frozen, use sequential one-file-at-a-time Bybit archive download/verification/extraction so permanent storage does not need to retain all 2.452 GiB.

Next:
commit -> seal exact event-only cluster-freeze bundle -> fresh explicit Runner approval -> persist manifest -> build streaming price-anchor extraction stage.
