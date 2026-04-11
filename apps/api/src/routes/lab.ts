import type { FastifyInstance } from "fastify";
import { prisma } from "../lib/prisma.js";
import { problem } from "../lib/problem.js";
import { logger } from "../lib/logger.js";
import { resolveWorkspace } from "../lib/workspace.js";
import { runBacktest } from "../lib/backtest.js";
import { applyDslSweepParam } from "../lib/dslSweepParam.js";
import { compileGraph } from "../lib/graphCompiler.js";
import type { GraphJson } from "../lib/graphCompiler.js";
import {
  explainGraph,
  explainValidation,
  explainDelta,
  suggestRisk,
  ExplainInputError,
  ProviderError,
  type ExplainGraphInput,
  type ExplainValidationInput,
  type ExplainDeltaInput,
  type ExplainRiskInput,
} from "../lib/aiExplain.js";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Stage 19 v2.2: fill price reference is fixed to CLOSE */
const ALLOWED_FILL_AT = ["CLOSE"] as const;
type FillAt = typeof ALLOWED_FILL_AT[number];

/** Reasonable upper bound for fee/slippage to prevent nonsensical inputs */
const MAX_BPS = 1000; // 10%

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

/**
 * Phase 5 dataset-first backtest request.
 * strategyVersionId is required — explicit version binding for reproducibility.
 * datasetId is required — the dataset provides symbol/interval/range + candles.
 * Per docs/23-lab-v2-ide-spec.md §16 Phase 5.
 */
interface StartBacktestBody {
  strategyVersionId: string;
  datasetId: string;
  feeBps?: number;
  slippageBps?: number;
  fillAt?: FillAt;
}

/** Fields returned in list/detail views (includes Stage 19b + Phase 5 additions) */
const BACKTEST_SELECT = {
  id: true,
  workspaceId: true,
  strategyId: true,
  strategyVersionId: true,
  symbol: true,
  interval: true,
  fromTs: true,
  toTs: true,
  status: true,
  reportJson: true,
  errorMessage: true,
  createdAt: true,
  updatedAt: true,
  // Stage 19b reproducibility fields
  datasetId: true,
  datasetHash: true,
  feeBps: true,
  slippageBps: true,
  fillAt: true,
  engineVersion: true,
} as const;

// ---------------------------------------------------------------------------
// Phase 4 — Graph endpoints
// ---------------------------------------------------------------------------

interface CreateGraphBody {
  name: string;
  graphJson: GraphJson;
}

interface PatchGraphBody {
  graphJson?: GraphJson;
  name?: string;
}

interface CompileGraphBody {
  graphJson: GraphJson;
  /** Market symbol, e.g. "BTCUSDT" */
  symbol?: string;
  /** Timeframe key, e.g. "M15" */
  timeframe?: string;
  /** Attach to an existing Strategy; if omitted a new Strategy is created */
  strategyId?: string;
}

const GRAPH_SELECT = {
  id: true,
  workspaceId: true,
  name: true,
  blockLibraryVersion: true,
  dslVersionTarget: true,
  graphJson: true,
  validationSummaryJson: true,
  createdAt: true,
  updatedAt: true,
} as const;

export async function labRoutes(app: FastifyInstance) {
  // ── POST /lab/graphs ── create a new StrategyGraph draft ─────────────────
  app.post<{ Body: CreateGraphBody }>("/lab/graphs", {
    config: { rateLimit: { max: 30, timeWindow: "1 minute" } },
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const { name, graphJson } = request.body ?? {};

    if (!name || typeof name !== "string") {
      return problem(reply, 400, "Validation Error", "name is required");
    }
    if (!graphJson || typeof graphJson !== "object") {
      return problem(reply, 400, "Validation Error", "graphJson is required");
    }

    const graph = await prisma.strategyGraph.create({
      data: {
        workspaceId: workspace.id,
        name,
        graphJson: graphJson as object,
      },
      select: GRAPH_SELECT,
    });

    return reply.status(201).send(graph);
  });

  // ── GET /lab/graphs ── list StrategyGraphs for workspace ─────────────────
  app.get("/lab/graphs", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const graphs = await prisma.strategyGraph.findMany({
      where: { workspaceId: workspace.id },
      orderBy: { updatedAt: "desc" },
      take: 50,
      select: GRAPH_SELECT,
    });
    return reply.send(graphs);
  });

  // ── GET /lab/graphs/:id ── get a single StrategyGraph ────────────────────
  app.get<{ Params: { id: string } }>("/lab/graphs/:id", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const graph = await prisma.strategyGraph.findUnique({
      where: { id: request.params.id },
      select: GRAPH_SELECT,
    });
    if (!graph || graph.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Graph not found");
    }
    return reply.send(graph);
  });

  // ── PATCH /lab/graphs/:id ── update draft graph (auto-save) ─────────────
  // Phase 3A: debounced auto-save from frontend calls this endpoint.
  // Only graphJson and name may be updated; workspaceId is protected.
  app.patch<{ Params: { id: string }; Body: PatchGraphBody }>("/lab/graphs/:id", {
    config: { rateLimit: { max: 60, timeWindow: "1 minute" } },
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const graph = await prisma.strategyGraph.findUnique({
      where: { id: request.params.id },
    });
    if (!graph || graph.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Graph not found");
    }

    const { graphJson, name } = request.body ?? {};

    if (graphJson !== undefined && (typeof graphJson !== "object" || graphJson === null)) {
      return problem(reply, 400, "Validation Error", "graphJson must be an object");
    }
    if (name !== undefined && (typeof name !== "string" || name.trim().length === 0)) {
      return problem(reply, 400, "Validation Error", "name must be a non-empty string");
    }

    const updateData: { graphJson?: object; name?: string } = {};
    if (graphJson !== undefined) updateData.graphJson = graphJson as object;
    if (name !== undefined) updateData.name = name.trim();

    if (Object.keys(updateData).length === 0) {
      return problem(reply, 400, "Validation Error", "No updatable fields provided");
    }

    const updated = await prisma.strategyGraph.update({
      where: { id: graph.id },
      data: updateData,
      select: GRAPH_SELECT,
    });

    return reply.send(updated);
  });

  // ── POST /lab/graphs/:id/compile ── compile graph → StrategyVersion ───────
  // Per docs/23-lab-v2-ide-spec.md §19 Phase 4A
  // Returns: { strategyVersionId, compiledDsl, validationIssues }
  app.post<{ Params: { id: string }; Body: CompileGraphBody }>("/lab/graphs/:id/compile", {
    config: { rateLimit: { max: 20, timeWindow: "1 minute" } },
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    // Load graph — workspace isolation check
    const graph = await prisma.strategyGraph.findUnique({
      where: { id: request.params.id },
    });
    if (!graph || graph.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Graph not found");
    }

    const { graphJson, symbol = "BTCUSDT", timeframe = "M15", strategyId } = request.body ?? {};

    if (!graphJson || typeof graphJson !== "object") {
      return problem(reply, 400, "Validation Error", "graphJson is required");
    }

    // Update graphJson on the StrategyGraph record (upsert-friendly: keep graph in sync)
    await prisma.strategyGraph.update({
      where: { id: graph.id },
      data: { graphJson: graphJson as object },
    });

    // ── Compile ─────────────────────────────────────────────────────────────

    // Resolve or create Strategy
    let strategy: { id: string; name: string } | null = null;

    if (strategyId) {
      const found = await prisma.strategy.findUnique({ where: { id: strategyId } });
      if (!found || found.workspaceId !== workspace.id) {
        return problem(reply, 404, "Not Found", "Strategy not found");
      }
      strategy = found;
    } else {
      // Create a new Strategy for this graph
      const strategyName = graph.name;
      const existing = await prisma.strategy.findUnique({
        where: { workspaceId_name: { workspaceId: workspace.id, name: strategyName } },
      });
      if (existing) {
        strategy = existing;
      } else {
        strategy = await prisma.strategy.create({
          data: {
            workspaceId: workspace.id,
            name: strategyName,
            symbol,
            timeframe: (["M1", "M5", "M15", "H1"].includes(timeframe)
              ? timeframe
              : "M15") as "M1" | "M5" | "M15" | "H1",
            status: "DRAFT",
          },
        });
      }
    }

    // Run compiler (docs/10-strategy-dsl.md §9)
    const compileResult = compileGraph(
      graphJson as GraphJson,
      strategy.id,
      strategy.name,
      symbol,
      timeframe
    );

    if (!compileResult.ok) {
      return reply.status(422).send({
        type: "about:blank",
        title: "Compile Failed",
        status: 422,
        detail: "Graph compilation failed with validation errors",
        validationIssues: compileResult.validationIssues,
      });
    }

    // ── Persist StrategyVersion + StrategyGraphVersion ──────────────────────
    const latestVersion = await prisma.strategyVersion.findFirst({
      where: { strategyId: strategy.id },
      orderBy: { version: "desc" },
    });
    const nextVersion = (latestVersion?.version ?? 0) + 1;

    const strategyVersion = await prisma.strategyVersion.create({
      data: {
        strategyId: strategy.id,
        version: nextVersion,
        dslJson: compileResult.compiledDsl as object,
        executionPlanJson: { kind: "compiled-graph", graphId: graph.id, compiledAt: new Date().toISOString() },
      },
    });

    // Count existing StrategyGraphVersions for this graph to determine version number
    const existingVersionCount = await prisma.strategyGraphVersion.count({
      where: { strategyGraphId: graph.id },
    });

    const graphVersion = await prisma.strategyGraphVersion.create({
      data: {
        strategyGraphId: graph.id,
        version: existingVersionCount + 1,
        blockLibraryVersion: graph.blockLibraryVersion,
        graphSnapshotJson: graphJson as object,
        strategyVersionId: strategyVersion.id,
      },
    });

    return reply.status(201).send({
      strategyVersionId: strategyVersion.id,
      strategyVersion: nextVersion,
      graphVersionId: graphVersion.id,
      compiledDsl: compileResult.compiledDsl,
      validationIssues: compileResult.validationIssues,
    });
  });

  // ── GET /lab/strategy-versions ── list compiled StrategyVersions for workspace ──
  // Phase 5: needed for backtest form to select a specific compiled version.
  app.get("/lab/strategy-versions", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const versions = await prisma.strategyVersion.findMany({
      where: { strategy: { workspaceId: workspace.id } },
      orderBy: { createdAt: "desc" },
      take: 100,
      select: {
        id: true,
        version: true,
        createdAt: true,
        strategy: {
          select: { id: true, name: true, symbol: true },
        },
      },
    });

    return reply.send(versions);
  });

  // ── POST /lab/backtest ── trigger a new backtest (Phase 5, strategyVersionId-first) ──
  // Per docs/23-lab-v2-ide-spec.md §16 Phase 5
  app.post<{ Body: StartBacktestBody }>("/lab/backtest", {
    config: { rateLimit: { max: 5, timeWindow: "1 minute" } },
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const {
      strategyVersionId,
      datasetId,
      feeBps = 0,
      slippageBps = 0,
      fillAt = "CLOSE",
    } = request.body ?? {};

    // ── Validation ──────────────────────────────────────────────────────────
    const errors: Array<{ field: string; message: string }> = [];

    if (!strategyVersionId) errors.push({ field: "strategyVersionId", message: "strategyVersionId is required (Phase 5 explicit version binding)" });
    if (!datasetId)         errors.push({ field: "datasetId",         message: "datasetId is required (dataset-first contract)" });

    if (!Number.isInteger(feeBps) || feeBps < 0 || feeBps > MAX_BPS) {
      errors.push({ field: "feeBps", message: `feeBps must be integer 0–${MAX_BPS}` });
    }
    if (!Number.isInteger(slippageBps) || slippageBps < 0 || slippageBps > MAX_BPS) {
      errors.push({ field: "slippageBps", message: `slippageBps must be integer 0–${MAX_BPS}` });
    }
    if (!ALLOWED_FILL_AT.includes(fillAt as FillAt)) {
      errors.push({ field: "fillAt", message: `fillAt must be one of: ${ALLOWED_FILL_AT.join(", ")}` });
    }

    if (errors.length > 0) {
      return problem(reply, 400, "Validation Error", "Invalid backtest request", { errors });
    }

    // ── Resolve StrategyVersion (workspace isolation via strategy) ────────────
    const strategyVersion = await prisma.strategyVersion.findUnique({
      where: { id: strategyVersionId },
      include: { strategy: true },
    });
    if (!strategyVersion || strategyVersion.strategy.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "StrategyVersion not found");
    }

    // ── Resolve dataset (workspace isolation) ────────────────────────────────
    const dataset = await prisma.marketDataset.findUnique({ where: { id: datasetId } });
    if (!dataset || dataset.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Dataset not found");
    }

    // ── Derive symbol / interval / range from dataset ───────────────────────
    const symbol   = dataset.symbol;
    const interval = candleIntervalToBybit(dataset.interval);
    const fromTs   = new Date(Number(dataset.fromTsMs));
    const toTs     = new Date(Number(dataset.toTsMs));

    const engineVersion = process.env.COMMIT_SHA ?? "unknown";

    // ── Create PENDING record ────────────────────────────────────────────────
    const bt = await prisma.backtestResult.create({
      data: {
        workspaceId:       workspace.id,
        strategyId:        strategyVersion.strategyId,
        strategyVersionId: strategyVersion.id,
        symbol,
        interval,
        fromTs,
        toTs,
        status:            "PENDING",
        // Reproducibility snapshot
        datasetId:         dataset.id,
        datasetHash:       dataset.datasetHash,
        feeBps,
        slippageBps,
        fillAt,
        engineVersion,
      },
      select: BACKTEST_SELECT,
    });

    // Run async (fire-and-forget) — pass dslJson for DSL-driven evaluation
    runBacktestAsync(bt.id, dataset.id, dataset.exchange, symbol, dataset.interval, strategyVersion.dslJson).catch(() => {
      // errors handled inside runBacktestAsync
    });

    return reply.status(202).send(bt);
  });

  // ── GET /lab/backtest/:id ── get result ─────────────────────────────────────
  app.get<{ Params: { id: string } }>("/lab/backtest/:id", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const bt = await prisma.backtestResult.findUnique({
      where: { id: request.params.id },
      select: BACKTEST_SELECT,
    });
    if (!bt || bt.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Backtest not found");
    }
    return reply.send(bt);
  });

  // ── GET /lab/backtests ── list for workspace ─────────────────────────────────
  app.get("/lab/backtests", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const list = await prisma.backtestResult.findMany({
      where: { workspaceId: workspace.id },
      orderBy: { createdAt: "desc" },
      take: 50,
      select: BACKTEST_SELECT,
    });
    return reply.send(list);
  });

  // ── GET /lab/backtests/compare ── side-by-side comparison of two runs (Phase 6, 23b1) ──
  app.get<{ Querystring: { a: string; b: string } }>("/lab/backtests/compare", {
    config: { rateLimit: { max: 20, timeWindow: "1 minute" } },
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const { a, b } = request.query ?? {};
    if (!a || !b) {
      return problem(reply, 400, "Validation Error", "Query params 'a' and 'b' (backtest IDs) are required");
    }
    if (a === b) {
      return problem(reply, 400, "Validation Error", "Cannot compare a run with itself");
    }

    const [runA, runB] = await Promise.all([
      prisma.backtestResult.findUnique({ where: { id: a }, select: BACKTEST_SELECT }),
      prisma.backtestResult.findUnique({ where: { id: b }, select: BACKTEST_SELECT }),
    ]);

    if (!runA || runA.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Run A not found");
    }
    if (!runB || runB.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Run B not found");
    }

    // Compute deltas from reportJson
    const reportA = (runA.reportJson ?? {}) as Record<string, unknown>;
    const reportB = (runB.reportJson ?? {}) as Record<string, unknown>;

    const num = (v: unknown) => (typeof v === "number" && Number.isFinite(v) ? v : null);

    const delta = {
      pnlDelta: num(reportA.totalPnlPct) !== null && num(reportB.totalPnlPct) !== null
        ? (num(reportA.totalPnlPct)! - num(reportB.totalPnlPct)!) : null,
      winrateDelta: num(reportA.winrate) !== null && num(reportB.winrate) !== null
        ? (num(reportA.winrate)! - num(reportB.winrate)!) : null,
      drawdownDelta: num(reportA.maxDrawdownPct) !== null && num(reportB.maxDrawdownPct) !== null
        ? (num(reportA.maxDrawdownPct)! - num(reportB.maxDrawdownPct)!) : null,
      tradeDelta: num(reportA.trades) !== null && num(reportB.trades) !== null
        ? (num(reportA.trades)! - num(reportB.trades)!) : null,
      sharpeDelta: num(reportA.sharpe) !== null && num(reportB.sharpe) !== null
        ? (num(reportA.sharpe)! - num(reportB.sharpe)!) : null,
    };

    // Task 26: enrich compare response with lineage data
    const lineageA = runA.strategyVersionId
      ? await prisma.strategyGraphVersion.findFirst({
          where: { strategyVersionId: runA.strategyVersionId as string },
          select: { id: true, version: true, label: true, isBaseline: true, strategyGraph: { select: { name: true } } },
        })
      : null;
    const lineageB = runB.strategyVersionId
      ? await prisma.strategyGraphVersion.findFirst({
          where: { strategyVersionId: runB.strategyVersionId as string },
          select: { id: true, version: true, label: true, isBaseline: true, strategyGraph: { select: { name: true } } },
        })
      : null;

    return reply.send({
      a: { ...runA, lineage: lineageA ? { graphVersionId: lineageA.id, graphVersion: lineageA.version, label: lineageA.label, isBaseline: lineageA.isBaseline, graphName: lineageA.strategyGraph.name } : null },
      b: { ...runB, lineage: lineageB ? { graphVersionId: lineageB.id, graphVersion: lineageB.version, label: lineageB.label, isBaseline: lineageB.isBaseline, graphName: lineageB.strategyGraph.name } : null },
      delta,
    });
  });

  // ── PATCH /lab/graph-versions/:id ── update label (Task 26) ─────────────────
  app.patch<{ Params: { id: string }; Body: { label?: string | null } }>("/lab/graph-versions/:id", {
    config: { rateLimit: { max: 30, timeWindow: "1 minute" } },
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const gv = await prisma.strategyGraphVersion.findUnique({
      where: { id: request.params.id },
      include: { strategyGraph: { select: { workspaceId: true } } },
    });
    if (!gv || gv.strategyGraph.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Graph version not found");
    }

    const { label } = request.body ?? {};
    if (label !== undefined && label !== null && typeof label !== "string") {
      return problem(reply, 400, "Validation Error", "label must be a string or null");
    }
    if (typeof label === "string" && label.length > 100) {
      return problem(reply, 400, "Validation Error", "label must be 100 characters or fewer");
    }

    const updated = await prisma.strategyGraphVersion.update({
      where: { id: gv.id },
      data: { label: label ?? null },
    });

    return reply.send({
      id: updated.id,
      version: updated.version,
      label: updated.label,
      isBaseline: updated.isBaseline,
      createdAt: updated.createdAt,
    });
  });

  // ── POST /lab/graph-versions/:id/baseline ── set/unset baseline (Task 26) ──
  app.post<{ Params: { id: string } }>("/lab/graph-versions/:id/baseline", {
    config: { rateLimit: { max: 10, timeWindow: "1 minute" } },
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const gv = await prisma.strategyGraphVersion.findUnique({
      where: { id: request.params.id },
      include: {
        strategyGraph: { select: { workspaceId: true } },
        strategyVersion: { select: { strategyId: true } },
      },
    });
    if (!gv || gv.strategyGraph.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Graph version not found");
    }

    const strategyId = gv.strategyVersion.strategyId;

    // Toggle: if already baseline → unset; otherwise set and clear previous
    if (gv.isBaseline) {
      const updated = await prisma.strategyGraphVersion.update({
        where: { id: gv.id },
        data: { isBaseline: false },
      });
      return reply.send({
        id: updated.id,
        version: updated.version,
        label: updated.label,
        isBaseline: updated.isBaseline,
      });
    }

    // Clear any existing baseline for this strategy
    const allVersionsForStrategy = await prisma.strategyGraphVersion.findMany({
      where: {
        strategyVersion: { strategyId },
        isBaseline: true,
      },
      select: { id: true },
    });

    if (allVersionsForStrategy.length > 0) {
      await Promise.all(
        allVersionsForStrategy.map((v) =>
          prisma.strategyGraphVersion.update({
            where: { id: v.id },
            data: { isBaseline: false },
          })
        )
      );
    }

    const updated = await prisma.strategyGraphVersion.update({
      where: { id: gv.id },
      data: { isBaseline: true },
    });

    return reply.send({
      id: updated.id,
      version: updated.version,
      label: updated.label,
      isBaseline: updated.isBaseline,
    });
  });

  // ── GET /lab/graph-versions ── list versions for a strategy (Task 26) ──────
  app.get<{ Querystring: { strategyId?: string; graphId?: string } }>("/lab/graph-versions", {
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const { strategyId, graphId } = request.query ?? {};
    if (!strategyId && !graphId) {
      return problem(reply, 400, "Validation Error", "Either strategyId or graphId query param is required");
    }

    const where: Record<string, unknown> = {};
    if (graphId) {
      // Verify workspace ownership of graph
      const graph = await prisma.strategyGraph.findUnique({ where: { id: graphId } });
      if (!graph || graph.workspaceId !== workspace.id) {
        return problem(reply, 404, "Not Found", "Graph not found");
      }
      where.strategyGraphId = graphId;
    }
    if (strategyId) {
      where.strategyVersion = { strategyId };
    }

    const versions = await prisma.strategyGraphVersion.findMany({
      where,
      orderBy: { createdAt: "desc" },
      take: 50,
      select: {
        id: true,
        version: true,
        label: true,
        isBaseline: true,
        blockLibraryVersion: true,
        strategyVersionId: true,
        strategyGraphId: true,
        createdAt: true,
      },
    });

    return reply.send(versions);
  });

  // ── POST /lab/backtest/sweep ── trigger parametric grid search (Phase C1) ──
  // Per docs/25-lab-improvements-plan.md §Phase C1
  app.post<{ Body: SweepRequestBody }>("/lab/backtest/sweep", {
    config: { rateLimit: { max: 5, timeWindow: "1 minute" } },
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const {
      datasetId,
      strategyVersionId,
      sweepParam,
      feeBps = 0,
      slippageBps = 0,
    } = request.body ?? {};

    // ── Validation ──────────────────────────────────────────────────────────
    if (!datasetId || !strategyVersionId || !sweepParam) {
      return problem(reply, 400, "Validation Error", "datasetId, strategyVersionId, and sweepParam are required");
    }

    if (!sweepParam.blockId || !sweepParam.paramName) {
      return problem(reply, 400, "Validation Error", "sweepParam.blockId and sweepParam.paramName are required");
    }

    const { from, to, step } = sweepParam;
    if (typeof from !== "number" || typeof to !== "number" || typeof step !== "number") {
      return problem(reply, 400, "Validation Error", "sweepParam.from, .to, .step must be numbers");
    }
    if (from >= to) {
      return problem(reply, 400, "Validation Error", "sweepParam.from must be less than sweepParam.to");
    }
    if (step <= 0) {
      return problem(reply, 400, "Validation Error", "sweepParam.step must be greater than 0");
    }

    const runCount = Math.floor((to - from) / step) + 1;

    // ── Guard: max 20 runs (docs/24 §8.3) ────────────────────────────────
    if (runCount > 20) {
      return problem(reply, 422, "Sweep Too Large", "Sweep exceeds maximum of 20 runs. Narrow the range or increase the step.");
    }

    if (!Number.isInteger(feeBps) || feeBps < 0 || feeBps > MAX_BPS) {
      return problem(reply, 400, "Validation Error", `feeBps must be integer 0–${MAX_BPS}`);
    }
    if (!Number.isInteger(slippageBps) || slippageBps < 0 || slippageBps > MAX_BPS) {
      return problem(reply, 400, "Validation Error", `slippageBps must be integer 0–${MAX_BPS}`);
    }

    // ── Resolve StrategyVersion (workspace isolation) ─────────────────────────
    const strategyVersion = await prisma.strategyVersion.findUnique({
      where: { id: strategyVersionId },
      include: { strategy: true },
    });
    if (!strategyVersion || strategyVersion.strategy.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "StrategyVersion not found");
    }

    // ── Resolve dataset (workspace isolation) ────────────────────────────────
    const dataset = await prisma.marketDataset.findUnique({ where: { id: datasetId } });
    if (!dataset || dataset.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Dataset not found");
    }

    // ── Guard: max 2 concurrent sweeps per workspace ─────────────────────────
    const activeSweeps = await prisma.backtestSweep.count({
      where: { workspaceId: workspace.id, status: { in: ["PENDING", "RUNNING"] } },
    });
    if (activeSweeps >= 2) {
      return problem(reply, 429, "Too Many Sweeps", "Maximum 2 concurrent sweeps per workspace. Wait for an existing sweep to complete.");
    }

    // ── Create PENDING sweep record ─────────────────────────────────────────
    const sweep = await prisma.backtestSweep.create({
      data: {
        workspaceId: workspace.id,
        strategyVersionId,
        datasetId,
        sweepParamJson: sweepParam as object,
        feeBps,
        slippageBps,
        runCount,
        status: "PENDING",
      },
    });

    // Fire-and-forget async sweep execution
    runSweepAsync(sweep.id).catch(() => {});

    return reply.status(202).send({
      sweepId: sweep.id,
      runCount,
      estimatedSeconds: runCount * 5,
    });
  });

  // ── GET /lab/backtest/sweep/:id ── poll sweep status/results (Phase C1) ────
  app.get<{ Params: { id: string } }>("/lab/backtest/sweep/:id", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const sweep = await prisma.backtestSweep.findUnique({ where: { id: request.params.id } });
    if (!sweep || sweep.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Sweep not found");
    }

    const results = (sweep.resultsJson as SweepRow[] | null) ?? [];
    const bestRow = results.length > 0
      ? results.reduce((best, r) => r.pnlPct > best.pnlPct ? r : best, results[0])
      : undefined;

    return reply.send({
      id: sweep.id,
      status: sweep.status.toLowerCase(),
      progress: sweep.progress,
      runCount: sweep.runCount,
      results,
      bestRow,
      createdAt: sweep.createdAt.toISOString(),
      updatedAt: sweep.updatedAt.toISOString(),
    });
  });

  // ── GET /lab/backtest/sweeps ── list sweeps for workspace ──────────────────
  app.get("/lab/backtest/sweeps", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const list = await prisma.backtestSweep.findMany({
      where: { workspaceId: workspace.id },
      orderBy: { createdAt: "desc" },
      take: 50,
    });
    return reply.send(list.map((s) => ({
      id: s.id,
      status: s.status.toLowerCase(),
      progress: s.progress,
      runCount: s.runCount,
      sweepParamJson: s.sweepParamJson,
      resultsJson: s.resultsJson,
      bestParamValue: s.bestParamValue,
      createdAt: s.createdAt.toISOString(),
      updatedAt: s.updatedAt.toISOString(),
    })));
  });

  // -------------------------------------------------------------------------
  // Research Journal — CRUD (Task 28)
  // -------------------------------------------------------------------------

  const VALID_JOURNAL_STATUSES = ["BASELINE", "PROMOTE", "DISCARD", "KEEP_TESTING"] as const;

  // POST /lab/journal — create journal entry
  app.post<{ Body: Record<string, unknown> }>("/lab/journal", {
    config: { rateLimit: { max: 30, timeWindow: "1 minute" } },
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const { strategyGraphVersionId, backtestResultId, hypothesis, whatChanged, expectedResult, actualResult, nextStep, status } = request.body ?? {};

    if (!strategyGraphVersionId || typeof strategyGraphVersionId !== "string") {
      return problem(reply, 400, "Validation Error", "strategyGraphVersionId is required");
    }
    if (!hypothesis || typeof hypothesis !== "string") {
      return problem(reply, 400, "Validation Error", "hypothesis is required");
    }
    if (!whatChanged || typeof whatChanged !== "string") {
      return problem(reply, 400, "Validation Error", "whatChanged is required");
    }
    if (!expectedResult || typeof expectedResult !== "string") {
      return problem(reply, 400, "Validation Error", "expectedResult is required");
    }
    if (status && !VALID_JOURNAL_STATUSES.includes(status as typeof VALID_JOURNAL_STATUSES[number])) {
      return problem(reply, 400, "Validation Error", `status must be one of: ${VALID_JOURNAL_STATUSES.join(", ")}`);
    }

    const entry = await prisma.labJournalEntry.create({
      data: {
        workspaceId: workspace.id,
        strategyGraphVersionId: strategyGraphVersionId as string,
        backtestResultId: (backtestResultId as string) ?? null,
        hypothesis: hypothesis as string,
        whatChanged: whatChanged as string,
        expectedResult: expectedResult as string,
        actualResult: (actualResult as string) ?? null,
        nextStep: (nextStep as string) ?? null,
        status: (status as typeof VALID_JOURNAL_STATUSES[number]) ?? "KEEP_TESTING",
      },
    });

    return reply.status(201).send(entry);
  });

  // GET /lab/journal?graphVersionId=X — list journal entries
  app.get<{ Querystring: { graphVersionId?: string; status?: string } }>("/lab/journal", {
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const { graphVersionId, status } = request.query;

    const where: Record<string, unknown> = { workspaceId: workspace.id };
    if (graphVersionId) where.strategyGraphVersionId = graphVersionId;
    if (status && VALID_JOURNAL_STATUSES.includes(status as typeof VALID_JOURNAL_STATUSES[number])) {
      where.status = status;
    }

    const entries = await prisma.labJournalEntry.findMany({
      where,
      orderBy: { createdAt: "desc" },
      take: 100,
    });

    return reply.send(entries);
  });

  // PATCH /lab/journal/:id — update journal entry
  app.patch<{ Params: { id: string }; Body: Record<string, unknown> }>("/lab/journal/:id", {
    config: { rateLimit: { max: 30, timeWindow: "1 minute" } },
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const existing = await prisma.labJournalEntry.findUnique({ where: { id: request.params.id } });
    if (!existing || existing.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Journal entry not found");
    }

    const { hypothesis, whatChanged, expectedResult, actualResult, nextStep, status, backtestResultId } = request.body ?? {};

    if (status && !VALID_JOURNAL_STATUSES.includes(status as typeof VALID_JOURNAL_STATUSES[number])) {
      return problem(reply, 400, "Validation Error", `status must be one of: ${VALID_JOURNAL_STATUSES.join(", ")}`);
    }

    const data: Record<string, unknown> = {};
    if (typeof hypothesis === "string") data.hypothesis = hypothesis;
    if (typeof whatChanged === "string") data.whatChanged = whatChanged;
    if (typeof expectedResult === "string") data.expectedResult = expectedResult;
    if (typeof actualResult === "string" || actualResult === null) data.actualResult = actualResult;
    if (typeof nextStep === "string" || nextStep === null) data.nextStep = nextStep;
    if (typeof backtestResultId === "string" || backtestResultId === null) data.backtestResultId = backtestResultId;
    if (status) data.status = status;

    const updated = await prisma.labJournalEntry.update({
      where: { id: existing.id },
      data,
    });

    return reply.send(updated);
  });

  // DELETE /lab/journal/:id — delete journal entry
  app.delete<{ Params: { id: string } }>("/lab/journal/:id", {
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const existing = await prisma.labJournalEntry.findUnique({ where: { id: request.params.id } });
    if (!existing || existing.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Journal entry not found");
    }

    await prisma.labJournalEntry.delete({ where: { id: existing.id } });
    return reply.status(204).send();
  });

  // ── Task 29 — AI Explainability endpoints ────────────────────────────────
  // Per docs/35-expansion-layer-tasks.md §Task 29, docs/24 §8.5
  // Safety: advisory only, no compiler/validation bypass, no trade execution,
  //         no secrets. Graceful degradation when AI_API_KEY not set (503).
  //         Rate limited: 5 req/min per endpoint.
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * Map explain-module errors to HTTP responses.
   * Centralizes error handling for all four explain endpoints.
   */
  function handleExplainError(
    err: unknown,
    request: { id: string; log: { warn: (...a: unknown[]) => void; error: (...a: unknown[]) => void } },
    reply: { status: (code: number) => { send: (body: unknown) => unknown } },
    endpoint: string,
  ): unknown {
    if (err instanceof ExplainInputError) {
      return problem(reply as never, 400, "Bad Request", err.message);
    }
    if (err instanceof ProviderError) {
      request.log.warn({ reqId: request.id, providerStatus: err.providerStatus }, `ai.explain.${endpoint}.provider_error`);
      if (err.providerStatus === 429) {
        return problem(reply as never, 429, "Too Many Requests", "AI rate limit reached, try again later");
      }
      return problem(reply as never, 502, "Bad Gateway", "AI provider error");
    }
    const isTimeout = err instanceof Error &&
      (err.name === "TimeoutError" || err.name === "AbortError" || err.message.includes("timed out"));
    if (isTimeout) {
      return problem(reply as never, 504, "Gateway Timeout", "AI request timed out");
    }
    request.log.error({ err, reqId: request.id }, `ai.explain.${endpoint}.unexpected_error`);
    return problem(reply as never, 502, "Bad Gateway", "AI provider error");
  }

  // POST /lab/explain/graph — Explain Graph: LLM summarizes strategy
  app.post<{ Body: ExplainGraphInput }>("/lab/explain/graph", {
    config: { rateLimit: { max: 5, timeWindow: "1 minute" } },
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    if (!process.env.AI_API_KEY) {
      return problem(reply, 503, "Service Unavailable", "AI not configured");
    }
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    try {
      const result = await explainGraph(request.body);
      return reply.send(result);
    } catch (err) {
      return handleExplainError(err, request, reply, "graph");
    }
  });

  // POST /lab/explain/validation — Explain Validation Issue: error + fix
  app.post<{ Body: ExplainValidationInput }>("/lab/explain/validation", {
    config: { rateLimit: { max: 5, timeWindow: "1 minute" } },
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    if (!process.env.AI_API_KEY) {
      return problem(reply, 503, "Service Unavailable", "AI not configured");
    }
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    try {
      const result = await explainValidation(request.body);
      return reply.send(result);
    } catch (err) {
      return handleExplainError(err, request, reply, "validation");
    }
  });

  // POST /lab/explain/delta — Explain Run Delta: differences summary
  app.post<{ Body: ExplainDeltaInput }>("/lab/explain/delta", {
    config: { rateLimit: { max: 5, timeWindow: "1 minute" } },
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    if (!process.env.AI_API_KEY) {
      return problem(reply, 503, "Service Unavailable", "AI not configured");
    }
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    try {
      const result = await explainDelta(request.body);
      return reply.send(result);
    } catch (err) {
      return handleExplainError(err, request, reply, "delta");
    }
  });

  // POST /lab/explain/risk — Suggest Safer Risk Config
  app.post<{ Body: ExplainRiskInput }>("/lab/explain/risk", {
    config: { rateLimit: { max: 5, timeWindow: "1 minute" } },
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    if (!process.env.AI_API_KEY) {
      return problem(reply, 503, "Service Unavailable", "AI not configured");
    }
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    try {
      const result = await suggestRisk(request.body);
      return reply.send(result);
    } catch (err) {
      return handleExplainError(err, request, reply, "risk");
    }
  });
}

// ---------------------------------------------------------------------------
// Sweep request / response types (Phase C1)
// ---------------------------------------------------------------------------

interface SweepRequestBody {
  datasetId: string;
  strategyVersionId: string;
  sweepParam: {
    blockId: string;
    paramName: string;
    from: number;
    to: number;
    step: number;
  };
  feeBps?: number;
  slippageBps?: number;
}

interface SweepRow {
  paramValue: number;
  backtestResultId: string;
  pnlPct: number;
  winRate: number;
  maxDrawdownPct: number;
  tradeCount: number;
  sharpe: number | null;
}

// ---------------------------------------------------------------------------
// Async sweep runner (Phase C1) — sequential grid search
// ---------------------------------------------------------------------------

async function runSweepAsync(sweepId: string): Promise<void> {
  try {
    const sweep = await prisma.backtestSweep.findUnique({ where: { id: sweepId } });
    if (!sweep) return;

    await prisma.backtestSweep.update({
      where: { id: sweepId },
      data: { status: "RUNNING" },
    });

    const sweepParam = sweep.sweepParamJson as { blockId: string; paramName: string; from: number; to: number; step: number };

    // Resolve strategy version and dataset
    const strategyVersion = await prisma.strategyVersion.findUnique({
      where: { id: sweep.strategyVersionId },
      include: { strategy: true },
    });
    if (!strategyVersion) throw new Error("StrategyVersion not found");

    const dataset = await prisma.marketDataset.findUnique({ where: { id: sweep.datasetId } });
    if (!dataset) throw new Error("Dataset not found");

    // Load candles once (shared across all runs)
    const dbCandles = await prisma.marketCandle.findMany({
      where: {
        exchange: dataset.exchange,
        symbol: dataset.symbol,
        interval: dataset.interval,
        openTimeMs: { gte: dataset.fromTsMs, lte: dataset.toTsMs },
      },
      orderBy: { openTimeMs: "asc" },
    });

    const candles = dbCandles.map((c) => ({
      openTime: Number(c.openTimeMs),
      open: Number(c.open),
      high: Number(c.high),
      low: Number(c.low),
      close: Number(c.close),
      volume: Number(c.volume),
    }));

    const dslJson = strategyVersion.dslJson;
    if (!dslJson) throw new Error("StrategyVersion has no dslJson");

    const symbol = dataset.symbol;
    const interval = candleIntervalToBybit(dataset.interval);
    const fromTs = new Date(Number(dataset.fromTsMs));
    const toTs = new Date(Number(dataset.toTsMs));
    const engineVersion = process.env.COMMIT_SHA ?? "unknown";

    const results: SweepRow[] = [];

    // Sequential sweep — mutate DSL per iteration
    for (let paramValue = sweepParam.from; paramValue <= sweepParam.to; paramValue += sweepParam.step) {
      // Round to avoid floating point drift
      const roundedParam = Math.round(paramValue * 1e8) / 1e8;

      // Clone DSL and inject the sweep parameter value into the target block
      const mutatedDsl = applyDslSweepParam(
        dslJson as Record<string, unknown>,
        sweepParam.blockId,
        sweepParam.paramName,
        roundedParam,
      );

      // Create a BacktestResult record for this run
      const bt = await prisma.backtestResult.create({
        data: {
          workspaceId: sweep.workspaceId,
          strategyId: strategyVersion.strategyId,
          strategyVersionId: strategyVersion.id,
          symbol,
          interval,
          fromTs,
          toTs,
          status: "RUNNING",
          datasetId: dataset.id,
          datasetHash: dataset.datasetHash,
          feeBps: sweep.feeBps,
          slippageBps: sweep.slippageBps,
          fillAt: "CLOSE",
          engineVersion,
        },
      });

      try {
        // DSL-driven backtest — sweep-mutated DSL for this iteration
        const report = runBacktest(candles, mutatedDsl, {
          feeBps: sweep.feeBps,
          slippageBps: sweep.slippageBps,
          fillAt: "CLOSE",
        });

        await prisma.backtestResult.update({
          where: { id: bt.id },
          data: { status: "DONE", reportJson: report as unknown as object },
        });

        // Compute Sharpe ratio (annualised, assuming 365 trading days)
        const sharpe = computeSharpe(report.tradeLog.map((t) => t.pnlPct));

        results.push({
          paramValue: roundedParam,
          backtestResultId: bt.id,
          pnlPct: report.totalPnlPct,
          winRate: report.winrate,
          maxDrawdownPct: report.maxDrawdownPct,
          tradeCount: report.trades,
          sharpe,
        });
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        await prisma.backtestResult.update({
          where: { id: bt.id },
          data: { status: "FAILED", errorMessage: msg },
        }).catch(() => undefined);

        results.push({
          paramValue: roundedParam,
          backtestResultId: bt.id,
          pnlPct: 0,
          winRate: 0,
          maxDrawdownPct: 0,
          tradeCount: 0,
          sharpe: null,
        });
      }

      // Update progress
      await prisma.backtestSweep.update({
        where: { id: sweepId },
        data: {
          progress: results.length,
          resultsJson: results as unknown as object[],
        },
      });
    }

    // Find best param value by PnL
    const bestRow = results.reduce((best, r) => r.pnlPct > best.pnlPct ? r : best, results[0]);

    await prisma.backtestSweep.update({
      where: { id: sweepId },
      data: {
        status: "DONE",
        progress: results.length,
        resultsJson: results as unknown as object[],
        bestParamValue: bestRow?.paramValue ?? null,
      },
    });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    await prisma.backtestSweep.update({
      where: { id: sweepId },
      data: { status: "FAILED" },
    }).catch(() => undefined);
    logger.error({ sweepId, error: msg }, "Sweep failed");
  }
}

/** Compute annualised Sharpe ratio from per-trade PnL % array */
function computeSharpe(pnlPcts: number[]): number | null {
  if (pnlPcts.length < 2) return null;
  const mean = pnlPcts.reduce((s, v) => s + v, 0) / pnlPcts.length;
  const variance = pnlPcts.reduce((s, v) => s + (v - mean) ** 2, 0) / (pnlPcts.length - 1);
  const stdDev = Math.sqrt(variance);
  if (stdDev === 0) return null;
  return Math.round((mean / stdDev) * Math.sqrt(252) * 100) / 100;
}

// ---------------------------------------------------------------------------
// Async backtest runner — loads candles from DB (dataset-first)
// Phase 5: uses explicit strategyVersionId for DSL lookup (reproducible runs)
// ---------------------------------------------------------------------------

async function runBacktestAsync(
  btId: string,
  datasetId: string,
  exchange: string,
  symbol: string,
  interval: import("@prisma/client").CandleInterval,
  dslJson: unknown,
): Promise<void> {
  try {
    await prisma.backtestResult.update({
      where: { id: btId },
      data: { status: "RUNNING" },
    });

    if (!dslJson) throw new Error("dslJson is required for DSL-driven backtest");

    // Load dataset boundaries
    const dataset = await prisma.marketDataset.findUnique({ where: { id: datasetId } });
    if (!dataset) throw new Error(`Dataset ${datasetId} not found`);

    // Load candles from shared DB table (no workspace filter — candles are global)
    const dbCandles = await prisma.marketCandle.findMany({
      where: {
        exchange,
        symbol,
        interval,
        openTimeMs: {
          gte: dataset.fromTsMs,
          lte: dataset.toTsMs,
        },
      },
      orderBy: { openTimeMs: "asc" },
    });

    // Map to backtest engine format
    const candles = dbCandles.map((c) => ({
      openTime: Number(c.openTimeMs),
      open:   Number(c.open),
      high:   Number(c.high),
      low:    Number(c.low),
      close:  Number(c.close),
      volume: Number(c.volume),
    }));

    // Fetch fee/slippage from the BacktestResult record
    const btRecord = await prisma.backtestResult.findUnique({ where: { id: btId } });

    // DSL-driven backtest — behavior determined entirely by compiled DSL
    const report = runBacktest(candles, dslJson, {
      feeBps:      btRecord?.feeBps      ?? 0,
      slippageBps: btRecord?.slippageBps ?? 0,
      fillAt:      "CLOSE",
    });

    await prisma.backtestResult.update({
      where: { id: btId },
      data: {
        status:     "DONE",
        reportJson: report as unknown as object,
      },
    });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    await prisma.backtestResult.update({
      where: { id: btId },
      data: { status: "FAILED", errorMessage: msg },
    }).catch(() => undefined);
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Map CandleInterval enum → Bybit kline interval string */
function candleIntervalToBybit(interval: import("@prisma/client").CandleInterval): string {
  switch (interval) {
    case "M1":  return "1";
    case "M5":  return "5";
    case "M15": return "15";
    case "M30": return "30";
    case "H1":  return "60";
    case "H4":  return "240";
    case "D1":  return "D";
    default:    return "15";
  }
}
