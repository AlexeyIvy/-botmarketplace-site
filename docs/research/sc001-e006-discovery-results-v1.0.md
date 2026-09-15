# SC001-E006 — Discovery Results v1.0

Date: 2026-09-15  
Status: **TERMINAL `E006_DISCOVERY_FAIL`**

Parent protocol:

`docs/research/sc001-e006-spot-perp-basis-convergence-executable-protocol-v1.0.md`

Primary identifier:

`E006_POSBASIS_G10_VWAP10_LB6H_TRIG50_EXIT10_LAT500_H30_CAP4`

## 1. Terminal result

Frozen DEV-DISCOVERY returned:

`E006_DISCOVERY_FAIL`

Confirmation and paired-L2 remain closed. No rescue tuning is authorized.

## 2. Primary observed facts

On the frozen 2024-03-01..20 Discovery interval:

- completed paired trades: `1` versus frozen minimum `20`;
- active days: `1` versus frozen minimum `10`;
- pooled mean gross edge: approximately `+27.405 bps` versus `>=40 bps`;
- 10% trimmed mean: approximately `+27.405 bps` versus `>=35 bps`;
- pooled median: approximately `+27.405 bps`, which passed the `>=25 bps` median gate;
- median active-day mean: approximately `+27.405 bps` versus `>=30 bps`;
- positive active-day share: `1.0`, but from only one active day;
- day-block bootstrap lower bound: approximately `+27.405 bps`, but from only one active day;
- top-1 and top-3 day concentration: `1.0`, failing diversification gates by construction;
- 1,000 ms latency mean/trimmed mean: approximately `+27.893 bps`, below frozen `35/30 bps` hurdles;
- 2,000 ms latency mean: approximately `+25.476 bps`, below frozen `30 bps` hurdle;
- 2,000 ms latency trimmed mean: approximately `+25.476 bps`, passing the `>=25 bps` trimmed hurdle;
- daily cap and one-pair concurrency invariants passed.

Total failed frozen gates: `10`.

## 3. Interpretation

This is not the same failure mode as E004.

E006 did **not** demonstrate near-zero gross economics. The sole completed pair was positive and of order tens of bps. However:

1. the event definition was far too rare on the frozen Discovery interval to support inference or deployment;
2. the single observed pair did not reach the frozen mean/trimmed/median-day economics hurdle;
3. concentration is maximal because all evidence comes from one day;
4. latency-stress economics also remain below the required promotion margin;
5. approximately 27 bps gross leaves only limited residual headroom above the roughly 20 bps four-taker-fill regular-user fee reference before spread, depth, legging and funding/borrow effects.

Therefore E006 is classified as:

**event-scarcity + insufficient-economics-headroom failure**, not a zero-edge mechanism failure.

## 4. Stop rule

Effective immediately:

- do not run E006 Confirmation;
- do not acquire paired L2 for E006;
- do not lower the +50 bps trigger;
- do not change the 6-hour baseline, 10-second VWAP/grid, sign, exit, max hold, latency or turnover cap;
- do not add TFI, FLOW_IMPULSE, E004 compression, day/hour filters or alternative sign as a rescue;
- do not open Q2/Validation/Final;
- do not treat the one positive trade as evidence of strategy viability.

The exact historical terminal verdict remains:

`E006_DISCOVERY_FAIL`

## 5. Reusable lesson

The E006 result adds a new branch-level lesson:

A mechanism may have economically nontrivial **per-event** movement yet still be unsuitable as a standalone systematic strategy if the causal event is too rare and gross headroom above execution burden is too small.

Future candidates should therefore require both:

- a natural movement scale large enough to survive taker costs; and
- enough event frequency / active-day breadth to support inference and practical turnover.

## 6. Next research implication

Do not rescue E006 on the same Discovery outputs.

The next candidate should be a genuinely new mechanism family. A retained candidate family is extreme short-horizon price displacement followed by partial mean reversion. This family can be evaluated under a new experiment identifier only after a fresh planning/critical-audit step and an exact executable freeze before any new alpha output.
