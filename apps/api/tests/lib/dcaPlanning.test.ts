import { describe, it, expect } from "vitest";
import {
  generateSafetyOrderSchedule,
  calculateAvgEntry,
  recalcTakeProfit,
  calculateMaxExposure,
  openDcaPosition,
  applySafetyOrderFill,
} from "../../src/lib/dcaPlanning.js";
import type { DcaConfig, DcaFill } from "../../src/lib/dcaPlanning.js";

// ---------------------------------------------------------------------------
// Fixture: standard DCA config matching docs/strategies/06-dca-momentum-bot.md
// ---------------------------------------------------------------------------

function makeConfig(overrides: Partial<DcaConfig> = {}): DcaConfig {
  return {
    baseOrderSizeUsd: 100,
    maxSafetyOrders: 3,
    priceStepPct: 1.0,
    stepScale: 1.0,
    volumeScale: 1.5,
    takeProfitPct: 1.5,
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// generateSafetyOrderSchedule
// ---------------------------------------------------------------------------

describe("dcaPlanning – generateSafetyOrderSchedule", () => {
  it("generates correct number of safety orders", () => {
    const schedule = generateSafetyOrderSchedule(makeConfig(), 10000, "long");
    expect(schedule.safetyOrders).toHaveLength(3);
  });

  it("SO trigger prices decrease for long side", () => {
    const schedule = generateSafetyOrderSchedule(makeConfig(), 10000, "long");
    for (const so of schedule.safetyOrders) {
      expect(so.triggerPrice).toBeLessThan(10000);
    }
    // Each subsequent SO should be further from entry
    for (let i = 1; i < schedule.safetyOrders.length; i++) {
      expect(schedule.safetyOrders[i].triggerPrice).toBeLessThan(
        schedule.safetyOrders[i - 1].triggerPrice,
      );
    }
  });

  it("SO trigger prices increase for short side", () => {
    const schedule = generateSafetyOrderSchedule(makeConfig(), 10000, "short");
    for (const so of schedule.safetyOrders) {
      expect(so.triggerPrice).toBeGreaterThan(10000);
    }
    for (let i = 1; i < schedule.safetyOrders.length; i++) {
      expect(schedule.safetyOrders[i].triggerPrice).toBeGreaterThan(
        schedule.safetyOrders[i - 1].triggerPrice,
      );
    }
  });

  it("SO sizes scale geometrically with volumeScale", () => {
    const cfg = makeConfig({ volumeScale: 2.0 });
    const schedule = generateSafetyOrderSchedule(cfg, 10000, "long");
    // SO[0] = base * 2.0, SO[1] = SO[0] * 2.0, SO[2] = SO[1] * 2.0
    expect(schedule.safetyOrders[0].orderSizeUsd).toBeCloseTo(200, 2);
    expect(schedule.safetyOrders[1].orderSizeUsd).toBeCloseTo(400, 2);
    expect(schedule.safetyOrders[2].orderSizeUsd).toBeCloseTo(800, 2);
  });

  it("step scale compounds price deviations", () => {
    const cfg = makeConfig({ priceStepPct: 1.0, stepScale: 2.0 });
    const schedule = generateSafetyOrderSchedule(cfg, 10000, "long");
    // Deviations: 1%, 1%+2%=3%, 3%+4%=7%
    expect(schedule.safetyOrders[0].deviationPct).toBeCloseTo(1.0, 6);
    expect(schedule.safetyOrders[1].deviationPct).toBeCloseTo(3.0, 6);
    expect(schedule.safetyOrders[2].deviationPct).toBeCloseTo(7.0, 6);
  });

  it("totalCapitalUsd equals base + sum of all SO sizes", () => {
    const cfg = makeConfig();
    const schedule = generateSafetyOrderSchedule(cfg, 10000, "long");
    const soTotal = schedule.safetyOrders.reduce((s, so) => s + so.orderSizeUsd, 0);
    expect(schedule.totalCapitalUsd).toBeCloseTo(cfg.baseOrderSizeUsd + soTotal, 2);
  });

  it("worstCaseAvgEntry is between base entry and last SO trigger", () => {
    const schedule = generateSafetyOrderSchedule(makeConfig(), 10000, "long");
    const lastSO = schedule.safetyOrders[schedule.safetyOrders.length - 1];
    expect(schedule.worstCaseAvgEntry).toBeLessThan(10000);
    expect(schedule.worstCaseAvgEntry).toBeGreaterThan(lastSO.triggerPrice);
  });

  it("worstCaseTpPrice is above worstCaseAvgEntry for long", () => {
    const schedule = generateSafetyOrderSchedule(makeConfig(), 10000, "long");
    expect(schedule.worstCaseTpPrice).toBeGreaterThan(schedule.worstCaseAvgEntry);
  });

  it("worstCaseTpPrice is below worstCaseAvgEntry for short", () => {
    const schedule = generateSafetyOrderSchedule(makeConfig(), 10000, "short");
    expect(schedule.worstCaseTpPrice).toBeLessThan(schedule.worstCaseAvgEntry);
  });

  it("is deterministic — same inputs produce identical output", () => {
    const cfg = makeConfig();
    const a = generateSafetyOrderSchedule(cfg, 10000, "long");
    const b = generateSafetyOrderSchedule(cfg, 10000, "long");
    expect(a).toEqual(b);
  });
});

// ---------------------------------------------------------------------------
// calculateAvgEntry
// ---------------------------------------------------------------------------

describe("dcaPlanning – calculateAvgEntry", () => {
  it("returns 0 for empty fills", () => {
    expect(calculateAvgEntry([])).toBe(0);
  });

  it("returns the price for a single fill", () => {
    const fills: DcaFill[] = [{ price: 100, qty: 1, sizeUsd: 100 }];
    expect(calculateAvgEntry(fills)).toBe(100);
  });

  it("correctly computes VWAP for two fills", () => {
    const fills: DcaFill[] = [
      { price: 100, qty: 1, sizeUsd: 100 },
      { price: 90, qty: 2, sizeUsd: 180 },
    ];
    // VWAP = (100*1 + 90*2) / (1+2) = 280/3 ≈ 93.33
    expect(calculateAvgEntry(fills)).toBeCloseTo(93.3333, 2);
  });

  it("correctly computes VWAP for three fills (triple DCA)", () => {
    const fills: DcaFill[] = [
      { price: 10000, qty: 0.01, sizeUsd: 100 },
      { price: 9900, qty: 0.015, sizeUsd: 148.5 },
      { price: 9800, qty: 0.0225, sizeUsd: 220.5 },
    ];
    const expected = (10000 * 0.01 + 9900 * 0.015 + 9800 * 0.0225) / (0.01 + 0.015 + 0.0225);
    expect(calculateAvgEntry(fills)).toBeCloseTo(expected, 4);
  });
});

// ---------------------------------------------------------------------------
// recalcTakeProfit
// ---------------------------------------------------------------------------

describe("dcaPlanning – recalcTakeProfit", () => {
  it("long TP is above avg entry", () => {
    const tp = recalcTakeProfit(10000, 1.5, "long");
    expect(tp).toBeCloseTo(10150, 2);
  });

  it("short TP is below avg entry", () => {
    const tp = recalcTakeProfit(10000, 1.5, "short");
    expect(tp).toBeCloseTo(9850, 2);
  });

  it("TP moves down as avg entry moves down (long DCA)", () => {
    const tp1 = recalcTakeProfit(10000, 1.5, "long");
    const tp2 = recalcTakeProfit(9900, 1.5, "long");
    expect(tp2).toBeLessThan(tp1);
  });
});

// ---------------------------------------------------------------------------
// calculateMaxExposure
// ---------------------------------------------------------------------------

describe("dcaPlanning – calculateMaxExposure", () => {
  it("equals base for maxSafetyOrders = 0 edge case", () => {
    // 0 SOs means just the base order (even though schema requires min 1)
    const cfg = makeConfig({ maxSafetyOrders: 0 });
    expect(calculateMaxExposure(cfg)).toBe(100);
  });

  it("matches totalCapitalUsd from schedule generation", () => {
    const cfg = makeConfig();
    const exposure = calculateMaxExposure(cfg);
    const schedule = generateSafetyOrderSchedule(cfg, 10000, "long");
    expect(exposure).toBeCloseTo(schedule.totalCapitalUsd, 2);
  });

  it("scales correctly: 3 SOs with volumeScale 1.5", () => {
    const cfg = makeConfig({ baseOrderSizeUsd: 100, maxSafetyOrders: 3, volumeScale: 1.5 });
    // base=100, SO1=150, SO2=225, SO3=337.5 → total=812.5
    expect(calculateMaxExposure(cfg)).toBeCloseTo(812.5, 2);
  });

  it("large ladder: 12 SOs with volumeScale 1.2", () => {
    const cfg = makeConfig({ baseOrderSizeUsd: 100, maxSafetyOrders: 12, volumeScale: 1.2 });
    const exposure = calculateMaxExposure(cfg);
    // Verify it's bounded and reasonable
    expect(exposure).toBeGreaterThan(100);
    expect(exposure).toBeLessThan(10000);
  });
});

// ---------------------------------------------------------------------------
// openDcaPosition + applySafetyOrderFill (position state lifecycle)
// ---------------------------------------------------------------------------

describe("dcaPlanning – position state lifecycle", () => {
  it("openDcaPosition creates correct initial state", () => {
    const state = openDcaPosition(10000, 0.01, 100, 1.5, "long");
    expect(state.fills).toHaveLength(1);
    expect(state.totalQty).toBe(0.01);
    expect(state.avgEntryPrice).toBe(10000);
    expect(state.totalCostUsd).toBe(100);
    expect(state.tpPrice).toBeCloseTo(10150, 2);
    expect(state.safetyOrdersFilled).toBe(0);
    expect(state.side).toBe("long");
  });

  it("applySafetyOrderFill updates avg entry and TP", () => {
    const state0 = openDcaPosition(10000, 0.01, 100, 1.5, "long");
    const state1 = applySafetyOrderFill(state0, 9900, 0.015, 148.5, 1.5);

    expect(state1.fills).toHaveLength(2);
    expect(state1.totalQty).toBeCloseTo(0.025, 6);
    expect(state1.safetyOrdersFilled).toBe(1);
    // Avg entry should be between 9900 and 10000
    expect(state1.avgEntryPrice).toBeGreaterThan(9900);
    expect(state1.avgEntryPrice).toBeLessThan(10000);
    // TP should be above new avg entry
    expect(state1.tpPrice).toBeGreaterThan(state1.avgEntryPrice);
    // TP should be lower than original TP (avg entry moved down)
    expect(state1.tpPrice).toBeLessThan(state0.tpPrice);
  });

  it("multiple fills accumulate correctly", () => {
    let state = openDcaPosition(10000, 0.01, 100, 1.5, "long");
    state = applySafetyOrderFill(state, 9900, 0.015, 148.5, 1.5);
    state = applySafetyOrderFill(state, 9800, 0.0225, 220.5, 1.5);

    expect(state.fills).toHaveLength(3);
    expect(state.safetyOrdersFilled).toBe(2);
    expect(state.totalCostUsd).toBeCloseTo(469, 0);
    expect(state.avgEntryPrice).toBeLessThan(9900);
    expect(state.avgEntryPrice).toBeGreaterThan(9800);
  });

  it("is immutable — original state unchanged after fill", () => {
    const state0 = openDcaPosition(10000, 0.01, 100, 1.5, "long");
    const original = { ...state0, fills: [...state0.fills] };
    applySafetyOrderFill(state0, 9900, 0.015, 148.5, 1.5);
    expect(state0.fills).toHaveLength(original.fills.length);
    expect(state0.avgEntryPrice).toBe(original.avgEntryPrice);
  });

  it("short DCA: avg entry rises and TP falls", () => {
    const state0 = openDcaPosition(10000, 0.01, 100, 1.5, "short");
    expect(state0.tpPrice).toBeCloseTo(9850, 2);

    const state1 = applySafetyOrderFill(state0, 10100, 0.015, 151.5, 1.5);
    expect(state1.avgEntryPrice).toBeGreaterThan(10000);
    expect(state1.tpPrice).toBeLessThan(state1.avgEntryPrice);
    expect(state1.tpPrice).toBeGreaterThan(state0.tpPrice); // TP moved up (less favorable for short)
  });
});
