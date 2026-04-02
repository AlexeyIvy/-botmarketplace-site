/**
 * DCA Worker Integration Tests (#132 — Slice 2)
 *
 * Tests the DCA-aware paths added to botWorker:
 *   1. Entry intent creation with DCA config → DCA state in metaJson
 *   2. Base fill → DCA ladder activation + SL/TP override
 *   3. SO fill → ladder advance + SL/TP update
 *   4. Full lifecycle: init → base fill → SO fills → complete
 *
 * These tests exercise the bridge/engine functions in the same sequence
 * the worker calls them, without requiring Prisma or exchange mocks.
 */

import { describe, it, expect } from "vitest";
import type { DcaConfig } from "../../src/lib/dcaPlanning.js";
import {
  extractDcaConfig,
  extractSlPct,
  initializeDcaLadder,
  handleDcaBaseFill,
  handleDcaSoFill,
  checkAndTriggerSOs,
  finalizeDcaLadder,
  recoverDcaState,
} from "../../src/lib/runtime/dcaBridge.js";
import { serializeDcaState } from "../../src/lib/runtime/dcaEngine.js";

// ---------------------------------------------------------------------------
// Fixtures matching the worker's DSL shape
// ---------------------------------------------------------------------------

function makeDcaDsl() {
  return {
    id: "test-dca-worker",
    name: "DCA Worker Test",
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
    dca: {
      baseOrderSizeUsd: 100,
      maxSafetyOrders: 3,
      priceStepPct: 1.0,
      stepScale: 1.0,
      volumeScale: 1.5,
      takeProfitPct: 1.5,
    },
  };
}

function makeNonDcaDsl() {
  const dsl = makeDcaDsl();
  const { dca: _, ...rest } = dsl;
  return rest;
}

// ---------------------------------------------------------------------------
// 1. Entry intent creation: DCA config detection
// ---------------------------------------------------------------------------

describe("worker DCA integration – entry intent creation", () => {
  it("extracts DCA config from DSL used in worker", () => {
    const dsl = makeDcaDsl();
    const dcaConfig = extractDcaConfig(dsl);
    expect(dcaConfig).not.toBeNull();
    expect(dcaConfig!.baseOrderSizeUsd).toBe(100);
    expect(dcaConfig!.maxSafetyOrders).toBe(3);
  });

  it("returns null for non-DCA DSL (worker skips DCA path)", () => {
    expect(extractDcaConfig(makeNonDcaDsl())).toBeNull();
  });

  it("extracts SL% from DSL exit config", () => {
    expect(extractSlPct(makeDcaDsl())).toBe(10);
  });

  it("initializes DCA ladder for intent metaJson", () => {
    const dcaConfig = extractDcaConfig(makeDcaDsl())!;
    const stopLossPct = extractSlPct(makeDcaDsl());
    const ladder = initializeDcaLadder(dcaConfig, "long", stopLossPct);

    expect(ladder.dcaState.phase).toBe("awaiting_base");
    expect(ladder.dcaState.config.baseOrderSizeUsd).toBe(100);
    expect(ladder.dcaState.stopLossPct).toBe(10);

    // Serialized form is what goes into intent.metaJson.dcaState
    expect(ladder.serialized).toBeDefined();
    expect((ladder.serialized as Record<string, unknown>).phase).toBe("awaiting_base");
  });

  it("intent metaJson shape matches what worker creates", () => {
    const dcaConfig = extractDcaConfig(makeDcaDsl())!;
    const stopLossPct = extractSlPct(makeDcaDsl());
    const ladder = initializeDcaLadder(dcaConfig, "long", stopLossPct);

    // This mirrors the metaJson shape the worker constructs
    const intentMeta = {
      signalType: "crossover",
      reason: "sma_cross",
      slPrice: 9000,
      tpPrice: 10500,
      rawSizingQty: 0.01,
      exchangeQty: 0.01,
      notionalUsd: 100,
      dca: true,
      dcaBaseOrder: true,
      dcaState: ladder.serialized,
    };

    // Recovery must work from this shape
    const recovered = recoverDcaState({ dcaState: intentMeta.dcaState });
    expect(recovered).not.toBeNull();
    expect(recovered!.phase).toBe("awaiting_base");
  });
});

// ---------------------------------------------------------------------------
// 2. Base fill reconciliation: DCA ladder activation
// ---------------------------------------------------------------------------

describe("worker DCA integration – base fill reconciliation", () => {
  it("recovers DCA state from intent metaJson and applies base fill", () => {
    // Simulate: worker creates intent with DCA state, then reconciles fill
    const dcaConfig = extractDcaConfig(makeDcaDsl())!;
    const ladder = initializeDcaLadder(dcaConfig, "long", 10);

    // Simulate intent.metaJson as stored in DB
    const intentMeta = { dca: true, dcaState: ladder.serialized };

    // reconcileEntryFill recovers state from intent meta
    const recovered = recoverDcaState({ dcaState: intentMeta.dcaState });
    expect(recovered).not.toBeNull();

    // Apply base fill (what worker does after openPosition)
    const baseResult = handleDcaBaseFill(recovered!, 10000, 0.01);
    expect(baseResult.state.phase).toBe("ladder_active");
    expect(baseResult.state.baseEntryPrice).toBe(10000);
    expect(baseResult.pendingSOs).toHaveLength(3);
    expect(baseResult.exitLevelsChanged).toBe(true);

    // SL/TP from DCA state override the signal's values
    expect(baseResult.state.slPrice).toBeCloseTo(9000, 0);
    expect(baseResult.state.tpPrice).toBeCloseTo(10150, 0);
  });

  it("DCA base fill produces serializable state for position metaJson", () => {
    const dcaConfig = extractDcaConfig(makeDcaDsl())!;
    const ladder = initializeDcaLadder(dcaConfig, "long", 10);
    const recovered = recoverDcaState({ dcaState: ladder.serialized })!;
    const baseResult = handleDcaBaseFill(recovered, 10000, 0.01);

    // This is what goes into Position.metaJson
    const positionMeta = { dcaState: serializeDcaState(baseResult.state) };

    // Must be JSON-safe
    const json = JSON.stringify(positionMeta);
    const parsed = JSON.parse(json);
    expect(parsed.dcaState.phase).toBe("ladder_active");
    expect(parsed.dcaState.avgEntryPrice).toBe(10000);
  });
});

// ---------------------------------------------------------------------------
// 3. SO fill reconciliation: ladder advancement
// ---------------------------------------------------------------------------

describe("worker DCA integration – SO fill reconciliation", () => {
  function makeActiveLadderInPosition() {
    const dcaConfig = extractDcaConfig(makeDcaDsl())!;
    const ladder = initializeDcaLadder(dcaConfig, "long", 10);
    const recovered = recoverDcaState({ dcaState: ladder.serialized })!;
    const baseResult = handleDcaBaseFill(recovered, 10000, 0.01);
    return baseResult.state;
  }

  it("recovers DCA state from position metaJson and applies SO fill", () => {
    const activeLadder = makeActiveLadderInPosition();

    // Simulate: position.metaJson has DCA state from base fill
    const positionMeta = { dcaState: serializeDcaState(activeLadder) };

    // Worker recovers state from position metaJson
    const recovered = recoverDcaState(positionMeta);
    expect(recovered).not.toBeNull();
    expect(recovered!.nextSoIndex).toBe(0);

    // Apply SO fill
    const so0 = recovered!.schedule!.safetyOrders[0];
    const soResult = handleDcaSoFill(recovered!, 0, so0.triggerPrice, so0.qty);

    expect(soResult.exitLevelsChanged).toBe(true);
    expect(soResult.state.safetyOrdersFilled).toBe(1);
    expect(soResult.state.nextSoIndex).toBe(1);
    expect(soResult.state.avgEntryPrice).toBeLessThan(10000);
    // TP/SL recalculated from new avg entry
    expect(soResult.state.tpPrice).toBeLessThan(activeLadder.tpPrice);
    expect(soResult.state.slPrice).toBeLessThan(activeLadder.slPrice);
  });

  it("updated DCA state is persistable back to position metaJson", () => {
    const activeLadder = makeActiveLadderInPosition();
    const so0 = activeLadder.schedule!.safetyOrders[0];
    const soResult = handleDcaSoFill(activeLadder, 0, so0.triggerPrice, so0.qty);

    // Re-persist
    const updatedMeta = { dcaState: serializeDcaState(soResult.state) };
    const json = JSON.stringify(updatedMeta);
    const parsed = JSON.parse(json);

    // Recover again — must work for next SO
    const recovered2 = recoverDcaState(parsed);
    expect(recovered2).not.toBeNull();
    expect(recovered2!.safetyOrdersFilled).toBe(1);
    expect(recovered2!.nextSoIndex).toBe(1);
  });
});

// ---------------------------------------------------------------------------
// 4. Full worker lifecycle: init → base → SOs → complete
// ---------------------------------------------------------------------------

describe("worker DCA integration – full lifecycle", () => {
  it("simulates complete worker DCA flow end-to-end", () => {
    // Step 1: Worker detects DCA config in DSL
    const dsl = makeDcaDsl();
    const dcaConfig = extractDcaConfig(dsl)!;
    const stopLossPct = extractSlPct(dsl);

    // Step 2: Worker creates entry intent with DCA state
    const ladder = initializeDcaLadder(dcaConfig, "long", stopLossPct);
    const intentMeta = { dca: true, dcaBaseOrder: true, dcaState: ladder.serialized };

    // Step 3: Intent fills → reconcileEntryFill → base fill
    const recovered = recoverDcaState({ dcaState: intentMeta.dcaState })!;
    const baseResult = handleDcaBaseFill(recovered, 10000, 0.01);

    // Step 4: Store DCA state in position metaJson
    let currentState = baseResult.state;
    expect(currentState.phase).toBe("ladder_active");

    // Step 5: Worker poll loop checks SO triggers
    const so0 = currentState.schedule!.safetyOrders[0];
    let triggered = checkAndTriggerSOs(currentState, so0.triggerPrice);
    expect(triggered).toHaveLength(1);

    // Step 6: SO fills come through reconciliation
    for (let i = 0; i < 3; i++) {
      const so = currentState.schedule!.safetyOrders[i];
      const soResult = handleDcaSoFill(currentState, i, so.triggerPrice, so.qty);
      expect(soResult.exitLevelsChanged).toBe(true);
      currentState = soResult.state;
    }

    expect(currentState.safetyOrdersFilled).toBe(3);
    expect(currentState.nextSoIndex).toBe(-1);
    expect(currentState.avgEntryPrice).toBeLessThan(10000);

    // Step 7: TP hit → position closed → finalize ladder
    const finalResult = finalizeDcaLadder(currentState, "tp_hit");
    expect(finalResult.state.phase).toBe("completed");

    // Step 8: Verify SL/TP were consistently derived from avg entry
    const expectedSlDist = currentState.avgEntryPrice * 0.10;
    const actualSlDist = currentState.avgEntryPrice - currentState.slPrice;
    expect(actualSlDist).toBeCloseTo(expectedSlDist, 0);

    const expectedTpDist = currentState.avgEntryPrice * 0.015;
    const actualTpDist = currentState.tpPrice - currentState.avgEntryPrice;
    expect(actualTpDist).toBeCloseTo(expectedTpDist, 0);
  });

  it("non-DCA DSL flow is unaffected", () => {
    const dsl = makeNonDcaDsl();
    const dcaConfig = extractDcaConfig(dsl);
    expect(dcaConfig).toBeNull();
    // Worker follows the original non-DCA intent creation path
  });

  it("short-side DCA flow works correctly", () => {
    const dsl = makeDcaDsl();
    const dcaConfig = extractDcaConfig(dsl)!;
    const ladder = initializeDcaLadder(dcaConfig, "short", 10);
    const recovered = recoverDcaState({ dcaState: ladder.serialized })!;

    const baseResult = handleDcaBaseFill(recovered, 10000, 0.01);
    expect(baseResult.state.phase).toBe("ladder_active");
    // Short: TP below entry, SL above entry
    expect(baseResult.state.tpPrice).toBeLessThan(10000);
    expect(baseResult.state.slPrice).toBeGreaterThan(10000);

    // SOs trigger above entry for short
    const so0 = baseResult.state.schedule!.safetyOrders[0];
    expect(so0.triggerPrice).toBeGreaterThan(10000);

    const triggered = checkAndTriggerSOs(baseResult.state, so0.triggerPrice + 1);
    expect(triggered.length).toBeGreaterThanOrEqual(1);
  });

  it("DCA state survives JSON round-trip (simulates DB persistence)", () => {
    const dcaConfig = extractDcaConfig(makeDcaDsl())!;
    const ladder = initializeDcaLadder(dcaConfig, "long", 10);
    const recovered = recoverDcaState({ dcaState: ladder.serialized })!;
    const baseResult = handleDcaBaseFill(recovered, 10000, 0.01);

    // Simulate Prisma JSON persistence round-trip
    const dbJson = JSON.parse(JSON.stringify({ dcaState: serializeDcaState(baseResult.state) }));
    const recovered2 = recoverDcaState(dbJson);
    expect(recovered2).not.toBeNull();
    expect(recovered2!.phase).toBe("ladder_active");
    expect(recovered2!.avgEntryPrice).toBe(10000);
    expect(recovered2!.schedule!.safetyOrders).toHaveLength(3);

    // Can continue filling from recovered state
    const so0 = recovered2!.schedule!.safetyOrders[0];
    const soResult = handleDcaSoFill(recovered2!, 0, so0.triggerPrice, so0.qty);
    expect(soResult.state.safetyOrdersFilled).toBe(1);
  });
});
