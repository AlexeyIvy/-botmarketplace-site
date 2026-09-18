# SC001 — C7-C10 Post-Slate Mechanism & Building-Block Synthesis v0.1

Date: 2026-09-18
Status: **NON-ALPHA SYNTHESIS / NO NEW OUTCOME AUTHORIZED**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-strategy-selection-time-horizon-mechanism-and-feature-framework-v0.3.md`;
- `docs/research/sc001-c1-c6-second-pass-knowledge-extraction-audit-v0.1.md`;
- `docs/research/sc001-feature-evidence-registry-v0.6.md`;
- `docs/research/sc001-reusable-market-building-blocks-registry-v0.5.md`;
- `docs/research/sc001-strategy-landscape-v0.6.md`.

## 1. Purpose

The C7-C10 slate is complete with zero survivors.

Before creating any C11+ strategy IDs, consolidate what is now known about:

- economic mechanisms;
- reusable measurements;
- evidence maturity;
- headroom relative to fill structure;
- promising feature roles;
- overfitting risks;
- next candidate-design constraints.

This document opens no new alpha and changes no terminal verdict.

## 2. Main empirical pattern across SC001

The central repeated result from C1-C10 is:

`valid causal measurements often exist, but standalone gross edge/headroom is too small for the chosen execution architecture`.

Examples:

- C4 residual information: small positive but sub-bps;
- C5 exhaustion state: small positive, possible microstructure bounce;
- C6 cross-sectional residual rank: strongest direct positive block, but low-single-digit bps;
- C9 funding-state normalization: essentially zero;
- C8B transient cross-venue basis: low-single-digit bps at p99, insufficient for four fills;
- C10 L2 vacuum: weak positive signed tendency and rare tails, but p90 far below two-fill hurdle;
- C7 quoted spread: too tight to support maker-entry/taker-exit reserve.

Therefore the next generation should not search for another isolated predictor with multiple new fills.

## 3. Most promising reusable blocks by role

### A. R6 reference / normalization — strongest and safest

High-value methodology/state primitives:

- RB004 residualization;
- RB008 causal local reference;
- RB012 causal local cross-venue basis reference;
- RB015 side-specific depth normalization;
- RB017 causal quoted-spread state.

These are not alpha by themselves, but they materially improve measurement correctness and reduce false signals.

### B. R2 state/regime — useful contextual information

Potentially useful state blocks:

- RB002 expansion/breakout state;
- RB007 continuous basis state;
- RB009 scheduled funding-event context;
- RB010 mark/index premium state;
- RB011 strict-coactive cross-venue basis;
- RB014 near-touch depth state;
- RB016 one-sided liquidity-vacuum onset;
- RB018 persistent high-spread regime, with current 10-bps state strongly negative/rare.

### C. R3/R5 filter/execution context — potentially attractive because they add no new fills

The strongest design opportunity is to use weak predictive blocks as **veto/timing/execution** information for an independently valid base opportunity.

Candidates for this role include:

- RB001 persistence/opposite-sign local deviation hypothesis;
- RB003 leader-impulse residual context;
- RB005 aggressive-flow exhaustion / anti-chase state;
- RB016 liquidity-vacuum onset.

This matches the edge-to-fill lesson: a 0.5-3 bps information block may be useless as a standalone two/four-fill strategy but still valuable if it avoids a bad trade or improves execution without adding fills.

### D. Ranking/state

RB006 cross-sectional residual rank remains the strongest directly positive C1-C6 calibration block.

Its best future use is not a rewrite of C6, but an R2/R3 ranking input inside a materially different architecture with already-required fills.

## 4. What should NOT become the next candidate

Do not create a new candidate merely by:

- reversing C2;
- lowering C1 basis threshold;
- lowering C7 spread threshold;
- isolating C10 rare large-move tails;
- lowering C8B dislocation hurdle;
- combining C5 + C10 because both concern stress/liquidity;
- summing historical mean effects across RB blocks.

Those would be post-hoc rescue paths or hidden multiplicity.

## 5. Next-candidate design principle

Future candidates should satisfy all:

1. **Independent base mechanism**  
   The base economic opportunity exists without relying on a weak historical feature.

2. **Low incremental fill cost**  
   New features should preferably act as:
   - veto,
   - timing,
   - ranking,
   - state,
   - sizing,
   - execution mode choice,
   rather than create additional entry/exit legs.

3. **Prospective interaction hypothesis**  
   A combination is allowed only when there is a stated mechanism explaining why one block changes the usefulness of another.

4. **Small interaction budget**  
   Ordinary SC001 candidate:
   - one base mechanism;
   - at most one primary auxiliary block;
   - optionally one execution/risk veto;
   - no combinatorial search.

5. **Fresh evidence after design**  
   Any period used to choose the combination becomes nonpromotional.

## 6. Three candidate-family archetypes worth designing next

These are design directions only, not frozen candidates and not authorized experiments.

### Family N1 — Execution-veto architecture

Question:

> Can an independently defined opportunity be improved by refusing entry during adverse microstructure states?

Candidate blocks:

- RB005 aggressive-flow exhaustion / anti-chase;
- RB016 liquidity-vacuum onset;
- RB017 quoted-spread state.

Why attractive:

- features may improve realized execution/risk without adding fills;
- weak directional bps can still be economically relevant as a veto.

Requirement:

The base opportunity must be defined independently and must not be one of the rejected C1-C10 rules in disguise.

### Family N2 — Relative ranking with one-sided execution

Question:

> Can RB006 cross-sectional residual rank drive a one-sided allocation/ranking decision where the economic architecture requires only the trade that would exist anyway, rather than a four-fill convergence cycle?

Why attractive:

- RB006 had the strongest directly positive calibration evidence;
- ranking may convert relative information into lower fill-count action.

Requirement:

Must be a genuinely new architecture, not a cheaper rewrite of C6.

### Family N3 — Regime-dependent execution-mode choice

Question:

> Can R2/R6 market-state features choose between maker/taker/no-trade modes for an independent base opportunity?

Candidate state primitives:

- RB007 continuous basis;
- RB009 funding clock;
- RB014/RB015 depth state;
- RB017 spread state.

Why attractive:

- uses measurements with high validity;
- aims to reduce execution cost rather than predict return directly.

Requirement:

Must freeze the base opportunity and mode-selection logic before opening outcome data.

## 7. Priority ordering for design work

Preferred next research work:

1. design N1/N2/N3 candidate cards without outcomes;
2. evaluate data availability and contamination cost;
3. reject any family requiring expensive proprietary data or many new fills;
4. select at most 2-3 orthogonal candidates;
5. freeze cheapest sentinels before any outcome.

Do not assign C11/C12/C13 until the cards pass non-alpha feasibility review.

## 8. Stop condition

If no N1/N2/N3 design can produce a plausible:

`information scale / fill-cost architecture`

without hidden rescue of C1-C10, stop SC001 candidate expansion and preserve the research as negative/feature evidence rather than forcing another backtest.
