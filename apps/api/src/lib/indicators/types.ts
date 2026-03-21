/**
 * Shared types for the indicator engine.
 *
 * Candle shape mirrors the backtest/fixture format used throughout the project.
 */

export interface Candle {
  openTime: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}
