/**
 * Phase 4 — Graph-to-DSL Compiler (registry-based)
 *
 * Compiles a StrategyGraph (nodes + edges) to a validated StrategyVersion.body DSL.
 * Block-to-DSL mapping table: docs/10-strategy-dsl.md §9
 *
 * Architecture: block handlers are registered in BlockRegistry.
 * The compiler queries the registry to validate and extract data.
 * Unknown block types produce explicit errors.
 */

import { validateDsl } from "../dslValidator.js";
import type { BlockRegistry } from "./blockRegistry.js";
import type {
  GraphJson,
  GraphNode,
  GraphEdge,
  CompileIssue,
  CompileResult,
  CompileContext,
} from "./types.js";

// Re-export types for consumers
export type { GraphJson, GraphNode, GraphEdge, CompileIssue, CompileResult };

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
// Context builder
// ---------------------------------------------------------------------------

function buildContext(graphJson: GraphJson): CompileContext {
  const { nodes, edges } = graphJson;
  const issues: CompileIssue[] = [];

  const incomingEdges: Record<string, GraphEdge[]> = {};
  for (const node of nodes) incomingEdges[node.id] = [];
  for (const edge of edges) {
    incomingEdges[edge.target] = incomingEdges[edge.target] ?? [];
    incomingEdges[edge.target].push(edge);
  }

  const nodesByType: Record<string, GraphNode[]> = {};
  for (const node of nodes) {
    nodesByType[node.data.blockType] = nodesByType[node.data.blockType] ?? [];
    nodesByType[node.data.blockType].push(node);
  }

  const nodeById: Record<string, GraphNode> = {};
  for (const node of nodes) nodeById[node.id] = node;

  return { nodeById, nodesByType, incomingEdges, issues };
}

// ---------------------------------------------------------------------------
// Signal extraction (walks backwards from entry signal port)
// ---------------------------------------------------------------------------

function extractSignalInfo(ctx: CompileContext, entryNode: GraphNode): Record<string, unknown> {
  const signalEdge = ctx.incomingEdges[entryNode.id]?.find((e) => e.targetHandle === "signal");
  const signalSourceNode = signalEdge ? ctx.nodeById[signalEdge.source] : undefined;

  if (signalSourceNode?.data.blockType === "cross") {
    const mode = String(signalSourceNode.data.params["mode"] ?? "crossover");
    const inputA = ctx.incomingEdges[signalSourceNode.id]?.find((e) => e.targetHandle === "a");
    const inputB = ctx.incomingEdges[signalSourceNode.id]?.find((e) => e.targetHandle === "b");
    const nodeA = inputA ? ctx.nodeById[inputA.source] : undefined;
    const nodeB = inputB ? ctx.nodeById[inputB.source] : undefined;

    return {
      type: mode,
      fast: nodeA
        ? { blockType: nodeA.data.blockType, nodeId: nodeA.id, length: nodeA.data.params["length"] }
        : null,
      slow: nodeB
        ? { blockType: nodeB.data.blockType, nodeId: nodeB.id, length: nodeB.data.params["length"] }
        : null,
    };
  }

  if (signalSourceNode?.data.blockType === "compare") {
    const op = String(signalSourceNode.data.params["op"] ?? ">");
    const inputA = ctx.incomingEdges[signalSourceNode.id]?.find((e) => e.targetHandle === "a");
    const inputB = ctx.incomingEdges[signalSourceNode.id]?.find((e) => e.targetHandle === "b");
    const nodeA = inputA ? ctx.nodeById[inputA.source] : undefined;
    const nodeB = inputB ? ctx.nodeById[inputB.source] : undefined;

    return {
      type: "compare",
      op,
      left: nodeA
        ? { blockType: nodeA.data.blockType, nodeId: nodeA.id, length: nodeA.data.params["length"] }
        : null,
      right: nodeB
        ? { blockType: nodeB.data.blockType, nodeId: nodeB.id, length: nodeB.data.params["length"] }
        : null,
    };
  }

  if (signalSourceNode) {
    return { type: "direct", sourceBlockType: signalSourceNode.data.blockType };
  }

  return { type: "raw" };
}

// ---------------------------------------------------------------------------
// Compiler
// ---------------------------------------------------------------------------

/**
 * Compile a graph JSON to Strategy DSL using the provided block registry.
 */
export function compileGraph(
  registry: BlockRegistry,
  graphJson: GraphJson,
  strategyId: string,
  name: string,
  symbol: string,
  timeframe: string,
): CompileResult {
  const ctx = buildContext(graphJson);

  // ── 1. Check for unregistered block types ────────────────────────────────
  for (const node of graphJson.nodes) {
    if (!registry.has(node.data.blockType)) {
      ctx.issues.push({
        severity: "error",
        message: `Unsupported block type "${node.data.blockType}". Register a handler to support it.`,
        nodeId: node.id,
      });
    }
  }

  // ── 2. Run all registered handlers' validation ──────────────────────────
  for (const handler of registry.allHandlers()) {
    handler.validate(ctx);
  }

  // If there are blocking errors, return early
  if (ctx.issues.some((i) => i.severity === "error")) {
    return { ok: false, validationIssues: ctx.issues };
  }

  // ── 3. Extract indicator data from all indicator handlers ───────────────
  const indicators: Array<Record<string, unknown>> = [];
  for (const handler of registry.allHandlers()) {
    if (handler.category === "indicator") {
      const extracted = handler.extract(ctx);
      if (extracted["indicators"]) {
        indicators.push(...(extracted["indicators"] as Array<Record<string, unknown>>));
      }
    }
  }

  // ── 4. Extract entry side ──────────────────────────────────────────────
  const enterLongNodes = ctx.nodesByType["enter_long"] ?? [];
  const enterShortNodes = ctx.nodesByType["enter_short"] ?? [];
  const entryNodes = [...enterLongNodes, ...enterShortNodes];
  const entryNode = entryNodes[0]!;
  const side = enterLongNodes.length > 0 ? "Buy" : "Sell";

  // ── 5. Extract signal info ─────────────────────────────────────────────
  const signalInfo = extractSignalInfo(ctx, entryNode);

  // ── 6. Extract risk params from stop_loss + take_profit handlers ───────
  const slExtracted = registry.get("stop_loss")!.extract(ctx);
  const tpExtracted = registry.get("take_profit")!.extract(ctx);
  const stopLoss = slExtracted["stopLoss"] as { type: string; value: number };
  const takeProfit = tpExtracted["takeProfit"] as { type: string; value: number };
  const riskPerTradePct = Math.max(0.01, Math.min(stopLoss.value, 100));

  // ── 7. Assemble DSL ──────────────────────────────────────────────────
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
      stopLoss,
      takeProfit,
    },
    risk: {
      ...RISK_DEFAULTS,
      riskPerTradePct,
    },
    execution: EXECUTION_DEFAULTS,
    guards: GUARDS_DEFAULTS,
  };

  // ── 8. Validate DSL against schema ───────────────────────────────────
  const dslErrors = validateDsl(compiledDsl);
  if (dslErrors && dslErrors.length > 0) {
    const schemaIssues: CompileIssue[] = dslErrors.map((e) => ({
      severity: "error",
      message: `DSL schema error: ${e.field} — ${e.message}`,
    }));
    return { ok: false, validationIssues: [...ctx.issues, ...schemaIssues] };
  }

  return {
    ok: true,
    compiledDsl,
    validationIssues: ctx.issues,
  };
}
