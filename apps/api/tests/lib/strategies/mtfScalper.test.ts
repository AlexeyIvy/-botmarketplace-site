/**
 * MTF Confluence Scalper — golden DSL pin (docs/54-T2, helper-extracted under 54-T5).
 *
 * Shared contract checks (seed/golden pin, validateDsl, parseDsl smoke,
 * supported-primitives) come from `describeGoldenStrategyContract`.
 * Strategy-specific assertions inline:
 *
 *   - parseDsl exit shape — `atr_multiple` SL, `fixed_pct` TP, `gt`
 *     indicatorExit. Drift in any of these would change behaviour.
 *   - Sanity evaluator on a synthetic {M1, M5, M15} bundle:
 *       * Three-way confluence (M15 EMA50>EMA200, M5 close>VWAP, M1
 *         RSI(3)<30 oversold dip) → entry fires.
 *       * M15 downtrend (EMA50<EMA200) → no entry even if M1/M5 align.
 *       * Calm baseline (no trend, RSI ≈ 50) → no entry.
 *
 * Walk-forward acceptance, demo smoke, profile-check (54-T2 §2/§3/§4)
 * need real data and a live runtime — out of scope here.
 */

import { describe, it, expect } from "vitest";
import { fileURLToPath } from "node:url";
import { dirname } from "node:path";
import {
  evaluateSignal,
  parseDsl,
  createIndicatorCache,
  type DslSignal,
  type RuntimeMtfContext,
} from "../../../src/lib/dslEvaluator.js";
import {
  createCandleBundle,
  INTERVAL_MS,
  type Interval,
  type MtfCandle,
} from "../../../src/lib/mtf/intervalAlignment.js";
import { createMtfCache } from "../../../src/lib/mtf/mtfIndicatorResolver.js";
import {
  describeGoldenStrategyContract,
  describeWalkForwardSmoke,
} from "../../_helpers/strategyAcceptance.js";

// ---------------------------------------------------------------------------
// Shared contract — seed/golden pin, validateDsl, parseDsl, supported blocks
// ---------------------------------------------------------------------------

const { golden: goldenDsl } = describeGoldenStrategyContract({
  slug: "mtf-scalper",
  baseDir: dirname(fileURLToPath(import.meta.url)),
  goldenPath: "../../fixtures/strategies/mtf-scalper.golden.json",
  seedPath: "../../../prisma/seed/presets/mtf-scalper.json",
});

// ---------------------------------------------------------------------------
// Walk-forward smoke — bundle {M1, M5, M15}, primary M1
// ---------------------------------------------------------------------------

describeWalkForwardSmoke({
  slug: "mtf-scalper",
  goldenDsl,
  primaryInterval: "1m",
  contextIntervals: ["5m", "15m"],
});

// ---------------------------------------------------------------------------
// Strategy-specific: exit shape pin
// ---------------------------------------------------------------------------

describe("mtf-scalper — exit shape", () => {
  it("parseDsl yields atr_multiple SL, fixed_pct TP, gt indicatorExit", () => {
    const parsed = parseDsl(goldenDsl);
    expect(parsed.exit?.stopLoss?.type).toBe("atr_multiple");
    expect(parsed.exit?.takeProfit?.type).toBe("fixed_pct");
    expect(parsed.exit?.indicatorExit?.condition.op).toBe("gt");
  });
});

// ---------------------------------------------------------------------------
// Strategy-specific: sanity evaluator on a synthetic {M1, M5, M15} bundle
// ---------------------------------------------------------------------------

const t0 = Date.UTC(2026, 0, 1, 0, 0, 0);

function makeCandles(
  count: number,
  intervalMs: number,
  closeFn: (i: number) => number,
): MtfCandle[] {
  return Array.from({ length: count }, (_, i) => {
    const close = closeFn(i);
    return {
      openTime: t0 + i * intervalMs,
      open: close - 0.05,
      high: close + 0.5,
      low: close - 0.5,
      close,
      volume: 100,
    };
  });
}

function makeMtfCtx(
  m1: MtfCandle[], m5: MtfCandle[], m15: MtfCandle[],
): RuntimeMtfContext {
  const bundle = createCandleBundle("1m" as Interval, {
    "1m": m1, "5m": m5, "15m": m15,
  });
  return { bundle, mtfCache: createMtfCache() };
}

function fires(m1: MtfCandle[], m5: MtfCandle[], m15: MtfCandle[]): boolean {
  const parsed = parseDsl(goldenDsl);
  const ctx = makeMtfCtx(m1, m5, m15);
  return evaluateSignal(
    parsed.entry.signal as DslSignal,
    m1.length - 1,
    m1,
    createIndicatorCache(),
    0,
    ctx,
  );
}

describe("mtf-scalper — sanity evaluator", () => {
  it("three-way confluence: M15 uptrend + M5 above VWAP + M1 RSI(3)<30 dip → fires", () => {
    // M15 needs ≥ 200 bars after the EMA(200) warm-up. m1Count=3500 →
    // primary openTime = 3499*60s ≈ 58.3h → M15 idx ≈ 233. Good.
    const m1Count = 3500;
    const m1 = makeCandles(m1Count, INTERVAL_MS["1m"], (i) => {
      // Steady uptrend with a sharp last-bars dip on M1 to push RSI(3)
      // below 30 right at the primary's most recent bar.
      if (i < m1Count - 6) return 100 + i * 0.005;
      return 100 + (m1Count - 6) * 0.005 - (i - (m1Count - 6)) * 0.5;
    });
    const m5 = makeCandles(700, INTERVAL_MS["5m"], (i) => 100 + i * 0.025);
    const m15 = makeCandles(240, INTERVAL_MS["15m"], (i) => 100 + i * 0.07);
    expect(fires(m1, m5, m15)).toBe(true);
  });

  it("M15 downtrend (EMA50 < EMA200) → no entry even if M1/M5 align", () => {
    const m1Count = 3500;
    const m1 = makeCandles(m1Count, INTERVAL_MS["1m"], (i) =>
      i < m1Count - 6 ? 100 + i * 0.005 : 100 + (m1Count - 6) * 0.005 - (i - (m1Count - 6)) * 0.5
    );
    const m5 = makeCandles(700, INTERVAL_MS["5m"], (i) => 100 + i * 0.025);
    // M15 series: long flat then sharp drop in the second half so the
    // recent EMA(50) sits below the slower EMA(200).
    const m15 = makeCandles(240, INTERVAL_MS["15m"], (i) => (i < 100 ? 200 : 200 - (i - 100) * 0.4));
    expect(fires(m1, m5, m15)).toBe(false);
  });

  it("calm baseline: flat across all three TFs → no entry", () => {
    const m1 = makeCandles(3500, INTERVAL_MS["1m"], () => 100);
    const m5 = makeCandles(700, INTERVAL_MS["5m"], () => 100);
    const m15 = makeCandles(240, INTERVAL_MS["15m"], () => 100);
    expect(fires(m1, m5, m15)).toBe(false);
  });
});
