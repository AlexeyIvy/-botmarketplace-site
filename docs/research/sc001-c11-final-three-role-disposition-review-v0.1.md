# SC001 — C11 Final Three-Role Disposition Review v0.1

Date: 2026-09-19
Status: **FINAL C11 TRADING-CANDIDATE DISPOSITION**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c11-v2-selection-stage-ab-result-v1.1.md`;
- `docs/research/sc001-c11-v2-direction-retention-readonly-postmortem-result-v0.1.md`;
- `docs/research/sc001-c11-c12-three-role-current-state-review-v0.1.md`.

## 1. Final disposition

C11 trading-strategy candidate is terminal:

`C11_TERMINAL_REJECT_DIRECTION_CAPTURE`

This does not revoke:

`C11_S0_EVENT_MOVE_HEADROOM_SURVIVE`

and does not reinterpret:

`C11_S1_DEFER_SAMPLE`.

The terminal conclusion is specific:

> Scheduled CPI/Employment events generate economically large raw and residual BTC movement, but the prospectively frozen first-causal-1-second impulse sign does not extract direction with enough consistency or magnitude to justify Confirmation or execution modeling.

## 2. Programmer / trader review

What worked:

- 24/24 exact event bodies were data-valid;
- both legacy and new OKX trade schemas were handled with explicit fail-closed semantics;
- DATA_INVALID / NO_TRADE / LONG / SHORT semantics were separated;
- Stage A and Stage B were executed under frozen identities;
- opportunity retention remained explicit.

What failed:

- Direction Rule v2 did not convert event opportunity into a tradable directional edge.

The failure is not an implementation artifact:

- data-valid = 24/24;
- actionable = 24/24;
- no sample exclusion;
- no NO_TRADE concentration;
- both event families represented fully.

Engineering conclusion:

Do not spend more implementation effort on event slippage/fill/PnL for this C11 rule because the gross directional extractor already fails before execution.

## 3. Financial review

C11 retains strong opportunity scale:

- H1 raw 60s median ~45.26 bps;
- fresh Selection residual +1s -> +60s median ~24.11 bps;
- 14/24 fresh events retained >=20 bps absolute residual movement.

But usable directional capture is weak:

- median signed continuation ~3.63 bps;
- only 6/24 events achieved >=20 bps in the chosen direction;
- only 6/14 large-residual events were captured at >=20 bps.

Therefore:

`large movement != monetizable direction`

The expected economic burden remains ~20 bps before exact execution modeling.

A median directional continuation of ~3.63 bps is not close enough to justify spending the protected Confirmation sample or building an execution model.

## 4. Mathematics / statistics review

The fresh Selection batch improved materially over the old H1 evidence:

- n = 24 scheduled events;
- 24/24 data-valid;
- 12 CPI + 12 Employment;
- full actionability.

The rejection is therefore not caused by one zero-impulse event or an inadequate sample gate.

Postmortem structure:

- 14 large residual events;
- 8/14 wrong-or-zero direction;
- 6/14 captured >=20 bps;
- 0/14 in the category "correct sign but positive continuation <20 bps".

This supports the descriptive conclusion that sign failure dominates.

Family medians differ:

- CPI ~-12.14 bps;
- Employment ~+13.83 bps.

But these are post-outcome family descriptives on 12 events each.

They cannot justify a new family-specific rule on this chronology.

## 5. Why C11 is terminal now

Continuing C11 in place would require one or more of:

- a different impulse window;
- a different direction statistic;
- reversal;
- family-dependent sign;
- macro surprise;
- an order-flow/microprice extractor;
- a different entry delay.

Each is a materially different rule.

Testing any of them on the already-open Selection chronology would be outcome-driven redesign.

Therefore no in-place C11 v3 is authorized.

## 6. Future macro-direction research boundary

A future macro-direction strategy is not scientifically forbidden.

But it must satisfy all:

1. new experiment/candidate ID;
2. independently specified direction mechanism before outcome;
3. fresh Selection evidence not used for C11 design;
4. later untouched Confirmation;
5. explicit multiple-testing entry in the research ledger;
6. no use of C11 family descriptives as a hidden sign rule.

Examples of concept classes that might qualify only under a new design:

- independently sourced macro-surprise data with reproducible provenance;
- independently specified causal order-flow/microprice extractor;
- a structural hedge/inventory mechanism rather than directional prediction.

None is authorized by this review.

## 7. Reusable value retained

C11 supports a reusable:

`SCHEDULED_MACRO_EVENT_RISK_STATE`

because both contaminated H1 and fresh Selection show broad large movement around CPI/Employment releases.

Preferred roles:

- R2 regime/risk state;
- R3 veto;
- R5 execution/risk scheduler;
- R6 external calendar reference.

This state does not claim directional alpha.

## 8. Prospective Confirmation reserve

The 12 frozen prospective C11 Confirmation identities remain:

`UNOPENED / UNCONSUMED`

They must not be opened for C11.

They are not automatically reassigned to another candidate.

Any future reuse requires a new prospective contamination/source audit and explicit reassignment before the relevant outcomes are opened.

## 9. C13+ gate

The prior block:

`DO_NOT_OPEN_C13_PLUS_WHILE_C11_UNRESOLVED`

is now satisfied.

C13+ may move to **non-alpha design only**.

No new outcome is authorized merely by closing C11.

## 10. Recommended next research action

Return to the independent-base search framework.

Before any C13 price outcome:

1. update strategy/feature/reusable-block registries with C11 terminal knowledge;
2. construct at most three independent base concepts;
3. apply Edge-to-Fill structural review;
4. assign at most one or two new candidate IDs;
5. audit fresh evidence chronology;
6. freeze cheapest sentinel before outcome.

Do not make the next candidate a disguised C11 direction rescue.
