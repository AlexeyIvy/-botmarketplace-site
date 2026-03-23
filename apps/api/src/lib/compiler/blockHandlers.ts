/**
 * Block handler implementations for all Phase 3/4 MVP block types.
 *
 * Each handler encapsulates validation and DSL extraction logic for its block type.
 * To add a new block type, create a new handler object and register it in defaultHandlers().
 */

import type { BlockHandler, CompileContext, GraphNode } from "./types.js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function nodesOf(ctx: CompileContext, blockType: string): GraphNode[] {
  return ctx.nodesByType[blockType] ?? [];
}

// ---------------------------------------------------------------------------
// Input blocks
// ---------------------------------------------------------------------------

export const candlesHandler: BlockHandler = {
  blockType: "candles",
  category: "input",
  validate(ctx) {
    if (nodesOf(ctx, "candles").length === 0) {
      ctx.issues.push({ severity: "error", message: "Graph must have a Candles input block." });
    }
  },
  extract() {
    return {};
  },
};

export const constantHandler: BlockHandler = {
  blockType: "constant",
  category: "input",
  validate() {
    // constant blocks are optional, no constraints
  },
  extract(ctx) {
    const nodes = nodesOf(ctx, "constant");
    return {
      constants: nodes.map((n) => ({
        nodeId: n.id,
        value: Number(n.data.params["value"] ?? 0),
      })),
    };
  },
};

// ---------------------------------------------------------------------------
// Indicator blocks — generic handler factory
// ---------------------------------------------------------------------------

function makeIndicatorHandler(blockType: string): BlockHandler {
  return {
    blockType,
    category: "indicator",
    validate() {
      // indicators are optional; no graph-level constraint
    },
    extract(ctx) {
      const nodes = nodesOf(ctx, blockType);
      return {
        indicators: nodes.map((n) => ({
          type: blockType,
          length: Number(n.data.params["length"] ?? 14),
          nodeId: n.id,
        })),
      };
    },
  };
}

export const smaHandler = makeIndicatorHandler("SMA");
export const emaHandler = makeIndicatorHandler("EMA");
export const rsiHandler = makeIndicatorHandler("RSI");

// B2 indicator handlers — extract params specific to each type

export const macdHandler: BlockHandler = {
  blockType: "macd",
  category: "indicator",
  validate() {},
  extract(ctx) {
    const nodes = nodesOf(ctx, "macd");
    return {
      indicators: nodes.map((n) => ({
        type: "macd",
        nodeId: n.id,
        fastPeriod: Number(n.data.params["fastPeriod"] ?? 12),
        slowPeriod: Number(n.data.params["slowPeriod"] ?? 26),
        signalPeriod: Number(n.data.params["signalPeriod"] ?? 9),
      })),
    };
  },
};

export const bollingerHandler: BlockHandler = {
  blockType: "bollinger",
  category: "indicator",
  validate() {},
  extract(ctx) {
    const nodes = nodesOf(ctx, "bollinger");
    return {
      indicators: nodes.map((n) => ({
        type: "bollinger",
        nodeId: n.id,
        period: Number(n.data.params["period"] ?? 20),
        stdDevMult: Number(n.data.params["stdDevMult"] ?? 2.0),
      })),
    };
  },
};

export const atrHandler: BlockHandler = {
  blockType: "atr",
  category: "indicator",
  validate() {},
  extract(ctx) {
    const nodes = nodesOf(ctx, "atr");
    return {
      indicators: nodes.map((n) => ({
        type: "atr",
        nodeId: n.id,
        period: Number(n.data.params["period"] ?? 14),
      })),
    };
  },
};

export const volumeHandler: BlockHandler = {
  blockType: "volume",
  category: "indicator",
  validate() {},
  extract(ctx) {
    const nodes = nodesOf(ctx, "volume");
    return {
      indicators: nodes.map((n) => ({
        type: "volume",
        nodeId: n.id,
      })),
    };
  },
};

// Stage 2 indicator handlers (#125) — VWAP, ADX, SuperTrend

export const vwapHandler: BlockHandler = {
  blockType: "vwap",
  category: "indicator",
  validate() {},
  extract(ctx) {
    const nodes = nodesOf(ctx, "vwap");
    return {
      indicators: nodes.map((n) => ({
        type: "vwap",
        nodeId: n.id,
      })),
    };
  },
};

export const adxHandler: BlockHandler = {
  blockType: "adx",
  category: "indicator",
  validate() {},
  extract(ctx) {
    const nodes = nodesOf(ctx, "adx");
    return {
      indicators: nodes.map((n) => ({
        type: "adx",
        nodeId: n.id,
        period: Number(n.data.params["period"] ?? 14),
      })),
    };
  },
};

export const superTrendHandler: BlockHandler = {
  blockType: "supertrend",
  category: "indicator",
  validate() {},
  extract(ctx) {
    const nodes = nodesOf(ctx, "supertrend");
    return {
      indicators: nodes.map((n) => ({
        type: "supertrend",
        nodeId: n.id,
        atrPeriod: Number(n.data.params["atrPeriod"] ?? 10),
        multiplier: Number(n.data.params["multiplier"] ?? 3),
      })),
    };
  },
};

// ---------------------------------------------------------------------------
// Logic blocks
// ---------------------------------------------------------------------------

export const crossHandler: BlockHandler = {
  blockType: "cross",
  category: "logic",
  validate() {},
  extract(ctx) {
    const nodes = nodesOf(ctx, "cross");
    return {
      crossNodes: nodes.map((n) => ({
        nodeId: n.id,
        mode: String(n.data.params["mode"] ?? "crossover"),
      })),
    };
  },
};

export const compareHandler: BlockHandler = {
  blockType: "compare",
  category: "logic",
  validate() {},
  extract(ctx) {
    const nodes = nodesOf(ctx, "compare");
    return {
      compareNodes: nodes.map((n) => ({
        nodeId: n.id,
        op: String(n.data.params["op"] ?? ">"),
      })),
    };
  },
};

export const andGateHandler: BlockHandler = {
  blockType: "and_gate",
  category: "logic",
  validate() {},
  extract() {
    return {};
  },
};

export const orGateHandler: BlockHandler = {
  blockType: "or_gate",
  category: "logic",
  validate() {},
  extract() {
    return {};
  },
};

// ---------------------------------------------------------------------------
// Execution blocks
// ---------------------------------------------------------------------------

function makeEntryValidator(ctx: CompileContext): void {
  const enterLongNodes = nodesOf(ctx, "enter_long");
  const enterShortNodes = nodesOf(ctx, "enter_short");
  const enterAdaptiveNodes = nodesOf(ctx, "enter_adaptive");
  const entryNodes = [...enterLongNodes, ...enterShortNodes, ...enterAdaptiveNodes];

  if (entryNodes.length === 0) {
    ctx.issues.push({ severity: "error", message: "Graph must have an Enter Long, Enter Short, or Enter Adaptive block." });
  } else if (enterAdaptiveNodes.length > 0) {
    // enter_adaptive is validated by its own handler; skip dual-entry check
    return;
  } else if (enterLongNodes.length > 0 && enterShortNodes.length > 0) {
    ctx.issues.push({
      severity: "error",
      message: "Graph cannot have both Enter Long and Enter Short blocks (Phase 4 MVP constraint).",
    });
  } else if (entryNodes.length > 1) {
    ctx.issues.push({
      severity: "warning",
      message: `Multiple entry blocks detected (${entryNodes.length}). Only the first will be used.`,
    });
  }

  // Signal + risk connection checks
  const entryNode = entryNodes[0];
  if (entryNode) {
    const incoming = ctx.incomingEdges[entryNode.id] ?? [];
    if (!incoming.find((e) => e.targetHandle === "signal")) {
      ctx.issues.push({
        severity: "error",
        message: "Entry block signal input is not connected.",
        nodeId: entryNode.id,
      });
    }
    if (!incoming.find((e) => e.targetHandle === "risk")) {
      ctx.issues.push({
        severity: "error",
        message: "Entry block risk input is not connected.",
        nodeId: entryNode.id,
      });
    }
  }
}

export const enterLongHandler: BlockHandler = {
  blockType: "enter_long",
  category: "execution",
  validate(ctx) {
    makeEntryValidator(ctx);
  },
  extract(ctx) {
    const nodes = nodesOf(ctx, "enter_long");
    return { side: nodes.length > 0 ? "Buy" : null };
  },
};

export const enterShortHandler: BlockHandler = {
  blockType: "enter_short",
  category: "execution",
  validate() {
    // Validation is handled by enter_long handler which checks both types.
    // This avoids duplicate error messages.
  },
  extract(ctx) {
    const nodes = nodesOf(ctx, "enter_short");
    return { side: nodes.length > 0 ? "Sell" : null };
  },
};

/**
 * Adaptive entry block — DSL v2.
 *
 * Emits `sideCondition` instead of fixed `side`. The side-determining indicator
 * is connected via the "sideIndicator" target handle. The block params specify
 * the comparison ops for long/short (e.g. close > EMA → long, close < EMA → short).
 *
 * Graph pattern:
 *   candles → EMA(50) ─────────────────────→ enter_adaptive (sideIndicator)
 *   candles → ADX(14) → compare(> 25) ────→ enter_adaptive (signal)
 *                              stop_loss ──→ enter_adaptive (risk)
 */
export const enterAdaptiveHandler: BlockHandler = {
  blockType: "enter_adaptive",
  category: "execution",
  validate(ctx) {
    const nodes = nodesOf(ctx, "enter_adaptive");
    if (nodes.length === 0) return; // not present — skip

    // enter_adaptive is mutually exclusive with enter_long / enter_short
    const hasLong = nodesOf(ctx, "enter_long").length > 0;
    const hasShort = nodesOf(ctx, "enter_short").length > 0;
    if (hasLong || hasShort) {
      ctx.issues.push({
        severity: "error",
        message: "enter_adaptive cannot coexist with enter_long or enter_short.",
      });
      return;
    }

    const entryNode = nodes[0];
    const incoming = ctx.incomingEdges[entryNode.id] ?? [];

    if (!incoming.find((e) => e.targetHandle === "signal")) {
      ctx.issues.push({
        severity: "error",
        message: "enter_adaptive signal input is not connected.",
        nodeId: entryNode.id,
      });
    }
    if (!incoming.find((e) => e.targetHandle === "risk")) {
      ctx.issues.push({
        severity: "error",
        message: "enter_adaptive risk input is not connected.",
        nodeId: entryNode.id,
      });
    }
    if (!incoming.find((e) => e.targetHandle === "sideIndicator")) {
      ctx.issues.push({
        severity: "error",
        message: "enter_adaptive requires a side-determining indicator connected to sideIndicator.",
        nodeId: entryNode.id,
      });
    }
  },
  extract(ctx) {
    const nodes = nodesOf(ctx, "enter_adaptive");
    if (nodes.length === 0) return {};

    const entryNode = nodes[0];
    const incoming = ctx.incomingEdges[entryNode.id] ?? [];
    const sideEdge = incoming.find((e) => e.targetHandle === "sideIndicator");
    const sideNode = sideEdge ? ctx.nodeById[sideEdge.source] : undefined;

    if (!sideNode) return {};

    const indicatorType = sideNode.data.blockType.toUpperCase();
    const length = Number(sideNode.data.params["length"] ?? sideNode.data.params["period"] ?? 14);
    const source = String(entryNode.data.params["source"] ?? "close");
    const longOp = String(entryNode.data.params["longOp"] ?? "gt");
    const shortOp = String(entryNode.data.params["shortOp"] ?? "lt");

    return {
      adaptive: true,
      sideCondition: {
        indicator: { type: indicatorType, length },
        source,
        long: { op: longOp },
        short: { op: shortOp },
      },
    };
  },
};

// ---------------------------------------------------------------------------
// Risk blocks
// ---------------------------------------------------------------------------

export const stopLossHandler: BlockHandler = {
  blockType: "stop_loss",
  category: "risk",
  validate(ctx) {
    if (nodesOf(ctx, "stop_loss").length === 0) {
      ctx.issues.push({ severity: "error", message: "Graph must have a Stop Loss block." });
    }
  },
  extract(ctx) {
    const node = nodesOf(ctx, "stop_loss")[0];
    if (!node) return {};
    return {
      stopLoss: {
        type: String(node.data.params["type"] ?? "fixed"),
        value: Number(node.data.params["value"] ?? 1.0),
      },
    };
  },
};

export const takeProfitHandler: BlockHandler = {
  blockType: "take_profit",
  category: "risk",
  validate(ctx) {
    if (nodesOf(ctx, "take_profit").length === 0) {
      ctx.issues.push({ severity: "error", message: "Graph must have a Take Profit block." });
    }
  },
  extract(ctx) {
    const node = nodesOf(ctx, "take_profit")[0];
    if (!node) return {};
    return {
      takeProfit: {
        type: String(node.data.params["type"] ?? "fixed"),
        value: Number(node.data.params["value"] ?? 2.0),
      },
    };
  },
};

// ---------------------------------------------------------------------------
// Default handler set — all MVP block types
// ---------------------------------------------------------------------------

export function defaultHandlers(): BlockHandler[] {
  return [
    // Input
    candlesHandler,
    constantHandler,
    // Indicators
    smaHandler,
    emaHandler,
    rsiHandler,
    macdHandler,
    bollingerHandler,
    atrHandler,
    volumeHandler,
    vwapHandler,
    adxHandler,
    superTrendHandler,
    // Logic
    crossHandler,
    compareHandler,
    andGateHandler,
    orGateHandler,
    // Execution
    enterLongHandler,
    enterShortHandler,
    enterAdaptiveHandler,
    // Risk
    stopLossHandler,
    takeProfitHandler,
  ];
}
