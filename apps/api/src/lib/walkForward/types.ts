/**
 * Walk-forward validation — shared types.
 *
 * Configuration is expressed in **bars** (candle counts), not in time, so
 * the layout is deterministic regardless of gaps in the underlying market
 * data. See docs/48 §«Решение по форме fold-конфигурации».
 */

import type { Candle } from "../bybitCandles.js";
import type { DslBacktestReport } from "../dslEvaluator.js";

export type FoldConfig = {
  /** Length of the in-sample window (bars). Must be > 0. */
  isBars: number;
  /** Length of the out-of-sample window (bars). Must be > 0. */
  oosBars: number;
  /** Step between consecutive folds (bars). Must be > 0. Equal to oosBars
   *  for non-overlapping OOS blocks; smaller values produce overlapping
   *  OOS regions and are flagged as a `warning` by the HTTP layer (48-T5),
   *  but the pure split allows them. */
  step: number;
  /** When true, the IS window starts at index 0 and only grows; when false,
   *  the IS window has a fixed length and the whole pair slides. */
  anchored: boolean;
};

export type FoldRange = {
  fromIndex: number;
  /** Exclusive end index (matches Array.prototype.slice semantics). */
  toIndex: number;
  /** First candle's openTime in ms. */
  fromTsMs: number;
  /** Last candle's openTime in ms (inclusive). */
  toTsMs: number;
};

export type Fold = {
  foldIndex: number;
  isSlice: Candle[];
  oosSlice: Candle[];
  isRange: FoldRange;
  oosRange: FoldRange;
};

/** Per-fold backtest reports paired with the slice ranges they were run on. */
export type FoldReport = {
  foldIndex: number;
  isReport: DslBacktestReport;
  oosReport: DslBacktestReport;
  isRange: FoldRange;
  oosRange: FoldRange;
};

/**
 * Aggregate metrics across all folds in a walk-forward run.
 *
 *   foldCount         — number of folds (FoldReport[] length).
 *   avgIsPnlPct       — mean of isReport.totalPnlPct across folds.
 *   avgOosPnlPct      — mean of oosReport.totalPnlPct across folds.
 *   totalOosPnlPct    — naive sum of oosReport.totalPnlPct (no compounding;
 *                       first-version limitation, documented in aggregate.ts).
 *   avgIsSharpe       — mean of non-null isReport.sharpe; null if all null.
 *   avgOosSharpe      — mean of non-null oosReport.sharpe; null if all null.
 *   isOosPnlRatio     — avgOosPnlPct / avgIsPnlPct; null when avgIsPnlPct = 0.
 *   oosWinFoldShare   — fraction of folds with oosReport.totalPnlPct > 0.
 */
export type WalkForwardAggregate = {
  foldCount: number;
  avgIsPnlPct: number;
  avgOosPnlPct: number;
  totalOosPnlPct: number;
  avgIsSharpe: number | null;
  avgOosSharpe: number | null;
  isOosPnlRatio: number | null;
  oosWinFoldShare: number;
};

/** Walk-forward run output: per-fold reports plus an aggregate summary. */
export type WalkForwardReport = {
  folds: FoldReport[];
  aggregate: WalkForwardAggregate;
};
