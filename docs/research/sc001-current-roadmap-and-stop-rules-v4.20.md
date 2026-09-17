# SC001 Current Roadmap and Stop Rules v4.20

Date: 2026-09-17  
Status: **CURRENT SC001 ROADMAP — STRATEGY-SELECTION v0.2 FROZEN / NON-ALPHA CANDIDATE CARD STAGE OPEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.19.md`

## 1. Binding terminal states

E001-E008 remain terminal/closed.

E007R1 remains terminal:
`E007R1_GROSS_FEASIBILITY_FAIL`.

E009 remains terminal:
`E009_GROSS_FEASIBILITY_FAIL`.

E009 read-only postmortem is complete:
`E009_READONLY_POSTMORTEM_PASS`.

No prior terminal state is reopened by the new strategy-selection framework.

## 2. Binding strategy-selection framework

Current governing framework:

`docs/research/sc001-strategy-selection-time-horizon-and-mechanism-framework-v0.2.md`

Companion artifacts:

- `docs/research/sc001-legacy-retest-and-replication-policy-v0.1.md`;
- `docs/research/sc001-strategy-landscape-v0.1.md`;
- `docs/research/sc001-candidate-feasibility-card-template-v0.1.md`;
- existing `docs/research/sc001-next-generation-multi-asset-research-framework-v0.3.md`;
- existing `docs/research/sc001-simulation-verification-and-accounting-standard-v0.1.md`.

## 3. New binding findings after second three-role red-team

### Financial/economic

- under-covered horizons are information gaps, not evidence of alpha;
- candidate selection must include break-even move, cost floor, edge/cost reserve, opportunity frequency and capital-time usage;
- average bps/trade alone is insufficient;
- structural edge payer/persistence thesis is mandatory.

### Trader/programmer

- one “timeframe” label is insufficient;
- signal clock and execution clock are separate;
- final bar data are unavailable until bar close;
- same-bar OHLC look-ahead is prohibited;
- use minimal sufficient data before heavy L2;
- causal half-open windows, lineage and reference implementation are mandatory.

### Mathematical/statistical

- strategy-selection diagnostics can contaminate evidence even when not called PnL;
- Selection/Calibration Sandbox data are permanently non-promotional for that implementation;
- sample design must use an economically meaningful effect floor/MDE and independent block logic rather than a universal trade count;
- sequential research multiplicity and optional stopping require explicit ledger/stop rules;
- diversity applies only after structural feasibility.

## 4. Legacy retest decision

Do not rerun all old strategies.

Binding summary:

- E001: no direct retest;
- E002: no standalone retest; auxiliary reuse only under new ID;
- E003: no direct retest;
- E004/E005: no direct retest;
- E006: strict multi-asset E006R1 replication is scientifically justified, subject to cheap feasibility first;
- E007/E007R1: no further direct retest;
- E008: no BTC same-rule retest; new spread/fee-eligible maker universe only under a new ID;
- E009: no direct retest.

## 5. Current strategy landscape

Completed evidence is dense in:

- sub-minute/event-driven S0-S2;
- M1 order flow;
- M2 BTC maker/spread capture;
- M3 short displacement reversal;
- M4 short continuation/breakout;
- T1 directional taker.

Under-covered:

- S3-S4 signal horizons (1-10 min);
- P3-P4 holding horizons (5-30 min);
- M5 broader multi-asset relative value;
- M6 cross-asset information transfer;
- M7 forced-flow/event mechanisms;
- low-beta cross-sectional/paired risk signatures.

Under-coverage does not grant a candidate promotion by itself.

## 6. Candidate slate for non-alpha cards

Prepare standardized cards for:

- C1 — E006R1 multi-asset spot/perp basis convergence;
- C2 — multi-minute deviation / VWAP-style mean reversion;
- C3 — 5m/10m continuation or volatility expansion;
- C4 — BTC/ETH -> alt lead/lag;
- C5 — large-trade / sweep / forced-flow exhaustion;
- C6 — cross-sectional short-horizon dispersion/reversion.

C7 wider-spread maker remains reserve/lower priority and does not need immediate heavy work.

## 7. Current hard gate — NO NEW PROMOTIONAL ALPHA

Allowed now:

1. non-alpha candidate cards;
2. historical data-availability / metadata checks that reveal no strategy outcome;
3. conservative cost-structure analysis;
4. Selection/Calibration Sandbox design and contamination freeze;
5. prospective MDE/sample planning;
6. cheapest sentinel design.

Not allowed yet:

- promotional PnL/backtests for C1-C7;
- selecting symbols because of previous strategy winners;
- opening new holdout/Confirmation evidence;
- heavy L2 download without candidate structural feasibility;
- parameter tuning from fresh promotional data.

## 8. Candidate workflow

For each C1-C6:

1. complete candidate card;
2. apply structural gates: causality, cost plausibility, data availability, execution identifiability, sample feasibility, capital/venue feasibility;
3. if needed, define Selection Sandbox and permanently mark it contaminated;
4. define prospective MDE/sample requirement;
5. define cheapest sentinel falsification and kill condition;
6. classify card as `REJECT_STRUCTURAL`, `HOLD_INFORMATION_VALUE`, or `ELIGIBLE_FOR_BATCH` before promotional alpha.

## 9. Batch selection rule

Among structurally feasible candidates, choose a small Pareto-efficient research batch spanning materially different horizon/mechanism/execution/risk cells.

Do not use a single arbitrary weighted score.

Before first batch promotional outcome, freeze each selected experiment's:

- new ID;
- exact time architecture;
- universe rule;
- contamination roles;
- tuning budget;
- cost/headroom gates;
- MDE/sample plan;
- Discovery;
- asset holdout if applicable;
- chronological Confirmation;
- one-shot stop rules.

A result from one batch member may not retroactively redesign another member under the same ID.

## 10. Immediate execution order

Step 1 — complete `sc001-strategy-landscape-v0.1.md` (DONE).

Step 2 — complete standardized non-alpha feasibility cards for C1-C6 (OPEN).

Step 3 — structural feasibility comparison / Selection Sandbox requirements.

Step 4 — freeze the first small research batch.

Step 5 — only then authorize metadata/data acquisition and alpha-specific protocols.

SC001 remains independent from all principal frozen BotMarketplace branches.
