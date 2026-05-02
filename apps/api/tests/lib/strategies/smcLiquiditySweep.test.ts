/**
 * SMC Liquidity Sweep — golden DSL pin (docs/54-T3, partial 54-T5).
 *
 * Mirrors tests/lib/strategies/{adaptiveRegime,dcaMomentum,mtfScalper}.test.ts.
 *
 *   1. Seed/golden pin — preset's `dslJson` is byte-equal to the golden.
 *   2. Schema + parse smoke — validateDsl passes, parseDsl yields a
 *      v2-shaped ParsedDsl with ATR-based stop and pattern-based signal.
 *   3. No composite types — every `blockType` (including the SMC pattern
 *      blocks `liquidity_sweep`, `market_structure_shift`) is `supported`
 *      in BLOCK_SUPPORT_MAP.
 *   4. Sanity evaluator (negative cases only — pattern-positive fixtures
 *      are deferred to docs/54-T3 §4):
 *      - Calm/flat bundle across all three TFs → no entry; pattern
 *        blocks legitimately produce zeros, AND-gate stays false.
 *      - H4 downtrend (EMA50 < EMA200) → HTF bias filter blocks even
 *        if the lower-TF patterns happened to fire.
 *      - Pattern blocks resolve through the bundle without throwing
 *        — exercises the runtime evaluator's MTF integration end-to-end
 *        for SMC-pattern refs (their first appearance via DslSignalRef
 *        with sourceTimeframe).
 *
 * Walk-forward acceptance, demo smoke, and the `pattern engine sanity`
 * fixture (54-T3 §4) need real data and known-sweep candle sequences —
 * out of scope here.
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

const goldenDsl = loadJson("../../fixtures/strategies/smc-liquidity-sweep.golden.json") as Record<string, unknown>;
const seed = loadJson("../../../prisma/seed/presets/smc-liquidity-sweep.json") as { dslJson: unknown };

// ---------------------------------------------------------------------------
// 1. Seed ⇄ golden pin
// ---------------------------------------------------------------------------

describe("smc-liquidity-sweep — seed/golden pin", () => {
  it("seed.dslJson is byte-equal to the golden fixture", () => {
    expect(seed.dslJson).toEqual(goldenDsl);
  });
});

// ---------------------------------------------------------------------------
// 2. Schema + parse smoke
// ---------------------------------------------------------------------------

describe("smc-liquidity-sweep — DSL validity", () => {
  it("validates against the v2 strategy schema", () => {
    const errors = validateDsl(goldenDsl);
    expect(errors).toBeNull();
  });

  it("parseDsl yields a v2-shaped ParsedDsl with pattern-based signal + ATR exit", () => {
    const parsed = parseDsl(goldenDsl);
    expect(parsed.dslVersion).toBe(2);
    expect(parsed.entry.signal).toBeDefined();
    expect(parsed.exit?.stopLoss?.type).toBe("atr_multiple");
    expect(parsed.exit?.takeProfit?.type).toBe("fixed_pct");
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

describe("smc-liquidity-sweep — uses only supported primitives", () => {
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
// 4. Sanity evaluator on a synthetic {M15, H1, H4} bundle
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
  m15: MtfCandle[], h1: MtfCandle[], h4: MtfCandle[],
): RuntimeMtfContext {
  const bundle = createCandleBundle("15m" as Interval, {
    "15m": m15, "1h": h1, "4h": h4,
  });
  return { bundle, mtfCache: createMtfCache() };
}

function fires(m15: MtfCandle[], h1: MtfCandle[], h4: MtfCandle[]): boolean {
  const parsed = parseDsl(goldenDsl);
  const ctx = makeMtfCtx(m15, h1, h4);
  return evaluateSignal(
    parsed.entry.signal as DslSignal,
    m15.length - 1,
    m15,
    createIndicatorCache(),
    0,
    ctx,
  );
}

describe("smc-liquidity-sweep — sanity evaluator (negative cases)", () => {
  // M15 needs 800+ bars so the H4 EMA(200) warm-up clears at the
  // primary's last bar: 800 * 15min = 12000min = 200h ⇒ H4 idx ≈ 50;
  // bump M15 = 3300 → H4 idx ≈ 206 (post-warmup).
  const M15_COUNT = 3300;
  const H1_COUNT = 825;
  const H4_COUNT = 220;

  it("calm/flat bundle across all three TFs → no entry (patterns inactive)", () => {
    const m15 = makeCandles(M15_COUNT, INTERVAL_MS["15m"], () => 100);
    const h1 = makeCandles(H1_COUNT, INTERVAL_MS["1h"], () => 100);
    const h4 = makeCandles(H4_COUNT, INTERVAL_MS["4h"], () => 100);
    expect(fires(m15, h1, h4)).toBe(false);
  });

  it("H4 downtrend (EMA50 < EMA200) blocks even if patterns would fire", () => {
    const m15 = makeCandles(M15_COUNT, INTERVAL_MS["15m"], (i) => 100 + Math.sin(i * 0.3) * 5);
    const h1 = makeCandles(H1_COUNT, INTERVAL_MS["1h"], (i) => 100 + Math.sin(i * 0.2) * 4);
    // H4 long flat then sustained drop in the second half so the
    // recent EMA(50) sits below the slower EMA(200).
    const h4 = makeCandles(H4_COUNT, INTERVAL_MS["4h"], (i) => (i < 110 ? 200 : 200 - (i - 110) * 0.4));
    expect(fires(m15, h1, h4)).toBe(false);
  });

  it("pattern blocks resolve through the bundle without throwing on noisy data", () => {
    // Just ensure the full evaluator path runs to completion — pattern
    // blocks via DslSignalRef with sourceTimeframe must round-trip
    // through resolveMtfIndicator without errors. The signal value
    // (true / false) is not asserted here.
    const m15 = makeCandles(M15_COUNT, INTERVAL_MS["15m"], (i) => 100 + Math.sin(i * 0.05) * 3);
    const h1 = makeCandles(H1_COUNT, INTERVAL_MS["1h"], (i) => 100 + Math.cos(i * 0.07) * 4);
    const h4 = makeCandles(H4_COUNT, INTERVAL_MS["4h"], (i) => 100 + i * 0.03);
    expect(() => fires(m15, h1, h4)).not.toThrow();
  });
});
