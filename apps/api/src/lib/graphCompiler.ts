/**
 * Phase 4 — Graph-to-DSL Compiler
 *
 * Compiles a StrategyGraph (nodes + edges) to a validated StrategyVersion.body DSL.
 * Block-to-DSL mapping table: docs/10-strategy-dsl.md §9
 */

import { validateDsl } from "./dslValidator.js";

// ---------------------------------------------------------------------------
// Input types (mirror of frontend LabNodeData / LabEdge)
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
// Output types
// ---------------------------------------------------------------------------

export interface CompileIssue {
  severity: "error" | "warning";
  message: string;
  /** nodeId if the issue is tied to a specific node */
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
// DSL field constants (injected defaults — see docs/10-strategy-dsl.md §9.3)
// ---------------------------------------------------------------------------

const DSL_VERSION = 1;
const MARKET_DEFAULTS = {
  exchange: "bybit",
  env: "demo",
  category: "linear",
} as const;

const EXECUTION_DEFAULTS = {
  orderType: "Market",
  clientOrderIdPrefix: "lab_",
  maxSlippageBps: 50,
} as const;

const GUARDS_DEFAULTS = {
  maxOpenPositions: 1,
  maxOrdersPerMinute: 10,
  pauseOnError: true,
} as const;

const RISK_DEFAULTS = {
  maxPositionSizeUsd: 100,
  cooldownSeconds: 60,
} as const;

// ---------------------------------------------------------------------------
// Compiler
// ---------------------------------------------------------------------------

/**
 * Compile a graph JSON to Strategy DSL.
 *
 * @param graphJson  The serialized graph { nodes, edges }
 * @param strategyId The ID of the owning Strategy (used as DSL `id`)
 * @param name       The strategy name
 * @param symbol     Market symbol (e.g. "BTCUSDT")
 * @param timeframe  Timeframe string (e.g. "M15")
 */
export function compileGraph(
  graphJson: GraphJson,
  strategyId: string,
  name: string,
  symbol: string,
  timeframe: string
): CompileResult {
  const { nodes, edges } = graphJson;
  const issues: CompileIssue[] = [];

  // ── 1. Adjacency map: targetNodeId → list of incoming edges ─────────────
  const incomingEdges: Record<string, GraphEdge[]> = {};
  for (const node of nodes) incomingEdges[node.id] = [];
  for (const edge of edges) {
    incomingEdges[edge.target] = incomingEdges[edge.target] ?? [];
    incomingEdges[edge.target].push(edge);
  }

  // ── 2. Index nodes by type ───────────────────────────────────────────────
  const nodesByType: Record<string, GraphNode[]> = {};
  for (const node of nodes) {
    nodesByType[node.data.blockType] = nodesByType[node.data.blockType] ?? [];
    nodesByType[node.data.blockType].push(node);
  }

  const nodeById: Record<string, GraphNode> = {};
  for (const node of nodes) nodeById[node.id] = node;

  // ── 3. Validate required blocks (see docs §9.4) ──────────────────────────

  // 3a. candles block required
  if (!nodesByType["candles"] || nodesByType["candles"].length === 0) {
    issues.push({ severity: "error", message: "Graph must have a Candles input block." });
  }

  // 3b. Exactly one entry block
  const enterLongNodes = nodesByType["enter_long"] ?? [];
  const enterShortNodes = nodesByType["enter_short"] ?? [];
  const entryNodes = [...enterLongNodes, ...enterShortNodes];

  if (entryNodes.length === 0) {
    issues.push({ severity: "error", message: "Graph must have an Enter Long or Enter Short block." });
  } else if (enterLongNodes.length > 0 && enterShortNodes.length > 0) {
    issues.push({
      severity: "error",
      message: "Graph cannot have both Enter Long and Enter Short blocks (Phase 4 MVP constraint).",
    });
  } else if (entryNodes.length > 1) {
    issues.push({
      severity: "warning",
      message: `Multiple entry blocks detected (${entryNodes.length}). Only the first will be used.`,
    });
  }

  // 3c. Risk blocks required
  const stopLossNodes = nodesByType["stop_loss"] ?? [];
  const takeProfitNodes = nodesByType["take_profit"] ?? [];

  if (stopLossNodes.length === 0) {
    issues.push({ severity: "error", message: "Graph must have a Stop Loss block." });
  }
  if (takeProfitNodes.length === 0) {
    issues.push({ severity: "error", message: "Graph must have a Take Profit block." });
  }

  // 3d. Signal path — entry signal input must be connected
  const entryNode = entryNodes[0];
  if (entryNode) {
    const signalEdge = incomingEdges[entryNode.id]?.find((e) => e.targetHandle === "signal");
    if (!signalEdge) {
      issues.push({
        severity: "error",
        message: "Entry block signal input is not connected.",
        nodeId: entryNode.id,
      });
    }
    const riskEdge = incomingEdges[entryNode.id]?.find((e) => e.targetHandle === "risk");
    if (!riskEdge) {
      issues.push({
        severity: "error",
        message: "Entry block risk input is not connected.",
        nodeId: entryNode.id,
      });
    }
  }

  // If there are blocking errors, return early
  if (issues.some((i) => i.severity === "error")) {
    return { ok: false, validationIssues: issues };
  }

  // ── 4. Extract indicator nodes ───────────────────────────────────────────
  const indicatorTypes = ["SMA", "EMA", "RSI"];
  const indicators: Array<{ type: string; length: number; nodeId: string }> = [];

  for (const itype of indicatorTypes) {
    for (const node of nodesByType[itype] ?? []) {
      const length = Number(node.data.params["length"] ?? 14);
      indicators.push({ type: itype, length, nodeId: node.id });
    }
  }

  // ── 5. Extract signal logic ──────────────────────────────────────────────
  // Walk backwards from entry signal port to find the nearest cross/compare node.
  const signalEdge = incomingEdges[entryNode!.id]?.find((e) => e.targetHandle === "signal");
  const signalSourceNode = signalEdge ? nodeById[signalEdge.source] : undefined;

  let signalInfo: Record<string, unknown> = { type: "raw" };

  if (signalSourceNode?.data.blockType === "cross") {
    const mode = String(signalSourceNode.data.params["mode"] ?? "crossover");
    // Inputs a/b of cross node → find what they connect to
    const inputA = incomingEdges[signalSourceNode.id]?.find((e) => e.targetHandle === "a");
    const inputB = incomingEdges[signalSourceNode.id]?.find((e) => e.targetHandle === "b");
    const nodeA = inputA ? nodeById[inputA.source] : undefined;
    const nodeB = inputB ? nodeById[inputB.source] : undefined;

    signalInfo = {
      type: mode,
      fast: nodeA
        ? { blockType: nodeA.data.blockType, nodeId: nodeA.id, length: nodeA.data.params["length"] }
        : null,
      slow: nodeB
        ? { blockType: nodeB.data.blockType, nodeId: nodeB.id, length: nodeB.data.params["length"] }
        : null,
    };
  } else if (signalSourceNode?.data.blockType === "compare") {
    const op = String(signalSourceNode.data.params["op"] ?? ">");
    const inputA = incomingEdges[signalSourceNode.id]?.find((e) => e.targetHandle === "a");
    const inputB = incomingEdges[signalSourceNode.id]?.find((e) => e.targetHandle === "b");
    const nodeA = inputA ? nodeById[inputA.source] : undefined;
    const nodeB = inputB ? nodeById[inputB.source] : undefined;

    signalInfo = {
      type: "compare",
      op,
      left: nodeA
        ? { blockType: nodeA.data.blockType, nodeId: nodeA.id, length: nodeA.data.params["length"] }
        : null,
      right: nodeB
        ? { blockType: nodeB.data.blockType, nodeId: nodeB.id, length: nodeB.data.params["length"] }
        : null,
    };
  } else if (signalSourceNode) {
    signalInfo = { type: "direct", sourceBlockType: signalSourceNode.data.blockType };
  }

  // ── 6. Extract risk params from stop_loss + take_profit ─────────────────
  const slNode = stopLossNodes[0]!;
  const tpNode = takeProfitNodes[0]!;

  const slType = String(slNode.data.params["type"] ?? "fixed");
  const slValue = Number(slNode.data.params["value"] ?? 1.0);
  const tpType = String(tpNode.data.params["type"] ?? "fixed");
  const tpValue = Number(tpNode.data.params["value"] ?? 2.0);

  // riskPerTradePct: use stop-loss value (it's a % of position in the MVP model)
  const riskPerTradePct = Math.max(0.01, Math.min(slValue, 100));

  // ── 7. Determine entry side ──────────────────────────────────────────────
  const side = enterLongNodes.length > 0 ? "Buy" : "Sell";

  // ── 8. Assemble DSL ──────────────────────────────────────────────────────
  const compiledDsl: Record<string, unknown> = {
    id: strategyId,
    name,
    dslVersion: DSL_VERSION,
    enabled: true,
    market: {
      ...MARKET_DEFAULTS,
      symbol,
    },
    timeframes: [timeframe],
    entry: {
      side,
      signal: signalInfo,
      indicators,
      order: { type: "Market", maxSlippageBps: 50 },
      stopLoss: { type: slType, value: slValue },
      takeProfit: { type: tpType, value: tpValue },
    },
    risk: {
      ...RISK_DEFAULTS,
      riskPerTradePct,
    },
    execution: EXECUTION_DEFAULTS,
    guards: GUARDS_DEFAULTS,
  };

  // ── 9. Validate DSL against schema ───────────────────────────────────────
  const dslErrors = validateDsl(compiledDsl);
  if (dslErrors && dslErrors.length > 0) {
    const schemaIssues: CompileIssue[] = dslErrors.map((e) => ({
      severity: "error",
      message: `DSL schema error: ${e.field} — ${e.message}`,
    }));
    return { ok: false, validationIssues: [...issues, ...schemaIssues] };
  }

  return {
    ok: true,
    compiledDsl,
    validationIssues: issues,
  };
}
