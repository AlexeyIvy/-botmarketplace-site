# SC001 / B15-P1 — dialog handoff v6.52 — 2026-09-26

Current state:

`B15P1_COLLECTOR_V014_OPERATIONAL_FREEZE`

Collector v0.1.4 is operational on the VPS and is no longer an active development target.

Final read-only runtime evidence:
- active/enabled;
- all file gates PRESENT;
- running;
- process_epoch=1;
- poll_count=40;
- invalid_poll_count=0;
- missed_poll_slots=0;
- source_gap_count=0;
- process_restart_count=0;
- first background fee refresh completed:
  `last_fee_refresh_completed_ms=1790428549768`;
- price_data_collected=false;
- pnl_calculated=false.

Formal result:
`docs/research/sc001-b15-p1-collector-v0.1.4-operational-freeze-result-v0.1.json`

Roadmap:
`docs/research/sc001-current-roadmap-and-stop-rules-v5.104.md`

Collector anti-loop rule:
do not retune, rewrite, relaunch or restart a healthy collector. Change it only for demonstrated correctness, integrity, compatibility, security or operational defects.

Next:
let B15-P1 data accumulate and return the primary focus to SC001/B15-P1 research and analysis design. The first full operational review remains after 7 complete UTC days unless evidence requires earlier investigation.
