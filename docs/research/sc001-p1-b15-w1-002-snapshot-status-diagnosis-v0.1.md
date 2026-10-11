# SC001-P1-B15-W1-002 — W1 snapshot status-gate static diagnosis v0.1

Date: 2026-10-11  
Worker: `P1_PROSPECTIVE_EVENT`  
Authorization: `T0_DESIGN_ONLY_STATIC_DIAGNOSIS`  
Terminal status: `B15P1_W1_STATUS_GATE_STATIC_CAUSE_IDENTIFIED_REVIEW`

## Conclusion

`STATUS_MISMATCH_REQUIRES_BOUNDED_METADATA_PROOF`

The static cause of the observed failure is identified: the W1 census treats the materialized collector's **current lifecycle status** as a prerequisite and rejects every status other than `B15P1_NONPRICE_COLLECTION_RUNNING` before it evaluates any frozen-day manifest, poll-chain, coverage, or both-venue-valid evidence. A live `RUNNING` value on 2026-10-11 is not, by itself, a scientific property of the already closed 2026-09-27..2026-10-03 W1 records. A clean post-window `STOPPED` snapshot can therefore be historically analyzable in principle while failing the current implementation's present-tense gate.

That does **not** establish that the failed snapshot was cleanly stopped after W1. The canonical result exposes only a status mismatch, not the observed status, transition time, or reason. `SOURCE_REVIEW`, an early stop, stale `RUNNING` after an exceptional exit, or another invalid state remain possible. W1 quality was never evaluated and must not be called PASS.

## Exact static trace

### Census ordering

In `research/sc001/sc001_b15p1_stage_e_w1_input_census_v0_1.py`:

- `check_state_manifest()` starts at line 98, loads `collector_state.json` and `collector_manifest.json`, validates state identity at lines 107–108, and requires current `state.status == B15P1_NONPRICE_COLLECTION_RUNNING` at lines 109–110.
- The price/PnL firewalls, manifest identity, authorization firewalls, and 15-second cadence checks follow at lines 111–118.
- `analyze()` starts at line 183 and calls `check_state_manifest(root)` immediately at line 184.
- Only afterward does it validate the fixed W1 window, the pre-window manifest/baseline/fee metadata (lines 185–227), and each frozen W1 day's manifests and polls (lines 236–265).
- `verify_poll_day()` at lines 122–180 independently checks the per-row price firewall, recomputed hash chain, within-day and cross-day continuity, unique ordered in-day 15-second slots, coverage, and both-venue-valid fraction.
- The 99% coverage and 99% both-venue-valid gate is computed at lines 309–312. Source gaps remain explicit at lines 315–322.

Therefore the failed run's null coverage/validity/chain fields are an ordering consequence, not evidence that those historical gates failed or passed.

### Collector lifecycle

In `research/sc001/sc001_b15p1_nonprice_transferability_collector_v0_1_4.py`:

- constants at lines 62–68 define `RUNNING`, `SOURCE_REVIEW`, and `STOPPED`;
- `initial_state()` at lines 911–945 creates a new state as `INITIALIZED`, while a valid existing state is returned with its prior status;
- `run_collector()` begins at line 1687 and persists `RUNNING` after startup validation/state loading at lines 1703–1708;
- a `SIGINT`/`SIGTERM` handler only sets `STOP_REQUESTED` (lines 1682–1684); the orderly loop exit reaches the post-`finally` block, which persists `STOPPED`, `stopped_ms`, and a final heartbeat at lines 2001–2010;
- `STORAGE_WARNING` only warns, while `STORAGE_PRESSURE_REVIEW` persists `SOURCE_REVIEW` plus `stop_reason` and returns 2 at lines 1753–1763;
- if an exception escapes after `RUNNING` was persisted, the cleanup `finally` runs but the post-`finally` `STOPPED` write is not reached. Thus a stale `RUNNING` snapshot is statically possible too.

These are reachable code states, not findings about job `job_20261011T114243Z_57ec4c24`. The exact prior result, SHA256 `6b2e535b22500be5e425e0df804e3f002e99f772495774298ef47f437a52f58c`, reports only `RuntimeError: collector snapshot not running`, 17/17 declared inputs materialized, package integrity true, and no evaluation of coverage, both-venue validity, or chain continuity.

## Historical W1 validity versus present lifecycle

The binding W1 protocol and contracts define historical quality through the fixed complete UTC days, immutable daily-manifest/file bindings, recomputed poll hashes, within/cross-day chain continuity, explicit source gaps, firewalls, and 99% coverage and both-venue-valid thresholds. None of those predicates logically requires the collector process to remain live after `2026-10-04T00:00:00Z`.

However, lifecycle metadata can still be safety-relevant:

- a stop or `SOURCE_REVIEW` during W1 may identify missing exposure, storage pressure, or incomplete finalization;
- an exceptional exit may leave a stale status and could coincide with an unclosed day or chain break;
- an identity mismatch, price/PnL firewall violation, missing daily manifest, SHA/row mismatch, chain break, out-of-window slot, incomplete day, coverage below 99%, or both-venue-valid fraction below 99% must still fail closed.

The correct static separation is therefore:

1. lifecycle evidence establishes **when and why collection ceased or entered review**;
2. frozen-day evidence establishes **whether W1 itself is complete and internally valid**.

This diagnosis does not change the current code or waive its `RUNNING` predicate; it identifies why that predicate can be over-restrictive for a retrospective closed-window census.

## Frozen boundaries retained

No boundary changes are proposed:

- W1 stays exactly `2026-09-27` through `2026-10-03`, with `2026-09-26` used only for the frozen baseline/fee-freshness reachback;
- earliest census time remains `2026-10-04T00:00:00Z`;
- the original 17 materialized inputs remain the same;
- expected cadence remains 15 seconds / 5760 slots per complete UTC day;
- coverage and both-venue-valid thresholds remain 99.0%;
- daily-manifest SHA/row bindings and within/cross-day poll-chain continuity remain mandatory;
- source gaps remain explicit and are never forward-filled;
- price, PnL, opportunity-rate inference, network, credentials, collector mutation, and restart remain closed.

The failed PR #474 result remains immutable and `SOURCE_REVIEW`; it is not reinterpreted as a quality PASS.

## Cheapest discriminating future evidence

One future, separately authorized **metadata-only lifecycle receipt** is sufficient to decide whether a contract adjustment is worth considering. It should expose only:

- state schema/stage/version and exact `status`;
- `started_ms`, `last_heartbeat_ms`, `stopped_ms` if present, and `stop_reason` if present;
- `current_utc_day`, `last_scheduled_slot_ms`, `process_epoch`, `process_restart_count`, and `source_gap_count`;
- a mechanically derived relation of lifecycle times to W1 end `2026-10-04T00:00:00Z`.

No poll/event/fee body, raw market data, price, return, PnL, credential, or outcome field is needed for that discrimination. Interpretation:

- `STOPPED` with a credible stop after W1 end makes a retrospective historical-status contract mismatch plausible, subject to all original W1 gates still passing later;
- `SOURCE_REVIEW`, a stop/last slot before W1 end, or lifecycle ambiguity preserves the source-quality stop/review;
- stale `RUNNING` does not prove continuity and requires fail-closed review.

This task authorizes zero collector/VPS/Runner/protected-data reads, so it did not obtain that receipt. Because the documented state lives in protected collector material, obtaining it requires a new exact T3 user-approved collector/VPS metadata-read action, or a new exact T3 Runner/Runner-Probe task if the approved plane is a sealed snapshot. Authorization must name the fields above, forbid bodies, set one read/run and zero mutation/restart budgets, and stop after the receipt. No existing bundle retry is authorized.

## Three-lens review

- **Trader:** Rare outage events may have research value, but a full rerun or engineering change is unjustified until the cheap lifecycle metadata distinguishes a clean post-window stop from a source-quality hazard.
- **Engineer:** Current lifecycle and historical snapshot integrity are separate contracts. Any future implementation change should preserve identity/firewall checks and all daily/hash/coverage gates, and should accept a non-running snapshot only with explicit lifecycle evidence proving the stop was outside the window.
- **Statistician:** No after-failure relaxation is allowed. Dates, denominator, 99% thresholds, source-gap treatment, and chain rules stay frozen; metadata may explain admissibility but cannot substitute for the never-run W1 quality checks.

## Strategic implication

`NO ROADMAP CHANGE REQUIRED`.

The static cause is identified, but actual snapshot cause and W1 quality remain unresolved. The only recommended continuation is the one bounded metadata-only lifecycle receipt above, followed by independent Strategy Manager review. Do not retry the consumed bundle, open W1 bodies, patch the predicate, or advance to price/outcome work from this diagnosis.
