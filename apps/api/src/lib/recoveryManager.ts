/**
 * Recovery Manager — ephemeral state reconstruction after worker restart (#130)
 *
 * When the bot worker process restarts, two pieces of in-memory state are lost:
 *
 *   1. TrailingStopState — high/low watermark and activation status for trailing stops
 *   2. lastTradeCloseTime — timestamp of last position close (used for cooldown)
 *
 * This module provides:
 *   - Pure functions to reconstruct these from persistent data (position + events)
 *   - A DB-backed helper to query the last close event timestamp
 *   - A single `reconstructRunState()` function that returns the full recovery payload
 *
 * Design:
 *   - Pure reconstruction logic: given a position snapshot, build trailing stop state
 *   - DB query is isolated to a single helper (testable via mock/stub)
 *   - No global state mutation — caller receives the reconstructed state and applies it
 *   - Idempotent: calling reconstruct multiple times produces identical results
 *   - Safe default: if no position exists, returns neutral state (no trailing, no cooldown)
 */

import { createTrailingStopState, type TrailingStopState } from "./exitEngine.js";
import type { PositionSnapshot } from "./positionManager.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/**
 * Reconstructed ephemeral state for a single bot run.
 *
 * This is the exact state that was lost when the worker restarted.
 * The caller should apply it to the in-memory maps (trailingStopStates, lastTradeCloseTimes).
 */
export interface ReconstructedRunState {
  /** Trailing stop state, or null if no open position */
  trailingStopState: TrailingStopState | null;
  /** Last trade close timestamp (ms), or 0 if no prior trade */
  lastTradeCloseTime: number;
  /** Whether an open position was found (for logging) */
  hasOpenPosition: boolean;
  /** Position ID if found (for logging) */
  positionId: string | null;
}

// ---------------------------------------------------------------------------
// Pure reconstruction — trailing stop state from position
// ---------------------------------------------------------------------------

/**
 * Reconstruct trailing stop state from a position snapshot.
 *
 * After restart, we lost the high/low watermark and activation status.
 * The safest reconstruction is:
 *   - Reset watermarks to position entry price
 *   - Mark trailing as NOT activated
 *
 * This is conservative: the trailing stop won't fire on the first tick after
 * restart unless price exceeds the activation threshold from entry price.
 * This matches the behavior of `createTrailingStopState()` used when a new
 * position is opened, ensuring no spurious trailing stop triggers.
 *
 * Trade-off: if price had already activated the trailing stop before restart,
 * we lose that activation. This means the trailing stop must re-activate
 * from the entry price level. This is safer than guessing where the watermark
 * was — it avoids premature exits on stale data.
 */
export function reconstructTrailingStopState(
  position: PositionSnapshot,
): TrailingStopState {
  return createTrailingStopState(position.avgEntryPrice);
}

// ---------------------------------------------------------------------------
// Pure reconstruction — resume entry context
// ---------------------------------------------------------------------------

/**
 * Given a position and signal engine state, determine if re-entering is safe.
 *
 * After restart:
 *   - If position is OPEN → no entry should fire (signal engine already handles this)
 *   - If position is null → entry is allowed (normal behavior)
 *
 * This function validates the invariant explicitly for defense-in-depth.
 *
 * Returns true if entry is safe (no open position), false if position exists.
 */
export function isEntryAllowedAfterResume(
  position: PositionSnapshot | null,
): boolean {
  if (!position) return true;
  return position.status !== "OPEN";
}

/**
 * Given existing pending/placed intents and a signal, check if the signal
 * would produce a duplicate intent.
 *
 * This mirrors the intentId-based dedup in botWorker.ts evaluateStrategies().
 * After restart, the same candle window might produce the same signal —
 * but the intent from before restart is already in the DB.
 *
 * Returns true if the intent already exists (duplicate), false if new.
 */
export function isDuplicateIntent(
  existingIntentIds: Set<string>,
  candidateIntentId: string,
): boolean {
  return existingIntentIds.has(candidateIntentId);
}

// ---------------------------------------------------------------------------
// Full reconstruction — combines all recovery for a single run
// ---------------------------------------------------------------------------

/**
 * Reconstruct all ephemeral state for a bot run after worker restart.
 *
 * This is the main entry point for recovery. It takes:
 *   - The active position (or null if none)
 *   - The last close event timestamp (or 0 if none)
 *
 * And returns a complete ReconstructedRunState that the caller can apply
 * to the in-memory worker maps.
 *
 * Pure function: no I/O, no side effects. DB queries should be done by the caller.
 */
export function reconstructRunState(
  position: PositionSnapshot | null,
  lastCloseEventTimestamp: number,
): ReconstructedRunState {
  if (!position || position.status !== "OPEN") {
    return {
      trailingStopState: null,
      lastTradeCloseTime: lastCloseEventTimestamp,
      hasOpenPosition: false,
      positionId: null,
    };
  }

  return {
    trailingStopState: reconstructTrailingStopState(position),
    lastTradeCloseTime: lastCloseEventTimestamp,
    hasOpenPosition: true,
    positionId: position.id,
  };
}
