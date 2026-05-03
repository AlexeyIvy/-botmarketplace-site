/**
 * Hedge Execution API routes (Roadmap V3, Tier 4, #25)
 *
 * POST /hedges/entry          — create HedgePosition (PLANNED)
 * POST /hedges/:id/execute    — place entry legs (spot buy + perp short) → OPENING
 * POST /hedges/:id/exit       — place exit legs (spot sell + perp close) → CLOSING
 * GET  /hedges?botRunId=...   — list positions for a run
 * GET  /hedges/:id            — position details + legs + computed P&L
 */

import type { FastifyInstance, FastifyReply } from "fastify";
import { prisma } from "../lib/prisma.js";
import { problem } from "../lib/problem.js";
import { resolveWorkspace } from "../lib/workspace.js";
import { computeHedgePnl } from "../lib/funding/hedgePlanner.js";
import type { HedgePosition as HedgePlannerPos, LegExecution } from "../lib/funding/hedgeTypes.js";
import { decryptWithFallback } from "../lib/crypto.js";
import {
  executeHedgeEntry,
  executeHedgeExit,
  type HedgeExecutionResult,
  type LegCreds,
} from "../lib/exchange/hedgeExecutor.js";

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

/** Pull the BotRun with the credentials needed to execute hedge legs. The
 *  shape returned is consumed by both `resolveLegCreds` (decrypt) and the
 *  ownership check (workspaceId match). */
async function loadRunWithCreds(botRunId: string) {
  return prisma.botRun.findUnique({
    where: { id: botRunId },
    select: {
      id: true,
      workspaceId: true,
      bot: {
        select: {
          exchangeConnection: {
            select: {
              apiKey: true,
              encryptedSecret: true,
              spotApiKey: true,
              spotEncryptedSecret: true,
            },
          },
        },
      },
    },
  });
}

type RunWithCreds = NonNullable<Awaited<ReturnType<typeof loadRunWithCreds>>>;

/** Build per-leg credentials. Spot uses dedicated `spotApiKey/spotEncryptedSecret`
 *  when present, falling back to the linear key — the single-key fallback
 *  documented in docs/55-T5 §4. Returns null when no ExchangeConnection is
 *  linked at all (caller responds 422). Secrets are decrypted here so the
 *  hedgeExecutor receives plaintext and never touches crypto. */
function resolveLegCreds(run: RunWithCreds): { spotCreds: LegCreds; perpCreds: LegCreds } | null {
  const conn = run.bot?.exchangeConnection;
  if (!conn) return null;

  const perpSecret = decryptWithFallback(conn.encryptedSecret);
  const spotSecret = conn.spotEncryptedSecret
    ? decryptWithFallback(conn.spotEncryptedSecret)
    : perpSecret;
  return {
    perpCreds: { apiKey: conn.apiKey, secret: perpSecret },
    spotCreds: { apiKey: conn.spotApiKey ?? conn.apiKey, secret: spotSecret },
  };
}

/** Persist execution result + advance HedgePosition status, then send the
 *  HTTP response. Single-transaction write of LegExecution rows + status
 *  bump so an interrupted process can't leave a hedge with legs but stale
 *  status, or vice versa. */
async function persistAndRespond(
  reply: FastifyReply,
  hedgeId: string,
  exec: HedgeExecutionResult,
  type: "ENTRY" | "EXIT",
) {
  const isEntry = type === "ENTRY";

  // Status mapping — outcome × type:
  //   FILLED entry → OPEN
  //   FILLED exit  → CLOSED (with closedAt)
  //   FAILED any   → FAILED
  //   PARTIAL_ERROR any → FAILED (operator alert lives in the response body
  //                        + structured logs from hedgeExecutor)
  let nextStatus: "OPEN" | "CLOSED" | "FAILED";
  if (exec.outcome === "FILLED") {
    nextStatus = isEntry ? "OPEN" : "CLOSED";
  } else {
    nextStatus = "FAILED";
  }

  const updateData: { status: typeof nextStatus; closedAt?: Date } = { status: nextStatus };
  if (nextStatus === "CLOSED") updateData.closedAt = new Date();

  await prisma.$transaction([
    ...exec.legs.map((leg) =>
      prisma.legExecution.create({
        data: {
          hedgeId,
          side: leg.side,
          price: leg.price,
          quantity: leg.quantity,
          fee: leg.fee,
        },
      }),
    ),
    prisma.hedgePosition.update({
      where: { id: hedgeId },
      data: updateData,
    }),
  ]);

  const httpStatus = exec.outcome === "FILLED" ? 200 : 422;
  return reply.status(httpStatus).send({
    hedgeId,
    status: nextStatus,
    outcome: exec.outcome,
    legs: exec.legs,
    ...(exec.reason ? { reason: exec.reason } : {}),
    ...(exec.compensatingUnwindAttempted !== undefined
      ? {
          compensatingUnwind: {
            attempted: exec.compensatingUnwindAttempted,
            succeeded: exec.compensatingUnwindSucceeded ?? false,
          },
        }
      : {}),
  });
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

  // ── POST /hedges/:id/execute ── sync sequential entry → OPEN | FAILED ───
  app.post<{
    Params: { id: string };
    Body: {
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

    const run = await loadRunWithCreds(hedge.botRunId);
    if (!run || run.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Hedge position not found");
    }

    // Idempotency: only PLANNED hedges may be executed. Any other status
    // (OPENING, OPEN, CLOSING, CLOSED, FAILED) returns 409 — covers both
    // a repeated execute after success (status=OPEN) and a repeated execute
    // after a partial-error path (status=FAILED).
    if (hedge.status !== "PLANNED") {
      return problem(reply, 409, "Conflict", `Cannot execute hedge in status: ${hedge.status}`);
    }

    const qty = request.body?.quantity;
    if (typeof qty !== "number" || qty <= 0) {
      return problem(reply, 400, "Bad Request", "'quantity' must be a positive number");
    }

    const creds = resolveLegCreds(run);
    if (!creds) {
      return problem(reply, 422, "Unprocessable Content", "Bot has no linked ExchangeConnection");
    }

    const exec = await executeHedgeEntry({
      ...creds,
      symbol: hedge.symbol,
      qty: qty.toString(),
      hedgeId: hedge.id,
    });

    return persistAndRespond(reply, hedge.id, exec, "ENTRY");
  });

  // ── POST /hedges/:id/exit ── sync sequential exit → CLOSED | FAILED ─────
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

    const run = await loadRunWithCreds(hedge.botRunId);
    if (!run || run.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Hedge position not found");
    }

    if (hedge.status !== "OPEN") {
      return problem(reply, 409, "Conflict", `Cannot exit hedge in status: ${hedge.status}`);
    }

    // Quantity defaults to the SPOT_BUY leg quantity from entry — exit
    // matches entry size unless caller explicitly overrides.
    const spotEntryLeg = hedge.legs.find((l) => l.side === "SPOT_BUY");
    const exitQty = request.body?.quantity ?? spotEntryLeg?.quantity ?? 0;
    if (exitQty <= 0) {
      return problem(reply, 400, "Bad Request", "Cannot determine exit quantity — no filled entry legs");
    }

    const creds = resolveLegCreds(run);
    if (!creds) {
      return problem(reply, 422, "Unprocessable Content", "Bot has no linked ExchangeConnection");
    }

    const exec = await executeHedgeExit({
      ...creds,
      symbol: hedge.symbol,
      qty: exitQty.toString(),
      hedgeId: hedge.id,
    });

    return persistAndRespond(reply, hedge.id, exec, "EXIT");
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
