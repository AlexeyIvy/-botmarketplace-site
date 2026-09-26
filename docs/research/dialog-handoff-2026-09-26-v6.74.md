# SC001 parallel research — dialog handoff v6.74 — 2026-09-26

Current:
- B15-P1 W1 accumulation continues.
- B14-A P0 remains DEFER_DATA.
- B13-C S0 is active but price outcome remains closed.

Bybit public archive availability:
- 12/12 symbols have Sep19-Sep25 files;
- Sep26 is not yet published.

Exact B13-C source-only cluster census offline-selftest bundle:
- ID: `bundle_20260926T214337Z_a25b8bff`
- SHA256: `f6500de6a30e2d97430a29ec047ea85552c284d46f7e7917a794e198f4f2361e`
- approval: `BM-F6500DE6A30E`
- inputs: none
- package files: 5
- bytes: 29732

Entrypoint:
`research/sc001/sc001_b13c_s0_source_only_cluster_census_v0_1.py`

SHA256:
`601252728e8fa7caf2d9c467d99e61296268a78879a42323725b67bac223db5b`

Expected PASS:
`B13C_S0_SOURCE_ONLY_CLUSTER_CENSUS_V01_SELF_TEST_PASS`

After PASS, build the real event-only census bundle. Price archives remain unopened until the source-only census produces the exact required file identities and those archives are available/schema-qualified.
