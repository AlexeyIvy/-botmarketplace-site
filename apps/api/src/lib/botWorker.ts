/**
 * Bot Worker — background loop that advances bot run states.
 *
 * Lifecycle:
 *   QUEUED → STARTING → SYNCING → RUNNING  (worker drives this)
 *   STOPPING → STOPPED                      (worker completes stop)
 *
 * The worker runs independently in the same process. For production,
 * this should be extracted into a dedicated worker process.
 */

import { prisma } from "./prisma.js";
import { transition, isValidTransition } from "./stateMachine.js";

const WORKER_ID = `worker-${process.pid}`;
const POLL_INTERVAL_MS = 4_000;

// Max time a run can stay in RUNNING state before auto-timeout (default: 4 hours)
const MAX_RUN_DURATION_MS = parseInt(process.env.MAX_RUN_DURATION_MS ?? "", 10) || 4 * 60 * 60 * 1000;

async function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

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
  } catch (err) {
    // If another worker won or run was stopped, ignore
    console.error(`[botWorker] activateRun ${runId} error:`, err);
  }
}

/** Advance a STOPPING run to STOPPED. */
async function stopRun(runId: string) {
  try {
    const run = await prisma.botRun.findUnique({ where: { id: runId } });
    if (!run || run.state !== "STOPPING") return;
    await transition(runId, "STOPPED", {
      eventType: "RUN_STOPPED",
      message: "Worker completed stop",
      stoppedAt: new Date(),
    });
  } catch (err) {
    console.error(`[botWorker] stopRun ${runId} error:`, err);
  }
}

/** Mark RUNNING runs that exceeded MAX_RUN_DURATION_MS as TIMED_OUT. */
async function timeoutExpiredRuns() {
  const cutoff = new Date(Date.now() - MAX_RUN_DURATION_MS);
  const expired = await prisma.botRun.findMany({
    where: {
      state: "RUNNING",
      startedAt: { lt: cutoff },
    },
    select: { id: true },
    take: 10,
  });
  for (const { id } of expired) {
    try {
      await transition(id, "TIMED_OUT", {
        eventType: "RUN_TIMED_OUT",
        message: `Run exceeded max duration of ${MAX_RUN_DURATION_MS / 1000}s`,
        errorCode: "MAX_DURATION_EXCEEDED",
      });
      console.log(`[botWorker] run ${id} timed out (exceeded ${MAX_RUN_DURATION_MS}ms)`);
    } catch (err) {
      console.error(`[botWorker] timeoutExpiredRuns ${id} error:`, err);
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
  } catch (err) {
    console.error("[botWorker] poll error:", err);
  }
}

/** Start the background worker. Returns a cleanup function. */
export function startBotWorker(): () => void {
  console.log(`[botWorker] started (id=${WORKER_ID}, interval=${POLL_INTERVAL_MS}ms)`);
  const timer = setInterval(poll, POLL_INTERVAL_MS);
  // Run once immediately
  poll();
  return () => clearInterval(timer);
}
