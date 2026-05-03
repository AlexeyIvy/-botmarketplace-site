/**
 * Shared contract assertions for flagship preset golden tests (docs/54-T5).
 *
 * Every flagship preset (adaptive-regime, dca-momentum, mtf-scalper,
 * smc-liquidity-sweep, …) has a golden fixture pinned against its seed
 * `dslJson`, and four contract checks are identical across them:
 *
 *   1. seed.dslJson is byte-equal to the golden fixture.
 *   2. validateDsl(golden) returns null (schema-valid).
 *   3. parseDsl(golden) yields dslVersion=2 with a defined entry.signal.
 *   4. Every blockType / type referenced by the golden is `supported`
 *      in BLOCK_SUPPORT_MAP, after structural-keyword + alias normalisation.
 *
 * Strategy-specific assertions (deep parseDsl checks, synthetic-candle
 * sanity-evaluator runs, DCA-exposure planner checks, etc.) stay in the
 * per-strategy test file. The helper covers the four invariants that
 * every preset shares — drift in any of them shouts loudly without the
 * boilerplate being duplicated four ways.
 *
 * Smoke-replay support is intentionally NOT here yet — recording a
 * deterministic JSON of a 30-min Bybit-demo run requires the
 * acceptance-gate paths in docs/53-T3 / docs/54-T1..T3 / docs/55-T6 to
 * have actually run. Those need credentials this repository's CI does
 * not have. The helper will grow a `describeSmokeReplay` once the
 * recordings exist.
 */

import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { MarketCandle } from "@prisma/client";
import { parseDsl } from "../../src/lib/dslEvaluator.js";
import { validateDsl } from "../../src/lib/dslValidator.js";
import { BLOCK_SUPPORT_MAP } from "../../src/lib/compiler/supportMap.ts";
import {
  runWalkForward,
  runWalkForwardWithBundle,
} from "../../src/lib/walkForward/run.js";
import type { FoldConfig } from "../../src/lib/walkForward/types.js";
import type { CandleInterval } from "../../src/types/datasetBundle.js";
import { INTERVAL_MS, type Interval } from "../../src/lib/mtf/intervalAlignment.js";
import type { Candle } from "../../src/lib/bybitCandles.js";

// ---------------------------------------------------------------------------
// Shared keyword + alias tables
// ---------------------------------------------------------------------------

/** DSL nodes whose `type` field is a structural keyword, not a block name. */
export const STRUCTURAL_TYPES = new Set([
  "or",
  "and",
  "compare",
  "crossover",
  "crossunder",
  "confirm_n_bars",
  "fixed_pct",
  "fixed_price",
  "atr_multiple",
]);

/** Lower-case / shorthand block-name aliases → canonical key in
 *  `BLOCK_SUPPORT_MAP`. The runtime evaluator lowercases its input so the
 *  seed legitimately uses lowercase names; the support map keys are
 *  case-sensitive. Add aliases here as new presets land. */
export const SUPPORT_ALIASES: Record<string, string> = {
  ema: "EMA",
  rsi: "RSI",
  sma: "SMA",
  bollinger: "bollinger",
  bollinger_lower: "bollinger",
  bollinger_upper: "bollinger",
  bollinger_middle: "bollinger",
  bb_lower: "bollinger",
  bb_upper: "bollinger",
  bb_middle: "bollinger",
};

// ---------------------------------------------------------------------------
// Golden fixture / seed loading
// ---------------------------------------------------------------------------

export interface GoldenLoadArgs {
  /** Test file's directory — pass `dirname(fileURLToPath(import.meta.url))`. */
  baseDir: string;
  /** Relative path from `baseDir` to the golden JSON fixture. */
  goldenPath: string;
  /** Relative path from `baseDir` to the preset seed JSON. */
  seedPath: string;
}

export interface LoadedGolden {
  golden: Record<string, unknown>;
  seed: { dslJson: unknown };
}

/** Read both fixtures into memory. Used both inside the helper's
 *  describe blocks and returned to the caller so strategy-specific
 *  assertions can reuse the exact same JSON without re-reading. */
export function loadGoldenAndSeed(args: GoldenLoadArgs): LoadedGolden {
  const golden = JSON.parse(
    readFileSync(join(args.baseDir, args.goldenPath), "utf8"),
  ) as Record<string, unknown>;
  const seed = JSON.parse(
    readFileSync(join(args.baseDir, args.seedPath), "utf8"),
  ) as { dslJson: unknown };
  return { golden, seed };
}

// ---------------------------------------------------------------------------
// Block-type collector — recursive walk over the DSL tree
// ---------------------------------------------------------------------------

/**
 * Recursively collect every `blockType` and indicator-style `type` field
 * present in the DSL — anything the evaluator will hit on the hot path
 * needs to be either a structural keyword (compare, and, or, …) or a
 * supported block.
 */
export function collectIndicatorBlockTypes(
  node: unknown,
  out: Set<string> = new Set<string>(),
): Set<string> {
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

// ---------------------------------------------------------------------------
// Public entry point — registers the four contract describes
// ---------------------------------------------------------------------------

export interface DescribeGoldenStrategyArgs extends GoldenLoadArgs {
  /** Preset slug — used as the describe-block prefix. */
  slug: string;
}

/**
 * Register the four shared describe blocks for `slug`.
 *
 * Returns the loaded `{ golden, seed }` so the caller can chain
 * strategy-specific assertions against the exact same JSON without
 * re-reading from disk.
 *
 * Usage:
 *
 * ```ts
 * import { describeGoldenStrategyContract } from "../../_helpers/strategyAcceptance.js";
 *
 * const { golden } = describeGoldenStrategyContract({
 *   slug: "dca-momentum",
 *   baseDir: dirname(fileURLToPath(import.meta.url)),
 *   goldenPath: "../../fixtures/strategies/dca-momentum.golden.json",
 *   seedPath: "../../../prisma/seed/presets/dca-momentum.json",
 * });
 *
 * // Strategy-specific assertions follow:
 * describe("dca-momentum — DCA exposure inside risk cap", () => { … });
 * ```
 */
export function describeGoldenStrategyContract(
  args: DescribeGoldenStrategyArgs,
): LoadedGolden {
  const loaded = loadGoldenAndSeed(args);

  describe(`${args.slug} — seed/golden pin`, () => {
    it("seed.dslJson is byte-equal to the golden fixture", () => {
      expect(loaded.seed.dslJson).toEqual(loaded.golden);
    });
  });

  describe(`${args.slug} — DSL validity`, () => {
    it("validates against the v2 strategy schema", () => {
      expect(validateDsl(loaded.golden)).toBeNull();
    });

    it("parseDsl yields a v2-shaped ParsedDsl", () => {
      const parsed = parseDsl(loaded.golden);
      expect(parsed.dslVersion).toBe(2);
      expect(parsed.entry.signal).toBeDefined();
    });
  });

  describe(`${args.slug} — uses only supported primitives`, () => {
    it("every indicator/block referenced is `supported` in BLOCK_SUPPORT_MAP", () => {
      const types = collectIndicatorBlockTypes(loaded.golden);
      const offenders: Array<{ name: string; reason: string }> = [];

      for (const raw of types) {
        if (STRUCTURAL_TYPES.has(raw)) continue;
        const canonical = SUPPORT_ALIASES[raw] ?? raw;
        const entry = BLOCK_SUPPORT_MAP[canonical];
        if (!entry) {
          offenders.push({
            name: raw,
            reason: `not in BLOCK_SUPPORT_MAP (looked up as "${canonical}")`,
          });
          continue;
        }
        if (entry.status !== "supported") {
          offenders.push({
            name: raw,
            reason: `status is "${entry.status}", expected "supported"`,
          });
        }
      }

      expect(offenders).toEqual([]);
    });
  });

  return loaded;
}

// ---------------------------------------------------------------------------
// Walk-forward smoke (54-T5 — CI sub-fixture)
// ---------------------------------------------------------------------------
//
// `describeGoldenStrategyContract` proves the DSL is structurally valid and
// uses only supported primitives. What it does NOT prove is that the DSL
// actually survives the walk-forward pipeline — split → bundle slicing →
// runBacktest evaluator → aggregate. A regression in any of those layers
// can break a flagship strategy and ship to main without a single existing
// test failing.
//
// `describeWalkForwardSmoke` plugs that gap with a deterministic synthetic
// candle generator. It is intentionally *smoke-grade*: candles are a
// fixed-seed random walk and most strategies will produce zero trades.
// The assertion is "the pipeline ran end-to-end on this golden DSL and
// returned a well-shaped report"; PnL / signal-correctness checks belong
// in the per-strategy synthetic-evaluator tests, not here.

/** Map lowercase DSL-style interval names to the uppercase
 *  `CandleInterval` enum used by `MarketCandle.interval` and bundle keys. */
const LOWER_TO_UPPER: Record<Interval, CandleInterval> = {
  "1m": "M1",
  "5m": "M5",
  "15m": "M15",
  "1h": "H1",
  "4h": "H4",
  "1d": "D1",
};

/** Deterministic LCG — same seed ⇒ same candles across runs / machines.
 *  We cannot use `Math.random()` here because the smoke run must reproduce
 *  bit-for-bit on CI; a flaky walk-forward result would be useless. */
function lcg(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (state * 1103515245 + 12345) & 0x7fffffff;
    return state / 0x7fffffff;
  };
}

/** Build a fresh `MarketCandle[]` for one interval. The price series is a
 *  bounded random walk anchored at `basePrice`; OHLC are derived from the
 *  walk so high ≥ open/close ≥ low always holds. The output mirrors the
 *  shape `runBacktestWithBundle` consumes (Decimal columns are passed as
 *  plain numbers — `toMtfCandle` accepts both via `Number(v.toString())`). */
function generateCandles(args: {
  interval: Interval;
  count: number;
  basePrice?: number;
  seed?: number;
  startMs?: number;
}): MarketCandle[] {
  const upper = LOWER_TO_UPPER[args.interval];
  const ms = INTERVAL_MS[args.interval];
  const start = args.startMs ?? Date.UTC(2026, 0, 1, 0, 0, 0);
  const rand = lcg(args.seed ?? 0xC0FFEE);
  let price = args.basePrice ?? 100;
  const out: MarketCandle[] = [];
  for (let i = 0; i < args.count; i++) {
    // ±0.4% step keeps prices in a sensible band over a few hundred bars
    // and prevents indicator math (e.g. ATR, BB) from collapsing to zero.
    const drift = (rand() - 0.5) * 0.008;
    const open = price;
    price = Math.max(0.01, price * (1 + drift));
    const close = price;
    const high = Math.max(open, close) * (1 + rand() * 0.002);
    const low = Math.min(open, close) * (1 - rand() * 0.002);
    out.push({
      id: `wf-${upper}-${i}`,
      exchange: "bybit",
      symbol: "BTCUSDT",
      interval: upper,
      openTimeMs: BigInt(start + i * ms),
      open: open as unknown as MarketCandle["open"],
      high: high as unknown as MarketCandle["high"],
      low: low as unknown as MarketCandle["low"],
      close: close as unknown as MarketCandle["close"],
      volume: 100 as unknown as MarketCandle["volume"],
      createdAt: new Date(start + i * ms),
    });
  }
  return out;
}

function rowToCandle(row: MarketCandle): Candle {
  return {
    openTime: Number(row.openTimeMs),
    open: Number(row.open),
    high: Number(row.high),
    low: Number(row.low),
    close: Number(row.close),
    volume: Number(row.volume),
  };
}

/** Default fold config sized to the synthetic series below. With 400
 *  primary bars and (200 IS, 60 OOS, 60 step) the splitter produces 3
 *  folds — enough to exercise the bundle-slicing loop more than once. */
const DEFAULT_FOLD_CFG: FoldConfig = {
  isBars: 200,
  oosBars: 60,
  step: 60,
  anchored: false,
};

/** Default primary count provides ≥ 3 folds with `DEFAULT_FOLD_CFG`. */
const DEFAULT_PRIMARY_COUNT = 400;

export interface DescribeWalkForwardSmokeArgs {
  /** Preset slug — used as the describe-block prefix. */
  slug: string;
  /** The golden DSL (typically `loaded.golden` from
   *  `describeGoldenStrategyContract`). */
  goldenDsl: Record<string, unknown>;
  /** Primary timeframe in lowercase (e.g. "5m"). Drives split iteration. */
  primaryInterval: Interval;
  /** Other timeframes the bundle must include alongside the primary, also
   *  in lowercase. Empty / omitted ⇒ single-TF path (`runWalkForward`). */
  contextIntervals?: Interval[];
  /** Override the fold config when the default 400-bar window is wrong
   *  for a strategy (e.g. very long lookbacks). */
  foldCfg?: FoldConfig;
  /** Override the primary candle count. Must be ≥ isBars + oosBars. */
  primaryCount?: number;
}

/**
 * Register a smoke describe-block proving the golden DSL survives a full
 * walk-forward run on synthetic candles. The block fails iff the pipeline
 * throws or produces a malformed report — it is intentionally tolerant of
 * zero-trade outcomes (most strategies will no-op on a fixed-seed random
 * walk; that is fine for a smoke check).
 */
export function describeWalkForwardSmoke(args: DescribeWalkForwardSmokeArgs): void {
  const foldCfg = args.foldCfg ?? DEFAULT_FOLD_CFG;
  const primaryCount = args.primaryCount ?? DEFAULT_PRIMARY_COUNT;
  const ctx = args.contextIntervals ?? [];

  describe(`${args.slug} — walk-forward smoke (synthetic CI sub-fixture)`, () => {
    it("runs to completion across all folds with non-null reports", () => {
      const primaryRows = generateCandles({
        interval: args.primaryInterval,
        count: primaryCount,
        seed: 0xC0FFEE,
      });

      const isMtf = ctx.length > 0;
      const report = isMtf
        ? (() => {
            const bundle = new Map<CandleInterval, MarketCandle[]>();
            bundle.set(LOWER_TO_UPPER[args.primaryInterval], primaryRows);
            const primaryMs = INTERVAL_MS[args.primaryInterval];
            for (const tf of ctx) {
              if (tf === args.primaryInterval) continue;
              const tfMs = INTERVAL_MS[tf];
              // Cover the primary window plus a small lookback margin so
              // HTF indicators have at least a handful of closed bars from
              // the start.
              const tfCount = Math.max(50, Math.ceil((primaryCount * primaryMs) / tfMs) + 5);
              bundle.set(
                LOWER_TO_UPPER[tf],
                generateCandles({ interval: tf, count: tfCount, seed: 0xC0FFEE ^ tfMs }),
              );
            }
            return runWalkForwardWithBundle({
              bundle,
              primaryInterval: LOWER_TO_UPPER[args.primaryInterval],
              dslJson: args.goldenDsl,
              opts: {},
              foldCfg,
            });
          })()
        : runWalkForward(
            primaryRows.map(rowToCandle),
            args.goldenDsl,
            {},
            foldCfg,
          );

      expect(report.folds.length).toBeGreaterThan(0);
      for (const f of report.folds) {
        expect(f.isReport).not.toBeNull();
        expect(f.oosReport).not.toBeNull();
      }
      // aggregate is computed only after fold reports exist; if it's null
      // the helper is broken, not the strategy.
      expect(report.aggregate).toBeDefined();
      expect(report.aggregate.foldCount).toBe(report.folds.length);
    });
  });
}
