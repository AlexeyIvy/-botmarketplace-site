import { describe, it, expect } from "vitest";
import {
  detectFairValueGaps,
  findFvgFillIndex,
} from "../../src/lib/patterns/fairValueGap.js";
import {
  bullishFvgFixture,
  bearishFvgFixture,
  noFvgFixture,
  multiFvgFixture,
  unfilledFvgFixture,
  flatMarketFixture,
} from "./smcFixtures.js";

describe("detectFairValueGaps", () => {
  // ── Edge cases ────────────────────────────────────────

  it("returns empty array for fewer than 3 candles", () => {
    expect(detectFairValueGaps([])).toEqual([]);
    expect(detectFairValueGaps(bullishFvgFixture.slice(0, 1))).toEqual([]);
    expect(detectFairValueGaps(bullishFvgFixture.slice(0, 2))).toEqual([]);
  });

  it("returns no FVGs in a flat market", () => {
    expect(detectFairValueGaps(flatMarketFixture)).toEqual([]);
  });

  it("returns no FVGs when wicks overlap", () => {
    expect(detectFairValueGaps(noFvgFixture)).toEqual([]);
  });

  // ── Bullish FVG ───────────────────────────────────────

  it("detects a bullish FVG", () => {
    const fvgs = detectFairValueGaps(bullishFvgFixture);
    const bullish = fvgs.filter((f) => f.direction === "bullish");
    expect(bullish).toHaveLength(1);

    const fvg = bullish[0];
    expect(fvg.index).toBe(1); // middle candle
    expect(fvg.direction).toBe("bullish");
    expect(fvg.low).toBe(102);  // candle 0 high
    expect(fvg.high).toBe(104); // candle 2 low
    expect(fvg.timestamp).toBe(bullishFvgFixture[1].openTime);
  });

  // ── Bearish FVG ───────────────────────────────────────

  it("detects a bearish FVG", () => {
    const fvgs = detectFairValueGaps(bearishFvgFixture);
    const bearish = fvgs.filter((f) => f.direction === "bearish");
    expect(bearish).toHaveLength(1);

    const fvg = bearish[0];
    expect(fvg.index).toBe(1);
    expect(fvg.direction).toBe("bearish");
    expect(fvg.low).toBe(96);  // candle 2 high
    expect(fvg.high).toBe(98); // candle 0 low
    expect(fvg.timestamp).toBe(bearishFvgFixture[1].openTime);
  });

  // ── Multiple FVGs ─────────────────────────────────────

  it("detects multiple FVGs in a strong trend", () => {
    const fvgs = detectFairValueGaps(multiFvgFixture);
    expect(fvgs.length).toBeGreaterThanOrEqual(2);

    // Both should be bullish
    for (const fvg of fvgs) {
      expect(fvg.direction).toBe("bullish");
    }

    // First gap: [102, 104], second gap: [113, 115]
    expect(fvgs[0].low).toBe(102);
    expect(fvgs[0].high).toBe(104);
    expect(fvgs[1].low).toBe(115);
    expect(fvgs[1].high).toBe(117);
  });

  // ── minGapRatio filter ────────────────────────────────

  it("filters out small gaps with minGapRatio", () => {
    // The bullish FVG in our fixture has gap=2, body=|107-101|=6, ratio=0.33
    const all = detectFairValueGaps(bullishFvgFixture);
    expect(all.length).toBeGreaterThan(0);

    // Require ratio ≥ 0.5 → should filter it out
    const filtered = detectFairValueGaps(bullishFvgFixture, { minGapRatio: 0.5 });
    expect(filtered).toEqual([]);

    // Require ratio ≥ 0.2 → should keep it (0.33 ≥ 0.2)
    const kept = detectFairValueGaps(bullishFvgFixture, { minGapRatio: 0.2 });
    expect(kept.length).toBeGreaterThan(0);
  });

  // ── Determinism ───────────────────────────────────────

  it("is deterministic", () => {
    const a = detectFairValueGaps(multiFvgFixture);
    const b = detectFairValueGaps(multiFvgFixture);
    expect(a).toEqual(b);
  });

  // ── Invariants ────────────────────────────────────────

  it("every FVG has high > low", () => {
    const fvgs = detectFairValueGaps(multiFvgFixture);
    for (const fvg of fvgs) {
      expect(fvg.high).toBeGreaterThan(fvg.low);
    }
  });

  it("FVG index is always within valid range", () => {
    const fvgs = detectFairValueGaps(multiFvgFixture);
    for (const fvg of fvgs) {
      expect(fvg.index).toBeGreaterThanOrEqual(1);
      expect(fvg.index).toBeLessThan(multiFvgFixture.length - 1);
    }
  });
});

describe("findFvgFillIndex", () => {
  it("finds the fill candle for a bullish FVG", () => {
    const fvgs = detectFairValueGaps(bullishFvgFixture);
    const bullish = fvgs.find((f) => f.direction === "bullish")!;
    const fillIdx = findFvgFillIndex(bullish, bullishFvgFixture);
    expect(fillIdx).toBe(3); // candle 3 fills with low=101 ≤ 102
  });

  it("finds the fill candle for a bearish FVG", () => {
    const fvgs = detectFairValueGaps(bearishFvgFixture);
    const bearish = fvgs.find((f) => f.direction === "bearish")!;
    const fillIdx = findFvgFillIndex(bearish, bearishFvgFixture);
    expect(fillIdx).toBe(3); // candle 3 fills with high=99 ≥ 98
  });

  it("returns -1 for an unfilled FVG", () => {
    const fvgs = detectFairValueGaps(unfilledFvgFixture);
    expect(fvgs.length).toBeGreaterThan(0);
    const fillIdx = findFvgFillIndex(fvgs[0], unfilledFvgFixture);
    expect(fillIdx).toBe(-1);
  });
});
