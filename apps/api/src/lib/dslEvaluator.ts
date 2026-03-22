/**
 * DSL-Driven Backtest Evaluator (#126)
 *
 * Evaluates compiled Strategy DSL against candle data to produce backtest results.
 * Replaces the old hardcoded price-breakout algorithm with a generic evaluator
 * that reads entry conditions, exit rules, and trade direction from the DSL.
 *
 * Supports:
 *   - DSL v2 entry.sideCondition (dynamic long/short per bar)
 *   - DSL v1/v2 fixed entry.side
 *   - Fixed SL/TP exits (fixed_pct, atr_multiple)
 *   - Indicator-based exits (indicatorExit)
 *   - Time-based exits (timeExit.maxBarsInPosition)
 *   - Trailing stop exits (trailing_pct)
 *   - Deterministic bar-by-bar evaluation
 *
 * Design:
 *   - Pure function: no I/O, no side effects
 *   - Indicator values are pre-computed once for the full candle array
 *   - Entry/exit checks are evaluated per bar from the DSL specification
 *   - Position accounting supports both long and short within one evaluation
 */

import type { Candle } from "./bybitCandles.js";
import { calcATR } from "./indicators/atr.js";
import { calcADX } from "./indicators/adx.js";
import { calcSuperTrend } from "./indicators/supertrend.js";
import { calcVWAP } from "./indicators/vwap.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type TradeSide = "long" | "short";

export interface DslTradeRecord {
  entryTime: number;
  exitTime: number;
  side: TradeSide;
  entryPrice: number;
  exitPrice: number;
  slPrice: number;
  tpPrice: number;
  outcome: "WIN" | "LOSS" | "NEUTRAL";
  pnlPct: number;
  exitReason: "sl" | "tp" | "indicator_exit" | "time_exit" | "trailing_stop" | "end_of_data";
  barsHeld: number;
}

export interface DslBacktestReport {
  trades: number;
  wins: number;
  winrate: number;
  totalPnlPct: number;
  maxDrawdownPct: number;
  candles: number;
  tradeLog: DslTradeRecord[];
}

export interface DslExecOpts {
  feeBps: number;
  slippageBps: number;
}

// ---------------------------------------------------------------------------
// DSL shape types (mirrors compiled DSL structure)
// ---------------------------------------------------------------------------

interface DslIndicatorRef {
  type: string;
  length?: number;
  period?: number;
  atrPeriod?: number;
  multiplier?: number;
  fastPeriod?: number;
  slowPeriod?: number;
  signalPeriod?: number;
  stdDevMult?: number;
}

interface DslSignal {
  type: string; // "crossover" | "crossunder" | "compare" | "direct" | "raw"
  op?: string;
  fast?: { blockType: string; length?: number } | null;
  slow?: { blockType: string; length?: number } | null;
  left?: { blockType: string; length?: number } | null;
  right?: { blockType: string; length?: number } | null;
}

interface DslExitLevel {
  type: "fixed_pct" | "fixed_price" | "atr_multiple";
  value: number;
  atrPeriod?: number;
}

interface DslIndicatorExit {
  indicator: DslIndicatorRef;
  condition: { op: string; value: number };
  appliesTo?: "long" | "short" | "both";
}

interface DslTrailingStop {
  type: "trailing_pct" | "trailing_atr";
  activationPct?: number;
  callbackPct?: number;
  activationAtr?: number;
  callbackAtr?: number;
}

interface DslTimeExit {
  maxBarsInPosition: number;
}

interface DslSideCondition {
  indicator: DslIndicatorRef;
  source?: string;
  long: { op: string };
  short: { op: string };
}

interface DslEntry {
  side?: "Buy" | "Sell";
  sideCondition?: DslSideCondition;
  signal?: DslSignal;
  indicators?: DslIndicatorRef[];
  stopLoss?: DslExitLevel; // v1 embedded
  takeProfit?: DslExitLevel; // v1 embedded
}

interface DslExit {
  stopLoss: DslExitLevel;
  takeProfit: DslExitLevel;
  indicatorExit?: DslIndicatorExit;
  trailingStop?: DslTrailingStop;
  timeExit?: DslTimeExit;
}

interface DslRisk {
  riskPerTradePct: number;
  maxPositionSizeUsd?: number;
  cooldownSeconds?: number;
}

export interface ParsedDsl {
  dslVersion: number;
  entry: DslEntry;
  exit?: DslExit;
  risk: DslRisk;
}

// ---------------------------------------------------------------------------
// Indicator computation cache
// ---------------------------------------------------------------------------

interface IndicatorCache {
  sma: Map<number, (number | null)[]>;
  ema: Map<number, (number | null)[]>;
  rsi: Map<number, (number | null)[]>;
  atr: Map<number, (number | null)[]>;
  adx: Map<number, { adx: (number | null)[]; plusDI: (number | null)[]; minusDI: (number | null)[] }>;
  supertrend: Map<string, { supertrend: (number | null)[]; direction: (1 | -1 | null)[] }>;
  vwap: (number | null)[] | null;
}

function createIndicatorCache(): IndicatorCache {
  return {
    sma: new Map(),
    ema: new Map(),
    rsi: new Map(),
    atr: new Map(),
    adx: new Map(),
    supertrend: new Map(),
    vwap: null,
  };
}

// ---------------------------------------------------------------------------
// Simple indicator computations (SMA, EMA, RSI)
// These are pure, deterministic functions matching the block types.
// ---------------------------------------------------------------------------

function calcSMA(candles: Candle[], length: number): (number | null)[] {
  const n = candles.length;
  const result: (number | null)[] = new Array(n).fill(null);
  if (n < length) return result;

  let sum = 0;
  for (let i = 0; i < length; i++) sum += candles[i].close;
  result[length - 1] = sum / length;

  for (let i = length; i < n; i++) {
    sum += candles[i].close - candles[i - length].close;
    result[i] = sum / length;
  }
  return result;
}

function calcEMA(candles: Candle[], length: number): (number | null)[] {
  const n = candles.length;
  const result: (number | null)[] = new Array(n).fill(null);
  if (n < length) return result;

  // Seed with SMA
  let sum = 0;
  for (let i = 0; i < length; i++) sum += candles[i].close;
  let ema = sum / length;
  result[length - 1] = ema;

  const k = 2 / (length + 1);
  for (let i = length; i < n; i++) {
    ema = candles[i].close * k + ema * (1 - k);
    result[i] = ema;
  }
  return result;
}

function calcRSI(candles: Candle[], length: number): (number | null)[] {
  const n = candles.length;
  const result: (number | null)[] = new Array(n).fill(null);
  if (n < length + 1) return result;

  let gainSum = 0;
  let lossSum = 0;
  for (let i = 1; i <= length; i++) {
    const change = candles[i].close - candles[i - 1].close;
    if (change > 0) gainSum += change;
    else lossSum += Math.abs(change);
  }

  let avgGain = gainSum / length;
  let avgLoss = lossSum / length;
  result[length] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);

  for (let i = length + 1; i < n; i++) {
    const change = candles[i].close - candles[i - 1].close;
    const gain = change > 0 ? change : 0;
    const loss = change < 0 ? Math.abs(change) : 0;
    avgGain = (avgGain * (length - 1) + gain) / length;
    avgLoss = (avgLoss * (length - 1) + loss) / length;
    result[i] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
  }
  return result;
}

// ---------------------------------------------------------------------------
// Indicator resolution — get cached indicator values for a block type + params
// ---------------------------------------------------------------------------

function getIndicatorValues(
  blockType: string,
  params: { length?: number; period?: number; atrPeriod?: number; multiplier?: number },
  candles: Candle[],
  cache: IndicatorCache,
): (number | null)[] {
  const type = blockType.toLowerCase();

  if (type === "sma") {
    const len = params.length ?? 14;
    if (!cache.sma.has(len)) cache.sma.set(len, calcSMA(candles, len));
    return cache.sma.get(len)!;
  }

  if (type === "ema") {
    const len = params.length ?? 14;
    if (!cache.ema.has(len)) cache.ema.set(len, calcEMA(candles, len));
    return cache.ema.get(len)!;
  }

  if (type === "rsi") {
    const len = params.length ?? 14;
    if (!cache.rsi.has(len)) cache.rsi.set(len, calcRSI(candles, len));
    return cache.rsi.get(len)!;
  }

  if (type === "atr") {
    const period = params.period ?? params.length ?? 14;
    if (!cache.atr.has(period)) cache.atr.set(period, calcATR(candles, period));
    return cache.atr.get(period)!;
  }

  if (type === "adx") {
    const period = params.period ?? params.length ?? 14;
    if (!cache.adx.has(period)) cache.adx.set(period, calcADX(candles, period));
    return cache.adx.get(period)!.adx;
  }

  if (type === "supertrend") {
    const atrPeriod = params.atrPeriod ?? 10;
    const multiplier = params.multiplier ?? 3;
    const key = `${atrPeriod}_${multiplier}`;
    if (!cache.supertrend.has(key)) {
      cache.supertrend.set(key, calcSuperTrend(candles, atrPeriod, multiplier));
    }
    return cache.supertrend.get(key)!.direction.map(d => d as number | null);
  }

  if (type === "vwap") {
    if (!cache.vwap) cache.vwap = calcVWAP(candles);
    return cache.vwap;
  }

  if (type === "constant") {
    // Constant value — fill with the value
    const val = params.length ?? 0;
    return new Array(candles.length).fill(val);
  }

  // Unknown indicator — return all nulls
  return new Array(candles.length).fill(null);
}

function getSuperTrendDirection(
  params: { atrPeriod?: number; multiplier?: number },
  candles: Candle[],
  cache: IndicatorCache,
): (1 | -1 | null)[] {
  const atrPeriod = params.atrPeriod ?? 10;
  const multiplier = params.multiplier ?? 3;
  const key = `${atrPeriod}_${multiplier}`;
  if (!cache.supertrend.has(key)) {
    cache.supertrend.set(key, calcSuperTrend(candles, atrPeriod, multiplier));
  }
  return cache.supertrend.get(key)!.direction;
}

// ---------------------------------------------------------------------------
// Comparison operators
// ---------------------------------------------------------------------------

function evalOp(op: string, a: number, b: number): boolean {
  switch (op) {
    case "gt":
    case ">": return a > b;
    case "gte":
    case ">=": return a >= b;
    case "lt":
    case "<": return a < b;
    case "lte":
    case "<=": return a <= b;
    case "eq":
    case "==": return a === b;
    default: return false;
  }
}

// ---------------------------------------------------------------------------
// DSL parsing — extract structured data from raw dslJson
// ---------------------------------------------------------------------------

export function parseDsl(dslJson: unknown): ParsedDsl {
  if (!dslJson || typeof dslJson !== "object") {
    throw new Error("dslEvaluator: dslJson is null or not an object");
  }
  const dsl = dslJson as Record<string, unknown>;

  const dslVersion = typeof dsl.dslVersion === "number" ? dsl.dslVersion : 1;
  const entry = (dsl.entry ?? {}) as DslEntry;
  const exit = dsl.exit as DslExit | undefined;
  const risk = (dsl.risk ?? { riskPerTradePct: 1 }) as DslRisk;

  return { dslVersion, entry, exit, risk };
}

// ---------------------------------------------------------------------------
// Entry signal evaluation
// ---------------------------------------------------------------------------

function evaluateSignal(
  signal: DslSignal | undefined,
  i: number,
  candles: Candle[],
  cache: IndicatorCache,
): boolean {
  if (!signal) return false;

  if (signal.type === "crossover" || signal.type === "crossunder") {
    // Cross signal: fast crosses over/under slow
    if (!signal.fast || !signal.slow || i < 1) return false;
    const fastVals = getIndicatorValues(signal.fast.blockType, { length: signal.fast.length }, candles, cache);
    const slowVals = getIndicatorValues(signal.slow.blockType, { length: signal.slow.length }, candles, cache);

    const curFast = fastVals[i];
    const curSlow = slowVals[i];
    const prevFast = fastVals[i - 1];
    const prevSlow = slowVals[i - 1];

    if (curFast === null || curSlow === null || prevFast === null || prevSlow === null) return false;

    if (signal.type === "crossover") {
      return prevFast <= prevSlow && curFast > curSlow;
    } else {
      return prevFast >= prevSlow && curFast < curSlow;
    }
  }

  if (signal.type === "compare") {
    if (!signal.left || !signal.right) return false;
    const leftVals = getIndicatorValues(signal.left.blockType, { length: signal.left.length }, candles, cache);
    const rightVals = getIndicatorValues(signal.right.blockType, { length: signal.right.length }, candles, cache);

    const l = leftVals[i];
    const r = rightVals[i];
    if (l === null || r === null) return false;

    return evalOp(signal.op ?? ">", l, r);
  }

  // "direct" or "raw" — no structured signal, skip
  return false;
}

// ---------------------------------------------------------------------------
// Side determination
// ---------------------------------------------------------------------------

function determineSide(
  entry: DslEntry,
  i: number,
  candles: Candle[],
  cache: IndicatorCache,
): TradeSide | null {
  // Fixed side
  if (entry.side) {
    return entry.side === "Buy" ? "long" : "short";
  }

  // Dynamic sideCondition (DSL v2)
  if (entry.sideCondition) {
    const sc = entry.sideCondition;
    const indValues = getIndicatorValues(
      sc.indicator.type,
      {
        length: sc.indicator.length,
        period: (sc.indicator as unknown as Record<string, unknown>).period as number | undefined,
        atrPeriod: sc.indicator.atrPeriod,
        multiplier: sc.indicator.multiplier,
      },
      candles,
      cache,
    );

    const val = indValues[i];
    if (val === null) return null;

    // For sideCondition, the source defaults to "close"
    const source = sc.source ?? "close";
    const price = candles[i][source as keyof Candle] as number;

    // Evaluate long condition: if indicator op price (e.g., close > SMA → long)
    if (evalOp(sc.long.op, price, val)) return "long";
    if (evalOp(sc.short.op, price, val)) return "short";
    return null;
  }

  return null;
}

// ---------------------------------------------------------------------------
// Exit level computation
// ---------------------------------------------------------------------------

function computeExitLevels(
  sl: DslExitLevel,
  tp: DslExitLevel,
  effectiveEntry: number,
  side: TradeSide,
  i: number,
  candles: Candle[],
  cache: IndicatorCache,
): { slPrice: number; tpPrice: number } {
  let slPrice: number;
  let tpPrice: number;

  // Stop loss
  if (sl.type === "atr_multiple") {
    const atrPeriod = sl.atrPeriod ?? 14;
    const atrVals = getIndicatorValues("atr", { period: atrPeriod }, candles, cache);
    const atrVal = atrVals[i] ?? 0;
    if (side === "long") {
      slPrice = effectiveEntry - sl.value * atrVal;
    } else {
      slPrice = effectiveEntry + sl.value * atrVal;
    }
  } else {
    // fixed_pct (default)
    if (side === "long") {
      slPrice = effectiveEntry * (1 - sl.value / 100);
    } else {
      slPrice = effectiveEntry * (1 + sl.value / 100);
    }
  }

  // Take profit
  if (tp.type === "atr_multiple") {
    const atrPeriod = tp.atrPeriod ?? 14;
    const atrVals = getIndicatorValues("atr", { period: atrPeriod }, candles, cache);
    const atrVal = atrVals[i] ?? 0;
    if (side === "long") {
      tpPrice = effectiveEntry + tp.value * atrVal;
    } else {
      tpPrice = effectiveEntry - tp.value * atrVal;
    }
  } else {
    // fixed_pct
    if (side === "long") {
      tpPrice = effectiveEntry * (1 + tp.value / 100);
    } else {
      tpPrice = effectiveEntry * (1 - tp.value / 100);
    }
  }

  return { slPrice, tpPrice };
}

// ---------------------------------------------------------------------------
// Main evaluator
// ---------------------------------------------------------------------------

/**
 * Run a DSL-driven backtest evaluation.
 *
 * @param candles    OHLCV candle array (must be sorted by openTime ascending)
 * @param dslJson    Compiled strategy DSL (from StrategyVersion.dslJson)
 * @param opts       Execution options (fees, slippage)
 * @returns          Deterministic backtest report
 */
export function runDslBacktest(
  candles: Candle[],
  dslJson: unknown,
  opts: Partial<DslExecOpts> = {},
): DslBacktestReport {
  const { feeBps = 0, slippageBps = 0 } = opts;

  const emptyReport: DslBacktestReport = {
    trades: 0, wins: 0, winrate: 0, totalPnlPct: 0, maxDrawdownPct: 0,
    candles: candles.length, tradeLog: [],
  };

  const parsed = parseDsl(dslJson);
  const { entry, exit, risk } = parsed;

  // Resolve SL/TP from v2 exit section or v1 entry-embedded
  const slDef: DslExitLevel = exit?.stopLoss
    ?? entry.stopLoss
    ?? { type: "fixed_pct", value: risk.riskPerTradePct };
  const tpDef: DslExitLevel = exit?.takeProfit
    ?? entry.takeProfit
    ?? { type: "fixed_pct", value: risk.riskPerTradePct * 2 };

  // Need at least 2 candles for any signal evaluation
  if (candles.length < 2) return emptyReport;

  // Pre-compute indicator cache
  const cache = createIndicatorCache();

  const entryMult = 1 + (feeBps + slippageBps) / 10_000;
  const exitMult = 1 - feeBps / 10_000;

  const tradeLog: DslTradeRecord[] = [];

  // Position state
  let inPosition = false;
  let positionSide: TradeSide = "long";
  let effectiveEntry = 0;
  let entryTime = 0;
  let entryBarIndex = 0;
  let slPrice = 0;
  let tpPrice = 0;
  let trailingHigh = 0; // for trailing stop (long)
  let trailingLow = Infinity; // for trailing stop (short)
  let trailingStopPrice = 0;
  let trailingActivated = false;

  let cumulativePnl = 0;
  let peakPnl = 0;
  let maxDrawdownPct = 0;

  function recordTrade(
    exitTime: number,
    rawExitPrice: number,
    outcome: "WIN" | "LOSS" | "NEUTRAL",
    exitReason: DslTradeRecord["exitReason"],
    barsHeld: number,
  ): void {
    const effectiveExit = rawExitPrice * exitMult;
    let pnlPct: number;
    if (positionSide === "long") {
      pnlPct = ((effectiveExit - effectiveEntry) / effectiveEntry) * 100;
    } else {
      pnlPct = ((effectiveEntry - effectiveExit) / effectiveEntry) * 100;
    }

    tradeLog.push({
      entryTime,
      exitTime,
      side: positionSide,
      entryPrice: effectiveEntry,
      exitPrice: effectiveExit,
      slPrice,
      tpPrice,
      outcome,
      pnlPct,
      exitReason,
      barsHeld,
    });

    cumulativePnl += pnlPct;
    if (cumulativePnl > peakPnl) peakPnl = cumulativePnl;
    const dd = peakPnl - cumulativePnl;
    if (dd > maxDrawdownPct) maxDrawdownPct = dd;

    inPosition = false;
  }

  // Determine minimum lookback — start from bar 1 to allow prev-bar checks
  const startBar = 1;

  for (let i = startBar; i < candles.length; i++) {
    const c = candles[i];

    if (inPosition) {
      const barsHeld = i - entryBarIndex;

      // --- Exit checks (priority: SL → trailing → indicator → TP → time) ---

      // 1. Stop loss
      if (positionSide === "long") {
        if (c.low <= slPrice) {
          recordTrade(c.openTime, slPrice, "LOSS", "sl", barsHeld);
          continue;
        }
      } else {
        if (c.high >= slPrice) {
          recordTrade(c.openTime, slPrice, "LOSS", "sl", barsHeld);
          continue;
        }
      }

      // 2. Trailing stop
      if (exit?.trailingStop) {
        const ts = exit.trailingStop;
        if (ts.type === "trailing_pct" && ts.activationPct !== undefined && ts.callbackPct !== undefined) {
          if (positionSide === "long") {
            if (c.high > trailingHigh) trailingHigh = c.high;
            const activationPrice = effectiveEntry * (1 + ts.activationPct / 100);
            if (trailingHigh >= activationPrice) {
              trailingActivated = true;
              trailingStopPrice = trailingHigh * (1 - ts.callbackPct / 100);
            }
            if (trailingActivated && c.low <= trailingStopPrice) {
              const outcome = trailingStopPrice >= effectiveEntry ? "WIN" : "LOSS";
              recordTrade(c.openTime, trailingStopPrice, outcome, "trailing_stop", barsHeld);
              continue;
            }
          } else {
            if (c.low < trailingLow) trailingLow = c.low;
            const activationPrice = effectiveEntry * (1 - ts.activationPct / 100);
            if (trailingLow <= activationPrice) {
              trailingActivated = true;
              trailingStopPrice = trailingLow * (1 + ts.callbackPct / 100);
            }
            if (trailingActivated && c.high >= trailingStopPrice) {
              const outcome = trailingStopPrice <= effectiveEntry ? "WIN" : "LOSS";
              recordTrade(c.openTime, trailingStopPrice, outcome, "trailing_stop", barsHeld);
              continue;
            }
          }
        }
      }

      // 3. Indicator exit
      if (exit?.indicatorExit) {
        const ie = exit.indicatorExit;
        const appliesTo = ie.appliesTo ?? "both";
        if (appliesTo === "both" || appliesTo === positionSide) {
          const indVals = getIndicatorValues(
            ie.indicator.type,
            {
              length: ie.indicator.length,
              period: (ie.indicator as unknown as Record<string, unknown>).period as number | undefined,
              atrPeriod: ie.indicator.atrPeriod,
              multiplier: ie.indicator.multiplier,
            },
            candles,
            cache,
          );
          const val = indVals[i];
          if (val !== null && evalOp(ie.condition.op, val, ie.condition.value)) {
            const exitPrice = c.close;
            const pnlDirection = positionSide === "long"
              ? exitPrice * exitMult - effectiveEntry
              : effectiveEntry - exitPrice * exitMult;
            const outcome = pnlDirection > 0 ? "WIN" : pnlDirection < 0 ? "LOSS" : "NEUTRAL";
            recordTrade(c.openTime, exitPrice, outcome, "indicator_exit", barsHeld);
            continue;
          }
        }
      }

      // 4. Take profit
      if (positionSide === "long") {
        if (c.high >= tpPrice) {
          recordTrade(c.openTime, tpPrice, "WIN", "tp", barsHeld);
          continue;
        }
      } else {
        if (c.low <= tpPrice) {
          recordTrade(c.openTime, tpPrice, "WIN", "tp", barsHeld);
          continue;
        }
      }

      // 5. Time exit
      if (exit?.timeExit) {
        if (barsHeld >= exit.timeExit.maxBarsInPosition) {
          const exitPrice = c.close;
          const pnlDirection = positionSide === "long"
            ? exitPrice * exitMult - effectiveEntry
            : effectiveEntry - exitPrice * exitMult;
          const outcome = pnlDirection > 0 ? "WIN" : pnlDirection < 0 ? "LOSS" : "NEUTRAL";
          recordTrade(c.openTime, exitPrice, outcome, "time_exit", barsHeld);
          continue;
        }
      }

      // Still in position
    } else {
      // --- Entry evaluation ---

      // Determine side
      const side = determineSide(entry, i, candles, cache);
      if (!side) continue;

      // Evaluate entry signal
      const signalFired = evaluateSignal(entry.signal, i, candles, cache);
      if (!signalFired) continue;

      // Enter position
      inPosition = true;
      positionSide = side;
      effectiveEntry = c.close * entryMult;
      entryTime = c.openTime;
      entryBarIndex = i;

      // Compute SL/TP levels
      const levels = computeExitLevels(slDef, tpDef, effectiveEntry, side, i, candles, cache);
      slPrice = levels.slPrice;
      tpPrice = levels.tpPrice;

      // Reset trailing stop state
      trailingHigh = c.close;
      trailingLow = c.close;
      trailingStopPrice = 0;
      trailingActivated = false;
    }
  }

  // Close open position at last candle
  if (inPosition) {
    const last = candles[candles.length - 1];
    const barsHeld = candles.length - 1 - entryBarIndex;
    const eodExitPrice = last.close * exitMult;
    const eodPnlDirection = positionSide === "long"
      ? eodExitPrice - effectiveEntry
      : effectiveEntry - eodExitPrice;
    const eodOutcome = eodPnlDirection > 0 ? "WIN" : eodPnlDirection < 0 ? "LOSS" : "NEUTRAL";
    recordTrade(last.openTime, last.close, eodOutcome, "end_of_data", barsHeld);
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
    candles: candles.length,
    tradeLog,
  };
}
