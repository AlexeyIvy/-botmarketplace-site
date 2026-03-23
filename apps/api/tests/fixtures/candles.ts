/**
 * Shared candle fixtures for backtest and future strategy tests.
 *
 * Each candle: { openTime, open, high, low, close, volume }
 */

interface Candle {
  openTime: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

/** Generate N candles with a steady uptrend (close increases by `step` each bar). */
export function makeUptrend(n: number, startPrice = 100, step = 1): Candle[] {
  const candles: Candle[] = [];
  for (let i = 0; i < n; i++) {
    const close = startPrice + i * step;
    candles.push({
      openTime: 1_700_000_000_000 + i * 60_000,
      open: close - step * 0.3,
      high: close + step * 0.5,
      low: close - step * 0.5,
      close,
      volume: 1000 + i,
    });
  }
  return candles;
}

/** Generate N candles with a steady downtrend. */
export function makeDowntrend(n: number, startPrice = 200, step = 1): Candle[] {
  const candles: Candle[] = [];
  for (let i = 0; i < n; i++) {
    const close = startPrice - i * step;
    candles.push({
      openTime: 1_700_000_000_000 + i * 60_000,
      open: close + step * 0.3,
      high: close + step * 0.5,
      low: close - step * 0.5,
      close,
      volume: 1000 + i,
    });
  }
  return candles;
}

/** Generate N flat candles (close = startPrice every bar). */
export function makeFlat(n: number, startPrice = 100): Candle[] {
  const candles: Candle[] = [];
  for (let i = 0; i < n; i++) {
    candles.push({
      openTime: 1_700_000_000_000 + i * 60_000,
      open: startPrice,
      high: startPrice + 0.5,
      low: startPrice - 0.5,
      close: startPrice,
      volume: 1000,
    });
  }
  return candles;
}

/**
 * Generate N candles: flat start then strong uptrend.
 * This ensures SMA crossovers fire (fast SMA crosses above slow SMA).
 * @param n          Total candle count
 * @param flatBars   Number of initial flat bars (default: 25)
 * @param startPrice Starting price (default: 100)
 * @param trendStep  Price step per bar in trend phase (default: 2)
 */
export function makeFlatThenUp(n: number, flatBars = 25, startPrice = 100, trendStep = 2): Candle[] {
  const candles: Candle[] = [];
  for (let i = 0; i < n; i++) {
    const close = i < flatBars ? startPrice : startPrice + (i - flatBars) * trendStep;
    candles.push({
      openTime: 1_700_000_000_000 + i * 60_000,
      open: close - trendStep * 0.3,
      high: close + trendStep * 0.5,
      low: close - trendStep * 0.5,
      close,
      volume: 1000 + i,
    });
  }
  return candles;
}

/**
 * Generate N candles: flat start then strong downtrend.
 * This ensures SMA crossunders fire (fast SMA crosses below slow SMA).
 */
export function makeFlatThenDown(n: number, flatBars = 25, startPrice = 200, trendStep = 2): Candle[] {
  const candles: Candle[] = [];
  for (let i = 0; i < n; i++) {
    const close = i < flatBars ? startPrice : startPrice - (i - flatBars) * trendStep;
    candles.push({
      openTime: 1_700_000_000_000 + i * 60_000,
      open: close + trendStep * 0.3,
      high: close + trendStep * 0.5,
      low: close - trendStep * 0.5,
      close,
      volume: 1000 + i,
    });
  }
  return candles;
}

/**
 * Generate N candles with a strong, steady uptrend.
 *
 * Designed for Adaptive Regime Bot testing: produces high ADX (>25)
 * and bullish SuperTrend direction after indicator warm-up.
 *
 * Each bar has consistent directional movement:
 *   - High makes higher highs (step increase each bar)
 *   - Low makes higher lows
 *   - Range (high-low) stays proportional to step
 *
 * Deterministic: same inputs always produce identical candles.
 *
 * @param n          Total candle count (recommend ≥80 for ADX(14) warm-up)
 * @param startPrice Starting close price (default: 100)
 * @param step       Price increase per bar (default: 3)
 */
export function makeStrongUptrend(n: number, startPrice = 100, step = 3): Candle[] {
  const candles: Candle[] = [];
  for (let i = 0; i < n; i++) {
    const close = startPrice + i * step;
    candles.push({
      openTime: 1_700_000_000_000 + i * 60_000,
      open: close - step * 0.4,
      high: close + step * 0.6,
      low: close - step * 0.6,
      close,
      volume: 1000 + i * 10,
    });
  }
  return candles;
}

/**
 * Generate N candles with a strong, steady downtrend.
 *
 * Mirror of makeStrongUptrend for short-side testing.
 * Produces high ADX (>25) and bearish SuperTrend direction.
 *
 * @param n          Total candle count
 * @param startPrice Starting close price (default: 300)
 * @param step       Price decrease per bar (default: 3)
 */
export function makeStrongDowntrend(n: number, startPrice = 300, step = 3): Candle[] {
  const candles: Candle[] = [];
  for (let i = 0; i < n; i++) {
    const close = startPrice - i * step;
    candles.push({
      openTime: 1_700_000_000_000 + i * 60_000,
      open: close + step * 0.4,
      high: close + step * 0.6,
      low: close - step * 0.6,
      close,
      volume: 1000 + i * 10,
    });
  }
  return candles;
}

/**
 * Generate N candles in a range-bound (mean-reverting) market.
 *
 * Designed for Adaptive Regime Bot range-mode testing: produces low ADX (<20)
 * with price oscillating around a center price within a fixed band.
 *
 * The oscillation uses a sine wave with small random-free perturbation
 * to create realistic range-bound behavior:
 *   - Price swings between centerPrice ± amplitude
 *   - No directional trend → ADX stays low after warm-up
 *   - RSI oscillates between oversold and overbought zones
 *
 * Deterministic: same inputs always produce identical candles.
 *
 * @param n           Total candle count (recommend ≥80 for ADX warm-up)
 * @param centerPrice Center of the range (default: 100)
 * @param amplitude   Half-width of price oscillation (default: 5)
 * @param period      Oscillation period in bars (default: 20)
 */
export function makeRangeBound(
  n: number,
  centerPrice = 100,
  amplitude = 8,
  period = 20,
): Candle[] {
  // Produce oscillating price data with sharp multi-bar drops and recoveries.
  // This creates RSI extremes (oversold near 30, overbought near 70) while
  // keeping ADX low because price doesn't sustain direction.
  //
  // Pattern: alternate between sharp drops (6 bars down) and sharp rises (6 bars up),
  // with small drifts in between. The consecutive same-direction bars push RSI
  // toward extremes, while the reversals keep ADX low overall.
  const candles: Candle[] = [];
  const dropBars = 6;
  const riseBars = 6;
  const driftBars = period - dropBars - riseBars;
  const movePerBar = amplitude / Math.max(dropBars, riseBars);

  let price = centerPrice;

  for (let i = 0; i < n; i++) {
    const cyclePos = i % period;

    if (cyclePos < dropBars) {
      // Falling phase — consecutive down bars push RSI toward oversold
      price -= movePerBar;
    } else if (cyclePos < dropBars + riseBars) {
      // Rising phase — consecutive up bars push RSI toward overbought
      price += movePerBar;
    } else {
      // Drift phase — tiny random-free wobble
      price += (cyclePos % 2 === 0 ? 0.1 : -0.1);
    }

    // Clamp around center to prevent drift
    if (i > 0 && i % period === 0) {
      price = centerPrice;
    }

    const spread = movePerBar * 0.4;
    candles.push({
      openTime: 1_700_000_000_000 + i * 60_000,
      open: price + spread * 0.2,
      high: price + spread,
      low: price - spread,
      close: price,
      volume: 1000 + i,
    });
  }
  return candles;
}

/**
 * Generate N candles with a regime transition: range → trend.
 *
 * First half: range-bound oscillation (low ADX)
 * Second half: strong uptrend (high ADX)
 *
 * Designed for testing regime switching behavior:
 * the adaptive strategy should detect the transition and switch
 * from range-mode entries to trend-mode entries.
 *
 * Deterministic: same inputs produce identical candles.
 *
 * @param n           Total candle count (recommend ≥120 for both regimes to establish)
 * @param centerPrice Starting center price for range phase (default: 100)
 * @param trendStep   Price step per bar in trend phase (default: 3)
 */
export function makeRangeThenTrend(
  n: number,
  centerPrice = 100,
  trendStep = 3,
): Candle[] {
  const halfN = Math.floor(n / 2);
  const rangeCandles = makeRangeBound(halfN, centerPrice, 5, 20);

  // Start trend from the last range close
  const lastRangeClose = rangeCandles[rangeCandles.length - 1].close;
  const trendCandles: Candle[] = [];
  for (let i = 0; i < n - halfN; i++) {
    const close = lastRangeClose + i * trendStep;
    trendCandles.push({
      openTime: 1_700_000_000_000 + (halfN + i) * 60_000,
      open: close - trendStep * 0.4,
      high: close + trendStep * 0.6,
      low: close - trendStep * 0.6,
      close,
      volume: 1000 + (halfN + i) * 10,
    });
  }

  return [...rangeCandles, ...trendCandles];
}
