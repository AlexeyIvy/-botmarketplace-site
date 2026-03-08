// ---------------------------------------------------------------------------
// Phase 3C — ValidationIssue model + graph validation rules
// Per docs/23-lab-v2-ide-spec.md §13.3, §28 (Error presentation hierarchy)
// ---------------------------------------------------------------------------

import type { Node, Edge } from "@xyflow/react";
import { BLOCK_DEF_MAP, type LabNodeData } from "./build/blockDefs";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ValidationSeverity = "error" | "warning";

export interface ValidationIssue {
  /** Unique identifier per issue (stable within one validation pass) */
  id: string;
  severity: ValidationSeverity;
  /** Affected node ID (node-level or port-level issues) */
  nodeId?: string;
  /** Affected port handle ID (port-level issues) */
  portId?: string;
  /** Affected edge ID (edge-level issues) */
  edgeId?: string;
  /**
   * Machine-readable code.
   * Values: 'MISSING_RISK_BLOCK' | 'MISSING_ENTRY_BLOCK' | 'MISSING_INPUT_BLOCK' | 'REQUIRED_PORT_UNCONNECTED'
   */
  code: string;
  /** Human-readable message shown in Validation tab (§28 Level 5) */
  message: string;
}

// ---------------------------------------------------------------------------
// validateGraph — pure function, no side effects
// Per §13.3 Graph validation (client-side rules for Phase 3C)
// ---------------------------------------------------------------------------

export function validateGraph(
  nodes: Node[],
  edges: Edge[]
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  let issueSeq = 0;
  const nextId = () => `issue_${++issueSeq}`;

  // Helper: get LabNodeData safely
  const getNodeData = (node: Node): LabNodeData | undefined => {
    const d = node.data as LabNodeData | undefined;
    return d;
  };

  // ── Rule 1: MISSING_RISK_BLOCK ──────────────────────────────────────────
  // No node with category 'risk' exists → graph-level error
  const hasRiskBlock = nodes.some((n) => {
    const d = getNodeData(n);
    if (!d) return false;
    const def = BLOCK_DEF_MAP[d.blockType];
    return def?.category === "risk";
  });

  if (!hasRiskBlock) {
    issues.push({
      id: nextId(),
      severity: "error",
      code: "MISSING_RISK_BLOCK",
      message:
        "Graph requires at least one risk block (e.g. Stop Loss). Add a risk block to the canvas.",
    });
  }

  // ── Rule 2: MISSING_ENTRY_BLOCK ──────────────────────────────────────────
  // No node with blockType 'enter_long' or 'enter_short' → graph-level error
  const hasEntryBlock = nodes.some((n) => {
    const d = getNodeData(n);
    if (!d) return false;
    return d.blockType === "enter_long" || d.blockType === "enter_short";
  });

  if (!hasEntryBlock) {
    issues.push({
      id: nextId(),
      severity: "error",
      code: "MISSING_ENTRY_BLOCK",
      message:
        "Graph requires at least one entry block (Enter Long or Enter Short) to open positions.",
    });
  }

  // ── Rule 3: MISSING_INPUT_BLOCK ─────────────────────────────────────────
  // No node with category 'input' (i.e., candles) → graph-level warning
  const hasInputBlock = nodes.some((n) => {
    const d = getNodeData(n);
    if (!d) return false;
    const def = BLOCK_DEF_MAP[d.blockType];
    return def?.category === "input";
  });

  if (!hasInputBlock && nodes.length > 0) {
    issues.push({
      id: nextId(),
      severity: "warning",
      code: "MISSING_INPUT_BLOCK",
      message:
        "No data source block found. Add a Candles block to provide market data to indicators.",
    });
  }

  // ── Rule 4: REQUIRED_PORT_UNCONNECTED ────────────────────────────────────
  // For each node, check each required input port; if no edge connects to it
  // → port-level error on that node/port
  const connectedTargets = new Set(
    edges.map((e) => `${e.target}::${e.targetHandle}`)
  );

  for (const node of nodes) {
    const d = getNodeData(node);
    if (!d) continue;
    const def = BLOCK_DEF_MAP[d.blockType];
    if (!def) continue;

    for (const port of def.inputs) {
      if (!port.required) continue;
      const key = `${node.id}::${port.id}`;
      if (!connectedTargets.has(key)) {
        issues.push({
          id: nextId(),
          severity: "error",
          nodeId: node.id,
          portId: port.id,
          code: "REQUIRED_PORT_UNCONNECTED",
          message: `[${def.label}] input '${port.label}' is required but has no source.`,
        });
      }
    }
  }

  return issues;
}
