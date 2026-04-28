/**
 * Walk-forward runner — per-fold backtest without aggregation.
 *
 * Given a candle array, a compiled DSL, execution opts, and a FoldConfig,
 * `runWalkForward` produces one (IS, OOS) backtest pair per fold by calling
 * `runBacktest` twice on the slices returned by `split`. The function
 * does not touch the database, has no HTTP layer, and only side-effects
 * via the optional `onProgress` callback (used by the BD wrapper in 48-T5
 * to surface progress to the client).
 *
 * Multi-timeframe gate: walk-forward for MTF strategies is not yet
 * implemented (slicing the MTF context bundle in sync with the primary
 * candles is non-trivial and out of scope for this version). The runner
 * pre-flights the DSL and throws a `WalkForwardMtfNotSupportedError` when
 * any indicator carries a `sourceTimeframe`. The HTTP layer (48-T5) maps
 * that error to a 400.
 *
 * Determinism: mirrors the contracts of `split` (48-T1) and `runBacktest`
 * (docs/44 §Детерминизм). Identical inputs always produce identical output.
 */

import type { Candle } from "../bybitCandles.js";
import type { DslExecOpts } from "../dslEvaluator.js";
import { runBacktest } from "../backtest.js";
import { split } from "./split.js";
import { aggregate } from "./aggregate.js";
import type {
  FoldConfig,
  FoldReport,
  WalkForwardReport,
} from "./types.js";

/**
 * Thrown when a DSL contains at least one indicator with a non-empty
 * `sourceTimeframe`. The HTTP layer (48-T5) translates this into a 400
 * with the prescribed user-facing message.
 */
export class WalkForwardMtfNotSupportedError extends Error {
  constructor(public readonly indicatorType: string, public readonly sourceTimeframe: string) {
    super(
      `Walk-forward для MTF-стратегий не реализован: индикатор '${indicatorType}' использует sourceTimeframe='${sourceTimeframe}'. См. follow-up к docs/48.`,
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
  // MTF pre-flight: walk-forward does not slice MTF contexts yet, so a
  // strategy that references another timeframe would silently fall back
  // to the primary TF and produce different signals. Reject up front.
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
