/**
 * Bot Intent routes — idempotency layer for exchange orders.
 *
 * Intents represent "our intent to place an order". Each intent carries:
 *  - intentId   : client-provided idempotency key (unique per run)
 *  - orderLinkId: server-generated exchange clientOrderId (globally unique)
 *
 * The API is deliberately simple; the actual order placement is done by
 * the bot runtime worker, which uses orderLinkId when calling the exchange.
 */

import { randomUUID } from "node:crypto";
import type { FastifyInstance } from "fastify";
import type { IntentState, IntentType, OrderSide } from "@prisma/client";
import { prisma } from "../lib/prisma.js";
import { problem } from "../lib/problem.js";
import { resolveWorkspace } from "../lib/workspace.js";

// ---------------------------------------------------------------------------
// Route plugin
// ---------------------------------------------------------------------------

export async function intentRoutes(app: FastifyInstance) {
  // ── POST /runs/:runId/intents ── create intent (idempotent) ──────────────
  app.post<{
    Params: { runId: string };
    Body: {
      intentId: string;
      type: IntentType;
      side: OrderSide;
      qty: number;
      price?: number;
      metaJson?: Record<string, unknown>;
    };
  }>("/runs/:runId/intents", async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const run = await prisma.botRun.findUnique({ where: { id: request.params.runId } });
    if (!run || run.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Run not found");
    }

    const { intentId, type, side, qty, price, metaJson } = request.body ?? {};

    if (!intentId) return problem(reply, 400, "BadRequest", "'intentId' is required");
    if (!type)     return problem(reply, 400, "BadRequest", "'type' is required");
    if (!side)     return problem(reply, 400, "BadRequest", "'side' is required");
    if (qty == null || qty <= 0) return problem(reply, 400, "BadRequest", "'qty' must be a positive number");

    // Idempotency: if an intent with this intentId already exists for this run, return it
    const existing = await prisma.botIntent.findUnique({
      where: { botRunId_intentId: { botRunId: run.id, intentId } },
    });
    if (existing) {
      return reply.status(200).send(existing);
    }

    try {
      const intent = await prisma.botIntent.create({
        data: {
          botRunId:    run.id,
          intentId,
          orderLinkId: randomUUID(), // globally unique; sent to exchange as clientOrderId
          type,
          side,
          qty:         qty,
          price:       price ?? null,
          metaJson:    metaJson ?? null,
          state:       "PENDING",
        },
      });

      return reply.status(201).send(intent);
    } catch (err) {
      // P2002 = unique constraint violation → race on intentId creation
      if ((err as { code?: string })?.code === "P2002") {
        // Race: concurrent request created the same intentId; re-fetch and return
        const raced = await prisma.botIntent.findUnique({
          where: { botRunId_intentId: { botRunId: run.id, intentId } },
        });
        return reply.status(200).send(raced);
      }
      throw err;
    }
  });

  // ── GET /runs/:runId/intents ── list intents for a run ───────────────────
  app.get<{
    Params: { runId: string };
    Querystring: { state?: IntentState };
  }>("/runs/:runId/intents", async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const run = await prisma.botRun.findUnique({ where: { id: request.params.runId } });
    if (!run || run.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Run not found");
    }

    const intents = await prisma.botIntent.findMany({
      where: {
        botRunId: run.id,
        ...(request.query?.state ? { state: request.query.state } : {}),
      },
      orderBy: { createdAt: "asc" },
    });

    return reply.send(intents);
  });

  // ── PATCH /runs/:runId/intents/:intentId/state ── advance intent state ───
  app.patch<{
    Params: { runId: string; intentId: string };
    Body: { state: IntentState; orderId?: string; metaJson?: Record<string, unknown> };
  }>("/runs/:runId/intents/:intentId/state", async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const run = await prisma.botRun.findUnique({ where: { id: request.params.runId } });
    if (!run || run.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Run not found");
    }

    const intent = await prisma.botIntent.findUnique({
      where: { botRunId_intentId: { botRunId: run.id, intentId: request.params.intentId } },
    });
    if (!intent) {
      return problem(reply, 404, "Not Found", "Intent not found");
    }

    const { state: newState, orderId, metaJson } = request.body ?? {};
    if (!newState) return problem(reply, 400, "BadRequest", "'state' is required");

    // Terminal intents cannot be updated
    if (intent.state === "FILLED" || intent.state === "CANCELLED" || intent.state === "FAILED") {
      return problem(reply, 409, "Conflict", `Intent is already in terminal state: ${intent.state}`);
    }

    const updated = await prisma.botIntent.update({
      where: { id: intent.id },
      data: {
        state:   newState,
        orderId: orderId ?? intent.orderId,
        metaJson: metaJson != null
          ? { ...(intent.metaJson as Record<string, unknown> ?? {}), ...metaJson }
          : intent.metaJson,
      },
    });

    return reply.send(updated);
  });
}
