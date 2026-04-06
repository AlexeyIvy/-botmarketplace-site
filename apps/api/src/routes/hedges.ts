/**
 * Hedge Execution API routes (Roadmap V3, Tier 4, #25)
 *
 * POST /hedges/entry          — create HedgePosition (PLANNED)
 * POST /hedges/:id/execute    — place entry legs (spot buy + perp short) → OPENING
 * POST /hedges/:id/exit       — place exit legs (spot sell + perp close) → CLOSING
 * GET  /hedges?botRunId=...   — list positions for a run
 * GET  /hedges/:id            — position details + legs + computed P&L
 */

import { randomUUID } from "node:crypto";
import type { FastifyInstance } from "fastify";
import { prisma } from "../lib/prisma.js";
import { problem } from "../lib/problem.js";
import { resolveWorkspace } from "../lib/workspace.js";
import { computeHedgePnl } from "../lib/funding/hedgePlanner.js";
import type { HedgePosition as HedgePlannerPos, LegExecution } from "../lib/funding/hedgeTypes.js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Map DB HedgePosition + legs → hedgePlanner HedgePosition for P&L calc */
function toHedgePlannerPos(
  dbPos: {
    symbol: string;
    status: string;
    entryBasisBps: number;
    fundingCollected: number;
    createdAt: Date;
    closedAt: Date | null;
    legs: Array<{
      side: string;
      price: number;
      quantity: number;
      fee: number;
      timestamp: Date;
    }>;
  },
): HedgePlannerPos {
  function findLeg(side: string): LegExecution | null {
    const leg = dbPos.legs.find((l) => l.side === side);
    if (!leg) return null;
    return {
      side: leg.side as LegExecution["side"],
      price: leg.price,
      quantity: leg.quantity,
      fee: leg.fee,
      timestamp: leg.timestamp.getTime(),
    };
  }

  return {
    symbol: dbPos.symbol,
    status: dbPos.status as HedgePlannerPos["status"],
    entryBasisBps: dbPos.entryBasisBps,
    spotLeg: findLeg("SPOT_BUY"),
    perpLeg: findLeg("PERP_SHORT"),
    spotCloseLeg: findLeg("SPOT_SELL"),
    perpCloseLeg: findLeg("PERP_CLOSE"),
    fundingCollected: dbPos.fundingCollected,
    openedAt: dbPos.createdAt.getTime(),
    closedAt: dbPos.closedAt?.getTime() ?? 0,
  };
}

// ---------------------------------------------------------------------------
// Route plugin
// ---------------------------------------------------------------------------

export async function hedgeRoutes(app: FastifyInstance) {
  // ── POST /hedges/entry ── create HedgePosition (PLANNED) ────────────────
  app.post<{
    Body: {
      symbol: string;
      botRunId: string;
      positionSizeUsd?: number;
      entryBasisBps?: number;
      config?: Record<string, unknown>;
    };
  }>("/hedges/entry", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const { symbol, botRunId, positionSizeUsd, entryBasisBps, config } = request.body ?? {};

    if (!symbol) return problem(reply, 400, "Bad Request", "'symbol' is required");
    if (!botRunId) return problem(reply, 400, "Bad Request", "'botRunId' is required");

    // Verify run belongs to workspace
    const run = await prisma.botRun.findUnique({ where: { id: botRunId } });
    if (!run || run.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Run not found");
    }

    const hedge = await prisma.hedgePosition.create({
      data: {
        botRunId,
        symbol: symbol.toUpperCase(),
        status: "PLANNED",
        entryBasisBps: entryBasisBps ?? 0,
        fundingCollected: 0,
      },
    });

    return reply.status(201).send(hedge);
  });

  // ── POST /hedges/:id/execute ── place entry legs → OPENING ──────────────
  app.post<{
    Params: { id: string };
    Body: {
      spotPrice?: number;
      perpPrice?: number;
      quantity?: number;
    };
  }>("/hedges/:id/execute", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const hedge = await prisma.hedgePosition.findUnique({
      where: { id: request.params.id },
      include: { legs: true },
    });

    if (!hedge) return problem(reply, 404, "Not Found", "Hedge position not found");

    // Verify ownership via botRun → workspace
    const run = await prisma.botRun.findUnique({ where: { id: hedge.botRunId } });
    if (!run || run.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Hedge position not found");
    }

    if (hedge.status !== "PLANNED") {
      return problem(reply, 409, "Conflict", `Cannot execute hedge in status: ${hedge.status}`);
    }

    // Create two BotIntents — spot buy + perp short
    const spotIntentId = `hedge-${hedge.id}-spot-entry`;
    const perpIntentId = `hedge-${hedge.id}-perp-entry`;

    const [spotIntent, perpIntent] = await prisma.$transaction([
      prisma.botIntent.create({
        data: {
          botRunId: hedge.botRunId,
          intentId: spotIntentId,
          orderLinkId: randomUUID(),
          type: "ENTRY",
          state: "PENDING",
          side: "BUY",
          qty: request.body?.quantity ?? 0,
          metaJson: { hedgeId: hedge.id, legSide: "SPOT_BUY", category: "spot" },
        },
      }),
      prisma.botIntent.create({
        data: {
          botRunId: hedge.botRunId,
          intentId: perpIntentId,
          orderLinkId: randomUUID(),
          type: "ENTRY",
          state: "PENDING",
          side: "SELL",
          qty: request.body?.quantity ?? 0,
          metaJson: { hedgeId: hedge.id, legSide: "PERP_SHORT", category: "linear" },
        },
      }),
      prisma.hedgePosition.update({
        where: { id: hedge.id },
        data: { status: "OPENING" },
      }),
    ]);

    return reply.send({
      hedgeId: hedge.id,
      status: "OPENING",
      intents: { spot: spotIntent, perp: perpIntent },
    });
  });

  // ── POST /hedges/:id/exit ── place exit legs → CLOSING ──────────────────
  app.post<{
    Params: { id: string };
    Body: {
      quantity?: number;
    };
  }>("/hedges/:id/exit", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const hedge = await prisma.hedgePosition.findUnique({
      where: { id: request.params.id },
      include: { legs: true },
    });

    if (!hedge) return problem(reply, 404, "Not Found", "Hedge position not found");

    const run = await prisma.botRun.findUnique({ where: { id: hedge.botRunId } });
    if (!run || run.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Hedge position not found");
    }

    if (hedge.status !== "OPEN") {
      return problem(reply, 409, "Conflict", `Cannot exit hedge in status: ${hedge.status}`);
    }

    // Determine quantity from entry legs
    const spotLeg = hedge.legs.find((l) => l.side === "SPOT_BUY");
    const exitQty = request.body?.quantity ?? spotLeg?.quantity ?? 0;

    const spotExitIntentId = `hedge-${hedge.id}-spot-exit`;
    const perpExitIntentId = `hedge-${hedge.id}-perp-exit`;

    const [spotIntent, perpIntent] = await prisma.$transaction([
      prisma.botIntent.create({
        data: {
          botRunId: hedge.botRunId,
          intentId: spotExitIntentId,
          orderLinkId: randomUUID(),
          type: "EXIT",
          state: "PENDING",
          side: "SELL",
          qty: exitQty,
          metaJson: { hedgeId: hedge.id, legSide: "SPOT_SELL", category: "spot" },
        },
      }),
      prisma.botIntent.create({
        data: {
          botRunId: hedge.botRunId,
          intentId: perpExitIntentId,
          orderLinkId: randomUUID(),
          type: "EXIT",
          state: "PENDING",
          side: "BUY",
          qty: exitQty,
          metaJson: { hedgeId: hedge.id, legSide: "PERP_CLOSE", category: "linear" },
        },
      }),
      prisma.hedgePosition.update({
        where: { id: hedge.id },
        data: { status: "CLOSING" },
      }),
    ]);

    return reply.send({
      hedgeId: hedge.id,
      status: "CLOSING",
      intents: { spot: spotIntent, perp: perpIntent },
    });
  });

  // ── GET /hedges?botRunId=... ── list positions for a run ────────────────
  app.get<{
    Querystring: { botRunId?: string; status?: string };
  }>("/hedges", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const { botRunId, status } = request.query;

    if (!botRunId) {
      return problem(reply, 400, "Bad Request", "'botRunId' query parameter is required");
    }

    // Verify run belongs to workspace
    const run = await prisma.botRun.findUnique({ where: { id: botRunId } });
    if (!run || run.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Run not found");
    }

    const where: Record<string, unknown> = { botRunId };
    if (status) where.status = status;

    const hedges = await prisma.hedgePosition.findMany({
      where,
      include: { legs: true },
      orderBy: { createdAt: "desc" },
    });

    const result = hedges.map((h) => {
      const plannerPos = toHedgePlannerPos(h);
      return {
        ...h,
        pnl: h.status === "CLOSED" ? computeHedgePnl(plannerPos) : null,
      };
    });

    return reply.send(result);
  });

  // ── GET /hedges/:id ── position details + legs + P&L ────────────────────
  app.get<{
    Params: { id: string };
  }>("/hedges/:id", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const hedge = await prisma.hedgePosition.findUnique({
      where: { id: request.params.id },
      include: { legs: true },
    });

    if (!hedge) return problem(reply, 404, "Not Found", "Hedge position not found");

    const run = await prisma.botRun.findUnique({ where: { id: hedge.botRunId } });
    if (!run || run.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Hedge position not found");
    }

    const plannerPos = toHedgePlannerPos(hedge);
    const pnl = (hedge.status === "CLOSED" || hedge.status === "OPEN")
      ? computeHedgePnl(plannerPos)
      : null;

    return reply.send({ ...hedge, pnl });
  });
}
