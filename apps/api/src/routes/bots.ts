import type { FastifyInstance } from "fastify";
import { prisma } from "../lib/prisma.js";
import { problem } from "../lib/problem.js";
import { resolveWorkspace } from "../lib/workspace.js";
import {
  listBotPositions,
  getActiveBotPosition,
  getPositionEvents,
  calcUnrealisedPnl,
  type PositionSnapshot,
} from "../lib/positionManager.js";

const VALID_TIMEFRAMES = ["M1", "M5", "M15", "H1"] as const;

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CreateBotBody {
  name: string;
  strategyVersionId: string;
  symbol: string;
  timeframe: string;
  exchangeConnectionId?: string;
}

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

export async function botRoutes(app: FastifyInstance) {
  // GET /bots — list bots for workspace
  app.get("/bots", { onRequest: [app.authenticate] }, async (request, reply) => {
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
        exchangeConnectionId: true,
        updatedAt: true,
      },
    });
    return reply.send(bots);
  });

  // POST /bots — create a new bot (DRAFT)
  app.post<{ Body: CreateBotBody }>("/bots", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const { name, strategyVersionId, symbol, timeframe, exchangeConnectionId } = request.body ?? {};

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

    // --- verify exchangeConnectionId if provided ---
    if (exchangeConnectionId !== undefined && exchangeConnectionId !== null) {
      const conn = await prisma.exchangeConnection.findUnique({ where: { id: exchangeConnectionId } });
      if (!conn || conn.workspaceId !== workspace.id) {
        return problem(reply, 400, "Bad Request", "exchangeConnectionId not found in this workspace");
      }
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
        exchangeConnectionId: exchangeConnectionId ?? null,
        symbol,
        timeframe: timeframe as typeof VALID_TIMEFRAMES[number],
        status: "DRAFT",
      },
    });
    return reply.status(201).send(bot);
  });

  // PATCH /bots/:id — update name or exchangeConnectionId
  app.patch<{ Params: { id: string }; Body: { name?: string; exchangeConnectionId?: string | null } }>(
    "/bots/:id",
    { onRequest: [app.authenticate] },
    async (request, reply) => {
      const workspace = await resolveWorkspace(request, reply);
      if (!workspace) return;

      const bot = await prisma.bot.findUnique({ where: { id: request.params.id } });
      if (!bot || bot.workspaceId !== workspace.id) {
        return problem(reply, 404, "Not Found", "Bot not found");
      }

      const { name, exchangeConnectionId } = request.body ?? {};

      const updateData: Record<string, unknown> = {};

      if (name !== undefined) {
        if (typeof name !== "string" || name.trim() === "") {
          return problem(reply, 400, "Validation Error", "name must be a non-empty string");
        }
        // Check uniqueness if name is changing
        if (name !== bot.name) {
          const existing = await prisma.bot.findUnique({
            where: { workspaceId_name: { workspaceId: workspace.id, name } },
          });
          if (existing) {
            return problem(reply, 409, "Conflict", `Bot "${name}" already exists in this workspace`);
          }
        }
        updateData.name = name;
      }

      if (exchangeConnectionId !== undefined) {
        if (exchangeConnectionId !== null) {
          const conn = await prisma.exchangeConnection.findUnique({ where: { id: exchangeConnectionId } });
          if (!conn || conn.workspaceId !== workspace.id) {
            return problem(reply, 400, "Bad Request", "exchangeConnectionId not found in this workspace");
          }
        }
        updateData.exchangeConnectionId = exchangeConnectionId;
      }

      if (Object.keys(updateData).length === 0) {
        return problem(reply, 400, "Validation Error", "No updatable fields provided (name, exchangeConnectionId)");
      }

      const updated = await prisma.bot.update({
        where: { id: bot.id },
        data: updateData,
      });

      return reply.send(updated);
    },
  );

  // GET /bots/:id — get single bot (must belong to workspace)
  app.get<{ Params: { id: string } }>("/bots/:id", { onRequest: [app.authenticate] }, async (request, reply) => {
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
            durationMinutes: true,
            createdAt: true,
          },
        },
      },
    });
    if (!bot || bot.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Bot not found");
    }

    const { runs, ...rest } = bot;

    // Stage 3 (#127): include active position summary
    const activePosition = await getActiveBotPosition(bot.id, bot.symbol);

    return reply.send({
      ...rest,
      lastRun: runs[0] ?? null,
      activePosition: activePosition ?? null,
    });
  });

  // GET /bots/:id/runs — list runs for a bot
  app.get<{
    Params: { id: string };
    Querystring: { limit?: string; state?: string };
  }>("/bots/:id/runs", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const bot = await prisma.bot.findUnique({ where: { id: request.params.id } });
    if (!bot || bot.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Bot not found");
    }

    const limit = Math.min(Number(request.query?.limit ?? 20), 100);
    const stateFilter = request.query?.state;

    const runs = await prisma.botRun.findMany({
      where: {
        botId: bot.id,
        ...(stateFilter ? { state: stateFilter as import("@prisma/client").BotRunState } : {}),
      },
      orderBy: { createdAt: "desc" },
      take: limit,
      select: {
        id: true,
        state: true,
        symbol: true,
        startedAt: true,
        stoppedAt: true,
        errorCode: true,
        durationMinutes: true,
        leaseOwner: true,
        createdAt: true,
        updatedAt: true,
      },
    });

    return reply.send(runs);
  });

  // GET /bots/:id/positions — list positions for a bot
  app.get<{
    Params: { id: string };
    Querystring: { limit?: string; status?: string };
  }>("/bots/:id/positions", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const bot = await prisma.bot.findUnique({ where: { id: request.params.id } });
    if (!bot || bot.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Bot not found");
    }

    const limit = Math.min(Number(request.query?.limit ?? 20), 100);
    const statusFilter = request.query?.status;

    const validStatuses = ["OPEN", "CLOSED"] as const;
    const status = statusFilter && validStatuses.includes(statusFilter as typeof validStatuses[number])
      ? (statusFilter as "OPEN" | "CLOSED")
      : undefined;

    const positions = await listBotPositions(bot.id, { status, limit });
    return reply.send(positions);
  });

  // GET /bots/:id/positions/:positionId/events — position event log
  app.get<{
    Params: { id: string; positionId: string };
    Querystring: { limit?: string };
  }>("/bots/:id/positions/:positionId/events", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const bot = await prisma.bot.findUnique({ where: { id: request.params.id } });
    if (!bot || bot.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Bot not found");
    }

    // Verify position belongs to this bot
    const position = await prisma.position.findUnique({
      where: { id: request.params.positionId },
    });
    if (!position || position.botId !== bot.id) {
      return problem(reply, 404, "Not Found", "Position not found");
    }

    const limit = Math.min(Number(request.query?.limit ?? 50), 200);
    const events = await getPositionEvents(request.params.positionId, { limit });

    // Serialize Decimal fields to numbers for JSON response
    const serialized = events.map((e) => ({
      id: e.id,
      positionId: e.positionId,
      type: e.type,
      qty: e.qty?.toNumber() ?? null,
      price: e.price?.toNumber() ?? null,
      realisedPnl: e.realisedPnl?.toNumber() ?? null,
      snapshotJson: e.snapshotJson,
      intentId: e.intentId,
      metaJson: e.metaJson,
      ts: e.ts,
    }));

    return reply.send(serialized);
  });
}
