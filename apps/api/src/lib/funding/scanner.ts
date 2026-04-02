/**
 * Funding rate scanner — ranks instruments by arbitrage attractiveness.
 *
 * Given a set of funding snapshots and spread snapshots per symbol,
 * computes annualized yield, streak strength, and average rate,
 * then filters and ranks candidates.
 *
 * Pure functions — no side effects, deterministic.
 */

import type { FundingSnapshot, SpreadSnapshot, FundingCandidate, ScannerThresholds } from "./types.js";

/** Number of funding periods per year on Bybit (every 8 hours). */
const FUNDING_PERIODS_PER_YEAR = 365 * 3;

/**
 * Annualize a per-period funding rate.
 *
 * Bybit settles funding every 8 hours (3x per day).
 * Annualized yield = rate * 365 * 3 * 100 (as percentage).
 *
 * @param rate  Funding rate as a decimal (e.g., 0.0001).
 * @returns Annualized yield as a percentage.
 */
export function annualizeFundingRate(rate: number): number {
  return rate * FUNDING_PERIODS_PER_YEAR * 100;
}

/**
 * Compute the average funding rate over a series of snapshots.
 *
 * @param snapshots  Funding snapshots for one symbol, any order.
 * @returns Average rate, or 0 if empty.
 */
export function averageFundingRate(snapshots: FundingSnapshot[]): number {
  if (snapshots.length === 0) return 0;
  const sum = snapshots.reduce((acc, s) => acc + s.fundingRate, 0);
  return sum / snapshots.length;
}

/**
 * Count the consecutive same-sign funding rate streak from the most
 * recent snapshot backward.
 *
 * A streak of 5 means the last 5 funding periods all had the same sign
 * (all positive or all negative). This indicates persistent funding direction.
 *
 * @param snapshots  Funding snapshots for one symbol, sorted by timestamp ascending.
 * @returns Streak count (minimum 1 if at least one snapshot, 0 if empty).
 */
export function fundingStreak(snapshots: FundingSnapshot[]): number {
  if (snapshots.length === 0) return 0;

  const last = snapshots[snapshots.length - 1];
  const sign = Math.sign(last.fundingRate);
  if (sign === 0) return 1; // zero rate is its own "streak" of 1

  let streak = 1;
  for (let i = snapshots.length - 2; i >= 0; i--) {
    if (Math.sign(snapshots[i].fundingRate) !== sign) break;
    streak++;
  }
  return streak;
}

/**
 * Build a FundingCandidate from raw data for one symbol.
 *
 * @param symbol     The trading pair symbol.
 * @param snapshots  Funding snapshots sorted by timestamp ascending.
 * @param spread     Most recent spread snapshot (or null if unavailable).
 * @returns Candidate with computed metrics.
 */
export function buildCandidate(
  symbol: string,
  snapshots: FundingSnapshot[],
  spread: SpreadSnapshot | null,
): FundingCandidate {
  const currentRate = snapshots.length > 0
    ? snapshots[snapshots.length - 1].fundingRate
    : 0;

  return {
    symbol,
    currentRate,
    annualizedYieldPct: annualizeFundingRate(currentRate),
    basisBps: spread?.basisBps ?? 0,
    streak: fundingStreak(snapshots),
    avgRate: averageFundingRate(snapshots),
  };
}

const DEFAULT_THRESHOLDS: Required<ScannerThresholds> = {
  minAnnualizedYieldPct: 5,
  maxBasisBps: 50,
  minStreak: 3,
  topN: 10,
};

/**
 * Scan and rank funding arbitrage candidates.
 *
 * @param symbolData  Map of symbol → { snapshots, spread }.
 * @param thresholds  Configurable filter thresholds.
 * @returns Ranked candidates (highest absolute yield first), limited to topN.
 */
export function scanFundingCandidates(
  symbolData: Map<string, { snapshots: FundingSnapshot[]; spread: SpreadSnapshot | null }>,
  thresholds: ScannerThresholds = {},
): FundingCandidate[] {
  const t = { ...DEFAULT_THRESHOLDS, ...thresholds };

  const candidates: FundingCandidate[] = [];

  for (const [symbol, { snapshots, spread }] of symbolData) {
    const candidate = buildCandidate(symbol, snapshots, spread);

    // Filter
    if (Math.abs(candidate.annualizedYieldPct) < t.minAnnualizedYieldPct) continue;
    if (Math.abs(candidate.basisBps) > t.maxBasisBps) continue;
    if (candidate.streak < t.minStreak) continue;

    candidates.push(candidate);
  }

  // Sort by absolute annualized yield descending
  candidates.sort((a, b) => Math.abs(b.annualizedYieldPct) - Math.abs(a.annualizedYieldPct));

  return candidates.slice(0, t.topN);
}
