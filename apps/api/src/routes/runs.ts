import type { FastifyInstance } from "fastify";
import { Prisma } from "@prisma/client";
import { prisma } from "../lib/prisma.js";
import { problem } from "../lib/problem.js";
import { resolveWorkspace } from "../lib/workspace.js";

// ---------------------------------------------------------------------------
// Active states — must match the partial unique index in migration SQL
// ---------------------------------------------------------------------------

const ACTIVE_STATES = ["CREATED", "QUEUED", "STARTING", "SYNCING", "RUNNING"] as const;
const TERMINAL_STATES = ["STOPPED", "FAILED", "TIMED_OUT"] as const;

function isTerminal(state: string): boolean {
  return (TERMINAL_STATES as readonly string[]).includes(state);
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function eventPayload(message: string, state: string) {
  return { message, state, at: new Date().toISOString() };
}

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

export async function runRoutes(app: FastifyInstance) {
  // POST /bots/:botId/runs — start a new run
  app.post<{ Params: { botId: string } }>("/bots/:botId/runs", async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const bot = await prisma.bot.findUnique({ where: { id: request.params.botId } });
    if (!bot || bot.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Bot not found");
    }

    try {
      const run = await prisma.$transaction(async (tx) => {
        const created = await tx.botRun.create({
          data: {
            botId: bot.id,
            workspaceId: bot.workspaceId,
            symbol: bot.symbol,
            state: "QUEUED",
          },
        });

        await tx.botEvent.createMany({
          data: [
            {
              botRunId: created.id,
              type: "RUN_CREATED",
              payloadJson: eventPayload("Run created", "CREATED"),
            },
            {
              botRunId: created.id,
              type: "RUN_QUEUED",
              payloadJson: eventPayload("Run queued", "QUEUED"),
            },
          ],
        });

        return created;
      });

      return reply.status(201).send(run);
    } catch (err) {
      // Partial unique index violation → active run already exists
      if (err instanceof Prisma.PrismaClientKnownRequestError && err.code === "P2002") {
        return problem(reply, 409, "ActiveRunExists", "An active run already exists for this bot's symbol in this workspace");
      }
      throw err;
    }
  });

  // POST /bots/:botId/runs/:runId/stop — stop a run
  app.post<{ Params: { botId: string; runId: string } }>("/bots/:botId/runs/:runId/stop", async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const bot = await prisma.bot.findUnique({ where: { id: request.params.botId } });
    if (!bot || bot.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Bot not found");
    }

    const run = await prisma.botRun.findUnique({ where: { id: request.params.runId } });
    if (!run || run.botId !== bot.id) {
      return problem(reply, 404, "Not Found", "Run not found");
    }

    if (isTerminal(run.state)) {
      return problem(reply, 409, "Conflict", `Run is already in terminal state: ${run.state}`);
    }

    const now = new Date();

    const stopped = await prisma.$transaction(async (tx) => {
      const updated = await tx.botRun.update({
        where: { id: run.id },
        data: { state: "STOPPED", stoppedAt: now },
      });

      await tx.botEvent.createMany({
        data: [
          {
            botRunId: run.id,
            type: "RUN_STOPPING",
            payloadJson: eventPayload("Stopping run", "STOPPING"),
          },
          {
            botRunId: run.id,
            type: "RUN_STOPPED",
            payloadJson: eventPayload("Run stopped", "STOPPED"),
          },
        ],
      });

      return updated;
    });

    return reply.send(stopped);
  });

  // GET /runs/:runId/events — list events for a run
  app.get<{ Params: { runId: string } }>("/runs/:runId/events", async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const run = await prisma.botRun.findUnique({ where: { id: request.params.runId } });
    if (!run || run.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Run not found");
    }

    const events = await prisma.botEvent.findMany({
      where: { botRunId: run.id },
      orderBy: { ts: "asc" },
      select: { id: true, ts: true, type: true, payloadJson: true },
    });
    return reply.send(events);
  });
}
