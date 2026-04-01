/**
 * Startup Recovery — pure assessment of restart recovery completeness (#141)
 *
 * After a worker restart, multiple recovery subsystems run in sequence:
 *   1. Position recovery: read active position from DB (recoveryManager)
 *   2. Ephemeral state reconstruction: trailing stop + cooldown (recoveryManager)
 *   3. Intent reconciliation: cancel stale, audit in-flight (stateReconciler)
 *
 * This module provides a pure assessment function that takes the outputs of
 * all recovery subsystems and produces a single StartupRecoveryReport.
 * The report documents:
 *   - What was recovered and whether it's consistent
 *   - Whether the runtime is safe to proceed with normal evaluation
 *   - What monitoring is needed for in-flight state
 *
 * The assessment is the "exchange-state recovery" for the platform's architecture:
 *   - Demo mode: local DB IS the exchange (position + intent state)
 *   - Live mode: local DB + exchange order reconciliation loop (reconcilePlacedIntents)
 *
 * In both modes, the startup recovery path reads persisted state (positions,
 * intents, events) and reconstructs a consistent runtime view before
 * allowing new signal evaluation.
 *
 * Pure function: no I/O, deterministic, idempotent.
 *
 * Stage 8, issue #141 — final slice: restart recovery + kill switch.
 */

import type { PositionSnapshot } from "./positionManager.js";
import type { ReconstructedRunState } from "./recoveryManager.js";
import type { StartupReconciliationResult } from "./stateReconciler.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** Aggregated startup recovery report for a single run. */
export interface StartupRecoveryReport {
  /** Whether recovery completed without errors */
  recoveryComplete: boolean;
  /** Whether runtime is safe to proceed with normal signal evaluation */
  safeToEvaluate: boolean;
  /** Position state after recovery */
  position: {
    found: boolean;
    id: string | null;
    side: string | null;
    currentQty: number;
    avgEntryPrice: number;
  };
  /** Ephemeral state reconstruction results */
  ephemeral: {
    trailingStopReconstructed: boolean;
    cooldownRecovered: boolean;
    lastTradeCloseTime: number;
  };
  /** Intent reconciliation results */
  intents: {
    staleCancelled: number;
    inFlightMonitored: number;
    inconsistenciesFound: number;
  };
  /** Human-readable summary */
  summary: string;
}

// ---------------------------------------------------------------------------
// Assessment
// ---------------------------------------------------------------------------

/**
 * Assess the completeness of startup recovery for a single run.
 *
 * Takes the outputs of the three recovery subsystems and produces
 * a unified report. The key invariant: if all three subsystems
 * completed and the intent reconciliation shows safe-to-evaluate,
 * then the runtime can proceed.
 *
 * Recovery scenarios:
 *   - Clean start (no position, no intents): safe, nothing to recover
 *   - Restart with open position: position recovered, trailing stop
 *     reconstructed from entry price, stale intents cancelled
 *   - Restart with in-flight orders: position + ephemeral recovered,
 *     in-flight intents monitored by exchange reconciliation loop
 *   - Restart after crash during intent creation: stale PENDING
 *     intents cancelled, signal engine re-evaluates fresh
 *
 * Pure function: no I/O, deterministic, idempotent.
 */
export function assessStartupRecovery(
  position: PositionSnapshot | null,
  recoveredState: ReconstructedRunState,
  reconciliation: StartupReconciliationResult,
): StartupRecoveryReport {
  const positionFound = position !== null && position.status === "OPEN";

  const report: StartupRecoveryReport = {
    recoveryComplete: true,
    safeToEvaluate: reconciliation.safeToEvaluate,
    position: {
      found: positionFound,
      id: positionFound ? position!.id : null,
      side: positionFound ? position!.side : null,
      currentQty: positionFound ? position!.currentQty : 0,
      avgEntryPrice: positionFound ? position!.avgEntryPrice : 0,
    },
    ephemeral: {
      trailingStopReconstructed: recoveredState.trailingStopState !== null,
      cooldownRecovered: recoveredState.lastTradeCloseTime > 0,
      lastTradeCloseTime: recoveredState.lastTradeCloseTime,
    },
    intents: {
      staleCancelled: reconciliation.toCancel.length,
      inFlightMonitored: reconciliation.toMonitor.length,
      inconsistenciesFound: 0,
    },
    summary: "",
  };

  // Consistency checks
  const issues: string[] = [];

  // Position-ephemeral consistency: if position exists, trailing stop should be reconstructed
  if (positionFound && !recoveredState.trailingStopState) {
    issues.push("open position found but trailing stop not reconstructed");
  }

  // Position-recovery consistency: recoveredState should agree with position
  if (positionFound !== recoveredState.hasOpenPosition) {
    issues.push("position presence mismatch between DB read and recovery manager");
  }

  report.intents.inconsistenciesFound = issues.length;

  // Build summary
  const parts: string[] = [];

  const hasCooldown = recoveredState.lastTradeCloseTime > 0;
  if (!positionFound && reconciliation.counts.total === 0 && !hasCooldown) {
    parts.push("clean startup — no position, no intents");
  } else {
    if (positionFound) {
      parts.push(`position recovered: ${position!.side} ${position!.currentQty} @ ${position!.avgEntryPrice}`);
    }
    if (recoveredState.trailingStopState) {
      parts.push("trailing stop reconstructed");
    }
    if (recoveredState.lastTradeCloseTime > 0) {
      parts.push("cooldown state recovered");
    }
    if (reconciliation.toCancel.length > 0) {
      parts.push(`${reconciliation.toCancel.length} stale intents cancelled`);
    }
    if (reconciliation.toMonitor.length > 0) {
      parts.push(`${reconciliation.toMonitor.length} in-flight intents monitored`);
    }
  }

  if (issues.length > 0) {
    parts.push(`${issues.length} consistency issue(s): ${issues.join("; ")}`);
    // Still safe to evaluate — issues are logged but don't block
    // Conservative: trailing stop defaults are safe (reset to entry price)
  }

  report.summary = parts.join("; ") || "startup recovery complete";

  return report;
}
