/**
 * Risk Manager — minimal sizing and eligibility layer (#128)
 *
 * Provides pragmatic runtime boundaries for:
 *   - Position sizing (how much to open)
 *   - Entry eligibility (cooldown, max open positions)
 *   - Position size validation
 *
 * Not a full risk framework — just enough to make runtime decisions safe.
 * Exchange-specific validation is deferred to #129.
 */

import { parseDsl, type ParsedDsl, type DslRisk } from "./dslEvaluator.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface SizingResult {
  /** Quantity to trade (in base asset units) */
  qty: number;
  /** USD notional value */
  notionalUsd: number;
  /** Whether the trade is eligible */
  eligible: boolean;
  /** Reason if not eligible */
  reason?: string;
}

export interface RiskContext {
  /** Compiled strategy DSL */
  dslJson: unknown;
  /** Current market price */
  currentPrice: number;
  /** Whether there's already an open position */
  hasOpenPosition: boolean;
  /** Timestamp of last trade close (ms since epoch, 0 if none) */
  lastTradeCloseTime: number;
  /** Current timestamp (ms since epoch) */
  now: number;
}

// ---------------------------------------------------------------------------
// Engine
// ---------------------------------------------------------------------------

/**
 * Compute position size and check entry eligibility.
 *
 * Sizing formula:
 *   notionalUsd = min(maxPositionSizeUsd, default 100)
 *   qty = notionalUsd / currentPrice
 *
 * Eligibility checks:
 *   - No open position (max 1 position enforced by DSL guards)
 *   - Cooldown period respected since last trade
 */
export function computeSizing(ctx: RiskContext): SizingResult {
  const parsed = parseDsl(ctx.dslJson);
  const risk = parsed.risk;

  // Check: already in position
  if (ctx.hasOpenPosition) {
    return { qty: 0, notionalUsd: 0, eligible: false, reason: "already in position" };
  }

  // Check: cooldown
  const cooldownMs = (risk.cooldownSeconds ?? 0) * 1000;
  if (cooldownMs > 0 && ctx.lastTradeCloseTime > 0) {
    const elapsed = ctx.now - ctx.lastTradeCloseTime;
    if (elapsed < cooldownMs) {
      const remaining = Math.ceil((cooldownMs - elapsed) / 1000);
      return {
        qty: 0,
        notionalUsd: 0,
        eligible: false,
        reason: `cooldown: ${remaining}s remaining`,
      };
    }
  }

  // Compute sizing
  const maxPositionUsd = risk.maxPositionSizeUsd ?? 100;
  const notionalUsd = maxPositionUsd;
  const qty = notionalUsd / ctx.currentPrice;

  return { qty, notionalUsd, eligible: true };
}

/**
 * Extract risk parameters from DSL for display/logging.
 */
export function extractRiskParams(dslJson: unknown): {
  riskPerTradePct: number;
  maxPositionSizeUsd: number;
  cooldownSeconds: number;
} {
  const parsed = parseDsl(dslJson);
  return {
    riskPerTradePct: parsed.risk.riskPerTradePct,
    maxPositionSizeUsd: parsed.risk.maxPositionSizeUsd ?? 100,
    cooldownSeconds: parsed.risk.cooldownSeconds ?? 0,
  };
}
