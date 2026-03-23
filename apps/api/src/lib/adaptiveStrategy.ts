/**
 * Adaptive Regime Strategy — regime detection and multi-strategy dispatch (#130)
 *
 * Implements the core adaptive behavior for the Adaptive Regime Bot:
 *   - Regime detection via ADX thresholds (trend / range / neutral)
 *   - Per-bar strategy dispatch: trend-mode entry vs range-mode entry
 *   - Neutral zone: no new entries when ADX is between thresholds
 *
 * Design:
 *   - Pure functions: no I/O, no side effects, fully deterministic
 *   - Composes existing primitives: evaluateSignal, determineSide, computeExitLevels
 *   - Does NOT modify the single-strategy pipeline; layers on top of it
 *   - The AdaptiveStrategyConfig bundles two DSL entries + regime thresholds
 *
 * Strategy semantics:
 *   - ADX > trendThreshold  → trend mode (e.g., EMA crossover / ADX strength)
 *   - ADX < rangeThreshold  → range mode (e.g., BB + RSI mean-reversion)
 *   - rangeThreshold <= ADX <= trendThreshold → neutral, no new entries
 */

import type { Candle } from "./bybitCandles.js";
import type { PositionSnapshot } from "./positionManager.js";
import {
  evalOp,
  evaluateSignal,
  determineSide,
  computeExitLevels,
  createIndicatorCache,
  getIndicatorValues,
  type TradeSide,
  type DslEntry,
  type DslExit,
  type DslExitLevel,
  type DslRisk,
  type DslBacktestReport,
  type DslTradeRecord,
  type DslExecOpts,
  type IndicatorCache,
} from "./dslEvaluator.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type Regime = "trend" | "range" | "neutral";

export interface RegimeConfig {
  /** ADX indicator period (default: 14) */
  adxPeriod: number;
  /** ADX above this → trend mode */
  trendThreshold: number;
  /** ADX below this → range mode */
  rangeThreshold: number;
}

/**
 * Adaptive strategy configuration: two sub-strategies gated by ADX regime.
 *
 * Each sub-strategy is a standard DSL entry + shared exit/risk config.
 * The adaptive layer selects which entry to evaluate per bar.
 */
export interface AdaptiveStrategyConfig {
  regime: RegimeConfig;
  /** Entry config for trend regime */
  trendEntry: DslEntry;
  /** Entry config for range regime */
  rangeEntry: DslEntry;
  /** Shared exit configuration */
  exit: DslExit;
  /** Shared risk configuration */
  risk: DslRisk;
}

export interface AdaptiveTradeRecord extends DslTradeRecord {
  /** Which regime was active when the trade was entered */
  entryRegime: Regime;
}

export interface AdaptiveBacktestReport {
  trades: number;
  wins: number;
  winrate: number;
  totalPnlPct: number;
  maxDrawdownPct: number;
  candles: number;
  tradeLog: AdaptiveTradeRecord[];
  /** Per-bar regime classification (for diagnostics) */
  regimeLog: Regime[];
}

export interface AdaptiveEntrySignal {
  action: "open";
  side: TradeSide;
  price: number;
  slPrice: number;
  tpPrice: number;
  regime: Regime;
  reason: string;
  signalType: string;
  triggerTime: number;
}

// ---------------------------------------------------------------------------
// Regime detection — pure function
// ---------------------------------------------------------------------------

/**
 * Determine the market regime at bar `i` using ADX.
 *
 * Returns:
 *   - "trend"   if ADX > trendThreshold
 *   - "range"   if ADX < rangeThreshold
 *   - "neutral" if rangeThreshold <= ADX <= trendThreshold, or ADX not available
 */
export function determineRegime(
  config: RegimeConfig,
  i: number,
  candles: Candle[],
  cache: IndicatorCache,
): Regime {
  const adxValues = getIndicatorValues(
    "adx",
    { period: config.adxPeriod },
    candles,
    cache,
  );

  const adx = adxValues[i];
  if (adx === null) return "neutral";

  if (adx > config.trendThreshold) return "trend";
  if (adx < config.rangeThreshold) return "range";
  return "neutral";
}

// ---------------------------------------------------------------------------
// Adaptive backtest — bar-by-bar regime-aware evaluation
// ---------------------------------------------------------------------------

/**
 * Run an adaptive regime-aware backtest.
 *
 * Per bar:
 *   1. If in position → check exits (using shared exit config)
 *   2. If not in position → determine regime → evaluate corresponding entry
 *   3. Neutral regime → skip entry (no new trades)
 *
 * Exit logic is regime-agnostic: once in a position, exits follow the shared
 * exit config regardless of current regime. This avoids whipsaw on regime
 * transitions while a position is open.
 */
export function runAdaptiveBacktest(
  candles: Candle[],
  config: AdaptiveStrategyConfig,
  opts: Partial<DslExecOpts> = {},
): AdaptiveBacktestReport {
  const { feeBps = 0, slippageBps = 0 } = opts;

  const emptyReport: AdaptiveBacktestReport = {
    trades: 0, wins: 0, winrate: 0, totalPnlPct: 0, maxDrawdownPct: 0,
    candles: candles.length, tradeLog: [], regimeLog: [],
  };

  if (candles.length < 2) return emptyReport;

  const cache = createIndicatorCache();
  const { regime: regimeConfig, trendEntry, rangeEntry, exit, risk } = config;

  // Resolve SL/TP
  const slDef: DslExitLevel = exit.stopLoss;
  const tpDef: DslExitLevel = exit.takeProfit;

  const entryMult = 1 + (feeBps + slippageBps) / 10_000;
  const exitMult = 1 - feeBps / 10_000;

  const tradeLog: AdaptiveTradeRecord[] = [];
  const regimeLog: Regime[] = new Array(candles.length).fill("neutral");

  // Position state
  let inPosition = false;
  let positionSide: TradeSide = "long";
  let effectiveEntry = 0;
  let entryTime = 0;
  let entryBarIndex = 0;
  let slPrice = 0;
  let tpPrice = 0;
  let entryRegime: Regime = "neutral";
  let trailingHigh = 0;
  let trailingLow = Infinity;
  let trailingStopPrice = 0;
  let trailingActivated = false;

  let cumulativePnl = 0;
  let peakPnl = 0;
  let maxDrawdownPct = 0;

  function recordTrade(
    exitTime: number,
    rawExitPrice: number,
    outcome: "WIN" | "LOSS" | "NEUTRAL",
    exitReason: DslTradeRecord["exitReason"],
    barsHeld: number,
  ): void {
    const effectiveExit = rawExitPrice * exitMult;
    let pnlPct: number;
    if (positionSide === "long") {
      pnlPct = ((effectiveExit - effectiveEntry) / effectiveEntry) * 100;
    } else {
      pnlPct = ((effectiveEntry - effectiveExit) / effectiveEntry) * 100;
    }

    tradeLog.push({
      entryTime,
      exitTime,
      side: positionSide,
      entryPrice: effectiveEntry,
      exitPrice: effectiveExit,
      slPrice,
      tpPrice,
      outcome,
      pnlPct,
      exitReason,
      barsHeld,
      entryRegime,
    });

    cumulativePnl += pnlPct;
    if (cumulativePnl > peakPnl) peakPnl = cumulativePnl;
    const dd = peakPnl - cumulativePnl;
    if (dd > maxDrawdownPct) maxDrawdownPct = dd;

    inPosition = false;
  }

  for (let i = 1; i < candles.length; i++) {
    const c = candles[i];
    const currentRegime = determineRegime(regimeConfig, i, candles, cache);
    regimeLog[i] = currentRegime;

    if (inPosition) {
      const barsHeld = i - entryBarIndex;

      // --- Exit checks (same priority as single-strategy backtest) ---

      // 1. Stop loss
      if (positionSide === "long" && c.low <= slPrice) {
        recordTrade(c.openTime, slPrice, "LOSS", "sl", barsHeld);
        continue;
      }
      if (positionSide === "short" && c.high >= slPrice) {
        recordTrade(c.openTime, slPrice, "LOSS", "sl", barsHeld);
        continue;
      }

      // 2. Trailing stop
      if (exit.trailingStop) {
        const ts = exit.trailingStop;
        if (ts.type === "trailing_pct" && ts.activationPct !== undefined && ts.callbackPct !== undefined) {
          if (positionSide === "long") {
            if (c.high > trailingHigh) trailingHigh = c.high;
            const activationPrice = effectiveEntry * (1 + ts.activationPct / 100);
            if (trailingHigh >= activationPrice) {
              trailingActivated = true;
              trailingStopPrice = trailingHigh * (1 - ts.callbackPct / 100);
            }
            if (trailingActivated && c.low <= trailingStopPrice) {
              const outcome = trailingStopPrice >= effectiveEntry ? "WIN" : "LOSS";
              recordTrade(c.openTime, trailingStopPrice, outcome, "trailing_stop", barsHeld);
              continue;
            }
          } else {
            if (c.low < trailingLow) trailingLow = c.low;
            const activationPrice = effectiveEntry * (1 - ts.activationPct / 100);
            if (trailingLow <= activationPrice) {
              trailingActivated = true;
              trailingStopPrice = trailingLow * (1 + ts.callbackPct / 100);
            }
            if (trailingActivated && c.high >= trailingStopPrice) {
              const outcome = trailingStopPrice <= effectiveEntry ? "WIN" : "LOSS";
              recordTrade(c.openTime, trailingStopPrice, outcome, "trailing_stop", barsHeld);
              continue;
            }
          }
        }
      }

      // 3. Indicator exit
      if (exit.indicatorExit) {
        const ie = exit.indicatorExit;
        const appliesTo = ie.appliesTo ?? "both";
        if (appliesTo === "both" || appliesTo === positionSide) {
          const indVals = getIndicatorValues(
            ie.indicator.type,
            {
              length: ie.indicator.length,
              period: (ie.indicator as unknown as Record<string, unknown>).period as number | undefined,
              atrPeriod: ie.indicator.atrPeriod,
              multiplier: ie.indicator.multiplier,
            },
            candles,
            cache,
          );
          const val = indVals[i];
          if (val !== null && evalOp(ie.condition.op, val, ie.condition.value)) {
            const exitPrice = c.close;
            const pnlDirection = positionSide === "long"
              ? exitPrice * exitMult - effectiveEntry
              : effectiveEntry - exitPrice * exitMult;
            const outcome = pnlDirection > 0 ? "WIN" : pnlDirection < 0 ? "LOSS" : "NEUTRAL";
            recordTrade(c.openTime, exitPrice, outcome, "indicator_exit", barsHeld);
            continue;
          }
        }
      }

      // 4. Take profit
      if (positionSide === "long" && c.high >= tpPrice) {
        recordTrade(c.openTime, tpPrice, "WIN", "tp", barsHeld);
        continue;
      }
      if (positionSide === "short" && c.low <= tpPrice) {
        recordTrade(c.openTime, tpPrice, "WIN", "tp", barsHeld);
        continue;
      }

      // 5. Time exit
      if (exit.timeExit && barsHeld >= exit.timeExit.maxBarsInPosition) {
        const exitPrice = c.close;
        const pnlDirection = positionSide === "long"
          ? exitPrice * exitMult - effectiveEntry
          : effectiveEntry - exitPrice * exitMult;
        const outcome = pnlDirection > 0 ? "WIN" : pnlDirection < 0 ? "LOSS" : "NEUTRAL";
        recordTrade(c.openTime, exitPrice, outcome, "time_exit", barsHeld);
        continue;
      }

      // Still in position
    } else {
      // --- Entry evaluation: regime-gated ---
      if (currentRegime === "neutral") continue;

      const activeEntry = currentRegime === "trend" ? trendEntry : rangeEntry;

      // Determine side
      const side = determineSide(activeEntry, i, candles, cache);
      if (!side) continue;

      // Evaluate entry signal
      const signalFired = evaluateSignal(activeEntry.signal, i, candles, cache);
      if (!signalFired) continue;

      // Enter position
      inPosition = true;
      positionSide = side;
      effectiveEntry = c.close * entryMult;
      entryTime = c.openTime;
      entryBarIndex = i;
      entryRegime = currentRegime;

      // Compute SL/TP levels
      const levels = computeExitLevels(slDef, tpDef, effectiveEntry, side, i, candles, cache);
      slPrice = levels.slPrice;
      tpPrice = levels.tpPrice;

      // Reset trailing stop state
      trailingHigh = c.close;
      trailingLow = c.close;
      trailingStopPrice = 0;
      trailingActivated = false;
    }
  }

  // Close open position at last candle
  if (inPosition) {
    const last = candles[candles.length - 1];
    const barsHeld = candles.length - 1 - entryBarIndex;
    const eodExitPrice = last.close * exitMult;
    const eodPnlDirection = positionSide === "long"
      ? eodExitPrice - effectiveEntry
      : effectiveEntry - eodExitPrice;
    const eodOutcome = eodPnlDirection > 0 ? "WIN" : eodPnlDirection < 0 ? "LOSS" : "NEUTRAL";
    recordTrade(last.openTime, last.close, eodOutcome, "end_of_data", barsHeld);
  }

  const trades = tradeLog.length;
  const wins = tradeLog.filter((t) => t.outcome === "WIN").length;
  const winrate = trades > 0 ? wins / trades : 0;
  const totalPnlPct = tradeLog.reduce((s, t) => s + t.pnlPct, 0);

  return {
    trades,
    wins,
    winrate: Math.round(winrate * 10000) / 10000,
    totalPnlPct: Math.round(totalPnlPct * 100) / 100,
    maxDrawdownPct: Math.round(maxDrawdownPct * 100) / 100,
    candles: candles.length,
    tradeLog,
    regimeLog,
  };
}

// ---------------------------------------------------------------------------
// Adaptive entry evaluation — for runtime signal engine
// ---------------------------------------------------------------------------

/**
 * Evaluate adaptive entry conditions on the most recent candle.
 *
 * Returns an AdaptiveEntrySignal if conditions are met, null otherwise.
 * Mirrors the entry logic in runAdaptiveBacktest for parity.
 */
export function evaluateAdaptiveEntry(ctx: {
  candles: Candle[];
  config: AdaptiveStrategyConfig;
  position: PositionSnapshot | null;
}): AdaptiveEntrySignal | null {
  if (ctx.position && ctx.position.status === "OPEN") return null;

  const { candles, config } = ctx;
  if (candles.length < 2) return null;

  const cache = createIndicatorCache();
  const i = candles.length - 1;

  const currentRegime = determineRegime(config.regime, i, candles, cache);
  if (currentRegime === "neutral") return null;

  const activeEntry = currentRegime === "trend" ? config.trendEntry : config.rangeEntry;

  const side = determineSide(activeEntry, i, candles, cache);
  if (!side) return null;

  const signalFired = evaluateSignal(activeEntry.signal, i, candles, cache);
  if (!signalFired) return null;

  const entryPrice = candles[i].close;
  const levels = computeExitLevels(
    config.exit.stopLoss,
    config.exit.takeProfit,
    entryPrice,
    side,
    i,
    candles,
    cache,
  );

  const signalType = activeEntry.signal?.type ?? "unknown";
  const reason = `Adaptive ${currentRegime}-mode: ${signalType} signal → ${side} at ${entryPrice.toFixed(2)}`;

  return {
    action: "open",
    side,
    price: entryPrice,
    slPrice: levels.slPrice,
    tpPrice: levels.tpPrice,
    regime: currentRegime,
    reason,
    signalType,
    triggerTime: candles[i].openTime,
  };
}
