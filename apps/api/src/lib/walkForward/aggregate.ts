/**
 * Walk-forward aggregate metrics — pure summary over FoldReport[].
 *
 * After docs/49-T2 (closed), `DslBacktestReport.sharpe` is populated
 * directly by the engine, so the aggregate reads it straight from each
 * fold's report — no local sharpe helper is needed.
 *
 * Limitation: `totalOosPnlPct` is a naive arithmetic sum of OOS pnl%
 * across folds, not a compounded equity. Compounding requires a
 * notional-tracking model that is out of scope for the first walk-
 * forward version.
 *
 * Pure function — no I/O, no mutations.
 */

import type { FoldReport, WalkForwardAggregate } from "./types.js";

/** Round a finite number to 2 decimal places (matches the engine's
 *  totalPnlPct rounding, so aggregate fields read as "X.XX"). */
function r2(x: number): number {
  return Math.round(x * 100) / 100;
}

function mean(values: number[]): number {
  if (values.length === 0) return 0;
  return values.reduce((s, v) => s + v, 0) / values.length;
}

function meanIgnoringNull(values: (number | null)[]): number | null {
  const filtered = values.filter((v): v is number => v !== null);
  if (filtered.length === 0) return null;
  return mean(filtered);
}

export function aggregate(folds: FoldReport[]): WalkForwardAggregate {
  const foldCount = folds.length;

  if (foldCount === 0) {
    return {
      foldCount: 0,
      avgIsPnlPct: 0,
      avgOosPnlPct: 0,
      totalOosPnlPct: 0,
      avgIsSharpe: null,
      avgOosSharpe: null,
      isOosPnlRatio: null,
      oosWinFoldShare: 0,
    };
  }

  const isPnls = folds.map((f) => f.isReport.totalPnlPct);
  const oosPnls = folds.map((f) => f.oosReport.totalPnlPct);

  const avgIsPnlPct = mean(isPnls);
  const avgOosPnlPct = mean(oosPnls);
  const totalOosPnlPct = oosPnls.reduce((s, v) => s + v, 0);

  const avgIsSharpeRaw = meanIgnoringNull(folds.map((f) => f.isReport.sharpe));
  const avgOosSharpeRaw = meanIgnoringNull(folds.map((f) => f.oosReport.sharpe));

  const isOosPnlRatio = avgIsPnlPct === 0 ? null : avgOosPnlPct / avgIsPnlPct;
  const oosWinFoldShare = oosPnls.filter((v) => v > 0).length / foldCount;

  return {
    foldCount,
    avgIsPnlPct: r2(avgIsPnlPct),
    avgOosPnlPct: r2(avgOosPnlPct),
    totalOosPnlPct: r2(totalOosPnlPct),
    avgIsSharpe: avgIsSharpeRaw === null ? null : r2(avgIsSharpeRaw),
    avgOosSharpe: avgOosSharpeRaw === null ? null : r2(avgOosSharpeRaw),
    isOosPnlRatio: isOosPnlRatio === null ? null : r2(isOosPnlRatio),
    oosWinFoldShare: r2(oosWinFoldShare),
  };
}
