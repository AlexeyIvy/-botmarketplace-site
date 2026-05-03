/**
 * DCA Momentum — golden DSL pin (docs/54-T1, helper-extracted under 54-T5).
 *
 * Shared contract checks (seed/golden pin, validateDsl, parseDsl smoke,
 * supported-primitives) come from `describeGoldenStrategyContract`.
 * Strategy-specific assertions inline:
 *
 *   - Deep parseDsl shape — DCA section + indicatorExit + fixed_pct
 *     stopLoss + takeProfit. Drift in any of these would change the
 *     preset's behaviour, not just style.
 *   - DCA exposure stays within `risk.maxPositionSizeUsd` — uses the
 *     production planner so any drift in dcaPlanning is caught here.
 *   - Sanity evaluator on synthetic single-TF M15 candles:
 *       * Oversold pullback (RSI<40, EMA8<EMA21) → entry fires.
 *       * Strong uptrend (RSI≈70, EMA8>EMA21) → no entry.
 *
 * Walk-forward acceptance and demo smoke (54-T1 §2/§3) need real data
 * and Bybit credentials — not exercised here.
 */

import { describe, it, expect } from "vitest";
import { fileURLToPath } from "node:url";
import { dirname } from "node:path";
import {
  evaluateSignal,
  parseDsl,
  createIndicatorCache,
  type DslSignal,
} from "../../../src/lib/dslEvaluator.js";
import {
  generateSafetyOrderSchedule,
  type DcaConfig,
} from "../../../src/lib/dcaPlanning.js";
import {
  describeGoldenStrategyContract,
  describeWalkForwardSmoke,
} from "../../_helpers/strategyAcceptance.js";

// ---------------------------------------------------------------------------
// Shared contract — seed/golden pin, validateDsl, parseDsl, supported blocks
// ---------------------------------------------------------------------------

const { golden: goldenDsl } = describeGoldenStrategyContract({
  slug: "dca-momentum",
  baseDir: dirname(fileURLToPath(import.meta.url)),
  goldenPath: "../../fixtures/strategies/dca-momentum.golden.json",
  seedPath: "../../../prisma/seed/presets/dca-momentum.json",
});

// ---------------------------------------------------------------------------
// Walk-forward smoke — single-TF M15
// ---------------------------------------------------------------------------

describeWalkForwardSmoke({
  slug: "dca-momentum",
  goldenDsl,
  primaryInterval: "15m",
});

// ---------------------------------------------------------------------------
// Strategy-specific: deep parseDsl shape (DCA + exit configured)
// ---------------------------------------------------------------------------

describe("dca-momentum — DCA + exit shape", () => {
  it("parseDsl yields fixed_pct exits, indicatorExit, and the DCA section populated", () => {
    const parsed = parseDsl(goldenDsl);
    expect(parsed.exit?.stopLoss?.type).toBe("fixed_pct");
    expect(parsed.exit?.takeProfit?.type).toBe("fixed_pct");
    expect(parsed.exit?.indicatorExit?.condition.op).toBe("gt");
    expect(parsed.dca?.maxSafetyOrders).toBe(5);
    expect(parsed.dca?.priceStepPct).toBeCloseTo(1.2, 5);
  });
});

// ---------------------------------------------------------------------------
// Strategy-specific: DCA ladder fits inside risk.maxPositionSizeUsd
// ---------------------------------------------------------------------------

describe("dca-momentum — DCA exposure inside risk cap", () => {
  it("planner-produced ladder total notional ≤ risk.maxPositionSizeUsd", () => {
    const dsl = goldenDsl as Record<string, unknown>;
    const dca = dsl.dca as DcaConfig;
    const risk = dsl.risk as { maxPositionSizeUsd: number };

    // Plan around an arbitrary entry price — proportions are
    // price-invariant, so the bound holds regardless of entry.
    const schedule = generateSafetyOrderSchedule(dca, 100, "long");
    expect(schedule.totalCapitalUsd).toBeLessThanOrEqual(risk.maxPositionSizeUsd);
  });
});

// ---------------------------------------------------------------------------
// Strategy-specific: sanity evaluator on synthetic M15 candles
// ---------------------------------------------------------------------------

interface Candle {
  openTime: number; open: number; high: number; low: number; close: number; volume: number;
}

const M15_MS = 900_000;
const t0 = Date.UTC(2026, 0, 1, 0, 0, 0);

function makeCandles(count: number, closeFn: (i: number) => number): Candle[] {
  return Array.from({ length: count }, (_, i) => {
    const close = closeFn(i);
    return {
      openTime: t0 + i * M15_MS,
      open: close - 0.05,
      high: close + 0.5,
      low: close - 0.5,
      close,
      volume: 100,
    };
  });
}

function fires(candles: Candle[]): boolean {
  const parsed = parseDsl(goldenDsl);
  return evaluateSignal(
    parsed.entry.signal as DslSignal,
    candles.length - 1,
    candles,
    createIndicatorCache(),
  );
}

describe("dca-momentum — sanity evaluator", () => {
  it("oversold pullback (RSI<40, EMA8<EMA21) → entry fires", () => {
    // Long upward run followed by a sustained dip pushes both RSI
    // below 40 and the short EMA below the medium EMA.
    const candles = makeCandles(400, (i) => (i < 350 ? 100 + i * 0.2 : 170 - (i - 350) * 1.5));
    expect(fires(candles)).toBe(true);
  });

  it("strong uptrend (RSI ≈ 70+, EMA8 > EMA21) → no entry", () => {
    const candles = makeCandles(400, (i) => 100 + i * 0.5);
    expect(fires(candles)).toBe(false);
  });
});
