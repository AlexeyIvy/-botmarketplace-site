// ---------------------------------------------------------------------------
// Chart indicator helpers + registry framework (Stage 20e)
// All compute functions accept an array of close prices.
// Return arrays of same length: null for warm-up bars, number otherwise.
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Shared types
// ---------------------------------------------------------------------------

export interface IndicatorParams {
  period?: number;
  fastPeriod?: number;
  slowPeriod?: number;
  signalPeriod?: number;
  stdDev?: number;
}

export interface ActiveIndicator {
  /** Registry id — one of: "ma" | "ema" | "bb" | "rsi" | "macd" */
  id: string;
  params: IndicatorParams;
}

export interface IndicatorParamDef {
  key: keyof IndicatorParams;
  label: string;
  min: number;
  max: number;
  step?: number;
}

export interface IndicatorDefinition {
  id: string;
  label: string;
  defaultParams: IndicatorParams;
  placement: 'overlay' | 'oscillator';
  paramDefs: IndicatorParamDef[];
}

/** Master registry — add new indicators here in future */
export const INDICATOR_REGISTRY: IndicatorDefinition[] = [
  {
    id: 'ma',
    label: 'MA',
    defaultParams: { period: 20 },
    placement: 'overlay',
    paramDefs: [{ key: 'period', label: 'Period', min: 2, max: 500 }],
  },
  {
    id: 'ema',
    label: 'EMA',
    defaultParams: { period: 50 },
    placement: 'overlay',
    paramDefs: [{ key: 'period', label: 'Period', min: 2, max: 500 }],
  },
  {
    id: 'bb',
    label: 'Bollinger Bands',
    defaultParams: { period: 20, stdDev: 2 },
    placement: 'overlay',
    paramDefs: [
      { key: 'period', label: 'Period', min: 2, max: 500 },
      { key: 'stdDev', label: 'Std Dev', min: 0.5, max: 5, step: 0.5 },
    ],
  },
  {
    id: 'rsi',
    label: 'RSI',
    defaultParams: { period: 14 },
    placement: 'oscillator',
    paramDefs: [{ key: 'period', label: 'Period', min: 2, max: 100 }],
  },
  {
    id: 'macd',
    label: 'MACD',
    defaultParams: { fastPeriod: 12, slowPeriod: 26, signalPeriod: 9 },
    placement: 'oscillator',
    paramDefs: [
      { key: 'fastPeriod', label: 'Fast', min: 2, max: 100 },
      { key: 'slowPeriod', label: 'Slow', min: 2, max: 200 },
      { key: 'signalPeriod', label: 'Signal', min: 2, max: 50 },
    ],
  },
];

// ---------------------------------------------------------------------------
// Simple Moving Average (SMA / MA)
// ---------------------------------------------------------------------------

export function calcMA(closes: number[], period: number): (number | null)[] {
  return closes.map((_, i) => {
    if (i < period - 1) return null;
    let sum = 0;
    for (let j = i - period + 1; j <= i; j++) sum += closes[j];
    return sum / period;
  });
}

// ---------------------------------------------------------------------------
// Exponential Moving Average (EMA)
// Seeded with the first SMA, then Wilder-style smoothing k = 2/(period+1).
// ---------------------------------------------------------------------------

export function calcEMA(closes: number[], period: number): (number | null)[] {
  const result: (number | null)[] = new Array(closes.length).fill(null);
  if (closes.length < period) return result;

  const k = 2 / (period + 1);

  let sum = 0;
  for (let i = 0; i < period; i++) sum += closes[i];
  result[period - 1] = sum / period;

  for (let i = period; i < closes.length; i++) {
    result[i] = closes[i] * k + (result[i - 1] as number) * (1 - k);
  }
  return result;
}

// ---------------------------------------------------------------------------
// Relative Strength Index (RSI) — Wilder's smoothing
// ---------------------------------------------------------------------------

export function calcRSI(closes: number[], period: number): (number | null)[] {
  const result: (number | null)[] = new Array(closes.length).fill(null);
  if (closes.length < period + 1) return result;

  let avgGain = 0;
  let avgLoss = 0;
  for (let i = 1; i <= period; i++) {
    const diff = closes[i] - closes[i - 1];
    if (diff > 0) avgGain += diff;
    else avgLoss -= diff;
  }
  avgGain /= period;
  avgLoss /= period;

  result[period] =
    avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);

  for (let i = period + 1; i < closes.length; i++) {
    const diff = closes[i] - closes[i - 1];
    const gain = diff > 0 ? diff : 0;
    const loss = diff < 0 ? -diff : 0;
    avgGain = (avgGain * (period - 1) + gain) / period;
    avgLoss = (avgLoss * (period - 1) + loss) / period;
    result[i] =
      avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
  }

  return result;
}

// ---------------------------------------------------------------------------
// Bollinger Bands
// ---------------------------------------------------------------------------

export interface BBResult {
  upper: (number | null)[];
  mid: (number | null)[];
  lower: (number | null)[];
}

export function calcBB(closes: number[], period: number, stdDev: number): BBResult {
  const mid = calcMA(closes, period);
  const upper: (number | null)[] = new Array(closes.length).fill(null);
  const lower: (number | null)[] = new Array(closes.length).fill(null);

  for (let i = period - 1; i < closes.length; i++) {
    const slice = closes.slice(i - period + 1, i + 1);
    const mean = mid[i] as number;
    const variance = slice.reduce((s, v) => s + (v - mean) ** 2, 0) / period;
    const sigma = Math.sqrt(variance);
    upper[i] = mean + stdDev * sigma;
    lower[i] = mean - stdDev * sigma;
  }

  return { upper, mid, lower };
}

// ---------------------------------------------------------------------------
// MACD — Moving Average Convergence Divergence
// ---------------------------------------------------------------------------

export interface MACDResult {
  macd: (number | null)[];
  signal: (number | null)[];
  hist: (number | null)[];
}

export function calcMACD(
  closes: number[],
  fastPeriod: number,
  slowPeriod: number,
  signalPeriod: number,
): MACDResult {
  const fast = calcEMA(closes, fastPeriod);
  const slow = calcEMA(closes, slowPeriod);

  const macdLine: (number | null)[] = closes.map((_, i) => {
    if (fast[i] === null || slow[i] === null) return null;
    return (fast[i] as number) - (slow[i] as number);
  });

  // EMA of macdLine for signal line
  const signal: (number | null)[] = new Array(closes.length).fill(null);
  const hist: (number | null)[] = new Array(closes.length).fill(null);

  // Find first non-null macd value index
  const macdStart = macdLine.findIndex((v) => v !== null);
  if (macdStart === -1 || closes.length - macdStart < signalPeriod) {
    return { macd: macdLine, signal, hist };
  }

  // Seed signal EMA with first SMA of macdLine values
  const seedEnd = macdStart + signalPeriod - 1;
  if (seedEnd >= closes.length) return { macd: macdLine, signal, hist };

  let seedSum = 0;
  for (let i = macdStart; i <= seedEnd; i++) seedSum += macdLine[i] as number;
  signal[seedEnd] = seedSum / signalPeriod;
  hist[seedEnd] = (macdLine[seedEnd] as number) - (signal[seedEnd] as number);

  const k = 2 / (signalPeriod + 1);
  for (let i = seedEnd + 1; i < closes.length; i++) {
    if (macdLine[i] === null) break;
    signal[i] = (macdLine[i] as number) * k + (signal[i - 1] as number) * (1 - k);
    hist[i] = (macdLine[i] as number) - (signal[i] as number);
  }

  return { macd: macdLine, signal, hist };
}
