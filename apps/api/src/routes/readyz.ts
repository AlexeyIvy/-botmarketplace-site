import type { FastifyInstance } from "fastify";
import { prisma, getPoolMetrics } from "../lib/prisma.js";
import { lastPollTimestampMs, POLL_INTERVAL_MS } from "../lib/botWorker.js";

/**
 * Worker is considered stale if its last poll completed more than
 * 3× the poll interval ago (default: 12 seconds).
 */
const WORKER_STALENESS_FACTOR = 3;

export async function readyzRoutes(app: FastifyInstance) {
  app.get("/readyz", async (_request, reply) => {
    const checks: Record<string, { ok: boolean; detail?: string }> = {};

    // 1. Database connectivity
    try {
      await prisma.$queryRaw`SELECT 1`;
      checks.database = { ok: true };
    } catch {
      checks.database = { ok: false, detail: "Database connection failed" };
    }

    // 2. Worker health — has poll run recently?
    const now = Date.now();
    const maxStaleMs = POLL_INTERVAL_MS * WORKER_STALENESS_FACTOR;
    const workerExternal = !!process.env.DISABLE_EMBEDDED_WORKER;

    if (workerExternal) {
      // Task #21: Worker runs in separate process — skip in-process health check
      checks.worker = { ok: true, detail: "Worker runs in separate process" };
    } else if (lastPollTimestampMs === 0) {
      // Worker hasn't completed its first poll yet — may still be starting
      checks.worker = { ok: true, detail: "Worker starting (no poll completed yet)" };
    } else {
      const elapsed = now - lastPollTimestampMs;
      if (elapsed < maxStaleMs) {
        checks.worker = { ok: true, detail: `Last poll ${Math.round(elapsed / 1000)}s ago` };
      } else {
        checks.worker = {
          ok: false,
          detail: `Worker stale: last poll ${Math.round(elapsed / 1000)}s ago (threshold: ${Math.round(maxStaleMs / 1000)}s)`,
        };
      }
    }

    // 3. Encryption key availability
    try {
      const raw = process.env.SECRET_ENCRYPTION_KEY;
      if (raw && raw.length === 64) {
        checks.encryptionKey = { ok: true };
      } else if (!raw) {
        checks.encryptionKey = { ok: false, detail: "SECRET_ENCRYPTION_KEY not set" };
      } else {
        checks.encryptionKey = { ok: false, detail: `SECRET_ENCRYPTION_KEY wrong length: ${raw.length}` };
      }
    } catch {
      checks.encryptionKey = { ok: false, detail: "Failed to check encryption key" };
    }

    // 4. Stuck runs — ephemeral states older than 5 min
    try {
      const stuckCount = await prisma.botRun.count({
        where: {
          state: { in: ["STARTING", "SYNCING"] },
          updatedAt: { lt: new Date(now - 5 * 60 * 1000) },
        },
      });
      if (stuckCount === 0) {
        checks.stuckRuns = { ok: true };
      } else {
        checks.stuckRuns = { ok: false, detail: `${stuckCount} run(s) stuck in ephemeral state` };
      }
    } catch {
      checks.stuckRuns = { ok: true, detail: "Could not check (non-critical)" };
    }

    // 5. Connection pool metrics (Rec C)
    try {
      const poolMetrics = await getPoolMetrics();
      if (poolMetrics) {
        checks.connectionPool = {
          ok: poolMetrics.waitCount < 5,
          detail: `active=${poolMetrics.activeConnections} idle=${poolMetrics.idleConnections} waiting=${poolMetrics.waitCount}`,
        };
      } else {
        checks.connectionPool = { ok: true, detail: "Metrics unavailable (non-critical)" };
      }
    } catch {
      checks.connectionPool = { ok: true, detail: "Could not check (non-critical)" };
    }

    // Overall status: database + worker are critical; others are warnings
    const critical = checks.database.ok && checks.worker.ok;
    const allOk = Object.values(checks).every((c) => c.ok);

    const status = critical ? (allOk ? "ok" : "degraded") : "unavailable";
    const httpStatus = critical ? 200 : 503;

    return reply.status(httpStatus).send({ status, checks });
  });
}
