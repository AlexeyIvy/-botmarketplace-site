/**
 * Backtest metrics — pure statistical functions over per-trade PnL series.
 *
 * Each function takes an array of per-trade PnL percentages and returns a
 * single scalar (or null when the metric cannot be computed). No I/O, no
 * dependencies on the evaluator, the database, or HTTP layer.
 *
 * Public API:
 *   - sharpeRatio     — annualized Sharpe (default 252 periods/year)
 *   - profitFactor    — gross profit / gross loss
 *   - expectancy      — winRate * avgWin - lossRate * avgLoss
 */

export { sharpeRatio } from "./sharpe.js";
export { profitFactor } from "./profitFactor.js";
export { expectancy } from "./expectancy.js";
