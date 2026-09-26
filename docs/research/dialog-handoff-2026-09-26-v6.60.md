# SC001 / B15-P1 — dialog handoff v6.60 — 2026-09-26

Current state:

`B15P1_STAGE_E_W1_OFFLINE_SELFTEST_SEALED_AWAITING_APPROVAL`

W0 real-data pipeline is PASS. Collector remains healthy, operationally frozen and running.

W1 window:
`2026-09-27 .. 2026-10-03` inclusive.

Earliest real W1 census:
`after 2026-10-04T00:00:00Z`.

W1 implementation:
- census SHA `5386182a73eb6e0561eb3670223168d3e1ebe7d11640ee9d67ce753569de4aaf`;
- analyzer SHA `da4a218e7b624775e44e8403a1acf6ee1bff581ec1a7ddaa59eb42fd0f2330ce`;
- harness SHA `061ebfa96db2728e44c71473cc70ede06c0c764c59533fadba0fce8ac59358bc`.

Exact sealed Runner bundle:
- ID: `bundle_20260926T174651Z_681d463a`
- SHA256: `9a06452b4ef5b924cdb21fa48a66a0602632167ce4bbae97f51342d4e690d6eb`
- approval code: `BM-9A06452B4EF5`
- inputs: none
- files: 7
- bytes: 77216

Expected PASS:
`B15P1_STAGE_E_W1_OFFLINE_SELFTEST_PASS`

This is synthetic/offline only. No real dataset, prices, PnL, credentials, network or collector mutation.

After PASS, prepare the future read-only W1 input-census bundle, but do not run it before the 7 complete UTC-day window is finished and the exact real-data Runner approval boundary is satisfied.
