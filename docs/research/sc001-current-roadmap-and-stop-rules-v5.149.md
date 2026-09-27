# SC001 Current Roadmap and Stop Rules v5.149

Date: 2026-09-27
Status: **B15-P1 W1 accumulation / B14-A P0 DEFER_DATA / B13-C S0 terminal REJECT with RB021 / B14-B terminal REJECT with RB022**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.148.md`

## B14-B exact real result

Networked VPS execution completed successfully under:

`sc001-b14b-fresh-funding-v01.service`

Terminal classification:

`B14B_REJECT_PERSISTENT_CARRY_STRUCTURAL`

Valid non-overlapping seven-day cycles:

`110`

Pooled gross funding carry:
- p25 = -2.5951 bps;
- median = +1.3863 bps;
- p75 = +3.6405 bps;
- positive cycles = 67/110 = 60.9091%.

Breadth:
- positive-median symbols = 8;
- positive-median cycle-start months = 3.

All data/sample gates passed.

Structural gates:
- median >=50 bps = **FAIL**;
- positive share >=60% = PASS;
- positive-median symbols >=6 = PASS;
- positive-median months >=2 = PASS.

## Binding interpretation

B14-B fails on economic magnitude, not source quality, sample size, or sign persistence.

Observed median is only about 2.77% of the frozen 50 bps gross-headroom hurdle.

The p75 carry is only about 3.64 bps, still far below the pre-existing 40 bps four-fill burden before any basis, margin, capital-lock or venue-risk reserve.

Therefore:
- do not open price/basis/PnL for B14-B;
- do not rescue with a different hold, threshold, confirmation count, symbol subset, or basis add-on.

## Reusable block retained

`RB022 — Persistent cross-venue funding-differential direction state v0.1`

Scoped evidence:
- 60.91% positive cycles;
- 8 positive-median symbols;
- 3 positive-median months;
- standalone economic carry rejected.

Potential future roles:
R2 / R3 / R4 / R6 only under a new prospectively frozen mechanism.

## Parallel states unchanged

B15-P1:
W1 accumulation continues under operational freeze.

B14-A:
Sep25 P0 remains DEFER_DATA because the source collector never subscribed successfully. Any retry must be future prospective after transport preflight.

B13-C:
S0 terminal/closed; RB021 retained.

## Next research rule

Do not spend more outcome budget rescuing B13-C or B14-B.

While B15-P1 accumulates and B14-A waits for another expiry, select the next independent mechanism using non-price/source/access reasoning first.

Current reserve mechanisms from the prior critical review:
- B15-P3 fixed conversion/redemption anchor — strong structural economics if operational access exists;
- B15-P2 scheduled delisting/forced-close — real forced-flow mechanism but hostile execution;
- B14-C scheduled trading-resumption dislocation — source and latency risk high.

## Next state

`SOURCE_AND_ACCESS_FEASIBILITY_REVIEW_FOR_NEXT_INDEPENDENT_MECHANISM`
