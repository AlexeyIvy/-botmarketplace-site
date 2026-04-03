/**
 * Contract tests — UI / Compiler drift detection.
 *
 * These tests ensure that:
 *   1. Every block defined in the UI (blockDefs.ts) is accounted for in the backend
 *   2. Every compiler handler has a corresponding UI block definition
 *   3. The support map covers every UI block — no silent gaps
 *   4. Block categories are consistent between UI and compiler
 *
 * If any of these tests fail, it means someone added/removed a block on one side
 * without updating the other. This is the exact "drift" we want to catch.
 */

import { describe, it, expect } from "vitest";
import { createRegistry, defaultHandlers, BLOCK_SUPPORT_MAP } from "../../src/lib/compiler/index.js";

// Import UI block definitions via relative path (cross-package, test-only)
import { BLOCK_DEFS } from "../../../web/src/app/lab/build/blockDefs.js";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

/** All block types defined in the UI */
const uiBlockTypes = BLOCK_DEFS.map((b) => b.type).sort();

/** All block types with compiler handlers */
const registry = createRegistry(defaultHandlers());
const compilerBlockTypes = registry.registeredTypes().sort();

/** All block types in the support map */
const supportMapTypes = Object.keys(BLOCK_SUPPORT_MAP).sort();

/** UI blocks grouped by category */
const uiBlocksByCategory = new Map<string, string[]>();
for (const b of BLOCK_DEFS) {
  const list = uiBlocksByCategory.get(b.category) ?? [];
  list.push(b.type);
  uiBlocksByCategory.set(b.category, list);
}

// ---------------------------------------------------------------------------
// Contract: UI → Compiler coverage
// ---------------------------------------------------------------------------

describe("UI → Compiler contract", () => {
  it("every UI block type has a compiler handler", () => {
    const missing = uiBlockTypes.filter((t) => !registry.has(t));
    expect(missing, `UI blocks missing compiler handlers: [${missing.join(", ")}]`).toEqual([]);
  });

  it("every UI block type is listed in BLOCK_SUPPORT_MAP", () => {
    const missing = uiBlockTypes.filter((t) => !(t in BLOCK_SUPPORT_MAP));
    expect(missing, `UI blocks missing from support map: [${missing.join(", ")}]`).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// Contract: Compiler → UI coverage
// ---------------------------------------------------------------------------

describe("Compiler → UI contract", () => {
  it("every compiler handler corresponds to a UI block", () => {
    const uiSet = new Set(uiBlockTypes);
    const orphans = compilerBlockTypes.filter((t) => !uiSet.has(t));
    expect(orphans, `Compiler handlers without UI block: [${orphans.join(", ")}]`).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// Contract: Support map completeness
// ---------------------------------------------------------------------------

describe("Support map completeness", () => {
  it("support map has no entries for non-existent UI blocks", () => {
    const uiSet = new Set(uiBlockTypes);
    const stale = supportMapTypes.filter((t) => !uiSet.has(t));
    expect(stale, `Support map entries for removed UI blocks: [${stale.join(", ")}]`).toEqual([]);
  });

  it("support map has exactly the same block types as UI", () => {
    expect(supportMapTypes).toEqual(uiBlockTypes);
  });

  it("every support map entry has a valid status", () => {
    const validStatuses = new Set(["supported", "compile-only", "unsupported"]);
    for (const [type, entry] of Object.entries(BLOCK_SUPPORT_MAP)) {
      expect(validStatuses.has(entry.status), `Invalid status "${entry.status}" for block "${type}"`).toBe(true);
      expect(entry.note.length, `Empty note for block "${type}"`).toBeGreaterThan(0);
    }
  });

  it("compile-only blocks all have compiler handlers (not truly unsupported)", () => {
    const compileOnly = Object.entries(BLOCK_SUPPORT_MAP)
      .filter(([, e]) => e.status === "compile-only")
      .map(([t]) => t);

    for (const t of compileOnly) {
      expect(registry.has(t), `Block "${t}" is compile-only but has no compiler handler`).toBe(true);
    }
  });
});

// ---------------------------------------------------------------------------
// Contract: Category consistency
// ---------------------------------------------------------------------------

describe("Category consistency", () => {
  it("compiler handler category matches UI block category for all blocks", () => {
    const mismatches: string[] = [];
    for (const uiBlock of BLOCK_DEFS) {
      const handler = registry.get(uiBlock.type);
      if (handler && handler.category !== uiBlock.category) {
        mismatches.push(
          `${uiBlock.type}: UI="${uiBlock.category}" vs compiler="${handler.category}"`,
        );
      }
    }
    expect(mismatches, `Category mismatches:\n${mismatches.join("\n")}`).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// Snapshot: current support status (catches accidental status changes)
// ---------------------------------------------------------------------------

describe("Support status snapshot", () => {
  it("currently supported blocks", () => {
    const supported = Object.entries(BLOCK_SUPPORT_MAP)
      .filter(([, e]) => e.status === "supported")
      .map(([t]) => t)
      .sort();

    expect(supported).toEqual([
      "EMA",
      "RSI",
      "SMA",
      "adx",
      "and_gate",
      "atr",
      "bollinger",
      "candles",
      "compare",
      "constant",
      "cross",
      "dca_config",
      "enter_adaptive",
      "enter_long",
      "enter_short",
      "fair_value_gap",
      "liquidity_sweep",
      "market_structure_shift",
      "or_gate",
      "order_block",
      "stop_loss",
      "supertrend",
      "take_profit",
      "vwap",
    ]);
  });

  it("currently compile-only blocks", () => {
    const compileOnly = Object.entries(BLOCK_SUPPORT_MAP)
      .filter(([, e]) => e.status === "compile-only")
      .map(([t]) => t)
      .sort();

    expect(compileOnly).toEqual([
      "macd",
      "proximity_filter",
      "volume",
      "volume_profile",
    ]);
  });

  it("block count matches expected total", () => {
    expect(uiBlockTypes.length).toBe(28);
    expect(compilerBlockTypes.length).toBe(28);
    expect(supportMapTypes.length).toBe(28);
  });
});
