/**
 * Intent Executor — extracted from botWorker.ts (#230)
 *
 * Processes a single BotIntent:
 * - Demo mode (no exchangeConnection): simulate immediately → FILLED
 * - Live mode (has exchangeConnection): call Bybit → PLACED (or FAILED on error)
 *
 * Uses optimistic locking: atomically claims PENDING → PLACED before acting.
 */

import { Prisma } from "@prisma/client";
import { prisma } from "../prisma.js";
import { decrypt, getEncryptionKeyRaw } from "../crypto.js";
import {
  bybitPlaceOrder,
  getBybitBaseUrl,
  isBybitLive,
} from "../bybitOrder.js";
import { getInstrument } from "../exchange/instrumentCache.js";
import { normalizeOrder } from "../exchange/normalizer.js";
import { classifyExecutionError } from "../errorClassifier.js";
import type { Logger } from "pino";

/** Max retries for transient intent failures before dead-lettering (Task #22). */
export const MAX_INTENT_RETRIES = parseInt(process.env.MAX_INTENT_RETRIES ?? "", 10) || 3;

// ---------------------------------------------------------------------------
// Intent shape
// ---------------------------------------------------------------------------

export interface IntentRecord {
  id: string;
  intentId: string;
  orderLinkId: string;
  side: string;
  qty: { toString: () => string };
  price: { toString: () => string } | null;
  retryCount: number;
  metaJson: Prisma.JsonValue;
  botRun: {
    id: string;
    bot: {
      id: string;
      symbol: string;
      exchangeConnectionId: string | null;
      exchangeConnection: { apiKey: string; encryptedSecret: string } | null;
      strategyVersion: { dslJson: Prisma.JsonValue } | null;
    };
  };
}

// ---------------------------------------------------------------------------
// Execute
// ---------------------------------------------------------------------------

export async function executeIntent(intent: IntentRecord, parentLog: Logger): Promise<void> {
  const { botRun } = intent;
  const { bot } = botRun;
  const intentLog = parentLog.child({ runId: botRun.id, intentId: intent.intentId, symbol: bot.symbol });

  // Atomically claim the intent (optimistic lock)
  const claimed = await prisma.botIntent.updateMany({
    where: { id: intent.id, state: "PENDING" },
    data: { state: "PLACED" },
  });
  if (claimed.count === 0) return; // another worker grabbed it or it changed

  try {
    if (!bot.exchangeConnection) {
      // ── Demo mode: simulate order placement ──────────────────────────────
      const meta = {
        ...(intent.metaJson && typeof intent.metaJson === "object" ? intent.metaJson as Record<string, unknown> : {}),
        simulated: true,
        filledAt: new Date().toISOString(),
      };
      await prisma.botIntent.update({
        where: { id: intent.id },
        data: { state: "FILLED", metaJson: meta as Prisma.InputJsonValue },
      });
      await prisma.botEvent.create({
        data: {
          botRunId: botRun.id,
          type: "intent_simulated",
          payloadJson: {
            intentId: intent.intentId,
            orderLinkId: intent.orderLinkId,
            side: intent.side,
            qty: intent.qty.toString(),
            simulated: true,
            at: new Date().toISOString(),
          } as Prisma.InputJsonValue,
        },
      });
      intentLog.info("intent simulated (demo mode)");
    } else {
      // ── Live mode: place order on Bybit ──────────────────────────────────
      const encKey = getEncryptionKeyRaw();
      const plainSecret = decrypt(bot.exchangeConnection.encryptedSecret, encKey);

      const dsl = bot.strategyVersion?.dslJson as { execution?: { orderType?: string } } | null;
      const orderType =
        (dsl?.execution?.orderType === "Limit" ? "Limit" : "Market") as "Market" | "Limit";

      const side = intent.side === "BUY" ? "Buy" : "Sell";

      let qtyStr = intent.qty.toString();
      let priceStr = intent.price && orderType === "Limit" ? intent.price.toString() : undefined;

      try {
        const instrument = await getInstrument(bot.symbol);
        const normalized = normalizeOrder(
          {
            symbol: bot.symbol,
            side,
            orderType,
            qty: Number(intent.qty.toString()),
            price: intent.price ? Number(intent.price.toString()) : undefined,
          },
          instrument,
        );

        if (!normalized.valid) {
          throw new Error(`Order normalization failed: ${normalized.reason}`);
        }

        qtyStr = normalized.order.qty;
        priceStr = normalized.order.price;

        intentLog.info(
          {
            diagnostics: normalized.order.diagnostics,
            env: isBybitLive() ? "live" : "demo",
            baseUrl: getBybitBaseUrl(),
          },
          "order normalized",
        );
      } catch (normErr) {
        intentLog.warn({ err: normErr }, "order normalization error");
        throw normErr;
      }

      const result = await bybitPlaceOrder(
        bot.exchangeConnection.apiKey,
        plainSecret,
        {
          symbol: bot.symbol,
          side,
          orderType,
          qty: qtyStr,
          ...(priceStr ? { price: priceStr } : {}),
        },
      );

      const meta = {
        ...(intent.metaJson && typeof intent.metaJson === "object" ? intent.metaJson as Record<string, unknown> : {}),
        exchangeOrderId: result.orderId,
        placedAt: new Date().toISOString(),
      };
      await prisma.botIntent.update({
        where: { id: intent.id },
        data: { orderId: result.orderId, metaJson: meta as Prisma.InputJsonValue },
      });
      await prisma.botEvent.create({
        data: {
          botRunId: botRun.id,
          type: "intent_placed",
          payloadJson: {
            intentId: intent.intentId,
            orderId: result.orderId,
            orderLinkId: result.orderLinkId,
            at: new Date().toISOString(),
          } as Prisma.InputJsonValue,
        },
      });
      intentLog.info({ orderId: result.orderId }, "intent placed");
    }
  } catch (err) {
    await handleIntentError(intent, botRun, err, intentLog);
  }
}

// ---------------------------------------------------------------------------
// Error handling with retry / dead-letter
// ---------------------------------------------------------------------------

async function handleIntentError(
  intent: IntentRecord,
  botRun: { id: string },
  err: unknown,
  intentLog: Logger,
): Promise<void> {
  const classification = classifyExecutionError(err);
  const currentRetry = intent.retryCount;
  const canRetry = classification.retryable && currentRetry < MAX_INTENT_RETRIES;

  if (canRetry) {
    const meta = {
      ...(intent.metaJson && typeof intent.metaJson === "object" ? intent.metaJson as Record<string, unknown> : {}),
      lastError: String(err),
      errorClass: classification.errorClass,
      retryAttempt: currentRetry + 1,
      retriedAt: new Date().toISOString(),
    };
    await prisma.botIntent.update({
      where: { id: intent.id },
      data: {
        state: "PENDING",
        retryCount: currentRetry + 1,
        metaJson: meta as Prisma.InputJsonValue,
      },
    });
    await prisma.botEvent.create({
      data: {
        botRunId: botRun.id,
        type: "intent_retry",
        payloadJson: {
          intentId: intent.intentId,
          error: String(err),
          errorClass: classification.errorClass,
          retryAttempt: currentRetry + 1,
          maxRetries: MAX_INTENT_RETRIES,
          at: new Date().toISOString(),
        } as Prisma.InputJsonValue,
      },
    });
    intentLog.warn(
      {
        errorClass: classification.errorClass,
        retryAttempt: currentRetry + 1,
        maxRetries: MAX_INTENT_RETRIES,
      },
      `executeIntent transient error — retry ${currentRetry + 1}/${MAX_INTENT_RETRIES}`,
    );
  } else {
    const deadLetterReason = classification.retryable
      ? `max retries exhausted (${currentRetry}/${MAX_INTENT_RETRIES})`
      : `permanent error: ${classification.reason}`;

    const meta = {
      ...(intent.metaJson && typeof intent.metaJson === "object" ? intent.metaJson as Record<string, unknown> : {}),
      error: String(err),
      errorClass: classification.errorClass,
      retryable: classification.retryable,
      classificationReason: classification.reason,
      retryCount: currentRetry,
      deadLetterReason,
      failedAt: new Date().toISOString(),
    };
    await prisma.botIntent.update({
      where: { id: intent.id },
      data: { state: "FAILED", metaJson: meta as Prisma.InputJsonValue },
    });
    await prisma.botEvent.create({
      data: {
        botRunId: botRun.id,
        type: classification.retryable ? "intent_dead_lettered" : "intent_failed",
        payloadJson: {
          intentId: intent.intentId,
          error: String(err),
          errorClass: classification.errorClass,
          retryable: classification.retryable,
          retryCount: currentRetry,
          deadLetterReason,
          at: new Date().toISOString(),
        } as Prisma.InputJsonValue,
      },
    });
    intentLog.error(
      {
        err,
        errorClass: classification.errorClass,
        retryable: classification.retryable,
        retryCount: currentRetry,
        deadLetterReason,
      },
      `executeIntent ${classification.retryable ? "dead-lettered" : "permanent failure"}`,
    );
  }
}
