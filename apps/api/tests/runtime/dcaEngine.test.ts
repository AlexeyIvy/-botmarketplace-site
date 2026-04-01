import { describe, it, expect } from "vitest";
import type { DcaConfig } from "../../src/lib/dcaPlanning.js";
import type { DcaRuntimeState } from "../../src/lib/runtime/dcaEngine.js";
import {
  initDcaState,
  applyBaseFill,
  applySafetyOrderFillRT,
  evaluateTriggeredSOs,
  completeDcaLadder,
  cancelDcaLadder,
  getNextPendingSO,
  getRemainingExposure,
  getTotalExposure,
  isTerminal,
  serializeDcaState,
  deserializeDcaState,
} from "../../src/lib/runtime/dcaEngine.js";
import {
  extractDcaConfig,
  extractSlPct,
  initializeDcaLadder,
  handleDcaBaseFill,
  checkAndTriggerSOs,
  handleDcaSoFill,
  finalizeDcaLadder,
  recoverDcaState,
} from "../../src/lib/runtime/dcaBridge.js";

// ---------------------------------------------------------------------------
// Fixture
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

function makeDsl(dcaConfig?: DcaConfig) {
  return {
    id: "test-dca",
    name: "DCA Test",
    dslVersion: 2,
    enabled: true,
    market: { exchange: "bybit", env: "demo", category: "linear", symbol: "BTCUSDT" },
    entry: { side: "Buy" },
    exit: {
      stopLoss: { type: "fixed_pct", value: 10 },
      takeProfit: { type: "fixed_pct", value: 5 },
    },
    risk: { maxPositionSizeUsd: 1000, riskPerTradePct: 2, cooldownSeconds: 0 },
    execution: { orderType: "Market", clientOrderIdPrefix: "test_" },
    guards: { maxOpenPositions: 1, maxOrdersPerMinute: 10, pauseOnError: true },
    ...(dcaConfig ? { dca: dcaConfig } : {}),
  };
}

const NOW = 1700000000000;

// ---------------------------------------------------------------------------
// initDcaState
// ---------------------------------------------------------------------------

describe("dcaEngine – initDcaState", () => {
  it("creates state in awaiting_base phase", () => {
    const state = initDcaState(makeConfig(), "long", 10, NOW);
    expect(state.phase).toBe("awaiting_base");
    expect(state.side).toBe("long");
    expect(state.stopLossPct).toBe(10);
    expect(state.fills).toHaveLength(0);
    expect(state.avgEntryPrice).toBe(0);
    expect(state.totalQty).toBe(0);
    expect(state.schedule).toBeNull();
    expect(state.nextSoIndex).toBe(0);
    expect(state.createdAt).toBe(NOW);
  });

  it("stores the config for later use", () => {
    const cfg = makeConfig({ maxSafetyOrders: 5 });
    const state = initDcaState(cfg, "short", 5, NOW);
    expect(state.config.maxSafetyOrders).toBe(5);
    expect(state.side).toBe("short");
  });

  it("throws on invalid config", () => {
    expect(() => initDcaState(makeConfig({ baseOrderSizeUsd: 0 }), "long", 10)).toThrow();
  });
});

// ---------------------------------------------------------------------------
// applyBaseFill
// ---------------------------------------------------------------------------

describe("dcaEngine – applyBaseFill", () => {
  it("transitions from awaiting_base to ladder_active", () => {
    const state = initDcaState(makeConfig(), "long", 10, NOW);
    const result = applyBaseFill(state, 10000, 0.01, NOW + 1000);

    expect(result.state.phase).toBe("ladder_active");
    expect(result.state.baseEntryPrice).toBe(10000);
    expect(result.state.avgEntryPrice).toBe(10000);
    expect(result.state.fills).toHaveLength(1);
    expect(result.state.totalQty).toBe(0.01);
    expect(result.exitLevelsChanged).toBe(true);
    expect(result.state.updatedAt).toBe(NOW + 1000);
  });

  it("generates safety order schedule", () => {
    const state = initDcaState(makeConfig(), "long", 10, NOW);
    const result = applyBaseFill(state, 10000, 0.01);

    expect(result.state.schedule).not.toBeNull();
    expect(result.state.schedule!.safetyOrders).toHaveLength(3);
    expect(result.state.nextSoIndex).toBe(0);
  });

  it("computes TP and SL from base entry", () => {
    const state = initDcaState(makeConfig({ takeProfitPct: 1.5 }), "long", 10, NOW);
    const result = applyBaseFill(state, 10000, 0.01);

    expect(result.state.tpPrice).toBeCloseTo(10150, 0);
    expect(result.state.slPrice).toBeCloseTo(9000, 0);
  });

  it("is idempotent if already in ladder_active", () => {
    const state = initDcaState(makeConfig(), "long", 10, NOW);
    const result1 = applyBaseFill(state, 10000, 0.01);
    const result2 = applyBaseFill(result1.state, 10000, 0.01);

    expect(result2.state).toBe(result1.state); // same reference
    expect(result2.exitLevelsChanged).toBe(false);
  });

  it("works for short side", () => {
    const state = initDcaState(makeConfig(), "short", 10, NOW);
    const result = applyBaseFill(state, 10000, 0.01);

    expect(result.state.tpPrice).toBeLessThan(10000);
    expect(result.state.slPrice).toBeGreaterThan(10000);
    // SOs should be above entry for short
    for (const so of result.state.schedule!.safetyOrders) {
      expect(so.triggerPrice).toBeGreaterThan(10000);
    }
  });
});

// ---------------------------------------------------------------------------
// applySafetyOrderFillRT
// ---------------------------------------------------------------------------

describe("dcaEngine – applySafetyOrderFillRT", () => {
  function makeActiveLadder(): DcaRuntimeState {
    const state = initDcaState(makeConfig(), "long", 10, NOW);
    return applyBaseFill(state, 10000, 0.01).state;
  }

  it("updates avg entry, TP, SL after SO fill", () => {
    const active = makeActiveLadder();
    const so0 = active.schedule!.safetyOrders[0];
    const result = applySafetyOrderFillRT(active, 0, so0.triggerPrice, so0.qty);

    expect(result.state.fills).toHaveLength(2);
    expect(result.state.safetyOrdersFilled).toBe(1);
    expect(result.state.avgEntryPrice).toBeLessThan(10000);
    expect(result.state.avgEntryPrice).toBeGreaterThan(so0.triggerPrice);
    expect(result.state.tpPrice).toBeLessThan(active.tpPrice);
    expect(result.state.slPrice).toBeLessThan(active.slPrice);
    expect(result.exitLevelsChanged).toBe(true);
  });

  it("advances nextSoIndex", () => {
    const active = makeActiveLadder();
    const so0 = active.schedule!.safetyOrders[0];
    const result = applySafetyOrderFillRT(active, 0, so0.triggerPrice, so0.qty);
    expect(result.state.nextSoIndex).toBe(1);
  });

  it("sets nextSoIndex to -1 when all SOs filled", () => {
    let state = makeActiveLadder();
    for (let i = 0; i < 3; i++) {
      const so = state.schedule!.safetyOrders[i];
      state = applySafetyOrderFillRT(state, i, so.triggerPrice, so.qty).state;
    }
    expect(state.nextSoIndex).toBe(-1);
    expect(state.safetyOrdersFilled).toBe(3);
  });

  it("is idempotent for already-filled SO", () => {
    const active = makeActiveLadder();
    const so0 = active.schedule!.safetyOrders[0];
    const result1 = applySafetyOrderFillRT(active, 0, so0.triggerPrice, so0.qty);
    const result2 = applySafetyOrderFillRT(result1.state, 0, so0.triggerPrice, so0.qty);

    expect(result2.state).toBe(result1.state);
    expect(result2.exitLevelsChanged).toBe(false);
  });

  it("no-ops in wrong phase", () => {
    const state = initDcaState(makeConfig(), "long", 10, NOW);
    const result = applySafetyOrderFillRT(state, 0, 9900, 0.015);
    expect(result.state).toBe(state);
    expect(result.exitLevelsChanged).toBe(false);
  });

  it("accumulates fills correctly across 3 SOs", () => {
    let state = makeActiveLadder();
    const initialCost = state.totalCostUsd;

    for (let i = 0; i < 3; i++) {
      const so = state.schedule!.safetyOrders[i];
      state = applySafetyOrderFillRT(state, i, so.triggerPrice, so.qty).state;
    }

    expect(state.fills).toHaveLength(4); // base + 3 SOs
    expect(state.totalCostUsd).toBeGreaterThan(initialCost);
    expect(state.totalQty).toBeGreaterThan(0.01); // more than base qty
  });
});

// ---------------------------------------------------------------------------
// evaluateTriggeredSOs
// ---------------------------------------------------------------------------

describe("dcaEngine – evaluateTriggeredSOs", () => {
  function makeActiveLadder(): DcaRuntimeState {
    const state = initDcaState(makeConfig(), "long", 10, NOW);
    return applyBaseFill(state, 10000, 0.01).state;
  }

  it("returns no SOs if price is above all triggers (long)", () => {
    const state = makeActiveLadder();
    const triggered = evaluateTriggeredSOs(state, 10000);
    expect(triggered).toHaveLength(0);
  });

  it("returns first SO when price touches first trigger", () => {
    const state = makeActiveLadder();
    const so0 = state.schedule!.safetyOrders[0];
    const triggered = evaluateTriggeredSOs(state, so0.triggerPrice);
    expect(triggered).toHaveLength(1);
    expect(triggered[0].index).toBe(0);
  });

  it("returns multiple SOs if price drops past several triggers", () => {
    const state = makeActiveLadder();
    const lastSO = state.schedule!.safetyOrders[2];
    // Price below all SO triggers
    const triggered = evaluateTriggeredSOs(state, lastSO.triggerPrice - 1);
    expect(triggered).toHaveLength(3);
  });

  it("skips already-filled SOs", () => {
    const active = makeActiveLadder();
    const so0 = active.schedule!.safetyOrders[0];
    const afterFill = applySafetyOrderFillRT(active, 0, so0.triggerPrice, so0.qty).state;

    const so1 = afterFill.schedule!.safetyOrders[1];
    const triggered = evaluateTriggeredSOs(afterFill, so1.triggerPrice);
    expect(triggered).toHaveLength(1);
    expect(triggered[0].index).toBe(1);
  });

  it("returns empty for non-ladder phases", () => {
    const state = initDcaState(makeConfig(), "long", 10, NOW);
    expect(evaluateTriggeredSOs(state, 5000)).toHaveLength(0);
  });

  it("works for short side (triggers above entry)", () => {
    const state = initDcaState(makeConfig(), "short", 10, NOW);
    const active = applyBaseFill(state, 10000, 0.01).state;
    const so0 = active.schedule!.safetyOrders[0];
    // For short, SO triggers when price goes UP
    const triggered = evaluateTriggeredSOs(active, so0.triggerPrice + 1);
    expect(triggered.length).toBeGreaterThanOrEqual(1);
  });
});

// ---------------------------------------------------------------------------
// completeDcaLadder / cancelDcaLadder
// ---------------------------------------------------------------------------

describe("dcaEngine – terminal transitions", () => {
  function makeActiveLadder(): DcaRuntimeState {
    const state = initDcaState(makeConfig(), "long", 10, NOW);
    return applyBaseFill(state, 10000, 0.01).state;
  }

  it("completeDcaLadder → completed phase", () => {
    const active = makeActiveLadder();
    const result = completeDcaLadder(active, "tp_hit");
    expect(result.state.phase).toBe("completed");
    expect(result.state.nextSoIndex).toBe(-1);
  });

  it("cancelDcaLadder → cancelled phase", () => {
    const active = makeActiveLadder();
    const result = cancelDcaLadder(active, "bot_stopped");
    expect(result.state.phase).toBe("cancelled");
  });

  it("no-ops on already-terminal state", () => {
    const active = makeActiveLadder();
    const completed = completeDcaLadder(active, "tp").state;
    const result = completeDcaLadder(completed, "again");
    expect(result.state).toBe(completed);

    const result2 = cancelDcaLadder(completed, "too_late");
    expect(result2.state).toBe(completed);
  });

  it("isTerminal returns true for completed/cancelled", () => {
    const active = makeActiveLadder();
    expect(isTerminal(active)).toBe(false);

    const completed = completeDcaLadder(active, "tp").state;
    expect(isTerminal(completed)).toBe(true);

    const cancelled = cancelDcaLadder(makeActiveLadder(), "err").state;
    expect(isTerminal(cancelled)).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Query helpers
// ---------------------------------------------------------------------------

describe("dcaEngine – query helpers", () => {
  it("getNextPendingSO returns first SO after base fill", () => {
    const state = initDcaState(makeConfig(), "long", 10, NOW);
    const active = applyBaseFill(state, 10000, 0.01).state;
    const next = getNextPendingSO(active);
    expect(next).not.toBeNull();
    expect(next!.index).toBe(0);
  });

  it("getNextPendingSO returns null when all SOs filled", () => {
    let state = applyBaseFill(initDcaState(makeConfig(), "long", 10), 10000, 0.01).state;
    for (let i = 0; i < 3; i++) {
      const so = state.schedule!.safetyOrders[i];
      state = applySafetyOrderFillRT(state, i, so.triggerPrice, so.qty).state;
    }
    expect(getNextPendingSO(state)).toBeNull();
  });

  it("getRemainingExposure decreases as SOs fill", () => {
    let state = applyBaseFill(initDcaState(makeConfig(), "long", 10), 10000, 0.01).state;
    const initial = getRemainingExposure(state);
    expect(initial).toBeGreaterThan(0);

    const so0 = state.schedule!.safetyOrders[0];
    state = applySafetyOrderFillRT(state, 0, so0.triggerPrice, so0.qty).state;
    const after = getRemainingExposure(state);
    expect(after).toBeLessThan(initial);
  });

  it("getTotalExposure equals filled + remaining", () => {
    const state = applyBaseFill(initDcaState(makeConfig(), "long", 10), 10000, 0.01).state;
    const total = getTotalExposure(state);
    expect(total).toBeCloseTo(state.totalCostUsd + getRemainingExposure(state), 2);
  });
});

// ---------------------------------------------------------------------------
// Serialization / deserialization
// ---------------------------------------------------------------------------

describe("dcaEngine – serialization", () => {
  it("round-trips through serialize → deserialize", () => {
    const state = initDcaState(makeConfig(), "long", 10, NOW);
    const active = applyBaseFill(state, 10000, 0.01, NOW + 1).state;

    const serialized = serializeDcaState(active);
    const recovered = deserializeDcaState(serialized);

    expect(recovered).not.toBeNull();
    expect(recovered!.phase).toBe("ladder_active");
    expect(recovered!.avgEntryPrice).toBe(10000);
    expect(recovered!.fills).toHaveLength(1);
    expect(recovered!.config.maxSafetyOrders).toBe(3);
  });

  it("deserialize returns null for non-DCA objects", () => {
    expect(deserializeDcaState(null)).toBeNull();
    expect(deserializeDcaState({})).toBeNull();
    expect(deserializeDcaState({ phase: "invalid" })).toBeNull();
    expect(deserializeDcaState("string")).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// dcaBridge
// ---------------------------------------------------------------------------

describe("dcaBridge – extractDcaConfig", () => {
  it("extracts DCA config from DSL", () => {
    const cfg = makeConfig();
    const dsl = makeDsl(cfg);
    const extracted = extractDcaConfig(dsl);
    expect(extracted).not.toBeNull();
    expect(extracted!.maxSafetyOrders).toBe(3);
  });

  it("returns null for DSL without DCA", () => {
    expect(extractDcaConfig(makeDsl())).toBeNull();
    expect(extractDcaConfig(null)).toBeNull();
    expect(extractDcaConfig({})).toBeNull();
  });
});

describe("dcaBridge – extractSlPct", () => {
  it("extracts SL% from exit.stopLoss.value", () => {
    expect(extractSlPct(makeDsl(makeConfig()))).toBe(10);
  });

  it("falls back to risk.riskPerTradePct", () => {
    const dsl = {
      ...makeDsl(),
      exit: { stopLoss: { type: "atr_multiple", value: 2 }, takeProfit: { type: "fixed_pct", value: 5 } },
    };
    expect(extractSlPct(dsl)).toBe(2); // riskPerTradePct
  });
});

describe("dcaBridge – initializeDcaLadder", () => {
  it("returns state and serialized form", () => {
    const result = initializeDcaLadder(makeConfig(), "long", 10);
    expect(result.dcaState.phase).toBe("awaiting_base");
    expect(result.serialized).toBeDefined();
    expect((result.serialized as Record<string, unknown>).phase).toBe("awaiting_base");
  });
});

describe("dcaBridge – handleDcaBaseFill", () => {
  it("returns pending SOs list", () => {
    const init = initializeDcaLadder(makeConfig(), "long", 10);
    const result = handleDcaBaseFill(init.dcaState, 10000, 0.01);
    expect(result.pendingSOs).toHaveLength(3);
    expect(result.state.phase).toBe("ladder_active");
  });
});

describe("dcaBridge – checkAndTriggerSOs", () => {
  it("delegates to evaluateTriggeredSOs", () => {
    const init = initializeDcaLadder(makeConfig(), "long", 10);
    const active = handleDcaBaseFill(init.dcaState, 10000, 0.01).state;
    const so0 = active.schedule!.safetyOrders[0];
    const triggered = checkAndTriggerSOs(active, so0.triggerPrice);
    expect(triggered).toHaveLength(1);
  });
});

describe("dcaBridge – recoverDcaState", () => {
  it("recovers from metaJson with dcaState key", () => {
    const init = initializeDcaLadder(makeConfig(), "long", 10);
    const active = handleDcaBaseFill(init.dcaState, 10000, 0.01).state;
    const metaJson = { dcaState: serializeDcaState(active) };
    const recovered = recoverDcaState(metaJson);
    expect(recovered).not.toBeNull();
    expect(recovered!.phase).toBe("ladder_active");
  });

  it("returns null for non-DCA metaJson", () => {
    expect(recoverDcaState(null)).toBeNull();
    expect(recoverDcaState({})).toBeNull();
    expect(recoverDcaState({ foo: "bar" })).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Full lifecycle integration test
// ---------------------------------------------------------------------------

describe("dcaEngine – full lifecycle (deterministic)", () => {
  it("base fill → 3 SO fills → complete: deterministic state progression", () => {
    // 1. Init
    const config = makeConfig();
    const state0 = initDcaState(config, "long", 10, NOW);
    expect(state0.phase).toBe("awaiting_base");

    // 2. Base fill at 10000
    const r1 = applyBaseFill(state0, 10000, 0.01, NOW + 1000);
    expect(r1.state.phase).toBe("ladder_active");
    expect(r1.state.fills).toHaveLength(1);
    const schedule = r1.state.schedule!;
    expect(schedule.safetyOrders).toHaveLength(3);

    // 3. SO 0 fill
    const so0 = schedule.safetyOrders[0];
    const r2 = applySafetyOrderFillRT(r1.state, 0, so0.triggerPrice, so0.qty, NOW + 2000);
    expect(r2.state.safetyOrdersFilled).toBe(1);
    expect(r2.state.nextSoIndex).toBe(1);
    expect(r2.state.avgEntryPrice).toBeLessThan(10000);

    // 4. SO 1 fill
    const so1 = schedule.safetyOrders[1];
    const r3 = applySafetyOrderFillRT(r2.state, 1, so1.triggerPrice, so1.qty, NOW + 3000);
    expect(r3.state.safetyOrdersFilled).toBe(2);
    expect(r3.state.nextSoIndex).toBe(2);
    expect(r3.state.avgEntryPrice).toBeLessThan(r2.state.avgEntryPrice);

    // 5. SO 2 fill
    const so2 = schedule.safetyOrders[2];
    const r4 = applySafetyOrderFillRT(r3.state, 2, so2.triggerPrice, so2.qty, NOW + 4000);
    expect(r4.state.safetyOrdersFilled).toBe(3);
    expect(r4.state.nextSoIndex).toBe(-1); // all SOs filled

    // 6. Complete (TP hit)
    const r5 = completeDcaLadder(r4.state, "tp_hit", NOW + 5000);
    expect(r5.state.phase).toBe("completed");
    expect(isTerminal(r5.state)).toBe(true);

    // 7. Verify determinism
    const state0b = initDcaState(config, "long", 10, NOW);
    const r1b = applyBaseFill(state0b, 10000, 0.01, NOW + 1000);
    const r2b = applySafetyOrderFillRT(r1b.state, 0, so0.triggerPrice, so0.qty, NOW + 2000);
    const r3b = applySafetyOrderFillRT(r2b.state, 1, so1.triggerPrice, so1.qty, NOW + 3000);
    const r4b = applySafetyOrderFillRT(r3b.state, 2, so2.triggerPrice, so2.qty, NOW + 4000);

    expect(r4b.state.avgEntryPrice).toBe(r4.state.avgEntryPrice);
    expect(r4b.state.tpPrice).toBe(r4.state.tpPrice);
    expect(r4b.state.slPrice).toBe(r4.state.slPrice);
    expect(r4b.state.totalQty).toBe(r4.state.totalQty);
    expect(r4b.state.totalCostUsd).toBe(r4.state.totalCostUsd);
  });

  it("cancel mid-ladder preserves filled state", () => {
    const state = initDcaState(makeConfig(), "long", 10, NOW);
    const active = applyBaseFill(state, 10000, 0.01).state;
    const so0 = active.schedule!.safetyOrders[0];
    const afterSo = applySafetyOrderFillRT(active, 0, so0.triggerPrice, so0.qty).state;

    const cancelled = cancelDcaLadder(afterSo, "bot_stopped").state;
    expect(cancelled.phase).toBe("cancelled");
    expect(cancelled.safetyOrdersFilled).toBe(1);
    expect(cancelled.fills).toHaveLength(2);
    // Avg entry and cost preserved
    expect(cancelled.avgEntryPrice).toBe(afterSo.avgEntryPrice);
    expect(cancelled.totalCostUsd).toBe(afterSo.totalCostUsd);
  });

  it("serialize → recover → continue ladder", () => {
    const state = initDcaState(makeConfig(), "long", 10, NOW);
    const active = applyBaseFill(state, 10000, 0.01).state;

    // Simulate persist
    const metaJson = { dcaState: serializeDcaState(active) };

    // Simulate restart/recovery
    const recovered = recoverDcaState(metaJson);
    expect(recovered).not.toBeNull();
    expect(recovered!.phase).toBe("ladder_active");

    // Continue from recovered state
    const so0 = recovered!.schedule!.safetyOrders[0];
    const result = applySafetyOrderFillRT(recovered!, 0, so0.triggerPrice, so0.qty);
    expect(result.state.safetyOrdersFilled).toBe(1);
    expect(result.state.avgEntryPrice).toBeLessThan(10000);
  });
});
