import { describe, it, expect } from "vitest";
import { detectMarketStructureShifts } from "../../src/lib/patterns/marketStructureShift.js";
import {
  makeBosBullishFixture,
  makeChochBearishFixture,
  flatMarketFixture,
} from "./smcFixtures.js";

describe("detectMarketStructureShifts", () => {
  it("returns empty for insufficient data", () => {
    expect(detectMarketStructureShifts([])).toEqual([]);
    expect(detectMarketStructureShifts(flatMarketFixture)).toEqual([]);
  });

  it("detects a bullish BOS in an uptrend", () => {
    const candles = makeBosBullishFixture();
    const shifts = detectMarketStructureShifts(candles, { swingLen: 2 });

    // Should find at least one bullish BOS
    const bullishBos = shifts.filter(
      (s) => s.direction === "bullish" && s.type === "BOS",
    );
    expect(bullishBos.length).toBeGreaterThanOrEqual(1);

    // The final break should be at bar 14 (close=113 > 112)
    const lastBos = bullishBos[bullishBos.length - 1];
    expect(lastBos.index).toBe(14);
    expect(lastBos.brokenLevel).toBe(112);
    expect(lastBos.timestamp).toBe(candles[14].openTime);
  });

  it("detects a bearish CHoCH after an uptrend", () => {
    const candles = makeChochBearishFixture();
    const shifts = detectMarketStructureShifts(candles, { swingLen: 2 });

    // Should find at least one bearish CHoCH
    const bearishChoch = shifts.filter(
      (s) => s.direction === "bearish" && s.type === "CHoCH",
    );
    expect(bearishChoch.length).toBeGreaterThanOrEqual(1);

    // The break should be at bar 14 (close=97 < 98 swing low)
    const lastChoch = bearishChoch[bearishChoch.length - 1];
    expect(lastChoch.index).toBe(14);
    expect(lastChoch.brokenLevel).toBe(98);
  });

  it("is deterministic", () => {
    const candles = makeBosBullishFixture();
    const a = detectMarketStructureShifts(candles, { swingLen: 2 });
    const b = detectMarketStructureShifts(candles, { swingLen: 2 });
    expect(a).toEqual(b);
  });

  it("brokenLevel matches a real swing point", () => {
    const candles = makeBosBullishFixture();
    const shifts = detectMarketStructureShifts(candles, { swingLen: 2 });
    for (const shift of shifts) {
      expect(shift.brokenLevel).toBeGreaterThan(0);
      expect(shift.index).toBeGreaterThan(0);
      expect(shift.index).toBeLessThan(candles.length);
    }
  });
});
