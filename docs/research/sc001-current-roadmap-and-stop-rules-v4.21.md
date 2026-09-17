# SC001 Current Roadmap and Stop Rules v4.21

Date: 2026-09-17  
Status: **CURRENT SC001 ROADMAP — FEATURE/INDICATOR GOVERNANCE FROZEN / CANDIDATE FEATURE-INVENTORY STAGE OPEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.20.md`

## 1. Binding terminal states

E001-E008 remain terminal/closed.

E007R1 remains terminal:
`E007R1_GROSS_FEASIBILITY_FAIL`.

E009 remains terminal:
`E009_GROSS_FEASIBILITY_FAIL`.

E009 postmortem remains complete.

No prior strategy is reopened by feature/indicator research.

## 2. Binding top-level governance

Current entry point:
`docs/research/sc001-strategy-selection-time-horizon-mechanism-and-feature-framework-v0.3.md`

Binding companions:

- `docs/research/sc001-feature-indicator-research-governance-v0.1.md`;
- `docs/research/sc001-feature-indicator-taxonomy-v0.1.md`;
- `docs/research/sc001-incremental-feature-testing-protocol-v0.1.md`;
- `docs/research/sc001-feature-evidence-registry-v0.1.md`;
- `docs/research/sc001-legacy-retest-and-replication-policy-v0.1.md`;
- `docs/research/sc001-strategy-landscape-v0.1.md`;
- `docs/research/sc001-candidate-feasibility-card-template-v0.2.md`;
- `docs/research/sc001-next-generation-multi-asset-research-framework-v0.3.md`;
- `docs/research/sc001-simulation-verification-and-accounting-standard-v0.1.md`.

## 3. Feature/indicator research finding

SC001 will now accumulate two linked forms of evidence:

1. strategy-mechanism evidence;
2. scoped feature/indicator evidence.

The feature layer is not a global indicator leaderboard.

No statement such as `RSI works`, `ATR does not work`, or `VWAP works` is allowed without scope.

Evidence must specify feature/version, role, market, horizon, mechanism, chronology and execution/cost stage.

## 4. Feature roles

Every future feature declares one or more roles:

- R1 core signal;
- R2 state/regime;
- R3 filter/veto;
- R4 sizing/risk;
- R5 execution;
- R6 reference/normalization.

A feature may fail in one role and remain useful in another.

## 5. Feature taxonomy and redundancy

Feature families are grouped by economic primitive rather than popular name.

Current primitive taxonomy P1-P11 covers:

- price/return location;
- trend/persistence;
- volatility/range;
- volume/activity;
- aggressive flow;
- order-book/liquidity;
- reference/fair-value transforms;
- relative value/derivative state;
- cross-asset information transfer;
- forced-flow/event state;
- calendar/session/structural context.

Related indicators are not independent discoveries.

## 6. Feature Evidence Registry bootstrapped

The append-only registry now contains scoped bootstrap evidence from completed SC001 work including:

- TFI/aggressive-flow information;
- volatility-compression state;
- spot/perp basis dislocation;
- 60-second displacement reversal;
- VWAP/reference use;
- visible spread/liquidity state;
- robust MAD volatility normalization;
- passive queue-ahead execution modeling.

Whole-strategy failures are not converted into global feature failures unless the feature was isolated.

## 7. Legacy retest policy unchanged

Do not rerun all old strategies.

- E001 no direct retest;
- E002 no standalone retest; auxiliary reuse only under new ID;
- E003 no direct retest;
- E004/E005 no direct retest;
- E006R1 strict multi-asset replication remains scientifically justified subject to cheap sentinel;
- E007/E007R1 no further direct retest;
- E008 no BTC same-rule retest;
- E009 no direct retest.

## 8. Candidate slate remains C1-C6

Non-alpha cards exist for:

- C1 E006R1 multi-asset basis;
- C2 multi-minute deviation/VWAP mean reversion;
- C3 5m/10m continuation/volatility expansion;
- C4 BTC/ETH -> alt lead/lag;
- C5 large-trade/sweep/forced-flow exhaustion;
- C6 cross-sectional short-horizon dispersion/reversion.

C7 wider-spread maker remains reserve/lower priority.

## 9. Current work stage

Before sentinel design, update C1-C6 using candidate-card template v0.2 with:

- exact primitive families;
- minimum mechanism-defining feature set;
- optional auxiliary features;
- core vs auxiliary role;
- likely redundancy;
- causal availability;
- feature parameter/interaction budget;
- previous registry evidence;
- contamination status.

Do not add indicators because they are popular.

## 10. Selection/Calibration Sandbox rule

Any data used to choose:

- feature family;
- parameter;
- normalization;
- feature interaction;
- custom composite;
- strategy horizon;
- filter threshold;

becomes non-promotional for that resulting implementation.

All variants considered, including human/LLM proposals, enter the research ledger.

## 11. Incremental feature testing

Where relevant, pre-register:

`BASE` vs `BASE + FEATURE`.

Prefer same baseline opportunity set.

Filter/veto tests must report both per-trade economics and economics per original base opportunity plus opportunity-retention rate.

If augmentation materially changes the mechanism/opportunity definition, it becomes a new strategy experiment ID.

## 12. Custom-indicator rule

Proprietary features are allowed only if they target a defined economic primitive and have:

- simpler comparator;
- exact formula/version;
- causal inputs;
- complexity/interaction budget;
- falsification rule;
- fresh promotional evidence after design.

No direct formula optimization against promotional PnL.

## 13. Current hard gate

**NO NEW PROMOTIONAL ALPHA.**

Allowed now:

1. finish Feature / Indicator Inventory for C1-C6;
2. define Selection/Calibration Sandbox periods/permissions;
3. define one cheapest sentinel per candidate;
4. estimate MDE/sample requirements prospectively;
5. review structural feasibility and redundancy;
6. freeze a small diversified research batch;
7. only then assign/freeze exact new experiment IDs and authorize alpha/data stages.

## 14. Immediate next action

Create C1-C6 Feature / Indicator Inventory update using template v0.2, then design sentinel/kill conditions without opening new promotional outcomes.
