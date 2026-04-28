/**
 * Annualized Sharpe ratio over per-trade PnL percentages.
 *
 *   Sharpe = (mean / stdDev) * sqrt(periodsPerYear)
 *
 * `stdDev` is the sample standard deviation (Bessel's correction, n-1).
 * Result is rounded to 2 decimals to match the historical lab.ts contract.
 *
 * Returns null when:
 *   - the input has fewer than 2 trades (variance undefined);
 *   - all returns are equal (stdDev = 0).
 *
 * Limitation: the function treats per-trade returns as if they were daily
 * returns; a more accurate annualization would require per-bar returns and
 * is left as future work. The 252-default mirrors the legacy implementation
 * in apps/api/src/routes/lab.ts (`computeSharpe`) bit-for-bit so existing
 * sweep results stay numerically comparable across the 49-T2/T3 migration.
 *
 * Pure, deterministic — no I/O, no side effects.
 *
 * @param pnlPcts        Array of per-trade PnL percentages.
 * @param periodsPerYear Annualization factor (default 252, ≈ trading days).
 */
export function sharpeRatio(pnlPcts: number[], periodsPerYear = 252): number | null {
  if (pnlPcts.length < 2) return null;
  const mean = pnlPcts.reduce((s, v) => s + v, 0) / pnlPcts.length;
  const variance =
    pnlPcts.reduce((s, v) => s + (v - mean) ** 2, 0) / (pnlPcts.length - 1);
  const stdDev = Math.sqrt(variance);
  if (stdDev === 0) return null;
  return Math.round((mean / stdDev) * Math.sqrt(periodsPerYear) * 100) / 100;
}
