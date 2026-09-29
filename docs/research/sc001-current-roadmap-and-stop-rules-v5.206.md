# SC001 Current Roadmap and Stop Rules v5.206

Date: 2026-09-29
Status: **B15-P2 P0 SOURCE-COVERAGE REVIEW COMPLETE / FRESH SUCCESSOR DESIGN REQUIRED**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.205.md`

## Frozen P0 state

Canonical verdict remains:

`DEFER_SOURCE_COVERAGE`

Canonical result:
`docs/research/sc001-b15p2-p0-basis-convergence-result-v0.1.json`

SHA256:
`e2554fcf95992e64d58ffcdac85faf68edff45f5320a596a5249256176bd13a3`

The completed P0 must not be modified or rerun as a rescue.

## Official-source coverage review

Canonical review:
`docs/research/sc001-b15p2-p0-official-source-coverage-review-v0.1.md`

SHA256:
`8e07fc018e908341d0ca37c5ba6a7bc60491d8ad972187deb798f79594ddef22`

Review verdict:

`OFFICIAL_SOURCE_PRESENT_BUT_EXACT_1M_ACTIVITY_COVERAGE_INSUFFICIENT`

The dominant source failure is not missing exact candles. The frozen implementation raises `CONTRACT_ZERO_ACTIVITY` only after exact candle identity is established.

Observed source-only census from the canonical P0 ledger:
- 282 registered affected-contract snapshots;
- 156 passed exact-minute positive volume+turnover;
- 125 exact candles failed the activity rule with zero reported volume/turnover;
- 1 Bybit retCode 10016 service error;
- zero-activity failures by offset: T-55 = 45, T-30 = 48, T-5 = 32;
- 23 / 94 events passed all three source checks;
- 18 / 37 delivery clusters eligible;
- 8 / 9 months represented.

## Interpretation

The frozen exact-1m activity condition is too sparse for confirmatory inference on this event universe.

This is not permission to treat zero-volume candles as valid after seeing outcomes. The original activity rule remains a valid stale-price/executability safeguard for P0.

## Contamination / stop rules

Still forbidden on the frozen 94-event P0 evidence:
- changing the zero-activity rule;
- nearest-candle substitution;
- interpolation / forward fill / backward fill;
- alternate venue or third-party archive;
- mark, premium or spot substitution;
- horizon search;
- symbol selection;
- threshold tuning;
- returns or PnL;
- L1/L2 or individual trades;
- trading.

Any changed sampling or activity rule is a new successor design and cannot regain confirmatory status on the same 94-event price outcomes.

## Next allowed action

`DESIGN_FRESH_B15P2_SOURCE_ROBUST_SUCCESSOR_PREREGISTRATION`

Requirements before any new successor outcome access:
1. separate successor identifier and preregistration;
2. fresh/untouched or prospective event set for confirmatory evidence;
3. official Bybit source semantics preserved unless a new source is explicitly preregistered before access;
4. fixed observation/staleness/activity rule before successor price or basis access;
5. no selection of aggregation interval or staleness bound by historical outcome;
6. source-coverage feasibility and price-effect inference kept as separate gates.

No new outcome-bearing run is authorized by this roadmap version.
