/**
 * Profit factor — gross profit divided by gross loss.
 *
 *   profitFactor = sum(pnl% > 0) / |sum(pnl% < 0)|
 *
 * Conventions:
 *   - Empty array                 → null.
 *   - All wins, no losses         → +Infinity (consumers must handle this
 *                                   explicitly — e.g. ranking treats Infinity
 *                                   as "best", JSON serializers may need
 *                                   special handling).
 *   - All losses, no wins         → 0.
 *   - Both gross and loss are 0   → null (no information; trades were all
 *                                   exactly breakeven or array contains only
 *                                   zeros).
 *
 * Result is rounded to 2 decimals (Infinity is preserved as-is).
 *
 * Pure, deterministic — no I/O, no side effects.
 *
 * @param pnlPcts Array of per-trade PnL percentages.
 */
export function profitFactor(pnlPcts: number[]): number | null {
  if (pnlPcts.length === 0) return null;
  let gross = 0;
  let loss = 0;
  for (const v of pnlPcts) {
    if (v > 0) gross += v;
    else if (v < 0) loss += -v;
  }
  if (loss === 0 && gross === 0) return null;
  if (loss === 0) return Number.POSITIVE_INFINITY;
  return Math.round((gross / loss) * 100) / 100;
}
