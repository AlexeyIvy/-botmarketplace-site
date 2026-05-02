/**
 * DCA Momentum — golden DSL pin (docs/54-T1, partial 54-T5).
 *
 * Mirrors tests/lib/strategies/adaptiveRegime.test.ts:
 *
 *   1. Seed/golden pin — preset's `dslJson` is byte-equal to the golden.
 *   2. Schema + parse smoke — validateDsl passes, parseDsl yields a
 *      v2-shaped ParsedDsl with the DCA section populated.
 *   3. No composite types — every `blockType` is supported (or a
 *      structural keyword) in BLOCK_SUPPORT_MAP.
 *   4. DCA exposure stays within risk.maxPositionSizeUsd — uses the
 *      production planner so any drift in dcaPlanning is caught here.
 *   5. Sanity evaluator on synthetic single-TF M15 candles:
 *      - Oversold pullback (RSI<40, EMA8<EMA21) → entry fires.
 *      - Strong uptrend (RSI≈70, EMA8>EMA21) → no entry.
 *
 * Walk-forward acceptance and demo smoke (54-T1 §2/§3) need real data
 * and Bybit credentials — not exercised here.
 */

import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import {
  evaluateSignal,
  parseDsl,
  createIndicatorCache,
  type DslSignal,
} from "../../../src/lib/dslEvaluator.js";
import { validateDsl } from "../../../src/lib/dslValidator.js";
import {
  generateSafetyOrderSchedule,
  type DcaConfig,
} from "../../../src/lib/dcaPlanning.js";
import { BLOCK_SUPPORT_MAP } from "../../../src/lib/compiler/supportMap.ts";

// ---------------------------------------------------------------------------
// Fixture / seed loading
// ---------------------------------------------------------------------------

const here = dirname(fileURLToPath(import.meta.url));

function loadJson(rel: string): unknown {
  return JSON.parse(readFileSync(join(here, rel), "utf8"));
}

const goldenDsl = loadJson("../../fixtures/strategies/dca-momentum.golden.json") as Record<string, unknown>;
const seed = loadJson("../../../prisma/seed/presets/dca-momentum.json") as { dslJson: unknown };

// ---------------------------------------------------------------------------
// 1. Seed ⇄ golden pin
// ---------------------------------------------------------------------------

describe("dca-momentum — seed/golden pin", () => {
  it("seed.dslJson is byte-equal to the golden fixture", () => {
    expect(seed.dslJson).toEqual(goldenDsl);
  });
});

// ---------------------------------------------------------------------------
// 2. Schema + parse smoke
// ---------------------------------------------------------------------------

describe("dca-momentum — DSL validity", () => {
  it("validates against the v2 strategy schema", () => {
    const errors = validateDsl(goldenDsl);
    expect(errors).toBeNull();
  });

  it("parseDsl yields a v2-shaped ParsedDsl with DCA + exit configured", () => {
    const parsed = parseDsl(goldenDsl);
    expect(parsed.dslVersion).toBe(2);
    expect(parsed.entry.signal).toBeDefined();
    expect(parsed.exit?.stopLoss?.type).toBe("fixed_pct");
    expect(parsed.exit?.takeProfit?.type).toBe("fixed_pct");
    expect(parsed.exit?.indicatorExit?.condition.op).toBe("gt");
    expect(parsed.dca?.maxSafetyOrders).toBe(5);
    expect(parsed.dca?.priceStepPct).toBeCloseTo(1.2, 5);
  });
});

// ---------------------------------------------------------------------------
// 3. No composite types — every block in BLOCK_SUPPORT_MAP, supported
// ---------------------------------------------------------------------------

function collectIndicatorBlockTypes(node: unknown, out = new Set<string>()): Set<string> {
  if (Array.isArray(node)) {
    for (const item of node) collectIndicatorBlockTypes(item, out);
    return out;
  }
  if (node && typeof node === "object") {
    const obj = node as Record<string, unknown>;
    if (typeof obj.blockType === "string") out.add(obj.blockType);
    if (typeof obj.type === "string") out.add(obj.type);
    for (const v of Object.values(obj)) collectIndicatorBlockTypes(v, out);
  }
  return out;
}

const STRUCTURAL_TYPES = new Set([
  "or", "and", "compare", "crossover", "crossunder", "confirm_n_bars",
  "fixed_pct", "fixed_price", "atr_multiple",
]);

const SUPPORT_ALIASES: Record<string, string> = {
  ema: "EMA", rsi: "RSI", sma: "SMA",
  bollinger: "bollinger",
  bollinger_lower: "bollinger", bollinger_upper: "bollinger", bollinger_middle: "bollinger",
  bb_lower: "bollinger", bb_upper: "bollinger", bb_middle: "bollinger",
};

describe("dca-momentum — uses only supported primitives", () => {
  it("every indicator/block referenced is `supported` in BLOCK_SUPPORT_MAP", () => {
    const types = collectIndicatorBlockTypes(goldenDsl);
    const offenders: Array<{ name: string; reason: string }> = [];

    for (const raw of types) {
      if (STRUCTURAL_TYPES.has(raw)) continue;
      const canonical = SUPPORT_ALIASES[raw] ?? raw;
      const entry = BLOCK_SUPPORT_MAP[canonical];
      if (!entry) {
        offenders.push({ name: raw, reason: `not in BLOCK_SUPPORT_MAP (looked up as "${canonical}")` });
        continue;
      }
      if (entry.status !== "supported") {
        offenders.push({ name: raw, reason: `status is "${entry.status}", expected "supported"` });
      }
    }
    expect(offenders).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// 4. DCA ladder fits inside risk.maxPositionSizeUsd
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
// 5. Sanity evaluator on synthetic M15 candles (single-TF — no bundle)
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
