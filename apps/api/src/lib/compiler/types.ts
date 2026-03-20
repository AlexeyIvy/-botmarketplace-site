/**
 * Shared types for the block-registry compiler architecture.
 */

// ---------------------------------------------------------------------------
// Graph input types (mirror of frontend LabNodeData / LabEdge)
// ---------------------------------------------------------------------------

export interface GraphNode {
  id: string;
  type?: string;
  data: {
    blockType: string;
    params: Record<string, unknown>;
  };
}

export interface GraphEdge {
  id: string;
  source: string;
  sourceHandle?: string | null;
  target: string;
  targetHandle?: string | null;
}

export interface GraphJson {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// ---------------------------------------------------------------------------
// Compile result types
// ---------------------------------------------------------------------------

export interface CompileIssue {
  severity: "error" | "warning";
  message: string;
  nodeId?: string;
}

export type CompileSuccess = {
  ok: true;
  compiledDsl: Record<string, unknown>;
  validationIssues: CompileIssue[];
};

export type CompileFailure = {
  ok: false;
  validationIssues: CompileIssue[];
};

export type CompileResult = CompileSuccess | CompileFailure;

// ---------------------------------------------------------------------------
// Block handler context — passed to every handler during compilation
// ---------------------------------------------------------------------------

export interface CompileContext {
  /** All nodes indexed by id */
  nodeById: Record<string, GraphNode>;
  /** Nodes grouped by blockType */
  nodesByType: Record<string, GraphNode[]>;
  /** Incoming edges indexed by target node id */
  incomingEdges: Record<string, GraphEdge[]>;
  /** Accumulator for compilation issues */
  issues: CompileIssue[];
}

// ---------------------------------------------------------------------------
// Block handler interface
// ---------------------------------------------------------------------------

export type BlockCategory = "input" | "indicator" | "logic" | "execution" | "risk";

/**
 * A BlockHandler encapsulates all compile-time logic for a single block type.
 *
 * - `validate`: checks that required instances/connections exist, pushes issues.
 * - `extract`: pulls DSL-relevant data from graph nodes of this type.
 *    Returns an arbitrary payload that the assembler uses.
 */
export interface BlockHandler {
  readonly blockType: string;
  readonly category: BlockCategory;

  /** Validate graph constraints for this block type. Push issues to ctx. */
  validate(ctx: CompileContext): void;

  /**
   * Extract DSL-relevant data from graph nodes of this type.
   * Called only when validation has no errors.
   * Returns a partial payload consumed by the DSL assembler.
   */
  extract(ctx: CompileContext): Record<string, unknown>;
}
