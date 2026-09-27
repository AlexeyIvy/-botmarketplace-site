# SC001 parallel research — dialog handoff v6.77 — 2026-09-27

Current:
- B15-P1 W1 accumulation continues.
- B14-A remains DEFER_DATA.
- B13-C S0 source-only sample gate passed decisively.

Real B13-C event-only census:
- job `job_20260927T065951Z_3326eb04`;
- 32,381 unique events;
- 1,905 eligible frozen clusters;
- required price archives = 76;
- prices/returns still CLOSED.

Exact census result:
`docs/research/sc001-b13c-s0-real-event-only-cluster-census-result-v0.1.json`

Required Sep26 archives now appear on Bybit for all eight symbols that need that date.

Next script:
`research/sc001/sc001_b13c_s0_price_archive_metadata_preflight_v0_1.py`

SHA:
`4ba2c03f060c3b009a1090d52fd394dbab5829f103a4a01328a75cdaf9bd5039`

This is HEAD-only over the exact 76 archive URLs. It downloads no price body and calculates no return.

Research Runner cannot do the HEAD step because its network is disabled by design. Run this script on the VPS under the normal networked host environment, then review exact total bytes before designing the streaming download/schema-qualification stage.
