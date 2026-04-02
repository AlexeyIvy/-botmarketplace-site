import { describe, it, expect } from "vitest";
import {
  computeBasisBps,
  buildSpreadSnapshot,
  annualizedBasisYieldPct,
} from "../../src/lib/funding/basis.js";

describe("computeBasisBps", () => {
  it("returns positive bps for contango (perp premium)", () => {
    // perp = 100.50, spot = 100.00 → (0.50 / 100) * 10000 = 50 bps
    expect(computeBasisBps(100, 100.5)).toBe(50);
  });

  it("returns negative bps for backwardation (perp discount)", () => {
    // perp = 99.50, spot = 100.00 → (-0.50 / 100) * 10000 = -50 bps
    expect(computeBasisBps(100, 99.5)).toBe(-50);
  });

  it("returns 0 for equal prices", () => {
    expect(computeBasisBps(100, 100)).toBe(0);
  });

  it("returns 0 for zero spot price", () => {
    expect(computeBasisBps(0, 100)).toBe(0);
  });

  it("returns 0 for negative spot price", () => {
    expect(computeBasisBps(-1, 100)).toBe(0);
  });

  it("returns 0 for non-finite inputs", () => {
    expect(computeBasisBps(NaN, 100)).toBe(0);
    expect(computeBasisBps(100, NaN)).toBe(0);
    expect(computeBasisBps(Infinity, 100)).toBe(0);
    expect(computeBasisBps(100, Infinity)).toBe(0);
  });

  it("handles realistic BTC prices", () => {
    // BTC spot = 67432.50, perp = 67445.00
    // basis = (12.50 / 67432.50) * 10000 ≈ 1.854 bps
    const basis = computeBasisBps(67432.5, 67445);
    expect(basis).toBeCloseTo(1.854, 2);
  });

  it("is deterministic", () => {
    expect(computeBasisBps(100, 101)).toBe(computeBasisBps(100, 101));
  });
});

describe("buildSpreadSnapshot", () => {
  it("builds a snapshot with computed basisBps", () => {
    const snap = buildSpreadSnapshot("BTCUSDT", 100, 100.5, 1700000000000);
    expect(snap.symbol).toBe("BTCUSDT");
    expect(snap.spotPrice).toBe(100);
    expect(snap.perpPrice).toBe(100.5);
    expect(snap.basisBps).toBe(50);
    expect(snap.timestamp).toBe(1700000000000);
  });
});

describe("annualizedBasisYieldPct", () => {
  it("annualizes a daily basis", () => {
    // 50 bps daily → 50/10000 * 365/1 * 100 = 182.5%
    expect(annualizedBasisYieldPct(50, 1)).toBeCloseTo(182.5, 1);
  });

  it("returns 0 for zero holdingDays", () => {
    expect(annualizedBasisYieldPct(50, 0)).toBe(0);
  });

  it("returns 0 for negative holdingDays", () => {
    expect(annualizedBasisYieldPct(50, -1)).toBe(0);
  });

  it("scales with holding period", () => {
    const daily = annualizedBasisYieldPct(10, 1);
    const weekly = annualizedBasisYieldPct(10, 7);
    expect(daily).toBeCloseTo(weekly * 7, 1);
  });
});
