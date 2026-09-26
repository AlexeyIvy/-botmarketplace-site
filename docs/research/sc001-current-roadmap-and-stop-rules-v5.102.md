# SC001 Current Roadmap and Stop Rules v5.102

Date: 2026-09-26  
Status: **B15-P1 collector v0.1.4 real VPS launch PASS / short stability check next / collector infrastructure freeze**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.101.md`

## Milestone reached

The exact controlled launch wrapper v0.2.0 has completed successfully on the real VPS.

Terminal status:

`B15P1_FINAL_COLLECTOR_DEPLOYMENT_LAUNCH_V020_PASS`

Evidence source: user-supplied terminal screenshots from the real host execution.

Host result:
`docs/research/sc001-b15-p1-final-collector-deployment-launch-v0.2.0-host-result-v0.1.json`

## Launch acceptance evidence

Observed during the real host launch:
- runtime path/storage preflight = PASS;
- free storage = 67,589,185,536 bytes / 82.34%;
- collector v0.1.4 self-test = PASS;
- staged launch authorization validator = PASS;
- final launch v0.2.0 prerequisites = PASS;
- recovery archived files = 134;
- capability snapshot SHA256 = `01cfa63b6001ec972c4ed87daba5bbd9fba932233b9e8323a49a6a5355e89647`;
- runtime prestart freeze/capability/authorization = PASS;
- service created and enabled;
- initial readiness reached after the expected NOT_READY phase at poll_count=1;
- accepted READY state had poll_count=2;
- valid_poll_count=2;
- invalid_poll_count=0;
- process_epoch=1;
- process_restart_count=0;
- service active=active;
- service enabled=enabled;
- runtime launch authorization SHA256 = `7c6a0296dc47f91a47d4747a0d29174338599a805b797427f19aa2e0c9d3b01c`.

Firewalls remained closed:
- price_data_authorized=false;
- pnl_authorized=false;
- live_execution_authorized=false.

## Operational interpretation

This is the first accepted real deployment of collector v0.1.4.

The collector has demonstrated:
- correct fail-closed prechecks;
- exact frozen artifact binding;
- successful first start;
- no restart during launch acceptance;
- two fully valid Bybit+OKX polls;
- valid 15-second cadence acceptance;
- active/enabled systemd state;
- preserved price/PnL/live-execution firewalls.

The collector is now an operational research data source, not an active development target.

## Anti-loop rule: collector infrastructure freeze

From this point, do **not** change collector code, cadence, service, authorization, normalization, storage semantics or launch machinery merely to improve elegance or add convenience.

Collector changes are allowed only for a demonstrated:
1. correctness defect;
2. data-integrity defect;
3. source/API compatibility break;
4. safety/security defect;
5. operational failure that prevents valid data accumulation.

Any such change must be evidence-driven and separately validated.

## Immediate next step

Use the existing read-only status helper once after launch to confirm continuity:

`ops/systemd/sc001_b15p1_transferability_status.sh`

Acceptance goal:
- service active;
- service enabled;
- state/manifest/capability/authorization present;
- status remains `B15P1_NONPRICE_COLLECTION_RUNNING`;
- poll_count has advanced beyond 2;
- heartbeat remains fresh;
- invalid_poll_count remains 0 or any nonzero value is explicitly explained by source evidence;
- process_restart_count remains 0;
- price_data_collected=false;
- pnl_calculated=false.

No new script is required for this check.

## After short stability acceptance

If continuity is confirmed:
- declare `B15P1_COLLECTOR_V014_OPERATIONAL_FREEZE`;
- let the collector accumulate the non-price dataset;
- shift primary engineering/research attention away from collector construction;
- continue B15-P1 strategy research using the accumulated data when the required observation horizon is reached;
- retain the wrapper-generated first operational review horizon of 7 complete UTC days unless evidence justifies an earlier diagnostic.

## Stop rules

- Never rerun old final launch v0.1/v0.1.1.
- Do not rerun v0.2.0 merely because it already passed.
- Do not restart a healthy collector for testing convenience.
- Do not change the 15-second cadence without demonstrated necessity.
- Keep price/PnL/live-execution firewalls closed.
- Treat data continuity and correctness as higher priority than feature additions.

## Next state

`RUN_ONE_READ_ONLY_POST_LAUNCH_STABILITY_CHECK_THEN_FREEZE_COLLECTOR_INFRASTRUCTURE`
