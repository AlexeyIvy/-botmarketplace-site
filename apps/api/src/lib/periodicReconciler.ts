/**
 * Periodic reconciliation (§4.5.2 / docs/37).
 *
 * The in-poll reconcile loop in botWorker.ts handles PLACED intents against
 * the exchange, but only when the worker tick is alive. If the worker gets
 * wedged (stuck HTTP call, unhandled rejection blocking the event loop,
 * Prisma pool exhaustion…), PENDING intents accumulate indefinitely with
 * nobody to place them.
 *
 * This module is a safety net that runs independently from the poll loop.
 * Every STALE_PENDING_INTERVAL_MS it cancels PENDING intents belonging to
 * RUNNING runs that were created more than STALE_PENDING_MIN_AGE_MS ago —
 * on a healthy worker, PENDING → PLACED happens within one poll cycle
 * (~4s), so a PENDING older than the threshold is definitely stuck.
 */

import { Prisma } from "@prisma/client";
import { prisma } from "./prisma.js";
import { logger } from "./logger.js";
import { stalePendingCancelledTotal } from "./metrics.js";

const reconcilerLog = logger.child({ module: "periodicReconciler" });

/** PENDING intents older than this are considered stuck and get cancelled. */
export const STALE_PENDING_MIN_AGE_MS = parseInt(
  process.env.STALE_PENDING_MIN_AGE_MS ?? "",
  10,
) || 10 * 60_000;

/** How often the periodic sweep runs. */
export const STALE_PENDING_INTERVAL_MS = parseInt(
  process.env.STALE_PENDING_INTERVAL_MS ?? "",
  10,
) || 5 * 60_000;

/**
 * Find and cancel PENDING intents attached to RUNNING runs that are older
 * than STALE_PENDING_MIN_AGE_MS. Returns the number of intents cancelled.
 *
 * Emits a `periodic_reconciliation` BotEvent for each affected run so the
 * action is visible in the run's event log.
 */
export async function sweepStalePendingIntents(): Promise<number> {
  const cutoff = new Date(Date.now() - STALE_PENDING_MIN_AGE_MS);

  const stale = await prisma.botIntent.findMany({
    where: {
      state: "PENDING",
      createdAt: { lt: cutoff },
      botRun: { state: "RUNNING" },
    },
    select: { id: true, intentId: true, botRunId: true, createdAt: true },
    take: 500,
  });

  if (stale.length === 0) return 0;

  const ids = stale.map((i) => i.id);
  const updated = await prisma.botIntent.updateMany({
    where: { id: { in: ids }, state: "PENDING" },
    data: {
      state: "CANCELLED",
      metaJson: {
        reason: "periodic_reconciliation_stale_pending",
        cancelledAt: new Date().toISOString(),
        minAgeMs: STALE_PENDING_MIN_AGE_MS,
      } as Prisma.InputJsonValue,
    },
  });

  // Group by run for event log
  const byRun = new Map<string, typeof stale>();
  for (const i of stale) {
    const arr = byRun.get(i.botRunId) ?? [];
    arr.push(i);
    byRun.set(i.botRunId, arr);
  }

  for (const [botRunId, intents] of byRun) {
    await prisma.botEvent.create({
      data: {
        botRunId,
        type: "periodic_reconciliation",
        payloadJson: {
          action: "cancel_stale_pending",
          cancelledCount: intents.length,
          cancelledIntentIds: intents.map((i) => i.intentId),
          oldestAgeMs: Date.now() - Math.min(...intents.map((i) => i.createdAt.getTime())),
          minAgeMs: STALE_PENDING_MIN_AGE_MS,
        } as Prisma.InputJsonValue,
      },
    });
  }

  stalePendingCancelledTotal.inc(updated.count);
  reconcilerLog.warn(
    { cancelled: updated.count, runs: byRun.size, minAgeMs: STALE_PENDING_MIN_AGE_MS },
    "periodic reconciliation: cancelled stale PENDING intents (worker may be wedged)",
  );
  return updated.count;
}

/**
 * Start the periodic reconciliation sweep. Returns a stop function.
 * Safe to call from any process that has DB access (server / worker).
 */
export function startPeriodicReconciler(): () => void {
  const run = () => {
    sweepStalePendingIntents().catch((err) => {
      reconcilerLog.error({ err }, "periodic reconciler error (non-fatal)");
    });
  };
  const timer = setInterval(run, STALE_PENDING_INTERVAL_MS);
  if (timer.unref) timer.unref();
  reconcilerLog.info(
    { intervalMs: STALE_PENDING_INTERVAL_MS, minAgeMs: STALE_PENDING_MIN_AGE_MS },
    "periodic reconciler started",
  );
  return () => {
    clearInterval(timer);
    reconcilerLog.info("periodic reconciler stopped");
  };
}
