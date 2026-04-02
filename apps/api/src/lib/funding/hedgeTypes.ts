/**
 * Shared types for the multi-leg hedge execution model.
 *
 * A hedge position consists of two legs:
 *   - Spot leg: buy the underlying asset
 *   - Perp leg: short the perpetual future
 *
 * The position earns funding payments (positive funding = shorts collect)
 * while maintaining delta-neutral exposure.
 */

/** Status of a hedge position. */
export type HedgeStatus = "PLANNED" | "OPENING" | "OPEN" | "CLOSING" | "CLOSED" | "FAILED";

/** Side of a leg execution. */
export type LegSide = "SPOT_BUY" | "PERP_SHORT" | "SPOT_SELL" | "PERP_CLOSE";

/** A single leg execution record. */
export interface LegExecution {
  side: LegSide;
  price: number;
  quantity: number;
  fee: number;
  timestamp: number;
}

/** A hedge position with two legs. */
export interface HedgePosition {
  symbol: string;
  status: HedgeStatus;
  /** Entry basis at position open (bps). */
  entryBasisBps: number;
  /** Spot buy leg (null if not yet executed). */
  spotLeg: LegExecution | null;
  /** Perp short leg (null if not yet executed). */
  perpLeg: LegExecution | null;
  /** Spot sell leg for closing (null if still open). */
  spotCloseLeg: LegExecution | null;
  /** Perp close leg for closing (null if still open). */
  perpCloseLeg: LegExecution | null;
  /** Accumulated funding payments collected (USD). */
  fundingCollected: number;
  /** When the position was opened (ms epoch). */
  openedAt: number;
  /** When the position was closed (ms epoch, 0 if open). */
  closedAt: number;
}

/** Configuration for hedge entry/exit decisions. */
export interface HedgeConfig {
  /** Minimum annualized yield (%) to enter. Default: 10. */
  minEntryYieldPct?: number;
  /** Maximum basis at entry (bps). Default: 30. */
  maxEntryBasisBps?: number;
  /** Exit if annualized yield drops below this (%). Default: 2. */
  exitYieldFloorPct?: number;
  /** Exit if basis widens beyond this (bps). Default: 100. */
  exitBasisCeilingBps?: number;
  /** Maximum position hold time (ms). Default: 7 days. */
  maxHoldMs?: number;
  /** Position size in USD. Default: 1000. */
  positionSizeUsd?: number;
}
