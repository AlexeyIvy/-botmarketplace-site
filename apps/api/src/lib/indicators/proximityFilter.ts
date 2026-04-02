/**
 * Proximity Filter (#135)
 *
 * Signal gating based on distance to key price levels.
 * Returns true when price is "near" a reference level (within threshold).
 *
 * Used by MTF Confluence Scalper to gate entries near volume profile
 * levels (POC, VAH, VAL) or other support/resistance levels.
 *
 * Design:
 *   - Pure function, deterministic
 *   - Works with any pair of price series (e.g., close vs POC)
 *   - Threshold can be absolute or percentage-based
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ProximityMode = "absolute" | "percentage";

// ---------------------------------------------------------------------------
// Computation
// ---------------------------------------------------------------------------

/**
 * Compute proximity filter: true when price is within threshold of a level.
 *
 * @param prices      The price series to check (e.g., candle closes)
 * @param levels      The reference level series (e.g., POC from VolumeProfile)
 * @param threshold   Distance threshold
 * @param mode        "absolute" (fixed price distance) or "percentage" (% of level)
 * @returns Boolean series: true = price is near level, false = not near, null = insufficient data
 */
export function calcProximityFilter(
  prices: (number | null)[],
  levels: (number | null)[],
  threshold: number,
  mode: ProximityMode = "percentage",
): (boolean | null)[] {
  const n = Math.min(prices.length, levels.length);
  const result: (boolean | null)[] = new Array(n).fill(null);

  for (let i = 0; i < n; i++) {
    const price = prices[i];
    const level = levels[i];
    if (price === null || level === null || level === 0) {
      result[i] = null;
      continue;
    }

    const distance = Math.abs(price - level);
    if (mode === "absolute") {
      result[i] = distance <= threshold;
    } else {
      // percentage: threshold is % of the level price
      result[i] = (distance / level) * 100 <= threshold;
    }
  }

  return result;
}

/**
 * Compute directional proximity: near level AND approaching from a specific side.
 *
 * @param side  "above" = price is above the level, "below" = price is below
 * @returns Boolean series: true = near level from specified side
 */
export function calcDirectionalProximity(
  prices: (number | null)[],
  levels: (number | null)[],
  threshold: number,
  side: "above" | "below",
  mode: ProximityMode = "percentage",
): (boolean | null)[] {
  const proximity = calcProximityFilter(prices, levels, threshold, mode);
  const n = Math.min(prices.length, levels.length);
  const result: (boolean | null)[] = new Array(n).fill(null);

  for (let i = 0; i < n; i++) {
    if (proximity[i] === null || prices[i] === null || levels[i] === null) {
      result[i] = null;
      continue;
    }
    if (!proximity[i]) {
      result[i] = false;
      continue;
    }
    // Price is near — check direction
    result[i] = side === "above" ? prices[i]! >= levels[i]! : prices[i]! <= levels[i]!;
  }

  return result;
}
