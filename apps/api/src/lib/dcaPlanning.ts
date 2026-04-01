/**
 * DCA Planning Primitives (#131)
 *
 * Pure, deterministic functions for Dollar-Cost Averaging (DCA) planning:
 *   - Safety order schedule generation (price levels + quantities)
 *   - Average entry (VWAP) calculation across multiple fills
 *   - Take-profit recalculation from averaged entry
 *   - Maximum capital / exposure bound calculation
 *
 * These are planning-only primitives — no runtime execution, no I/O.
 * They power backtest DCA simulation and future runtime scheduling.
 *
 * Terminology:
 *   - Base order: the initial entry order
 *   - Safety order (SO): subsequent ladder orders placed below (long) / above (short) entry
 *   - Step: price deviation from base entry for each SO level
 *   - Volume scale: geometric multiplier on SO quantity
 *   - Step scale: geometric multiplier on price deviation between SOs
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface DcaConfig {
  /** Base order size in USD */
  baseOrderSizeUsd: number;
  /** Maximum number of safety orders */
  maxSafetyOrders: number;
  /** Price deviation step for the first safety order (percent, e.g. 1.2 = 1.2%) */
  priceStepPct: number;
  /** Multiplier applied to price step for each subsequent SO (geometric, ≥1) */
  stepScale: number;
  /** Multiplier applied to SO volume for each subsequent SO (geometric, ≥1) */
  volumeScale: number;
  /** Take-profit as percent from average entry price (e.g. 1.5 = 1.5%) */
  takeProfitPct: number;
}

export interface SafetyOrderLevel {
  /** 0-indexed safety order number (0 = first SO, not base order) */
  index: number;
  /** Price deviation from base entry as a percentage */
  deviationPct: number;
  /** Absolute trigger price for this SO */
  triggerPrice: number;
  /** Order size in USD for this SO */
  orderSizeUsd: number;
  /** Order quantity (orderSizeUsd / triggerPrice) */
  qty: number;
}

export interface DcaSchedule {
  /** Base entry price */
  baseEntryPrice: number;
  /** Base order quantity */
  baseQty: number;
  /** Base order size in USD */
  baseOrderSizeUsd: number;
  /** All safety order levels */
  safetyOrders: SafetyOrderLevel[];
  /** Total capital required if all SOs fill (base + all SOs) */
  totalCapitalUsd: number;
  /** Worst-case average entry if all SOs fill */
  worstCaseAvgEntry: number;
  /** TP price at worst-case average entry */
  worstCaseTpPrice: number;
}

export interface DcaFill {
  price: number;
  qty: number;
  sizeUsd: number;
}

export interface DcaPositionState {
  /** All fills so far (base + safety orders) */
  fills: DcaFill[];
  /** Total quantity held */
  totalQty: number;
  /** Volume-weighted average entry price */
  avgEntryPrice: number;
  /** Total cost basis in USD */
  totalCostUsd: number;
  /** Current take-profit price */
  tpPrice: number;
  /** Number of safety orders filled (0 = only base order) */
  safetyOrdersFilled: number;
  /** Side of the position */
  side: "long" | "short";
}

// ---------------------------------------------------------------------------
// Safety order schedule generation
// ---------------------------------------------------------------------------

/**
 * Generate the full safety order schedule for a DCA ladder.
 *
 * Each SO level's deviation compounds geometrically:
 *   SO[0] deviation = priceStepPct
 *   SO[n] deviation = SO[n-1] deviation + priceStepPct * stepScale^n
 *
 * Each SO level's volume compounds geometrically:
 *   SO[0] size = baseOrderSizeUsd * volumeScale
 *   SO[n] size = SO[n-1] size * volumeScale
 *
 * @param config  DCA configuration
 * @param baseEntryPrice  The base entry price
 * @param side    Position side ("long" = SOs below entry, "short" = SOs above)
 */
export function generateSafetyOrderSchedule(
  config: DcaConfig,
  baseEntryPrice: number,
  side: "long" | "short",
): DcaSchedule {
  const safetyOrders: SafetyOrderLevel[] = [];

  const baseQty = config.baseOrderSizeUsd / baseEntryPrice;
  let cumulativeDeviation = 0;
  let currentStepPct = config.priceStepPct;
  let currentSizeUsd = config.baseOrderSizeUsd * config.volumeScale;

  let totalCostUsd = config.baseOrderSizeUsd;
  let totalQty = baseQty;

  for (let i = 0; i < config.maxSafetyOrders; i++) {
    cumulativeDeviation += currentStepPct;

    const triggerPrice =
      side === "long"
        ? baseEntryPrice * (1 - cumulativeDeviation / 100)
        : baseEntryPrice * (1 + cumulativeDeviation / 100);

    const qty = currentSizeUsd / triggerPrice;

    safetyOrders.push({
      index: i,
      deviationPct: cumulativeDeviation,
      triggerPrice,
      orderSizeUsd: currentSizeUsd,
      qty,
    });

    totalCostUsd += currentSizeUsd;
    totalQty += qty;

    // Scale for next level
    currentStepPct *= config.stepScale;
    currentSizeUsd *= config.volumeScale;
  }

  const worstCaseAvgEntry = totalCostUsd / totalQty;
  const worstCaseTpPrice =
    side === "long"
      ? worstCaseAvgEntry * (1 + config.takeProfitPct / 100)
      : worstCaseAvgEntry * (1 - config.takeProfitPct / 100);

  return {
    baseEntryPrice,
    baseQty,
    baseOrderSizeUsd: config.baseOrderSizeUsd,
    safetyOrders,
    totalCapitalUsd: totalCostUsd,
    worstCaseAvgEntry,
    worstCaseTpPrice,
  };
}

// ---------------------------------------------------------------------------
// Average entry calculation
// ---------------------------------------------------------------------------

/**
 * Calculate the volume-weighted average entry price across fills.
 *
 * VWAP = sum(price_i * qty_i) / sum(qty_i)
 *
 * Pure function: no side effects.
 */
export function calculateAvgEntry(fills: DcaFill[]): number {
  if (fills.length === 0) return 0;
  let totalCost = 0;
  let totalQty = 0;
  for (const f of fills) {
    totalCost += f.price * f.qty;
    totalQty += f.qty;
  }
  if (totalQty === 0) return 0;
  return totalCost / totalQty;
}

// ---------------------------------------------------------------------------
// TP recalculation
// ---------------------------------------------------------------------------

/**
 * Recalculate take-profit price from the current average entry.
 *
 * For long: TP = avgEntry * (1 + takeProfitPct / 100)
 * For short: TP = avgEntry * (1 - takeProfitPct / 100)
 */
export function recalcTakeProfit(
  avgEntryPrice: number,
  takeProfitPct: number,
  side: "long" | "short",
): number {
  return side === "long"
    ? avgEntryPrice * (1 + takeProfitPct / 100)
    : avgEntryPrice * (1 - takeProfitPct / 100);
}

// ---------------------------------------------------------------------------
// Exposure bound
// ---------------------------------------------------------------------------

/**
 * Calculate maximum capital exposure for a DCA configuration.
 *
 * This is the total USD committed if the base order and all safety orders fill.
 * Used for risk validation: totalCapital must not exceed maxPositionSizeUsd.
 */
export function calculateMaxExposure(config: DcaConfig): number {
  let total = config.baseOrderSizeUsd;
  let currentSizeUsd = config.baseOrderSizeUsd * config.volumeScale;
  for (let i = 0; i < config.maxSafetyOrders; i++) {
    total += currentSizeUsd;
    currentSizeUsd *= config.volumeScale;
  }
  return total;
}

// ---------------------------------------------------------------------------
// Position state management (pure, for backtest)
// ---------------------------------------------------------------------------

/**
 * Create initial DCA position state from a base fill.
 */
export function openDcaPosition(
  basePrice: number,
  baseQty: number,
  baseSizeUsd: number,
  takeProfitPct: number,
  side: "long" | "short",
): DcaPositionState {
  const tpPrice = recalcTakeProfit(basePrice, takeProfitPct, side);
  return {
    fills: [{ price: basePrice, qty: baseQty, sizeUsd: baseSizeUsd }],
    totalQty: baseQty,
    avgEntryPrice: basePrice,
    totalCostUsd: baseSizeUsd,
    tpPrice,
    safetyOrdersFilled: 0,
    side,
  };
}

/**
 * Apply a safety order fill to an existing DCA position.
 *
 * Recalculates average entry and TP. Returns a new state (immutable).
 */
export function applySafetyOrderFill(
  state: DcaPositionState,
  fillPrice: number,
  fillQty: number,
  fillSizeUsd: number,
  takeProfitPct: number,
): DcaPositionState {
  const newFills = [...state.fills, { price: fillPrice, qty: fillQty, sizeUsd: fillSizeUsd }];
  const newTotalQty = state.totalQty + fillQty;
  const newTotalCost = state.totalCostUsd + fillSizeUsd;
  const newAvgEntry = calculateAvgEntry(newFills);
  const newTp = recalcTakeProfit(newAvgEntry, takeProfitPct, state.side);

  return {
    fills: newFills,
    totalQty: newTotalQty,
    avgEntryPrice: newAvgEntry,
    totalCostUsd: newTotalCost,
    tpPrice: newTp,
    safetyOrdersFilled: state.safetyOrdersFilled + 1,
    side: state.side,
  };
}
