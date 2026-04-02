/**
 * DCA Runtime Engine (#132 — Slice 1)
 *
 * Pure state machine for runtime DCA position lifecycle.
 * Owns state transitions for:
 *   - Base order initialization → ladder plan active
 *   - Safety order trigger evaluation
 *   - Fill application → avg entry / TP / SL / next step update
 *   - Position state serialization/recovery
 *
 * Design:
 *   - Pure functions: no I/O, no DB, no exchange calls
 *   - Reuses planning primitives from dcaPlanning.ts (#131)
 *   - State is an immutable value object — each transition returns a new state
 *   - Designed for reconciliation-friendly modeling: every transition is idempotent
 *     given the same inputs
 *   - One logical DCA position invariant: all ladder activity belongs to one position
 *
 * The bot worker / runtime layer calls these functions and persists state
 * to DB / metaJson. This module never touches persistence directly.
 */

import type {
  DcaConfig,
  DcaSchedule,
  SafetyOrderLevel,
  DcaFill,
} from "../dcaPlanning.js";

import {
  generateSafetyOrderSchedule,
  calculateAvgEntry,
  recalcTakeProfit,
  recalcStopLoss,
  validateDcaConfig,
} from "../dcaPlanning.js";

// ---------------------------------------------------------------------------
// Runtime state types
// ---------------------------------------------------------------------------

/** Lifecycle phase of a DCA ladder */
export type DcaPhase =
  | "awaiting_base"     // Entry signal fired, base order not yet filled
  | "ladder_active"     // Base filled, SOs pending
  | "completed"         // TP/SL hit or all SOs filled + TP hit → position closed
  | "cancelled";        // Ladder cancelled before completion

/** Runtime state for one DCA position (serializable to JSON) */
export interface DcaRuntimeState {
  /** Current lifecycle phase */
  phase: DcaPhase;
  /** The DCA config that generated this ladder */
  config: DcaConfig;
  /** Stop-loss percentage (frozen at entry time for recalculation) */
  stopLossPct: number;
  /** Position side */
  side: "long" | "short";
  /** Base entry price (set when base order fills) */
  baseEntryPrice: number;
  /** The full safety order schedule (generated from base entry price) */
  schedule: DcaSchedule | null;
  /** All fills applied so far */
  fills: DcaFill[];
  /** Current average entry price (VWAP across all fills) */
  avgEntryPrice: number;
  /** Current total quantity held */
  totalQty: number;
  /** Current total cost in USD */
  totalCostUsd: number;
  /** Current take-profit price (recalculated after each fill) */
  tpPrice: number;
  /** Current stop-loss price (recalculated after each fill) */
  slPrice: number;
  /** Number of safety orders filled so far */
  safetyOrdersFilled: number;
  /** Index of the next pending safety order (-1 if none remaining) */
  nextSoIndex: number;
  /** Timestamp of creation (epoch ms) */
  createdAt: number;
  /** Timestamp of last state transition (epoch ms) */
  updatedAt: number;
}

/** Result of a state transition — new state + description of what changed */
export interface DcaTransitionResult {
  state: DcaRuntimeState;
  /** Human-readable description of the transition for logging */
  description: string;
  /** Whether TP/SL levels changed (signals the worker to update exchange orders) */
  exitLevelsChanged: boolean;
}

// ---------------------------------------------------------------------------
// Initialization
// ---------------------------------------------------------------------------

/**
 * Create a new DCA runtime state in the "awaiting_base" phase.
 *
 * Called when an entry signal fires for a strategy with DCA config.
 * The base order has been submitted but not yet filled.
 *
 * @param config        DCA configuration from DSL
 * @param side          Position side
 * @param stopLossPct   SL percentage (frozen for the ladder lifetime)
 * @param now           Current timestamp (epoch ms)
 * @throws Error if config is invalid
 */
export function initDcaState(
  config: DcaConfig,
  side: "long" | "short",
  stopLossPct: number,
  now: number = Date.now(),
): DcaRuntimeState {
  const configErr = validateDcaConfig(config);
  if (configErr) throw new Error(`Cannot init DCA state: ${configErr}`);

  return {
    phase: "awaiting_base",
    config,
    stopLossPct,
    side,
    baseEntryPrice: 0,
    schedule: null,
    fills: [],
    avgEntryPrice: 0,
    totalQty: 0,
    totalCostUsd: 0,
    tpPrice: 0,
    slPrice: 0,
    safetyOrdersFilled: 0,
    nextSoIndex: 0,
    createdAt: now,
    updatedAt: now,
  };
}

// ---------------------------------------------------------------------------
// State transitions
// ---------------------------------------------------------------------------

/**
 * Apply the base order fill.
 *
 * Transitions: awaiting_base → ladder_active
 *
 * Generates the safety order schedule from the actual fill price,
 * computes initial TP/SL, and activates the ladder.
 *
 * Idempotent: if already in ladder_active with fills, returns current state unchanged.
 */
export function applyBaseFill(
  state: DcaRuntimeState,
  fillPrice: number,
  fillQty: number,
  now: number = Date.now(),
): DcaTransitionResult {
  if (state.phase !== "awaiting_base") {
    return {
      state,
      description: `No-op: base fill in phase "${state.phase}" (expected "awaiting_base")`,
      exitLevelsChanged: false,
    };
  }

  const fillSizeUsd = fillPrice * fillQty;
  const schedule = generateSafetyOrderSchedule(state.config, fillPrice, state.side);
  const tpPrice = recalcTakeProfit(fillPrice, state.config.takeProfitPct, state.side);
  const slPrice = recalcStopLoss(fillPrice, state.stopLossPct, state.side);

  const newState: DcaRuntimeState = {
    ...state,
    phase: "ladder_active",
    baseEntryPrice: fillPrice,
    schedule,
    fills: [{ price: fillPrice, qty: fillQty, sizeUsd: fillSizeUsd }],
    avgEntryPrice: fillPrice,
    totalQty: fillQty,
    totalCostUsd: fillSizeUsd,
    tpPrice,
    slPrice,
    safetyOrdersFilled: 0,
    nextSoIndex: schedule.safetyOrders.length > 0 ? 0 : -1,
    updatedAt: now,
  };

  return {
    state: newState,
    description: `Base fill at ${fillPrice}, qty=${fillQty}. Ladder active with ${schedule.safetyOrders.length} pending SOs. TP=${tpPrice.toFixed(2)}, SL=${slPrice.toFixed(2)}`,
    exitLevelsChanged: true,
  };
}

/**
 * Apply a safety order fill.
 *
 * Transitions: ladder_active → ladder_active (with updated state)
 *
 * Recalculates avg entry, TP, SL. Advances nextSoIndex.
 * If all SOs are filled, nextSoIndex becomes -1 (no more pending SOs).
 *
 * @param soIndex  The index of the safety order that was filled (0-based)
 */
export function applySafetyOrderFillRT(
  state: DcaRuntimeState,
  soIndex: number,
  fillPrice: number,
  fillQty: number,
  now: number = Date.now(),
): DcaTransitionResult {
  if (state.phase !== "ladder_active") {
    return {
      state,
      description: `No-op: SO fill in phase "${state.phase}" (expected "ladder_active")`,
      exitLevelsChanged: false,
    };
  }

  if (!state.schedule) {
    return {
      state,
      description: "No-op: SO fill but no schedule present",
      exitLevelsChanged: false,
    };
  }

  // Idempotent guard: don't re-apply an already-filled SO
  if (soIndex < state.nextSoIndex) {
    return {
      state,
      description: `No-op: SO ${soIndex} already filled (nextSoIndex=${state.nextSoIndex})`,
      exitLevelsChanged: false,
    };
  }

  // Sequential fill guard: reject out-of-order fills that would skip SOs.
  // SOs must fill in index order (0, 1, 2, ...). If the worker or reconciler
  // submits SO 2 while nextSoIndex is 0, something is wrong upstream.
  if (soIndex > state.nextSoIndex) {
    return {
      state,
      description: `No-op: SO ${soIndex} is out of order (expected nextSoIndex=${state.nextSoIndex}); SOs must fill sequentially`,
      exitLevelsChanged: false,
    };
  }

  const fillSizeUsd = fillPrice * fillQty;
  const newFills = [...state.fills, { price: fillPrice, qty: fillQty, sizeUsd: fillSizeUsd }];
  const newAvgEntry = calculateAvgEntry(newFills);
  const newTp = recalcTakeProfit(newAvgEntry, state.config.takeProfitPct, state.side);
  const newSl = recalcStopLoss(newAvgEntry, state.stopLossPct, state.side);
  const newSoFilled = state.safetyOrdersFilled + 1;

  const maxSO = state.schedule.safetyOrders.length;
  const newNextIndex = soIndex + 1 < maxSO ? soIndex + 1 : -1;

  const newState: DcaRuntimeState = {
    ...state,
    fills: newFills,
    avgEntryPrice: newAvgEntry,
    totalQty: state.totalQty + fillQty,
    totalCostUsd: state.totalCostUsd + fillSizeUsd,
    tpPrice: newTp,
    slPrice: newSl,
    safetyOrdersFilled: newSoFilled,
    nextSoIndex: newNextIndex,
    updatedAt: now,
  };

  return {
    state: newState,
    description: `SO ${soIndex} filled at ${fillPrice}, qty=${fillQty}. Avg entry=${newAvgEntry.toFixed(2)}, TP=${newTp.toFixed(2)}, SL=${newSl.toFixed(2)}. SOs filled: ${newSoFilled}/${maxSO}`,
    exitLevelsChanged: true,
  };
}

/**
 * Mark the DCA ladder as completed (position closed via TP/SL/manual).
 *
 * Transitions: ladder_active → completed
 */
export function completeDcaLadder(
  state: DcaRuntimeState,
  reason: string = "position_closed",
  now: number = Date.now(),
): DcaTransitionResult {
  // Only ladder_active can be completed — awaiting_base has no position to close,
  // and terminal states are already final.
  if (state.phase !== "ladder_active") {
    return {
      state,
      description: `No-op: cannot complete ladder in phase "${state.phase}" (requires "ladder_active")`,
      exitLevelsChanged: false,
    };
  }

  return {
    state: { ...state, phase: "completed", nextSoIndex: -1, updatedAt: now },
    description: `Ladder completed: ${reason}. ${state.safetyOrdersFilled} SOs filled, avg entry=${state.avgEntryPrice.toFixed(2)}`,
    exitLevelsChanged: false,
  };
}

/**
 * Cancel the DCA ladder (e.g., bot stopped, error, manual cancel).
 *
 * Transitions: any non-terminal → cancelled
 */
export function cancelDcaLadder(
  state: DcaRuntimeState,
  reason: string = "cancelled",
  now: number = Date.now(),
): DcaTransitionResult {
  if (state.phase === "completed" || state.phase === "cancelled") {
    return {
      state,
      description: `No-op: already in terminal phase "${state.phase}"`,
      exitLevelsChanged: false,
    };
  }

  return {
    state: { ...state, phase: "cancelled", nextSoIndex: -1, updatedAt: now },
    description: `Ladder cancelled: ${reason}. ${state.safetyOrdersFilled} SOs were filled`,
    exitLevelsChanged: false,
  };
}

// ---------------------------------------------------------------------------
// Safety order trigger evaluation
// ---------------------------------------------------------------------------

/**
 * Evaluate which pending safety orders are triggered at the current price.
 *
 * Returns the list of SO levels that should be filled, in order.
 * For long: triggered when currentPrice <= triggerPrice
 * For short: triggered when currentPrice >= triggerPrice
 *
 * Only returns SOs starting from nextSoIndex (sequential fill order).
 * Multiple SOs can trigger on a single price check if price moved fast.
 */
export function evaluateTriggeredSOs(
  state: DcaRuntimeState,
  currentPrice: number,
): SafetyOrderLevel[] {
  if (state.phase !== "ladder_active" || !state.schedule || state.nextSoIndex < 0) {
    return [];
  }

  const triggered: SafetyOrderLevel[] = [];
  const orders = state.schedule.safetyOrders;

  for (let i = state.nextSoIndex; i < orders.length; i++) {
    const so = orders[i];
    const isTriggered =
      state.side === "long"
        ? currentPrice <= so.triggerPrice
        : currentPrice >= so.triggerPrice;

    if (isTriggered) {
      triggered.push(so);
    } else {
      // SOs are ordered by deviation — if this one isn't triggered, none after will be
      break;
    }
  }

  return triggered;
}

// ---------------------------------------------------------------------------
// Query helpers
// ---------------------------------------------------------------------------

/** Get the next pending safety order level, or null if none remaining */
export function getNextPendingSO(state: DcaRuntimeState): SafetyOrderLevel | null {
  if (state.phase !== "ladder_active" || !state.schedule || state.nextSoIndex < 0) {
    return null;
  }
  return state.schedule.safetyOrders[state.nextSoIndex] ?? null;
}

/** Get remaining capital commitment (unfilled SOs) */
export function getRemainingExposure(state: DcaRuntimeState): number {
  if (!state.schedule || state.nextSoIndex < 0) return 0;
  let remaining = 0;
  for (let i = state.nextSoIndex; i < state.schedule.safetyOrders.length; i++) {
    remaining += state.schedule.safetyOrders[i].orderSizeUsd;
  }
  return remaining;
}

/** Get total exposure (filled + pending) */
export function getTotalExposure(state: DcaRuntimeState): number {
  return state.totalCostUsd + getRemainingExposure(state);
}

/** Check if the ladder is in a terminal state */
export function isTerminal(state: DcaRuntimeState): boolean {
  return state.phase === "completed" || state.phase === "cancelled";
}

// ---------------------------------------------------------------------------
// Serialization (for metaJson persistence)
// ---------------------------------------------------------------------------

/**
 * Serialize DCA runtime state to a plain JSON-safe object.
 * Suitable for storing in Position.metaJson or BotIntent.metaJson.
 */
export function serializeDcaState(state: DcaRuntimeState): Record<string, unknown> {
  return { ...state } as unknown as Record<string, unknown>;
}

/**
 * Deserialize DCA runtime state from a plain object (e.g., from metaJson).
 * Returns null if the object doesn't look like a valid DCA state.
 */
export function deserializeDcaState(obj: unknown): DcaRuntimeState | null {
  if (!obj || typeof obj !== "object") return null;
  const o = obj as Record<string, unknown>;

  // Structural validation: check all fields the engine accesses at runtime.
  // This runs on bot restart recovery — corrupted or outdated metaJson must
  // not crash the engine.
  const validPhases: DcaPhase[] = ["awaiting_base", "ladder_active", "completed", "cancelled"];
  if (typeof o.phase !== "string" || !validPhases.includes(o.phase as DcaPhase)) return null;
  if (!o.config || typeof o.config !== "object") return null;
  if (typeof o.side !== "string" || (o.side !== "long" && o.side !== "short")) return null;
  if (!Array.isArray(o.fills)) return null;
  if (typeof o.avgEntryPrice !== "number" || !Number.isFinite(o.avgEntryPrice)) return null;
  if (typeof o.totalQty !== "number" || !Number.isFinite(o.totalQty)) return null;
  if (typeof o.totalCostUsd !== "number" || !Number.isFinite(o.totalCostUsd)) return null;
  if (typeof o.tpPrice !== "number") return null;
  if (typeof o.slPrice !== "number") return null;
  if (typeof o.safetyOrdersFilled !== "number") return null;
  if (typeof o.nextSoIndex !== "number") return null;
  if (typeof o.stopLossPct !== "number") return null;
  if (typeof o.baseEntryPrice !== "number") return null;

  return o as unknown as DcaRuntimeState;
}
