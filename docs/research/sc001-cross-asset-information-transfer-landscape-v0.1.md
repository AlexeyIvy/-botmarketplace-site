# SC001 — Cross-Asset Information-Transfer Landscape v0.1

Date: 2026-10-03
TASK_ID: SC001-X1-001
WORKER_ID: X1_CROSS_ASSET_STRUCTURE
Authorization: DESIGN_ONLY
Terminal recommendation: CROSS_ASSET_STATIC_DEFER_SOURCE
Selected future candidates: 0
Adaptive status: ADAPTIVE_DISCOVERY_GENERATED
Origin: Issue #419 / PR #427
Canonical main reviewed: 0889832f94868537e6aa9487b0b8e9b50af7ab6e
Exact task blob: 01b492150e23a2a3e667824469d5a1834751babc
Assigned branch: sc001/x1/SC001-X1-001

## Decision

No new outcome-bearing cross-asset candidate is ready. Three static families were considered, with no parameterizations, pair search, symbol selection, horizon tests, acquisition or outcome computation. Labels A/B/C below are local table labels, not experiment IDs.

A is a C4 mechanism variant; B is a C6 mechanism variant. C has a different hypothetical payer, but the permitted canonical source knowledge does not establish an identifiable observable product, causal historical event record or mandatory transmission channel. C is deferred at source/mechanism-identification level, not selected for a future experiment. The overall token is DEFER_SOURCE because the only potentially distinct family remains unqualified; it does not reopen A or B.

This is not a universal claim that cross-asset research cannot work. It is a bounded conclusion about these architectures under the current public-source and execution constraints. Candidate 2 remains the existing reserve; it is neither duplicated nor executed.

## Three-family static ledger

### A — Liquid leader flow to another asset

- Economic payer / causal story: a common information shock is incorporated first in a liquid leader; slower counterparties in a related target may subsequently update. Aggressive leader flow is a possible observable representation, not proof of a new payer. No compulsory buyer or guaranteed delay is established.
- Source and target: source BTC/ETH leader return/flow; target other liquid crypto perpetuals. These are lineage objects from C4, not a newly selected universe.
- Expected timescale: short information-incorporation delay, seconds to at most the legacy minute scale. No new numerical response horizon is proposed or tested.
- Monetization / entry: one-sided target continuation only after leader information is actually available; leader is observation-only.
- Exit/termination: information-incorporation expiry, not an outcome-chosen holding extension.
- Structural fills: 2 for a standalone target entry and exit. A later hedge adds fills and cannot be credited for free.
- Capital-time: short occupancy but directional/common-shock exposure; repeated events overlap and can concentrate collateral. Net edge and edge per capital-day are unestimated.
- Frequency prior: plausibly many observable impulses per day in liquid assets, qualitatively; qualified independent and actionable opportunities are unknown. No event count was measured.
- Public-data feasibility: canonical trade-archive and causal-window primitives exist, but an exact fresh cross-asset coverage/receive-time qualification does not follow from them.
- Latency: high; event-time ordering alone can manufacture an apparent leader. Both source availability and target tradability must be later qualified.
- Cheapest falsification: the current fingerprint comparison already fails novelty. No new price test is justified for this version. A future distinct proposal would first need a different payer/architecture, then source-only causal availability proof.
- Edge-to-fill: legacy C4 summaries describe sub-1-bps residual information, not a new edge estimate. There is no independent reason here for materially larger scale or free execution. Status: STRUCTURALLY_IMPLAUSIBLE as a newly labeled standalone revival.
- Disposition: SAME_MECHANISM_VARIANT relative to C4. Replacing leader returns with flow alone is insufficient: the canonical C4 inventory already includes return/flow state. Same-window tuning would be DISGUISED_RESCUE_REJECT.
- Decision: REJECT_OVERLAP; retain RB003 as prospective context and RB004 as reference only.

### B — Common-factor residual convergence across a fixed universe

- Economic payer / causal story: transient relative inventory pressure is expected to be absorbed by liquidity providers/relative-value participants. A statistical residual is not itself an economic obligation to converge.
- Source and target: a fixed common-market benchmark/reference plus relative over/under-movers in an ex ante universe. Sector labels are a possible universe restriction, not a fourth mechanism.
- Expected timescale: minutes over which temporary inventory pressure is hypothesized to normalize; legacy C6 reviewed a 15-minute response. That legacy value is not newly selected or extended here.
- Monetization / entry: simultaneous exposure to the under- and over-moving legs after a causally available residual state.
- Exit/termination: relative normalization or a prospectively bounded expiry; neither is optimized here.
- Structural fills: minimum 4 for a two-leg paired round trip; trading more constituents or rebalancing adds fills. Dropping a hedge after seeing prior results is not an architectural innovation.
- Capital-time: two-leg collateral, legging and beta-model risk with minute-scale occupancy; hedge maintenance can add turnover. No capital-day profitability estimate is available.
- Frequency prior: rankings can be calculated repeatedly, but repeat ranks are not independent opportunities. Actual qualifying frequency and capacity remain unknown.
- Public-data feasibility: synchronized historical trades or completed derived candles could represent the state if exact point-in-time membership and data availability are established. Present-day membership is inadequate.
- Latency: less dependent on subsecond speed than A, but asynchronous bars, last-price carry-forward and unavailable betas can create false residuals.
- Cheapest falsification: static overlap with C6 is sufficient to stop this architecture. Changing benchmark, sector subset or volatility scale does not justify a new outcome test.
- Edge-to-fill: prior scoped C6 summaries report only a few bps against its frozen four-fill hurdle. That is a parent limitation, not an estimate on new data. Status: STRUCTURALLY_IMPLAUSIBLE for direct standalone revival.
- Disposition: SAME_MECHANISM_VARIANT relative to C6. Lowering turnover/fill assumptions without an independently specified opportunity would be DISGUISED_RESCUE_REJECT.
- Decision: REJECT_OVERLAP; preserve RB004/RB006 as normalization/risk/ranking primitives under fresh, separately justified use.

### C — Contractually constrained basket-allocation flow to constituents

This is a schematic economic hypothesis, not a claim that a particular accessible crypto product or historical dataset has been found.

- Economic payer / causal story: if a funded tracker or other contractually constrained allocator must change constituent holdings under a publicly specified basket rule, its non-discretionary orders could transmit demand to constituent markets. Index publication alone does not force any trade. A cash-settled reference, optional dealer hedging or a merely correlated sector basket does not establish this payer.
- Source and target: source would have to be an identified basket product, historical weight/units changes and a causal public effective/announcement clock; targets would be the actual required constituents and only semantically qualified tradable equivalents. No instrument, venue, pair or constituent set is selected.
- Expected timescale: the documented implementation/hedging interval of that actual obligation. It cannot be inferred from a generic price correlation or from a desire for more bps; therefore no numeric horizon is proposed.
- Monetization / entry: hypothetical one-sided constituent response to a signed, already public mandatory allocation change. If the position can only be entered after the flow has completed, the hypothesized monetization fails.
- Exit/termination: documented completion of the mandatory flow, not a chosen return peak.
- Structural fills: 2 per one-sided constituent round trip; at least 4 if hedged with a basket/other leg; a basket of n separate constituents needs at least 2n fills before hedging/rebalance. These are accounting bounds, not selected execution forks.
- Capital-time: exposure during an as-yet-unidentified implementation window, with event concentration, anticipation, funding/basis and inventory risk. Capital occupancy and edge per capital-day cannot be quantified.
- Frequency prior: unknown and potentially episodic. No basis exists to claim many daily opportunities or suitability as the frequent-market primary.
- Public-data feasibility: UNQUALIFIED. The references examined contain no verified causal historical basket membership/weight vintage, required-flow record or exact tradable transmission map for this hypothesis.
- Latency: announcement time, publication/receipt time and effective time must be distinct. A revised weight file with only today's timestamp cannot establish historical availability. Anticipation may exhaust the opportunity before public access.
- Cheapest falsification: a separately authorized documentation-only gate must identify one concrete product and prove both a mandatory transmission rule and an as-published historical clock. Absent either, stop before market bodies. No such external lookup or acquisition was performed here.
- Edge-to-fill: UNKNOWN_NEEDS_NON_ALPHA_DATA. Neither a magnitude nor a conservative product-specific fee/capital profile is established; plausible forced flow is not a static economic PASS.
- Disposition: INDEPENDENT_MECHANISM in the limited conditional fingerprint sense relative to the reviewed C4/C6/Candidate 2 architectures. This is not proof that an accessible instantiated mechanism exists.
- Decision: DEFER_SOURCE; NOT_SELECTED. No fingerprint-draft output, fresh-window allocation or experiment ID is warranted.
- CROSS_DOMAIN_REFERRAL: a future scheduled-event/announcement version belongs to Strategy Manager for P1 ownership review before dispatch. X1 has only recorded its cross-asset transmission/source question; no P1 work or alternate event program is authorized.

## Structured mechanism-overlap comparison

| Local family | Nearest C4 relationship | Nearest C6 relationship | Candidate 2 relationship | Other relevant relatives / invariant |
|---|---|---|---|---|
| A | SAME_MECHANISM_VARIANT: same leader-to-alt information incorporation, including flow inputs, common-factor adjustment and two-fill target path | Different trigger from residual rank; using ranks as target selection would not establish new payer | Related information propagation, but Candidate 2 is fixed same-underlying OKX-to-Bybit flow at 2 seconds. Swapping A to that architecture duplicates an existing reserve | E002/RB003: signed flow or weak lead context is not standalone taker economics. C8A broad directional fork is not a new freeze |
| B | Common-factor reference shared with C4, but paired relative convergence differs from leader continuation | SAME_MECHANISM_VARIANT: same residual rank, paired monetization and normalization premise | Different object from Candidate 2; changing to one-sided delayed flow would require a new fingerprint, not relabeling residual convergence | C1 and C8B are related paired-convergence architectures with different economic objects. Threshold/subset or four-to-two-fill changes alone cannot rescue any of them |
| C | INDEPENDENT_MECHANISM conditionally: mandatory portfolio allocation versus inferred leader information | INDEPENDENT_MECHANISM conditionally: specified demand obligation versus statistical mean reversion; sector rank alone collapses back to B | INDEPENDENT_MECHANISM conditionally: required constituent allocation versus same-asset venue-fragmented price discovery | C9 uses funding/mark-index state, not mandatory basket constituent trades. B14-B is funding carry, not constituent allocation. Candidate 1/B13-C concerns venue-local liquidation, not basket flow. Substituting liquidation/funding events would change scope and require referral |

Mechanism changes limited to horizon, lag, threshold, asset subset, reference transform or fee optimism are not counted as new families. Candidate 2 is compared, not evaluated as a fourth new candidate. No C8B/Candidate 2 response body, protected P1 evidence or terminal market window was opened.

## Evidence and decision limits

Only canonical task/governance documents, published legacy summaries, source/clock summaries and repository metadata were read. Legacy summary values encountered are lineage/economic-context evidence only; they are not new outcomes, clean Discovery, Confirmation, or prospective evidence. No raw rows, response calculation or performance-driven selection occurred.

No family survives selection, so there is no proposed untouched historical allocation and no new primary horizon. Inventing calendar dates or asserting cleanliness without a prior-use audit would create false precision. A later separately authorized candidate would require exact dataset identity, prior-use/contamination clearance, source clock qualification, one mechanism-derived horizon, an explicit bounded universe, resource review and prefreeze before any body access. Positive adaptive Discovery would still require fresh chronological/prospective Confirmation.

Current primary and Candidate 2 evidence boundaries remain untouched. No shared-state change is proposed as a prerequisite to accept this result.

## Reusable knowledge review

- Exact failed architectures: A repeats C4 standalone leader continuation; B repeats C6 paired residual convergence. Both fail novelty and retain inherited economic limitations. C has not failed an outcome test; its actionable source and obligated-flow identity are unqualified.
- Existing scoped components retained: RB003 (R2/R3 context), RB004 (R6 common-factor residualization), RB006 (R4/R6 and separately justified ranking), and qualified strict-coactive clock/reference primitives RB011/RB012 where their original scope applies.
- No new empirical component was validated: NO_REUSABLE_BLOCK_IDENTIFIED for new registration. Existing blocks are cited, not modified or promoted.
- Forbidden claims: correlation proves transfer; residualization creates alpha; clock PASS proves live latency/fills; static payer story proves economic scale; prior summaries establish a clean new window.
- Fresh reuse: define independent base opportunity, exact feature role and interaction budget before separately authorized fresh evidence; no parent-window rescue.

## Three-lens self-review

Financial/trader: A/B lack a new payer and cannot escape parent costs by relabeling. C identifies what a payer would have to be but does not establish frequency, capacity or headroom.
Engineering/trader: clock qualification is scoped; event time is not receive time. C needs source vintage and mandatory-transmission semantics before prices. No new engine/collector is justified.
Mathematical/statistical: three static hypotheses, zero tested variants, zero selected candidates. Correlated observations, basket events and calendar blocks are not IID ticks. No statistical significance or profitability claim is made.

## Authorized handoff

Strategy Manager may accept this bounded defer and keep C4/C6 closed. Any future source-only investigation of C requires a new exact task and, for an event-centered design, a CROSS_DOMAIN_REFERRAL routing decision. No follow-up run is authorized by this document.

MERGE_AUTHORIZED: false
SHARED_STATE_WRITE_AUTHORIZED: false
PROPOSED_SHARED_STATE_CHANGE: NONE
STRATEGY_REVIEW_REQUIRED: true

## Canonical references

- tasks/sc001-x1-001-cross-asset-static-feasibility.json (exact PR task)
- sc001-c1-c6-feature-indicator-inventory-v0.1.md
- sc001-c1-c6-five-role-reusable-mechanism-feature-review-v0.1.md
- sc001-reusable-market-building-blocks-registry-v0.1.md and v0.9.md
- sc001-reserve-candidate2-cross-venue-causal-flow-static-feasibility-card-v0.1.md
- sc001-strategy-manager-portfolio-review-v0.1.md
- sc001-c9-scheduled-funding-mark-index-feasibility-card-v0.1.md
- sc001-midcourse-research-strategy-audit-and-governance-amendment-v0.2.md
- sc001-edge-to-fill-structural-preflight-v0.1.md
- sc001-terminal-experiment-reusable-block-extraction-policy-v0.1.md
- sc001-cross-asset-source-and-clock-feasibility-v0.1.md (companion output)
