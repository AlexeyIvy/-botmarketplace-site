# SC001 — C10-S0 Liquidity-Vacuum Headroom Result & Read-Only Postmortem v0.1

Date: 2026-09-18
Status: **C10_S0_REJECT_HEADROOM — SAMPLE AMPLE / BROAD 5s MOVE HEADROOM INSUFFICIENT**
Scope: `SCALPING RESEARCH / SC001`

## 1. Execution integrity

Exact terminal state:

`C10_S0_REJECT_HEADROOM`

Technical completion:

- exit code: `0`;
- frozen L2 source identity passed;
- frozen top-5 near-touch depth definition preserved;
- frozen 60-second causal median baseline preserved;
- frozen one-sided 1/3 vs 2/3 vacuum rule preserved;
- frozen 5-second horizon preserved;
- C5 labels/aggressive-flow conditioning remained excluded;
- no fill model, queue model, fees or PnL were calculated;
- no promotional alpha was accessed.

## 2. Sample result

Observed:

- bid-vacuum events: `6,443`;
- ask-vacuum events: `6,331`;
- total evaluable event count: `12,774`;
- event UTC hours: `24`;
- failed sample gates: none.

Therefore C10-S0 did not fail because of sparse L2 events, one-sided event imbalance, or poor time-of-day coverage.

## 3. Structural move-headroom result

Observed 5-second absolute midquote move:

- p50: about `0.9543 bps`;
- p90: about `3.5799 bps`;
- p99: about `8.4431 bps`;
- maximum: about `39.0877 bps`.

Observed large-move tail:

- events with absolute 5s move >=15 bps: `19`;
- such events span `4` UTC hours.

Directional descriptive diagnostics:

- mean signed 5s move: about `+0.5803 bps`;
- positive signed-move share: about `58.67%`.

Frozen structural hurdle:

- two-fill directional taker reference;
- 5 bps per fill;
- 10 bps fee-reference floor;
- 15 bps gross move hurdle.

All sample gates passed.

Of the structural headroom gates, only:

`p90_abs_move_gte15bps`

failed.

## 4. Mechanism conclusion

Primary failure class:

`AMPLE_SAMPLE_RARE_TAIL_BUT_INSUFFICIENT_BROAD_L2_VACUUM_HEADROOM`

The exact base mechanism is not a structural survivor because its typical and 90th-percentile 5-second move scale is far below the frozen 15 bps hurdle.

The presence of 19 rare >=15 bps events and a ~39.1 bps maximum is not sufficient to promote the mechanism because the frozen p90 gate was intentionally designed to prevent a rare-tail-only strategy from passing.

## 5. Important feature interpretation

C10-S0 is more informative than a simple "no signal" result.

The one-sided L2 vacuum state is:

- frequent;
- symmetric in event counts;
- present across all 24 hours;
- associated with a modest positive directional tendency in the predeclared direction;
- occasionally followed by large moves.

But the broad conditional move distribution is too small for the frozen standalone two-fill taker architecture.

This supports retaining the book-state measurements as reusable features while rejecting the standalone base strategy.

## 6. No-rescue rule

Do not rescue C10-S0 by:

- selecting only the 19 large events;
- changing the 1/3 or 2/3 ratios;
- choosing one side;
- changing the top-5 definition;
- changing the 60-second baseline;
- changing the 5-second horizon;
- lowering the 15 bps hurdle;
- adding C5 aggressive flow;
- selecting a different known Q1 day.

Any tail-specialized or replenishment-failure mechanism would require a materially new candidate/experiment ID and prospective design.

## 7. Evidence disposition

C10-S0:

`REJECT_HEADROOM`

No fill/queue/execution build.
No MDE planning.
No promotional batch.

Feature/building-block evidence should be retained separately.

## 8. Next research action

Return to the previously frozen next-slate order.

Next remaining direction:

`C7 — SPREAD-QUALIFIED NON-BTC / MULTI-ASSET PASSIVE-HYBRID MAKER UNIVERSE`

Start with metadata-only historical L2 availability and non-PnL universe feasibility before any multi-asset L2 body acquisition.
