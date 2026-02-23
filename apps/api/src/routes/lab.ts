import type { FastifyInstance } from "fastify";
import { prisma } from "../lib/prisma.js";
import { problem } from "../lib/problem.js";
import { resolveWorkspace } from "../lib/workspace.js";
import { fetchCandles } from "../lib/bybitCandles.js";
import { runBacktest } from "../lib/backtest.js";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Current backtest algorithm version — bump when algorithm changes */
export const ENGINE_VERSION = "1";

/** Valid Bybit kline intervals for backtest (MVP subset) */
const VALID_INTERVALS = ["1", "5", "15", "60"] as const;
type Interval = typeof VALID_INTERVALS[number];

/** Max candles to load per backtest (limits execution time) */
const MAX_CANDLES = 2000;

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

interface StartBacktestBody {
  /** Preferred: pinned version for exact reproducibility */
  strategyVersionId?: string;
  /** Fallback: strategy ID (resolves to latest version) */
  strategyId?: string;
  symbol?: string;
  interval?: Interval;
  fromTs: string; // ISO date string
  toTs: string;   // ISO date string
}

export async function labRoutes(app: FastifyInstance) {

  // ── POST /lab/backtest ── trigger a new backtest ───────────────────────────
  app.post<{ Body: StartBacktestBody }>("/lab/backtest", {
    config: { rateLimit: { max: 5, timeWindow: "1 minute" } },
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const {
      strategyVersionId: bodyVersionId,
      strategyId: bodyStrategyId,
      symbol: bodySymbol,
      interval: bodyInterval,
      fromTs,
      toTs,
    } = request.body ?? {};

    // Require at least one strategy reference
    const errors: Array<{ field: string; message: string }> = [];
    if (!bodyVersionId && !bodyStrategyId) {
      errors.push({ field: "strategyVersionId", message: "strategyVersionId (or strategyId) is required" });
    }
    if (!fromTs) errors.push({ field: "fromTs", message: "fromTs is required (ISO date)" });
    if (!toTs)   errors.push({ field: "toTs",   message: "toTs is required (ISO date)" });
    if (bodyInterval && !VALID_INTERVALS.includes(bodyInterval)) {
      errors.push({ field: "interval", message: `interval must be one of: ${VALID_INTERVALS.join(", ")}` });
    }
    if (errors.length > 0) {
      return problem(reply, 400, "Validation Error", "Invalid backtest request", { errors });
    }

    const fromDate = new Date(fromTs);
    const toDate   = new Date(toTs);
    if (isNaN(fromDate.getTime()) || isNaN(toDate.getTime())) {
      return problem(reply, 400, "Validation Error", "fromTs and toTs must be valid ISO dates");
    }
    if (fromDate >= toDate) {
      return problem(reply, 400, "Validation Error", "fromTs must be before toTs");
    }

    // ---------------------------------------------------------------------------
    // Resolve strategy + version with cross-workspace checks
    // ---------------------------------------------------------------------------
    let resolvedStrategyId: string;
    let resolvedVersionId: string | null = null;
    let resolvedSymbol: string;
    let resolvedInterval: string;

    if (bodyVersionId) {
      // Preferred path: strategyVersionId provided — exact reproducibility
      const version = await prisma.strategyVersion.findUnique({
        where: { id: bodyVersionId },
        include: { strategy: true },
      });
      if (!version || version.strategy.workspaceId !== workspace.id) {
        return problem(reply, 403, "Forbidden", "Strategy version not found in this workspace");
      }
      resolvedVersionId  = version.id;
      resolvedStrategyId = version.strategyId;
      resolvedSymbol     = bodySymbol ?? version.strategy.symbol;
      resolvedInterval   = bodyInterval ?? intervalFromTimeframe(version.strategy.timeframe);
    } else {
      // Fallback: strategyId — resolves to latest version
      const strategy = await prisma.strategy.findUnique({ where: { id: bodyStrategyId! } });
      if (!strategy || strategy.workspaceId !== workspace.id) {
        return problem(reply, 403, "Forbidden", "Strategy not found in this workspace");
      }
      const latestVersion = await prisma.strategyVersion.findFirst({
        where: { strategyId: strategy.id },
        orderBy: { version: "desc" },
      });
      resolvedVersionId  = latestVersion?.id ?? null;
      resolvedStrategyId = strategy.id;
      resolvedSymbol     = bodySymbol ?? strategy.symbol;
      resolvedInterval   = bodyInterval ?? intervalFromTimeframe(strategy.timeframe);
    }

    // Create PENDING record
    const bt = await prisma.backtestResult.create({
      data: {
        workspaceId:       workspace.id,
        strategyId:        resolvedStrategyId,
        strategyVersionId: resolvedVersionId,
        symbol:            resolvedSymbol,
        interval:          resolvedInterval,
        fromTs:            fromDate,
        toTs:              toDate,
        engineVersion:     ENGINE_VERSION,
        status:            "PENDING",
      },
    });

    // Fire-and-forget — errors handled inside
    runBacktestAsync(
      bt.id,
      resolvedStrategyId,
      resolvedVersionId,
      resolvedSymbol,
      resolvedInterval,
      fromDate,
      toDate,
    ).catch(() => undefined);

    return reply.status(202).send(bt);
  });

  // ── GET /lab/backtest/:id ── get full record ───────────────────────────────
  app.get<{ Params: { id: string } }>("/lab/backtest/:id", {
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const bt = await prisma.backtestResult.findUnique({ where: { id: request.params.id } });
    if (!bt || bt.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Backtest not found");
    }
    return reply.send(bt);
  });

  // ── GET /lab/backtest/:id/result ── clean result summary ──────────────────
  app.get<{ Params: { id: string } }>("/lab/backtest/:id/result", {
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const bt = await prisma.backtestResult.findUnique({
      where: { id: request.params.id },
      select: {
        id: true,
        workspaceId: true,
        strategyId: true,
        strategyVersionId: true,
        symbol: true,
        interval: true,
        fromTs: true,
        toTs: true,
        status: true,
        engineVersion: true,
        reportJson: true,
        errorMessage: true,
        createdAt: true,
        updatedAt: true,
      },
    });
    if (!bt || bt.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Backtest not found");
    }
    if (bt.status !== "DONE") {
      return reply.status(202).send({
        id:           bt.id,
        status:       bt.status,
        errorMessage: bt.errorMessage ?? null,
      });
    }
    return reply.send({
      id:                bt.id,
      strategyId:        bt.strategyId,
      strategyVersionId: bt.strategyVersionId,
      symbol:            bt.symbol,
      interval:          bt.interval,
      fromTs:            bt.fromTs,
      toTs:              bt.toTs,
      engineVersion:     bt.engineVersion,
      metrics:           bt.reportJson,
      createdAt:         bt.createdAt,
    });
  });

  // ── GET /lab/backtests ── list for workspace ───────────────────────────────
  app.get("/lab/backtests", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const list = await prisma.backtestResult.findMany({
      where: { workspaceId: workspace.id },
      orderBy: { createdAt: "desc" },
      take: 50,
      select: {
        id: true,
        strategyId: true,
        strategyVersionId: true,
        symbol: true,
        interval: true,
        fromTs: true,
        toTs: true,
        status: true,
        engineVersion: true,
        reportJson: true,
        errorMessage: true,
        createdAt: true,
      },
    });
    return reply.send(list);
  });
}

// ---------------------------------------------------------------------------
// Async backtest runner
// ---------------------------------------------------------------------------

async function runBacktestAsync(
  btId: string,
  strategyId: string,
  strategyVersionId: string | null,
  symbol: string,
  interval: string,
  fromDate: Date,
  toDate: Date,
): Promise<void> {
  try {
    await prisma.backtestResult.update({
      where: { id: btId },
      data: { status: "RUNNING" },
    });

    // Resolve riskPct: prefer pinned version for determinism, fall back to latest
    const versionRecord = strategyVersionId
      ? await prisma.strategyVersion.findUnique({ where: { id: strategyVersionId } })
      : await prisma.strategyVersion.findFirst({
          where: { strategyId },
          orderBy: { version: "desc" },
        });

    const riskPct = extractRiskPct(versionRecord?.dslJson);

    const candles = await fetchCandles(
      symbol,
      interval,
      fromDate.getTime(),
      toDate.getTime(),
      MAX_CANDLES,
    );

    const report = runBacktest(candles, riskPct);

    // Store metrics without the full trade log (keep reportJson compact)
    const { tradeLog: _ignored, ...metrics } = report;

    await prisma.backtestResult.update({
      where: { id: btId },
      data: {
        status: "DONE",
        reportJson: {
          ...metrics,
          engineVersion: ENGINE_VERSION,
        } as unknown as object,
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
  const dsl  = dslJson as Record<string, unknown>;
  const risk = dsl["risk"];
  if (!risk || typeof risk !== "object") return 1.0;
  const r   = risk as Record<string, unknown>;
  const pct = Number(r["riskPerTradePct"]);
  return Number.isFinite(pct) && pct > 0 ? pct : 1.0;
}

/** Map DB Timeframe enum → Bybit interval string */
function intervalFromTimeframe(tf: string): string {
  switch (tf) {
    case "M1":  return "1";
    case "M5":  return "5";
    case "M15": return "15";
    case "H1":  return "60";
    default:    return "15";
  }
}
