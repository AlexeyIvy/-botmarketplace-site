/**
 * Compiler module — public API.
 *
 * Provides a pre-configured `compileGraph` function that uses the default
 * block registry. Also exports the registry and types for testing / extension.
 */

export type {
  GraphJson,
  GraphNode,
  GraphEdge,
  CompileIssue,
  CompileResult,
  CompileSuccess,
  CompileFailure,
  CompileContext,
  BlockHandler,
  BlockCategory,
} from "./types.js";

export { BlockRegistry, createRegistry } from "./blockRegistry.js";
export { defaultHandlers } from "./blockHandlers.js";
export { compileGraph as compileGraphWithRegistry } from "./graphCompiler.js";
export { BLOCK_SUPPORT_MAP } from "./supportMap.js";
export type { BlockSupportStatus, BlockSupportEntry } from "./supportMap.js";

import { createRegistry } from "./blockRegistry.js";
import { defaultHandlers } from "./blockHandlers.js";
import { compileGraph as compileGraphWithRegistry } from "./graphCompiler.js";
import type { GraphJson, CompileResult } from "./types.js";

// Pre-built default registry (singleton)
const defaultRegistry = createRegistry(defaultHandlers());

/**
 * Compile a graph JSON to Strategy DSL using the default block registry.
 * Drop-in replacement for the old `compileGraph` function signature.
 */
export function compileGraph(
  graphJson: GraphJson,
  strategyId: string,
  name: string,
  symbol: string,
  timeframe: string,
): CompileResult {
  return compileGraphWithRegistry(defaultRegistry, graphJson, strategyId, name, symbol, timeframe);
}
