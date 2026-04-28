/**
 * Pure walk-forward fold generator.
 *
 * For a candle array of length N and a `FoldConfig`, produces consecutive
 * (IS, OOS) pairs until the next OOS block would run past the end of the
 * data. Two layouts are supported:
 *
 *   anchored = false  (rolling)
 *     fold i:  IS  = [i*step, i*step + isBars)
 *              OOS = [i*step + isBars, i*step + isBars + oosBars)
 *     The IS window has fixed length isBars; the whole pair slides forward
 *     by `step` each iteration.
 *
 *   anchored = true   (anchored)
 *     fold i:  IS  = [0, isBars + i*step)
 *              OOS = [isBars + i*step, isBars + i*step + oosBars)
 *     The IS window always starts at 0 and grows; only the OOS slides.
 *
 * The function is pure: it neither mutates the input nor performs I/O.
 *
 * Validation:
 *   - isBars, oosBars, step must all be positive integers.
 *   - candles.length >= isBars + oosBars (otherwise no fold fits).
 *   - step < oosBars is allowed — the resulting OOS blocks overlap, which
 *     is methodologically suboptimal (a single trade can land in two
 *     adjacent folds and skew the aggregate). The HTTP layer (48-T5)
 *     flags this in a `warnings` array; the split function itself stays
 *     pure and has no warning channel.
 *
 * Determinism: identical inputs always yield identical outputs.
 */

import type { Candle } from "../bybitCandles.js";
import type { FoldConfig, Fold, FoldRange } from "./types.js";

function rangeOf(candles: Candle[], from: number, to: number): FoldRange {
  return {
    fromIndex: from,
    toIndex: to,
    fromTsMs: candles[from].openTime,
    toTsMs: candles[to - 1].openTime,
  };
}

export function split(candles: Candle[], cfg: FoldConfig): Fold[] {
  if (!Number.isFinite(cfg.isBars) || cfg.isBars <= 0) {
    throw new Error("isBars must be a positive number");
  }
  if (!Number.isFinite(cfg.oosBars) || cfg.oosBars <= 0) {
    throw new Error("oosBars must be a positive number");
  }
  if (!Number.isFinite(cfg.step) || cfg.step <= 0) {
    throw new Error("step must be a positive number");
  }
  if (candles.length < cfg.isBars + cfg.oosBars) {
    throw new Error(
      `candles.length (${candles.length}) < isBars + oosBars (${cfg.isBars + cfg.oosBars})`,
    );
  }

  const folds: Fold[] = [];
  for (let i = 0; ; i++) {
    const isStart = cfg.anchored ? 0 : i * cfg.step;
    const oosStart = cfg.isBars + i * cfg.step;
    const oosEnd = oosStart + cfg.oosBars;

    if (oosEnd > candles.length) break;

    const isSlice = candles.slice(isStart, oosStart);
    const oosSlice = candles.slice(oosStart, oosEnd);

    folds.push({
      foldIndex: i,
      isSlice,
      oosSlice,
      isRange: rangeOf(candles, isStart, oosStart),
      oosRange: rangeOf(candles, oosStart, oosEnd),
    });
  }
  return folds;
}
