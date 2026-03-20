/**
 * Phase 4 — Graph-to-DSL Compiler (legacy entry point)
 *
 * This file re-exports from the new compiler module for backwards compatibility.
 * All logic now lives in ./compiler/.
 *
 * @deprecated Import from "./compiler/index.js" instead.
 */

export {
  compileGraph,
  type GraphJson,
  type GraphNode,
  type GraphEdge,
  type CompileIssue,
  type CompileResult,
  type CompileSuccess,
  type CompileFailure,
} from "./compiler/index.js";
