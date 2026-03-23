# Adaptive Regime Bot — End-to-End Flow Reference

> Reference document for the first flagship strategy delivered end-to-end.
> Serves as the pattern for subsequent strategies (#130).

## Pipeline Overview

```
Graph Authoring  →  Compilation  →  Backtest  →  Runtime (Demo)  →  Lifecycle
     (UI)            (API)          (API)         (Worker)         (Worker)
```

### 1. Graph Authoring (UI)

**Location:** `apps/web/src/app/lab/build/`

The user creates a strategy in the visual graph builder by connecting blocks:
- `candles` → source block (symbol + interval)
- Indicator blocks: `ADX`, `EMA`, `RSI`, `BollingerBands`, `SuperTrend`, `SMA`, `VWAP`
- Signal blocks: `compare`, `cross`
- Entry blocks: `enter_long`, `enter_short`
- Risk blocks: `stop_loss`, `take_profit`

**Adaptive Regime Bot graph** (trend-mode path):
```
candles(BTCUSDT, 5m) → ADX(14) → compare(> 25) → enter_long ← stop_loss(2%) + take_profit(4%)
```

**Fixture:** `tests/fixtures/graphs.ts → makeAdaptiveRegimeBotGraph()`

### 2. Compilation (API)

**Location:** `apps/api/src/lib/compiler/`

`compileGraph(graph, strategyId, name, symbol, timeframe)` transforms the graph JSON into a Strategy DSL JSON object.

**Current state:**
- Compiler emits **DSL v1**: fixed side (`Buy`/`Sell`), single entry signal, SL/TP on entry
- **DSL v2** features (`sideCondition`, top-level `exit`, regime dispatch) are hand-authored
- Compiler limitation is documented and tested (`adaptiveRegimeBot.test.ts` section 6)

**Output:** `CompileResult { ok: true, compiledDsl: Record<string, unknown> }`

**Key files:**
- `compiler/index.ts` — entry point
- `compiler/graphCompiler.ts` — compilation engine
- `compiler/types.ts` — GraphJson, CompileResult types
- `compiler/blockHandlers.ts` — per-block compilation rules

### 3. Backtest (API)

**Location:** `apps/api/src/lib/dslEvaluator.ts`, `backtest.ts`, `adaptiveStrategy.ts`

Two backtest paths:

#### Single-strategy backtest
`runBacktest(candles, dslJson)` — bar-by-bar evaluation using compiled or hand-authored DSL.

Returns: `DslBacktestReport { trades, wins, winrate, totalPnlPct, maxDrawdownPct, tradeLog }`

#### Adaptive regime backtest
`runAdaptiveBacktest(candles, config)` — regime-aware bar-by-bar evaluation.

Per bar:
1. `determineRegime(config.regime, i, candles, cache)` → `"trend" | "range" | "neutral"`
2. If trend → evaluate trend entry (EMA sideCondition + ADX signal)
3. If range → evaluate range entry (RSI mean-reversion)
4. If neutral → no new entries, manage open position only
5. SL/TP exit evaluation on every bar

Returns: `AdaptiveBacktestReport { trades, wins, winrate, totalPnlPct, tradeLog, regimeLog }`

**Determinism:** Both backtests are pure functions. Same inputs always produce same outputs.
No randomness, no I/O, no clock dependence.

**Fixtures:** `tests/fixtures/candles.ts` — `makeStrongUptrend()`, `makeRangeBound()`, `makeRangeThenTrend()`

### 4. Runtime Signal Evaluation (Worker)

**Location:** `apps/api/src/lib/signalEngine.ts`, `exitEngine.ts`, `riskManager.ts`

The bot worker (`botWorker.ts`) polls every 4 seconds. For each RUNNING bot run:

#### Entry path (no open position)
1. Load 200 recent candles from `MarketCandle` table
2. `computeSizing(ctx)` — check eligibility (cooldown, max positions) + compute qty
3. `evaluateEntry({ candles, dslJson, position: null })` — pure function
4. If signal fires → create `BotIntent(type: ENTRY, state: PENDING)` with deterministic `intentId`
5. `intentId = entry_{triggerTime}_{side}` — idempotency key (DB unique constraint)

#### Exit path (open position)
1. Load position via `getActivePosition(runId, symbol)`
2. Reconstruct or load `TrailingStopState`
3. `evaluateExit({ candles, dslJson, position, barsHeld, trailingState })` — pure function
4. Checks: SL → trailing stop → indicator → TP → time exit
5. If exit fires → create `BotIntent(type: EXIT, state: PENDING)` with deterministic `intentId`

#### Demo mode intent execution
- No exchange connection → intent immediately: `PENDING → PLACED → FILLED` (simulated)
- `BotEvent(type: intent_simulated)` logged for audit

#### Live mode intent execution
- Exchange connection → `PENDING → PLACED` (on Bybit) → reconciled later
- `reconcilePlacedIntents()` polls exchange for fill status

### 5. Position Lifecycle

**Location:** `apps/api/src/lib/positionManager.ts`

Immutable event-sourced position management:
```
openPosition()  →  Position(OPEN) + PositionEvent(OPEN)
addToPosition() →  VWAP recalc + PositionEvent(ADD)
closePosition() →  Position(CLOSED) + PnL calc + PositionEvent(CLOSE)
```

All mutations create an immutable `PositionEvent` for auditability.

### 6. Restart/Resume Recovery

**Location:** `apps/api/src/lib/recoveryManager.ts`

On worker restart, two ephemeral states are lost:
- `TrailingStopState` (in-memory map)
- `lastTradeCloseTime` (in-memory map)

Recovery in `activateRun()`:
1. Load open position from DB via `getActivePosition()`
2. Query last `CLOSE` PositionEvent timestamp
3. `reconstructRunState(position, lastCloseTimestamp)` — pure function
4. Populate in-memory maps

**Safety properties:**
- Trailing stop reset to entry price (conservative — must re-activate)
- No duplicate entries: 3-layer defense (position check + intentId dedup + signal purity)
- Idempotent: same reconstruction always produces same state

### 7. Bot Run State Machine

**Location:** `apps/api/src/lib/stateMachine.ts`

```
CREATED → QUEUED → STARTING → SYNCING → RUNNING
                                           │
                     STOPPING → STOPPED  ←─┤
                     FAILED              ←─┤
                     TIMED_OUT           ←─┘
```

Terminal states: `STOPPED`, `FAILED`, `TIMED_OUT`

Worker lease: 30s renewal, `WORKER_ID` ownership.

## Known Limitations

| Limitation | Status | Impact |
|---|---|---|
| Compiler emits DSL v1 only (no sideCondition, no top-level exit) | Documented | Hand-authored DSL v2 used for adaptive features |
| Single timeframe (5m) | By design for MVP | MTF is out of scope (#130) |
| BB band proximity not used as explicit range entry filter | Documented | RSI < 40 used instead, effective in low-ADX regimes |
| Range-mode short entries not in adaptive config | Documented | Long-only mean reversion currently |
| Trailing stop watermark lost on restart | By design | Conservative reset from entry price is safe |

## Key Files

| File | Role |
|---|---|
| `src/lib/compiler/index.ts` | Graph → DSL compilation |
| `src/lib/dslEvaluator.ts` | DSL evaluation, indicator computation, backtest |
| `src/lib/adaptiveStrategy.ts` | Regime detection, adaptive backtest/entry |
| `src/lib/signalEngine.ts` | Runtime entry evaluation |
| `src/lib/exitEngine.ts` | Runtime exit evaluation |
| `src/lib/riskManager.ts` | Sizing + eligibility |
| `src/lib/positionManager.ts` | Position lifecycle |
| `src/lib/recoveryManager.ts` | Restart/resume state reconstruction |
| `src/lib/botWorker.ts` | Worker loop, intent execution, strategy evaluation |
| `src/lib/stateMachine.ts` | Bot run state machine |

## Test Coverage

| Test Suite | Count | What it covers |
|---|---|---|
| `adaptiveRegimeBot.test.ts` | 39 | Compilation, backtest, signals, exits, parity, compiler continuity |
| `adaptiveRegimeSwitching.test.ts` | 31 | Regime detection, range/trend/neutral, adaptive backtest, transitions |
| `restartResume.test.ts` | 29 | State reconstruction, no duplicate entry, exit after restart, idempotency |
| `demoLifecycleAcceptance.test.ts` | 22 | Full pipeline: graph → compile → backtest → runtime → lifecycle |

All tests are deterministic: fixed fixtures, no randomness, no I/O.

## Pattern for Subsequent Strategies

To implement a new flagship strategy following this pattern:

1. **Define strategy spec** in `docs/strategies/NN-strategy-name.md`
2. **Add graph fixture** in `tests/fixtures/graphs.ts`
3. **Add DSL fixture** in `tests/fixtures/` (hand-authored if compiler doesn't support features yet)
4. **Add indicator** if needed in `dslEvaluator.ts` indicator cache
5. **Add entry/exit logic** as pure functions (no I/O)
6. **Add backtest** path (bar-by-bar, deterministic)
7. **Add runtime evaluation** path (same primitives as backtest)
8. **Add recovery** handling if new ephemeral state is introduced
9. **Add tests** for each pipeline stage
10. **Add acceptance test** proving full lifecycle coherence
