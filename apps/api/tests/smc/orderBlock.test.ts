import { describe, it, expect } from "vitest";
import { detectOrderBlocks } from "../../src/lib/patterns/orderBlock.js";
import {
  makeBullishObFixture,
  makeBearishObFixture,
  flatMarketFixture,
} from "./smcFixtures.js";

describe("detectOrderBlocks", () => {
  it("returns empty for insufficient data", () => {
    expect(detectOrderBlocks([])).toEqual([]);
    expect(detectOrderBlocks(flatMarketFixture)).toEqual([]); // only 5 candles, need atrPeriod+1=15
  });

  it("detects a bullish order block", () => {
    const candles = makeBullishObFixture();
    const obs = detectOrderBlocks(candles);
    const bullish = obs.filter((o) => o.direction === "bullish");
    expect(bullish.length).toBeGreaterThanOrEqual(1);

    const ob = bullish[bullish.length - 1]; // last bullish OB should be the one at bar 15
    expect(ob.index).toBe(15);
    expect(ob.direction).toBe("bullish");
    expect(ob.high).toBe(101);  // bar 15 high
    expect(ob.low).toBe(99);    // bar 15 low
    expect(ob.impulseStrength).toBeGreaterThan(0);
    expect(ob.timestamp).toBe(candles[15].openTime);
  });

  it("detects a bearish order block", () => {
    const candles = makeBearishObFixture();
    const obs = detectOrderBlocks(candles);
    const bearish = obs.filter((o) => o.direction === "bearish");
    expect(bearish.length).toBeGreaterThanOrEqual(1);

    const ob = bearish[bearish.length - 1];
    expect(ob.index).toBe(15);
    expect(ob.direction).toBe("bearish");
    expect(ob.high).toBe(101);
    expect(ob.low).toBe(99);
    expect(ob.impulseStrength).toBeGreaterThan(0);
  });

  it("OB zone always has high > low", () => {
    const obs = [
      ...detectOrderBlocks(makeBullishObFixture()),
      ...detectOrderBlocks(makeBearishObFixture()),
    ];
    for (const ob of obs) {
      expect(ob.high).toBeGreaterThan(ob.low);
    }
  });

  it("respects minImpulseMultiple", () => {
    const candles = makeBullishObFixture();

    // Very high threshold → no OBs
    const none = detectOrderBlocks(candles, { minImpulseMultiple: 10 });
    expect(none).toEqual([]);

    // Low threshold → should find OBs
    const some = detectOrderBlocks(candles, { minImpulseMultiple: 0.5 });
    expect(some.length).toBeGreaterThan(0);
  });

  it("is deterministic", () => {
    const candles = makeBullishObFixture();
    const a = detectOrderBlocks(candles);
    const b = detectOrderBlocks(candles);
    expect(a).toEqual(b);
  });

  it("deduplicates OBs when multiple impulse candles reference the same opposing candle", () => {
    // Build fixture: 14 bars of ATR baseline, then a bearish candle,
    // then TWO consecutive bullish impulse candles.
    const candles = makeBullishObFixture();
    // Add a second impulse candle right after the first one
    candles.push({
      openTime: 1_700_000_000_000 + 17 * 60_000,
      open: 102.5,
      high: 106,
      low: 102,
      close: 105.5,
      volume: 1000,
    });
    const obs = detectOrderBlocks(candles);
    // The OB at index 15 should appear only once despite two impulse candles
    const obsAtIndex15 = obs.filter((o) => o.index === 15);
    expect(obsAtIndex15.length).toBe(1);
  });
});
