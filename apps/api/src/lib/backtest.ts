/**
 * Deterministic backtest engine (pure function, no I/O).
 *
 * Algorithm (price-breakout, 2:1 R/R):
 *   - Lookback N = 20 candles
 *   - Signal BUY: close[i] > max(close[i-N .. i-1])
 *   - Entry at close[i] price when no open position
 *   - SL  = effectiveEntry * (1 - riskPct / 100)
 *   - TP  = effectiveEntry * (1 + 2 * riskPct / 100)
 *   - Next candles: low ≤ SL → LOSS, high ≥ TP → WIN
 *   - End of data with open position → close at last close (NEUTRAL)
 *
 * Execution realism (Stage 19c):
 *   fillAt = "CLOSE" — fill at candle close price (only supported value)
 *   effectiveEntry = fillPrice * (1 + (feeBps + slippageBps) / 10_000)
 *     — fee on entry + slippage applied at entry only
 *   effectiveExit  = rawExit  * (1 - feeBps / 10_000)
 *     — fee on exit; slippage does NOT apply to exits
 *   SL/TP levels and pnlPct are all computed from effective prices.
 *   entryPrice/exitPrice in TradeRecord are effective (real economic cost/proceeds).
 */

import type { Candle } from "./bybitCandles.js";

export interface ExecOpts {
  feeBps: number;
  slippageBps: number;
  fillAt: "CLOSE";
}

const DEFAULT_EXEC_OPTS: ExecOpts = { feeBps: 0, slippageBps: 0, fillAt: "CLOSE" };

export interface TradeRecord {
  entryTime: number;
  exitTime: number;
  /** Effective entry price (after fee + slippage) */
  entryPrice: number;
  /** Effective exit price (after fee) */
  exitPrice: number;
  slPrice: number;
  tpPrice: number;
  outcome: "WIN" | "LOSS" | "NEUTRAL";
  pnlPct: number;
}

export interface BacktestReport {
  /** Number of completed trades */
  trades: number;
  /** Number of winning trades */
  wins: number;
  /** Win rate 0–1 */
  winrate: number;
  /** Sum of per-trade PnL % */
  totalPnlPct: number;
  /** Maximum drawdown % (peak-to-trough on cumulative PnL) */
  maxDrawdownPct: number;
  /** Candles processed */
  candles: number;
  tradeLog: TradeRecord[];
}

const LOOKBACK = 20;

export function runBacktest(
  candleData: Candle[],
  riskPct: number,
  opts: Partial<ExecOpts> = {},
): BacktestReport {
  const { feeBps, slippageBps } = { ...DEFAULT_EXEC_OPTS, ...opts };

  if (candleData.length < LOOKBACK + 1) {
    return {
      trades: 0, wins: 0, winrate: 0, totalPnlPct: 0, maxDrawdownPct: 0,
      candles: candleData.length, tradeLog: [],
    };
  }

  const tradeLog: TradeRecord[] = [];
  let inPosition = false;
  let effectiveEntry = 0;
  let entryTime = 0;
  let slPrice = 0;
  let tpPrice = 0;

  let cumulativePnl = 0;
  let peakPnl = 0;
  let maxDrawdownPct = 0;

  // Pre-compute multipliers
  const entryMult = 1 + (feeBps + slippageBps) / 10_000;
  const exitMult  = 1 - feeBps / 10_000;

  for (let i = LOOKBACK; i < candleData.length; i++) {
    const c = candleData[i];

    if (inPosition) {
      // Check SL first, then TP (conservative assumption: SL triggers before TP on the same candle)
      if (c.low <= slPrice) {
        const effectiveExit = slPrice * exitMult;
        const pnlPct = ((effectiveExit - effectiveEntry) / effectiveEntry) * 100;
        tradeLog.push({
          entryTime, exitTime: c.openTime, entryPrice: effectiveEntry, exitPrice: effectiveExit,
          slPrice, tpPrice, outcome: "LOSS", pnlPct,
        });
        cumulativePnl += pnlPct;
        if (cumulativePnl > peakPnl) peakPnl = cumulativePnl;
        const dd = peakPnl - cumulativePnl;
        if (dd > maxDrawdownPct) maxDrawdownPct = dd;
        inPosition = false;
      } else if (c.high >= tpPrice) {
        const effectiveExit = tpPrice * exitMult;
        const pnlPct = ((effectiveExit - effectiveEntry) / effectiveEntry) * 100;
        tradeLog.push({
          entryTime, exitTime: c.openTime, entryPrice: effectiveEntry, exitPrice: effectiveExit,
          slPrice, tpPrice, outcome: "WIN", pnlPct,
        });
        cumulativePnl += pnlPct;
        if (cumulativePnl > peakPnl) peakPnl = cumulativePnl;
        const dd = peakPnl - cumulativePnl;
        if (dd > maxDrawdownPct) maxDrawdownPct = dd;
        inPosition = false;
      }
      // else: still in position, continue
    } else {
      // Entry signal: close[i] > rolling max of previous LOOKBACK closes
      const rollingMax = Math.max(...candleData.slice(i - LOOKBACK, i).map((x) => x.close));
      if (c.close > rollingMax) {
        inPosition = true;
        effectiveEntry = c.close * entryMult;
        entryTime = c.openTime;
        // SL/TP anchored to effectiveEntry so fees/slippage affect risk levels
        slPrice = effectiveEntry * (1 - riskPct / 100);
        tpPrice = effectiveEntry * (1 + (2 * riskPct) / 100);
      }
    }
  }

  // Close open position at last candle's close
  if (inPosition) {
    const last = candleData[candleData.length - 1];
    const effectiveExit = last.close * exitMult;
    const pnlPct = ((effectiveExit - effectiveEntry) / effectiveEntry) * 100;
    tradeLog.push({
      entryTime, exitTime: last.openTime, entryPrice: effectiveEntry, exitPrice: effectiveExit,
      slPrice, tpPrice, outcome: "NEUTRAL", pnlPct,
    });
    cumulativePnl += pnlPct;
    if (cumulativePnl > peakPnl) peakPnl = cumulativePnl;
    const dd = peakPnl - cumulativePnl;
    if (dd > maxDrawdownPct) maxDrawdownPct = dd;
  }

  const trades = tradeLog.length;
  const wins = tradeLog.filter((t) => t.outcome === "WIN").length;
  const winrate = trades > 0 ? wins / trades : 0;
  const totalPnlPct = tradeLog.reduce((s, t) => s + t.pnlPct, 0);

  return {
    trades,
    wins,
    winrate: Math.round(winrate * 10000) / 10000,
    totalPnlPct: Math.round(totalPnlPct * 100) / 100,
    maxDrawdownPct: Math.round(maxDrawdownPct * 100) / 100,
    candles: candleData.length,
    tradeLog,
  };
}
