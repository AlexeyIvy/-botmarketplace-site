import { describe, it, expect } from "vitest";
import { sharpeRatio } from "../../../src/lib/backtestMetrics/sharpe.js";

/**
 * Bit-for-bit copy of the pre-49-T3 `computeSharpe` from
 * apps/api/src/routes/lab.ts (lines 1461–1468 in main @ 6580564).
 * Locks the numerical contract so any future change to `sharpeRatio` is
 * caught against the historical lab.ts implementation.
 */
function legacyComputeSharpe(pnlPcts: number[]): number | null {
  if (pnlPcts.length < 2) return null;
  const mean = pnlPcts.reduce((s, v) => s + v, 0) / pnlPcts.length;
  const variance =
    pnlPcts.reduce((s, v) => s + (v - mean) ** 2, 0) / (pnlPcts.length - 1);
  const stdDev = Math.sqrt(variance);
  if (stdDev === 0) return null;
  return Math.round((mean / stdDev) * Math.sqrt(252) * 100) / 100;
}

describe("sharpeRatio", () => {
  it("returns null for fewer than 2 trades", () => {
    expect(sharpeRatio([])).toBeNull();
    expect(sharpeRatio([1.5])).toBeNull();
  });

  it("returns null when all returns are equal (stdDev = 0)", () => {
    expect(sharpeRatio([2, 2, 2, 2])).toBeNull();
    expect(sharpeRatio([0, 0])).toBeNull();
  });

  it("matches a hand-calculated reference (mixed wins/losses)", () => {
    // Hand-calc:
    //   pnl = [2, -1, 3, -2, 1]
    //   mean = 3/5 = 0.6
    //   sumSq = 1.96 + 2.56 + 5.76 + 6.76 + 0.16 = 17.2
    //   variance = 17.2 / (5 - 1) = 4.3
    //   stdDev = sqrt(4.3) ≈ 2.0736
    //   mean / stdDev ≈ 0.28934
    //   * sqrt(252) ≈ 4.5933 → rounded 4.59
    expect(sharpeRatio([2, -1, 3, -2, 1])).toBeCloseTo(4.59, 2);
  });

  it("returns a negative value for a losing series with positive variance", () => {
    const result = sharpeRatio([-1, -2, -0.5]);
    expect(result).not.toBeNull();
    expect(result as number).toBeLessThan(0);
  });

  it("respects custom periodsPerYear", () => {
    // sqrt(1) = 1 → annualization is a no-op, just rounded mean/stdDev.
    const result = sharpeRatio([2, -1, 3, -2, 1], 1);
    // mean/stdDev ≈ 0.28934, rounded 0.29
    expect(result).toBeCloseTo(0.29, 2);
  });

  it("is bit-for-bit identical to the legacy computeSharpe (regression anchor)", () => {
    const fixtures: number[][] = [
      [],
      [3.5],
      [2, -1, 3, -2, 1],
      [1.5, 2.0, 0.5],
      [-1, -2, -0.5],
      [0.1, -0.05, 0.2, -0.15, 0.3, -0.1],
      Array.from({ length: 50 }, (_, i) => Math.sin(i / 5)),
    ];
    for (const fx of fixtures) {
      expect(sharpeRatio(fx)).toBe(legacyComputeSharpe(fx));
    }
  });
});
