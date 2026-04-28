/**
 * 49-T4: shared reference fixtures for backtestMetrics tests.
 *
 * Five canonical pnlPcts shapes covering empty, single-trade, mixed,
 * all-wins, and all-losses. Each fixture has a hand-calculated comment
 * recording the expected sharpe / profitFactor / expectancy values; the
 * actual numeric assertions live in the *.test.ts files alongside.
 *
 * Do NOT edit these arrays without justification — they are the
 * regression contract for the 49-T1 utilities and the 49-T2 report.
 * Any change must be paired with a PR that explains why the underlying
 * math has shifted.
 */

/** Empty input — every metric is null (no trades). */
export const EMPTY: number[] = [];

/** Single winning trade — sharpe is null (n<2), pf is +Infinity (no losses), expectancy is the trade's own pnl%. */
export const SINGLE_WIN: number[] = [3.5];

/**
 * Balanced mixed series.
 *   mean    = 0.6
 *   variance(n-1) = 17.2 / 4 = 4.3
 *   stdDev  ≈ 2.0736
 *   sharpe  = round(mean/stdDev * sqrt(252) * 100) / 100 ≈ 4.59
 *   pf      = sum(>0)/|sum(<0)| = 6/3 = 2.00
 *   exp     = 0.6*2 - 0.4*1.5 = 0.60
 */
export const MIXED_BALANCED: number[] = [2, -1, 3, -2, 1];

/**
 * All-wins series.
 *   mean    = 4/3
 *   variance(n-1) = 7/12
 *   stdDev  ≈ 0.7638
 *   sharpe  = round(mean/stdDev * sqrt(252) * 100) / 100 ≈ 27.71
 *   pf      = +Infinity (no losses)
 *   exp     = winRate(1) * avgWin(4/3) - 0 = 1.33
 */
export const ALL_WINS: number[] = [1.5, 2.0, 0.5];

/**
 * All-losses series — mirror of ALL_WINS.
 *   mean    = -7/6
 *   stdDev  ≈ 0.7638 (same magnitudes, symmetric)
 *   sharpe  = round(mean/stdDev * sqrt(252) * 100) / 100 ≈ -24.25
 *   pf      = 0 (no wins)
 *   exp     = 0 - lossRate(1) * avgLoss(7/6) = -1.17
 */
export const ALL_LOSSES: number[] = [-1, -2, -0.5];

export const ALL_FIXTURES = {
  EMPTY,
  SINGLE_WIN,
  MIXED_BALANCED,
  ALL_WINS,
  ALL_LOSSES,
} as const;
