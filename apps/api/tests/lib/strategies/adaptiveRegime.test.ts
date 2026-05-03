/**
 * Adaptive Regime — golden DSL pin (docs/53-T1 + 53-T6, 54-T5 helper extraction).
 *
 * The golden fixture is the single source of truth for the
 * `adaptive-regime` preset. The four shared contract checks (seed/golden
 * pin, DSL validity, parseDsl smoke, supported-primitives) are
 * registered via `describeGoldenStrategyContract` (54-T5). The two
 * strategy-specific assertions remain inline:
 *
 *   - parseDsl returns the expected exit shape (`atr_multiple` SL,
 *     `fixed_pct` TP) — drift in either type would be a real preset
 *     change masquerading as a refactor.
 *   - Sanity-evaluator on a synthetic {M5, H1} bundle:
 *       * Trend-up branch fires when EMA50(H1) > EMA200(H1), supertrend(M5) > 0,
 *         ADX(H1) > 20.
 *       * Mean-reversion branch fires when RSI(M5) < 30 and ADX(H1) < 20.
 *       * Calm baseline fires neither.
 *
 * Acceptance gate (full walk-forward on real data) lives in docs/53-T2.
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
  slug: "adaptive-regime",
  baseDir: dirname(fileURLToPath(import.meta.url)),
  goldenPath: "../../fixtures/strategies/adaptive-regime.golden.json",
  seedPath: "../../../prisma/seed/presets/adaptive-regime.json",
});

// ---------------------------------------------------------------------------
// Walk-forward smoke — bundle {M5, H1}, primary M5
// ---------------------------------------------------------------------------

describeWalkForwardSmoke({
  slug: "adaptive-regime",
  goldenDsl,
  primaryInterval: "5m",
  contextIntervals: ["1h"],
});

// ---------------------------------------------------------------------------
// Strategy-specific: exit shape pin
// ---------------------------------------------------------------------------

describe("adaptive-regime — exit shape", () => {
  it("parseDsl yields atr_multiple stopLoss + fixed_pct takeProfit", () => {
    const parsed = parseDsl(goldenDsl);
    expect(parsed.exit?.stopLoss?.type).toBe("atr_multiple");
    expect(parsed.exit?.takeProfit?.type).toBe("fixed_pct");
  });
});

// ---------------------------------------------------------------------------
// Strategy-specific: sanity evaluator on a synthetic {M5, H1} bundle
// ---------------------------------------------------------------------------

const t0 = Date.UTC(2026, 0, 1, 0, 0, 0);

/** Build M5 candles with a closed-form `closeFn(i)`; OHLC is symmetric
 *  around the close so the synthetic series stays simple to reason about. */
function makeM5(count: number, closeFn: (i: number) => number): MtfCandle[] {
  return Array.from({ length: count }, (_, i) => {
    const close = closeFn(i);
    return {
      openTime: t0 + i * INTERVAL_MS["5m"],
      open: close - 0.05,
      high: close + 0.5,
      low: close - 0.5,
      close,
      volume: 10,
    };
  });
}

function makeH1(count: number, closeFn: (i: number) => number): MtfCandle[] {
  return Array.from({ length: count }, (_, i) => {
    const close = closeFn(i);
    return {
      openTime: t0 + i * INTERVAL_MS["1h"],
      open: close - 0.5,
      high: close + 1,
      low: close - 1,
      close,
      volume: 100,
    };
  });
}

function makeMtfCtx(m5: MtfCandle[], h1: MtfCandle[]): RuntimeMtfContext {
  const bundle = createCandleBundle("5m" as Interval, { "5m": m5, "1h": h1 });
  return { bundle, mtfCache: createMtfCache() };
}

/** Evaluate the golden DSL's entry.signal at the latest primary bar. */
function fires(m5: MtfCandle[], h1: MtfCandle[]): boolean {
  const parsed = parseDsl(goldenDsl);
  const ctx = makeMtfCtx(m5, h1);
  return evaluateSignal(
    parsed.entry.signal as DslSignal,
    m5.length - 1,
    m5,
    createIndicatorCache(),
    0,
    ctx,
  );
}

describe("adaptive-regime — sanity evaluator", () => {
  it("trend branch: H1 strong uptrend + supertrend(M5) > 0 + ADX(H1) > 20 → fires", () => {
    // Need enough H1 bars for EMA(200) + ADX(14) to warm up at the
    // primary's last bar. Primary openTime = (m5Count-1) * 5min, so an
    // M5 series of 3600 bars maps to H1 ≈ 299 — comfortably past the
    // EMA(200) warm-up boundary.
    const m5 = makeM5(3600, (i) => 100 + i * 0.05);
    const h1 = makeH1(300, (i) => 100 + i * 0.5);
    expect(fires(m5, h1)).toBe(true);
  });

  it("flat regime: RSI(M5) < 30 + ADX(H1) < 20 → fires (mean-reversion branch)", () => {
    // Long flat at 100 followed by a sharp drop in the last ~25 bars
    // to push RSI(14) below 30. H1 stays dead-flat so ADX never
    // crosses 20 — only the mean-reversion branch should match.
    const m5 = makeM5(400, (i) => (i < 375 ? 100 : 100 - (i - 375) * 0.5));
    const h1 = makeH1(120, () => 100);
    expect(fires(m5, h1)).toBe(true);
  });

  it("calm baseline: neither branch fires (RSI ≈ 50, ADX flat, no trend)", () => {
    const m5 = makeM5(400, () => 100);
    const h1 = makeH1(120, () => 100);
    expect(fires(m5, h1)).toBe(false);
  });
});
