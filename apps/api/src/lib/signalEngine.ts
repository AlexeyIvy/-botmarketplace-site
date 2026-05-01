/**
 * Signal Engine — runtime entry condition evaluator (#128)
 *
 * Reads compiled DSL and evaluates entry conditions against current market state
 * to produce open-position BotIntent descriptors.
 *
 * Uses the same evaluation primitives as the backtest evaluator (#126) to ensure
 * parity: evaluateSignal, determineSide, computeExitLevels are shared.
 *
 * The engine is a pure function: given candles + DSL + position state, it returns
 * an OpenSignal or null. No I/O, no side effects.
 */

import type { Candle } from "./bybitCandles.js";
import type { PositionSnapshot } from "./positionManager.js";
import {
  parseDsl,
  evaluateSignal,
  evaluateProximityFilter,
  determineSide,
  computeExitLevels,
  createIndicatorCache,
  type ParsedDsl,
  type TradeSide,
  type DslExitLevel,
  type IndicatorCache,
  type RuntimeMtfContext,
} from "./dslEvaluator.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface OpenSignal {
  /** Intent type */
  action: "open";
  /** Trade direction */
  side: TradeSide;
  /** Suggested entry price (last candle close) */
  price: number;
  /** Computed stop-loss level */
  slPrice: number;
  /** Computed take-profit level */
  tpPrice: number;
  /** Human-readable reason for the signal */
  reason: string;
  /** DSL signal type that fired */
  signalType: string;
  /** Candle timestamp that triggered the signal */
  triggerTime: number;
}

export interface SignalEngineContext {
  /** OHLCV candles (sorted ascending by openTime, recent window) */
  candles: Candle[];
  /** Compiled strategy DSL */
  dslJson: unknown;
  /** Current active position (null if no position) */
  position: PositionSnapshot | null;
  /**
   * Optional multi-TF runtime context (docs/52-T3). When set, DSL refs that
   * carry a `sourceTimeframe` resolve from the bundle's context-TF candles.
   * When absent, refs without `sourceTimeframe` continue to work; refs with
   * one throw {@link MtfBundleRequiredError}.
   */
  mtfContext?: RuntimeMtfContext | null;
}

// ---------------------------------------------------------------------------
// Engine
// ---------------------------------------------------------------------------

/**
 * Evaluate entry conditions on the most recent candle in the provided window.
 *
 * Returns an OpenSignal if conditions are met and no position is currently open.
 * Returns null otherwise.
 *
 * The candle window must contain enough history for indicator warm-up
 * (e.g., at least slowLength + 1 candles for SMA crossover signals).
 */
export function evaluateEntry(ctx: SignalEngineContext): OpenSignal | null {
  // If already in a position, no entry signal
  if (ctx.position && ctx.position.status === "OPEN") {
    return null;
  }

  const { candles, dslJson, mtfContext } = ctx;
  if (candles.length < 2) return null;

  const parsed = parseDsl(dslJson);
  const { entry, exit, risk } = parsed;

  const cache = createIndicatorCache();
  const i = candles.length - 1; // evaluate on the latest candle

  // Determine side — propagate MTF context so sideCondition.indicator with a
  // `sourceTimeframe` can resolve from the HTF candles in the bundle.
  const side = determineSide(entry, i, candles, cache, mtfContext);
  if (!side) return null;

  // Evaluate entry signal
  const signalFired = evaluateSignal(entry.signal, i, candles, cache);
  if (!signalFired) return null;

  // Proximity filter gate: block signal if price is too far from reference level
  if (!evaluateProximityFilter(entry.proximityFilter, i, candles, cache)) return null;

  // Compute exit levels
  const slDef: DslExitLevel = exit?.stopLoss
    ?? entry.stopLoss
    ?? { type: "fixed_pct", value: risk.riskPerTradePct };
  const tpDef: DslExitLevel = exit?.takeProfit
    ?? entry.takeProfit
    ?? { type: "fixed_pct", value: risk.riskPerTradePct * 2 };

  const entryPrice = candles[i].close;
  const levels = computeExitLevels(slDef, tpDef, entryPrice, side, i, candles, cache);

  const signalType = entry.signal?.type ?? "unknown";
  const reason = `DSL ${signalType} signal fired → ${side} entry at ${entryPrice.toFixed(2)}`;

  return {
    action: "open",
    side,
    price: entryPrice,
    slPrice: levels.slPrice,
    tpPrice: levels.tpPrice,
    reason,
    signalType,
    triggerTime: candles[i].openTime,
  };
}

/**
 * Convenience: evaluate entry and return a BotIntent-compatible descriptor
 * ready for insertion into the database.
 */
export function generateOpenIntent(
  ctx: SignalEngineContext,
  opts: { botRunId: string; symbol: string; sizingQty: number },
): {
  intentId: string;
  side: "BUY" | "SELL";
  qty: number;
  price: number;
  slPrice: number;
  tpPrice: number;
  type: "ENTRY";
  reason: string;
} | null {
  const signal = evaluateEntry(ctx);
  if (!signal) return null;

  return {
    intentId: `entry_${signal.triggerTime}_${signal.side}`,
    side: signal.side === "long" ? "BUY" : "SELL",
    qty: opts.sizingQty,
    price: signal.price,
    slPrice: signal.slPrice,
    tpPrice: signal.tpPrice,
    type: "ENTRY",
    reason: signal.reason,
  };
}
