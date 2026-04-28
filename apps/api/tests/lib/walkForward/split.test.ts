import { describe, it, expect } from "vitest";
import { split } from "../../../src/lib/walkForward/split.js";
import type { FoldConfig } from "../../../src/lib/walkForward/types.js";

interface Candle {
  openTime: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

function makeCandles(n: number): Candle[] {
  return Array.from({ length: n }, (_, i) => ({
    openTime: 1_700_000_000_000 + i * 60_000,
    open: 100,
    high: 100,
    low: 100,
    close: 100,
    volume: 1000,
  }));
}

describe("walkForward.split", () => {
  it("rolling: 100 candles, isBars=50/oosBars=10/step=10 → 5 folds, sliding IS", () => {
    const cfg: FoldConfig = { isBars: 50, oosBars: 10, step: 10, anchored: false };
    const folds = split(makeCandles(100), cfg);

    expect(folds).toHaveLength(5);
    expect(folds.map((f) => f.foldIndex)).toEqual([0, 1, 2, 3, 4]);

    // Fold 0
    expect(folds[0].isRange).toMatchObject({ fromIndex: 0, toIndex: 50 });
    expect(folds[0].oosRange).toMatchObject({ fromIndex: 50, toIndex: 60 });
    expect(folds[0].isSlice).toHaveLength(50);
    expect(folds[0].oosSlice).toHaveLength(10);

    // Fold 4 — last fits exactly: IS [40..90), OOS [90..100)
    expect(folds[4].isRange).toMatchObject({ fromIndex: 40, toIndex: 90 });
    expect(folds[4].oosRange).toMatchObject({ fromIndex: 90, toIndex: 100 });

    // Rolling: every IS has exactly isBars
    for (const f of folds) expect(f.isSlice).toHaveLength(50);
  });

  it("anchored: 100 candles, isBars=50/oosBars=10/step=10 → 5 folds, growing IS", () => {
    const cfg: FoldConfig = { isBars: 50, oosBars: 10, step: 10, anchored: true };
    const folds = split(makeCandles(100), cfg);

    expect(folds).toHaveLength(5);

    // Anchored: every IS starts at index 0 and grows by step.
    expect(folds.map((f) => f.isRange.fromIndex)).toEqual([0, 0, 0, 0, 0]);
    expect(folds.map((f) => f.isRange.toIndex)).toEqual([50, 60, 70, 80, 90]);
    expect(folds.map((f) => f.isSlice.length)).toEqual([50, 60, 70, 80, 90]);

    // OOS slides identically: [50..60), [60..70), …
    expect(folds.map((f) => f.oosRange.fromIndex)).toEqual([50, 60, 70, 80, 90]);
    expect(folds.map((f) => f.oosSlice.length)).toEqual([10, 10, 10, 10, 10]);
  });

  it("returns exactly 1 fold when candles.length === isBars + oosBars", () => {
    const cfg: FoldConfig = { isBars: 30, oosBars: 10, step: 10, anchored: false };
    const folds = split(makeCandles(40), cfg);

    expect(folds).toHaveLength(1);
    expect(folds[0].isRange).toMatchObject({ fromIndex: 0, toIndex: 30 });
    expect(folds[0].oosRange).toMatchObject({ fromIndex: 30, toIndex: 40 });
  });

  it("throws when isBars + oosBars > candles.length", () => {
    const cfg: FoldConfig = { isBars: 80, oosBars: 30, step: 10, anchored: false };
    expect(() => split(makeCandles(100), cfg)).toThrow(/candles\.length/);
  });

  it("throws on non-positive isBars / oosBars / step", () => {
    expect(() =>
      split(makeCandles(100), { isBars: 0, oosBars: 10, step: 10, anchored: false }),
    ).toThrow(/isBars/);
    expect(() =>
      split(makeCandles(100), { isBars: 10, oosBars: -1, step: 10, anchored: false }),
    ).toThrow(/oosBars/);
    expect(() =>
      split(makeCandles(100), { isBars: 10, oosBars: 10, step: 0, anchored: false }),
    ).toThrow(/step/);
  });

  it("populates isRange.fromTsMs / toTsMs from Candle.openTime", () => {
    const candles = makeCandles(20);
    const folds = split(candles, { isBars: 10, oosBars: 5, step: 5, anchored: false });

    expect(folds[0].isRange.fromTsMs).toBe(candles[0].openTime);
    // toTsMs is inclusive — last index is toIndex - 1.
    expect(folds[0].isRange.toTsMs).toBe(candles[9].openTime);
    expect(folds[0].oosRange.fromTsMs).toBe(candles[10].openTime);
    expect(folds[0].oosRange.toTsMs).toBe(candles[14].openTime);
  });

  it("does not mutate the input candle array", () => {
    const candles = makeCandles(60);
    const before = JSON.parse(JSON.stringify(candles));
    split(candles, { isBars: 30, oosBars: 10, step: 10, anchored: false });
    expect(candles).toEqual(before);
  });

  it("is deterministic — repeated calls produce identical output", () => {
    const candles = makeCandles(100);
    const cfg: FoldConfig = { isBars: 50, oosBars: 10, step: 10, anchored: false };
    const a = split(candles, cfg);
    const b = split(candles, cfg);
    expect(a).toEqual(b);
  });

  it("permits step < oosBars (overlapping OOS) — pure split has no warning channel", () => {
    // step=5, oosBars=10 → adjacent OOS blocks overlap by 5 bars.
    const folds = split(
      makeCandles(60),
      { isBars: 30, oosBars: 10, step: 5, anchored: false },
    );
    expect(folds.length).toBeGreaterThan(1);
    // OOS of fold 0 ends at index 40; OOS of fold 1 starts at 35 → overlap.
    expect(folds[0].oosRange.toIndex).toBe(40);
    expect(folds[1].oosRange.fromIndex).toBe(35);
  });
});
