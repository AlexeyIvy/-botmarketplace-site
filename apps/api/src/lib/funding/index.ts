/**
 * Funding rate arbitrage data layer.
 *
 * Pure computation modules for basis spread, funding annualization,
 * and candidate scanning/ranking.
 */

export { computeBasisBps, buildSpreadSnapshot, annualizedBasisYieldPct } from "./basis.js";
export {
  annualizeFundingRate,
  averageFundingRate,
  fundingStreak,
  buildCandidate,
  scanFundingCandidates,
} from "./scanner.js";
export {
  parseFundingHistoryItem,
  parseFundingHistory,
  parseLinearTicker,
  buildSpreadFromTickers,
} from "./ingestion.js";
export type {
  BybitFundingHistoryItem,
  BybitLinearTicker,
  BybitSpotTicker,
} from "./ingestion.js";
export {
  shouldEnterHedge,
  planHedge,
  applySpotFill,
  applyPerpFill,
  applyFundingPayment,
  shouldExitHedge,
  beginClose,
  finalizeClose,
  computeHedgePnl,
} from "./hedgePlanner.js";
export type {
  HedgePosition,
  HedgeConfig,
  HedgeStatus,
  LegSide,
  LegExecution,
} from "./hedgeTypes.js";
export type { ExitReason } from "./hedgePlanner.js";
export type {
  FundingSnapshot,
  SpreadSnapshot,
  FundingCandidate,
  ScannerThresholds,
} from "./types.js";
