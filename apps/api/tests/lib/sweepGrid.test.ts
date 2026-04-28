import { describe, it, expect } from "vitest";
import { enumerateGrid } from "../../src/lib/sweepGrid.js";

describe("sweepGrid.enumerateGrid", () => {
  it("returns an empty array when no params are given", () => {
    expect(enumerateGrid([])).toEqual([]);
  });

  it("expands a single-param sweep to one combination per value (lex order)", () => {
    const combos = enumerateGrid([
      { blockId: "b1", paramName: "p1", from: 1, to: 3, step: 1 },
    ]);

    expect(combos).toHaveLength(3);
    expect(combos[0]).toEqual([{ blockId: "b1", paramName: "p1", value: 1 }]);
    expect(combos[1]).toEqual([{ blockId: "b1", paramName: "p1", value: 2 }]);
    expect(combos[2]).toEqual([{ blockId: "b1", paramName: "p1", value: 3 }]);
  });

  it("hand-calc reference: 2-param 2×3 grid in lexicographic order", () => {
    // The LAST param iterates fastest (per docs/47-T3).
    //   [(1,10), (1,15), (1,20), (2,10), (2,15), (2,20)]
    const combos = enumerateGrid([
      { blockId: "b1", paramName: "p1", from: 1, to: 2, step: 1 },
      { blockId: "b2", paramName: "p2", from: 10, to: 20, step: 5 },
    ]);

    expect(combos).toHaveLength(6);
    expect(combos.map((c) => c.map((x) => x.value))).toEqual([
      [1, 10], [1, 15], [1, 20],
      [2, 10], [2, 15], [2, 20],
    ]);
    // Each combination preserves blockId / paramName order.
    for (const combo of combos) {
      expect(combo[0].blockId).toBe("b1");
      expect(combo[0].paramName).toBe("p1");
      expect(combo[1].blockId).toBe("b2");
      expect(combo[1].paramName).toBe("p2");
    }
  });

  it("3-param grid produces Π(runs) combinations in lex order", () => {
    const combos = enumerateGrid([
      { blockId: "a", paramName: "x", from: 1, to: 2, step: 1 },
      { blockId: "b", paramName: "y", from: 10, to: 20, step: 10 },
      { blockId: "c", paramName: "z", from: 100, to: 100, step: 50 },
    ]);
    // 2 × 2 × 1 = 4 combinations.
    expect(combos).toHaveLength(4);
    expect(combos.map((c) => c.map((x) => x.value))).toEqual([
      [1, 10, 100], [1, 20, 100],
      [2, 10, 100], [2, 20, 100],
    ]);
  });

  it("rounds values to 8 decimal places to avoid float drift", () => {
    // 0.1 + 0.1 + 0.1 in JS is 0.30000000000000004, etc.
    const combos = enumerateGrid([
      { blockId: "b1", paramName: "p1", from: 0.1, to: 0.3, step: 0.1 },
    ]);
    expect(combos.map((c) => c[0].value)).toEqual([0.1, 0.2, 0.3]);
  });

  it("inclusive upper bound: from=1, to=2.0, step=0.1 includes 2.0", () => {
    const combos = enumerateGrid([
      { blockId: "b1", paramName: "p1", from: 1, to: 2, step: 0.1 },
    ]);
    expect(combos[combos.length - 1][0].value).toBe(2);
  });

  it("is deterministic — repeated calls produce identical output", () => {
    const params = [
      { blockId: "b1", paramName: "p1", from: 1, to: 3, step: 1 },
      { blockId: "b2", paramName: "p2", from: 10, to: 30, step: 10 },
    ];
    expect(enumerateGrid(params)).toEqual(enumerateGrid(params));
  });

  it("returns fresh objects per combination (no shared references)", () => {
    const combos = enumerateGrid([
      { blockId: "b1", paramName: "p1", from: 1, to: 2, step: 1 },
      { blockId: "b2", paramName: "p2", from: 10, to: 20, step: 10 },
    ]);
    // Mutating one combination must not leak into another.
    combos[0][0].value = 999;
    expect(combos[1][0].value).toBe(1);
  });
});
