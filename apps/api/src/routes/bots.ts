import type { FastifyInstance } from "fastify";
import { prisma } from "../lib/prisma.js";
import { Prisma } from "@prisma/client";
import { problem } from "../lib/problem.js";
import { resolveWorkspace } from "../lib/workspace.js";
import { transition, isValidTransition, isTerminalState } from "../lib/stateMachine.js";
import {
  listBotPositions,
  getActiveBotPosition,
  getPositionEvents,
  calcUnrealisedPnl,
  type PositionSnapshot,
} from "../lib/positionManager.js";
import { recoverDcaState } from "../lib/runtime/dcaBridge.js";

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

    // Stage 4 (#132): include DCA ladder state if present
    let dcaLadder: Record<string, unknown> | null = null;
    if (activePosition) {
      try {
        const posRow = await prisma.position.findUnique({
          where: { id: activePosition.id },
          select: { metaJson: true },
        });
        const dcaState = recoverDcaState(posRow?.metaJson);
        if (dcaState) {
          dcaLadder = {
            phase: dcaState.phase,
            side: dcaState.side,
            baseEntryPrice: dcaState.baseEntryPrice,
            avgEntryPrice: dcaState.avgEntryPrice,
            tpPrice: dcaState.tpPrice,
            slPrice: dcaState.slPrice,
            safetyOrdersFilled: dcaState.safetyOrdersFilled,
            nextSoIndex: dcaState.nextSoIndex,
            totalCostUsd: dcaState.totalCostUsd,
            fillCount: dcaState.fills.length,
          };
        }
      } catch (_dcaErr) {
        // Non-fatal: DCA state not available
      }
    }

    return reply.send({
      ...rest,
      lastRun: runs[0] ?? null,
      activePosition: activePosition ?? null,
      dcaLadder,
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

  // ── POST /bots/:id/kill ── emergency kill switch (#141) ───────────────────
  //
  // Immediately stops all bot activity:
  //   1. Transitions all non-terminal runs to STOPPED
  //   2. Cancels all PENDING intents (prevent stale actions)
  //   3. Syncs Bot.status to DRAFT
  //
  // Idempotent: calling kill on an already-stopped bot is a safe no-op.
  // Does NOT cancel PLACED orders on the exchange — that requires exchange API
  // calls which are handled by the reconciliation loop or manual intervention.
  //
  app.post<{ Params: { id: string } }>(
    "/bots/:id/kill",
    { onRequest: [app.authenticate] },
    async (request, reply) => {
      const workspace = await resolveWorkspace(request, reply);
      if (!workspace) return;

      const bot = await prisma.bot.findUnique({ where: { id: request.params.id } });
      if (!bot || bot.workspaceId !== workspace.id) {
        return problem(reply, 404, "Not Found", "Bot not found");
      }

      // Find all non-terminal runs for this bot
      const activeRuns = await prisma.botRun.findMany({
        where: {
          botId: bot.id,
          state: { notIn: ["STOPPED", "FAILED", "TIMED_OUT"] },
        },
        select: { id: true, state: true },
      });

      const stoppedRuns: string[] = [];
      const runErrors: { id: string; error: string }[] = [];

      for (const run of activeRuns) {
        try {
          if (isValidTransition(run.state, "STOPPING")) {
            await transition(run.id, "STOPPING", {
              eventType: "RUN_STOPPING",
              message: "Kill switch activated",
            });
          }
          if (!isTerminalState(run.state === "STOPPING" ? "STOPPING" : run.state)) {
            await transition(run.id, "STOPPED", {
              eventType: "RUN_STOPPED",
              message: "Killed by kill switch",
              stoppedAt: new Date(),
            });
          }
          stoppedRuns.push(run.id);
        } catch (err) {
          runErrors.push({ id: run.id, error: String(err) });
        }
      }

      // Cancel all PENDING intents for this bot's runs
      const cancelResult = await prisma.botIntent.updateMany({
        where: {
          state: "PENDING",
          botRun: { botId: bot.id },
        },
        data: {
          state: "CANCELLED",
          metaJson: {
            reason: "kill_switch",
            cancelledAt: new Date().toISOString(),
          } as Prisma.InputJsonValue,
        },
      });

      // Sync bot status to DRAFT
      await prisma.bot.update({
        where: { id: bot.id },
        data: { status: "DRAFT" },
      });

      // Record kill event
      if (activeRuns.length > 0 || cancelResult.count > 0) {
        // Use the first active run for the event, or skip if none
        const eventRunId = activeRuns[0]?.id;
        if (eventRunId) {
          await prisma.botEvent.create({
            data: {
              botRunId: eventRunId,
              type: "kill_switch",
              payloadJson: {
                botId: bot.id,
                stoppedRuns: stoppedRuns.length,
                cancelledIntents: cancelResult.count,
                at: new Date().toISOString(),
              } as Prisma.InputJsonValue,
            },
          });
        }
      }

      return reply.send({
        killed: true,
        stoppedRuns,
        cancelledIntents: cancelResult.count,
        errors: runErrors,
      });
    },
  );
}
