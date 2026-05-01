/**
 * Backtest engine (#126) — DSL-driven evaluation.
 *
 * All backtest behavior is now driven by compiled Strategy DSL.
 * The old hardcoded price-breakout algorithm has been removed.
 *
 * This module re-exports the DSL evaluator as the primary `runBacktest` function
 * and maintains backward-compatible report types.
 *
 * Execution realism:
 *   fillAt — fill price reference (default "CLOSE", backward-compatible):
 *     "CLOSE"     — fill at the signal candle's close (legacy default)
 *     "OPEN"      — fill at the signal candle's open
 *     "NEXT_OPEN" — fill at the next candle's open (lookahead-free for
 *                   indicator signals computed on closed bars)
 *   feeBps / takerFeeBps / makerFeeBps:
 *     `takerFeeBps` is the canonical taker-fee field. `feeBps` is a
 *     backward-compat alias that maps to `takerFeeBps` when the latter is
 *     omitted. `makerFeeBps` is reserved for the upcoming limit-order
 *     backtest mode and is currently unused in the formulas — every fill is
 *     market (taker).
 *   effectiveEntry = fillPrice * (1 + (takerFeeBps + slippageBps) / 10_000)
 *   effectiveExit  = rawExit  * (1 - (takerFeeBps + slippageBps) / 10_000)
 *   Slippage is symmetric: applied at both entry (cost up) and exit
 *   (proceeds down) — round-trip cost reflects realistic market conditions.
 *   At slippageBps = 0 the formulas reduce to fee-only behavior; existing
 *   results with default slippage stay bit-for-bit unchanged.
 *   SL/TP/trailing trigger on intra-bar high/low and execute at their own
 *   trigger prices — fillAt does not apply to them. fillAt applies only to
 *   entry and indicator_exit fills.
 */

import type { Candle } from "./bybitCandles.js";
import { runDslBacktest } from "./dslEvaluator.js";
import type { DslBacktestReport, DslTradeRecord, MtfBacktestContext, DslFillAt } from "./dslEvaluator.js";
import {
  TIMEFRAME_TO_INTERVAL,
  createClosedCandleBundle,
  type Interval,
  type MtfCandle,
} from "./mtf/intervalAlignment.js";
import type { CandlesByInterval } from "./mtf/loadCandleBundle.js";
import type { CandleInterval } from "../types/datasetBundle.js";

// Re-export DSL evaluator types as canonical backtest types
export type { DslBacktestReport as BacktestReport, DslTradeRecord as TradeRecord, MtfBacktestContext };

export type FillAt = DslFillAt;

export interface ExecOpts {
  /**
   * @deprecated Use {@link takerFeeBps} instead. Retained as a backward-compat
   * alias: when `takerFeeBps` is omitted, `feeBps` populates it.
   */
  feeBps?: number;
  /** Taker (market-order) fee in basis points. Used for all current fills. */
  takerFeeBps?: number;
  /** Maker (limit-order) fee in basis points. Reserved for future limit-order backtest. */
  makerFeeBps?: number;
  slippageBps: number;
  fillAt: FillAt;
}

/**
 * Run a DSL-driven backtest.
 *
 * @param candleData  Sorted OHLCV candle array (primary timeframe)
 * @param dslJson     Compiled strategy DSL (from StrategyVersion.dslJson)
 * @param opts        Execution options (feeBps, slippageBps, fillAt)
 * @param mtfContext  Optional multi-timeframe context for MTF strategies (#134)
 * @returns           Deterministic backtest report
 */
export function runBacktest(
  candleData: Candle[],
  dslJson: unknown,
  opts: Partial<ExecOpts> = {},
  mtfContext?: MtfBacktestContext,
): DslBacktestReport {
  return runDslBacktest(candleData, dslJson, {
    feeBps: opts.feeBps,
    takerFeeBps: opts.takerFeeBps,
    makerFeeBps: opts.makerFeeBps,
    slippageBps: opts.slippageBps ?? 0,
    fillAt: opts.fillAt ?? "CLOSE",
  }, mtfContext);
}

// ---------------------------------------------------------------------------
// Multi-interval bundle entry point (docs/52-T4)
// ---------------------------------------------------------------------------

/**
 * Convert a `MarketCandle` row (Decimal-backed, BigInt openTimeMs) into the
 * lightweight `MtfCandle` shape used by the alignment helpers / evaluator.
 */
function toMtfCandle(row: {
  openTimeMs: bigint;
  open: { toString(): string } | number;
  high: { toString(): string } | number;
  low: { toString(): string } | number;
  close: { toString(): string } | number;
  volume: { toString(): string } | number;
}): MtfCandle {
  return {
    openTime: Number(row.openTimeMs),
    open: typeof row.open === "number" ? row.open : Number(row.open.toString()),
    high: typeof row.high === "number" ? row.high : Number(row.high.toString()),
    low: typeof row.low === "number" ? row.low : Number(row.low.toString()),
    close: typeof row.close === "number" ? row.close : Number(row.close.toString()),
    volume: typeof row.volume === "number" ? row.volume : Number(row.volume.toString()),
  };
}

/** Translate a Prisma `CandleInterval` enum into the alignment-helper string. */
function toAlignmentInterval(interval: CandleInterval): Interval {
  const out = TIMEFRAME_TO_INTERVAL[interval];
  if (!out) {
    throw new Error(`runBacktestWithBundle: unsupported interval "${interval}"`);
  }
  return out;
}

export interface RunBacktestWithBundleArgs {
  /** Candles per interval as returned by `loadCandleBundle`. */
  bundle: CandlesByInterval;
  /** Drives bar iteration; must be a key of `bundle`. */
  primaryInterval: CandleInterval;
  dslJson: unknown;
  opts?: Partial<ExecOpts>;
}

/**
 * Run a backtest from a multi-interval candle bundle.
 *
 * Iterates the primary-TF candles; HTF context is exposed to the evaluator
 * via a {@link createClosedCandleBundle} (look-ahead-safe) — at every
 * primary bar `i`, an HTF indicator can only see HTF candles whose period
 * has fully closed by `primary[i].openTime`.
 */
export function runBacktestWithBundle(args: RunBacktestWithBundleArgs): DslBacktestReport {
  const primaryRows = args.bundle.get(args.primaryInterval);
  if (!primaryRows) {
    throw new Error(
      `runBacktestWithBundle: primary interval "${args.primaryInterval}" missing from bundle`,
    );
  }
  if (primaryRows.length === 0) {
    return {
      trades: 0, wins: 0, winrate: 0, totalPnlPct: 0, maxDrawdownPct: 0,
      candles: 0, tradeLog: [], sharpe: null, profitFactor: null, expectancy: null,
    };
  }

  // Build a Record<intervalString, MtfCandle[]> for the alignment helpers.
  // Skip intervals the alignment module does not understand (M30 — no
  // mapping in TIMEFRAME_TO_INTERVAL today; runtime tolerates this and the
  // backtest path simply ignores unmappable intervals).
  const candlesByInterval: Record<string, MtfCandle[]> = {};
  for (const [interval, rows] of args.bundle.entries()) {
    const aligned = TIMEFRAME_TO_INTERVAL[interval];
    if (!aligned) continue;
    candlesByInterval[aligned] = rows.map(toMtfCandle);
  }

  const primaryAligned = toAlignmentInterval(args.primaryInterval);
  const candleBundle = createClosedCandleBundle(primaryAligned, candlesByInterval);
  const primaryCandles = candlesByInterval[primaryAligned];

  return runBacktest(
    primaryCandles as unknown as Candle[],
    args.dslJson,
    args.opts,
    { bundle: candleBundle },
  );
}
