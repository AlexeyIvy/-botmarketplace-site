# SC001 Current Roadmap and Stop Rules v5.199

Date: 2026-09-29
Status: **B15-P2 V0.1.8 OFFLINE + PUBLIC SMOKE PASS / FULL 94 SEMANTIC RERUN REQUIRES USER DECISION**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.198.md`

## 1. Engineering blocker resolved

The v0.1.7 failure was a synthetic HTML/JSON fixture defect, not a production dual-schema extraction failure.

v0.1.8:

- uses script-context-safe JSON serialization for synthetic `__NEXT_DATA__` fixtures;
- separates direct `visible_text_fragment` sanitizer testing from end-to-end hydration testing;
- does not change production fetch logic;
- does not change semantic classification;
- does not change frozen dual-schema routing;
- does not change the frozen 94-event set.

Frozen implementation:

- path: `research/sc001/sc001_b15p2_announcement_body_semantic_audit_v0_1_8.py`;
- SHA256: `c58d6c31f56c41d593ea5156d0e8ea407f9dfea1e515aa613a0d5113f5a0f9fa`;
- freeze: `docs/research/sc001-b15p2-announcement-body-semantic-audit-implementation-freeze-v0.1.8.json`;
- freeze SHA256: `709c06a314bd685ad37503bf4daa75f062525ba487bfae96292bf699c2a1c96e`.

## 2. Real offline dynamic validation

BotMarketplace Test Executor job:

`job_20260929T125116Z_b631a281`

Result:

- network profile: `offline`;
- exit code: 0;
- timeout: false;
- pass token:
  `B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_V018_SELF_TEST_PASS`;
- trading credentials available: false.

This consumed recovery iteration 1 of the new user-authorized 3-iteration engineering budget.

Remaining reserve:

`2 / 3`

No additional fix was required.

## 3. Public-research dual-schema smoke

BotMarketplace Test Executor job:

`job_20260929T125331Z_89a763dd`

Result:

`B15P2_ANNOUNCEMENT_BODY_DUAL_SCHEMA_SMOKE_V018_PASS`

Representatives:

- SCHEMA_A / BLT_RICHTEXT:
  - DOGUSDT;
  - TONUSDT;
- SCHEMA_B / DOUBLE_DASH_ART_HTML:
  - ESUSDT;
  - ICXUSDT.

Observed:

- 2 / 2 BLT representatives extracted through
  `$.props.pageProps.articleDetail.content.json.children`;
- 2 / 2 ART representatives extracted through
  `$.props.pageProps.articleDetail.content_html`;
- no adaptive fallback path;
- article body text was not persisted;
- semantic classification was not performed in the smoke;
- price/index/basis/returns/PnL remained closed.

Canonical smoke result:

- path: `docs/research/sc001-b15p2-announcement-body-dual-schema-smoke-v0.1.8-result.json`;
- SHA256: `21c80bbf0a921df9544c7c9d9ef04e4710f33985c5d5c51ed181ed19de4fc2b2`.

## 4. Research evidence preserved

Unchanged:

- frozen event count: 94;
- event-set SHA256:
  `1063695ec003a0d6789270659822f50577e6a0f07059d88ac03a5be4288ed1a2`;
- 76 BLT events already semantically resolved from official bodies;
- ART schema census: 18 / 18;
- SCHEMA_A:
  `$.props.pageProps.articleDetail.content.json.children`;
- SCHEMA_B:
  `$.props.pageProps.articleDetail.content_html`.

No new economic result has been observed.

## 5. Engineering budget

Canonical budget:

`docs/research/sc001-b15p2-engineering-recovery-budget-v0.1.json`

Status:

- authorized maximum: 3 recovery iterations;
- consumed: 1;
- remaining: 2;
- offline validation: PASS;
- public-research smoke: PASS.

The remaining two iterations are reserve for technical failures only. They are not permission to change frozen research rules, network scope, endpoint class, or economic firewalls.

## 6. Full frozen 94-event semantic rerun boundary

The full semantic rerun has **not** been executed.

Per the user-approved engineering budget, execution must return to the user before any full 94-event rerun.

If separately authorized, the next execution should:

1. use the exact frozen v0.1.8 bytes above;
2. use the frozen 94-event source only;
3. use the same official Bybit announcement endpoint class;
4. run through BotMarketplace Test Executor with `public_research`;
5. run semantic classification only;
6. persist structured result/logs;
7. keep price/index/basis/returns/PnL/trading closed;
8. perform strategy review after the terminal semantic result.

## 7. Firewalls

Still CLOSED:

- affected-contract price;
- external-reference price;
- observed index values;
- basis/spread calculation;
- returns;
- PnL;
- outcome ranking;
- trading/order execution;
- account/fund management.

## 8. Next state

`USER_DECISION_REQUIRED_BEFORE_FULL_FROZEN_94_SEMANTIC_RERUN_V018`
