# SC001 Current Roadmap and Stop Rules v5.104

Date: 2026-09-26  
Status: **B15-P1 collector v0.1.4 OPERATIONAL FREEZE / data accumulation active / primary focus returns to research**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.103.md`

## Operational freeze reached

The deployed collector v0.1.4 has now passed both:
1. real launch acceptance; and
2. post-launch continuity including completion of the first background fee refresh.

Formal state:

`B15P1_COLLECTOR_V014_OPERATIONAL_FREEZE`

Result evidence:

`docs/research/sc001-b15-p1-collector-v0.1.4-operational-freeze-result-v0.1.json`

## Final observed runtime state

Read-only status helper reported:
- service active = active;
- service enabled = enabled;
- state = PRESENT;
- manifest = PRESENT;
- capability = PRESENT;
- launch authorization = PRESENT;
- collector status = `B15P1_NONPRICE_COLLECTION_RUNNING`;
- process_epoch = 1;
- poll_count = 40;
- invalid_poll_count = 0;
- missed_poll_slots = 0;
- source_gap_count = 0;
- process_restart_count = 0;
- last_fee_refresh_completed_ms = 1790428549768;
- price_data_collected = false;
- pnl_calculated = false.

This confirms:
- the fast 15-second collection lane remains healthy;
- the first slow fee-refresh cycle completed;
- there were no observed invalid fast polls;
- no missed slots;
- no source gaps;
- no process restart;
- price/PnL firewalls remain closed.

## Collector anti-loop freeze rule

Collector infrastructure is now frozen.

Do not change:
- collector v0.1.4 code;
- 15-second cadence;
- systemd service;
- runtime authorization semantics;
- normalization/storage semantics;
- launch wrapper;
- price/PnL/live-execution firewall;

unless there is concrete evidence of:
1. correctness defect;
2. data-integrity defect;
3. source/API compatibility break;
4. safety/security defect;
5. operational failure preventing valid data accumulation.

Do not optimize for elegance or convenience.

## Operational phase

The collector should now remain running and accumulate the B15-P1 non-price dataset.

Routine work should be observation, not development.

The launch wrapper already records a first full operational review horizon after 7 complete UTC days. Earlier investigation is justified only by evidence such as:
- service inactive;
- restart count increase;
- source gaps;
- missed slots;
- repeated invalid polls;
- fee refresh failure/staleness;
- storage pressure;
- API compatibility break.

## Research phase transition

Primary engineering/research effort now moves away from collector construction and back to SC001/B15-P1 research.

The collector is an input-producing instrument. It is no longer the active development task.

Next research work should:
- preserve the frozen collector;
- define the minimum observation windows needed for B15-P1 inference;
- prepare analysis protocol(s) that consume the accumulated dataset without changing collection semantics;
- continue the strategy viability investigation under existing fail-closed rules.

## Stop rules

- Do not rerun final launch v0.2.0 while the healthy service is running.
- Never use old final launch v0.1/v0.1.1.
- Do not restart the service for convenience.
- Do not change cadence or firewalls without demonstrated necessity.
- Treat continuity/correctness defects as incidents, not tuning opportunities.
- Keep the collector operational while research advances independently.

## Next state

`ACCUMULATE_B15P1_DATA_AND_PREPARE_POST_FREEZE_RESEARCH_ANALYSIS`
