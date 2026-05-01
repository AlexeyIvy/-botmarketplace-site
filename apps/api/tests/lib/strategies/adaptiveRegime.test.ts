/**
 * Adaptive Regime — golden DSL pin (docs/53-T1 + 53-T6).
 *
 * The golden fixture is the single source of truth for the
 * `adaptive-regime` preset. Tests here lock down four invariants:
 *
 *   1. The seed file's `dslJson` and the golden fixture stay byte-equal —
 *      any change to the preset must be a deliberate update of the
 *      golden, not an accidental drift.
 *   2. The golden DSL is structurally valid against the v2 schema
 *      (`validateDsl`) and parses cleanly via `parseDsl`.
 *   3. Every block referenced by the golden is in {@link BLOCK_SUPPORT_MAP}
 *      with status `supported`. No "composite signal types" sneak in —
 *      the strategy must be expressible through primitives, per
 *      docs/50 §Решение 3 / docs/53 §Решение 1.
 *   4. Sanity-evaluator on a synthetic {M5, H1} bundle:
 *      - Trend-up branch fires when EMA50(H1) > EMA200(H1), supertrend(M5) > 0,
 *        ADX(H1) > 20.
 *      - Mean-reversion branch fires when RSI(M5) < 30 and ADX(H1) < 20.
 *      - Neither fires on a calm baseline (RSI ≈ 50, ADX flat).
 *
 * The acceptance gate (full walk-forward on real data) lives in
 * docs/53-T2 — that needs market data and is out of scope here.
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

function loadJson(rel: string): unknown {
  const abs = join(here, rel);
  return JSON.parse(readFileSync(abs, "utf8"));
}

const goldenDsl = loadJson("../../fixtures/strategies/adaptive-regime.golden.json") as Record<string, unknown>;
const seed = loadJson("../../../prisma/seed/presets/adaptive-regime.json") as { dslJson: unknown };

// ---------------------------------------------------------------------------
// 1. Seed ⇄ golden pin
// ---------------------------------------------------------------------------

describe("adaptive-regime — seed/golden pin", () => {
  it("seed.dslJson is byte-equal to the golden fixture", () => {
    expect(seed.dslJson).toEqual(goldenDsl);
  });
});

// ---------------------------------------------------------------------------
// 2. Schema + parse smoke
// ---------------------------------------------------------------------------

describe("adaptive-regime — DSL validity", () => {
  it("validates against the v2 strategy schema", () => {
    const errors = validateDsl(goldenDsl);
    expect(errors).toBeNull();
  });

  it("parseDsl yields a v2-shaped ParsedDsl with non-empty signal/exit", () => {
    const parsed = parseDsl(goldenDsl);
    expect(parsed.dslVersion).toBe(2);
    expect(parsed.entry.signal).toBeDefined();
    expect(parsed.exit?.stopLoss?.type).toBe("atr_multiple");
    expect(parsed.exit?.takeProfit?.type).toBe("fixed_pct");
  });
});

// ---------------------------------------------------------------------------
// 3. No composite types — every block is in BLOCK_SUPPORT_MAP, supported
// ---------------------------------------------------------------------------

/** Recursively collect every `blockType` and `type: "<indicator>"`-style
 *  reference present in the DSL — anything the evaluator will hit on the
 *  hot path needs to be either a structural keyword (compare, and, or,
 *  …) or a supported block. */
function collectIndicatorBlockTypes(node: unknown, out = new Set<string>()): Set<string> {
  if (Array.isArray(node)) {
    for (const item of node) collectIndicatorBlockTypes(item, out);
    return out;
  }
  if (node && typeof node === "object") {
    const obj = node as Record<string, unknown>;
    if (typeof obj.blockType === "string") out.add(obj.blockType);
    // `type` strings appear both as structural keywords (or/and/compare)
    // and as indicator names (atr inside exit.stopLoss). Capture them
    // here and filter the structural ones below.
    if (typeof obj.type === "string") out.add(obj.type);
    for (const v of Object.values(obj)) collectIndicatorBlockTypes(v, out);
  }
  return out;
}

const STRUCTURAL_TYPES = new Set([
  "or", "and", "compare", "crossover", "crossunder", "confirm_n_bars",
  "fixed_pct", "fixed_price", "atr_multiple",
]);

/** Map runtime block-name aliases (lowercase / shorthands) back to the
 *  canonical key in `BLOCK_SUPPORT_MAP`. The evaluator's getIndicatorValues
 *  lower-cases its input, so the seed legitimately uses lowercase names —
 *  the support map keys are case-sensitive. */
const SUPPORT_ALIASES: Record<string, string> = {
  ema:        "EMA",
  rsi:        "RSI",
  sma:        "SMA",
  // bollinger_lower/upper/middle / bb_* all resolve through the
  // `bollinger` runtime entry; treat them as the same supported block.
  bollinger:        "bollinger",
  bollinger_lower:  "bollinger",
  bollinger_upper:  "bollinger",
  bollinger_middle: "bollinger",
  bb_lower:         "bollinger",
  bb_upper:         "bollinger",
  bb_middle:        "bollinger",
};

describe("adaptive-regime — uses only supported primitives", () => {
  it("every indicator/block referenced is `supported` in BLOCK_SUPPORT_MAP", () => {
    const types = collectIndicatorBlockTypes(goldenDsl);
    const offenders: Array<{ name: string; reason: string }> = [];

    for (const raw of types) {
      if (STRUCTURAL_TYPES.has(raw)) continue; // structural keyword, not a block
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
// 4. Sanity evaluator on a synthetic {M5, H1} bundle
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
