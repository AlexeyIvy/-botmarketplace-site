# Flagship Strategies — Implementation Roadmap (Issue-ready)

**Project:** BotMarketplace  
**Repository:** `AlexeyIvy/-botmarketplace-site`  
**Status:** Planning — based on current public code and docs (March 2026)  
**Author role:** Senior Software Engineer / Trading Systems Architect  
**Scope:** Turn the flagship strategy program into an execution-ready implementation backlog for engineering.  
**Change type:** Docs-only planning document. No code changes in this document.

---

## 1. Purpose

This document converts the flagship strategy analysis into an implementation roadmap in a format suitable for GitHub Issues.

It is designed to answer five practical questions for each stage:

1. What exactly needs to be built
2. Which files are expected to change
3. Which data model / API changes are required
4. Which tests are mandatory
5. What acceptance criteria define “done”

This document should be used as the execution bridge between:
- strategy concept docs in `docs/strategies/`
- the current Strategy DSL in `docs/10-strategy-dsl.md`
- the current bot runtime in `docs/11-bot-runtime.md`
- the current Lab compiler / backtest implementation in `apps/api` and `apps/web`

---

## 2. Current diagnosis

The project already has a good product and documentation foundation, but the flagship strategies are not yet executable end-to-end.

### 2.1 Core gaps

| Gap | Why it matters |
|---|---|
| Backtest engine does not execute the actual DSL strategy | Current backtests are not valid strategy verification |
| Compiler covers only a narrow subset of blocks | UI can express more than backend can compile |
| Runtime does not evaluate DSL into autonomous trading intents | Bot lifecycle exists, but strategy execution core is incomplete |
| No proper automated test harness for strategy logic | Unsafe for trading system evolution |
| No full position domain (`Position`, average entry, PnL, reconciliation) | Impossible to run advanced strategies safely |
| No exchange normalization layer | Backtest/runtime/live behavior can drift from real Bybit rules |

### 2.2 Strategic principle

The roadmap is built around one rule:

```text
Graph/UI → Compiler → DSL Schema → Backtest Engine → Runtime Evaluator → Execution Adapter
```

A flagship strategy is not considered implemented until it passes through this whole chain consistently.

---

## 3. Delivery model

Each stage below is written so it can be split into one or more GitHub Issues.

For every stage we define:
- Goal
- Priority
- Tasks
- Files
- Data model / API changes
- Tests
- Acceptance criteria
- Suggested issue split

---

## 4. Stage 1 — Foundation core

**Priority:** P0  
**Outcome:** the codebase gains a stable engineering foundation for DSL, indicators, compiler growth, and automated verification.

### 4.1 Goal

Before adding more strategy blocks, create a maintainable execution framework.

### 4.2 Tasks

- Add a proper automated test runner for backend strategy logic
- Refactor compiler from hardcoded logic into extensible block registry architecture
- Introduce indicator engine layer separated from compiler and runtime
- Introduce strategy capability matrix documenting support status for each block
- Add golden tests for graph → DSL compilation
- Add contract tests to detect drift between UI blocks and backend compiler support

### 4.3 Expected files

- `package.json`
- `apps/api/package.json`
- `apps/web/package.json`
- `apps/api/src/lib/graphCompiler.ts`
- `apps/api/src/lib/dslValidator.ts`
- `apps/web/src/app/lab/build/blockDefs.ts`
- New directories:
  - `apps/api/src/lib/compiler/`
  - `apps/api/src/lib/indicators/`
  - `apps/api/src/lib/testing/`
  - `apps/api/tests/`
- New docs:
  - `docs/strategies/08-strategy-capability-matrix.md`

### 4.4 Data model / API changes

- No Prisma migrations required in this stage
- No public API changes required in this stage

### 4.5 Tests required

- Unit tests for:
  - schema validation
  - compiler mapping rules
  - indicator primitives
- Contract tests for:
  - every block in `blockDefs.ts` must either have compiler support or be explicitly marked unsupported
- Snapshot / golden tests for:
  - canonical graph inputs producing stable DSL outputs

### 4.6 Acceptance criteria

- Test runner is integrated and used in CI/local workflow
- Compiler no longer relies on ad hoc hardcoded expansion paths
- There is a single registry / mapping source for block support
- Engineering can add a new block without editing unrelated compiler logic
- Drift between UI block library and backend support is detectable by tests

### 4.7 Suggested issue split

- Issue 1A — Add test harness and backend strategy test layout
- Issue 1B — Refactor compiler into block registry architecture
- Issue 1C — Add strategy capability matrix and block support contract tests

---

## 5. Stage 2 — DSL v2 and honest backtesting

**Priority:** P0  
**Outcome:** backtests become strategy-valid instead of engine-valid.

### 5.1 Goal

Replace the current fixed backtest behavior with DSL-driven strategy execution and introduce the first missing flagship-critical blocks.

### 5.2 Tasks

- Extend `Strategy DSL` from MVP shape to DSL v2
- Update `strategy.schema.json` to represent advanced strategy constructs
- Implement `VWAP`
- Implement `ADX`
- Implement `SuperTrend`
- Rewrite backtest engine to evaluate compiled DSL instead of using one hardcoded breakout algorithm
- Ensure `POST /lab/backtest` uses real strategy semantics from `StrategyVersion`
- Add deterministic test datasets / fixtures for strategy backtesting

### 5.3 Expected files

- `docs/10-strategy-dsl.md`
- `docs/schema/strategy.schema.json`
- `apps/api/src/lib/dslValidator.ts`
- `apps/api/src/lib/backtest.ts`
- `apps/api/src/routes/lab.ts`
- `apps/api/src/lib/indicators/`
- `apps/web/src/app/lab/build/blockDefs.ts`
- `apps/api/tests/backtest/`

### 5.4 Data model / API changes

- No mandatory Prisma change if the existing `StrategyVersion.dslJson` remains the source of truth
- API contract update needed for Lab backtest docs if the returned report shape changes

### 5.5 Tests required

- Unit tests for:
  - `VWAP`
  - `ADX`
  - `SuperTrend`
- Golden backtest tests:
  - same DSL + same dataset = same report
- Integration tests:
  - graph compile → strategy version → backtest → report
- Regression tests:
  - unsupported DSL patterns must fail clearly, not silently degrade

### 5.6 Acceptance criteria

- Backtest behavior is driven by compiled strategy DSL
- Backtest no longer ignores strategy entry/exit logic
- At least one flagship-class DSL strategy can be truthfully simulated
- Results are reproducible from `datasetId + datasetHash + strategyVersionId`

### 5.7 Suggested issue split

- Issue 2A — Design and document Strategy DSL v2
- Issue 2B — Implement VWAP, ADX, SuperTrend in indicator engine
- Issue 2C — Replace hardcoded breakout backtest with DSL-driven evaluator

---

## 6. Stage 3 — Runtime signal engine and first tradable strategy

**Priority:** P0  
**Outcome:** the bot can autonomously evaluate a strategy and generate intents.

### 6.1 Goal

Turn bot runtime from lifecycle manager into actual strategy executor.

### 6.2 Tasks

- Introduce runtime signal evaluation layer
- Add position state tracking
- Add runtime risk manager
- Add runtime state snapshot / reconciliation primitives
- Wire compiled DSL into live/demo runtime
- Implement `Adaptive Regime Bot` as the first fully tradable strategy

### 6.3 Expected files

- `apps/api/src/lib/botWorker.ts`
- `apps/api/src/routes/bots.ts`
- `apps/api/src/routes/strategies.ts`
- `apps/api/prisma/schema.prisma`
- New runtime files:
  - `apps/api/src/lib/runtime/signalEngine.ts`
  - `apps/api/src/lib/runtime/positionManager.ts`
  - `apps/api/src/lib/runtime/riskManager.ts`
  - `apps/api/src/lib/runtime/stateReconciler.ts`
- Strategy fixtures/tests under `apps/api/tests/runtime/`

### 6.4 Data model / API changes

#### Prisma

Add at minimum:
- `Position`
- `PositionEvent`
- optional `ExecutionFill`
- optional `BotStateSnapshot`

#### API

Potential additions:
- read endpoint for current position state
- read endpoint for bot runtime state / health
- richer bot detail response including active position and strategy state

### 6.5 Tests required

- Unit tests for:
  - regime switching logic
  - runtime signal generation
  - position state transitions
- Integration tests for:
  - bot run → signal → intent → position transition
- Replay tests for:
  - deterministic candle stream producing expected runtime decisions

### 6.6 Acceptance criteria

- Runtime reads DSL and produces strategy-driven `BotIntent`s
- Position state exists as first-class runtime concept
- `Adaptive Regime Bot` works in backtest and demo runtime
- Restart / resume path preserves or reconciles active strategy state

### 6.7 Suggested issue split

- Issue 3A — Add position domain to Prisma and runtime state layer
- Issue 3B — Implement runtime signal engine from compiled DSL
- Issue 3C — Ship Adaptive Regime Bot end-to-end in demo mode

---

## 7. Stage 4 — DCA execution model

**Priority:** P1  
**Outcome:** project supports stateful averaging strategies, not only single-entry setups.

### 7.1 Goal

Add a dedicated execution model for DCA and make `DCA Momentum Bot` production-shaped in demo mode.

### 7.2 Tasks

- Extend DSL with DCA-specific section / block semantics
- Add DCA runtime engine:
  - base order
  - safety orders
  - average price recalculation
  - TP recalculation
  - max capital load guard
- Extend backtest to support laddered entries and position averaging
- Add DCA configuration surfaces to authoring / compile flow

### 7.3 Expected files

- `docs/10-strategy-dsl.md`
- `docs/schema/strategy.schema.json`
- `apps/api/src/lib/backtest.ts`
- `apps/api/src/lib/runtime/dcaEngine.ts`
- `apps/api/src/lib/runtime/positionManager.ts`
- `apps/web/src/app/lab/build/blockDefs.ts`
- `apps/api/tests/dca/`

### 7.4 Data model / API changes

#### Prisma

Potential additions:
- fields to `Position` / `PositionEvent` for ladder state
- optional `DcaPlan` or equivalent JSON state on active position / bot state

#### API

- expose DCA state in bot detail response
- expose current ladder and average entry information

### 7.5 Tests required

- Unit tests for:
  - average entry calculation
  - safety order schedule generation
  - TP recalculation logic
- Integration tests for:
  - DCA strategy sequence over controlled candles
- Safety tests for:
  - capital allocation caps
  - max safety order enforcement

### 7.6 Acceptance criteria

- DCA strategy produces the same ladder behavior in backtest and runtime replay
- Capital exposure is explicitly bounded
- Runtime can recover DCA state after restart
- `DCA Momentum Bot` becomes executable end-to-end in demo

### 7.7 Suggested issue split

- Issue 4A — Extend DSL/backtest for DCA model
- Issue 4B — Implement runtime DCA engine and state tracking
- Issue 4C — Ship DCA Momentum Bot in demo runtime

---

## 8. Stage 5 — Professional confluence strategy layer

**Priority:** P1  
**Outcome:** system supports multi-timeframe and session-aware professional strategies.

### 8.1 Goal

Implement the infrastructure required for `MTF Confluence Scalper`.

### 8.2 Tasks

- Implement `VolumeProfile`
- Implement `SessionFilter`
- Implement `ProximityFilter`
- Implement `MultiTimeframe` context support
- Extend ATR usage as first-class indicator / risk dependency
- Add session-aware and timeframe-aware backtest / runtime behavior

### 8.3 Expected files

- `docs/10-strategy-dsl.md`
- `docs/schema/strategy.schema.json`
- `apps/web/src/app/lab/build/blockDefs.ts`
- `apps/api/src/lib/graphCompiler.ts`
- `apps/api/src/lib/backtest.ts`
- `apps/api/src/lib/runtime/`
- `apps/api/tests/mtf/`

### 8.4 Data model / API changes

- No mandatory new Prisma model if MTF context is computed at runtime
- Potential metadata expansion for backtest reports to record timeframe dependencies

### 8.5 Tests required

- Unit tests for:
  - session reset rules
  - MTF alignment / resampling behavior
  - level proximity logic
  - volume profile core outputs
- Integration tests for:
  - 1m execution using 5m/15m context
- Regression tests for:
  - identical dataset and strategy version producing stable confluence signals

### 8.6 Acceptance criteria

- Multi-timeframe context is represented in DSL and understood by compiler/backtest/runtime
- Session-aware signals are handled consistently
- `MTF Confluence Scalper` becomes executable in backtest and demo runtime

### 8.7 Suggested issue split

- Issue 5A — Implement MTF/session context layer
- Issue 5B — Implement VolumeProfile and ProximityFilter
- Issue 5C — Ship MTF Confluence Scalper end-to-end

---

## 9. Stage 6 — SMC pattern engine

**Priority:** P2  
**Outcome:** system supports stateful market structure strategies.

### 9.1 Goal

Implement the pattern-detection architecture needed for `SMC Liquidity Sweep + FVG + Order Block`.

### 9.2 Tasks

- Add `LiquiditySweep`
- Add `FairValueGap`
- Add `OrderBlock`
- Add `MarketStructureShift`
- Add previous-day / previous-week structural level logic
- Add session-aware structural context
- Add fixtures for canonical SMC setups

### 9.3 Expected files

- `docs/strategies/02-smc-liquidity-sweep.md`
- `docs/10-strategy-dsl.md`
- `docs/schema/strategy.schema.json`
- `apps/web/src/app/lab/build/blockDefs.ts`
- `apps/api/src/lib/graphCompiler.ts`
- New pattern layer:
  - `apps/api/src/lib/patterns/`
  - `apps/api/src/lib/runtime/patternEngine.ts`
- `apps/api/tests/smc/`

### 9.4 Data model / API changes

- No required new Prisma model if pattern state is runtime-computed
- Optional pattern annotation persistence may be added later if needed for UX/debugging

### 9.5 Tests required

- Unit tests for:
  - sweep detection
  - FVG detection
  - order block detection
  - market structure shift
- Fixture tests for:
  - known candle sequences representing valid/invalid SMC patterns
- Integration tests for:
  - compile → backtest → runtime replay parity on SMC fixtures

### 9.6 Acceptance criteria

- SMC detection is deterministic enough to be regression-tested
- Pattern blocks are documented, compiled, backtestable, and runtime-executable
- `SMC Liquidity Sweep` can be evaluated end-to-end in demo mode

### 9.7 Suggested issue split

- Issue 6A — Implement pattern detection primitives for SMC
- Issue 6B — Add SMC blocks to DSL/compiler/UI/runtime
- Issue 6C — Ship SMC flagship strategy in demo environment

---

## 10. Stage 7 — Funding arbitrage track

**Priority:** P2  
**Outcome:** architecture expands from single-leg strategies to multi-leg neutral strategies.

### 10.1 Goal

Treat `Funding Rate Arbitrage` as a separate architecture track, not as a simple extension of single-market strategies.

### 10.2 Tasks

- Add funding rate ingestion and history support
- Add funding scanner logic
- Add basis spread monitoring
- Introduce spot + perp two-leg execution model
- Introduce hedge position model
- Add spot execution adapter for Bybit
- Support exit on funding deterioration / basis widening

### 10.3 Expected files

- `docs/strategies/04-funding-arbitrage-delta-hedge.md`
- `docs/10-strategy-dsl.md`
- `apps/api/src/routes/terminal.ts`
- New files:
  - `apps/api/src/lib/funding/`
  - `apps/api/src/lib/runtime/multiLegEngine.ts`
  - `apps/api/src/lib/exchange/bybitSpot.ts`
  - `apps/api/src/lib/exchange/bybitPerp.ts`
- `apps/api/prisma/schema.prisma`
- `apps/api/tests/funding/`

### 10.4 Data model / API changes

#### Prisma

Likely additions:
- `FundingSnapshot`
- `SpreadSnapshot`
- `HedgePosition`
- `LegExecution`

#### API

Potential additions:
- scanner endpoint / service for funding opportunities
- hedge position read model
- basis / funding diagnostics endpoints

### 10.5 Tests required

- Unit tests for:
  - funding annualization
  - candidate ranking
  - basis threshold logic
- Integration tests for:
  - scan → select → plan paired execution
- Simulation tests for:
  - funding compression
  - basis blowout
  - forced unwind conditions

### 10.6 Acceptance criteria

- Funding strategy is represented as a first-class multi-leg execution problem
- Spot/perp legs are tracked coherently
- Research / paper-trading quality path exists before any production promotion

### 10.7 Suggested issue split

- Issue 7A — Add funding data ingestion and scanner
- Issue 7B — Add multi-leg hedge execution model
- Issue 7C — Deliver funding arbitrage research / demo execution path

---

## 11. Stage 8 — Production hardening

**Priority:** P0 for safety, continuous across all previous stages  
**Outcome:** the strategy platform becomes safe enough for serious demo-first trading and later controlled live rollout.

### 11.1 Goal

Align runtime behavior with real exchange constraints and failure modes.

### 11.2 Tasks

- Add exchange normalization layer:
  - tick size
  - qty step
  - min notional
  - leverage step
  - funding interval awareness
- Implement partial fill handling
- Implement startup reconciliation
- Add dead-letter / failed intent handling
- Add structured runtime observability
- Add circuit breakers and safety stops
- Add runbooks for stuck positions / drift / exchange mismatch

### 11.3 Expected files

- `apps/api/prisma/schema.prisma`
- `apps/api/src/lib/bybitOrder.ts`
- `apps/api/src/lib/botWorker.ts`
- `apps/api/src/routes/terminal.ts`
- `docs/15-operations.md`
- `docs/runbooks/`
- `apps/api/tests/safety/`

### 11.4 Data model / API changes

- extend runtime entities as needed for reconciliation and execution safety
- expose enough bot state for operator diagnosis

### 11.5 Tests required

- Integration tests for:
  - restart reconciliation
  - duplicate intent prevention
  - partial fill behavior
  - retry classification
- Demo end-to-end tests against Bybit demo where feasible
- Safety tests for:
  - daily loss limit
  - pause on repeated error
  - kill switch behavior

### 11.6 Acceptance criteria

- Bot can recover from restart without losing active trading state
- Exchange restrictions are normalized before order submission
- Safety mechanisms are tested, not just documented
- Demo environment is reliable enough to serve as pre-live validation layer

### 11.7 Suggested issue split

- Issue 8A — Exchange normalization and execution safety layer
- Issue 8B — Runtime reconciliation and recovery path
- Issue 8C — Safety automation and operational hardening

---

## 12. Strategy rollout order

Recommended implementation order:

1. `Adaptive Regime Bot`
2. `DCA Momentum Bot`
3. `MTF Confluence Scalper`
4. `SMC Liquidity Sweep + FVG + OB`
5. `Funding Rate Arbitrage + Delta Hedge`

### Why this order

| Strategy | Why now / why later |
|---|---|
| Adaptive Regime | Best fit for first-class DSL + first autonomous runtime evaluator |
| DCA Momentum | Strong product value and requires execution model expansion |
| MTF Scalper | Extends data/context complexity after base runtime is stable |
| SMC | Requires pattern engine and deterministic fixture-driven validation |
| Funding Arb | Separate multi-leg architecture; should not block single-leg flagship rollout |

---

## 13. Minimal GitHub issue template

Each implementation issue created from this roadmap should use this structure:

### Title
`[Stage X] Short actionable title`

### Body
- Goal
- Scope
- Files
- Data model changes
- API changes
- Tests required
- Acceptance criteria
- Out of scope

### Example

```md
## Goal
Implement VWAP, ADX, and SuperTrend as first-class indicator primitives for DSL-driven backtesting.

## Scope
- Add indicator implementations
- Add compiler support
- Add DSL schema support
- Add tests

## Files
- apps/api/src/lib/indicators/
- apps/api/src/lib/graphCompiler.ts
- docs/10-strategy-dsl.md
- docs/schema/strategy.schema.json

## Tests required
- Unit tests for indicator outputs
- Golden tests for graph → DSL → backtest

## Acceptance criteria
- Indicators are available in compiler and evaluator
- Backtest can use them from compiled DSL

## Out of scope
- Runtime live trading integration
```

---

## 14. Final rule

A strategy is not “implemented” when its block appears in the UI.

A strategy is implemented only when it is:
- authoring-ready
- compile-ready
- schema-valid
- backtest-ready
- runtime-ready
- safety-reviewed

Anything less should be treated as partial progress, not delivery.
