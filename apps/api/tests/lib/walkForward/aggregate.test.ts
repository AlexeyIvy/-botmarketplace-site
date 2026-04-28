import { describe, it, expect } from "vitest";
import { aggregate } from "../../../src/lib/walkForward/aggregate.js";
import type { FoldReport } from "../../../src/lib/walkForward/types.js";
import type { DslBacktestReport } from "../../../src/lib/dslEvaluator.js";

function fakeReport(totalPnlPct: number, sharpe: number | null = null): DslBacktestReport {
  return {
    trades: 0,
    wins: 0,
    winrate: 0,
    totalPnlPct,
    maxDrawdownPct: 0,
    candles: 0,
    tradeLog: [],
    sharpe,
    profitFactor: null,
    expectancy: null,
  };
}

function fold(
  i: number,
  isPnl: number,
  oosPnl: number,
  isSharpe: number | null = null,
  oosSharpe: number | null = null,
): FoldReport {
  return {
    foldIndex: i,
    isReport: fakeReport(isPnl, isSharpe),
    oosReport: fakeReport(oosPnl, oosSharpe),
    isRange: { fromIndex: 0, toIndex: 0, fromTsMs: 0, toTsMs: 0 },
    oosRange: { fromIndex: 0, toIndex: 0, fromTsMs: 0, toTsMs: 0 },
  };
}

describe("walkForward.aggregate", () => {
  it("hand-calculated reference: 3 folds with mixed pnl + sharpe", () => {
    const folds = [
      fold(0, 5,  3,  1.5, 0.8),
      fold(1, 4, -1,  1.0, 0.4),
      fold(2, 6,  2,  null, null),
    ];
    const agg = aggregate(folds);

    // avgIsPnlPct = (5 + 4 + 6) / 3 = 5.0
    // avgOosPnlPct = (3 + (-1) + 2) / 3 = 4/3 ≈ 1.33
    // totalOosPnlPct = 4
    // avgIsSharpe (skipping null): (1.5 + 1.0) / 2 = 1.25
    // avgOosSharpe: (0.8 + 0.4) / 2 = 0.6
    // isOosPnlRatio = 1.33 / 5 ≈ 0.267 → 0.27
    // oosWinFoldShare = 2 wins / 3 folds = 0.67
    expect(agg.foldCount).toBe(3);
    expect(agg.avgIsPnlPct).toBe(5);
    expect(agg.avgOosPnlPct).toBe(1.33);
    expect(agg.totalOosPnlPct).toBe(4);
    expect(agg.avgIsSharpe).toBe(1.25);
    expect(agg.avgOosSharpe).toBe(0.6);
    expect(agg.isOosPnlRatio).toBe(0.27);
    expect(agg.oosWinFoldShare).toBe(0.67);
  });

  it("oosWinFoldShare = 0 when every fold's OOS pnl is 0 or negative", () => {
    const folds = [fold(0, 1, 0), fold(1, 1, -2), fold(2, 1, 0)];
    expect(aggregate(folds).oosWinFoldShare).toBe(0);
  });

  it("avgOosSharpe = null when every fold's OOS sharpe is null", () => {
    const folds = [
      fold(0, 1, 1, 0.5, null),
      fold(1, 1, 1, 0.5, null),
    ];
    expect(aggregate(folds).avgOosSharpe).toBeNull();
    // avgIsSharpe still defined because IS sharpes are present.
    expect(aggregate(folds).avgIsSharpe).toBe(0.5);
  });

  it("isOosPnlRatio = null when avgIsPnlPct is exactly 0 (avoid division by 0)", () => {
    const folds = [
      fold(0,  5, 1),
      fold(1, -5, 2),
    ];
    // avgIsPnlPct = 0
    expect(aggregate(folds).isOosPnlRatio).toBeNull();
  });

  it("ignores null sharpes when computing the mean", () => {
    // Three IS sharpes: 1.0, null, 3.0 → mean over non-null = 2.0
    const folds = [
      fold(0, 1, 1, 1.0, null),
      fold(1, 1, 1, null, 1.5),
      fold(2, 1, 1, 3.0, null),
    ];
    const agg = aggregate(folds);
    expect(agg.avgIsSharpe).toBe(2);
    expect(agg.avgOosSharpe).toBe(1.5);
  });

  it("empty folds array returns zero/null aggregate (degenerate case)", () => {
    const agg = aggregate([]);
    expect(agg).toEqual({
      foldCount: 0,
      avgIsPnlPct: 0,
      avgOosPnlPct: 0,
      totalOosPnlPct: 0,
      avgIsSharpe: null,
      avgOosSharpe: null,
      isOosPnlRatio: null,
      oosWinFoldShare: 0,
    });
  });

  it("rounds avg / total / ratio fields to 2 decimal places", () => {
    const folds = [
      fold(0, 1.111, 2.222, 0.333, 0.444),
      fold(1, 2.345, 1.005, 0.667, 0.556),
    ];
    const agg = aggregate(folds);
    // Each field — Math.round(x * 100) / 100; just check shape, not exact math.
    for (const k of ["avgIsPnlPct", "avgOosPnlPct", "totalOosPnlPct", "isOosPnlRatio", "avgIsSharpe", "avgOosSharpe"] as const) {
      const v = agg[k];
      if (v !== null) {
        expect(Math.round(v * 100) / 100).toBe(v);
      }
    }
  });

  it("totalOosPnlPct is a naive sum, not a compound (documented limitation)", () => {
    const folds = [fold(0, 0, 10), fold(1, 0, 10), fold(2, 0, 10)];
    expect(aggregate(folds).totalOosPnlPct).toBe(30);
  });
});
