import type { FastifyInstance } from "fastify";
import { prisma } from "../lib/prisma.js";
import { problem } from "../lib/problem.js";
import { resolveWorkspace } from "../lib/workspace.js";
import { runBacktest } from "../lib/backtest.js";

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
 * Stage 19 dataset-first backtest request.
 * datasetId is required — the dataset provides symbol/interval/range + candles.
 * Legacy range-based fields (fromTs/toTs/symbol/interval) are not accepted;
 * the dataset is the single source of truth (spec §10.1).
 */
interface StartBacktestBody {
  strategyId: string;
  datasetId: string;
  feeBps?: number;
  slippageBps?: number;
  fillAt?: FillAt;
}

/** Fields returned in list/detail views (includes Stage 19b additions) */
const BACKTEST_SELECT = {
  id: true,
  workspaceId: true,
  strategyId: true,
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

export async function labRoutes(app: FastifyInstance) {
  // ── POST /lab/backtest ── trigger a new backtest (dataset-first) ──────────
  app.post<{ Body: StartBacktestBody }>("/lab/backtest", {
    config: { rateLimit: { max: 5, timeWindow: "1 minute" } },
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const {
      strategyId,
      datasetId,
      feeBps = 0,
      slippageBps = 0,
      fillAt = "CLOSE",
    } = request.body ?? {};

    // ── Validation ──────────────────────────────────────────────────────────
    const errors: Array<{ field: string; message: string }> = [];

    if (!strategyId) errors.push({ field: "strategyId", message: "strategyId is required" });
    if (!datasetId)  errors.push({ field: "datasetId",  message: "datasetId is required (Stage 19 dataset-first contract)" });

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

    // ── Resolve strategy (workspace isolation) ───────────────────────────────
    const strategy = await prisma.strategy.findUnique({ where: { id: strategyId } });
    if (!strategy || strategy.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Strategy not found");
    }

    // ── Resolve dataset (workspace isolation) ────────────────────────────────
    const dataset = await prisma.marketDataset.findUnique({ where: { id: datasetId } });
    if (!dataset || dataset.workspaceId !== workspace.id) {
      // 404 rather than 403 to avoid leaking existence of other workspace datasets
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
        workspaceId:  workspace.id,
        strategyId:   strategy.id,
        symbol,
        interval,
        fromTs,
        toTs,
        status:       "PENDING",
        // Stage 19b reproducibility snapshot
        datasetId:    dataset.id,
        datasetHash:  dataset.datasetHash,
        feeBps,
        slippageBps,
        fillAt,
        engineVersion,
      },
      select: BACKTEST_SELECT,
    });

    // Run async (fire-and-forget)
    runBacktestAsync(bt.id, dataset.id, dataset.exchange, symbol, dataset.interval).catch(() => {
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
}

// ---------------------------------------------------------------------------
// Async backtest runner — loads candles from DB (dataset-first)
// ---------------------------------------------------------------------------

async function runBacktestAsync(
  btId: string,
  datasetId: string,
  exchange: string,
  symbol: string,
  interval: import("@prisma/client").CandleInterval,
): Promise<void> {
  try {
    await prisma.backtestResult.update({
      where: { id: btId },
      data: { status: "RUNNING" },
    });

    // Fetch strategy + latest version for riskPct
    const bt = await prisma.backtestResult.findUnique({ where: { id: btId } });
    const strategy = bt
      ? await prisma.strategy.findUnique({
          where: { id: bt.strategyId },
          include: { versions: { orderBy: { version: "desc" }, take: 1 } },
        })
      : null;

    const riskPct = extractRiskPct(strategy?.versions[0]?.dslJson);

    // Load dataset boundaries (needed for fromTsMs/toTsMs range)
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

    const report = runBacktest(candles, riskPct);

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

/** Extract riskPerTradePct from DSL JSON, defaulting to 1.0 */
function extractRiskPct(dslJson: unknown): number {
  if (!dslJson || typeof dslJson !== "object") return 1.0;
  const dsl = dslJson as Record<string, unknown>;
  const risk = dsl["risk"];
  if (!risk || typeof risk !== "object") return 1.0;
  const r = risk as Record<string, unknown>;
  const pct = Number(r["riskPerTradePct"]);
  return Number.isFinite(pct) && pct > 0 ? pct : 1.0;
}

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
