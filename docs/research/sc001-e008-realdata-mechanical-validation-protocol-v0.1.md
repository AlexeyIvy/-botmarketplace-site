# SC001-E008 — Real-Data Mechanical Queue Validation Protocol v0.1

Date: 2026-09-16  
Status: **FROZEN NON-PROMOTIONAL MECHANICS VALIDATION — NO P&L**

Prerequisites:
- `E008_DATA_INVENTORY_PASS`;
- historical queue-feasibility v0.1 remains `E008_QUEUE_MODEL_FEASIBILITY_REVIEW`;
- `E008_STALE_LATCH_MODEL_PASS`;
- `E008_QUEUE_SIMULATOR_SYNTHETIC_PASS`.

## 1. Purpose

Apply the already-frozen conservative queue mechanics to the four contaminated Q009A/Q009B engineering days only to prove that the state machine behaves deterministically and fail-closed on real L2 + trade chronology.

This stage is **not** E008 Discovery and must not be used as promotional profitability evidence.

It may report mechanical probe outcomes only. It must not calculate spread capture, markout, fees/rebates, inventory P&L, or profitability.

## 2. Engineering days

Exactly:
- 2024-01-14;
- 2024-01-31;
- 2024-02-12;
- 2024-02-13.

No other L2 body may be opened.

## 3. Deterministic probe schedule

This stage does not choose a trading strategy. It uses a fixed engineering probe schedule solely to exercise queue mechanics.

For each UTC day:
- one scheduled probe every 15 minutes from 00:00 through 23:45 UTC: 96 scheduled probes;
- side alternates deterministically by slot index: even slot = BUY, odd slot = SELL;
- quantity = exactly `1.0` historical size unit;
- placement may occur only on the first trusted L2 state at or after the scheduled boundary and no later than 1,000 ms after it;
- if no trusted state exists in that interval, the probe is `SKIPPED_NO_TRUSTED_STATE`;
- BUY rests at observed best bid; SELL rests at observed best ask;
- initial queue-ahead = full displayed aggregate size at that resting price;
- TTL = 60,000 ms from actual placement;
- at most one probe may be live at any time. The 15-minute schedule and 60-second TTL make overlap impossible by design.

These probe parameters are mechanical-test constants and are **not** E008 profitability parameters.

## 4. Frozen queue semantics

Reuse the synthetic mechanics unchanged:
- only compatible aggressive transaction volume reduces queue-ahead;
- BUY uses sell-aggressor trades at price `<= resting_price`;
- SELL uses buy-aggressor trades at price `>= resting_price`;
- queue-ahead is consumed before own quantity;
- partial fills explicit;
- same-millisecond trade/L2 ambiguity receives zero queue/fill credit;
- displayed-size decrease/cancellation gives zero queue progress;
- displayed-size increase at resting price is added ahead;
- resting-level disappearance before full fill terminates the remainder `CANCELLED_UNFILLED` with no inferred fill;
- book-price movement alone never implies fill;
- no exact FIFO claim.

## 5. Snapshot and stale-latch semantics

Frozen stale-book rule remains:
- trusted only after full snapshot;
- book age >5,000 ms => stale latch;
- stale latch immediately terminates a live probe as `STALE_CANCELLED`;
- no trade while latched gives queue/fill credit;
- incremental updates do not restore trust;
- only a later full snapshot restores trusted state.

Additional conservative resynchronization rule:
- any full snapshot received while a probe is live terminates the live remainder as `CANCELLED_UNFILLED` before applying the new snapshot, because historical aggregate snapshots cannot preserve the hypothetical order's queue priority.

## 6. Allowed outputs

Per day and pooled:
- scheduled probes;
- placement count / skipped-no-trusted-state count;
- terminal mechanical states: `FILLED`, `CANCELLED_UNFILLED`, `STALE_CANCELLED`;
- probes with nonzero partial quantity before cancellation;
- total mechanically credited fill quantity in historical size units;
- stale-latch cancellations;
- level-disappearance cancellations;
- TTL cancellations;
- snapshot-resync cancellations;
- invariant violations;
- source identity/hash facts and runtime/resource facts.

Forbidden:
- entry/exit return;
- spread capture in price or bps;
- markout;
- maker fee or rebate;
- inventory P&L;
- profitability;
- parameter ranking/optimization;
- TFI or prior signals.

## 7. PASS rule

Exact `E008_QUEUE_SIMULATOR_MECHANICAL_PASS` requires:
- all four source sets load with qualified identities;
- all four days complete deterministic replay without exception;
- exactly 96 scheduled probes/day;
- placed + skipped = scheduled for every day;
- max concurrent live probes <=1;
- no fill credit occurs while stale-latched;
- no same-ms ambiguous trade contributes credit;
- no size decrease/cancellation contributes queue progress;
- no level disappearance creates inferred fill;
- every credited fill quantity is within `[0, 1.0]` per probe;
- every live probe terminates by FILLED, TTL/level/snapshot cancellation, or stale cancellation;
- no profitability fields are produced;
- Q2 / Validation / Final remain closed.

Any invariant failure yields `E008_QUEUE_SIMULATOR_MECHANICAL_REVIEW`.

## 8. Interpretation

PASS means only that the conservative simulator mechanics are executable on real historical chronology. It does **not** establish maker profitability and does not authorize using these four contaminated days as E008 Discovery evidence.

## 9. Next step after PASS

Only after PASS may E008:
1. freeze a new untouched Q1 Discovery date set before opening/downloading their L2 bodies;
2. freeze an actual passive strategy protocol (quote placement/cancel/inventory/fee rules) before promotional output;
3. acquire only the frozen Discovery data under data-only integrity gates;
4. run one E008 Discovery.
