# SC001 parallel research — dialog handoff v6.73 — 2026-09-26

Current:
- B15-P1 W1 accumulation continues.
- B14-A Sep25 P0 remains DEFER_DATA.
- B13-C is the active parallel strategy-research branch.

B13-C protected source census has 32,381 events over 7.596 days.

S0 reversal protocol was frozen before price access.

Official Bybit public-trade directories show all 12 symbol files for Sep19-Sep25. Sep26 is not yet published while the UTC day is still open.

To avoid blindly downloading 96 archives, a source-ingestion amendment now defines required archives as exact symbol-date files touched by already frozen eligible clusters. This changes no S0 hypothesis or threshold.

Prepared cluster census:
`research/sc001/sc001_b13c_s0_source_only_cluster_census_v0_1.py`

SHA256:
`601252728e8fa7caf2d9c467d99e61296268a78879a42323725b67bac223db5b`

Next:
1. commit preparation;
2. build/seal no-input synthetic self-test bundle;
3. require explicit Runner approval;
4. after self-test PASS, build/seal real source-only event census bundle;
5. price remains closed until archive qualification.
