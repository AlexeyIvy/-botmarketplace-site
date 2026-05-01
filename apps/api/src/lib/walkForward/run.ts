/**
 * Walk-forward runner — per-fold backtest without aggregation.
 *
 * Two entry points:
 *
 *   1. `runWalkForward(candles, ...)` — legacy single-TF path. Iterates the
 *      primary candle array, runs `runBacktest` twice per fold. MTF DSLs
 *      are rejected up front via `WalkForwardMtfNotSupportedError` because
 *      no HTF data is available to align against.
 *
 *   2. `runWalkForwardWithBundle({ bundle, primaryInterval, ... })` — the
 *      multi-interval path (docs/52 follow-up). Splits the *primary* TF
 *      into folds; for each fold, slices every interval in the bundle by
 *      the primary fold's `[fromTsMs, toTsMs]` window and feeds the
 *      resulting per-fold bundle into `runBacktestWithBundle`. The
 *      look-ahead-safe alignment used by `createClosedCandleBundle`
 *      (inside `runBacktestWithBundle`) ensures HTF candles that have not
 *      closed by a primary bar's open time are excluded.
 *
 * The function is otherwise pure: no I/O, only the optional `onProgress`
 * callback (used by the BD wrapper in 48-T5 to surface progress).
 *
 * Determinism: mirrors the contracts of `split` (48-T1) and `runBacktest`
 * (docs/44 §Детерминизм). Identical inputs always produce identical output.
 */

import type { MarketCandle } from "@prisma/client";
import type { Candle } from "../bybitCandles.js";
import type { DslExecOpts } from "../dslEvaluator.js";
import { runBacktest, runBacktestWithBundle } from "../backtest.js";
import type { CandlesByInterval } from "../mtf/loadCandleBundle.js";
import type { CandleInterval } from "../../types/datasetBundle.js";
import { split } from "./split.js";
import { aggregate } from "./aggregate.js";
import type {
  FoldConfig,
  FoldReport,
  WalkForwardReport,
} from "./types.js";

/**
 * Thrown when a DSL contains at least one indicator with a non-empty
 * `sourceTimeframe` and no bundle is supplied. The HTTP layer (48-T5)
 * translates this into a 400 with the prescribed user-facing message.
 *
 * Bundle-aware walk-forward (`runWalkForwardWithBundle`) does *not*
 * throw this — MTF DSLs are first-class on that path.
 */
export class WalkForwardMtfNotSupportedError extends Error {
  constructor(public readonly indicatorType: string, public readonly sourceTimeframe: string) {
    super(
      `Walk-forward для MTF-стратегий требует datasetBundleJson: индикатор '${indicatorType}' использует sourceTimeframe='${sourceTimeframe}'. Передайте bundle в запрос.`,
    );
    this.name = "WalkForwardMtfNotSupportedError";
  }
}

/**
 * Recursively scan a JSON-shaped value for the first object that carries
 * a non-empty `sourceTimeframe` key alongside an indicator-like `type`
 * field. Returns `{ type, sourceTimeframe }` for the first match or `null`.
 *
 * The scanner walks plain objects and arrays; primitives are ignored.
 * It does not interpret the DSL semantically — any JSON-shaped DSL is
 * acceptable input. This is a structural pre-flight, not a semantic one.
 */
function findMtfIndicator(node: unknown): { type: string; sourceTimeframe: string } | null {
  if (Array.isArray(node)) {
    for (const item of node) {
      const hit = findMtfIndicator(item);
      if (hit) return hit;
    }
    return null;
  }
  if (node && typeof node === "object") {
    const obj = node as Record<string, unknown>;
    const stf = obj.sourceTimeframe;
    if (typeof stf === "string" && stf.length > 0) {
      const t = typeof obj.type === "string" ? obj.type : "<unknown>";
      return { type: t, sourceTimeframe: stf };
    }
    for (const v of Object.values(obj)) {
      const hit = findMtfIndicator(v);
      if (hit) return hit;
    }
  }
  return null;
}

export function runWalkForward(
  candles: Candle[],
  dslJson: unknown,
  opts: Partial<DslExecOpts>,
  foldCfg: FoldConfig,
  onProgress?: (done: number, total: number) => void,
): WalkForwardReport {
  // Single-TF path: walk-forward does not slice MTF contexts here, so a
  // strategy that references another timeframe would silently fall back
  // to the primary TF and produce different signals. Reject up front and
  // direct the caller to the bundle-aware path below.
  const mtfHit = findMtfIndicator(dslJson);
  if (mtfHit) {
    throw new WalkForwardMtfNotSupportedError(mtfHit.type, mtfHit.sourceTimeframe);
  }

  const folds = split(candles, foldCfg);

  const folded: FoldReport[] = folds.map((fold) => {
    // Two independent runBacktest calls per fold — IS and OOS are
    // evaluated as standalone backtests so each fold's report is
    // self-contained. mtfContext is intentionally undefined; MTF is
    // gated by the pre-flight above.
    const isReport = runBacktest(fold.isSlice, dslJson, opts, undefined);
    const oosReport = runBacktest(fold.oosSlice, dslJson, opts, undefined);
    onProgress?.(fold.foldIndex + 1, folds.length);
    return {
      foldIndex: fold.foldIndex,
      isReport,
      oosReport,
      isRange: fold.isRange,
      oosRange: fold.oosRange,
    };
  });

  return { folds: folded, aggregate: aggregate(folded) };
}

// ---------------------------------------------------------------------------
// Bundle-aware path
// ---------------------------------------------------------------------------

export interface RunWalkForwardWithBundleArgs {
  /** Candles per interval, as returned by `loadCandleBundle({mode:'backtest'})`. */
  bundle: CandlesByInterval;
  /** Drives fold iteration; must be a key of `bundle`. */
  primaryInterval: CandleInterval;
  dslJson: unknown;
  opts: Partial<DslExecOpts>;
  foldCfg: FoldConfig;
  onProgress?: (done: number, total: number) => void;
}

/**
 * Slice a bundle by the [fromTsMs, toTsMs] window of a primary fold.
 *
 * Inclusive on both ends — the window comes from {@link FoldRange} which
 * stores the open time of the first and last primary candle. Each
 * interval is filtered independently; HTF candles whose open time falls
 * within the primary window are kept. Look-ahead safety is delegated to
 * {@link runBacktestWithBundle}, which builds a closed-bundle alignment
 * map internally.
 */
function sliceBundleByWindow(
  bundle: CandlesByInterval,
  fromTsMs: number,
  toTsMs: number,
): CandlesByInterval {
  const out: CandlesByInterval = new Map();
  const fromBig = BigInt(fromTsMs);
  const toBig = BigInt(toTsMs);
  for (const [interval, rows] of bundle.entries()) {
    const sliced: MarketCandle[] = [];
    for (const c of rows) {
      const t = c.openTimeMs;
      if (t >= fromBig && t <= toBig) sliced.push(c);
    }
    out.set(interval, sliced);
  }
  return out;
}

/** Convert a `MarketCandle` row to the {@link Candle} shape consumed by `split`.
 *
 *  Mirrors the OHLCV decoding in `backtest.ts:toMtfCandle` so the wrapper
 *  is robust to test fixtures that pass plain numbers in place of Prisma
 *  Decimals. */
function toCandle(row: MarketCandle): Candle {
  const num = (v: { toString(): string } | number): number =>
    typeof v === "number" ? v : Number(v.toString());
  return {
    openTime: Number(row.openTimeMs),
    open: num(row.open),
    high: num(row.high),
    low: num(row.low),
    close: num(row.close),
    volume: num(row.volume),
  };
}

export function runWalkForwardWithBundle(args: RunWalkForwardWithBundleArgs): WalkForwardReport {
  const primaryRows = args.bundle.get(args.primaryInterval);
  if (!primaryRows) {
    throw new Error(
      `runWalkForwardWithBundle: primary interval "${args.primaryInterval}" missing from bundle`,
    );
  }

  // Use the primary candles as the splitting axis — fold count and
  // ranges are determined entirely by primary-TF bars, exactly as in
  // the single-TF path.
  const primaryCandles = primaryRows.map(toCandle);
  const folds = split(primaryCandles, args.foldCfg);

  const folded: FoldReport[] = folds.map((fold) => {
    const isBundle = sliceBundleByWindow(args.bundle, fold.isRange.fromTsMs, fold.isRange.toTsMs);
    const oosBundle = sliceBundleByWindow(args.bundle, fold.oosRange.fromTsMs, fold.oosRange.toTsMs);

    const isReport = runBacktestWithBundle({
      bundle: isBundle,
      primaryInterval: args.primaryInterval,
      dslJson: args.dslJson,
      opts: args.opts,
    });
    const oosReport = runBacktestWithBundle({
      bundle: oosBundle,
      primaryInterval: args.primaryInterval,
      dslJson: args.dslJson,
      opts: args.opts,
    });

    args.onProgress?.(fold.foldIndex + 1, folds.length);
    return {
      foldIndex: fold.foldIndex,
      isReport,
      oosReport,
      isRange: fold.isRange,
      oosRange: fold.oosRange,
    };
  });

  return { folds: folded, aggregate: aggregate(folded) };
}
