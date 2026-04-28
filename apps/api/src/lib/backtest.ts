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
 *   effectiveEntry = fillPrice * (1 + (feeBps + slippageBps) / 10_000)
 *   effectiveExit  = rawExit  * (1 - (feeBps + slippageBps) / 10_000)
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
  feeBps: number;
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
    feeBps: opts.feeBps ?? 0,
    slippageBps: opts.slippageBps ?? 0,
    fillAt: opts.fillAt ?? "CLOSE",
  }, mtfContext);
}
