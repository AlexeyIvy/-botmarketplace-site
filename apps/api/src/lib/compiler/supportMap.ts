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

  // ── Logic ───────────────────────────────────────────────────────────────────
  compare:      { status: "supported",    note: "Fully supported since Phase 4" },
  cross:        { status: "supported",    note: "Fully supported since Phase 3" },
  and_gate:     { status: "compile-only", note: "Compiler handler added in #122; runtime pending (#124)" },
  or_gate:      { status: "compile-only", note: "Compiler handler added in #122; runtime pending (#124)" },

  // ── Execution ───────────────────────────────────────────────────────────────
  enter_long:   { status: "supported",    note: "Fully supported since Phase 3" },
  enter_short:  { status: "supported",    note: "Fully supported since Phase 4" },

  // ── Risk ────────────────────────────────────────────────────────────────────
  stop_loss:    { status: "supported",    note: "Fully supported since Phase 3" },
  take_profit:  { status: "supported",    note: "Fully supported since Phase 3" },
};
