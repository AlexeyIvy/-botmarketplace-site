/**
 * Backtest engine (#126) — DSL-driven evaluation.
 *
 * All backtest behavior is now driven by compiled Strategy DSL.
 * The old hardcoded price-breakout algorithm has been removed.
 *
 * This module re-exports the DSL evaluator as the primary `runBacktest` function
 * and maintains backward-compatible report types.
 *
 * Execution realism:
 *   fillAt — fill price reference (default "CLOSE", backward-compatible):
 *     "CLOSE"     — fill at the signal candle's close (legacy default)
 *     "OPEN"      — fill at the signal candle's open
 *     "NEXT_OPEN" — fill at the next candle's open (lookahead-free for
 *                   indicator signals computed on closed bars)
 *   feeBps / takerFeeBps / makerFeeBps:
 *     `takerFeeBps` is the canonical taker-fee field. `feeBps` is a
 *     backward-compat alias that maps to `takerFeeBps` when the latter is
 *     omitted. `makerFeeBps` is reserved for the upcoming limit-order
 *     backtest mode and is currently unused in the formulas — every fill is
 *     market (taker).
 *   effectiveEntry = fillPrice * (1 + (takerFeeBps + slippageBps) / 10_000)
 *   effectiveExit  = rawExit  * (1 - (takerFeeBps + slippageBps) / 10_000)
 *   Slippage is symmetric: applied at both entry (cost up) and exit
 *   (proceeds down) — round-trip cost reflects realistic market conditions.
 *   At slippageBps = 0 the formulas reduce to fee-only behavior; existing
 *   results with default slippage stay bit-for-bit unchanged.
 *   SL/TP/trailing trigger on intra-bar high/low and execute at their own
 *   trigger prices — fillAt does not apply to them. fillAt applies only to
 *   entry and indicator_exit fills.
 */

import type { Candle } from "./bybitCandles.js";
import { runDslBacktest } from "./dslEvaluator.js";
import type { DslBacktestReport, DslTradeRecord, MtfBacktestContext, DslFillAt } from "./dslEvaluator.js";

// Re-export DSL evaluator types as canonical backtest types
export type { DslBacktestReport as BacktestReport, DslTradeRecord as TradeRecord, MtfBacktestContext };

export type FillAt = DslFillAt;

export interface ExecOpts {
  /**
   * @deprecated Use {@link takerFeeBps} instead. Retained as a backward-compat
   * alias: when `takerFeeBps` is omitted, `feeBps` populates it.
   */
  feeBps?: number;
  /** Taker (market-order) fee in basis points. Used for all current fills. */
  takerFeeBps?: number;
  /** Maker (limit-order) fee in basis points. Reserved for future limit-order backtest. */
  makerFeeBps?: number;
  slippageBps: number;
  fillAt: FillAt;
}

/**
 * Run a DSL-driven backtest.
 *
 * @param candleData  Sorted OHLCV candle array (primary timeframe)
 * @param dslJson     Compiled strategy DSL (from StrategyVersion.dslJson)
 * @param opts        Execution options (feeBps, slippageBps, fillAt)
 * @param mtfContext  Optional multi-timeframe context for MTF strategies (#134)
 * @returns           Deterministic backtest report
 */
export function runBacktest(
  candleData: Candle[],
  dslJson: unknown,
  opts: Partial<ExecOpts> = {},
  mtfContext?: MtfBacktestContext,
): DslBacktestReport {
  return runDslBacktest(candleData, dslJson, {
    feeBps: opts.feeBps,
    takerFeeBps: opts.takerFeeBps,
    makerFeeBps: opts.makerFeeBps,
    slippageBps: opts.slippageBps ?? 0,
    fillAt: opts.fillAt ?? "CLOSE",
  }, mtfContext);
}
