/**
 * Safety Guards — pure decision functions for runtime circuit breakers (#141)
 *
 * Two guards:
 *   1. Daily loss limit: stops a run when estimated daily loss exceeds threshold
 *   2. Pause on error: stops a run after consecutive failed intents
 *
 * All functions are pure — no DB, no I/O, deterministic.
 * The botWorker queries state and feeds it to these functions for decisions.
 */

// ---------------------------------------------------------------------------
// DSL config parsers
// ---------------------------------------------------------------------------

export interface DailyLossConfig {
  dailyLossLimitUsd: number | null;
  riskPerTradePct: number;
  maxPositionSizeUsd: number;
}

export interface GuardsConfig {
  pauseOnError: boolean;
}

/**
 * Parse daily-loss-related fields from DSL risk section.
 * Returns safe defaults when fields are missing or wrong type.
 */
export function parseDailyLossConfig(dslJson: unknown): DailyLossConfig {
  const dsl = dslJson as Record<string, unknown> | null;
  const risk = (dsl && typeof dsl === "object" ? dsl["risk"] : undefined) as
    | Record<string, unknown>
    | undefined;

  const dailyLossLimitUsd =
    typeof risk?.["dailyLossLimitUsd"] === "number" && risk["dailyLossLimitUsd"] > 0
      ? (risk["dailyLossLimitUsd"] as number)
      : null;

  const riskPerTradePct =
    typeof risk?.["riskPerTradePct"] === "number" ? (risk["riskPerTradePct"] as number) : 1;

  const maxPositionSizeUsd =
    typeof risk?.["maxPositionSizeUsd"] === "number" ? (risk["maxPositionSizeUsd"] as number) : 100;

  return { dailyLossLimitUsd, riskPerTradePct, maxPositionSizeUsd };
}

/**
 * Parse guards section from DSL.
 * `pauseOnError` defaults to true (same as graphCompiler default).
 */
export function parseGuardsConfig(dslJson: unknown): GuardsConfig {
  const dsl = dslJson as Record<string, unknown> | null;
  const guards = (dsl && typeof dsl === "object" ? dsl["guards"] : undefined) as
    | Record<string, unknown>
    | undefined;

  return {
    pauseOnError: guards?.["pauseOnError"] !== false,
  };
}

// ---------------------------------------------------------------------------
// Daily loss limit
// ---------------------------------------------------------------------------

export interface DailyLossResult {
  triggered: boolean;
  estimatedLoss: number;
  estimatedLossPerTrade: number;
  reason: string;
}

/**
 * Decide whether the daily loss limit has been breached.
 *
 * Heuristic: failedIntentCount × (riskPerTradePct% × maxPositionSizeUsd) ≥ dailyLossLimitUsd
 *
 * Returns triggered=false when:
 *   - dailyLossLimitUsd is null/zero (no limit configured)
 *   - estimated loss is below the limit
 *
 * Deterministic: same inputs always produce the same output.
 */
export function shouldTriggerDailyLossLimit(
  config: DailyLossConfig,
  failedIntentCount: number,
): DailyLossResult {
  if (config.dailyLossLimitUsd === null || config.dailyLossLimitUsd <= 0) {
    return {
      triggered: false,
      estimatedLoss: 0,
      estimatedLossPerTrade: 0,
      reason: "no daily loss limit configured",
    };
  }

  const estimatedLossPerTrade = (config.riskPerTradePct / 100) * config.maxPositionSizeUsd;
  const estimatedLoss = failedIntentCount * estimatedLossPerTrade;

  if (estimatedLoss >= config.dailyLossLimitUsd) {
    return {
      triggered: true,
      estimatedLoss,
      estimatedLossPerTrade,
      reason: `estimated loss $${estimatedLoss.toFixed(2)} >= limit $${config.dailyLossLimitUsd} (${failedIntentCount} failed × $${estimatedLossPerTrade.toFixed(2)}/trade)`,
    };
  }

  return {
    triggered: false,
    estimatedLoss,
    estimatedLossPerTrade,
    reason: `estimated loss $${estimatedLoss.toFixed(2)} < limit $${config.dailyLossLimitUsd}`,
  };
}

// ---------------------------------------------------------------------------
// Pause on error
// ---------------------------------------------------------------------------

/** Default: pause after 3 consecutive failures. */
export const DEFAULT_ERROR_PAUSE_THRESHOLD = 3;

export interface PauseOnErrorResult {
  triggered: boolean;
  consecutiveFailures: number;
  threshold: number;
  reason: string;
}

/**
 * Decide whether to pause a run due to consecutive intent failures.
 *
 * When `pauseOnError` is true and the most recent N intents are all FAILED,
 * the run should be stopped to prevent further damage.
 *
 * @param pauseOnError  Whether the guard is active (from DSL guards section)
 * @param consecutiveFailedIntents  Count of most-recent consecutive FAILED intents
 * @param threshold  How many consecutive failures trigger the pause (default: 3)
 */
export function shouldPauseOnError(
  pauseOnError: boolean,
  consecutiveFailedIntents: number,
  threshold: number = DEFAULT_ERROR_PAUSE_THRESHOLD,
): PauseOnErrorResult {
  if (!pauseOnError) {
    return {
      triggered: false,
      consecutiveFailures: consecutiveFailedIntents,
      threshold,
      reason: "pauseOnError disabled in guards",
    };
  }

  if (consecutiveFailedIntents >= threshold) {
    return {
      triggered: true,
      consecutiveFailures: consecutiveFailedIntents,
      threshold,
      reason: `${consecutiveFailedIntents} consecutive failed intents >= threshold ${threshold}`,
    };
  }

  return {
    triggered: false,
    consecutiveFailures: consecutiveFailedIntents,
    threshold,
    reason: `${consecutiveFailedIntents} consecutive failures < threshold ${threshold}`,
  };
}
