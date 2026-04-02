/**
 * DCA Runtime Bridge (#132 — Slice 1)
 *
 * Thin integration layer between the pure DCA engine state machine
 * and the bot worker runtime. Provides helper functions that the worker
 * calls at key lifecycle points:
 *
 *   1. Entry signal → initializeDcaLadder()
 *   2. Base order fill → handleDcaBaseFill()
 *   3. Price update / candle close → checkAndTriggerSOs()
 *   4. Safety order fill → handleDcaSoFill()
 *   5. Position close → finalizeDcaLadder()
 *
 * These helpers translate between worker-level concepts (intents, positions,
 * DSL json) and the DCA engine's pure state transitions.
 *
 * Persistence: The worker stores DCA state in Position.metaJson.dcaState.
 * This module reads/writes that field via the provided accessors but never
 * calls the database directly.
 */

import type { DcaConfig } from "../dcaPlanning.js";
import type { DcaRuntimeState, DcaTransitionResult } from "./dcaEngine.js";
import type { SafetyOrderLevel } from "../dcaPlanning.js";

import {
  initDcaState,
  applyBaseFill,
  applySafetyOrderFillRT,
  evaluateTriggeredSOs,
  completeDcaLadder,
  cancelDcaLadder,
  serializeDcaState,
  deserializeDcaState,
} from "./dcaEngine.js";

// ---------------------------------------------------------------------------
// DSL extraction
// ---------------------------------------------------------------------------

/**
 * Extract DCA config from a parsed DSL json object.
 * Returns null if no DCA config is present or invalid.
 */
export function extractDcaConfig(dslJson: unknown): DcaConfig | null {
  if (!dslJson || typeof dslJson !== "object") return null;
  const obj = dslJson as Record<string, unknown>;
  const dca = obj.dca;
  if (!dca || typeof dca !== "object") return null;
  return dca as DcaConfig;
}

/**
 * Extract stop-loss percentage from DSL exit configuration.
 * Falls back to risk.riskPerTradePct if exit.stopLoss is not fixed_pct.
 *
 * TODO(#132-slice2): For atr_multiple and fixed_price SL types, the backtest
 * evaluator derives SL% from abs(entry - slPrice) / entry * 100 at entry time.
 * This bridge currently falls back to riskPerTradePct for those types, which will
 * produce different SL levels than backtest. When worker integration is wired,
 * accept a computedSlPrice parameter and derive % the same way the evaluator does.
 */
export function extractSlPct(dslJson: unknown): number {
  if (!dslJson || typeof dslJson !== "object") return 5;
  const obj = dslJson as Record<string, unknown>;

  // Try v2 exit.stopLoss
  const exit = obj.exit as Record<string, unknown> | undefined;
  if (exit?.stopLoss && typeof exit.stopLoss === "object") {
    const sl = exit.stopLoss as Record<string, unknown>;
    if (sl.type === "fixed_pct" && typeof sl.value === "number") {
      return sl.value;
    }
  }

  // Fallback to risk.riskPerTradePct
  const risk = obj.risk as Record<string, unknown> | undefined;
  if (typeof risk?.riskPerTradePct === "number") {
    return risk.riskPerTradePct;
  }

  return 5; // safe default
}

// ---------------------------------------------------------------------------
// Lifecycle helpers
// ---------------------------------------------------------------------------

export interface DcaLadderInit {
  dcaState: DcaRuntimeState;
  serialized: Record<string, unknown>;
}

/**
 * Initialize a DCA ladder when an entry signal fires.
 *
 * Called by the worker when it detects that the strategy has a DCA config
 * and an entry signal has been generated. Creates the initial state
 * in "awaiting_base" phase.
 *
 * @returns The initial DCA state + serialized form for metaJson
 */
export function initializeDcaLadder(
  dcaConfig: DcaConfig,
  side: "long" | "short",
  stopLossPct: number,
): DcaLadderInit {
  const dcaState = initDcaState(dcaConfig, side, stopLossPct);
  return {
    dcaState,
    serialized: serializeDcaState(dcaState),
  };
}

/**
 * Handle the base order fill.
 *
 * Transitions state from awaiting_base → ladder_active.
 * Returns the transition result with the updated state, plus
 * the list of safety order levels that should be tracked.
 */
export function handleDcaBaseFill(
  dcaState: DcaRuntimeState,
  fillPrice: number,
  fillQty: number,
): DcaTransitionResult & { pendingSOs: SafetyOrderLevel[] } {
  const result = applyBaseFill(dcaState, fillPrice, fillQty);
  const pendingSOs = result.state.schedule?.safetyOrders ?? [];
  return { ...result, pendingSOs };
}

/**
 * Check if any safety orders should trigger at the current price.
 *
 * Returns the list of triggered SO levels. The worker should then
 * place orders for these levels and call handleDcaSoFill() when each fills.
 */
export function checkAndTriggerSOs(
  dcaState: DcaRuntimeState,
  currentPrice: number,
): SafetyOrderLevel[] {
  return evaluateTriggeredSOs(dcaState, currentPrice);
}

/**
 * Handle a safety order fill.
 *
 * Updates avg entry, TP, SL, and advances the ladder.
 */
export function handleDcaSoFill(
  dcaState: DcaRuntimeState,
  soIndex: number,
  fillPrice: number,
  fillQty: number,
): DcaTransitionResult {
  return applySafetyOrderFillRT(dcaState, soIndex, fillPrice, fillQty);
}

/**
 * Finalize the DCA ladder when the position is closed.
 */
export function finalizeDcaLadder(
  dcaState: DcaRuntimeState,
  reason: string,
): DcaTransitionResult {
  return completeDcaLadder(dcaState, reason);
}

/**
 * Cancel the DCA ladder (bot stopped, error, etc).
 */
export function cancelDca(
  dcaState: DcaRuntimeState,
  reason: string,
): DcaTransitionResult {
  return cancelDcaLadder(dcaState, reason);
}

// ---------------------------------------------------------------------------
// State recovery
// ---------------------------------------------------------------------------

/**
 * Recover DCA state from a position's metaJson.
 *
 * Used on bot restart to reconstruct the DCA engine state from
 * persisted data without re-querying the exchange.
 *
 * @param metaJson  The Position.metaJson field
 * @returns The recovered DCA state, or null if not a DCA position
 */
export function recoverDcaState(metaJson: unknown): DcaRuntimeState | null {
  if (!metaJson || typeof metaJson !== "object") return null;
  const meta = metaJson as Record<string, unknown>;
  return deserializeDcaState(meta.dcaState ?? null);
}
