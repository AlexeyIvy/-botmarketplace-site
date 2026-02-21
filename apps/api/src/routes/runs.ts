import type { FastifyInstance, FastifyRequest, FastifyReply } from "fastify";
import type { BotRunState } from "@prisma/client";
import { prisma } from "../lib/prisma.js";
import { problem } from "../lib/problem.js";
import { resolveWorkspace } from "../lib/workspace.js";
import {
  transition,
  isTerminalState,
  isValidTransition,
  InvalidTransitionError,
  RunNotFoundError,
} from "../lib/stateMachine.js";

// ---------------------------------------------------------------------------
// Worker-secret guard
// Applied to machine-to-machine endpoints that must NOT be callable by
// arbitrary users. The in-process botWorker bypasses HTTP entirely (calls
// Prisma directly), so this guard has zero runtime impact today; it protects
// the HTTP surface for any future external worker.
//
// Auth scheme: Authorization: Bearer <BOT_WORKER_SECRET>
// If BOT_WORKER_SECRET is not set (dev / CI), the check is skipped.
// In production always set BOT_WORKER_SECRET in the environment.
// ---------------------------------------------------------------------------
async function verifyWorkerSecret(request: FastifyRequest, reply: FastifyReply) {
  const secret = process.env.BOT_WORKER_SECRET;
  if (!secret) return; // permissive in dev; production must set the var
  const auth = request.headers.authorization;
  const token = auth?.startsWith("Bearer ") ? auth.slice(7) : undefined;
  if (!token || token !== secret) {
    return reply.status(401).send({
      type: "about:blank",
      title: "Unauthorized",
      status: 401,
      detail: "Valid worker secret required (Authorization: Bearer <BOT_WORKER_SECRET>)",
    });
  }
}

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

export async function runRoutes(app: FastifyInstance) {
  // ── POST /bots/:botId/runs ── start a new run ────────────────────────────
  app.post<{ Params: { botId: string } }>("/bots/:botId/runs", {
    config: { rateLimit: { max: 10, timeWindow: "1 minute" } },
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const bot = await prisma.bot.findUnique({ where: { id: request.params.botId } });
    if (!bot || bot.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Bot not found");
    }

    // Enforce single-active-run invariant
    const activeRun = await prisma.botRun.findFirst({
      where: {
        botId: bot.id,
        state: { notIn: ["STOPPED", "FAILED", "TIMED_OUT"] },
      },
    });
    if (activeRun) {
      return problem(reply, 409, "ActiveRunExists", "An active run already exists for this bot");
    }

    const run = await prisma.$transaction(async (tx) => {
      const created = await tx.botRun.create({
        data: {
          botId: bot.id,
          workspaceId: bot.workspaceId,
          symbol: bot.symbol,
          state: "CREATED",
        },
      });

      await tx.botEvent.create({
        data: {
          botRunId: created.id,
          type: "RUN_CREATED",
          payloadJson: {
            from: null,
            to: "CREATED",
            message: "Run created",
            at: new Date().toISOString(),
          },
        },
      });

      return created;
    });

    // Immediately transition to QUEUED via state machine
    await transition(run.id, "QUEUED", {
      eventType: "RUN_QUEUED",
      message: "Run queued for processing",
    });

    const fresh = await prisma.botRun.findUnique({ where: { id: run.id } });
    return reply.status(201).send(fresh);
  });

  // ── POST /bots/:botId/runs/:runId/stop ───────────────────────────────────
  app.post<{ Params: { botId: string; runId: string } }>(
    "/bots/:botId/runs/:runId/stop",
    { onRequest: [app.authenticate] },
    async (request, reply) => {
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

      if (isTerminalState(run.state)) {
        return problem(reply, 409, "Conflict", `Run is already in terminal state: ${run.state}`);
      }

      try {
        // STOPPING is intermediate; if state doesn't allow STOPPING, go straight to STOPPED
        let updated;
        if (isValidTransition(run.state, "STOPPING")) {
          await transition(run.id, "STOPPING", {
            eventType: "RUN_STOPPING",
            message: "Stop requested",
          });
          updated = await transition(run.id, "STOPPED", {
            eventType: "RUN_STOPPED",
            message: "Run stopped",
          });
        } else {
          updated = await transition(run.id, "STOPPED", {
            eventType: "RUN_STOPPED",
            message: "Run stopped",
          });
        }
        return reply.send(updated);
      } catch (err) {
        if (err instanceof InvalidTransitionError) {
          return problem(reply, 409, "InvalidTransition", err.message);
        }
        throw err;
      }
    },
  );

  // ── POST /runs/stop-all ── emergency stop all active runs in workspace ─────
  app.post("/runs/stop-all", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const activeRuns = await prisma.botRun.findMany({
      where: {
        workspaceId: workspace.id,
        state: { notIn: ["STOPPED", "FAILED", "TIMED_OUT", "CREATED"] },
      },
      select: { id: true, state: true },
    });

    const stopped: string[] = [];
    const errors: { id: string; error: string }[] = [];

    for (const run of activeRuns) {
      try {
        if (isValidTransition(run.state, "STOPPING")) {
          await transition(run.id, "STOPPING", {
            eventType: "RUN_STOPPING",
            message: "Stop All requested",
          });
        }
        await transition(run.id, "STOPPED", {
          eventType: "RUN_STOPPED",
          message: "Stopped by Stop All",
          stoppedAt: new Date(),
        });
        stopped.push(run.id);
      } catch (err) {
        errors.push({ id: run.id, error: String(err) });
      }
    }

    return reply.send({ stopped, errors, total: activeRuns.length });
  });

  // ── PATCH /runs/:runId/state ── worker-driven state advance ──────────────
  app.patch<{
    Params: { runId: string };
    Body: { state: BotRunState; message?: string; errorCode?: string };
  }>("/runs/:runId/state", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const run = await prisma.botRun.findUnique({ where: { id: request.params.runId } });
    if (!run || run.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Run not found");
    }

    const { state: toState, message, errorCode } = request.body ?? {};
    if (!toState) {
      return problem(reply, 400, "BadRequest", "Body must include 'state'");
    }

    try {
      const updated = await transition(run.id, toState, {
        message,
        errorCode,
        startedAt: toState === "RUNNING" ? new Date() : undefined,
      });
      return reply.send(updated);
    } catch (err) {
      if (err instanceof InvalidTransitionError) {
        return problem(reply, 409, "InvalidTransition", err.message);
      }
      if (err instanceof RunNotFoundError) {
        return problem(reply, 404, "Not Found", err.message);
      }
      throw err;
    }
  });

  // ── POST /runs/:runId/heartbeat ── lease renewal ──────────────────────────
  app.post<{ Params: { runId: string }; Body: { workerId: string } }>(
    "/runs/:runId/heartbeat",
    { onRequest: [app.authenticate] },
    async (request, reply) => {
      const workspace = await resolveWorkspace(request, reply);
      if (!workspace) return;

      const run = await prisma.botRun.findUnique({ where: { id: request.params.runId } });
      if (!run || run.workspaceId !== workspace.id) {
        return problem(reply, 404, "Not Found", "Run not found");
      }

      if (isTerminalState(run.state)) {
        return problem(reply, 409, "Conflict", `Run is in terminal state: ${run.state}`);
      }

      const workerId = request.body?.workerId ?? "unknown";
      const leaseUntil = new Date(Date.now() + 30_000); // 30s lease

      const updated = await prisma.botRun.update({
        where: { id: run.id },
        data: { leaseOwner: workerId, leaseUntil },
        select: { id: true, state: true, leaseOwner: true, leaseUntil: true, updatedAt: true },
      });

      return reply.send(updated);
    },
  );

  // ── GET /runs/:runId/events ── list events for a run ─────────────────────
  app.get<{ Params: { runId: string }; Querystring: { limit?: string; after?: string } }>(
    "/runs/:runId/events",
    { onRequest: [app.authenticate] },
    async (request, reply) => {
      const workspace = await resolveWorkspace(request, reply);
      if (!workspace) return;

      const run = await prisma.botRun.findUnique({ where: { id: request.params.runId } });
      if (!run || run.workspaceId !== workspace.id) {
        return problem(reply, 404, "Not Found", "Run not found");
      }

      const limit = Math.min(Number(request.query?.limit ?? 100), 500);
      const after = request.query?.after;

      const events = await prisma.botEvent.findMany({
        where: {
          botRunId: run.id,
          ...(after ? { ts: { gt: new Date(after) } } : {}),
        },
        orderBy: { ts: "asc" },
        take: limit,
        select: { id: true, ts: true, type: true, payloadJson: true },
      });

      return reply.send(events);
    },
  );

  // ── POST /runs/reconcile ── recover stale runs ────────────────────────────
  app.post("/runs/reconcile", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const now = new Date();
    const staleTimeout = 60_000; // 60s — if no heartbeat for 60s, consider stale

    // Find active runs with expired lease or no lease set for > 60s
    const staleRuns = await prisma.botRun.findMany({
      where: {
        workspaceId: workspace.id,
        state: { notIn: ["STOPPED", "FAILED", "TIMED_OUT", "CREATED", "QUEUED"] },
        OR: [
          { leaseUntil: { lt: now } },
          {
            leaseUntil: null,
            updatedAt: { lt: new Date(now.getTime() - staleTimeout) },
          },
        ],
      },
      select: { id: true, state: true, leaseOwner: true, leaseUntil: true },
    });

    const recovered: string[] = [];
    const errors: { id: string; error: string }[] = [];

    for (const stale of staleRuns) {
      try {
        await transition(stale.id, "FAILED", {
          eventType: "RUN_RECONCILED_FAILED",
          message: "Run marked FAILED by reconciliation (stale lease)",
          errorCode: "STALE_LEASE",
          meta: { leaseOwner: stale.leaseOwner, leaseUntil: stale.leaseUntil },
        });
        recovered.push(stale.id);
      } catch (err) {
        errors.push({ id: stale.id, error: String(err) });
      }
    }

    return reply.send({
      staleFound: staleRuns.length,
      markedFailed: recovered,
      errors,
      at: now.toISOString(),
    });
  });
}
