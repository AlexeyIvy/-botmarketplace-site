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
  constant:     { status: "supported",    note: "Evaluator runtime wired in dslEvaluator getIndicatorValues" },

  // ── Indicators ──────────────────────────────────────────────────────────────
  SMA:          { status: "supported",    note: "Fully supported since Phase 3" },
  EMA:          { status: "supported",    note: "Fully supported since Phase 3" },
  RSI:          { status: "supported",    note: "Fully supported since Phase 3" },
  macd:         { status: "supported",    note: "MACD histogram in evaluator, calcMACD indicator engine" },
  bollinger:    { status: "supported",    note: "Evaluator runtime wired in dslEvaluator getIndicatorValues (bb_lower/upper/middle)" },
  atr:          { status: "supported",    note: "Evaluator runtime wired in dslEvaluator getIndicatorValues" },
  volume:       { status: "supported",    note: "Volume series from candles in evaluator runtime" },
  vwap:         { status: "supported",    note: "Indicator engine #125 + DSL evaluator runtime #126" },
  adx:          { status: "supported",    note: "Indicator engine #125 + DSL evaluator runtime #126" },
  supertrend:   { status: "supported",    note: "Indicator engine #125 + DSL evaluator runtime #126" },

  // ── Logic ───────────────────────────────────────────────────────────────────
  compare:      { status: "supported",    note: "Fully supported since Phase 4" },
  cross:        { status: "supported",    note: "Fully supported since Phase 3" },
  and_gate:     { status: "supported",    note: "Recursive evaluateSignal with conditions.every(), maxDepth=5" },
  or_gate:      { status: "supported",    note: "Recursive evaluateSignal with conditions.some(), maxDepth=5" },

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
  volume_profile:    { status: "supported", note: "VolumeProfile indicator #135. Runtime: calcVolumeProfile in dslEvaluator (POC/VAH/VAL)" },
  proximity_filter:  { status: "supported", note: "ProximityFilter #135. Runtime: calcProximityFilter in dslEvaluator, gates signals by proximity to level" },

  // ── SMC Pattern Primitives (#137, #138) ────────────────────────────────────
  liquidity_sweep:         { status: "supported", note: "SMC liquidity sweep #137/#138. Detects swing sweeps, pattern engine + evaluator wired" },
  fair_value_gap:          { status: "supported", note: "SMC fair value gap #137/#138. Detects 3-candle imbalances, pattern engine + evaluator wired" },
  order_block:             { status: "supported", note: "SMC order block #137/#138. Detects institutional order zones, pattern engine + evaluator wired" },
  market_structure_shift:  { status: "supported", note: "SMC market structure shift #137/#138. Detects BOS/CHoCH, pattern engine + evaluator wired" },
};
