/**
 * MTF Indicator Resolver (#134 — Slice 2)
 *
 * Resolves indicator values across multiple timeframes using a CandleBundle.
 *
 * When a DSL indicator ref has `sourceTimeframe` set, this module:
 *   1. Looks up the context-TF candle array from the bundle
 *   2. Computes the indicator on that TF's candles (using the standard cache)
 *   3. Maps the result back to primary-TF bar indices via the alignment map
 *
 * The result is an array indexed by primary-TF bar — each element is the
 * context-TF indicator value that was "current" at that primary bar.
 *
 * Design:
 *   - Pure functions, no I/O
 *   - Reuses existing getIndicatorValues() from dslEvaluator
 *   - One IndicatorCache per timeframe (no cross-TF cache pollution)
 *   - Falls back to primary TF when sourceTimeframe is absent or bundle unavailable
 */

import type { Candle } from "../bybitCandles.js";
import type { DslIndicatorRef } from "../dslEvaluator.js";
import { getIndicatorValues, createIndicatorCache, type IndicatorCache } from "../dslEvaluator.js";
import type { CandleBundle } from "./intervalAlignment.js";

// ---------------------------------------------------------------------------
// Multi-TF indicator cache
// ---------------------------------------------------------------------------

/** Per-timeframe indicator cache. Each TF gets its own cache to avoid cross-pollution. */
export interface MtfIndicatorCache {
  /** Cache for the primary timeframe */
  primary: IndicatorCache;
  /** Caches for context timeframes, keyed by interval string */
  context: Map<string, IndicatorCache>;
}

export function createMtfCache(): MtfIndicatorCache {
  return {
    primary: createIndicatorCache(),
    context: new Map(),
  };
}

function getOrCreateContextCache(mtfCache: MtfIndicatorCache, interval: string): IndicatorCache {
  let cache = mtfCache.context.get(interval);
  if (!cache) {
    cache = createIndicatorCache();
    mtfCache.context.set(interval, cache);
  }
  return cache;
}

// ---------------------------------------------------------------------------
// MTF indicator resolution
// ---------------------------------------------------------------------------

/**
 * Resolve an indicator value array, potentially from a context timeframe.
 *
 * If `ref.sourceTimeframe` is set and `bundle` is provided:
 *   1. Get context-TF candles from bundle
 *   2. Compute indicator on those candles (with TF-specific cache)
 *   3. Map results back to primary bar indices via alignment map
 *
 * If `ref.sourceTimeframe` is absent or bundle is null:
 *   Falls back to computing on the primary candle array (standard path).
 *
 * @param ref           Indicator reference (may have sourceTimeframe)
 * @param primaryCandles  Primary TF candle array
 * @param mtfCache      Multi-TF indicator cache
 * @param bundle        Optional CandleBundle for MTF resolution
 * @returns Array of indicator values indexed by primary bar
 */
export function resolveMtfIndicator(
  ref: DslIndicatorRef,
  primaryCandles: Candle[],
  mtfCache: MtfIndicatorCache,
  bundle: CandleBundle | null,
): (number | null)[] {
  const params = {
    length: ref.length,
    period: ref.period,
    atrPeriod: ref.atrPeriod,
    multiplier: ref.multiplier,
  };

  // No MTF: use primary candles directly
  if (!ref.sourceTimeframe || !bundle) {
    return getIndicatorValues(ref.type, params, primaryCandles, mtfCache.primary);
  }

  const tf = ref.sourceTimeframe;
  const contextCandles = bundle.candles[tf];
  const alignmentMap = bundle.alignmentMaps[tf];

  // If context TF data is unavailable, fall back to primary
  if (!contextCandles || !alignmentMap) {
    return getIndicatorValues(ref.type, params, primaryCandles, mtfCache.primary);
  }

  // Compute indicator on context-TF candles
  const contextCache = getOrCreateContextCache(mtfCache, tf);
  const contextValues = getIndicatorValues(
    ref.type,
    params,
    contextCandles as unknown as Candle[],
    contextCache,
  );

  // Map context-TF results back to primary-TF bar indices
  const result: (number | null)[] = new Array(primaryCandles.length).fill(null);
  for (let i = 0; i < primaryCandles.length; i++) {
    const ctxIdx = alignmentMap[i];
    if (ctxIdx >= 0 && ctxIdx < contextValues.length) {
      result[i] = contextValues[ctxIdx];
    }
  }

  return result;
}

/**
 * Convenience: resolve indicator for a specific bar index.
 *
 * Used in signal evaluation where only the current bar's value is needed.
 */
export function resolveMtfIndicatorAt(
  ref: DslIndicatorRef,
  barIndex: number,
  primaryCandles: Candle[],
  mtfCache: MtfIndicatorCache,
  bundle: CandleBundle | null,
): number | null {
  const values = resolveMtfIndicator(ref, primaryCandles, mtfCache, bundle);
  return values[barIndex] ?? null;
}
