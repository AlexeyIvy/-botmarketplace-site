import type { FastifyInstance } from "fastify";
import { prisma } from "../lib/prisma.js";
import { problem } from "../lib/problem.js";
import { resolveWorkspace } from "../lib/workspace.js";

const VALID_TIMEFRAMES = ["M1", "M5", "M15", "H1"] as const;

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CreateBotBody {
  name: string;
  strategyVersionId: string;
  symbol: string;
  timeframe: string;
}

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

export async function botRoutes(app: FastifyInstance) {
  // GET /bots — list bots for workspace
  app.get("/bots", async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const bots = await prisma.bot.findMany({
      where: { workspaceId: workspace.id },
      orderBy: { updatedAt: "desc" },
      select: {
        id: true,
        name: true,
        symbol: true,
        timeframe: true,
        status: true,
        strategyVersionId: true,
        updatedAt: true,
      },
    });
    return reply.send(bots);
  });

  // POST /bots — create a new bot (DRAFT)
  app.post<{ Body: CreateBotBody }>("/bots", async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const { name, strategyVersionId, symbol, timeframe } = request.body ?? {};

    // --- field validation ---
    const errors: Array<{ field: string; message: string }> = [];
    if (!name || typeof name !== "string") {
      errors.push({ field: "name", message: "name is required" });
    }
    if (!strategyVersionId || typeof strategyVersionId !== "string") {
      errors.push({ field: "strategyVersionId", message: "strategyVersionId is required" });
    }
    if (!symbol || typeof symbol !== "string") {
      errors.push({ field: "symbol", message: "symbol is required" });
    }
    if (!timeframe || !VALID_TIMEFRAMES.includes(timeframe as typeof VALID_TIMEFRAMES[number])) {
      errors.push({ field: "timeframe", message: `timeframe must be one of: ${VALID_TIMEFRAMES.join(", ")}` });
    }
    if (errors.length > 0) {
      return problem(reply, 400, "Validation Error", "Invalid bot payload", { errors });
    }

    // --- verify strategyVersion exists and belongs to same workspace ---
    const sv = await prisma.strategyVersion.findUnique({
      where: { id: strategyVersionId },
      include: { strategy: { select: { workspaceId: true } } },
    });
    if (!sv || sv.strategy.workspaceId !== workspace.id) {
      return problem(reply, 400, "Bad Request", "strategyVersionId not found in this workspace");
    }

    // --- unique name check ---
    const existing = await prisma.bot.findUnique({
      where: { workspaceId_name: { workspaceId: workspace.id, name } },
    });
    if (existing) {
      return problem(reply, 409, "Conflict", `Bot "${name}" already exists in this workspace`);
    }

    const bot = await prisma.bot.create({
      data: {
        workspaceId: workspace.id,
        name,
        strategyVersionId,
        symbol,
        timeframe: timeframe as typeof VALID_TIMEFRAMES[number],
        status: "DRAFT",
      },
    });
    return reply.status(201).send(bot);
  });

  // GET /bots/:id — get single bot (must belong to workspace)
  app.get<{ Params: { id: string } }>("/bots/:id", async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const bot = await prisma.bot.findUnique({
      where: { id: request.params.id },
      include: {
        strategyVersion: {
          include: { strategy: { select: { id: true, name: true } } },
        },
        runs: {
          orderBy: { createdAt: "desc" },
          take: 1,
          select: {
            id: true,
            state: true,
            startedAt: true,
            stoppedAt: true,
            errorCode: true,
            createdAt: true,
          },
        },
      },
    });
    if (!bot || bot.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Bot not found");
    }

    const { runs, ...rest } = bot;
    return reply.send({ ...rest, lastRun: runs[0] ?? null });
  });
}
