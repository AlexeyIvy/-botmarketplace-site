/**
 * Per-trade expectancy in percent units:
 *
 *   E = winRate * avgWin - lossRate * avgLoss
 *
 * where avgWin = mean(positive pnl%), avgLoss = mean(|negative pnl%|),
 * winRate = wins.length / totalTrades, lossRate = losses.length / totalTrades.
 *
 * Conventions:
 *   - Empty array       → null.
 *   - Single trade      → degenerates to its own pnl% (winRate=1, avgWin=pnl
 *                         for a winning trade; lossRate=1, avgLoss=|pnl| for
 *                         a losing trade).
 *   - Zero-pnl trades   → counted in totalTrades but contribute 0 to both
 *                         numerator and denominator.
 *
 * Result is rounded to 2 decimals.
 *
 * Pure, deterministic — no I/O, no side effects.
 *
 * @param pnlPcts Array of per-trade PnL percentages.
 */
export function expectancy(pnlPcts: number[]): number | null {
  if (pnlPcts.length === 0) return null;
  const wins = pnlPcts.filter((v) => v > 0);
  const losses = pnlPcts.filter((v) => v < 0).map((v) => -v);
  const winRate = wins.length / pnlPcts.length;
  const lossRate = losses.length / pnlPcts.length;
  const avgWin = wins.length ? wins.reduce((s, v) => s + v, 0) / wins.length : 0;
  const avgLoss = losses.length ? losses.reduce((s, v) => s + v, 0) / losses.length : 0;
  return Math.round((winRate * avgWin - lossRate * avgLoss) * 100) / 100;
}
