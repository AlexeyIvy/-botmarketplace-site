import { describe, it, expect } from "vitest";
import { profitFactor } from "../../../src/lib/backtestMetrics/profitFactor.js";

describe("profitFactor", () => {
  it("returns null on an empty array", () => {
    expect(profitFactor([])).toBeNull();
  });

  it("returns null when all entries are exactly zero", () => {
    // Both gross and loss are 0 → no information to report.
    expect(profitFactor([0, 0, 0])).toBeNull();
  });

  it("returns +Infinity for a series of wins with no losses", () => {
    expect(profitFactor([1.5, 2.0, 0.5])).toBe(Number.POSITIVE_INFINITY);
  });

  it("returns 0 for a series of losses with no wins", () => {
    expect(profitFactor([-1, -2, -0.5])).toBe(0);
  });

  it("matches a hand-calculated reference (mixed wins/losses)", () => {
    // gross = 2 + 3 + 1 = 6; loss = 1 + 2 = 3; pf = 6 / 3 = 2.00
    expect(profitFactor([2, -1, 3, -2, 1])).toBe(2);
  });

  it("rounds to 2 decimals (gross 5, loss 3 → 1.67)", () => {
    expect(profitFactor([5, -3])).toBe(1.67);
  });

  it("ignores zero entries (treated as neither win nor loss)", () => {
    expect(profitFactor([2, 0, -1, 0])).toBe(2);
  });
});
