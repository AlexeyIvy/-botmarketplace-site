/**
 * Position Sizer — converts USD notional to exchange-valid quantity.
 *
 * Takes the output of riskManager.computeSizing() (which produces a raw qty)
 * and normalizes it through instrument rules to produce an exchange-valid
 * quantity that can be submitted to the order API.
 *
 * Stage 3 — Issue #129
 */

import type { InstrumentInfo } from "../exchange/instrumentCache.js";
import { roundToStep } from "../exchange/normalizer.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface SizeOrderInput {
  /** USD notional to allocate */
  notionalUsd: number;
  /** Current market price of the instrument */
  currentPrice: number;
  /** Leverage multiplier (1 = no leverage) */
  leverage: number;
}

export interface SizeOrderResult {
  /** Whether a valid order can be placed */
  valid: boolean;
  /** Exchange-valid quantity (0 if invalid) */
  qty: number;
  /** Actual USD notional after qty normalization */
  effectiveNotionalUsd: number;
  /** Human-readable reason if invalid */
  reason?: string;
}

// ---------------------------------------------------------------------------
// Main API
// ---------------------------------------------------------------------------

/**
 * Convert a USD notional into an exchange-valid quantity.
 *
 * Formula:
 *   rawQty = (notionalUsd × leverage) / currentPrice
 *   qty = roundToStep(rawQty, instrument.qtyStep)
 *
 * Validation:
 *   - qty ≥ instrument.minOrderQty
 *   - qty ≤ instrument.maxOrderQty
 *   - effective notional ≥ instrument.minNotional
 */
export function sizeOrder(
  input: SizeOrderInput,
  instrument: InstrumentInfo,
): SizeOrderResult {
  if (input.currentPrice <= 0) {
    return { valid: false, qty: 0, effectiveNotionalUsd: 0, reason: "currentPrice must be positive" };
  }
  if (input.notionalUsd <= 0) {
    return { valid: false, qty: 0, effectiveNotionalUsd: 0, reason: "notionalUsd must be positive" };
  }

  const leverage = Math.max(1, Math.min(input.leverage, instrument.maxLeverage));

  // Raw qty before normalization
  const rawQty = (input.notionalUsd * leverage) / input.currentPrice;

  // Round down to qty step
  const qty = roundToStep(rawQty, instrument.qtyStep);

  if (qty <= 0) {
    return {
      valid: false,
      qty: 0,
      effectiveNotionalUsd: 0,
      reason: `Quantity rounds to zero (raw: ${rawQty}, step: ${instrument.qtyStep})`,
    };
  }

  // Check min order qty
  if (qty < instrument.minOrderQty) {
    return {
      valid: false,
      qty: 0,
      effectiveNotionalUsd: 0,
      reason: `Quantity ${qty} below minimum ${instrument.minOrderQty} for ${instrument.symbol}`,
    };
  }

  // Check max order qty
  if (qty > instrument.maxOrderQty) {
    return {
      valid: false,
      qty: 0,
      effectiveNotionalUsd: 0,
      reason: `Quantity ${qty} exceeds maximum ${instrument.maxOrderQty} for ${instrument.symbol}`,
    };
  }

  // Effective notional after rounding
  const effectiveNotionalUsd = (qty * input.currentPrice) / leverage;

  // Check min notional
  if (instrument.minNotional > 0) {
    const orderNotional = qty * input.currentPrice;
    if (orderNotional < instrument.minNotional) {
      return {
        valid: false,
        qty: 0,
        effectiveNotionalUsd: 0,
        reason: `Notional $${orderNotional.toFixed(2)} below minimum $${instrument.minNotional} for ${instrument.symbol}`,
      };
    }
  }

  return { valid: true, qty, effectiveNotionalUsd };
}
