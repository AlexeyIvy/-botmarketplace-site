import { describe, it, expect } from "vitest";
import {
  generateSafetyOrderSchedule,
  calculateAvgEntry,
  recalcTakeProfit,
  recalcStopLoss,
  calculateMaxExposure,
  calculateMaxDeviation,
  validateDcaConfig,
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
// validateDcaConfig
// ---------------------------------------------------------------------------

describe("dcaPlanning – validateDcaConfig", () => {
  it("returns null for valid config", () => {
    expect(validateDcaConfig(makeConfig())).toBeNull();
  });

  it("rejects baseOrderSizeUsd <= 0", () => {
    expect(validateDcaConfig(makeConfig({ baseOrderSizeUsd: 0 }))).toContain("baseOrderSizeUsd");
    expect(validateDcaConfig(makeConfig({ baseOrderSizeUsd: -1 }))).toContain("baseOrderSizeUsd");
  });

  it("rejects non-finite baseOrderSizeUsd", () => {
    expect(validateDcaConfig(makeConfig({ baseOrderSizeUsd: Infinity }))).toContain("baseOrderSizeUsd");
    expect(validateDcaConfig(makeConfig({ baseOrderSizeUsd: NaN }))).toContain("baseOrderSizeUsd");
  });

  it("rejects priceStepPct <= 0", () => {
    expect(validateDcaConfig(makeConfig({ priceStepPct: 0 }))).toContain("priceStepPct");
  });

  it("rejects stepScale < 1", () => {
    expect(validateDcaConfig(makeConfig({ stepScale: 0.5 }))).toContain("stepScale");
  });

  it("rejects volumeScale < 1", () => {
    expect(validateDcaConfig(makeConfig({ volumeScale: 0.9 }))).toContain("volumeScale");
  });

  it("rejects takeProfitPct <= 0", () => {
    expect(validateDcaConfig(makeConfig({ takeProfitPct: 0 }))).toContain("takeProfitPct");
  });

  it("rejects config where deviation >= 100%", () => {
    // 50 SOs at 5% step with 1x scale = 250% deviation → rejected
    const cfg = makeConfig({ maxSafetyOrders: 50, priceStepPct: 5.0, stepScale: 1.0 });
    const err = validateDcaConfig(cfg);
    expect(err).not.toBeNull();
    expect(err).toContain("deviation");
  });

  it("accepts config where deviation stays well under 100%", () => {
    const cfg = makeConfig({ maxSafetyOrders: 5, priceStepPct: 1.0, stepScale: 1.0 });
    expect(validateDcaConfig(cfg)).toBeNull();
  });

  it("rejects null/undefined config", () => {
    expect(validateDcaConfig(null as unknown as DcaConfig)).not.toBeNull();
    expect(validateDcaConfig(undefined as unknown as DcaConfig)).not.toBeNull();
  });
});

// ---------------------------------------------------------------------------
// calculateMaxDeviation
// ---------------------------------------------------------------------------

describe("dcaPlanning – calculateMaxDeviation", () => {
  it("calculates correct cumulative deviation with stepScale 1.0", () => {
    // 3 SOs at 1% step = 3%
    expect(calculateMaxDeviation(makeConfig())).toBeCloseTo(3.0, 6);
  });

  it("calculates correct cumulative deviation with stepScale 2.0", () => {
    // Steps: 1, 2, 4 → cumulative: 1, 3, 7
    const cfg = makeConfig({ priceStepPct: 1.0, stepScale: 2.0 });
    expect(calculateMaxDeviation(cfg)).toBeCloseTo(7.0, 6);
  });

  it("returns 0 for 0 safety orders", () => {
    expect(calculateMaxDeviation(makeConfig({ maxSafetyOrders: 0 }))).toBe(0);
  });
});

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
    expect(schedule.safetyOrders[0].orderSizeUsd).toBeCloseTo(200, 2);
    expect(schedule.safetyOrders[1].orderSizeUsd).toBeCloseTo(400, 2);
    expect(schedule.safetyOrders[2].orderSizeUsd).toBeCloseTo(800, 2);
  });

  it("step scale compounds price deviations", () => {
    const cfg = makeConfig({ priceStepPct: 1.0, stepScale: 2.0 });
    const schedule = generateSafetyOrderSchedule(cfg, 10000, "long");
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

  it("throws on invalid config (e.g., baseOrderSizeUsd <= 0)", () => {
    expect(() =>
      generateSafetyOrderSchedule(makeConfig({ baseOrderSizeUsd: 0 }), 10000, "long"),
    ).toThrow("Invalid DCA config");
  });

  it("throws on non-positive baseEntryPrice", () => {
    expect(() =>
      generateSafetyOrderSchedule(makeConfig(), 0, "long"),
    ).toThrow("baseEntryPrice");
    expect(() =>
      generateSafetyOrderSchedule(makeConfig(), -100, "long"),
    ).toThrow("baseEntryPrice");
  });

  it("throws on config where deviation >= 100%", () => {
    const cfg = makeConfig({ maxSafetyOrders: 50, priceStepPct: 5.0, stepScale: 1.0 });
    expect(() =>
      generateSafetyOrderSchedule(cfg, 10000, "long"),
    ).toThrow("deviation");
  });

  it("all trigger prices are positive for valid config", () => {
    const schedule = generateSafetyOrderSchedule(makeConfig(), 10000, "long");
    for (const so of schedule.safetyOrders) {
      expect(so.triggerPrice).toBeGreaterThan(0);
      expect(Number.isFinite(so.triggerPrice)).toBe(true);
    }
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
// recalcStopLoss
// ---------------------------------------------------------------------------

describe("dcaPlanning – recalcStopLoss", () => {
  it("long SL is below avg entry", () => {
    const sl = recalcStopLoss(10000, 5.0, "long");
    expect(sl).toBeCloseTo(9500, 2);
  });

  it("short SL is above avg entry", () => {
    const sl = recalcStopLoss(10000, 5.0, "short");
    expect(sl).toBeCloseTo(10500, 2);
  });

  it("SL moves down as avg entry moves down (long DCA)", () => {
    const sl1 = recalcStopLoss(10000, 5.0, "long");
    const sl2 = recalcStopLoss(9800, 5.0, "long");
    expect(sl2).toBeLessThan(sl1);
  });

  it("SL and TP are symmetric around avg entry for same percentage", () => {
    const pct = 2.0;
    const avg = 10000;
    const sl = recalcStopLoss(avg, pct, "long");
    const tp = recalcTakeProfit(avg, pct, "long");
    expect(avg - sl).toBeCloseTo(tp - avg, 2);
  });
});

// ---------------------------------------------------------------------------
// calculateMaxExposure
// ---------------------------------------------------------------------------

describe("dcaPlanning – calculateMaxExposure", () => {
  it("equals base for maxSafetyOrders = 0 edge case", () => {
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
    expect(calculateMaxExposure(cfg)).toBeCloseTo(812.5, 2);
  });

  it("large ladder: 12 SOs with volumeScale 1.2", () => {
    const cfg = makeConfig({ baseOrderSizeUsd: 100, maxSafetyOrders: 12, volumeScale: 1.2 });
    const exposure = calculateMaxExposure(cfg);
    expect(exposure).toBeGreaterThan(100);
    expect(exposure).toBeLessThan(10000);
  });
});

// ---------------------------------------------------------------------------
// openDcaPosition + applySafetyOrderFill (position state lifecycle)
// ---------------------------------------------------------------------------

describe("dcaPlanning – position state lifecycle", () => {
  it("openDcaPosition creates correct initial state with SL and TP", () => {
    const state = openDcaPosition(10000, 0.01, 100, 1.5, 5.0, "long");
    expect(state.fills).toHaveLength(1);
    expect(state.totalQty).toBe(0.01);
    expect(state.avgEntryPrice).toBe(10000);
    expect(state.totalCostUsd).toBe(100);
    expect(state.tpPrice).toBeCloseTo(10150, 2);
    expect(state.slPrice).toBeCloseTo(9500, 2);
    expect(state.safetyOrdersFilled).toBe(0);
    expect(state.side).toBe("long");
  });

  it("applySafetyOrderFill updates avg entry, TP, and SL", () => {
    const state0 = openDcaPosition(10000, 0.01, 100, 1.5, 5.0, "long");
    const state1 = applySafetyOrderFill(state0, 9900, 0.015, 148.5, 1.5, 5.0);

    expect(state1.fills).toHaveLength(2);
    expect(state1.totalQty).toBeCloseTo(0.025, 6);
    expect(state1.safetyOrdersFilled).toBe(1);
    // Avg entry should be between 9900 and 10000
    expect(state1.avgEntryPrice).toBeGreaterThan(9900);
    expect(state1.avgEntryPrice).toBeLessThan(10000);
    // TP should be above new avg entry and lower than original TP
    expect(state1.tpPrice).toBeGreaterThan(state1.avgEntryPrice);
    expect(state1.tpPrice).toBeLessThan(state0.tpPrice);
    // SL should be below new avg entry and lower than original SL
    expect(state1.slPrice).toBeLessThan(state1.avgEntryPrice);
    expect(state1.slPrice).toBeLessThan(state0.slPrice);
  });

  it("SL recalculation is consistent with TP recalculation", () => {
    const state0 = openDcaPosition(10000, 0.01, 100, 1.5, 5.0, "long");
    const state1 = applySafetyOrderFill(state0, 9900, 0.015, 148.5, 1.5, 5.0);
    // SL distance from avg = 5% of avg
    const slDist = state1.avgEntryPrice - state1.slPrice;
    expect(slDist / state1.avgEntryPrice * 100).toBeCloseTo(5.0, 2);
    // TP distance from avg = 1.5% of avg
    const tpDist = state1.tpPrice - state1.avgEntryPrice;
    expect(tpDist / state1.avgEntryPrice * 100).toBeCloseTo(1.5, 2);
  });

  it("multiple fills accumulate correctly with SL tracking", () => {
    let state = openDcaPosition(10000, 0.01, 100, 1.5, 5.0, "long");
    state = applySafetyOrderFill(state, 9900, 0.015, 148.5, 1.5, 5.0);
    state = applySafetyOrderFill(state, 9800, 0.0225, 220.5, 1.5, 5.0);

    expect(state.fills).toHaveLength(3);
    expect(state.safetyOrdersFilled).toBe(2);
    expect(state.totalCostUsd).toBeCloseTo(469, 0);
    expect(state.avgEntryPrice).toBeLessThan(9900);
    expect(state.avgEntryPrice).toBeGreaterThan(9800);
    // SL should track avg entry
    expect(state.slPrice).toBeCloseTo(state.avgEntryPrice * 0.95, 0);
  });

  it("is immutable — original state unchanged after fill", () => {
    const state0 = openDcaPosition(10000, 0.01, 100, 1.5, 5.0, "long");
    const original = { ...state0, fills: [...state0.fills] };
    applySafetyOrderFill(state0, 9900, 0.015, 148.5, 1.5, 5.0);
    expect(state0.fills).toHaveLength(original.fills.length);
    expect(state0.avgEntryPrice).toBe(original.avgEntryPrice);
    expect(state0.slPrice).toBe(original.slPrice);
  });

  it("short DCA: avg entry rises, TP and SL adjust", () => {
    const state0 = openDcaPosition(10000, 0.01, 100, 1.5, 5.0, "short");
    expect(state0.tpPrice).toBeCloseTo(9850, 2);
    expect(state0.slPrice).toBeCloseTo(10500, 2);

    const state1 = applySafetyOrderFill(state0, 10100, 0.015, 151.5, 1.5, 5.0);
    expect(state1.avgEntryPrice).toBeGreaterThan(10000);
    expect(state1.tpPrice).toBeLessThan(state1.avgEntryPrice);
    expect(state1.slPrice).toBeGreaterThan(state1.avgEntryPrice);
    // SL moved up (tracks higher avg entry for short)
    expect(state1.slPrice).toBeGreaterThan(state0.slPrice);
  });
});
