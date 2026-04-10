/**
 * Notification Settings API routes (Roadmap V3, Tier 4, #26)
 *
 * GET  /user/notifications       — get notification config
 * PUT  /user/notifications       — save notification config
 * POST /user/notifications/test  — send a test notification
 */

import type { FastifyInstance } from "fastify";
import { prisma } from "../lib/prisma.js";
import { problem } from "../lib/problem.js";
import { parseNotifyConfig, sendTelegramMessage, invalidateNotifyCache } from "../lib/notify.js";

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

function validateNotifyJson(val: unknown): string | null {
  if (typeof val !== "object" || val === null || Array.isArray(val)) {
    return "notifyJson must be an object";
  }
  const obj = val as Record<string, unknown>;

  if (obj.telegram !== undefined) {
    if (typeof obj.telegram !== "object" || obj.telegram === null || Array.isArray(obj.telegram)) {
      return "notifyJson.telegram must be an object";
    }
    const tg = obj.telegram as Record<string, unknown>;

    if (typeof tg.botToken !== "string") {
      return "notifyJson.telegram.botToken must be a string";
    }
    if (tg.botToken.length > 200) {
      return "notifyJson.telegram.botToken is too long";
    }
    if (typeof tg.chatId !== "string") {
      return "notifyJson.telegram.chatId must be a string";
    }
    if (tg.chatId.length > 50) {
      return "notifyJson.telegram.chatId is too long";
    }
    if (!/^-?\d+$/.test(tg.chatId as string) && !/^@[a-zA-Z0-9_]+$/.test(tg.chatId as string)) {
      return "notifyJson.telegram.chatId must be a numeric ID or @username";
    }
    if (tg.enabled !== undefined && typeof tg.enabled !== "boolean") {
      return "notifyJson.telegram.enabled must be a boolean";
    }
  }

  return null;
}

// ---------------------------------------------------------------------------
// Route plugin
// ---------------------------------------------------------------------------

export async function notificationRoutes(app: FastifyInstance) {
  // ── GET /user/notifications ─────────────────────────────────────────────
  app.get("/user/notifications", { onRequest: [app.authenticate] }, async (request, reply) => {
    const payload = request.user as { sub: string };

    const row = await prisma.userPreference.findUnique({
      where: { userId: payload.sub },
    });

    if (!row?.notifyJson) {
      return reply.send({ notifyJson: null });
    }

    // Redact botToken for security (only show last 4 chars)
    const config = row.notifyJson as Record<string, unknown>;
    const tg = config.telegram as Record<string, unknown> | undefined;
    if (tg?.botToken && typeof tg.botToken === "string") {
      tg.botToken = "****" + tg.botToken.slice(-4);
    }

    return reply.send({ notifyJson: config });
  });

  // ── PUT /user/notifications ─────────────────────────────────────────────
  app.put<{ Body: { notifyJson: unknown } }>(
    "/user/notifications",
    { onRequest: [app.authenticate] },
    async (request, reply) => {
      const payload = request.user as { sub: string };
      const body = request.body as Record<string, unknown> | undefined;

      if (!body || typeof body !== "object" || !("notifyJson" in body)) {
        return problem(reply, 400, "Bad Request", "Request body must contain notifyJson");
      }

      const err = validateNotifyJson(body.notifyJson);
      if (err) {
        return problem(reply, 400, "Bad Request", err);
      }

      const row = await prisma.userPreference.upsert({
        where: { userId: payload.sub },
        create: {
          userId: payload.sub,
          terminalJson: { version: 1, terminal: {} },
          notifyJson: body.notifyJson as object,
        },
        update: {
          notifyJson: body.notifyJson as object,
        },
      });

      // Invalidate notification cache so changes take effect immediately
      invalidateNotifyCache(payload.sub);

      // Redact botToken in response
      const config = row.notifyJson as Record<string, unknown> | null;
      const tg = config?.telegram as Record<string, unknown> | undefined;
      if (tg?.botToken && typeof tg.botToken === "string") {
        tg.botToken = "****" + tg.botToken.slice(-4);
      }

      return reply.send({ notifyJson: config });
    },
  );

  // ── POST /user/notifications/test ───────────────────────────────────────
  app.post(
    "/user/notifications/test",
    { onRequest: [app.authenticate] },
    async (request, reply) => {
      const payload = request.user as { sub: string };

      const row = await prisma.userPreference.findUnique({
        where: { userId: payload.sub },
      });

      const config = parseNotifyConfig(row?.notifyJson);
      if (!config?.telegram) {
        return problem(reply, 400, "Bad Request", "No Telegram configuration found. Save settings first.");
      }

      const sent = await sendTelegramMessage(
        config.telegram,
        "✅ <b>Test Notification</b>\n\nBotMarketplace notifications are working!",
      );

      if (sent) {
        return reply.send({ success: true, message: "Test message sent" });
      } else {
        return problem(reply, 502, "Bad Gateway", "Failed to send test message. Check your bot token and chat ID.");
      }
    },
  );
}
