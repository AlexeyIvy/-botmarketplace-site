# SC001 — Reusable Market Building Blocks Registry v0.7

Date: 2026-09-19
Status: **APPEND-ONLY CONTINUATION AFTER C11 FINAL DISPOSITION**
Parent: `sc001-reusable-market-building-blocks-registry-v0.6.md`

## 1. Inheritance

RB001-RB019 remain unchanged.

## 2. New reusable block

### RB020 — Scheduled macro-event risk state v0.1

- source evidence: C11-S0 / C11-v2 Stage A / F027;
- state trigger:
  prospectively known official BLS CPI or Employment Situation release window;
- preferred roles:
  - R2 regime/risk state;
  - R3 veto/context;
  - R5 execution-risk scheduler;
  - R6 external calendar reference;
- evidence:
  - H1 raw abs 60s move >=20 bps in 11/12 events;
  - H1 median abs 60s move ~45.26 bps;
  - fresh Selection residual +1s -> +60s >=20 bps in 14/24 events;
  - fresh median residual ~24.11 bps;
- evidence strength:
  `BROAD_SCHEDULED_EVENT_MOVEMENT_STATE / NON_DIRECTIONAL`;
- reusable lesson:
  exogenous scheduled macro releases can create movement scale materially above ordinary endogenous SC001 signals even when the tested directional extractor fails;
- preferred operational hypotheses:
  - temporarily reduce unrelated passive exposure;
  - widen execution reserves;
  - enter event-risk mode;
  - apply candidate-specific vetoes only under separately frozen experiments;
- forbidden reuse:
  - treat event presence as directional alpha;
  - infer CPI/Employment direction from C11 postmortem family descriptives;
  - rescue terminal C11.
