/**
 * Standalone Bot Worker process entrypoint.
 *
 * Runs the botWorker polling loop in a dedicated Node.js process,
 * isolated from the API server. Communicates via shared database (Prisma).
 *
 * Usage:
 *   node dist/worker.js          (production)
 *   npx tsx src/worker.ts        (development)
 *
 * Roadmap V3, Task #21 — Worker extraction.
 */

import { startBotWorker } from "./lib/botWorker.js";
import { prisma } from "./lib/prisma.js";
import { logger } from "./lib/logger.js";

const workerLog = logger.child({ module: "worker-main" });

/** Fail fast if required env vars are missing. */
function validateEnv() {
  const required = ["DATABASE_URL"];
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
  workerLog.info("Starting standalone bot worker process");

  const stopWorker = startBotWorker();

  // Graceful shutdown
  for (const signal of ["SIGINT", "SIGTERM"] as const) {
    process.once(signal, async () => {
      workerLog.info({ signal }, "Received shutdown signal");
      await stopWorker();
      await prisma.$disconnect();
      workerLog.info("Standalone worker stopped");
      process.exit(0);
    });
  }
}

main().catch((err) => {
  workerLog.error({ err }, "Standalone worker failed to start");
  process.exit(1);
});
