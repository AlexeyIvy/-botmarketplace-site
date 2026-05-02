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
import { parseDsl } from "../../src/lib/dslEvaluator.js";
import { validateDsl } from "../../src/lib/dslValidator.js";
import { BLOCK_SUPPORT_MAP } from "../../src/lib/compiler/supportMap.ts";

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
