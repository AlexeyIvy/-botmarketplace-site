# BotMarketplace / SC001 — Dialog Handoff v8.00

Date: 2026-09-29  
Canonical Git HEAD at handoff: `2739658913823c1104e3148709296097e9f08179`

## 1. Source of truth

Repository:

`AlexeyIvy/-botmarketplace-site`

Branch:

`main`

Use GitHub as canonical source of truth.

Primary current research state:

`docs/research/sc001-research-strategy-state-v0.1.json`

Primary current roadmap:

`docs/research/sc001-current-roadmap-and-stop-rules-v5.198.md`

## 2. SC001 / B15-P1

State:

`W1_ACCUMULATION_OPERATIONAL_FREEZE`

Window:

`2026-09-27..2026-10-03 UTC`

Earliest real census:

`2026-10-04T00:00:00Z`

Healthy collector must not be modified.

## 3. SC001 / B15-P2 — current research status

Frozen event set:

- 94 Bybit USDT perpetual delisting events;
- event-set SHA256:
  `1063695ec003a0d6789270659822f50577e6a0f07059d88ac03a5be4288ed1a2`.

Price/index/basis/returns/PnL remain CLOSED.

### Semantic evidence already obtained

76 BLT-generation announcement pages were semantically resolved from official announcement bodies.

For all 76 resolved events:

- exact announced-time match;
- automatic close explicit;
- active-order auto-cancel explicit;
- trading-stop explicit;
- closing-price basis:
  `AVERAGE_INDEX_PRICE_WINDOW`;
- stated window:
  30 minutes;
- funding wording not stated;
- no revision/postponement wording.

Canonical terminal REVIEW:

`docs/research/sc001-b15p2-announcement-body-semantic-audit-v015-review-result-v0.1.json`

Worker Result Manifest:

`docs/research/worker-results/sc001-b15p2-semantic-v015-review-manifest-v0.1.json`

### Dual official Bybit hydration schemas

SCHEMA_A — BLT_RICHTEXT:

- frozen count: 76;
- URL generation: `-blt...`;
- title:
  `$.props.pageProps.articleDetail.title`;
- body:
  `$.props.pageProps.articleDetail.content.json.children`.

SCHEMA_B — DOUBLE_DASH_ART_HTML:

- frozen count: 18;
- URL generation: `--art...`;
- title:
  `$.props.pageProps.articleDetail.title`;
- body:
  `$.props.pageProps.articleDetail.content_html`;
- census coverage: 18 / 18.

Canonical ART census:

`docs/research/sc001-b15p2-art-generation-schema-census-result-v0.1.json`

Canonical dual-schema routing freeze:

`docs/research/sc001-b15p2-hydration-dual-schema-routing-freeze-v0.1.json`

### B15-P2 technical stop state

Previous user-approved engineering recovery budget:

`5 / 5 consumed`

Automatic sixth B15-P2 recovery run is NOT authorized.

Current canonical state:

`RECOVERY_BUDGET_EXHAUSTED_JOINT_REVIEW_REQUIRED`

Last B15-P2 failure was offline self-test only, before network execution:

`SCHEMA_B_SCRIPT_STYLE_EXCLUSION`

Root cause:

the synthetic end-to-end fixture embedded literal `</script>` inside JSON placed in outer `<script id="__NEXT_DATA__">`, truncating the outer script before JSON decode.

Canonical post-mortem:

`docs/research/sc001-b15p2-final-recovery-v017-invalid-script-context-fixture-diagnostic-v0.1.json`

Research meaning:

- frozen 94-event source NOT invalidated;
- SCHEMA_A NOT invalidated;
- SCHEMA_B NOT invalidated;
- semantic classifier NOT invalidated;
- dual-schema routing NOT invalidated;
- no economic result observed;
- price/outcome firewalls remain closed.

Before any renewed B15-P2 execution, establish a new explicit engineering budget/authorization.

## 4. Process rule learned from B15-P2

Binding engineering policy:

`docs/research/sc001-engineering-iteration-and-runtime-output-policy-v0.1.md`

Important operating rule:

**STATIC REVIEW -> REAL OFFLINE DYNAMIC TEST -> FIX -> OPTIONAL PUBLIC-RESEARCH SMOKE -> FREEZE -> RESEARCH EXECUTION**

Do not use the user as the default command runner for ordinary software debugging.

Large outputs must be structured JSON/logs readable through MCP, not reconstructed from many screenshots.

## 5. New infrastructure: BotMarketplace Test Executor

Purpose:

separate bounded VPS execution plane for ordinary software/research testing.

It does NOT replace or weaken the hardened Research Runner.

Runbook:

`docs/infrastructure/botmarket-test-executor-v1.0.md`

### Security model

Separate users:

- control:
  `botmarket-testctl`;
- worker:
  `botmarket-testjob`.

Dedicated read-only GitHub deploy key.

GitHub write:

`DENIED_AS_REQUIRED`

No arbitrary shell MCP tool.

No trading/account credentials are available to jobs.

Network profiles:

- `offline`;
- `public_research`.

Limits:

- max 3 runs / rolling hour;
- max 10 runs / UTC day;
- max 1 concurrent job;
- max 900 s per job.

Worker sandbox retains:

- `NoNewPrivileges=yes`;
- empty capability sets;
- `ProtectSystem=strict`;
- process/kernel/device protections;
- private/offline network profile when requested;
- public-research profile blocks loopback/private/link-local ranges.

## 6. VPS compatibility work already completed

The VPS systemd namespace incompatibility was localized to:

`InaccessiblePaths=/run/systemd`

That broad mask causes:

`226/NAMESPACE`

Targeted replacement:

`InaccessiblePaths=/run/systemd/private`

was validated.

Canonical compatibility result:

`docs/infrastructure/botmarket-test-executor-compatibility-v2-result-v0.1.json`

Installation freeze v1.0.2 successfully passed:

- repository read PASS;
- repository write DENIED;
- arbitrary root sudo DENIED;
- restricted sudo bridge PASS;
- isolated offline job PASS;
- public-research network sandbox PASS;
- local MCP active.

## 7. Tunnel + ChatGPT app

Tunnel ID:

`tunnel_6abb7a5d33908191a1a58705afd5176a`

Tunnel service:

`botmarket-test-executor-tunnel.service`

Local MCP:

`http://127.0.0.1:8769/mcp`

Tunnel health:

`http://127.0.0.1:8083`

Tunnel readiness:

`PASS / READY`

ChatGPT app:

`BotMarketplace Test Executor`

App status:

`CONNECTED`

Test Executor tools are visible in ChatGPT.

Canonical deployment state:

`docs/infrastructure/botmarket-test-executor-deployment-state-v1.0.json`

## 8. First MCP end-to-end test

Already passed:

- `get_test_executor_info`: PASS;
- privilege bridge: PASS;
- `refresh_repo`: PASS;
- Test Executor clone refreshed cleanly.

Observed refresh:

- before:
  `f873606a0e0aa596eadd8e201737b2ff0dad1c46`;
- after/origin:
  `ebb727376e8423cf528817661fbc4ded116a6d8b`.

First `run_repo_test` failed before creating a job manifest.

Canonical diagnostic:

`docs/infrastructure/botmarket-test-executor-first-mcp-run-diagnostic-v0.1.json`

Root cause:

`CONTROL_SERVICE_RESTRICT_SUIDSGID_VS_RUNTIME_SETGID_CHMOD`

The security policy is correct.

The runtime directory implementation was wrong:

the control service correctly uses `RestrictSUIDSGID=true`, but `run_repo_test` attempted runtime setgid chmod modes `02750/02770`.

### Prepared fix

Installation freeze:

`docs/infrastructure/botmarket-test-executor-installation-freeze-v1.0.3.json`

Status:

`READY_FOR_REDEPLOY_AFTER_FIRST_MCP_RUN_DIAGNOSTIC`

Fix:

- retain control-service `RestrictSUIDSGID=true`;
- remove runtime setgid chmod;
- explicitly assign group `botmarket-test-jobs`;
- job mode `0750`;
- package dir `0750`;
- package files `0440/0550`;
- output `0770`;
- manifest `0440`;
- add startup filesystem-boundary self-test;
- add cleanup for orphan manifestless jobs older than 3600 s.

Worker security is unchanged.

## 9. Exact next action in the new dialog

DO NOT return to B15-P2 yet.

First complete Test Executor E2E:

1. inspect current Git HEAD and canonical deployment state;
2. redeploy the main Test Executor using installation freeze v1.0.3;
3. verify MCP service startup filesystem-boundary self-test PASS;
4. verify restricted sudo bridge PASS;
5. through the connected Test Executor app:
   - `get_test_executor_info`;
   - `refresh_repo`;
   - harmless offline `run_repo_test`;
   - `get_job_status`;
   - `read_job_log`;
6. only after complete E2E PASS mark Test Executor operational.

After Test Executor E2E PASS:

- return to B15-P2;
- propose a NEW explicit engineering budget;
- repair the synthetic `__NEXT_DATA__` fixture using script-context-safe JSON serialization;
- separate direct `visible_text_fragment` sanitizer tests from end-to-end hydration tests;
- run self-tests through Test Executor offline;
- only after offline PASS perform a small public-research smoke;
- only then consider a new full frozen 94-event semantic rerun.

## 10. Governance / non-negotiable firewalls

Still CLOSED unless separately authorized:

- price access;
- external-reference price access;
- observed index values;
- basis/spread;
- returns;
- PnL;
- outcome ranking;
- trading/order execution;
- account/fund management.

Research Strategy Manager remains advisory and does not execute Runner/VPS jobs.

## 11. Start-new-dialog instruction

In the new dialog:

- connect:
  - BotMarketplace Test Executor;
  - BotMarketplace GitHub Control;
  - VPS Reader if needed;
  - Research Runner only when offline sealed-bundle work is actually required;
- read this handoff first;
- then continue from section 9.
