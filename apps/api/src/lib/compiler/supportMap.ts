/**
 * Block support map — explicit record of backend support status for every UI block type.
 *
 * This map is the single source of truth for contract tests that detect drift
 * between the UI block library (blockDefs.ts) and the backend compiler.
 *
 * Support levels:
 *   - "supported"   — compiler handler exists AND backtest runtime can execute it
 *   - "compile-only" — compiler handler exists but runtime does not yet execute the compiled DSL for this block
 *   - "unsupported" — no compiler handler, block cannot be compiled
 *
 * When adding a new block to blockDefs.ts:
 *   1. Add a compiler handler in blockHandlers.ts
 *   2. Register it in defaultHandlers()
 *   3. Add an entry here with the correct status
 *   4. Run `pnpm --filter @botmarketplace/api test` — the contract test will fail if you miss any step
 */

export type BlockSupportStatus = "supported" | "compile-only" | "unsupported";

export interface BlockSupportEntry {
  status: BlockSupportStatus;
  /** Brief note on why this status, or what's needed to promote it. */
  note: string;
}

/**
 * Authoritative support map. Keys must match blockType from blockDefs.ts exactly.
 *
 * Maintained manually — contract tests enforce that this map covers every UI block.
 */
export const BLOCK_SUPPORT_MAP: Record<string, BlockSupportEntry> = {
  // ── Input ───────────────────────────────────────────────────────────────────
  candles:      { status: "supported",    note: "Core input block, fully supported since Phase 3" },
  constant:     { status: "compile-only", note: "Compiler handler extracts value; runtime DSL execution pending (#124)" },

  // ── Indicators ──────────────────────────────────────────────────────────────
  SMA:          { status: "supported",    note: "Fully supported since Phase 3" },
  EMA:          { status: "supported",    note: "Fully supported since Phase 3" },
  RSI:          { status: "supported",    note: "Fully supported since Phase 3" },
  macd:         { status: "compile-only", note: "Compiler handler added in #122; backtest runtime pending (#125)" },
  bollinger:    { status: "compile-only", note: "Compiler handler added in #122; backtest runtime pending (#125)" },
  atr:          { status: "compile-only", note: "Compiler handler added in #122; backtest runtime pending (#125)" },
  volume:       { status: "compile-only", note: "Compiler handler added in #122; backtest runtime pending (#125)" },
  vwap:         { status: "supported",    note: "Indicator engine #125 + DSL evaluator runtime #126" },
  adx:          { status: "supported",    note: "Indicator engine #125 + DSL evaluator runtime #126" },
  supertrend:   { status: "supported",    note: "Indicator engine #125 + DSL evaluator runtime #126" },

  // ── Logic ───────────────────────────────────────────────────────────────────
  compare:      { status: "supported",    note: "Fully supported since Phase 4" },
  cross:        { status: "supported",    note: "Fully supported since Phase 3" },
  and_gate:     { status: "compile-only", note: "Compiler handler added in #122; runtime pending (#124)" },
  or_gate:      { status: "compile-only", note: "Compiler handler added in #122; runtime pending (#124)" },

  // ── Execution ───────────────────────────────────────────────────────────────
  enter_long:     { status: "supported",    note: "Fully supported since Phase 3" },
  enter_short:    { status: "supported",    note: "Fully supported since Phase 4" },
  enter_adaptive: { status: "supported",    note: "DSL v2 sideCondition emission, #130" },

  // ── Risk ────────────────────────────────────────────────────────────────────
  stop_loss:    { status: "supported",    note: "Fully supported since Phase 3" },
  take_profit:  { status: "supported",    note: "Fully supported since Phase 3" },

  // ── DCA ─────────────────────────────────────────────────────────────────────
  dca_config:   { status: "supported",    note: "DCA ladder config block, #133. Compiles to DSL dca section, runtime engine #132" },

  // ── MTF Confluence (#135) ──────────────────────────────────────────────────
  volume_profile:    { status: "compile-only", note: "VolumeProfile indicator #135. Compiler handler extracts params; evaluator runtime pending #134" },
  proximity_filter:  { status: "compile-only", note: "ProximityFilter #135. Compiler handler extracts params; evaluator runtime pending #134" },

  // ── SMC Pattern Primitives (#137, #138) ────────────────────────────────────
  liquidity_sweep:         { status: "compile-only", note: "SMC liquidity sweep #137. Compiler handler extracts swingLen/maxAge; evaluator runtime pending #138" },
  fair_value_gap:          { status: "compile-only", note: "SMC fair value gap #137. Compiler handler extracts minGapRatio; evaluator runtime pending #138" },
  order_block:             { status: "compile-only", note: "SMC order block #137. Compiler handler extracts atrPeriod/impulseMultiple; evaluator runtime pending #138" },
  market_structure_shift:  { status: "compile-only", note: "SMC market structure shift #137. Compiler handler extracts swingLen; evaluator runtime pending #138" },
};
