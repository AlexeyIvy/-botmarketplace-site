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

// ---------------------------------------------------------------------------
// 5. SO trigger evaluation (slice 3): poll loop checks price → triggers SOs
// ---------------------------------------------------------------------------

describe("worker DCA integration – SO trigger evaluation (slice 3)", () => {
  function makeActiveLadder() {
    const dcaConfig = extractDcaConfig(makeDcaDsl())!;
    const ladder = initializeDcaLadder(dcaConfig, "long", 10);
    const recovered = recoverDcaState({ dcaState: ladder.serialized })!;
    return handleDcaBaseFill(recovered, 10000, 0.01);
  }

  it("detects triggered SOs when price drops to trigger level", () => {
    const { state } = makeActiveLadder();
    const so0 = state.schedule!.safetyOrders[0];

    // Price at SO trigger → should trigger
    const triggered = checkAndTriggerSOs(state, so0.triggerPrice);
    expect(triggered).toHaveLength(1);
    expect(triggered[0].index).toBe(0);
    expect(triggered[0].triggerPrice).toBe(so0.triggerPrice);
    expect(triggered[0].qty).toBeGreaterThan(0);
    expect(triggered[0].orderSizeUsd).toBeGreaterThan(0);
  });

  it("returns empty when price is above all SO triggers", () => {
    const { state } = makeActiveLadder();
    const triggered = checkAndTriggerSOs(state, 10001);
    expect(triggered).toHaveLength(0);
  });

  it("returns multiple SOs on a large price drop", () => {
    const { state } = makeActiveLadder();
    const lastSO = state.schedule!.safetyOrders[2];
    const triggered = checkAndTriggerSOs(state, lastSO.triggerPrice - 1);
    expect(triggered).toHaveLength(3);
  });

  it("skips already-filled SOs after sequential application", () => {
    let { state } = makeActiveLadder();
    // Fill SO 0
    const so0 = state.schedule!.safetyOrders[0];
    state = handleDcaSoFill(state, 0, so0.triggerPrice, so0.qty).state;

    // Now check triggers — SO 0 should be skipped
    const so1 = state.schedule!.safetyOrders[1];
    const triggered = checkAndTriggerSOs(state, so1.triggerPrice);
    expect(triggered).toHaveLength(1);
    expect(triggered[0].index).toBe(1);
  });

  it("SO intent has correct metaJson shape for fill reconciliation", () => {
    const { state } = makeActiveLadder();
    const so0 = state.schedule!.safetyOrders[0];

    // This is what the worker puts in SO intent metaJson
    const soIntentMeta = {
      dca: true,
      dcaSafetyOrder: true,
      soIndex: so0.index,
      triggerPrice: so0.triggerPrice,
      positionId: "pos-123",
    };

    // meta.dca === true → fill path will activate DCA state update
    expect(soIntentMeta.dca).toBe(true);
    expect(soIntentMeta.soIndex).toBe(0);
  });

  it("short-side SO triggers work above entry price", () => {
    const dcaConfig = extractDcaConfig(makeDcaDsl())!;
    const ladder = initializeDcaLadder(dcaConfig, "short", 10);
    const recovered = recoverDcaState({ dcaState: ladder.serialized })!;
    const { state } = handleDcaBaseFill(recovered, 10000, 0.01);

    const so0 = state.schedule!.safetyOrders[0];
    expect(so0.triggerPrice).toBeGreaterThan(10000);

    const triggered = checkAndTriggerSOs(state, so0.triggerPrice + 1);
    expect(triggered.length).toBeGreaterThanOrEqual(1);
  });
});

// ---------------------------------------------------------------------------
// 6. DCA ladder finalization (slice 3): position close → ladder completed
// ---------------------------------------------------------------------------

describe("worker DCA integration – ladder finalization (slice 3)", () => {
  it("finalizes ladder on position close", () => {
    const dcaConfig = extractDcaConfig(makeDcaDsl())!;
    const ladder = initializeDcaLadder(dcaConfig, "long", 10);
    const recovered = recoverDcaState({ dcaState: ladder.serialized })!;
    const { state } = handleDcaBaseFill(recovered, 10000, 0.01);

    // Simulate some SOs filled
    let current = state;
    const so0 = current.schedule!.safetyOrders[0];
    current = handleDcaSoFill(current, 0, so0.triggerPrice, so0.qty).state;

    // Position closes → finalize
    const finalized = finalizeDcaLadder(current, "position_closed");
    expect(finalized.state.phase).toBe("completed");
    expect(finalized.state.safetyOrdersFilled).toBe(1);
    expect(finalized.state.avgEntryPrice).toBeLessThan(10000);
  });

  it("finalization is idempotent", () => {
    const dcaConfig = extractDcaConfig(makeDcaDsl())!;
    const ladder = initializeDcaLadder(dcaConfig, "long", 10);
    const recovered = recoverDcaState({ dcaState: ladder.serialized })!;
    const { state } = handleDcaBaseFill(recovered, 10000, 0.01);

    const first = finalizeDcaLadder(state, "tp_hit");
    const second = finalizeDcaLadder(first.state, "tp_hit_again");
    expect(second.state).toBe(first.state); // same reference — no-op
  });

  it("finalized state persists and recovers correctly", () => {
    const dcaConfig = extractDcaConfig(makeDcaDsl())!;
    const ladder = initializeDcaLadder(dcaConfig, "long", 10);
    const recovered = recoverDcaState({ dcaState: ladder.serialized })!;
    const { state } = handleDcaBaseFill(recovered, 10000, 0.01);
    const finalized = finalizeDcaLadder(state, "sl_hit");

    // Persist and recover
    const metaJson = { dcaState: serializeDcaState(finalized.state) };
    const dbJson = JSON.parse(JSON.stringify(metaJson));
    const recoveredFinal = recoverDcaState(dbJson);
    expect(recoveredFinal).not.toBeNull();
    expect(recoveredFinal!.phase).toBe("completed");
  });
});

// ---------------------------------------------------------------------------
// 7. Startup recovery (slice 4): DCA state survives restart
// ---------------------------------------------------------------------------

describe("worker DCA integration – startup recovery (slice 4)", () => {
  it("recovers active DCA ladder from position metaJson on startup", () => {
    // Simulate: position has DCA state persisted from before restart
    const dcaConfig = extractDcaConfig(makeDcaDsl())!;
    const ladder = initializeDcaLadder(dcaConfig, "long", 10);
    const recovered = recoverDcaState({ dcaState: ladder.serialized })!;
    const { state } = handleDcaBaseFill(recovered, 10000, 0.01);

    // Fill one SO before "restart"
    const so0 = state.schedule!.safetyOrders[0];
    const afterSo = handleDcaSoFill(state, 0, so0.triggerPrice, so0.qty).state;

    // Persist → simulate restart → recover
    const posMetaJson = JSON.parse(JSON.stringify({
      dcaState: serializeDcaState(afterSo),
    }));

    const recoveredAfterRestart = recoverDcaState(posMetaJson);
    expect(recoveredAfterRestart).not.toBeNull();
    expect(recoveredAfterRestart!.phase).toBe("ladder_active");
    expect(recoveredAfterRestart!.safetyOrdersFilled).toBe(1);
    expect(recoveredAfterRestart!.nextSoIndex).toBe(1);
    expect(recoveredAfterRestart!.avgEntryPrice).toBeLessThan(10000);

    // Can continue filling SOs from recovered state
    const so1 = recoveredAfterRestart!.schedule!.safetyOrders[1];
    const soResult = handleDcaSoFill(recoveredAfterRestart!, 1, so1.triggerPrice, so1.qty);
    expect(soResult.state.safetyOrdersFilled).toBe(2);
    expect(soResult.state.nextSoIndex).toBe(2);
  });

  it("recovery returns null for non-DCA position", () => {
    const posMetaJson = { source: "reconciliation", orderId: "abc" };
    expect(recoverDcaState(posMetaJson)).toBeNull();
  });

  it("recovery returns null for corrupted DCA state", () => {
    const posMetaJson = { dcaState: { phase: "ladder_active", corrupted: true } };
    expect(recoverDcaState(posMetaJson)).toBeNull();
  });

  it("completed ladder survives restart and is recognized as terminal", () => {
    const dcaConfig = extractDcaConfig(makeDcaDsl())!;
    const ladder = initializeDcaLadder(dcaConfig, "long", 10);
    const recovered = recoverDcaState({ dcaState: ladder.serialized })!;
    const { state } = handleDcaBaseFill(recovered, 10000, 0.01);
    const finalized = finalizeDcaLadder(state, "tp_hit");

    const posMetaJson = JSON.parse(JSON.stringify({
      dcaState: serializeDcaState(finalized.state),
    }));

    const recoveredAfterRestart = recoverDcaState(posMetaJson);
    expect(recoveredAfterRestart).not.toBeNull();
    expect(recoveredAfterRestart!.phase).toBe("completed");
    // Poll loop won't trigger SOs on completed ladders
    const triggered = checkAndTriggerSOs(recoveredAfterRestart!, 5000);
    expect(triggered).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// 8. Bot detail API response shape (slice 4)
// ---------------------------------------------------------------------------

describe("worker DCA integration – API response shape (slice 4)", () => {
  it("DCA ladder response has expected fields", () => {
    const dcaConfig = extractDcaConfig(makeDcaDsl())!;
    const ladder = initializeDcaLadder(dcaConfig, "long", 10);
    const recovered = recoverDcaState({ dcaState: ladder.serialized })!;
    const { state } = handleDcaBaseFill(recovered, 10000, 0.01);

    // Simulate what the API route constructs from dcaState
    const dcaLadder = {
      phase: state.phase,
      side: state.side,
      baseEntryPrice: state.baseEntryPrice,
      avgEntryPrice: state.avgEntryPrice,
      tpPrice: state.tpPrice,
      slPrice: state.slPrice,
      safetyOrdersFilled: state.safetyOrdersFilled,
      nextSoIndex: state.nextSoIndex,
      totalCostUsd: state.totalCostUsd,
      fillCount: state.fills.length,
    };

    expect(dcaLadder.phase).toBe("ladder_active");
    expect(dcaLadder.side).toBe("long");
    expect(dcaLadder.baseEntryPrice).toBe(10000);
    expect(dcaLadder.avgEntryPrice).toBe(10000);
    expect(dcaLadder.safetyOrdersFilled).toBe(0);
    expect(dcaLadder.nextSoIndex).toBe(0);
    expect(dcaLadder.fillCount).toBe(1);
    expect(dcaLadder.tpPrice).toBeGreaterThan(10000);
    expect(dcaLadder.slPrice).toBeLessThan(10000);
    expect(dcaLadder.totalCostUsd).toBeGreaterThan(0);
  });

  it("no dcaLadder for non-DCA position", () => {
    // When recoverDcaState returns null, API sets dcaLadder = null
    const result = recoverDcaState(null);
    expect(result).toBeNull();
  });
});
