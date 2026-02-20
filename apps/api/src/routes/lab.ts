import type { FastifyInstance } from "fastify";
import { prisma } from "../lib/prisma.js";
import { problem } from "../lib/problem.js";
import { resolveWorkspace } from "../lib/workspace.js";
import { fetchCandles } from "../lib/bybitCandles.js";
import { runBacktest } from "../lib/backtest.js";

// Valid Bybit kline intervals for backtest (MVP subset)
const VALID_INTERVALS = ["1", "5", "15", "60"] as const;
type Interval = typeof VALID_INTERVALS[number];

// Max candles to load per backtest (limits execution time)
const MAX_CANDLES = 2000;

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

interface StartBacktestBody {
  strategyId: string;
  symbol?: string;
  interval?: Interval;
  fromTs: string; // ISO date string
  toTs: string;   // ISO date string
}

export async function labRoutes(app: FastifyInstance) {
  // ── POST /lab/backtest ── trigger a new backtest ──────────────────────────
  app.post<{ Body: StartBacktestBody }>("/lab/backtest", {
    config: { rateLimit: { max: 5, timeWindow: "1 minute" } },
  }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const { strategyId, symbol: bodySymbol, interval: bodyInterval, fromTs, toTs } =
      request.body ?? {};

    // Validate required fields
    const errors: Array<{ field: string; message: string }> = [];
    if (!strategyId) errors.push({ field: "strategyId", message: "strategyId is required" });
    if (!fromTs) errors.push({ field: "fromTs", message: "fromTs is required (ISO date)" });
    if (!toTs) errors.push({ field: "toTs", message: "toTs is required (ISO date)" });
    if (bodyInterval && !VALID_INTERVALS.includes(bodyInterval)) {
      errors.push({ field: "interval", message: `interval must be one of: ${VALID_INTERVALS.join(", ")}` });
    }
    if (errors.length > 0) {
      return problem(reply, 400, "Validation Error", "Invalid backtest request", { errors });
    }

    const fromDate = new Date(fromTs);
    const toDate = new Date(toTs);
    if (isNaN(fromDate.getTime()) || isNaN(toDate.getTime())) {
      return problem(reply, 400, "Validation Error", "fromTs and toTs must be valid ISO dates");
    }
    if (fromDate >= toDate) {
      return problem(reply, 400, "Validation Error", "fromTs must be before toTs");
    }

    // Resolve strategy (must belong to workspace)
    const strategy = await prisma.strategy.findUnique({ where: { id: strategyId } });
    if (!strategy || strategy.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Strategy not found");
    }

    const symbol = bodySymbol ?? strategy.symbol;
    const interval = bodyInterval ?? intervalFromTimeframe(strategy.timeframe);

    // Create PENDING record
    const bt = await prisma.backtestResult.create({
      data: {
        workspaceId: workspace.id,
        strategyId: strategy.id,
        symbol,
        interval,
        fromTs: fromDate,
        toTs: toDate,
        status: "PENDING",
      },
    });

    // Run async (fire-and-forget) — update record when done
    runBacktestAsync(bt.id, symbol, interval, fromDate, toDate).catch(() => {
      // errors are already handled inside runBacktestAsync
    });

    return reply.status(202).send(bt);
  });

  // ── GET /lab/backtest/:id ── get result ────────────────────────────────────
  app.get<{ Params: { id: string } }>("/lab/backtest/:id", async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const bt = await prisma.backtestResult.findUnique({ where: { id: request.params.id } });
    if (!bt || bt.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Backtest not found");
    }
    return reply.send(bt);
  });

  // ── GET /lab/backtests ── list for workspace ───────────────────────────────
  app.get("/lab/backtests", async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const list = await prisma.backtestResult.findMany({
      where: { workspaceId: workspace.id },
      orderBy: { createdAt: "desc" },
      take: 50,
      select: {
        id: true,
        strategyId: true,
        symbol: true,
        interval: true,
        fromTs: true,
        toTs: true,
        status: true,
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

    // Fetch strategy to get riskPct
    const bt = await prisma.backtestResult.findUnique({ where: { id: btId } });
    const strategy = bt
      ? await prisma.strategy.findUnique({
          where: { id: bt.strategyId },
          include: { versions: { orderBy: { version: "desc" }, take: 1 } },
        })
      : null;

    const riskPct = extractRiskPct(strategy?.versions[0]?.dslJson);

    const candles = await fetchCandles(
      symbol,
      interval,
      fromDate.getTime(),
      toDate.getTime(),
      MAX_CANDLES,
    );

    const report = runBacktest(candles, riskPct);

    await prisma.backtestResult.update({
      where: { id: btId },
      data: {
        status: "DONE",
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
