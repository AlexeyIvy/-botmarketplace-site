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
import { calcSMA } from "./indicators/sma.js";
import { calcEMA } from "./indicators/ema.js";
import { calcRSI } from "./indicators/rsi.js";
import { calcATR } from "./indicators/atr.js";
import { calcADX } from "./indicators/adx.js";
import { calcSuperTrend } from "./indicators/supertrend.js";
import { calcVWAP } from "./indicators/vwap.js";
import { calcMACD } from "./indicators/macd.js";
import type { MACDResult } from "./indicators/macd.js";
import { resolveMtfIndicator, createMtfCache } from "./mtf/mtfIndicatorResolver.js";
import { fvgSeries, sweepSeries, orderBlockSeries, mssSeries } from "./runtime/patternEngine.js";
import { calcVolumeProfile, type VolumeProfileResult } from "./indicators/volumeProfile.js";
import { calcProximityFilter, type ProximityMode } from "./indicators/proximityFilter.js";
import { logger } from "./logger.js";
import type { DcaConfig, SafetyOrderLevel, DcaPositionState } from "./dcaPlanning.js";
import {
  generateSafetyOrderSchedule,
  openDcaPosition,
  applySafetyOrderFill,
  validateDcaConfig,
} from "./dcaPlanning.js";

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
  /** DCA-specific: number of safety orders filled during this trade (0 for non-DCA) */
  dcaSafetyOrdersFilled?: number;
  /** DCA-specific: average entry after all fills */
  dcaAvgEntry?: number;
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

export interface DslIndicatorRef {
  type: string;
  length?: number;
  period?: number;
  atrPeriod?: number;
  multiplier?: number;
  fastPeriod?: number;
  slowPeriod?: number;
  signalPeriod?: number;
  stdDevMult?: number;
  bins?: number;
  /** Optional: resolve this indicator from a different timeframe's candle data.
   *  When set, the evaluator looks up candles from the CandleBundle's context TF
   *  instead of the primary candle array. Requires MTF evaluation mode (#134). */
  sourceTimeframe?: string;
}

export interface DslSignalRef {
  blockType: string;
  length?: number;
  period?: number;
  multiplier?: number;
}

export interface DslSignal {
  type: string; // "crossover" | "crossunder" | "compare" | "and" | "or" | "confirm_n_bars" | "direct" | "raw"
  op?: string;
  fast?: DslSignalRef | null;
  slow?: DslSignalRef | null;
  left?: DslSignalRef | null;
  right?: DslSignalRef | null;
  /** Sub-conditions for composed signals (type "and" / "or" / "confirm_n_bars") */
  conditions?: DslSignal[];
  /** Number of consecutive bars required (type "confirm_n_bars") */
  bars?: number;
}

export interface DslExitLevel {
  type: "fixed_pct" | "fixed_price" | "atr_multiple";
  value: number;
  atrPeriod?: number;
}

export interface DslIndicatorExit {
  indicator: DslIndicatorRef;
  condition: { op: string; value: number };
  appliesTo?: "long" | "short" | "both";
}

export interface DslTrailingStop {
  type: "trailing_pct" | "trailing_atr";
  activationPct?: number;
  callbackPct?: number;
  activationAtr?: number;
  callbackAtr?: number;
}

export interface DslTimeExit {
  maxBarsInPosition: number;
}

export interface DslSideCondition {
  indicator: DslIndicatorRef;
  source?: string;
  mode?: "price_vs_indicator" | "indicator_sign";
  long: { op: string };
  short: { op: string };
}

export interface DslProximityFilter {
  threshold: number;
  mode: ProximityMode;
  /** Optional: indicator type providing the reference level (default: volume_profile POC). */
  levelSource?: string;
}

export interface DslEntry {
  side?: "Buy" | "Sell";
  sideCondition?: DslSideCondition;
  signal?: DslSignal;
  indicators?: DslIndicatorRef[];
  proximityFilter?: DslProximityFilter;
  stopLoss?: DslExitLevel; // v1 embedded
  takeProfit?: DslExitLevel; // v1 embedded
}

export interface DslExit {
  stopLoss: DslExitLevel;
  takeProfit: DslExitLevel;
  indicatorExit?: DslIndicatorExit;
  trailingStop?: DslTrailingStop;
  timeExit?: DslTimeExit;
}

export interface DslRisk {
  riskPerTradePct: number;
  maxPositionSizeUsd?: number;
  cooldownSeconds?: number;
}

export interface ParsedDsl {
  dslVersion: number;
  entry: DslEntry;
  exit?: DslExit;
  risk: DslRisk;
  dca?: DcaConfig;
}

// ---------------------------------------------------------------------------
// Indicator computation cache
// ---------------------------------------------------------------------------

export interface BollingerBandsResult {
  upper: (number | null)[];
  middle: (number | null)[];
  lower: (number | null)[];
}

export interface IndicatorCache {
  sma: Map<number, (number | null)[]>;
  ema: Map<number, (number | null)[]>;
  rsi: Map<number, (number | null)[]>;
  atr: Map<number, (number | null)[]>;
  adx: Map<number, { adx: (number | null)[]; plusDI: (number | null)[]; minusDI: (number | null)[] }>;
  supertrend: Map<string, { supertrend: (number | null)[]; direction: (1 | -1 | null)[] }>;
  vwap: (number | null)[] | null;
  bollinger: Map<string, BollingerBandsResult>;
  macd: Map<string, MACDResult>;
  volume: (number | null)[] | null;
  /** SMC pattern series cache (keyed by "type_params" string). */
  smcPatterns: Map<string, (number | null)[]>;
  /** Volume profile cache (keyed by "period_bins"). */
  volumeProfile: Map<string, VolumeProfileResult>;
}

export function createIndicatorCache(): IndicatorCache {
  return {
    sma: new Map(),
    ema: new Map(),
    rsi: new Map(),
    atr: new Map(),
    adx: new Map(),
    supertrend: new Map(),
    vwap: null,
    bollinger: new Map(),
    macd: new Map(),
    volume: null,
    smcPatterns: new Map(),
    volumeProfile: new Map(),
  };
}

// ---------------------------------------------------------------------------
// Bollinger Bands computation
// ---------------------------------------------------------------------------

function calcBollingerBands(
  candles: Candle[],
  period: number,
  stdDevMult: number,
): BollingerBandsResult {
  const n = candles.length;
  const upper: (number | null)[] = new Array(n).fill(null);
  const middle: (number | null)[] = new Array(n).fill(null);
  const lower: (number | null)[] = new Array(n).fill(null);
  if (n < period) return { upper, middle, lower };

  for (let i = period - 1; i < n; i++) {
    let sum = 0;
    for (let j = i - period + 1; j <= i; j++) sum += candles[j].close;
    const mean = sum / period;

    let sqSum = 0;
    for (let j = i - period + 1; j <= i; j++) {
      const diff = candles[j].close - mean;
      sqSum += diff * diff;
    }
    const stdDev = Math.sqrt(sqSum / period);

    middle[i] = mean;
    upper[i] = mean + stdDevMult * stdDev;
    lower[i] = mean - stdDevMult * stdDev;
  }

  return { upper, middle, lower };
}

function getBollingerBands(
  params: { period?: number; length?: number; stdDevMult?: number; multiplier?: number },
  candles: Candle[],
  cache: IndicatorCache,
): BollingerBandsResult {
  const period = params.period ?? params.length ?? 20;
  const mult = params.stdDevMult ?? params.multiplier ?? 2;
  const key = `${period}_${mult}`;
  if (!cache.bollinger.has(key)) {
    cache.bollinger.set(key, calcBollingerBands(candles, period, mult));
  }
  return cache.bollinger.get(key)!;
}

// ---------------------------------------------------------------------------
// Indicator resolution — get cached indicator values for a block type + params
// ---------------------------------------------------------------------------

export function getIndicatorValues(
  blockType: string,
  params: {
    length?: number; period?: number; atrPeriod?: number; multiplier?: number;
    fastPeriod?: number; slowPeriod?: number; signalPeriod?: number;
    bins?: number;
  },
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

  if (type === "bollinger_lower" || type === "bb_lower") {
    const bb = getBollingerBands(params, candles, cache);
    return bb.lower;
  }

  if (type === "bollinger_upper" || type === "bb_upper") {
    const bb = getBollingerBands(params, candles, cache);
    return bb.upper;
  }

  if (type === "bollinger_middle" || type === "bb_middle" || type === "bollinger") {
    const bb = getBollingerBands(params, candles, cache);
    return bb.middle;
  }

  if (type === "macd" || type === "macd_signal" || type === "macd_histogram") {
    const fast = params.fastPeriod ?? 12;
    const slow = params.slowPeriod ?? 26;
    const sig = params.signalPeriod ?? 9;
    const key = `${fast}_${slow}_${sig}`;
    if (!cache.macd.has(key)) {
      cache.macd.set(key, calcMACD(candles, fast, slow, sig));
    }
    const result = cache.macd.get(key)!;
    if (type === "macd_signal") return result.signal;
    if (type === "macd_histogram") return result.histogram;
    return result.histogram; // "macd" block returns histogram (primary signal for compare)
  }

  if (type === "volume") {
    if (!cache.volume) {
      cache.volume = candles.map((c) => c.volume);
    }
    return cache.volume;
  }

  if (type === "constant") {
    // Constant value — DSL convention stores threshold in "length" field
    const val = params.length ?? (params as Record<string, unknown>)["value"] ?? 0;
    return new Array(candles.length).fill(val);
  }

  // ── SMC Pattern Primitives (#137/#138) ──────────────────────────────────
  if (type === "fair_value_gap") {
    const minGapRatio = params.multiplier ?? 0;
    const key = `fvg_${minGapRatio}`;
    if (!cache.smcPatterns.has(key)) {
      cache.smcPatterns.set(key, fvgSeries(candles, { minGapRatio }));
    }
    return cache.smcPatterns.get(key)!;
  }

  if (type === "liquidity_sweep") {
    const swingLen = params.length ?? 3;
    const maxAge = params.period ?? 50;
    const key = `sweep_${swingLen}_${maxAge}`;
    if (!cache.smcPatterns.has(key)) {
      cache.smcPatterns.set(key, sweepSeries(candles, { swingLen, maxAge }));
    }
    return cache.smcPatterns.get(key)!;
  }

  if (type === "order_block") {
    const atrPeriod = params.period ?? 14;
    const minImpulseMultiple = params.multiplier ?? 1.5;
    const maxLookback = params.length ?? 5;
    const key = `ob_${atrPeriod}_${minImpulseMultiple}_${maxLookback}`;
    if (!cache.smcPatterns.has(key)) {
      cache.smcPatterns.set(key, orderBlockSeries(candles, { atrPeriod, minImpulseMultiple, maxLookback }));
    }
    return cache.smcPatterns.get(key)!;
  }

  if (type === "market_structure_shift") {
    const swingLen = params.length ?? 3;
    const key = `mss_${swingLen}`;
    if (!cache.smcPatterns.has(key)) {
      cache.smcPatterns.set(key, mssSeries(candles, { swingLen }));
    }
    return cache.smcPatterns.get(key)!;
  }

  // ── Volume Profile (#135) ─────────────────────────────────────────────
  if (type === "volume_profile" || type === "volume_profile_poc") {
    const vp = getVolumeProfileCached(params, candles, cache);
    return vp.poc;
  }
  if (type === "volume_profile_vah") {
    const vp = getVolumeProfileCached(params, candles, cache);
    return vp.vah;
  }
  if (type === "volume_profile_val") {
    const vp = getVolumeProfileCached(params, candles, cache);
    return vp.val;
  }

  // Unknown indicator — return all nulls
  logger.warn({ blockType: type }, "Unknown indicator type — returning nulls");
  return new Array(candles.length).fill(null);
}

function getVolumeProfileCached(
  params: { period?: number; bins?: number },
  candles: Candle[],
  cache: IndicatorCache,
): VolumeProfileResult {
  const period = params.period ?? 20;
  const bins = params.bins ?? 24;
  const key = `${period}_${bins}`;
  if (!cache.volumeProfile.has(key)) {
    cache.volumeProfile.set(key, calcVolumeProfile(candles, period, bins));
  }
  return cache.volumeProfile.get(key)!;
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

export function evalOp(op: string, a: number, b: number): boolean {
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
  const dca = dsl.dca as DcaConfig | undefined;

  return { dslVersion, entry, exit, risk, dca };
}

// ---------------------------------------------------------------------------
// Entry signal evaluation
// ---------------------------------------------------------------------------

const MAX_SIGNAL_DEPTH = 5;

export function evaluateSignal(
  signal: DslSignal | undefined,
  i: number,
  candles: Candle[],
  cache: IndicatorCache,
  _depth = 0,
): boolean {
  if (!signal) return false;
  if (_depth >= MAX_SIGNAL_DEPTH) return false;

  // Composed conditions: and / or
  if (signal.type === "and") {
    if (!signal.conditions || signal.conditions.length === 0) return false;
    return signal.conditions.every((sub) => evaluateSignal(sub, i, candles, cache, _depth + 1));
  }
  if (signal.type === "or") {
    if (!signal.conditions || signal.conditions.length === 0) return false;
    return signal.conditions.some((sub) => evaluateSignal(sub, i, candles, cache, _depth + 1));
  }

  // Confirm N Bars: sub-signal must be true for N consecutive bars
  if (signal.type === "confirm_n_bars") {
    if (!signal.conditions || signal.conditions.length !== 1) return false;
    const nBars = signal.bars ?? 3;
    if (i < nBars - 1) return false;
    for (let j = i - nBars + 1; j <= i; j++) {
      if (!evaluateSignal(signal.conditions[0], j, candles, cache, _depth + 1)) return false;
    }
    return true;
  }

  if (signal.type === "crossover" || signal.type === "crossunder") {
    // Cross signal: fast crosses over/under slow
    if (!signal.fast || !signal.slow || i < 1) return false;
    const fastVals = getIndicatorValues(signal.fast.blockType, signal.fast, candles, cache);
    const slowVals = getIndicatorValues(signal.slow.blockType, signal.slow, candles, cache);

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
    const leftVals = getIndicatorValues(signal.left.blockType, signal.left, candles, cache);
    const rightVals = getIndicatorValues(signal.right.blockType, signal.right, candles, cache);

    const l = leftVals[i];
    const r = rightVals[i];
    if (l === null || r === null) return false;

    return evalOp(signal.op ?? ">", l, r);
  }

  // "direct" or "raw" — no structured signal, skip
  return false;
}

// ---------------------------------------------------------------------------
// Proximity filter gate
// ---------------------------------------------------------------------------

/**
 * Evaluate proximity filter at bar index `i`.
 * Returns true if price is near the reference level (signal allowed),
 * false if too far (signal blocked), or true if no filter configured.
 */
export function evaluateProximityFilter(
  pf: DslProximityFilter | undefined,
  i: number,
  candles: Candle[],
  cache: IndicatorCache,
): boolean {
  if (!pf) return true; // no filter → pass through

  // Get reference level series (default: volume_profile POC)
  const levelSource = pf.levelSource ?? "volume_profile";
  const levelVals = getIndicatorValues(levelSource, {}, candles, cache);

  const price = candles[i]?.close ?? null;
  const level = levelVals[i];
  if (price === null || level === null || level === 0) return true; // insufficient data → pass through

  const distance = Math.abs(price - level);
  if (pf.mode === "absolute") {
    return distance <= pf.threshold;
  }
  // percentage mode
  return (distance / level) * 100 <= pf.threshold;
}

// ---------------------------------------------------------------------------
// Side determination
// ---------------------------------------------------------------------------

export function determineSide(
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

    // Discrete signal mode: sign of indicator value determines side
    if (sc.mode === "indicator_sign") {
      if (val > 0) return "long";
      if (val < 0) return "short";
      return null;
    }

    // Default mode (price_vs_indicator): compare price to indicator value
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

export function computeExitLevels(
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
/**
 * Optional multi-timeframe context for backtest evaluation.
 * When provided, indicator refs with `sourceTimeframe` resolve
 * from the bundle's context-TF candles via the MTF resolver.
 */
export interface MtfBacktestContext {
  bundle: import("./mtf/intervalAlignment.js").CandleBundle;
}

export function runDslBacktest(
  candles: Candle[],
  dslJson: unknown,
  opts: Partial<DslExecOpts> = {},
  mtfContext?: MtfBacktestContext,
): DslBacktestReport {
  const { feeBps = 0, slippageBps = 0 } = opts;

  // MTF-aware indicator resolution helper (#134-slice4):
  // When mtfContext is provided, indicator refs with sourceTimeframe resolve
  // from context-TF candles. Otherwise falls back to single-TF getIndicatorValues.
  const mtfCache = mtfContext
    ? createMtfCache()
    : null;

  function resolveIndicator(
    ref: DslIndicatorRef,
    primaryCandles: Candle[],
    singleTfCache: IndicatorCache,
  ): (number | null)[] {
    if (mtfCache && mtfContext) {
      return resolveMtfIndicator(ref, primaryCandles, mtfCache, mtfContext.bundle);
    }
    return getIndicatorValues(ref.type, {
      length: ref.length,
      period: ref.period,
      atrPeriod: ref.atrPeriod,
      multiplier: ref.multiplier,
    }, primaryCandles, singleTfCache);
  }

  const emptyReport: DslBacktestReport = {
    trades: 0, wins: 0, winrate: 0, totalPnlPct: 0, maxDrawdownPct: 0,
    candles: candles.length, tradeLog: [],
  };

  const parsed = parseDsl(dslJson);
  const { entry, exit, risk, dca: dcaConfig } = parsed;

  // Resolve SL/TP from v2 exit section or v1 entry-embedded
  const slDef: DslExitLevel = exit?.stopLoss
    ?? entry.stopLoss
    ?? { type: "fixed_pct", value: risk.riskPerTradePct };
  const tpDef: DslExitLevel = exit?.takeProfit
    ?? entry.takeProfit
    ?? { type: "fixed_pct", value: risk.riskPerTradePct * 2 };

  // DCA mode: when dcaConfig is present, TP and SL are driven by DCA planning
  let isDca = !!dcaConfig;

  // Defensive: validate DCA config before use; skip DCA if invalid
  if (isDca && dcaConfig) {
    const dcaErr = validateDcaConfig(dcaConfig);
    if (dcaErr) {
      isDca = false; // fall back to non-DCA behavior rather than producing corrupt state
    }
  }

  // For DCA, derive SL% from the exit-level definition for consistent recalculation.
  // Supported SL types for DCA recalc:
  //   fixed_pct   → use value directly
  //   atr_multiple → derive % from (entryPrice, slPrice) at entry time
  //   fixed_price  → derive % from (entryPrice, slPrice) at entry time
  const dcaSlPct = isDca && slDef.type === "fixed_pct" ? slDef.value : 0;

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

  // DCA state (#131)
  let dcaState: DcaPositionState | null = null;
  let dcaPendingSOs: SafetyOrderLevel[] = [];
  // Resolved SL% for DCA recalculation (set at entry, frozen for position lifetime)
  let dcaSlPctResolved = dcaSlPct;

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

    const record: DslTradeRecord = {
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
    };

    // Attach DCA metadata if applicable
    if (dcaState) {
      record.dcaSafetyOrdersFilled = dcaState.safetyOrdersFilled;
      record.dcaAvgEntry = dcaState.avgEntryPrice;
    }

    tradeLog.push(record);

    cumulativePnl += pnlPct;
    if (cumulativePnl > peakPnl) peakPnl = cumulativePnl;
    const dd = peakPnl - cumulativePnl;
    if (dd > maxDrawdownPct) maxDrawdownPct = dd;

    inPosition = false;
    dcaState = null;
    dcaPendingSOs = [];
  }

  // Determine minimum lookback — start from bar 1 to allow prev-bar checks
  const startBar = 1;

  for (let i = startBar; i < candles.length; i++) {
    const c = candles[i];

    if (inPosition) {
      const barsHeld = i - entryBarIndex;

      // --- DCA safety order fills (#131) ---
      // Check before exit evaluation: SO fills change avg entry and TP
      if (isDca && dcaState && dcaPendingSOs.length > 0) {
        // Fill all SOs whose trigger price was reached on this bar
        let soFilled = true;
        while (soFilled && dcaPendingSOs.length > 0) {
          const nextSO = dcaPendingSOs[0];
          const triggered =
            positionSide === "long"
              ? c.low <= nextSO.triggerPrice
              : c.high >= nextSO.triggerPrice;

          if (triggered) {
            dcaPendingSOs.shift();
            dcaState = applySafetyOrderFill(
              dcaState,
              nextSO.triggerPrice,
              nextSO.qty,
              nextSO.orderSizeUsd,
              dcaConfig!.takeProfitPct,
              dcaSlPctResolved,
            );
            // Update position-level state from DCA state
            effectiveEntry = dcaState.avgEntryPrice;
            tpPrice = dcaState.tpPrice;
            slPrice = dcaState.slPrice;
          } else {
            soFilled = false;
          }
        }
      }

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
          const indVals = resolveIndicator(ie.indicator, candles, cache);
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

      // Determine side (MTF-aware: uses resolveIndicator for sideCondition).
      // Note: this inlines the logic from determineSide() to use resolveIndicator.
      // Keep in sync with determineSide() if sideCondition evaluation changes.
      let side: TradeSide | null = null;
      if (entry.side) {
        side = entry.side === "Buy" ? "long" : "short";
      } else if (entry.sideCondition) {
        const sc = entry.sideCondition;
        const indValues = resolveIndicator(sc.indicator, candles, cache);
        const val = indValues[i];
        if (val !== null) {
          const source = sc.source ?? "close";
          const price = candles[i][source as keyof Candle] as number;
          if (evalOp(sc.long.op, price, val)) side = "long";
          else if (evalOp(sc.short.op, price, val)) side = "short";
        }
      }
      if (!side) continue;

      // Evaluate entry signal
      const signalFired = evaluateSignal(entry.signal, i, candles, cache);
      if (!signalFired) continue;

      // Proximity filter gate
      if (!evaluateProximityFilter(entry.proximityFilter, i, candles, cache)) continue;

      // Enter position
      inPosition = true;
      positionSide = side;
      effectiveEntry = c.close * entryMult;
      entryTime = c.openTime;
      entryBarIndex = i;

      // Compute SL/TP levels
      const levels = computeExitLevels(slDef, tpDef, effectiveEntry, side, i, candles, cache);
      slPrice = levels.slPrice;

      // DCA entry: initialize DCA state and override TP + SL from DCA planning
      if (isDca && dcaConfig) {
        // For non-fixed_pct SL types (atr_multiple, fixed_price), derive the
        // SL distance as a frozen percentage from the computed entry-time levels.
        if (slDef.type !== "fixed_pct") {
          dcaSlPctResolved = effectiveEntry > 0
            ? Math.abs(effectiveEntry - slPrice) / effectiveEntry * 100
            : dcaSlPct;
        } else {
          dcaSlPctResolved = dcaSlPct;
        }

        const schedule = generateSafetyOrderSchedule(dcaConfig, effectiveEntry, side);
        const baseQty = dcaConfig.baseOrderSizeUsd / effectiveEntry;
        dcaState = openDcaPosition(
          effectiveEntry,
          baseQty,
          dcaConfig.baseOrderSizeUsd,
          dcaConfig.takeProfitPct,
          dcaSlPctResolved,
          side,
        );
        dcaPendingSOs = [...schedule.safetyOrders];
        tpPrice = dcaState.tpPrice;
        slPrice = dcaState.slPrice;
      } else {
        tpPrice = levels.tpPrice;
        dcaState = null;
        dcaPendingSOs = [];
      }

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
