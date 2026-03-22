import type { FastifyInstance } from "fastify";
import { prisma } from "../lib/prisma.js";
import { problem } from "../lib/problem.js";
import { resolveWorkspace } from "../lib/workspace.js";
import { runBacktest } from "../lib/backtest.js";
import { compileGraph } from "../lib/graphCompiler.js";
import type { GraphJson } from "../lib/graphCompiler.js";

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

    await prisma.strategyGraphVersion.create({
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

    // ── Guard: max 50 runs ──────────────────────────────────────────────────
    if (runCount > 50) {
      return problem(reply, 422, "Sweep Too Large", "Sweep exceeds maximum of 50 runs. Narrow the range or increase the step.");
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

    // Sequential sweep
    for (let paramValue = sweepParam.from; paramValue <= sweepParam.to; paramValue += sweepParam.step) {
      // Round to avoid floating point drift
      const roundedParam = Math.round(paramValue * 1e8) / 1e8;

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
        // DSL-driven backtest — same evaluator path as single backtest
        const report = runBacktest(candles, dslJson, {
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
    console.error(`Sweep ${sweepId} failed:`, msg);
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
