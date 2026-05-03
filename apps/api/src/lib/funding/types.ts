/**
 * Shared types for the funding rate / basis-trade data layer.
 *
 * All computation modules consume these types. Persistence models
 * (Prisma) are separate — these are the runtime-only shapes.
 */

/** A single funding rate observation for one symbol at one timestamp. */
export interface FundingSnapshot {
  symbol: string;
  /** Funding rate as a decimal (e.g., 0.0001 = 0.01%). */
  fundingRate: number;
  /** Next funding settlement time (ms epoch). */
  nextFundingAt: number;
  /** Observation timestamp (ms epoch). */
  timestamp: number;
}

/** A spot-vs-perp price snapshot for basis computation. */
export interface SpreadSnapshot {
  symbol: string;
  spotPrice: number;
  perpPrice: number;
  /** Basis in basis points: (perp - spot) / spot * 10_000. */
  basisBps: number;
  /** Observation timestamp (ms epoch). */
  timestamp: number;
}

/** A ranked funding arbitrage candidate from the scanner. */
export interface FundingCandidate {
  symbol: string;
  /** Current funding rate (decimal). */
  currentRate: number;
  /** Annualized funding yield as a percentage (e.g., 10.95 = 10.95%). */
  annualizedYieldPct: number;
  /** Current basis in basis points. */
  basisBps: number;
  /** Number of consecutive same-sign funding periods (streak strength). */
  streak: number;
  /** Average funding rate over the lookback window. */
  avgRate: number;
  /**
   * Next funding settlement time (ms epoch) from the most recent snapshot,
   * or null if the candidate has no snapshots. Same units as
   * `FundingSnapshot.nextFundingAt`; route layer serialises to ISO before
   * returning to clients.
   */
  nextFundingAt: number | null;
}

/** Thresholds for the scanner to filter candidates. */
export interface ScannerThresholds {
  /** Minimum absolute annualized yield (%) to qualify. Default: 5. */
  minAnnualizedYieldPct?: number;
  /** Maximum absolute basis (bps) to qualify. Default: 50. */
  maxBasisBps?: number;
  /** Minimum consecutive same-sign funding streak. Default: 3. */
  minStreak?: number;
  /** Number of top candidates to return. Default: 10. */
  topN?: number;
}
