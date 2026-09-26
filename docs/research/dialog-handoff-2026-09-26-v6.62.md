# SC001 / B15-P1 — dialog handoff v6.62 — 2026-09-26

Current state:

`W1_7_COMPLETE_UTC_DAY_OBSERVATION_ACCUMULATING`

Collector:
`B15P1_COLLECTOR_V014_OPERATIONAL_FREEZE`

Completed:
- W0 real-data smoke PASS;
- W1 census/analyzer offline self-test PASS.

W1 exact observation window:
`2026-09-27 .. 2026-10-03` UTC inclusive.

Earliest permitted real W1 census:
`2026-10-04T00:00:00Z`.

Future W1 census bundle is already SEALED:
- ID: `bundle_20260926T175529Z_93fa9025`
- SHA256: `1308ce4c140161618dc465672564bdc3f2409e62cf219dc6932bc7edf1891495`
- approval code: `BM-1308CE4C1401`
- inputs: 17 read-only `sc001_data` files
- files in package: 6
- bytes: 48883
- runtime: `offline-research-v1`.

Bootstrap:
`research/sc001/sc001_b15p1_stage_e_w1_real_data_census_bootstrap_v0_1.py`

Bootstrap hard-fails before 2026-10-04T00:00:00Z.

After W1 window completion:
1. obtain fresh explicit Runner approval for this exact bundle;
2. run census;
3. inspect quality/integrity and census manifest;
4. only if PASS, assemble a second exact W1 source-only analysis bundle using the manifest-derived event/fee/gap/baseline files;
5. keep price/PnL closed;
6. W1 is still not the formal 30-day opportunity-rate classification.

No action is required on VPS now. Do not restart the collector.
