import { describe, it, expect } from "vitest";
import {
  detectLiquiditySweeps,
  findSwingPoints,
} from "../../src/lib/patterns/liquiditySweep.js";
import {
  bullishSweepFixture,
  bearishSweepFixture,
  noSweepFixture,
  flatMarketFixture,
} from "./smcFixtures.js";

describe("findSwingPoints", () => {
  it("returns empty for insufficient data", () => {
    expect(findSwingPoints([], 2)).toEqual([]);
    expect(findSwingPoints(bullishSweepFixture.slice(0, 3), 2)).toEqual([]);
  });

  it("finds a swing low in the bullish sweep fixture", () => {
    const swings = findSwingPoints(bullishSweepFixture, 2);
    const lows = swings.filter((s) => s.type === "low");
    expect(lows.length).toBeGreaterThanOrEqual(1);
    expect(lows.some((s) => s.index === 2 && s.level === 95)).toBe(true);
  });

  it("finds a swing high in the bearish sweep fixture", () => {
    const swings = findSwingPoints(bearishSweepFixture, 2);
    const highs = swings.filter((s) => s.type === "high");
    expect(highs.length).toBeGreaterThanOrEqual(1);
    expect(highs.some((s) => s.index === 2 && s.level === 110)).toBe(true);
  });

  it("no swing points in flat market", () => {
    const swings = findSwingPoints(flatMarketFixture, 2);
    expect(swings).toEqual([]);
  });
});

describe("detectLiquiditySweeps", () => {
  it("returns empty for insufficient data", () => {
    expect(detectLiquiditySweeps([])).toEqual([]);
    expect(detectLiquiditySweeps(bullishSweepFixture.slice(0, 3))).toEqual([]);
  });

  it("detects a bullish liquidity sweep", () => {
    const sweeps = detectLiquiditySweeps(bullishSweepFixture, { swingLen: 2 });
    const bullish = sweeps.filter((s) => s.direction === "bullish");
    expect(bullish.length).toBeGreaterThanOrEqual(1);

    const sweep = bullish[0];
    expect(sweep.index).toBe(5);
    expect(sweep.direction).toBe("bullish");
    expect(sweep.level).toBe(95);
    expect(sweep.penetration).toBe(2); // 95 - 93
    expect(sweep.timestamp).toBe(bullishSweepFixture[5].openTime);
  });

  it("detects a bearish liquidity sweep", () => {
    const sweeps = detectLiquiditySweeps(bearishSweepFixture, { swingLen: 2 });
    const bearish = sweeps.filter((s) => s.direction === "bearish");
    expect(bearish.length).toBeGreaterThanOrEqual(1);

    const sweep = bearish[0];
    expect(sweep.index).toBe(5);
    expect(sweep.direction).toBe("bearish");
    expect(sweep.level).toBe(110);
    expect(sweep.penetration).toBe(2); // 112 - 110
    expect(sweep.timestamp).toBe(bearishSweepFixture[5].openTime);
  });

  it("does not detect a sweep when price breaks but does not reverse", () => {
    const sweeps = detectLiquiditySweeps(noSweepFixture, { swingLen: 2 });
    // close=94 < 95, so it's not a bullish sweep (no reversal)
    const bullish = sweeps.filter((s) => s.direction === "bullish");
    expect(bullish).toEqual([]);
  });

  it("respects maxAge parameter", () => {
    // With maxAge=2, bar 5 is 3 bars after swing at bar 2 → too old
    const sweeps = detectLiquiditySweeps(bullishSweepFixture, { swingLen: 2, maxAge: 2 });
    expect(sweeps.filter((s) => s.direction === "bullish")).toEqual([]);

    // With maxAge=3, bar 5 is exactly 3 bars after → should detect
    const sweeps2 = detectLiquiditySweeps(bullishSweepFixture, { swingLen: 2, maxAge: 3 });
    expect(sweeps2.filter((s) => s.direction === "bullish").length).toBeGreaterThanOrEqual(1);
  });

  it("is deterministic", () => {
    const a = detectLiquiditySweeps(bullishSweepFixture, { swingLen: 2 });
    const b = detectLiquiditySweeps(bullishSweepFixture, { swingLen: 2 });
    expect(a).toEqual(b);
  });

  it("penetration is always positive", () => {
    const sweeps = [
      ...detectLiquiditySweeps(bullishSweepFixture, { swingLen: 2 }),
      ...detectLiquiditySweeps(bearishSweepFixture, { swingLen: 2 }),
    ];
    for (const sweep of sweeps) {
      expect(sweep.penetration).toBeGreaterThan(0);
    }
  });
});
