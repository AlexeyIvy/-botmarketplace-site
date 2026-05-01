/**
 * Exit Engine — runtime exit condition evaluator (#128)
 *
 * Evaluates DSL v2 exit conditions against current market state and position
 * to produce close-position BotIntent descriptors.
 *
 * Supports:
 *   - Fixed SL/TP (fixed_pct, atr_multiple)
 *   - Indicator-based exits (conditional, e.g. RSI > 70)
 *   - Trailing stops (trailing_pct)
 *   - Time-based exits (maxBarsInPosition)
 *
 * Uses the same evaluation primitives as the backtest evaluator (#126).
 * Exit priority matches backtest: SL → trailing → indicator → TP → time.
 *
 * The engine is a pure function: no I/O, no side effects.
 */

import type { Candle } from "./bybitCandles.js";
import type { PositionSnapshot } from "./positionManager.js";
import {
  parseDsl,
  evalOp,
  resolveIndicatorRef,
  computeExitLevels,
  createIndicatorCache,
  type ParsedDsl,
  type TradeSide,
  type DslExitLevel,
  type DslExit,
  type IndicatorCache,
  type RuntimeMtfContext,
} from "./dslEvaluator.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ExitReason =
  | "sl"
  | "tp"
  | "indicator_exit"
  | "time_exit"
  | "trailing_stop";

export interface CloseSignal {
  action: "close";
  side: TradeSide;
  price: number;
  reason: ExitReason;
  description: string;
  triggerTime: number;
}

/**
 * Trailing stop state tracked across ticks.
 * The caller must persist this between evaluateExit calls.
 */
export interface TrailingStopState {
  highWaterMark: number;   // highest price since entry (long)
  lowWaterMark: number;    // lowest price since entry (short)
  activated: boolean;      // whether activation threshold has been reached
  trailingStopPrice: number;
}

export function createTrailingStopState(entryPrice: number): TrailingStopState {
  return {
    highWaterMark: entryPrice,
    lowWaterMark: entryPrice,
    activated: false,
    trailingStopPrice: 0,
  };
}

export interface ExitEngineContext {
  /** OHLCV candles (sorted ascending, recent window) */
  candles: Candle[];
  /** Compiled strategy DSL */
  dslJson: unknown;
  /** Current open position */
  position: PositionSnapshot;
  /** Number of bars since position was opened */
  barsHeld: number;
  /** Mutable trailing stop state (updated in-place) */
  trailingState: TrailingStopState;
  /**
   * Optional multi-TF runtime context (docs/52-T3). When set, indicator-exit
   * refs that carry a `sourceTimeframe` resolve from the bundle's context-TF
   * candles. Refs with `sourceTimeframe` and no bundle throw
   * {@link MtfBundleRequiredError}.
   */
  mtfContext?: RuntimeMtfContext | null;
}

// ---------------------------------------------------------------------------
// Engine
// ---------------------------------------------------------------------------

/**
 * Evaluate exit conditions on the most recent candle.
 *
 * Returns a CloseSignal if any exit condition fires, null otherwise.
 * Exit priority: SL → trailing stop → indicator exit → TP → time exit.
 *
 * This mirrors the exact same priority and condition semantics as
 * runDslBacktest in dslEvaluator.ts.
 */
export function evaluateExit(ctx: ExitEngineContext): CloseSignal | null {
  const { candles, dslJson, position, barsHeld, trailingState, mtfContext } = ctx;
  if (candles.length < 1) return null;
  if (position.status !== "OPEN") return null;

  const parsed = parseDsl(dslJson);
  const { entry, exit, risk } = parsed;
  const positionSide: TradeSide = position.side === "LONG" ? "long" : "short";

  // Resolve SL/TP definitions
  const slDef: DslExitLevel = exit?.stopLoss
    ?? entry.stopLoss
    ?? { type: "fixed_pct", value: risk.riskPerTradePct };
  const tpDef: DslExitLevel = exit?.takeProfit
    ?? entry.takeProfit
    ?? { type: "fixed_pct", value: risk.riskPerTradePct * 2 };

  const cache = createIndicatorCache();
  const i = candles.length - 1;
  const c = candles[i];

  // Use position's stored SL/TP prices if available, otherwise compute from DSL
  let slPrice: number;
  let tpPrice: number;
  if (position.slPrice != null && position.tpPrice != null) {
    slPrice = position.slPrice;
    tpPrice = position.tpPrice;
  } else {
    const levels = computeExitLevels(
      slDef, tpDef, position.avgEntryPrice, positionSide, i, candles, cache,
    );
    slPrice = levels.slPrice;
    tpPrice = levels.tpPrice;
  }

  // --- 1. Stop Loss ---
  if (positionSide === "long" && c.low <= slPrice) {
    return {
      action: "close",
      side: positionSide,
      price: slPrice,
      reason: "sl",
      description: `Stop loss triggered at ${slPrice.toFixed(2)} (low: ${c.low.toFixed(2)})`,
      triggerTime: c.openTime,
    };
  }
  if (positionSide === "short" && c.high >= slPrice) {
    return {
      action: "close",
      side: positionSide,
      price: slPrice,
      reason: "sl",
      description: `Stop loss triggered at ${slPrice.toFixed(2)} (high: ${c.high.toFixed(2)})`,
      triggerTime: c.openTime,
    };
  }

  // --- 2. Trailing Stop ---
  if (exit?.trailingStop) {
    const ts = exit.trailingStop;
    if (ts.type === "trailing_pct" && ts.activationPct !== undefined && ts.callbackPct !== undefined) {
      if (positionSide === "long") {
        if (c.high > trailingState.highWaterMark) {
          trailingState.highWaterMark = c.high;
        }
        const activationPrice = position.avgEntryPrice * (1 + ts.activationPct / 100);
        if (trailingState.highWaterMark >= activationPrice) {
          trailingState.activated = true;
          trailingState.trailingStopPrice = trailingState.highWaterMark * (1 - ts.callbackPct / 100);
        }
        if (trailingState.activated && c.low <= trailingState.trailingStopPrice) {
          return {
            action: "close",
            side: positionSide,
            price: trailingState.trailingStopPrice,
            reason: "trailing_stop",
            description: `Trailing stop triggered at ${trailingState.trailingStopPrice.toFixed(2)}`,
            triggerTime: c.openTime,
          };
        }
      } else {
        if (c.low < trailingState.lowWaterMark) {
          trailingState.lowWaterMark = c.low;
        }
        const activationPrice = position.avgEntryPrice * (1 - ts.activationPct / 100);
        if (trailingState.lowWaterMark <= activationPrice) {
          trailingState.activated = true;
          trailingState.trailingStopPrice = trailingState.lowWaterMark * (1 + ts.callbackPct / 100);
        }
        if (trailingState.activated && c.high >= trailingState.trailingStopPrice) {
          return {
            action: "close",
            side: positionSide,
            price: trailingState.trailingStopPrice,
            reason: "trailing_stop",
            description: `Trailing stop triggered at ${trailingState.trailingStopPrice.toFixed(2)}`,
            triggerTime: c.openTime,
          };
        }
      }
    }
  }

  // --- 3. Indicator Exit ---
  if (exit?.indicatorExit) {
    const ie = exit.indicatorExit;
    const appliesTo = ie.appliesTo ?? "both";
    if (appliesTo === "both" || appliesTo === positionSide) {
      // 52-T3: branch on ie.indicator.sourceTimeframe so indicator exits
      // declared on a context TF resolve through the bundle.
      const indVals = resolveIndicatorRef(ie.indicator, candles, cache, mtfContext);
      const val = indVals[i];
      if (val !== null && evalOp(ie.condition.op, val, ie.condition.value)) {
        return {
          action: "close",
          side: positionSide,
          price: c.close,
          reason: "indicator_exit",
          description: `Indicator exit: ${ie.indicator.type} ${ie.condition.op} ${ie.condition.value} (value: ${val.toFixed(2)})`,
          triggerTime: c.openTime,
        };
      }
    }
  }

  // --- 4. Take Profit ---
  if (positionSide === "long" && c.high >= tpPrice) {
    return {
      action: "close",
      side: positionSide,
      price: tpPrice,
      reason: "tp",
      description: `Take profit triggered at ${tpPrice.toFixed(2)} (high: ${c.high.toFixed(2)})`,
      triggerTime: c.openTime,
    };
  }
  if (positionSide === "short" && c.low <= tpPrice) {
    return {
      action: "close",
      side: positionSide,
      price: tpPrice,
      reason: "tp",
      description: `Take profit triggered at ${tpPrice.toFixed(2)} (low: ${c.low.toFixed(2)})`,
      triggerTime: c.openTime,
    };
  }

  // --- 5. Time Exit ---
  if (exit?.timeExit && barsHeld >= exit.timeExit.maxBarsInPosition) {
    return {
      action: "close",
      side: positionSide,
      price: c.close,
      reason: "time_exit",
      description: `Time exit after ${barsHeld} bars (max: ${exit.timeExit.maxBarsInPosition})`,
      triggerTime: c.openTime,
    };
  }

  return null;
}

/**
 * Convenience: evaluate exit and return a BotIntent-compatible descriptor.
 */
export function generateCloseIntent(
  ctx: ExitEngineContext,
): {
  intentId: string;
  side: "BUY" | "SELL";
  qty: number;
  price: number;
  type: "EXIT";
  reason: ExitReason;
  description: string;
} | null {
  const signal = evaluateExit(ctx);
  if (!signal) return null;

  // Close side is opposite of position side
  const closeSide: "BUY" | "SELL" = signal.side === "long" ? "SELL" : "BUY";

  return {
    intentId: `exit_${signal.triggerTime}_${signal.reason}`,
    side: closeSide,
    qty: ctx.position.currentQty,
    price: signal.price,
    type: "EXIT",
    reason: signal.reason,
    description: signal.description,
  };
}

