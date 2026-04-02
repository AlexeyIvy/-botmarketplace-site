/**
 * Multi-leg hedge planner — pure state machine for funding arbitrage.
 *
 * Handles the lifecycle of a hedge position:
 *   PLANNED → OPENING → OPEN → CLOSING → CLOSED
 *                                        → FAILED (on partial fill or error)
 *
 * Entry decision: candidate meets yield + basis thresholds.
 * Exit decision: funding deteriorates, basis widens, or max hold exceeded.
 *
 * Pure functions — no side effects, no I/O, deterministic.
 */

import type {
  HedgePosition,
  HedgeConfig,
  HedgeStatus,
  LegExecution,
} from "./hedgeTypes.js";
import type { FundingCandidate } from "./types.js";
import { computeBasisBps } from "./basis.js";
import { annualizeFundingRate } from "./scanner.js";

const DEFAULT_CONFIG: Required<HedgeConfig> = {
  minEntryYieldPct: 10,
  maxEntryBasisBps: 30,
  exitYieldFloorPct: 2,
  exitBasisCeilingBps: 100,
  maxHoldMs: 7 * 24 * 60 * 60 * 1000, // 7 days
  positionSizeUsd: 1000,
};

/**
 * Evaluate whether a funding candidate qualifies for hedge entry.
 *
 * @returns true if the candidate passes all entry thresholds.
 */
export function shouldEnterHedge(
  candidate: FundingCandidate,
  config: HedgeConfig = {},
): boolean {
  const c = { ...DEFAULT_CONFIG, ...config };

  // Only enter when funding is positive (shorts collect) and yield is high enough
  if (candidate.annualizedYieldPct < c.minEntryYieldPct) return false;

  // Basis must be tight enough (low entry cost)
  if (Math.abs(candidate.basisBps) > c.maxEntryBasisBps) return false;

  // Need a consistent funding streak
  if (candidate.streak < 3) return false;

  return true;
}

/**
 * Create a new hedge position in PLANNED state.
 */
export function planHedge(
  symbol: string,
  entryBasisBps: number,
  timestamp: number,
): HedgePosition {
  return {
    symbol,
    status: "PLANNED",
    entryBasisBps,
    spotLeg: null,
    perpLeg: null,
    spotCloseLeg: null,
    perpCloseLeg: null,
    fundingCollected: 0,
    openedAt: timestamp,
    closedAt: 0,
  };
}

/**
 * Record a spot buy leg fill → transition to OPENING (one leg done).
 */
export function applySpotFill(
  position: HedgePosition,
  fill: LegExecution,
): HedgePosition {
  return {
    ...position,
    status: position.perpLeg ? "OPEN" : "OPENING",
    spotLeg: fill,
  };
}

/**
 * Record a perp short leg fill → transition to OPEN (both legs done).
 */
export function applyPerpFill(
  position: HedgePosition,
  fill: LegExecution,
): HedgePosition {
  return {
    ...position,
    status: position.spotLeg ? "OPEN" : "OPENING",
    perpLeg: fill,
  };
}

/**
 * Record a funding payment received while the hedge is open.
 */
export function applyFundingPayment(
  position: HedgePosition,
  paymentUsd: number,
): HedgePosition {
  return {
    ...position,
    fundingCollected: position.fundingCollected + paymentUsd,
  };
}

/** Exit reason for a hedge position. */
export type ExitReason =
  | "funding_deteriorated"
  | "basis_widened"
  | "max_hold_exceeded"
  | "manual";

/**
 * Evaluate whether an open hedge should exit.
 *
 * @param position     Current hedge position.
 * @param currentRate  Current funding rate (decimal).
 * @param spotPrice    Current spot price.
 * @param perpPrice    Current perp price.
 * @param now          Current time (ms epoch).
 * @param config       Hedge configuration.
 * @returns Exit reason if should exit, null if should stay.
 */
export function shouldExitHedge(
  position: HedgePosition,
  currentRate: number,
  spotPrice: number,
  perpPrice: number,
  now: number,
  config: HedgeConfig = {},
): ExitReason | null {
  if (position.status !== "OPEN") return null;

  const c = { ...DEFAULT_CONFIG, ...config };

  // Check funding deterioration
  const currentYield = annualizeFundingRate(currentRate);
  if (currentYield < c.exitYieldFloorPct) return "funding_deteriorated";

  // Check basis widening
  const currentBasis = Math.abs(computeBasisBps(spotPrice, perpPrice));
  if (currentBasis > c.exitBasisCeilingBps) return "basis_widened";

  // Check max hold time
  if (now - position.openedAt > c.maxHoldMs) return "max_hold_exceeded";

  return null;
}

/**
 * Transition a hedge position to CLOSING state.
 */
export function beginClose(
  position: HedgePosition,
  reason: ExitReason,
): HedgePosition {
  return {
    ...position,
    status: "CLOSING",
  };
}

/**
 * Apply close leg fills and finalize the hedge position.
 *
 * @returns Position in CLOSED state with both close legs recorded.
 */
export function finalizeClose(
  position: HedgePosition,
  spotSellFill: LegExecution,
  perpCloseFill: LegExecution,
  closedAt: number,
): HedgePosition {
  return {
    ...position,
    status: "CLOSED",
    spotCloseLeg: spotSellFill,
    perpCloseLeg: perpCloseFill,
    closedAt,
  };
}

/**
 * Compute realized P&L for a closed hedge position.
 *
 * P&L = funding collected + spot P&L + perp P&L - total fees
 *
 * Spot P&L = (sellPrice - buyPrice) * quantity
 * Perp P&L = (shortPrice - closePrice) * quantity  (short → profit when price drops)
 */
export function computeHedgePnl(position: HedgePosition): number {
  if (position.status !== "CLOSED") return 0;
  if (!position.spotLeg || !position.perpLeg || !position.spotCloseLeg || !position.perpCloseLeg) return 0;

  const spotPnl = (position.spotCloseLeg.price - position.spotLeg.price) * position.spotLeg.quantity;
  const perpPnl = (position.perpLeg.price - position.perpCloseLeg.price) * position.perpLeg.quantity;
  const totalFees = position.spotLeg.fee + position.perpLeg.fee +
    position.spotCloseLeg.fee + position.perpCloseLeg.fee;

  return position.fundingCollected + spotPnl + perpPnl - totalFees;
}
