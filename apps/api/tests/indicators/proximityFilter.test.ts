import { describe, it, expect } from "vitest";
import { calcProximityFilter, calcDirectionalProximity } from "../../src/lib/indicators/proximityFilter.js";

describe("calcProximityFilter", () => {
  it("returns true when price is within percentage threshold of level", () => {
    const prices = [100, 101, 105, 110];
    const levels = [100, 100, 100, 100];
    // 2% threshold → within 2 of 100
    const result = calcProximityFilter(prices, levels, 2, "percentage");
    expect(result[0]).toBe(true);  // 0% away
    expect(result[1]).toBe(true);  // 1% away
    expect(result[2]).toBe(false); // 5% away
    expect(result[3]).toBe(false); // 10% away
  });

  it("returns true when price is within absolute threshold", () => {
    const prices = [100, 101, 105];
    const levels = [100, 100, 100];
    const result = calcProximityFilter(prices, levels, 2, "absolute");
    expect(result[0]).toBe(true);  // 0 away
    expect(result[1]).toBe(true);  // 1 away
    expect(result[2]).toBe(false); // 5 away
  });

  it("handles null values in prices or levels", () => {
    const prices = [100, null, 100];
    const levels = [100, 100, null];
    const result = calcProximityFilter(prices, levels, 2, "percentage");
    expect(result[0]).toBe(true);
    expect(result[1]).toBeNull();
    expect(result[2]).toBeNull();
  });

  it("handles zero level (avoid division by zero)", () => {
    const prices = [0];
    const levels = [0];
    const result = calcProximityFilter(prices, levels, 1, "percentage");
    expect(result[0]).toBeNull();
  });

  it("works with mismatched array lengths", () => {
    const prices = [100, 101, 102, 103];
    const levels = [100, 100];
    const result = calcProximityFilter(prices, levels, 2, "percentage");
    expect(result).toHaveLength(2); // min of both
  });

  it("is deterministic", () => {
    const prices = [100, 101, 105];
    const levels = [100, 100, 100];
    const a = calcProximityFilter(prices, levels, 2, "percentage");
    const b = calcProximityFilter(prices, levels, 2, "percentage");
    expect(a).toEqual(b);
  });
});

describe("calcDirectionalProximity", () => {
  it("filters for price above level", () => {
    const prices = [101, 99, 100.5, 105];
    const levels = [100, 100, 100, 100];
    // 2% threshold, above
    const result = calcDirectionalProximity(prices, levels, 2, "above", "percentage");
    expect(result[0]).toBe(true);  // 101 >= 100 and within 2%
    expect(result[1]).toBe(false); // 99 < 100 (below, not above)
    expect(result[2]).toBe(true);  // 100.5 >= 100 and within 2%
    expect(result[3]).toBe(false); // 105 > 100 but 5% away (not near)
  });

  it("filters for price below level", () => {
    const prices = [99, 101, 99.5];
    const levels = [100, 100, 100];
    const result = calcDirectionalProximity(prices, levels, 2, "below", "percentage");
    expect(result[0]).toBe(true);  // 99 <= 100 and within 2%
    expect(result[1]).toBe(false); // 101 > 100 (above, not below)
    expect(result[2]).toBe(true);  // 99.5 <= 100 and within 2%
  });

  it("returns null for null inputs", () => {
    const result = calcDirectionalProximity([null], [100], 2, "above");
    expect(result[0]).toBeNull();
  });
});
