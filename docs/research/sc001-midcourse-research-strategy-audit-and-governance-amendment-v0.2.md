# SC001 — Mid-Course Research-Strategy Audit & Governance Amendment v0.2

Date: 2026-09-27
Status: **BINDING THREE-ROLE CRITICAL REVISION**
Supersedes:
`docs/research/sc001-midcourse-research-strategy-audit-and-governance-amendment-v0.1.md`

Scope:
`SCALPING RESEARCH / SC001`

## 1. Three-role review conclusion

The v0.1 audit is directionally correct and remains binding, but four refinements are necessary.

The review was performed from three roles:

1. financial-market expert / trader;
2. programmer-expert / trader;
3. mathematician-statistician.

The purpose is not to add process. It is to remove avoidable low-value research.

---

## 2. Financial-market / trader critique

### 2.1 Critique: longer horizon is not intrinsically better

A longer position horizon gives price more time to move, but it also adds:
- market beta exposure;
- regime-change risk;
- funding/borrow;
- inventory time;
- capital lock;
- basis drift;
- liquidation/tail exposure.

Therefore:

`LONGER HOLD != MORE EDGE`

B14-B is direct evidence:
a seven-day carry still produced only about +1.39 bps median gross carry.

### Binding correction

Horizon must be derived from:

`MECHANISM DECAY / PAYOUT CLOCK -> EXECUTION COST -> POSITION HORIZON`

not from:

`NEED MORE BPS -> HOLD LONGER`

Under-covered H2/H3 regions are research gaps only.

They may be used as a tie-breaker between otherwise comparable mechanisms, but must never receive priority merely because they are under-covered.

---

## 3. Financial-market / trader reinforcement: capital-time economics

Per-trade bps alone are insufficient.

Every candidate that survives structural headroom must also report:

- expected opportunity frequency;
- expected capital occupancy;
- expected gross/net edge per completed cycle;
- approximate edge per capital-day or equivalent capital-time measure;
- concurrent-position / collateral requirement;
- capacity constraint.

No universal hard annualized-return threshold is introduced here because strategy families differ materially.

Instead, capital-time economics is a **ranking/deprioritization dimension**.

A strategy can be individually profitable yet economically unimportant if:
- opportunities are extremely rare;
- capital is locked for long periods;
- capacity is tiny;
- operational overhead dominates.

This strengthens, but does not duplicate, the existing Edge-to-Fill preflight.

---

## 4. Financial-market / trader critique of MVH

### Problem

An unconditional p90 move can wrongly reject a strategy whose causal event deliberately targets rare tail movement.

Examples:
- macro release;
- forced liquidation;
- delisting/forced close;
- transferability outage.

### Binding correction: two-mode MVH

#### Mode A — ordinary/liquid-state mechanism

Use an unconditional or broadly state-conditioned movement envelope.

If broad movement at the proposed horizon is materially below the economic hurdle and no structural payer exists:

`REJECT_HORIZON_STRUCTURAL`

#### Mode B — structural/exogenous event mechanism

Use an **event-conditioned movement envelope**, but only from:
- non-promotional calibration;
- independent prior event family;
- source-only/economic reasoning where price outcomes remain unopened.

Do not use the protected promotional event set to choose the horizon.

The candidate card must state why the event can plausibly escape ordinary market movement scale.

### Key point

MVH is only a **necessary-condition upper-bound screen**.

It does not claim:
- predictability;
- tradability;
- directional edge.

---

## 5. Programmer-expert / trader critique

### 5.1 Critique: mechanism fingerprint can become subjective

A prose statement such as “this is different” is too easy to rationalize after prior failures.

### Binding correction

Every new outcome-bearing candidate must include a structured mechanism fingerprint with the following exact fields:

- parent/family lineage;
- economic payer;
- causal trigger/state;
- economic object(s);
- monetization path;
- entry architecture;
- exit/termination anchor;
- structural fill count;
- horizon class;
- latency dependency;
- capital/risk constraint;
- relationship to nearest prior mechanism.

Disposition must be one of:

- `INDEPENDENT_MECHANISM`;
- `RELATED_BUT_MATERIALLY_DIFFERENT_ARCHITECTURE`;
- `SAME_MECHANISM_VARIANT`;
- `DISGUISED_RESCUE_REJECT`.

Only the first two may reach a new outcome-bearing stage.

No retroactive fingerprint migration of every historical experiment is required.
Apply this prospectively to avoid work for work's sake.

---

## 6. Programmer-expert / trader reinforcement: implementation reuse

Do not build a new custom engine for each candidate when existing validated primitives apply.

Prefer versioned reusable kernel components for:
- half-open time windows;
- causal bar availability;
- strict-coactive synchronization;
- source identity/hash;
- event fingerprinting;
- source-gap censoring;
- cluster formation;
- cost/fill accounting;
- block-level result aggregation.

Candidate code should contain primarily:
- mechanism-specific state;
- mechanism-specific trigger;
- mechanism-specific accounting.

This reduces implementation variance and repeated bugs.

Do not refactor healthy frozen collectors merely to satisfy code-style preferences.

---

## 7. Programmer-expert / trader critique of feature augmentation

### Problem

The v0.1 phrase “far-below-hurdle failures should not be rescued with indicators” is correct for the completed evidence but too broad as a universal statement.

### Binding correction

Distinguish:

#### Same-evidence rescue

Forbidden.

Example:
B13-C fails on the protected interval, then liquidation size / RSI / volatility filters are searched on the same outcomes.

This remains prohibited.

#### New mechanism inspired by a reusable block

Allowed.

Example:
RB021 later becomes a prospectively defined liquidation-exhaustion state in a new architecture using fresh post-definition events.

This is not a rescue if:
- the new causal interaction is frozen first;
- the evidence window is fresh;
- the new mechanism/feature lineage is explicit.

Thus:

`FAILED PARENT != PERMANENT BAN ON ITS INFORMATION`

but:

`FAILED PARENT + SAME DATA TUNING = CONTAMINATED RESCUE`

---

## 8. Mathematician-statistician critique: adaptive research path

SC001 has explored many candidate families sequentially.

Even when each individual experiment is frozen correctly, the **research path itself is adaptive**:
later ideas are informed by earlier results.

Therefore a later positive Discovery is not independent of the overall search process.

### Binding correction: adaptive-discovery flag

Every candidate generated after observing prior SC001 outcomes is labeled:

`ADAPTIVE_DISCOVERY_GENERATED`

unless it demonstrably comes from a previously frozen queue independent of those results.

Consequence:
- a positive adaptive Discovery cannot be treated as Confirmation;
- it requires fresh chronological/prospective Confirmation before promotional claims;
- the number of explored mechanism/horizon/feature variants remains part of the multiplicity context.

This strengthens the existing rule:

`SELECTION_SURVIVE != CONFIRMATION`

without requiring formal p-value correction across economically heterogeneous strategies.

---

## 9. Mathematician-statistician critique: horizon search multiplicity

Testing 5s, 10s, 30s, 1m, 5m and keeping the best is parameter search, not six independent confirmations.

### Binding correction

Every outcome-bearing horizon considered counts toward the strategy-search budget.

Default practice:
- one primary horizon derived from mechanism timescale;
- optionally one separately justified secondary/stress horizon;
- no unrestricted horizon grid.

If calibration data select a horizon:
- that period is calibration only;
- the selected horizon requires fresh evidence.

---

## 10. Mathematician-statistician reinforcement: dependent observations

Existing block-level rules remain sufficient and should not be duplicated.

Binding interpretation:
- raw ticks are not IID;
- multiple events in one shock/regime may not be independent;
- strategy evidence must report the primary economic inference unit plus calendar/asset breadth;
- where uncertainty matters, use the already required block-aware uncertainty method.

No new generic “effective sample size” formula is imposed because dependence structure differs by mechanism.

---

## 11. No point-estimate promotion near the boundary

A candidate whose point estimate barely clears the cost/headroom hurdle is not automatically economically viable.

If a candidate reaches later Confirmation/execution stages near the boundary, require:
- cost stress;
- latency stress;
- block-level uncertainty;
- concentration/breadth;
- capital-time economics.

This is a robustness requirement, not a new sentinel gate.

Large negative structural gaps may still be rejected cheaply without expensive uncertainty modeling.

---

## 12. Updated practical research funnel

Use this order:

### G0 — Mechanism fingerprint
Is it actually new?

### G1 — Economic payer
Why should edge exist?

### G2 — Mechanism timescale
When should the information/payout decay?

### G3 — Edge-to-Fill
How many bps are required after fills/costs/reserve?

### G4 — Two-mode MVH
Can the proposed horizon plausibly contain that scale?

### G5 — Capital-time economics
Would a survivor be economically relevant given frequency and capital lock?

### G6 — Source/semantic feasibility
Can it be measured causally?

### G7 — Minimum base sentinel
Test the smallest mechanism-defining architecture.

### G8 — Failure decomposition + reusable-block extraction
Do not throw away valid information.

### G9 — Augmentation eligibility
Only prospectively justified feature work.

### G10 — Fresh Confirmation / forward
Mandatory for adaptive discoveries.

---

## 13. Three-role verdict on the user's concerns

### Concern 1 — too-short horizons

`VALID CONCERN / PROCESS STRENGTHENED`

But do not replace a short-horizon bias with a long-horizon bias.

Correct principle:

`MECHANISM TIMESCALE + EDGE-TO-COST -> HORIZON`

### Concern 2 — repeated same mechanism

`VALID CONCERN / STRUCTURED FINGERPRINT NOW REQUIRED`

Threshold/lookback/horizon changes alone do not create a new strategy.

### Concern 3 — indicators might repair weaknesses

`VALID WITH CONDITIONS`

Use incremental indicators only when economically and causally justified.

Same-data rescue is forbidden.

Fresh new mechanisms inspired by reusable blocks are allowed.

### Concern 4 — custom indicators

`VALID AND DESIRABLE`

Build them from causal economic primitives and accumulated reusable evidence, not from historical PnL optimization.

---

## 14. Immediate B15-P2 consequence

The sealed B15-P2 Bybit source-census offline self-test remains valid.

Why:
- it opens no price;
- it chooses no trading horizon;
- it only validates event/source semantics.

Do not design B15-P2 price outcome until:
- structured mechanism fingerprint;
- mechanism-timescale statement;
- Edge-to-Fill;
- two-mode MVH;
- capital-time implications
are frozen.

No need to rebuild or reseal the current source-only self-test.
