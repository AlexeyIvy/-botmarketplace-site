import { initSentry } from "./lib/sentry.js";
initSentry(); // Must run before any other imports that emit errors

import { buildApp } from "./app.js";
import { startBotWorker } from "./lib/botWorker.js";
import cron from "node-cron";
import { runIngestion } from "./lib/funding/ingestJob.js";
import { prisma, startPoolMetricsLogging, stopPoolMetricsLogging } from "./lib/prisma.js";
import { startPeriodicReconciler } from "./lib/periodicReconciler.js";
import { validateBybitEnv } from "./lib/bybitEnv.js";
import { logger } from "./lib/logger.js";
import { cleanupExpiredRefreshTokens } from "./routes/auth.js";

const PORT = parseInt(process.env.API_PORT || "4000", 10);
const HOST = process.env.API_HOST || "0.0.0.0";

/** Fail fast if required env vars are missing. */
function validateEnv() {
  const required = ["DATABASE_URL", "JWT_SECRET"];
  const requiredInProd = ["SECRET_ENCRYPTION_KEY"];
  const missing = required.filter((k) => !process.env[k]);
  if (process.env.NODE_ENV === "production") {
    missing.push(...requiredInProd.filter((k) => !process.env[k]));
  }
  if (missing.length > 0) {
    throw new Error(`Missing required env vars: ${missing.join(", ")}`);
  }
}

async function main() {
  validateEnv();
  validateBybitEnv();
  const app = await buildApp();

  try {
    await app.listen({ port: PORT, host: HOST });
    app.log.info(`API server listening on http://${HOST}:${PORT}`);

    // Start bot worker background loop (skip if running as separate process — Task #21)
    const embeddedWorker = !process.env.DISABLE_EMBEDDED_WORKER;
    const stopWorker = embeddedWorker ? startBotWorker() : null;
    if (!embeddedWorker) {
      app.log.info("Embedded worker disabled (DISABLE_EMBEDDED_WORKER set). Use standalone worker process.");
    }

    // Start pool metrics logging (Rec C)
    startPoolMetricsLogging();

    // Periodic reconciler — safety net if the worker tick gets wedged (§4.5.2)
    const stopReconciler = embeddedWorker ? startPeriodicReconciler() : null;

    // Funding ingestion cron — every 8 hours (matches Bybit settlement schedule)
    const fundingCron = cron.schedule("0 */8 * * *", () => {
      logger.info("Funding cron triggered");
      runIngestion(prisma);
    });

    // Refresh token cleanup cron — daily at 03:00
    const tokenCleanupCron = cron.schedule("0 3 * * *", async () => {
      try {
        const deleted = await cleanupExpiredRefreshTokens();
        logger.info({ deleted }, "Refresh token cleanup completed");
      } catch (err) {
        logger.error({ err }, "Refresh token cleanup failed");
      }
    });

    // Graceful shutdown — wait for in-flight poll before disconnecting
    const SHUTDOWN_TIMEOUT_MS = 30_000;
    let isShuttingDown = false;

    for (const signal of ["SIGINT", "SIGTERM"]) {
      process.once(signal, async () => {
        if (isShuttingDown) {
          logger.warn("Duplicate shutdown signal received — ignoring");
          return;
        }
        isShuttingDown = true;
        logger.info({ signal }, "Graceful shutdown initiated");

        const forceTimer = setTimeout(() => {
          logger.error("Graceful shutdown timeout — forcing exit");
          process.exit(1);
        }, SHUTDOWN_TIMEOUT_MS);
        forceTimer.unref();

        fundingCron.stop();
        tokenCleanupCron.stop();
        stopPoolMetricsLogging();
        if (stopReconciler) stopReconciler();
        if (stopWorker) await stopWorker();
        await app.close();
        await prisma.$disconnect();
        process.exit(0);
      });
    }
  } catch (err) {
    app.log.error(err);
    process.exit(1);
  }
}

main();
