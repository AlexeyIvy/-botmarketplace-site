# SC001 parallel research — dialog handoff v6.95 — 2026-09-27

Current:
- B15-P1 W1 accumulation continues.
- B14-A P0 remains DEFER_DATA.
- B13-C S0 terminal REJECT; RB021 retained for future prospective use.
- reusable-block extraction is now mandatory after every terminal experiment.
- B14-B persistent multi-settlement funding carry is frozen before fresh 2026 funding-value access.

B14-B architecture:
- fresh window Jul1-Sep27 2026 exclusive end;
- 12 frozen assets;
- 3 same-sign matched funding differentials;
- no magnitude threshold;
- fixed 7-day hold;
- all venue funding cashflows in hold counted;
- non-overlapping cycles;
- 40 bps structural burden;
- 50 bps gross headroom hurdle.

Exact sealed offline self-test:
- ID `bundle_20260927T091925Z_389f482b`
- SHA `563919504e09b4c2ee866f45a71cabe776c72d40fbd5c36d0f46c8df5418aad4`
- approval `BM-563919504E09`
- inputs none
- files 7
- bytes 37,021

Expected PASS:
`B14B_PERSISTENT_CARRY_V01_SELF_TEST_PASS`

After PASS, prepare a separate approval boundary for the networked fresh funding-value screen.
