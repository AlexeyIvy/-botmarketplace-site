/**
 * Exchange order normalizer — safety gate before order submission.
 *
 * Validates and normalizes order parameters (qty, price) against
 * instrument rules. Rejects orders that cannot be made valid.
 *
 * This is NOT a rounding helper — it's a safety gate that ensures
 * every order sent to the exchange is valid per instrument constraints.
 *
 * Stage 3 — Issue #129
 */

import type { InstrumentInfo } from "./instrumentCache.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface NormalizeOrderInput {
  symbol: string;
  side: "Buy" | "Sell";
  orderType: "Market" | "Limit";
  /** Raw quantity (before normalization) */
  qty: number;
  /** Raw price (before normalization); required for Limit orders */
  price?: number;
}

export interface NormalizedOrder {
  symbol: string;
  side: "Buy" | "Sell";
  orderType: "Market" | "Limit";
  /** Exchange-valid quantity string */
  qty: string;
  /** Exchange-valid price string (only for Limit) */
  price?: string;
  /** Diagnostics about what was normalized */
  diagnostics: NormalizationDiagnostics;
}

export interface NormalizationDiagnostics {
  rawQty: number;
  normalizedQty: number;
  rawPrice?: number;
  normalizedPrice?: number;
  notionalUsd: number;
  appliedRules: string[];
}

export interface NormalizationError {
  valid: false;
  reason: string;
  details: Record<string, unknown>;
}

export type NormalizeResult =
  | { valid: true; order: NormalizedOrder }
  | NormalizationError;

// ---------------------------------------------------------------------------
// Main API
// ---------------------------------------------------------------------------

/**
 * Validate and normalize an order against instrument rules.
 *
 * Checks:
 * 1. Quantity ≥ minOrderQty
 * 2. Quantity ≤ maxOrderQty
 * 3. Quantity rounded to qtyStep
 * 4. Price rounded to tickSize (Limit orders)
 * 5. Notional (qty × price) ≥ minNotional
 * 6. Instrument is Trading
 *
 * Returns NormalizeResult: either a valid normalized order or an error.
 */
export function normalizeOrder(
  input: NormalizeOrderInput,
  instrument: InstrumentInfo,
): NormalizeResult {
  const rules: string[] = [];

  // Check instrument status
  if (instrument.status !== "Trading") {
    return {
      valid: false,
      reason: `Instrument ${input.symbol} is not trading (status: ${instrument.status})`,
      details: { symbol: input.symbol, status: instrument.status },
    };
  }

  // --- Normalize quantity ---
  let qty = input.qty;

  // Round to qtyStep
  if (instrument.qtyStep > 0) {
    const rawQty = qty;
    qty = roundToStep(qty, instrument.qtyStep);
    if (qty !== rawQty) {
      rules.push(`qty rounded ${rawQty} → ${qty} (step: ${instrument.qtyStep})`);
    }
  }

  // Check min qty
  if (qty < instrument.minOrderQty) {
    return {
      valid: false,
      reason: `Order quantity ${qty} is below minimum ${instrument.minOrderQty} for ${input.symbol}`,
      details: {
        symbol: input.symbol,
        qty,
        minOrderQty: instrument.minOrderQty,
        rawQty: input.qty,
      },
    };
  }

  // Check max qty
  if (qty > instrument.maxOrderQty) {
    return {
      valid: false,
      reason: `Order quantity ${qty} exceeds maximum ${instrument.maxOrderQty} for ${input.symbol}`,
      details: {
        symbol: input.symbol,
        qty,
        maxOrderQty: instrument.maxOrderQty,
      },
    };
  }

  // --- Normalize price (Limit orders) ---
  let normalizedPrice: number | undefined;

  if (input.orderType === "Limit") {
    if (input.price == null || input.price <= 0) {
      return {
        valid: false,
        reason: "Limit order requires a positive price",
        details: { price: input.price },
      };
    }

    normalizedPrice = input.price;
    if (instrument.tickSize > 0) {
      const rawPrice = normalizedPrice;
      normalizedPrice = roundToStep(normalizedPrice, instrument.tickSize);
      if (normalizedPrice !== rawPrice) {
        rules.push(`price rounded ${rawPrice} → ${normalizedPrice} (tick: ${instrument.tickSize})`);
      }
    }

    if (normalizedPrice <= 0) {
      return {
        valid: false,
        reason: `Price rounded to zero or negative (raw: ${input.price}, tick: ${instrument.tickSize})`,
        details: { rawPrice: input.price, tickSize: instrument.tickSize },
      };
    }
  }

  // --- Check min notional ---
  // For Market orders we can't know the exact fill price, so we use the provided
  // price hint or skip the check (exchange will enforce it).
  const referencePrice = normalizedPrice ?? input.price;
  if (referencePrice && instrument.minNotional > 0) {
    const notional = qty * referencePrice;
    if (notional < instrument.minNotional) {
      return {
        valid: false,
        reason: `Order notional $${notional.toFixed(2)} is below minimum $${instrument.minNotional} for ${input.symbol}`,
        details: {
          symbol: input.symbol,
          notional,
          minNotional: instrument.minNotional,
          qty,
          price: referencePrice,
        },
      };
    }
  }

  // --- Build result ---
  const notionalUsd = referencePrice ? qty * referencePrice : 0;
  const qtyDecimals = countDecimals(instrument.qtyStep);
  const qtyStr = qty.toFixed(qtyDecimals);

  const result: NormalizedOrder = {
    symbol: input.symbol,
    side: input.side,
    orderType: input.orderType,
    qty: qtyStr,
    diagnostics: {
      rawQty: input.qty,
      normalizedQty: qty,
      notionalUsd,
      appliedRules: rules,
    },
  };

  if (input.orderType === "Limit" && normalizedPrice != null) {
    const priceDecimals = countDecimals(instrument.tickSize);
    result.price = normalizedPrice.toFixed(priceDecimals);
    result.diagnostics.rawPrice = input.price;
    result.diagnostics.normalizedPrice = normalizedPrice;
  }

  return { valid: true, order: result };
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Round a value DOWN to the nearest step.
 * E.g. roundToStep(0.0025, 0.001) → 0.002
 */
export function roundToStep(value: number, step: number): number {
  if (step <= 0) return value;
  // Use integer math to avoid floating point issues
  const decimals = countDecimals(step);
  const factor = Math.pow(10, decimals);
  return Math.floor(value * factor / (step * factor)) * step;
}

/**
 * Count decimal places in a number.
 * E.g. countDecimals(0.001) → 3
 */
export function countDecimals(n: number): number {
  if (Math.floor(n) === n) return 0;
  const str = n.toString();
  const dotIndex = str.indexOf(".");
  if (dotIndex < 0) return 0;
  return str.length - dotIndex - 1;
}
