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
