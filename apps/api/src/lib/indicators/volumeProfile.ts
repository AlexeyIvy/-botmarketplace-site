/**
 * Volume Profile Indicator (#135)
 *
 * Computes volume distribution across price levels to identify:
 *   - POC (Point of Control): price level with highest volume
 *   - VAH (Value Area High): upper bound of the value area (70% of volume)
 *   - VAL (Value Area Low): lower bound of the value area
 *
 * Used by MTF Confluence Scalper to identify high-volume zones
 * where price is likely to find support/resistance.
 *
 * Design:
 *   - Pure function, deterministic
 *   - Configurable lookback period and bin count
 *   - Returns null arrays until enough data is available
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface VolumeProfileResult {
  /** Point of Control — price with highest traded volume */
  poc: (number | null)[];
  /** Value Area High — upper bound of 70% volume zone */
  vah: (number | null)[];
  /** Value Area Low — lower bound of 70% volume zone */
  val: (number | null)[];
}

export interface VolumeProfileCandle {
  high: number;
  low: number;
  close: number;
  volume: number;
}

// ---------------------------------------------------------------------------
// Computation
// ---------------------------------------------------------------------------

/**
 * Compute Volume Profile over a rolling window.
 *
 * For each bar, looks back `period` bars, distributes volume across
 * `bins` evenly-spaced price levels between the lookback's low and high,
 * then finds POC and value area.
 *
 * @param candles  OHLCV candle array
 * @param period   Lookback window in bars (default: 20)
 * @param bins     Number of price bins for volume distribution (default: 24)
 * @param valueAreaPct  Volume percentage for value area (default: 0.70 = 70%)
 */
export function calcVolumeProfile(
  candles: VolumeProfileCandle[],
  period: number = 20,
  bins: number = 24,
  valueAreaPct: number = 0.70,
): VolumeProfileResult {
  const n = candles.length;
  const poc: (number | null)[] = new Array(n).fill(null);
  const vah: (number | null)[] = new Array(n).fill(null);
  const val: (number | null)[] = new Array(n).fill(null);

  if (n < period || bins < 2) return { poc, vah, val };

  for (let i = period - 1; i < n; i++) {
    // Find price range over lookback window
    let rangeHigh = -Infinity;
    let rangeLow = Infinity;
    for (let j = i - period + 1; j <= i; j++) {
      if (candles[j].high > rangeHigh) rangeHigh = candles[j].high;
      if (candles[j].low < rangeLow) rangeLow = candles[j].low;
    }

    const rangeSpan = rangeHigh - rangeLow;
    if (rangeSpan <= 0) {
      // Flat market — POC = close, VAH = VAL = close
      poc[i] = candles[i].close;
      vah[i] = candles[i].close;
      val[i] = candles[i].close;
      continue;
    }

    // Distribute volume into bins
    const binSize = rangeSpan / bins;
    const volumeByBin = new Array<number>(bins).fill(0);

    for (let j = i - period + 1; j <= i; j++) {
      // Each candle's volume is distributed across the bins it covers
      const cLow = candles[j].low;
      const cHigh = candles[j].high;
      const cVol = candles[j].volume;

      const startBin = Math.max(0, Math.floor((cLow - rangeLow) / binSize));
      const endBin = Math.min(bins - 1, Math.floor((cHigh - rangeLow) / binSize));
      const coveredBins = endBin - startBin + 1;
      const volPerBin = coveredBins > 0 ? cVol / coveredBins : 0;

      for (let b = startBin; b <= endBin; b++) {
        volumeByBin[b] += volPerBin;
      }
    }

    // Find POC (bin with max volume)
    let maxVol = 0;
    let pocBin = 0;
    for (let b = 0; b < bins; b++) {
      if (volumeByBin[b] > maxVol) {
        maxVol = volumeByBin[b];
        pocBin = b;
      }
    }
    poc[i] = rangeLow + (pocBin + 0.5) * binSize;

    // Compute Value Area (70% of total volume, expanding from POC)
    const totalVolume = volumeByBin.reduce((s, v) => s + v, 0);
    const targetVolume = totalVolume * valueAreaPct;

    let vaVolume = volumeByBin[pocBin];
    let vaLow = pocBin;
    let vaHigh = pocBin;

    while (vaVolume < targetVolume && (vaLow > 0 || vaHigh < bins - 1)) {
      const belowVol = vaLow > 0 ? volumeByBin[vaLow - 1] : 0;
      const aboveVol = vaHigh < bins - 1 ? volumeByBin[vaHigh + 1] : 0;

      if (belowVol >= aboveVol && vaLow > 0) {
        vaLow--;
        vaVolume += volumeByBin[vaLow];
      } else if (vaHigh < bins - 1) {
        vaHigh++;
        vaVolume += volumeByBin[vaHigh];
      } else if (vaLow > 0) {
        vaLow--;
        vaVolume += volumeByBin[vaLow];
      } else {
        break;
      }
    }

    val[i] = rangeLow + vaLow * binSize;
    vah[i] = rangeLow + (vaHigh + 1) * binSize;
  }

  return { poc, vah, val };
}
