# SC001 parallel research — dialog handoff v7.03 — 2026-09-27

Status: **MOVE TO NEW DIALOG / DISCUSS RESEARCH-STRATEGY AGENT FIRST / THEN CONTINUE B15-P2**

Repository:
`AlexeyIvy/-botmarketplace-site`

Current GitHub HEAD before this handoff:
`d83e7dbc3fe420c38702fee0c2d77de93de10ff0`

## 1. FIRST TOPIC IN THE NEW DIALOG — dedicated Research Strategy Agent

Before continuing experiments, discuss whether to create a separate agent whose job is **only to manage and improve the research strategy itself**.

Concept:
- the agent does not run individual market/strategy experiments;
- it does not spend its context on iterative script execution;
- it reads canonical results from GitHub and, where useful, read-only VPS outputs;
- it maintains a compact map of active/terminal branches, reusable blocks, contamination, horizons, mechanism families, costs and evidence maturity;
- it periodically reviews the research portfolio from financial/trader, programmer/trader and mathematician-statistician perspectives;
- it detects:
  - duplicate/disguised-rescue mechanisms;
  - horizon bias;
  - weak edge-to-cost economics;
  - gaps in mechanism/horizon coverage;
  - opportunities to reuse validated building blocks;
  - candidate opportunities for custom indicators;
  - overfitting/multiplicity/contamination risks;
  - low-value work that should be stopped;
- it proposes versioned roadmap/governance amendments, but does not silently change frozen experiment rules;
- actual experiments remain separate workers/subagents/workflows.

Questions to decide first:
1. best technical form inside the current ChatGPT/GitHub/MCP architecture;
2. what data the manager may read/write;
3. whether it should be advisory-only or allowed to update roadmap/docs after approval;
4. how often it should review the program;
5. how to keep its context compact and independent from execution noise;
6. whether actual experiment agents should report standardized result manifests to it.

Do **not** continue B15-P2 until this architecture discussion is complete.

## 2. Mid-course research-strategy audit

Latest binding governance:

`docs/research/sc001-midcourse-research-strategy-audit-and-governance-amendment-v0.2.md`

Key rules:
- horizon follows mechanism timescale and economics; longer is not automatically better;
- H0-H4 horizon taxonomy;
- two-mode Minimum Viable Horizon: ordinary-state vs structural/exogenous-event;
- Edge-to-Fill before outcome;
- capital-time economics as ranking/deprioritization dimension;
- structured Mechanism Fingerprint Gate;
- new candidates classified as independent / materially different / same-mechanism variant / disguised rescue;
- adaptive discoveries require fresh Confirmation;
- horizon variants count toward search multiplicity;
- same-evidence indicator rescue is prohibited;
- reusable blocks may inspire new mechanisms on fresh evidence;
- custom indicators are encouraged when built from causal primitives, not direct historical-PnL optimization.

Roadmap:
`docs/research/sc001-current-roadmap-and-stop-rules-v5.154.md`

## 3. Current branch states

### B15-P1
- collector state: operational freeze;
- Stage E W1 accumulation continues;
- W1 full UTC window: 2026-09-27 through 2026-10-03;
- earliest real W1 census: 2026-10-04T00:00:00Z;
- do not mutate healthy collector.

### B14-A
- Sep25 P0 = `B14A_P0_DEFER_DATA`;
- cause: OKX WebSocket subscribe request used invalid id with hyphen -> code 60033;
- not an economic reject;
- future retry only on a new prospective expiry after ACK transport preflight.

### B13-C S0
Terminal:
`B13C_S0_SIMPLE_REVERSAL_HEADROOM_REJECT`

Real result:
- n=1,793;
- median signed 30s reversal = +1.3682 bps;
- p25 = -5.1393 bps;
- p75 = +9.1050 bps;
- positive share = 55.884%;
- positive complete-day medians = 5/6;
- only frozen 30 bps magnitude gate failed.

Reusable:
`RB021 — Explicit pure-side liquidation-burst reversal state v0.1`

Do not rescue on same interval.

### B14-B
Terminal:
`B14B_REJECT_PERSISTENT_CARRY_STRUCTURAL`

Fresh Jul-Sep 2026 result:
- 110 valid non-overlapping 7-day cycles;
- median gross carry = +1.3863 bps;
- p25 = -2.5951 bps;
- p75 = +3.6405 bps;
- positive cycles = 60.91%;
- 8 positive-median symbols;
- 3 positive-median months;
- only median >=50 bps gate failed.

Reusable:
`RB022 — Persistent cross-venue funding-differential direction state v0.1`

Do not rescue on same window.

Mandatory terminal-experiment reusable-block policy:
`docs/research/sc001-terminal-experiment-reusable-block-extraction-policy-v0.1.md`

Reusable registry current:
`docs/research/sc001-reusable-market-building-blocks-registry-v0.9.md`

## 4. Next independent branch already prepared but PAUSED

Selected next branch:
`B15-P2 — SCHEDULED PERPETUAL DELISTING / FORCED CLOSE`

First stage:
Bybit source-only event census.

No price/basis/PnL authorized.

Protocol:
`docs/research/sc001-b15p2-bybit-delisting-source-only-event-census-protocol-v0.1.md`

Implementation:
`research/sc001/sc001_b15p2_bybit_delisting_source_census_v0_1.py`

Implementation SHA:
`da047f6dba6881fdfa04db187616b851e1ed35af7af9b33ed6921daed807f8ef`

Exact sealed offline self-test, NOT RUN:
- bundle ID: `bundle_20260927T095903Z_afb63063`
- bundle SHA256: `ed2812b5baae997a24e3f10e5a214a5d71ae9f0f9fe9448625a4faf03611592a`
- approval code: `BM-ED2812B5BAAE`
- expected PASS: `B15P2_BYBIT_DELISTING_SOURCE_CENSUS_V01_SELF_TEST_PASS`
- inputs: none
- no network, no real announcements, no prices.

After the Research Strategy Agent discussion, if the current plan remains valid:
1. run this exact offline self-test after explicit approval;
2. if PASS, prepare separate networked source-only census approval;
3. only later, before any B15-P2 price outcome, require mechanism fingerprint + mechanism-timescale + Edge-to-Fill + two-mode MVH + capital-time review.

## 5. Operational principles

- GitHub is source of truth.
- Research Runner is offline/hardened; every newly sealed bundle requires exact fresh approval.
- Networked public-source jobs run on VPS only after separate user approval.
- Avoid overengineering and repeated rewrites of healthy infrastructure.
- Use reusable kernels and fail-closed semantics.
- Negative strategy result != useless information: always extract reusable blocks where evidence supports them.

## 6. New-dialog start instruction

Start by discussing the proposed **dedicated Research Strategy Agent / Manager** architecture.

Only after that discussion and any justified GitHub design updates should execution resume from the sealed B15-P2 source-only self-test.
