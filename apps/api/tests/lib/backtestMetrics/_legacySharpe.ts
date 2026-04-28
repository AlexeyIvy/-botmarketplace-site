/**
 * 49-T4: archived bit-for-bit copy of the pre-49-T3 `computeSharpe`
 * helper from `apps/api/src/routes/lab.ts` (lines 1463–1471 in main
 * @ commit 3d1c307, removed in #305).
 *
 * @deprecated Reference implementation only. Used as the regression
 * anchor for `sharpeRatio` in `apps/api/src/lib/backtestMetrics/sharpe.ts`.
 * Keep until either:
 *   (a) one minor release passes after 49-T3 with no regressions, or
 *   (b) the core team explicitly approves removal because no consumer
 *       depends on the legacy contract any more.
 *
 * Do not extend, fix, or import this file from production code.
 */

export function legacyComputeSharpe(pnlPcts: number[]): number | null {
  if (pnlPcts.length < 2) return null;
  const mean = pnlPcts.reduce((s, v) => s + v, 0) / pnlPcts.length;
  const variance =
    pnlPcts.reduce((s, v) => s + (v - mean) ** 2, 0) / (pnlPcts.length - 1);
  const stdDev = Math.sqrt(variance);
  if (stdDev === 0) return null;
  return Math.round((mean / stdDev) * Math.sqrt(252) * 100) / 100;
}
