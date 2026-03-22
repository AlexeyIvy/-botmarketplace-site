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
 *   fillAt = "CLOSE" — fill at candle close price (only supported value)
 *   effectiveEntry = fillPrice * (1 + (feeBps + slippageBps) / 10_000)
 *   effectiveExit  = rawExit  * (1 - feeBps / 10_000)
 *   SL/TP levels and pnlPct are all computed from effective prices.
 */

import type { Candle } from "./bybitCandles.js";
import { runDslBacktest } from "./dslEvaluator.js";
import type { DslBacktestReport, DslTradeRecord } from "./dslEvaluator.js";

// Re-export DSL evaluator types as canonical backtest types
export type { DslBacktestReport as BacktestReport, DslTradeRecord as TradeRecord };

export interface ExecOpts {
  feeBps: number;
  slippageBps: number;
  fillAt: "CLOSE";
}

/**
 * Run a DSL-driven backtest.
 *
 * @param candleData  Sorted OHLCV candle array
 * @param dslJson     Compiled strategy DSL (from StrategyVersion.dslJson)
 * @param opts        Execution options (feeBps, slippageBps, fillAt)
 * @returns           Deterministic backtest report
 */
export function runBacktest(
  candleData: Candle[],
  dslJson: unknown,
  opts: Partial<ExecOpts> = {},
): DslBacktestReport {
  return runDslBacktest(candleData, dslJson, {
    feeBps: opts.feeBps ?? 0,
    slippageBps: opts.slippageBps ?? 0,
  });
}
