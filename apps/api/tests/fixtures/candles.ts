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
