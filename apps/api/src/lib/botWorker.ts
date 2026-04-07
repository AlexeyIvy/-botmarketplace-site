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
 * Safety circuit breakers (Stage 8, #141):
 *   guards.pauseOnError    → RUNNING run transitions to STOPPING when N consecutive
 *                            intents are FAILED (default threshold: 3)
 *
 * The worker runs in the same process. For production, extract into a
 * dedicated worker process.
 */

import { logger } from "./logger.js";
import { Prisma } from "@prisma/client";
import { prisma } from "./prisma.js";
import { transition, isValidTransition } from "./stateMachine.js";
import {
  bybitPlaceOrder,
  bybitGetOrderStatus,
  mapBybitStatus,
  getBybitBaseUrl,
  isBybitLive,
} from "./bybitOrder.js";
import { decrypt, getEncryptionKeyRaw } from "./crypto.js";
import {
  getActivePosition,
  openPosition,
  applyPartialFill,
  closePosition,
  updateSLTP,
  type PositionSnapshot,
} from "./positionManager.js";
import { evaluateEntry, type OpenSignal } from "./signalEngine.js";
import {
  evaluateExit,
  createTrailingStopState,
  type CloseSignal,
  type TrailingStopState,
} from "./exitEngine.js";
import { computeSizing } from "./riskManager.js";
import { getInstrument, type InstrumentInfo } from "./exchange/instrumentCache.js";
import { normalizeOrder } from "./exchange/normalizer.js";
import { sizeOrder } from "./runtime/positionSizer.js";
import {
  extractDcaConfig,
  extractSlPct,
  initializeDcaLadder,
  handleDcaBaseFill,
  handleDcaSoFill,
  finalizeDcaLadder,
  recoverDcaState,
  checkAndTriggerSOs,
} from "./runtime/dcaBridge.js";
import { serializeDcaState, type DcaRuntimeState } from "./runtime/dcaEngine.js";
import { reconstructRunState } from "./recoveryManager.js";
import {
  reconcileStartupState,
  detectStartupInconsistencies,
  type StartupIntent,
} from "./stateReconciler.js";
import { classifyExecutionError } from "./errorClassifier.js";
import {
  parseDailyLossConfig,
  parseGuardsConfig,
  shouldTriggerDailyLossLimit,
  shouldPauseOnError,
  DEFAULT_ERROR_PAUSE_THRESHOLD,
} from "./safetyGuards.js";
import { notifyRunEvent } from "./notify.js";

const workerLog = logger.child({ module: "botWorker" });

const WORKER_ID = `worker-${process.pid}`;
const POLL_INTERVAL_MS = 4_000;

// ---------------------------------------------------------------------------
// Worker health observability (Task #18)
// ---------------------------------------------------------------------------

/** Timestamp (ms) of the last completed poll cycle. 0 = worker never ran. */
export let lastPollTimestampMs = 0;

/** Exported for /readyz to check if worker is alive. */
export { POLL_INTERVAL_MS };

/** Max retries for transient intent failures before dead-lettering (Task #22). */
const MAX_INTENT_RETRIES = parseInt(process.env.MAX_INTENT_RETRIES ?? "", 10) || 3;

// Max time a run can stay in RUNNING state before auto-timeout (default: 4 hours)
const MAX_RUN_DURATION_MS = parseInt(process.env.MAX_RUN_DURATION_MS ?? "", 10) || 4 * 60 * 60 * 1000;

/** Max time a run can stay in STARTING/SYNCING before being marked FAILED. */
const EPHEMERAL_TIMEOUT_MS = 5 * 60 * 1000; // 5 min

// Stage 19c: MarketCandle retention
const RETENTION_DAYS = parseInt(process.env.MARKET_CANDLE_RETENTION_DAYS ?? "", 10) || 90;
const RETENTION_INTERVAL_MS = 60 * 60 * 1000; // minimum gap between retention runs (1 hour)
let lastRetentionRunMs = 0;

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

    // STARTING → SYNCING
    const afterStart = await prisma.botRun.findUnique({ where: { id: runId } });
    if (!afterStart || afterStart.state !== "STARTING") return; // aborted
    await transition(runId, "SYNCING", {
      eventType: "RUN_SYNCING",
      message: "Syncing market data",
    });

    // SYNCING → RUNNING
    const afterSync = await prisma.botRun.findUnique({
      where: { id: runId },
      include: { bot: { select: { id: true, symbol: true } } },
    });
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

    // Stage 3 (#127/#130): reconstruct ephemeral state after restart/resume
    try {
      const existingPosition = await getActivePosition(runId, afterSync.bot.symbol);

      // Query last trade close timestamp from PositionEvent log
      let lastCloseEventTimestamp = 0;
      try {
        const lastCloseEvent = await prisma.positionEvent.findFirst({
          where: {
            position: { botRunId: runId },
            type: "CLOSE",
          },
          orderBy: { ts: "desc" },
          select: { ts: true },
        });
        if (lastCloseEvent) {
          lastCloseEventTimestamp = lastCloseEvent.ts.getTime();
        }
      } catch (_err) {
        // Non-fatal: if we can't find close events, cooldown starts fresh
      }

      // Reconstruct all ephemeral state from persistent data
      const recovered = reconstructRunState(existingPosition, lastCloseEventTimestamp);

      // Apply to in-memory maps
      if (recovered.trailingStopState) {
        trailingStopStates.set(runId, recovered.trailingStopState);
      }
      if (recovered.lastTradeCloseTime > 0) {
        lastTradeCloseTimes.set(runId, recovered.lastTradeCloseTime);
      }

      if (existingPosition) {
        // DCA recovery (#132 slice 4): check if position has active DCA ladder state.
        // The DCA state in Position.metaJson is already persistent — the poll loop
        // reads it on each evaluation. Log recovery for diagnostics.
        let dcaRecovered = false;
        let dcaLadderPhase: string | undefined;
        let dcaSosFilled: number | undefined;
        try {
          const posRow = await prisma.position.findUnique({
            where: { id: existingPosition.id },
            select: { metaJson: true },
          });
          const dcaState = recoverDcaState(posRow?.metaJson);
          if (dcaState) {
            dcaRecovered = true;
            dcaLadderPhase = dcaState.phase;
            dcaSosFilled = dcaState.safetyOrdersFilled;
          }
        } catch (_dcaErr) {
          // Non-fatal: if DCA state can't be read, poll loop will handle it
        }

        workerLog.info(
          {
            runId,
            positionId: existingPosition.id,
            side: existingPosition.side,
            currentQty: existingPosition.currentQty,
            avgEntryPrice: existingPosition.avgEntryPrice,
            trailingStopReconstructed: !!recovered.trailingStopState,
            lastTradeCloseTimeReconstructed: recovered.lastTradeCloseTime > 0,
            dcaRecovered,
            ...(dcaRecovered ? { dcaLadderPhase, dcaSosFilled } : {}),
          },
          "recovered existing open position and ephemeral state on startup",
        );
        await prisma.botEvent.create({
          data: {
            botRunId: runId,
            type: "position_recovered",
            payloadJson: {
              positionId: existingPosition.id,
              side: existingPosition.side,
              currentQty: existingPosition.currentQty,
              avgEntryPrice: existingPosition.avgEntryPrice,
              realisedPnl: existingPosition.realisedPnl,
              trailingStopReconstructed: !!recovered.trailingStopState,
              lastTradeCloseTime: recovered.lastTradeCloseTime,
              ...(dcaRecovered ? { dcaRecovered, dcaLadderPhase, dcaSosFilled } : {}),
            } as Prisma.InputJsonValue,
          },
        });
      } else if (recovered.lastTradeCloseTime > 0) {
        workerLog.info(
          { runId, lastTradeCloseTime: recovered.lastTradeCloseTime },
          "recovered cooldown state on startup (no open position)",
        );
      }
    } catch (err) {
      workerLog.warn({ err, runId }, "failed to read position on startup (non-fatal)");
    }

    // Stage 8 (#141): startup intent reconciliation
    // Cancel stale PENDING intents from before restart and audit in-flight state.
    try {
      const allIntents = await prisma.botIntent.findMany({
        where: { botRunId: runId },
        select: {
          id: true,
          intentId: true,
          state: true,
          type: true,
          side: true,
          orderId: true,
          createdAt: true,
        },
        orderBy: { createdAt: "desc" },
        take: 50,
      });

      const existingPosition = await getActivePosition(runId, afterSync.bot.symbol);

      // Pre-cancellation consistency check (for logging)
      const inconsistencies = detectStartupInconsistencies(
        allIntents as StartupIntent[],
        existingPosition,
      );
      if (inconsistencies.length > 0) {
        workerLog.warn(
          { runId, inconsistencies },
          "startup inconsistencies detected (will be resolved by reconciliation)",
        );
      }

      const result = reconcileStartupState(
        allIntents as StartupIntent[],
        existingPosition,
      );

      // Cancel stale PENDING intents
      if (result.toCancel.length > 0) {
        const cancelIds = result.toCancel.map((c) => c.id);
        await prisma.botIntent.updateMany({
          where: {
            id: { in: cancelIds },
            state: "PENDING", // guard: only cancel if still PENDING
          },
          data: {
            state: "CANCELLED",
            metaJson: {
              reason: "startup_reconciliation",
              cancelledAt: new Date().toISOString(),
            } as Prisma.InputJsonValue,
          },
        });

        await prisma.botEvent.create({
          data: {
            botRunId: runId,
            type: "startup_reconciliation",
            payloadJson: {
              action: "cancel_stale_intents",
              cancelledCount: result.toCancel.length,
              cancelledIntentIds: result.toCancel.map((c) => c.intentId),
              inconsistencies,
              summary: result.summary,
              counts: result.counts,
            } as Prisma.InputJsonValue,
          },
        });

        workerLog.info(
          { runId, cancelledCount: result.toCancel.length, summary: result.summary },
          "startup reconciliation: cancelled stale intents",
        );
      } else if (result.toMonitor.length > 0) {
        // No stale intents but some in-flight — log for visibility
        await prisma.botEvent.create({
          data: {
            botRunId: runId,
            type: "startup_reconciliation",
            payloadJson: {
              action: "audit_only",
              inFlightCount: result.toMonitor.length,
              summary: result.summary,
              counts: result.counts,
            } as Prisma.InputJsonValue,
          },
        });

        workerLog.info(
          { runId, inFlightCount: result.toMonitor.length, summary: result.summary },
          "startup reconciliation: in-flight intents will be tracked by exchange loop",
        );
      }
    } catch (err) {
      workerLog.warn({ err, runId }, "startup reconciliation error (non-fatal)");
    }

    // Sync Bot.status → ACTIVE
    await syncBotStatus(afterSync.bot.id);
  } catch (err) {
    workerLog.error({ err, runId }, "activateRun error");
    try {
      const failedRun = await prisma.botRun.findUnique({ where: { id: runId }, select: { workspaceId: true, symbol: true } });
      await transition(runId, "FAILED", {
        eventType: "RUN_FAILED",
        message: `activateRun crashed: ${err instanceof Error ? err.message : String(err)}`,
        errorCode: "ACTIVATE_CRASH",
      });
      if (failedRun) {
        notifyRunEvent(failedRun.workspaceId, {
          eventType: "RUN_FAILED",
          runId,
          symbol: failedRun.symbol,
          message: `Run activation crashed: ${err instanceof Error ? err.message : String(err)}`,
        });
      }
    } catch (transitionErr) {
      workerLog.warn({ err: transitionErr, runId }, "failed to transition crashed run to FAILED");
    }
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

  // Catch runs stuck in ephemeral states (STARTING/SYNCING) due to activateRun crashes
  const stuckEphemeral = await prisma.botRun.findMany({
    where: {
      state: { in: ["STARTING", "SYNCING"] },
      updatedAt: { lt: new Date(now - EPHEMERAL_TIMEOUT_MS) },
    },
    select: { id: true, botId: true, state: true, updatedAt: true, workspaceId: true, symbol: true },
    take: 20,
  });

  for (const run of stuckEphemeral) {
    try {
      await transition(run.id, "FAILED", {
        eventType: "RUN_FAILED",
        message: `Run stuck in ${run.state} for over 5 minutes`,
        errorCode: "EPHEMERAL_STATE_TIMEOUT",
      });
      workerLog.warn({ runId: run.id, state: run.state }, "stuck ephemeral run → FAILED");
      await syncBotStatus(run.botId);
      notifyRunEvent(run.workspaceId, {
        eventType: "RUN_FAILED",
        runId: run.id,
        symbol: run.symbol,
        message: `Run stuck in ${run.state} for over 5 minutes — moved to FAILED`,
      });
    } catch (err) {
      workerLog.error({ err, runId: run.id }, "failed to timeout stuck ephemeral run");
    }
  }

  const candidates = await prisma.botRun.findMany({
    where: {
      state: "RUNNING",
      startedAt: { not: null },
    },
    select: { id: true, botId: true, startedAt: true, durationMinutes: true, workspaceId: true, symbol: true },
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
      notifyRunEvent(run.workspaceId, {
        eventType: "RUN_TIMED_OUT",
        runId: run.id,
        symbol: run.symbol,
        message: `Run exceeded max duration of ${Math.round(maxDurationMs / 60000)} minutes`,
      });
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
      const plainSecret = decrypt(bot.exchangeConnection.encryptedSecret, encKey);

      // Determine orderType from strategy DSL or default to Market
      const dsl = bot.strategyVersion?.dslJson as { execution?: { orderType?: string } } | null;
      const orderType =
        (dsl?.execution?.orderType === "Limit" ? "Limit" : "Market") as "Market" | "Limit";

      const side = intent.side === "BUY" ? "Buy" : "Sell";

      // Stage 3 (#129): normalize order through instrument rules
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

        workerLog.info(
          {
            intentId: intent.intentId,
            diagnostics: normalized.order.diagnostics,
            env: isBybitLive() ? "live" : "demo",
            baseUrl: getBybitBaseUrl(),
          },
          "order normalized",
        );
      } catch (normErr) {
        // If normalization itself fails (e.g. instrument not found), log and throw
        workerLog.warn({ err: normErr, intentId: intent.intentId }, "order normalization error");
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
      workerLog.info({ intentId: intent.intentId, orderId: result.orderId }, "intent placed");
    }
  } catch (err) {
    // Stage 8 (#141) + Task #22: classify error and decide retry vs dead-letter
    const classification = classifyExecutionError(err);
    const currentRetry = intent.retryCount;
    const canRetry = classification.retryable && currentRetry < MAX_INTENT_RETRIES;

    if (canRetry) {
      // ── Retry: put back to PENDING with incremented retryCount ──
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
      workerLog.warn(
        {
          intentId: intent.intentId,
          errorClass: classification.errorClass,
          retryAttempt: currentRetry + 1,
          maxRetries: MAX_INTENT_RETRIES,
        },
        `executeIntent transient error — retry ${currentRetry + 1}/${MAX_INTENT_RETRIES}`,
      );
    } else {
      // ── Dead-letter: max retries exhausted or permanent error ──
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
      workerLog.error(
        {
          err,
          intentId: intent.intentId,
          errorClass: classification.errorClass,
          retryable: classification.retryable,
          retryCount: currentRetry,
          deadLetterReason,
        },
        `executeIntent ${classification.retryable ? "dead-lettered" : "permanent failure"}`,
      );
    }
  }
}

// ---------------------------------------------------------------------------
// Stage 12: DSL enforcement helpers
// ---------------------------------------------------------------------------

/**
 * Enforce risk.dailyLossLimitUsd for all RUNNING bot runs.
 *
 * Uses pure decision function from safetyGuards.ts:
 *   failed_intents_today × estimated_loss_per_intent ≥ dailyLossLimitUsd
 *
 * When the limit is exceeded the run is transitioned to STOPPING.
 */
async function enforceDailyLossLimit(): Promise<void> {
  try {
    const runningRuns = await prisma.botRun.findMany({
      where: { state: "RUNNING" },
      select: {
        id: true,
        workspaceId: true,
        symbol: true,
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
      const config = parseDailyLossConfig(run.bot?.strategyVersion?.dslJson);
      if (config.dailyLossLimitUsd === null) continue;

      const failedToday = await prisma.botIntent.count({
        where: {
          botRunId: run.id,
          state: "FAILED",
          createdAt: { gte: todayStart },
        },
      });

      const result = shouldTriggerDailyLossLimit(config, failedToday);
      if (!result.triggered) continue;

      try {
        await transition(run.id, "STOPPING", {
          eventType: "RUN_STOPPING",
          message: `Daily loss limit: ${result.reason}`,
        });
        workerLog.info(
          { runId: run.id, estimatedLoss: result.estimatedLoss, dailyLossLimitUsd: config.dailyLossLimitUsd },
          "daily loss limit exceeded, stopping run",
        );
        notifyRunEvent(run.workspaceId, {
          eventType: "RUN_STOPPING",
          runId: run.id,
          symbol: run.symbol,
          message: `Daily loss limit breached: ${result.reason}`,
        });
      } catch (err) {
        workerLog.error({ err, runId: run.id }, "enforceDailyLossLimit transition error");
      }
    }
  } catch (err) {
    workerLog.error({ err }, "enforceDailyLossLimit error");
  }
}

/**
 * Enforce guards.pauseOnError for all RUNNING bot runs (#141).
 *
 * When pauseOnError is true (default) and the most recent N intents
 * on a run are all FAILED, the run is transitioned to STOPPING.
 *
 * Uses pure decision function from safetyGuards.ts.
 */
async function enforceErrorPause(): Promise<void> {
  try {
    const runningRuns = await prisma.botRun.findMany({
      where: { state: "RUNNING" },
      select: {
        id: true,
        workspaceId: true,
        symbol: true,
        bot: {
          select: {
            strategyVersion: { select: { dslJson: true } },
          },
        },
      },
      take: 50,
    });

    for (const run of runningRuns) {
      const guards = parseGuardsConfig(run.bot?.strategyVersion?.dslJson);
      if (!guards.pauseOnError) continue;

      // Count consecutive FAILED intents from most recent
      const recentIntents = await prisma.botIntent.findMany({
        where: { botRunId: run.id },
        orderBy: { createdAt: "desc" },
        take: DEFAULT_ERROR_PAUSE_THRESHOLD,
        select: { state: true },
      });

      // If fewer intents than threshold exist, can't trigger
      if (recentIntents.length < DEFAULT_ERROR_PAUSE_THRESHOLD) continue;

      // Count how many of the most recent intents are FAILED
      let consecutiveFailed = 0;
      for (const intent of recentIntents) {
        if (intent.state === "FAILED") {
          consecutiveFailed++;
        } else {
          break;
        }
      }

      const result = shouldPauseOnError(guards.pauseOnError, consecutiveFailed);
      if (!result.triggered) continue;

      try {
        await transition(run.id, "STOPPING", {
          eventType: "RUN_STOPPING",
          message: `Pause on error: ${result.reason}`,
        });
        workerLog.info(
          { runId: run.id, consecutiveFailed, threshold: result.threshold },
          "pauseOnError triggered, stopping run",
        );
        notifyRunEvent(run.workspaceId, {
          eventType: "RUN_STOPPING",
          runId: run.id,
          symbol: run.symbol,
          message: `Circuit breaker: ${consecutiveFailed} consecutive failed intents`,
        });
      } catch (err) {
        workerLog.error({ err, runId: run.id }, "enforceErrorPause transition error");
      }
    }
  } catch (err) {
    workerLog.error({ err }, "enforceErrorPause error");
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
// Partial-fill reconciliation (Stage 3, #129 follow-up)
// ---------------------------------------------------------------------------

/**
 * Reconcile PLACED and PARTIALLY_FILLED intents against exchange order status.
 *
 * For each intent with an exchange orderId:
 * 1. Fetch live status from Bybit
 * 2. Compute fill delta (new cumExecQty - previously tracked cumExecQty)
 * 3. Route fill through position lifecycle:
 *    - ENTRY first fill → openPosition()
 *    - ENTRY subsequent fills → applyPartialFill("entry")
 *    - EXIT fills → applyPartialFill("exit") / closePosition()
 * 4. Update intent state + cumExecQty
 *
 * This is a minimal reconciliation loop — not a full OMS.
 * Runs once per poll cycle, processes up to 20 intents.
 */
async function reconcilePlacedIntents(): Promise<void> {
  try {
    const intents = await prisma.botIntent.findMany({
      where: {
        state: { in: ["PLACED", "PARTIALLY_FILLED"] },
        orderId: { not: null },
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
              },
            },
          },
        },
      },
      orderBy: { createdAt: "asc" },
      take: 20,
    });

    if (intents.length === 0) return;

    const encKey = getEncryptionKeyRaw();

    for (const intent of intents) {
      const { bot } = intent.botRun;
      if (!bot.exchangeConnection || !intent.orderId) continue;

      try {
        const secret = decrypt(bot.exchangeConnection.encryptedSecret, encKey);
        const liveStatus = await bybitGetOrderStatus(
          bot.exchangeConnection.apiKey,
          secret,
          intent.orderId,
          bot.symbol,
        );

        const mapped = mapBybitStatus(liveStatus.orderStatus);
        const exchangeCumQty = Number(liveStatus.cumExecQty || "0");
        const prevCumQty = intent.cumExecQty ? intent.cumExecQty.toNumber() : 0;
        const fillDelta = exchangeCumQty - prevCumQty;

        // No new fills — skip
        if (fillDelta <= 0 && mapped !== "CANCELLED" && mapped !== "REJECTED") {
          continue;
        }

        // Derive fill price: use actual avg fill price from exchange,
        // fall back to order price, then intent price
        const avgP = Number(liveStatus.avgPrice || "0");
        const fillPrice = avgP > 0
          ? avgP
          : (Number(liveStatus.price || "0") > 0
            ? Number(liveStatus.price)
            : (intent.price ? intent.price.toNumber() : 0));

        // Determine intent type from DB
        const isEntry = intent.type === "ENTRY";
        const isExit = intent.type === "EXIT";

        // Route fill delta through position lifecycle
        if (fillDelta > 0) {
          const meta = intent.metaJson && typeof intent.metaJson === "object"
            ? intent.metaJson as Record<string, unknown>
            : {};

          if (isEntry) {
            await reconcileEntryFill(intent, bot, fillDelta, fillPrice, prevCumQty, meta, intent.side);
          } else if (isExit) {
            await reconcileExitFill(intent, bot, fillDelta, fillPrice, meta);
          }
        }

        // Determine new intent state
        let newState: "PLACED" | "PARTIALLY_FILLED" | "FILLED" | "CANCELLED" | "FAILED" = intent.state as "PLACED" | "PARTIALLY_FILLED";
        if (mapped === "FILLED") {
          newState = "FILLED";
        } else if (mapped === "PARTIALLY_FILLED") {
          newState = "PARTIALLY_FILLED";
        } else if (mapped === "CANCELLED" || mapped === "REJECTED") {
          newState = mapped === "CANCELLED" ? "CANCELLED" : "FAILED";
        }

        // Update intent with fill progress
        const updateMeta = {
          ...(intent.metaJson && typeof intent.metaJson === "object" ? intent.metaJson as Record<string, unknown> : {}),
          lastReconcileAt: new Date().toISOString(),
          exchangeStatus: liveStatus.orderStatus,
        };

        await prisma.botIntent.update({
          where: { id: intent.id },
          data: {
            state: newState,
            cumExecQty: exchangeCumQty,
            avgFillPrice: fillPrice > 0 ? fillPrice : undefined,
            metaJson: updateMeta as Prisma.InputJsonValue,
          },
        });

        if (fillDelta > 0 || newState !== intent.state) {
          await prisma.botEvent.create({
            data: {
              botRunId: intent.botRun.id,
              type: "intent_reconciled",
              payloadJson: {
                intentId: intent.intentId,
                orderId: intent.orderId,
                prevState: intent.state,
                newState,
                cumExecQty: exchangeCumQty,
                fillDelta,
                fillPrice,
                exchangeStatus: liveStatus.orderStatus,
                at: new Date().toISOString(),
              } as Prisma.InputJsonValue,
            },
          });

          workerLog.info(
            {
              intentId: intent.intentId,
              orderId: intent.orderId,
              prevState: intent.state,
              newState,
              fillDelta,
              cumExecQty: exchangeCumQty,
            },
            "intent reconciled",
          );
        }
      } catch (err) {
        workerLog.warn(
          { err, intentId: intent.intentId, orderId: intent.orderId },
          "reconcile intent error (non-fatal)",
        );
      }
    }
  } catch (err) {
    workerLog.error({ err }, "reconcilePlacedIntents error");
  }
}

/**
 * Handle entry-side fill: first fill opens position, subsequent fills add to it.
 */
async function reconcileEntryFill(
  intent: { id: string; intentId: string; botRun: { id: string }; metaJson: Prisma.JsonValue },
  bot: { id: string; symbol: string },
  fillDelta: number,
  fillPrice: number,
  prevCumQty: number,
  meta: Record<string, unknown>,
  intentSide: string,
): Promise<void> {
  const position = await getActivePosition(intent.botRun.id, bot.symbol);

  // Check if this is a DCA entry
  const isDcaEntry = meta.dca === true;

  if (!position && prevCumQty === 0) {
    // First fill on new entry — open position
    let slPrice = typeof meta.slPrice === "number" ? meta.slPrice : undefined;
    let tpPrice = typeof meta.tpPrice === "number" ? meta.tpPrice : undefined;
    let positionMeta: Record<string, unknown> | undefined;

    // DCA base fill (#132): apply base fill to DCA state, persist to position metaJson
    if (isDcaEntry && meta.dcaState) {
      const recoveredState = recoverDcaState({ dcaState: meta.dcaState });
      if (recoveredState) {
        const baseResult = handleDcaBaseFill(recoveredState, fillPrice, fillDelta);
        const dcaState = baseResult.state;
        // Override SL/TP with DCA-computed values
        slPrice = dcaState.slPrice;
        tpPrice = dcaState.tpPrice;
        positionMeta = {
          source: "reconciliation",
          orderId: intent.id,
          dcaState: serializeDcaState(dcaState),
        };

        workerLog.info(
          {
            intentId: intent.intentId,
            avgEntry: dcaState.avgEntryPrice,
            tp: dcaState.tpPrice,
            sl: dcaState.slPrice,
            pendingSOs: baseResult.pendingSOs.length,
          },
          "DCA base fill: ladder activated",
        );
      }
    }

    // Derive position side from intent side (BUY→LONG, SELL→SHORT)
    const positionSide = intentSide === "SELL" ? "SHORT" as const : "LONG" as const;

    await openPosition({
      botId: bot.id,
      botRunId: intent.botRun.id,
      symbol: bot.symbol,
      side: positionSide,
      qty: fillDelta,
      price: fillPrice,
      slPrice,
      tpPrice,
      intentId: intent.intentId,
      meta: positionMeta ?? { source: "reconciliation", orderId: intent.id },
    });

    workerLog.info(
      { intentId: intent.intentId, qty: fillDelta, price: fillPrice, dca: isDcaEntry },
      "position opened from reconciled entry fill",
    );
  } else if (position) {
    // Subsequent fill — add to existing position via partial fill
    await applyPartialFill({
      positionId: position.id,
      filledQty: fillDelta,
      fillPrice,
      fillSide: "entry",
      intentId: intent.intentId,
      meta: { source: "reconciliation", orderId: intent.id },
    });

    // DCA SO fill (#132): if position has DCA state, advance the ladder.
    // Contract: SO intents (created in slice 3) must also carry meta.dca === true
    // for this path to activate on their fills.
    if (isDcaEntry) {
      const existingPos = await prisma.position.findUnique({
        where: { id: position.id },
        select: { metaJson: true },
      });
      const dcaState = recoverDcaState(existingPos?.metaJson);
      if (dcaState && dcaState.nextSoIndex >= 0) {
        // Validate soIndex from intent matches expected nextSoIndex from state.
        // In normal sequential processing these always agree; a mismatch means
        // a race or replay anomaly — log warning but proceed with state's index
        // since the engine enforces sequential fill guards.
        const intentSoIndex = typeof meta.soIndex === "number" ? meta.soIndex : undefined;
        if (intentSoIndex !== undefined && intentSoIndex !== dcaState.nextSoIndex) {
          workerLog.warn(
            { intentSoIndex, stateNextSoIndex: dcaState.nextSoIndex, intentId: intent.intentId },
            "DCA SO index mismatch: intent soIndex differs from state nextSoIndex",
          );
        }
        const soResult = handleDcaSoFill(dcaState, dcaState.nextSoIndex, fillPrice, fillDelta);
        if (soResult.exitLevelsChanged) {
          // Merge updated DCA state into existing metaJson (preserve other fields)
          const existingMeta = (existingPos?.metaJson as Record<string, unknown>) ?? {};
          await prisma.position.update({
            where: { id: position.id },
            data: {
              metaJson: {
                ...existingMeta,
                dcaState: serializeDcaState(soResult.state),
              } as Prisma.InputJsonValue,
            },
          });
          await updateSLTP({
            positionId: position.id,
            slPrice: soResult.state.slPrice,
            tpPrice: soResult.state.tpPrice,
            meta: { intentId: intent.intentId, source: "dca_so_fill" },
          });

          workerLog.info(
            {
              intentId: intent.intentId,
              positionId: position.id,
              soIndex: dcaState.nextSoIndex,
              avgEntry: soResult.state.avgEntryPrice,
              tp: soResult.state.tpPrice,
              sl: soResult.state.slPrice,
              sosFilled: soResult.state.safetyOrdersFilled,
            },
            "DCA SO fill: ladder advanced",
          );
        }
      }
    }

    workerLog.info(
      { intentId: intent.intentId, positionId: position.id, fillDelta, fillPrice },
      "partial entry fill applied to position",
    );
  }
}

/**
 * Handle exit-side fill: reduce position through partial fill or close.
 */
async function reconcileExitFill(
  intent: { id: string; intentId: string; botRun: { id: string }; metaJson: Prisma.JsonValue },
  bot: { id: string; symbol: string },
  fillDelta: number,
  fillPrice: number,
  meta: Record<string, unknown>,
): Promise<void> {
  const positionId = typeof meta.positionId === "string" ? meta.positionId : undefined;
  const position = positionId
    ? await prisma.position.findUnique({ where: { id: positionId } }).then((p) =>
        p && p.status === "OPEN" ? { id: p.id, currentQty: p.currentQty.toNumber() } : null,
      )
    : await getActivePosition(intent.botRun.id, bot.symbol);

  if (!position) {
    workerLog.warn(
      { intentId: intent.intentId },
      "no open position found for exit fill reconciliation",
    );
    return;
  }

  await applyPartialFill({
    positionId: position.id,
    filledQty: fillDelta,
    fillPrice,
    fillSide: "exit",
    intentId: intent.intentId,
    meta: { source: "reconciliation", orderId: intent.id },
  });

  // DCA ladder finalization (#132 slice 3): if position had DCA state,
  // mark ladder as completed on exit fill. This is best-effort — if
  // position is fully closed, the DCA ladder is done regardless.
  try {
    const posRow = await prisma.position.findUnique({
      where: { id: position.id },
      select: { metaJson: true, currentQty: true },
    });
    if (posRow) {
      const dcaState = recoverDcaState(posRow.metaJson);
      if (dcaState && dcaState.phase === "ladder_active" && posRow.currentQty.toNumber() <= 0) {
        // Only finalize when position is fully closed (currentQty = 0).
        // Partial exits don't end the DCA ladder.
        const finalized = finalizeDcaLadder(dcaState, "position_closed");
        if (finalized.state.phase !== dcaState.phase) {
          const existingMeta = (posRow.metaJson as Record<string, unknown>) ?? {};
          await prisma.position.update({
            where: { id: position.id },
            data: {
              metaJson: {
                ...existingMeta,
                dcaState: serializeDcaState(finalized.state),
              } as Prisma.InputJsonValue,
            },
          });
          workerLog.info(
            { positionId: position.id, sosFilled: dcaState.safetyOrdersFilled, reason: "position_closed" },
            "DCA ladder finalized on exit fill",
          );
        }
      }
    }
  } catch (dcaErr) {
    workerLog.warn({ err: dcaErr, positionId: position.id }, "DCA finalization error (non-fatal)");
  }

  workerLog.info(
    { intentId: intent.intentId, positionId: position.id, fillDelta, fillPrice },
    "exit fill applied to position",
  );
}

// ---------------------------------------------------------------------------
// Stage 3 (#128): Runtime strategy evaluation — signal/exit engine
// ---------------------------------------------------------------------------

/** Per-run trailing stop state, keyed by runId. */
const trailingStopStates = new Map<string, TrailingStopState>();

/** Per-run last trade close time, keyed by runId. */
const lastTradeCloseTimes = new Map<string, number>();

/**
 * Evaluate DSL strategy for all RUNNING runs with compiled DSL.
 *
 * For each run:
 *  1. Load recent candles from MarketCandle table
 *  2. Load current position state
 *  3. If no position → evaluate entry via signalEngine → create ENTRY intent
 *  4. If in position → evaluate exit via exitEngine → create EXIT intent
 *
 * Intent creation is idempotent: uses intentId derived from trigger timestamp
 * to prevent duplicates.
 */
async function evaluateStrategies(): Promise<void> {
  try {
    const runningRuns = await prisma.botRun.findMany({
      where: { state: "RUNNING" },
      select: {
        id: true,
        startedAt: true,
        bot: {
          select: {
            id: true,
            symbol: true,
            strategyVersion: { select: { dslJson: true } },
          },
        },
      },
      take: 20,
    });

    for (const run of runningRuns) {
      const dslJson = run.bot?.strategyVersion?.dslJson;
      if (!dslJson || typeof dslJson !== "object") continue;

      // Check if strategy is enabled
      const dsl = dslJson as Record<string, unknown>;
      if (dsl["enabled"] === false) continue;

      const symbol = run.bot.symbol;

      try {
        // Load recent candles (enough for indicator warm-up, ~200 bars)
        const recentCandles = await prisma.marketCandle.findMany({
          where: { symbol },
          orderBy: { openTimeMs: "desc" },
          take: 200,
        });

        if (recentCandles.length < 2) continue; // not enough data

        // Convert to Candle format and reverse to ascending order
        const candles = recentCandles
          .reverse()
          .map((mc) => ({
            openTime: Number(mc.openTimeMs),
            open: mc.open.toNumber(),
            high: mc.high.toNumber(),
            low: mc.low.toNumber(),
            close: mc.close.toNumber(),
            volume: mc.volume.toNumber(),
          }));

        // Get current position
        const position = await getActivePosition(run.id, symbol);

        if (!position) {
          // --- No position: evaluate entry ---
          const currentPrice = candles[candles.length - 1].close;
          const lastCloseTime = lastTradeCloseTimes.get(run.id) ?? 0;
          const sizing = computeSizing({
            dslJson,
            currentPrice,
            hasOpenPosition: false,
            lastTradeCloseTime: lastCloseTime,
            now: Date.now(),
          });

          if (!sizing.eligible) {
            workerLog.debug({ runId: run.id, reason: sizing.reason }, "entry not eligible");
            continue;
          }

          // Stage 3 (#129): normalize sizing through instrument rules
          let exchangeQty = sizing.qty;
          try {
            const instrument = await getInstrument(symbol);
            const sized = sizeOrder(
              { notionalUsd: sizing.notionalUsd, currentPrice, leverage: 1 },
              instrument,
            );
            if (!sized.valid) {
              workerLog.warn(
                { runId: run.id, reason: sized.reason },
                "sizing produces invalid exchange qty, skipping entry",
              );
              continue;
            }
            exchangeQty = sized.qty;
          } catch (instrErr) {
            workerLog.warn({ err: instrErr, runId: run.id }, "instrument lookup failed, using raw sizing");
          }

          const signal = evaluateEntry({
            candles,
            dslJson,
            position: null,
          });

          if (signal) {
            const intentId = `entry_${signal.triggerTime}_${signal.side}`;

            // DCA-aware entry (#132): if DCA config present, use base order sizing
            // and attach initial DCA state to intent metaJson
            const dcaConfig = extractDcaConfig(dslJson);
            let intentMeta: Record<string, unknown> = {
              signalType: signal.signalType,
              reason: signal.reason,
              slPrice: signal.slPrice,
              tpPrice: signal.tpPrice,
              rawSizingQty: sizing.qty,
              exchangeQty,
              notionalUsd: sizing.notionalUsd,
            };

            if (dcaConfig) {
              // Override qty with DCA base order sizing
              const dcaBaseQty = dcaConfig.baseOrderSizeUsd / currentPrice;
              try {
                const instrument = await getInstrument(symbol);
                const dcaSized = sizeOrder(
                  { notionalUsd: dcaConfig.baseOrderSizeUsd, currentPrice, leverage: 1 },
                  instrument,
                );
                if (dcaSized.valid) {
                  exchangeQty = dcaSized.qty;
                } else {
                  exchangeQty = dcaBaseQty;
                }
              } catch {
                exchangeQty = dcaBaseQty;
              }

              const dcaSide = signal.side === "long" ? "long" as const : "short" as const;
              const stopLossPct = extractSlPct(dslJson);
              const ladder = initializeDcaLadder(dcaConfig, dcaSide, stopLossPct);

              intentMeta = {
                ...intentMeta,
                dca: true,
                dcaBaseOrder: true,
                exchangeQty,
                notionalUsd: dcaConfig.baseOrderSizeUsd,
                dcaState: ladder.serialized,
              };

              workerLog.info(
                { runId: run.id, side: dcaSide, baseUsd: dcaConfig.baseOrderSizeUsd, maxSOs: dcaConfig.maxSafetyOrders },
                "DCA entry: creating base order intent",
              );
            }

            const orderLinkId = `lab_${run.id.slice(0, 8)}_${Date.now()}`;
            try {
              await prisma.botIntent.create({
                data: {
                  botRunId: run.id,
                  intentId,
                  orderLinkId,
                  side: signal.side === "long" ? "BUY" : "SELL",
                  qty: exchangeQty,
                  price: signal.price,
                  type: "ENTRY",
                  state: "PENDING",
                  metaJson: intentMeta as Prisma.InputJsonValue,
                },
              });
            } catch (createErr) {
              if ((createErr as { code?: string }).code === "P2002") continue; // duplicate intent
              throw createErr;
            }

            // Initialize trailing stop state for new position
            trailingStopStates.set(run.id, createTrailingStopState(signal.price));

            await prisma.botEvent.create({
              data: {
                botRunId: run.id,
                type: "signal_entry",
                payloadJson: {
                  intentId,
                  side: signal.side,
                  price: signal.price,
                  slPrice: signal.slPrice,
                  tpPrice: signal.tpPrice,
                  reason: signal.reason,
                  at: new Date().toISOString(),
                } as Prisma.InputJsonValue,
              },
            });

            workerLog.info(
              { runId: run.id, intentId, side: signal.side, price: signal.price },
              "entry signal → intent created",
            );
          }
        } else {
          // --- In position ---

          // DCA SO trigger evaluation (#132 slice 3): check if current price
          // triggers any pending safety orders and create ENTRY intents for them.
          const currentPrice = candles[candles.length - 1].close;
          const dcaConfig = extractDcaConfig(dslJson);
          if (dcaConfig) {
            try {
              const posRow = await prisma.position.findUnique({
                where: { id: position.id },
                select: { metaJson: true },
              });
              const dcaState = recoverDcaState(posRow?.metaJson);
              if (dcaState && dcaState.phase === "ladder_active" && dcaState.nextSoIndex >= 0) {
                const triggered = checkAndTriggerSOs(dcaState, currentPrice);
                for (const so of triggered) {
                  const soIntentId = `entry_so${so.index}_${run.id.slice(0, 8)}_${position.id.slice(0, 8)}`;
                  const soSide = dcaState.side === "long" ? "BUY" as const : "SELL" as const;
                  const orderLinkId = `lab_${run.id.slice(0, 8)}_so${so.index}_${Date.now()}`;

                  try {
                    await prisma.botIntent.create({
                      data: {
                        botRunId: run.id,
                        intentId: soIntentId,
                        orderLinkId,
                        side: soSide,
                        qty: so.qty,
                        price: so.triggerPrice,
                        type: "ENTRY",
                        state: "PENDING",
                        metaJson: {
                          dca: true,
                          dcaSafetyOrder: true,
                          soIndex: so.index,
                          triggerPrice: so.triggerPrice,
                          positionId: position.id,
                          slPrice: dcaState.slPrice,
                          tpPrice: dcaState.tpPrice,
                        } as Prisma.InputJsonValue,
                      },
                    });
                  } catch (createErr) {
                    if ((createErr as { code?: string }).code === "P2002") continue; // duplicate SO intent
                    throw createErr;
                  }

                  workerLog.info(
                    {
                      runId: run.id,
                      soIndex: so.index,
                      triggerPrice: so.triggerPrice,
                      qty: so.qty,
                      intentId: soIntentId,
                    },
                    "DCA SO triggered → intent created",
                  );
                }
              }
            } catch (dcaErr) {
              workerLog.warn({ err: dcaErr, runId: run.id }, "DCA SO trigger evaluation error (non-fatal)");
            }
          }

          // --- Evaluate exit ---
          const trailingState = trailingStopStates.get(run.id)
            ?? createTrailingStopState(position.avgEntryPrice);
          trailingStopStates.set(run.id, trailingState);

          // Estimate bars held: count candles since position open
          const openTimeMs = position.openedAt.getTime();
          const barsHeld = candles.filter((c) => c.openTime > openTimeMs).length;

          const closeSignal = evaluateExit({
            candles,
            dslJson,
            position,
            barsHeld,
            trailingState,
          });

          if (closeSignal) {
            const intentId = `exit_${closeSignal.triggerTime}_${closeSignal.reason}`;
            const closeSide = closeSignal.side === "long" ? "SELL" : "BUY";
            const orderLinkId = `lab_${run.id.slice(0, 8)}_${Date.now()}`;

            try {
              await prisma.botIntent.create({
                data: {
                  botRunId: run.id,
                  intentId,
                  orderLinkId,
                  side: closeSide,
                  qty: position.currentQty,
                  price: closeSignal.price,
                  type: "EXIT",
                  state: "PENDING",
                  metaJson: {
                    reason: closeSignal.reason,
                    description: closeSignal.description,
                    positionId: position.id,
                    positionSide: position.side,
                    avgEntryPrice: position.avgEntryPrice,
                  } as Prisma.InputJsonValue,
                },
              });
            } catch (createErr) {
              if ((createErr as { code?: string }).code === "P2002") continue; // duplicate exit intent
              throw createErr;
            }

            // Record last trade close time for cooldown
            lastTradeCloseTimes.set(run.id, Date.now());

            // Clean up trailing stop state
            trailingStopStates.delete(run.id);

            await prisma.botEvent.create({
              data: {
                botRunId: run.id,
                type: "signal_exit",
                payloadJson: {
                  intentId,
                  reason: closeSignal.reason,
                  description: closeSignal.description,
                  price: closeSignal.price,
                  positionId: position.id,
                  at: new Date().toISOString(),
                } as Prisma.InputJsonValue,
              },
            });

            workerLog.info(
              { runId: run.id, intentId, reason: closeSignal.reason, price: closeSignal.price },
              "exit signal → intent created",
            );
          }
        }
      } catch (err) {
        workerLog.error({ err, runId: run.id }, "evaluateStrategies: run evaluation error");
      }
    }
  } catch (err) {
    workerLog.error({ err }, "evaluateStrategies error");
  }
}

// ---------------------------------------------------------------------------
// Stage 19c: MarketCandle retention job
// ---------------------------------------------------------------------------

/**
 * Delete MarketCandle rows older than RETENTION_DAYS.
 * Deletion is by candle open time (openTimeMs), not row creation time.
 * MarketCandle is workspace-shared — no workspace filter needed.
 * Errors are caught and logged; they must not crash the worker.
 */
async function runMarketCandleRetention(): Promise<void> {
  lastRetentionRunMs = Date.now();
  try {
    const cutoffMs = Date.now() - RETENTION_DAYS * 24 * 60 * 60 * 1000;
    const result = await prisma.marketCandle.deleteMany({
      where: { openTimeMs: { lt: BigInt(cutoffMs) } },
    });
    workerLog.info(
      { deleted: result.count, retentionDays: RETENTION_DAYS },
      "marketCandle retention complete",
    );
  } catch (err) {
    workerLog.error({ err }, "marketCandle retention error");
  }
}

// ---------------------------------------------------------------------------
// Main polling loop
// ---------------------------------------------------------------------------

let isShuttingDown = false;
let pollInFlight: Promise<void> | null = null;

/** Run a named poll step, catching and logging errors so subsequent steps still execute. */
async function safeStep(name: string, fn: () => Promise<void>) {
  if (isShuttingDown) return;
  try {
    await fn();
  } catch (err) {
    workerLog.error({ err, step: name }, `poll step "${name}" failed (non-fatal)`);
  }
}

/** Main polling loop. */
async function poll() {
  await safeStep("activateRuns", async () => {
    const queued = await prisma.botRun.findMany({
      where: { state: "QUEUED" },
      take: 5,
      orderBy: { createdAt: "asc" },
      select: { id: true },
    });
    for (const { id } of queued) {
      await activateRun(id);
    }
  });

  await safeStep("stopRuns", async () => {
    const stopping = await prisma.botRun.findMany({
      where: { state: "STOPPING" },
      take: 10,
      select: { id: true },
    });
    for (const { id } of stopping) {
      await stopRun(id);
    }
  });

  await safeStep("timeoutExpiredRuns", () => timeoutExpiredRuns());
  await safeStep("renewLeases", () => renewLeases());

  // Stage 8 (#141): enforce safety circuit breakers before evaluation
  await safeStep("enforceDailyLossLimit", () => enforceDailyLossLimit());
  await safeStep("enforceErrorPause", () => enforceErrorPause());

  // Stage 3 (#128): Evaluate DSL strategies for RUNNING runs
  await safeStep("evaluateStrategies", () => evaluateStrategies());

  // Process PENDING intents on RUNNING runs (Stage 11)
  await safeStep("processIntents", () => processIntents());

  // Reconcile PLACED/PARTIALLY_FILLED intents against exchange (Stage 3, #129 follow-up)
  await safeStep("reconcilePlacedIntents", () => reconcilePlacedIntents());

  // Stage 19c: run retention at most once per hour
  if (Date.now() - lastRetentionRunMs >= RETENTION_INTERVAL_MS) {
    await safeStep("marketCandleRetention", () => runMarketCandleRetention());
  }

  // Mark poll completion for health checks (Task #18)
  lastPollTimestampMs = Date.now();
}

/**
 * Start the background worker.
 * Returns an async cleanup function that:
 *   1. Stops the interval timer (no new polls)
 *   2. Waits for the in-flight poll to finish (up to GRACE_PERIOD_MS)
 */
const GRACE_PERIOD_MS = 30_000;

// Test-only exports — prefixed with underscore to signal internal use
export { activateRun as _activateRun };
export { timeoutExpiredRuns as _timeoutExpiredRuns };
export { stopRun as _stopRun };

export function startBotWorker(): () => Promise<void> {
  workerLog.info({ workerId: WORKER_ID, interval: POLL_INTERVAL_MS }, "botWorker started");

  async function wrappedPoll() {
    pollInFlight = poll();
    await pollInFlight;
    pollInFlight = null;
  }

  const timer = setInterval(wrappedPoll, POLL_INTERVAL_MS);
  // Run poll once immediately
  wrappedPoll();
  // Run retention once immediately so the log line appears without waiting an hour
  runMarketCandleRetention();

  return async () => {
    isShuttingDown = true;
    clearInterval(timer);
    workerLog.info("botWorker shutting down, waiting for in-flight poll…");

    if (pollInFlight) {
      const timeout = new Promise<void>((resolve) => setTimeout(resolve, GRACE_PERIOD_MS));
      await Promise.race([pollInFlight, timeout]);
    }

    workerLog.info("botWorker stopped");
  };
}
