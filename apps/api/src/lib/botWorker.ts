/**
 * Bot Worker — background loop that advances bot run states and executes intents.
 *
 * Lifecycle:
 *   QUEUED → STARTING → SYNCING → RUNNING  (worker drives this)
 *   STOPPING → STOPPED                      (worker completes stop)
 *
 * Intent execution (Stage 11):
 *   PENDING → PLACED (on Bybit call or demo-sim) → FAILED (on error)
 *
 * Bot.status sync (Stage 11):
 *   Bot.status = ACTIVE when any run is not in terminal state
 *   Bot.status = DRAFT  when all runs are terminal
 *
 * DSL enforcement (Stage 12):
 *   enabled: false         → PENDING intents are CANCELLED immediately
 *   risk.dailyLossLimitUsd → RUNNING run transitions to STOPPING when estimated
 *                            daily loss (FAILED intents × loss-per-trade) exceeds limit
 *
 * The worker runs in the same process. For production, extract into a
 * dedicated worker process.
 */

import pino from "pino";
import { Prisma } from "@prisma/client";
import { prisma } from "./prisma.js";
import { transition, isValidTransition } from "./stateMachine.js";
import { bybitPlaceOrder } from "./bybitOrder.js";
import { decrypt, getEncryptionKeyRaw } from "./crypto.js";

const workerLog = pino({
  name: "botWorker",
  transport:
    process.env.NODE_ENV !== "production"
      ? { target: "pino-pretty" }
      : undefined,
});

const WORKER_ID = `worker-${process.pid}`;
const POLL_INTERVAL_MS = 4_000;

// Max time a run can stay in RUNNING state before auto-timeout (default: 4 hours)
const MAX_RUN_DURATION_MS = parseInt(process.env.MAX_RUN_DURATION_MS ?? "", 10) || 4 * 60 * 60 * 1000;

async function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ---------------------------------------------------------------------------
// Bot.status sync
// ---------------------------------------------------------------------------

/**
 * Sync Bot.status based on whether any active runs exist.
 * ACTIVE = at least one non-terminal run; DRAFT = all runs terminated.
 */
async function syncBotStatus(botId: string): Promise<void> {
  try {
    const activeCount = await prisma.botRun.count({
      where: {
        botId,
        state: { notIn: ["STOPPED", "FAILED", "TIMED_OUT"] },
      },
    });
    await prisma.bot.update({
      where: { id: botId },
      data: { status: activeCount > 0 ? "ACTIVE" : "DRAFT" },
    });
  } catch (err) {
    workerLog.error({ err, botId }, "syncBotStatus error");
  }
}

// ---------------------------------------------------------------------------
// Run lifecycle
// ---------------------------------------------------------------------------

/** Advance a single QUEUED run through STARTING → SYNCING → RUNNING. */
async function activateRun(runId: string) {
  try {
    // QUEUED → STARTING
    await transition(runId, "STARTING", {
      eventType: "RUN_STARTING",
      message: "Worker picked up run, initializing",
    });
    await sleep(800);

    // STARTING → SYNCING
    const afterStart = await prisma.botRun.findUnique({ where: { id: runId } });
    if (!afterStart || afterStart.state !== "STARTING") return; // aborted
    await transition(runId, "SYNCING", {
      eventType: "RUN_SYNCING",
      message: "Syncing market data",
    });
    await sleep(1_200);

    // SYNCING → RUNNING
    const afterSync = await prisma.botRun.findUnique({ where: { id: runId } });
    if (!afterSync || afterSync.state !== "SYNCING") return; // aborted
    await transition(runId, "RUNNING", {
      eventType: "RUN_RUNNING",
      message: "Bot is running",
      startedAt: new Date(),
    });

    // Lease to signal liveness
    await prisma.botRun.update({
      where: { id: runId },
      data: { leaseOwner: WORKER_ID, leaseUntil: new Date(Date.now() + 30_000) },
    });

    // Sync Bot.status → ACTIVE
    const run = await prisma.botRun.findUnique({ where: { id: runId }, select: { botId: true } });
    if (run) await syncBotStatus(run.botId);
  } catch (err) {
    // If another worker won or run was stopped, ignore
    workerLog.error({ err, runId }, "activateRun error");
  }
}

/** Advance a STOPPING run to STOPPED and sync Bot.status. */
async function stopRun(runId: string) {
  try {
    const run = await prisma.botRun.findUnique({ where: { id: runId } });
    if (!run || run.state !== "STOPPING") return;
    await transition(runId, "STOPPED", {
      eventType: "RUN_STOPPED",
      message: "Worker completed stop",
      stoppedAt: new Date(),
    });
    await syncBotStatus(run.botId);
  } catch (err) {
    workerLog.error({ err, runId }, "stopRun error");
  }
}

/**
 * Mark RUNNING runs that exceeded their duration as TIMED_OUT.
 * Respects per-run durationMinutes if set; falls back to MAX_RUN_DURATION_MS.
 */
async function timeoutExpiredRuns() {
  const now = Date.now();

  const candidates = await prisma.botRun.findMany({
    where: {
      state: "RUNNING",
      startedAt: { not: null },
    },
    select: { id: true, botId: true, startedAt: true, durationMinutes: true },
    take: 20,
  });

  for (const run of candidates) {
    if (!run.startedAt) continue;

    const maxDurationMs =
      run.durationMinutes !== null && run.durationMinutes !== undefined
        ? run.durationMinutes * 60 * 1000
        : MAX_RUN_DURATION_MS;

    const elapsed = now - run.startedAt.getTime();
    if (elapsed < maxDurationMs) continue;

    try {
      await transition(run.id, "TIMED_OUT", {
        eventType: "RUN_TIMED_OUT",
        message: `Run exceeded max duration of ${maxDurationMs / 1000}s`,
        errorCode: "MAX_DURATION_EXCEEDED",
      });
      workerLog.info({ runId: run.id, elapsed, maxDurationMs }, "run timed out");
      await syncBotStatus(run.botId);
    } catch (err) {
      workerLog.error({ err, runId: run.id }, "timeoutExpiredRuns error");
    }
  }
}

/** Renew lease on all RUNNING runs owned by this worker. */
async function renewLeases() {
  const newLeaseUntil = new Date(Date.now() + 30_000);
  await prisma.botRun.updateMany({
    where: { leaseOwner: WORKER_ID, state: "RUNNING" },
    data: { leaseUntil: newLeaseUntil },
  });
}

// ---------------------------------------------------------------------------
// Intent execution (Stage 11)
// ---------------------------------------------------------------------------

/**
 * Process a single BotIntent:
 * - Demo mode (no exchangeConnection): simulate immediately → FILLED
 * - Live mode (has exchangeConnection): call Bybit → PLACED (or FAILED on error)
 *
 * Uses optimistic locking: atomically claims PENDING → PLACED before acting.
 * If another worker already claimed it (count=0), skips silently.
 */
async function executeIntent(intent: {
  id: string;
  intentId: string;
  orderLinkId: string;
  side: string;
  qty: { toString: () => string };
  price: { toString: () => string } | null;
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
}) {
  const { botRun } = intent;
  const { bot } = botRun;

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
      workerLog.info({ intentId: intent.intentId }, "intent simulated (demo mode)");
    } else {
      // ── Live mode: place order on Bybit ──────────────────────────────────
      const encKey = getEncryptionKeyRaw();
      if (!encKey) {
        throw new Error("SECRET_ENCRYPTION_KEY not configured");
      }
      const plainSecret = decrypt(bot.exchangeConnection.encryptedSecret, encKey);

      // Determine orderType from strategy DSL or default to Market
      const dsl = bot.strategyVersion?.dslJson as { execution?: { orderType?: string } } | null;
      const orderType =
        (dsl?.execution?.orderType === "Limit" ? "Limit" : "Market") as "Market" | "Limit";

      const side = intent.side === "BUY" ? "Buy" : "Sell";

      const result = await bybitPlaceOrder(
        bot.exchangeConnection.apiKey,
        plainSecret,
        {
          symbol: bot.symbol,
          side,
          orderType,
          qty: intent.qty.toString(),
          ...(intent.price && orderType === "Limit" ? { price: intent.price.toString() } : {}),
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
      workerLog.info({ intentId: intent.intentId, orderId: result.orderId }, "intent placed");
    }
  } catch (err) {
    // Placement failed — mark intent as FAILED
    const meta = {
      ...(intent.metaJson && typeof intent.metaJson === "object" ? intent.metaJson as Record<string, unknown> : {}),
      error: String(err),
      failedAt: new Date().toISOString(),
    };
    await prisma.botIntent.update({
      where: { id: intent.id },
      data: { state: "FAILED", metaJson: meta as Prisma.InputJsonValue },
    });
    await prisma.botEvent.create({
      data: {
        botRunId: botRun.id,
        type: "intent_failed",
        payloadJson: {
          intentId: intent.intentId,
          error: String(err),
          at: new Date().toISOString(),
        } as Prisma.InputJsonValue,
      },
    });
    workerLog.error({ err, intentId: intent.intentId }, "executeIntent error");
  }
}

// ---------------------------------------------------------------------------
// Stage 12: DSL enforcement helpers
// ---------------------------------------------------------------------------

/**
 * Enforce risk.dailyLossLimitUsd for all RUNNING bot runs.
 *
 * Heuristic: failed_intents_today × estimated_loss_per_intent ≥ dailyLossLimitUsd
 * where estimated_loss_per_intent = (riskPerTradePct / 100) × maxPositionSizeUsd.
 *
 * When the limit is exceeded the run is transitioned to STOPPING.
 */
async function enforceDailyLossLimit(): Promise<void> {
  try {
    const runningRuns = await prisma.botRun.findMany({
      where: { state: "RUNNING" },
      select: {
        id: true,
        bot: {
          select: {
            strategyVersion: { select: { dslJson: true } },
          },
        },
      },
      take: 50,
    });

    const todayStart = new Date();
    todayStart.setHours(0, 0, 0, 0);

    for (const run of runningRuns) {
      const dsl = run.bot?.strategyVersion?.dslJson as Record<string, unknown> | null;
      const risk = dsl?.["risk"] as Record<string, unknown> | undefined;
      const dailyLossLimitUsd = typeof risk?.["dailyLossLimitUsd"] === "number"
        ? risk["dailyLossLimitUsd"] as number : null;
      if (!dailyLossLimitUsd || dailyLossLimitUsd <= 0) continue;

      const riskPerTradePct   = typeof risk?.["riskPerTradePct"]   === "number" ? risk["riskPerTradePct"]   as number : 1;
      const maxPositionSizeUsd = typeof risk?.["maxPositionSizeUsd"] === "number" ? risk["maxPositionSizeUsd"] as number : 100;
      const estimatedLossPerTrade = (riskPerTradePct / 100) * maxPositionSizeUsd;

      const failedToday = await prisma.botIntent.count({
        where: {
          botRunId: run.id,
          state: "FAILED",
          createdAt: { gte: todayStart },
        },
      });

      const estimatedDailyLoss = failedToday * estimatedLossPerTrade;
      if (estimatedDailyLoss < dailyLossLimitUsd) continue;

      try {
        await transition(run.id, "STOPPING", {
          eventType: "RUN_STOPPING",
          message: `Daily loss limit $${dailyLossLimitUsd} exceeded (estimated loss: $${estimatedDailyLoss.toFixed(2)} from ${failedToday} failed intent(s))`,
        });
        workerLog.info({ runId: run.id, estimatedDailyLoss, dailyLossLimitUsd }, "daily loss limit exceeded, stopping run");
      } catch (err) {
        workerLog.error({ err, runId: run.id }, "enforceDailyLossLimit error");
      }
    }
  } catch (err) {
    workerLog.error({ err }, "enforceDailyLossLimit error");
  }
}

/**
 * Process all PENDING intents on RUNNING runs.
 * Picks up to 20 at a time ordered by creation time.
 */
async function processIntents() {
  try {
    const pendingIntents = await prisma.botIntent.findMany({
      where: {
        state: "PENDING",
        botRun: { state: "RUNNING" },
      },
      include: {
        botRun: {
          include: {
            bot: {
              select: {
                id: true,
                symbol: true,
                exchangeConnectionId: true,
                exchangeConnection: {
                  select: { apiKey: true, encryptedSecret: true },
                },
                strategyVersion: {
                  select: { dslJson: true },
                },
              },
            },
          },
        },
      },
      orderBy: { createdAt: "asc" },
      take: 20,
    });

    for (const intent of pendingIntents) {
      // Stage 12: respect enabled: false — cancel intents for disabled strategies
      const dsl = intent.botRun.bot.strategyVersion?.dslJson as Record<string, unknown> | null;
      if (dsl && dsl["enabled"] === false) {
        await prisma.botIntent.updateMany({
          where: { id: intent.id, state: "PENDING" },
          data: {
            state: "CANCELLED",
            metaJson: { reason: "strategy_disabled", at: new Date().toISOString() } as Prisma.InputJsonValue,
          },
        });
        await prisma.botEvent.create({
          data: {
            botRunId: intent.botRun.id,
            type: "intent_cancelled",
            payloadJson: {
              intentId: intent.intentId,
              reason: "strategy disabled (enabled: false)",
              at: new Date().toISOString(),
            } as Prisma.InputJsonValue,
          },
        });
        workerLog.info({ intentId: intent.intentId }, "intent cancelled — strategy disabled");
        continue;
      }

      // Type narrowing: botRun.bot is always included here
      await executeIntent(intent as Parameters<typeof executeIntent>[0]);
    }
  } catch (err) {
    workerLog.error({ err }, "processIntents error");
  }
}

// ---------------------------------------------------------------------------
// Main polling loop
// ---------------------------------------------------------------------------

/** Main polling loop. */
async function poll() {
  try {
    // Pick up QUEUED runs (up to 5 at a time)
    const queued = await prisma.botRun.findMany({
      where: { state: "QUEUED" },
      take: 5,
      orderBy: { createdAt: "asc" },
      select: { id: true },
    });
    for (const { id } of queued) {
      activateRun(id); // fire-and-forget, don't await to stay non-blocking
    }

    // Complete STOPPING runs
    const stopping = await prisma.botRun.findMany({
      where: { state: "STOPPING" },
      take: 10,
      select: { id: true },
    });
    for (const { id } of stopping) {
      await stopRun(id);
    }

    // Timeout runs that exceeded max duration
    await timeoutExpiredRuns();

    // Renew leases on our RUNNING runs
    await renewLeases();

    // Process PENDING intents on RUNNING runs (Stage 11)
    await processIntents();
  } catch (err) {
    workerLog.error({ err }, "poll error");
  }
}

/** Start the background worker. Returns a cleanup function. */
export function startBotWorker(): () => void {
  workerLog.info({ workerId: WORKER_ID, interval: POLL_INTERVAL_MS }, "botWorker started");
  const timer = setInterval(poll, POLL_INTERVAL_MS);
  // Run once immediately
  poll();
  return () => clearInterval(timer);
}
