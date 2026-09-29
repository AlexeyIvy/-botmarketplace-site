# SC001 B15-P2 P0 — Official Bybit Source Coverage Review v0.1

Date: 2026-09-29
Status: **SOURCE_COVERAGE_ROOT_CAUSE_CLASSIFIED / NO P0 RESCUE**

Canonical P0 result:
`docs/research/sc001-b15p2-p0-basis-convergence-result-v0.1.json`

Canonical result SHA256:
`e2554fcf95992e64d58ffcdac85faf68edff45f5320a596a5249256176bd13a3`

Frozen implementation:
`research/sc001/sc001_b15p2_p0_basis_convergence_v0_1.py`

Implementation SHA256:
`dc52b2fb4914ea29bc6bc85a9cfc8aa27f327d8dd160e6c4aa9feeab5e328945`

## Scope

This review is source-semantics only. It does not rerun P0, does not change the frozen implementation, does not inspect a new outcome horizon, and does not authorize returns, PnL, L1/L2, individual trades, funding, mark/premium/spot, external venues or trading.

No new Bybit market-data request was required for this review. The classification below uses the already-canonical P0 source ledger plus the frozen implementation and official Bybit API field semantics.

## Official-source semantics

The frozen P0 contract source is the official Bybit V5 Market API endpoint:

`GET /v5/market/kline`

with:
- category = linear;
- interval = 1;
- exact frozen event symbol;
- exact registered candle start time.

Official Bybit documentation defines:
- list[0] = candle startTime;
- list[4] = closePrice;
- list[5] = trade volume;
- list[6] = turnover.

Reference:
https://bybit-exchange.github.io/docs/v5/market/kline

The frozen implementation first requires exactly one row whose startTime equals the registered minute. Only after that exact row exists does it parse volume and turnover. `CONTRACT_ZERO_ACTIVITY` is raised only when the exact row was found but reported volume <= 0 or turnover <= 0.

Therefore `CONTRACT_ZERO_ACTIVITY` is not an `EXACT_CANDLE_COUNT:0` archive-missing condition. It is an exact-candle-present, zero-reported-trade-activity condition under the registered source rule.

## Source-coverage census from the completed P0

Registered affected-contract snapshots:
- 94 events × 3 exact minutes = 282 snapshots.

Snapshot-level source result:
- 156 / 282 exact snapshots passed the positive volume+turnover rule;
- 125 / 282 returned an exact candle but failed as `CONTRACT_ZERO_ACTIVITY`;
- 1 / 282 failed with Bybit `retCode 10016` for LISTAUSDT at T-55.

Zero-activity count by registered offset:
- T-55: 45;
- T-30: 48;
- T-5: 32.

Event-level completeness:
- 23 / 94 events had all three registered snapshots eligible;
- 71 / 94 were ineligible;
- among the 71 ineligible events:
  - 32 failed at exactly one registered snapshot;
  - 23 failed at exactly two registered snapshots;
  - 16 failed at all three registered snapshots.

Cluster/month coverage remained below the frozen source gate:
- 18 / 37 delivery clusters eligible;
- 8 / 9 months represented;
- 2026-09 had no eligible event.

## Root-cause classification

Primary failure class:

`EXACT_1M_TRADE_ACTIVITY_SPARSITY_AT_REGISTERED_EVENT_TIMES`

Supporting reasons:
1. 125 of 126 registered snapshot errors are zero-activity failures after exact candle resolution.
2. Only one snapshot is a distinct API/service error.
3. The failure is distributed across all three registered offsets rather than being isolated to a single parser branch.
4. The existing implementation and exact-time matching logic remain internally consistent with the preregistration.

This does not prove every zero is economically identical, but it is sufficient to reject the interpretation that the P0 source gate mainly failed because the historical endpoint lacked the requested exact candles.

## Scientific consequence

The current P0 remains frozen as:

`DEFER_SOURCE_COVERAGE`

The zero-activity rule must not be relaxed and the same 94-event price evidence must not be rerun as a rescue. A zero-volume exact minute can represent a stale/non-executable last-trade reference; treating it as automatically valid after outcome access would weaken the original execution-realism safeguard.

No alternate venue, third-party archive, mark price, premium index, spot proxy, reconstructed index, nearest candle, interpolation or post-hoc horizon/symbol/threshold search is authorized.

## Successor-design requirement

A scientifically defensible successor may address source sparsity only if all of the following are satisfied before new successor outcome access:

1. It is a separate preregistered design, not a mutation of P0.
2. It uses a fresh/untouched or prospective event set for any confirmatory price outcome.
3. Its observation/staleness/activity rule is fixed before reading successor prices or basis.
4. Any aggregation interval or admissible staleness bound is justified from market-data semantics and mechanism timescale, not selected by best historical outcome.
5. Source-coverage diagnostics are kept separate from price-effect inference.
6. P0's 94-event outcome remains contamination-marked and is never reused as confirmatory evidence for the changed sampling rule.

## Three-role terminal review

### Financial expert / trader

The main operational finding is not that the Bybit contract source disappears, but that many affected contracts are too thin for an exact-minute positive-trade requirement at all three snapshots. That is itself strategy-relevant: any later executable design must treat stale last-trade references as a real liquidity risk, not merely a data-cleaning nuisance.

### Programmer-trader / research engineering

The P0 fetch path is behaving as designed. Exact candle identity is checked before the activity gate, so 125 zero-activity errors are semantically distinct from missing candles. No P0 code change is warranted. The next implementation, if any, must be a new successor artifact with its own freeze.

### Mathematician / statistician

The source gate failed too strongly to support inference from the surviving subset. Because outcome access has already occurred, source-rule adaptation on these same 94 observations cannot restore confirmatory status. A fresh holdout/prospective sample is required for a successor claim.

## Decision

Review verdict:

`OFFICIAL_SOURCE_PRESENT_BUT_EXACT_1M_ACTIVITY_COVERAGE_INSUFFICIENT`

Next allowed action:

`DESIGN_FRESH_B15P2_SOURCE_ROBUST_SUCCESSOR_PREREGISTRATION`

No new outcome-bearing run is authorized by this review.
