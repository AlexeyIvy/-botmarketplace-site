/**
 * Tick Processor — DSL enforcement and safety circuit breakers
 * Extracted from botWorker.ts (#230)
 *
 * Handles:
 * - enforceDailyLossLimit: stops runs that exceed daily loss budget
 * - enforceErrorPause: stops runs with consecutive failed intents
 * - processIntents: dispatches PENDING intents to the executor
 */

import { Prisma } from "@prisma/client";
import { prisma } from "../prisma.js";
import { transition } from "../stateMachine.js";
import {
  parseDailyLossConfig,
  parseGuardsConfig,
  shouldTriggerDailyLossLimit,
  shouldPauseOnError,
  DEFAULT_ERROR_PAUSE_THRESHOLD,
} from "../safetyGuards.js";
import { notifyRunEvent } from "../notify.js";
import { executeIntent, type IntentRecord } from "./intentExecutor.js";
import type { Logger } from "pino";

// ---------------------------------------------------------------------------
// Daily loss limit enforcement
// ---------------------------------------------------------------------------

export async function enforceDailyLossLimit(workerLog: Logger): Promise<void> {
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
      const runLog = workerLog.child({ runId: run.id, symbol: run.symbol, workspaceId: run.workspaceId });
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
        runLog.info(
          { estimatedLoss: result.estimatedLoss, dailyLossLimitUsd: config.dailyLossLimitUsd },
          "daily loss limit exceeded, stopping run",
        );
        notifyRunEvent(run.workspaceId, {
          eventType: "RUN_STOPPING",
          runId: run.id,
          symbol: run.symbol,
          message: `Daily loss limit breached: ${result.reason}`,
        });
      } catch (err) {
        runLog.error({ err }, "enforceDailyLossLimit transition error");
      }
    }
  } catch (err) {
    workerLog.error({ err }, "enforceDailyLossLimit error");
  }
}

// ---------------------------------------------------------------------------
// Error pause enforcement
// ---------------------------------------------------------------------------

export async function enforceErrorPause(workerLog: Logger): Promise<void> {
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
      const runLog = workerLog.child({ runId: run.id, symbol: run.symbol, workspaceId: run.workspaceId });
      const guards = parseGuardsConfig(run.bot?.strategyVersion?.dslJson);
      if (!guards.pauseOnError) continue;

      const recentIntents = await prisma.botIntent.findMany({
        where: { botRunId: run.id },
        orderBy: { createdAt: "desc" },
        take: DEFAULT_ERROR_PAUSE_THRESHOLD,
        select: { state: true },
      });

      if (recentIntents.length < DEFAULT_ERROR_PAUSE_THRESHOLD) continue;

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
        runLog.info(
          { consecutiveFailed, threshold: result.threshold },
          "pauseOnError triggered, stopping run",
        );
        notifyRunEvent(run.workspaceId, {
          eventType: "RUN_STOPPING",
          runId: run.id,
          symbol: run.symbol,
          message: `Circuit breaker: ${consecutiveFailed} consecutive failed intents`,
        });
      } catch (err) {
        runLog.error({ err }, "enforceErrorPause transition error");
      }
    }
  } catch (err) {
    workerLog.error({ err }, "enforceErrorPause error");
  }
}

// ---------------------------------------------------------------------------
// Process PENDING intents
// ---------------------------------------------------------------------------

export async function processIntents(workerLog: Logger): Promise<void> {
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
                  select: {
                    apiKey: true,
                    encryptedSecret: true,
                    // docs/55-T5: optional spot scope keys consumed by
                    // executeIntent for spot-category intents (funding-arb).
                    // Null when the operator hasn't configured a dedicated
                    // spot key — executor falls back to the linear pair.
                    spotApiKey: true,
                    spotEncryptedSecret: true,
                  },
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
        workerLog.info({ intentId: intent.intentId, runId: intent.botRun.id, symbol: intent.botRun.bot.symbol }, "intent cancelled — strategy disabled");
        continue;
      }

      await executeIntent(intent as IntentRecord, workerLog);
    }
  } catch (err) {
    workerLog.error({ err }, "processIntents error");
  }
}
