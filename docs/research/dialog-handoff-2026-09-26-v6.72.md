# SC001 parallel research — dialog handoff v6.72 — 2026-09-26

Current:
- B15-P1 W1 accumulation continues.
- B14-A P0 = DEFER_DATA; root cause = invalid OKX WS request-id grammar.
- B13-C protected source census PASS with 32,381 events over 7.596 days.

B13-C first outcome-bearing architecture is now frozen before price access:

`docs/research/sc001-b13c-s0-simple-post-liquidation-reversal-sentinel-protocol-v0.1.md`

Key S0:
- all 12 symbols;
- no size threshold;
- >=3 distinct-fingerprint pure-side events per cluster;
- 5s inter-event cluster gap;
- gap censoring;
- 1s post-cluster entry delay;
- 30s reversal horizon;
- 30 bps gross median headroom gate;
- 55% positive-cluster share;
- 4/6 positive complete-day medians;
- >=100 valid clusters;
- no winner-symbol ranking/rescue tuning.

Official Bybit public historical trade archives exist for all 12 symbol directories, but archive date freshness differs. Next is metadata/schema qualification only; do not calculate returns until every required frozen source file is available and hashed.
