/**
 * MTF Confluence Scalper — golden DSL pin (docs/54-T2, partial 54-T5).
 *
 * Mirrors tests/lib/strategies/{adaptiveRegime,dcaMomentum}.test.ts:
 *
 *   1. Seed/golden pin — preset's `dslJson` is byte-equal to the golden.
 *   2. Schema + parse smoke — validateDsl passes, parseDsl yields a
 *      v2-shaped ParsedDsl with ATR-based stop and indicatorExit.
 *   3. No composite types — every `blockType` is supported (or a
 *      structural keyword) in BLOCK_SUPPORT_MAP. `vwap` block is on
 *      the supported list.
 *   4. Sanity evaluator on a synthetic {M1, M5, M15} bundle:
 *      - Three-way confluence (M15 EMA50>EMA200, M5 close>VWAP, M1
 *        RSI(3)<30 oversold dip) → entry fires.
 *      - M15 downtrend (EMA50<EMA200) → no entry.
 *      - Calm baseline (no trend, RSI ≈ 50) → no entry.
 *
 * Walk-forward acceptance, demo smoke, profile-check (54-T2 §2/§3/§4)
 * need real data and a live runtime — out of scope here.
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
  type RuntimeMtfContext,
} from "../../../src/lib/dslEvaluator.js";
import { validateDsl } from "../../../src/lib/dslValidator.js";
import {
  createCandleBundle,
  INTERVAL_MS,
  type Interval,
  type MtfCandle,
} from "../../../src/lib/mtf/intervalAlignment.js";
import { createMtfCache } from "../../../src/lib/mtf/mtfIndicatorResolver.js";
import { BLOCK_SUPPORT_MAP } from "../../../src/lib/compiler/supportMap.ts";

// ---------------------------------------------------------------------------
// Fixture / seed loading
// ---------------------------------------------------------------------------

const here = dirname(fileURLToPath(import.meta.url));
const loadJson = (rel: string): unknown => JSON.parse(readFileSync(join(here, rel), "utf8"));

const goldenDsl = loadJson("../../fixtures/strategies/mtf-scalper.golden.json") as Record<string, unknown>;
const seed = loadJson("../../../prisma/seed/presets/mtf-scalper.json") as { dslJson: unknown };

// ---------------------------------------------------------------------------
// 1. Seed ⇄ golden pin
// ---------------------------------------------------------------------------

describe("mtf-scalper — seed/golden pin", () => {
  it("seed.dslJson is byte-equal to the golden fixture", () => {
    expect(seed.dslJson).toEqual(goldenDsl);
  });
});

// ---------------------------------------------------------------------------
// 2. Schema + parse smoke
// ---------------------------------------------------------------------------

describe("mtf-scalper — DSL validity", () => {
  it("validates against the v2 strategy schema", () => {
    const errors = validateDsl(goldenDsl);
    expect(errors).toBeNull();
  });

  it("parseDsl yields a v2-shaped ParsedDsl with ATR stop + indicatorExit", () => {
    const parsed = parseDsl(goldenDsl);
    expect(parsed.dslVersion).toBe(2);
    expect(parsed.entry.signal).toBeDefined();
    expect(parsed.exit?.stopLoss?.type).toBe("atr_multiple");
    expect(parsed.exit?.takeProfit?.type).toBe("fixed_pct");
    expect(parsed.exit?.indicatorExit?.condition.op).toBe("gt");
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

describe("mtf-scalper — uses only supported primitives", () => {
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
// 4. Sanity evaluator on a synthetic {M1, M5, M15} bundle
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
