# SC001-E008 — Maker Discovery Implementation Protocol v1.0

Date: 2026-09-16  
Status: **FROZEN BEFORE FIRST PROMOTIONAL MAKER DISCOVERY RUN**

Parent strategy protocol:  
`docs/research/sc001-e008-passive-maker-executable-protocol-v1.0.md`

Prerequisite data-quality gate:  
`E008_DISCOVERY_SEMANTIC_INTEGRITY_PASS` with 8/8 `DAY_PASS`.

This document freezes implementation details that were intentionally left below the strategy-level protocol. It does not change any strategy parameter, date, queue rule, stale rule, fee, latency, TTL, max-hold rule or promotion gate.

## 1. Allowed modes

Runner:

`research/sc001/sc001_e008_maker_discovery.py`

Allowed modes:

- `preflight` — no-alpha implementation and identity gate only;
- `run` — exactly one frozen promotional Discovery simulation after exact preflight/identity PASS.

Preflight terminal tokens:

- `E008_MAKER_DISCOVERY_IMPLEMENTATION_PREFLIGHT_PASS`
- `E008_MAKER_DISCOVERY_IDENTITY_GATE_PASS`

Promotional run terminal tokens:

- `E008_DISCOVERY_PASS_OPEN_CONFIRMATION_ONCE`
- `E008_DISCOVERY_FAIL`

No Confirmation body, Q2, formal Validation or Final may be accessed by this runner.

## 2. Frozen source identity

The runner may use only the 24 files already accepted by:

- `E008_DISCOVERY_ACQUISITION_VERIFY_PASS`;
- `E008_DISCOVERY_SEMANTIC_INTEGRITY_PASS`.

Before preflight PASS, every unique market-data file is SHA256-recomputed and compared with the frozen acquisition/semantic identities.

The implementation identity gate also requires exact Git blob identities from:

`docs/research/sc001-e008-maker-discovery-implementation-freeze-v1.0.json`

and a clean worktree for the frozen implementation files.

## 3. Frozen scenarios

The single Discovery run replays each of the eight frozen days once while evaluating three pre-declared scenarios in parallel on the same source stream:

1. `primary`
   - placement latency 250 ms;
   - cancel latency 250 ms;
   - forced taker proxy latency 250 ms;
   - initial queue-ahead multiplier 1.0.

2. `latency_500ms`
   - placement latency 500 ms;
   - cancel latency 500 ms;
   - forced taker proxy latency 500 ms;
   - initial queue-ahead multiplier 1.0.

3. `queue_2x`
   - placement latency 250 ms;
   - cancel latency 250 ms;
   - forced taker proxy latency 250 ms;
   - initial displayed queue-ahead multiplied by 2.0.

No other parameter differs across scenarios.

## 4. Causal event ordering

For each UTC day, exact+D+1 trades are reconstructed and L2 is replayed in source order.

Frozen ordering rules:

- deadlines strictly before a market timestamp are processed first;
- cancellation acknowledgements, stale-latch activation, funding boundaries and max-hold decisions at the same millisecond are processed before same-ms trade credit;
- an order activation at the same millisecond as market data is processed only after the market events at that millisecond and therefore receives zero same-ms fill credit;
- any trade sharing a millisecond with one or more L2 records receives zero passive queue/fill credit;
- such a same-ms trade may still serve as the frozen forced-taker proxy because the same-ms ambiguity rule applies to passive queue attribution, not to observed transaction-price availability;
- a forced-taker proxy trade exactly at the five-second proxy deadline remains admissible; missing-proxy failure is declared only after market events at that timestamp.

No hidden sub-millisecond ordering is inferred.

## 5. Passive queue mechanics

Each activated order starts behind the full displayed aggregate size at its own price.

Frozen queue rules:

- compatible aggressive trade volume consumes queue-ahead first;
- only excess compatible aggressive volume can fill our order;
- incompatible trades give zero progress;
- L2 size decreases/cancellations give zero queue progress;
- each L2 size increase is added ahead immediately;
- same-ms L2 records are replayed in exact source order so an increase followed by a decrease cannot be netted away;
- level disappearance/book movement alone never creates a fill;
- partial fills are explicit;
- queue position never survives a full snapshot resync.

For the `queue_2x` scenario only the initial displayed queue-ahead is multiplied by 2.0. Later displayed-size additions are added at their actual source size.

## 6. Snapshot / stale handling

Frozen stale threshold remains strictly `book age > 5,000 ms`.

At stale-latch activation:

- trust becomes false;
- all live maker quotes are cancelled with zero additional fill credit;
- pending placements are cleared;
- incremental L2 updates do not restore trust;
- only a later full snapshot restores trusted state.

Any full snapshot, even while already trusted, invalidates prior queue identity. Therefore all live quotes are cancelled with zero fill credit and replacement waits through the frozen cancel latency and then placement latency.

This is a conservative queue-identity rule and does not alter the parent stale semantics.

## 7. Quote placement and replacement

A placement decision records the current same-side best price.

After placement latency, activation succeeds only if:

- the book is trusted and uncrossed;
- the intended price is still the current same-side best;
- the order remains non-marketable;
- the current strategy state still desires that side/quantity.

Otherwise activation is rejected, never converted to taker, and a fresh decision may be made from then-current trusted state.

Queue-ahead is initialized from the displayed size observed at activation.

A best-price move submits cancellation with frozen cancel latency. The order can still receive causally valid fills before cancellation acknowledgement.

TTL = 30 seconds means cancellation is submitted at exact TTL; cancellation acknowledgement occurs after frozen cancel latency.

Level disappearance and full snapshot resync give zero fill credit immediately; replacement nevertheless waits through the conservative cancel-latency cooldown before a new placement-latency interval begins.

## 8. Strategy-state transitions and partial fills

While flat and outside the funding firewall, the engine maintains one 1-contract BUY at best bid and one 1-contract SELL at best ask.

Any positive maker fill starts or changes the current strategy state.

After any fill:

- all pending placements from the prior state are invalidated;
- any still-live prior-state orders are submitted for cancellation with frozen cancel latency;
- those orders may still receive causally valid fills before cancellation acknowledgement;
- replacement for the new inventory state begins only when conflicting live orders are harmless.

For nonzero inventory, the passive exit quantity equals the absolute remaining inventory.

Partial fills are retained exactly.

If cancellation-latency partial fills would overshoot through flat into the opposite inventory sign without an observable flat terminal state, the engine fails closed for that scenario/day rather than inventing a favorable truncation.

Maximum absolute inventory remains 1 contract.

## 9. Funding firewall

No new flat-state quoting is allowed inside:

- `[T-120s, T+120s)` around 00:00, 08:00 and 16:00 UTC;
- after 23:58:00 UTC.

Conservative implementation detail frozen before Discovery:

- when a funding-firewall window begins while flat with no active inventory cycle, live flat-entry quotes are removed immediately so they cannot create a new entry inside the forbidden window;
- existing inventory continues under the passive-exit/max-hold rules;
- inventory must be zero strictly before a funding boundary;
- nonzero inventory at the exact boundary is fail-closed/unresolved.

## 10. Maximum hold / taker fail-safe

Max hold remains 60 seconds from the first entry fill.

At exact max-hold time, if inventory remains nonzero:

- all passive maker fill credit stops;
- live maker quotes and pending placements are removed;
- forced taker execution uses the first causally observed trade at or after decision time + scenario latency;
- the eligible proxy window ends five seconds after that ready time, inclusive.

If no proxy trade exists, the scenario/day is unresolved and fails closed.

## 11. Cycle accounting

A completed cycle starts with the first maker fill from flat and ends only when:

- net inventory is zero; and
- no stale live order from that cycle can still refill/reopen inventory.

Cycle side classification is determined by the first maker fill:

- BUY => long-first;
- SELL => short-first.

For a completed flat cycle:

- normalized buy notional = sum(qty × price) across BUY fills;
- normalized sell notional = sum(qty × price) across SELL fills;
- gross normalized P&L = sell notional − buy notional;
- fees are charged on each fill notional at 2 bps maker or 5 bps taker;
- net normalized P&L = gross P&L − fees;
- entry notional is BUY notional for long-first or SELL notional for short-first;
- gross/net edge in bps = corresponding normalized P&L / entry notional × 10,000.

The fixed positive OKX contract-value multiplier is omitted because it cancels from bps and cannot change P&L sign or concentration shares. Reported P&L is therefore labelled normalized, not claimed as literal USDT.

## 12. Frozen statistics

Primary pooled statistics use completed primary cycles only.

10% trimmed mean:

- sort cycle net-edge bps;
- remove `floor(0.10 × N)` observations from each tail;
- average the remainder.

Daily mean:

- arithmetic mean of completed-cycle net-edge bps for each frozen UTC day.

Positive day:

- daily mean > 0.

Daily contribution concentration:

- day contribution = sum of normalized net P&L for that day;
- denominator = sum of absolute daily contributions;
- top-1 and top-3 shares use absolute contributions.

Day-block bootstrap:

- 10,000 resamples;
- deterministic seed = 8008;
- each resample selects eight whole days with replacement;
- all cycles from each selected day are retained;
- statistic = pooled mean net-edge bps;
- one-sided 95% LCB = frozen 5th-percentile order statistic at zero-based index `floor(0.05 × 10000)` after sorting.

No bootstrap choice may be changed after Discovery outcome.

## 13. Promotion gates

All parent v1.0 gates remain mandatory and unchanged:

- completed cycles >=100;
- active days = 8/8;
- unresolved inventory = 0;
- max absolute inventory <=1;
- forced-taker exit share <=10%;
- pooled mean net edge >= +1.0 bps;
- 10% trimmed mean >= +0.5 bps;
- pooled median >=0;
- positive days >=6/8;
- median daily mean >0;
- day-block bootstrap 95% LCB >0;
- top-1 absolute daily contribution share <=0.30;
- top-3 share <=0.65;
- long-first cycles >=20;
- short-first cycles >=20;
- primary invariants exact PASS;
- 500 ms stress pooled mean >=0 and total normalized net P&L >0;
- 2x initial queue-ahead stress pooled mean >=0 and unresolved inventory=0.

Stress economics are considered only when their accounting is complete; unresolved/invalid stress accounting cannot be used to pass an economics gate.

Any failed mandatory gate => terminal `E008_DISCOVERY_FAIL`.

Only all gates PASS => `E008_DISCOVERY_PASS_OPEN_CONFIRMATION_ONCE`.

## 14. Stop rules after run

After the first frozen Discovery output:

- do not rerun with altered parameters;
- do not weaken queue/stale semantics;
- do not lower fees;
- do not change dates;
- do not tune latency, TTL, hold, quote quantity or funding windows;
- do not cherry-pick sides/hours/days;
- do not add TFI or any prior SC001 signal family;
- do not replace failed dates.

If `E008_DISCOVERY_FAIL`, E008 is terminal at Discovery and Confirmation/Q2/Validation/Final remain closed.

If `E008_DISCOVERY_PASS_OPEN_CONFIRMATION_ONCE`, stop and freeze/report the Discovery result before opening any Confirmation body.
