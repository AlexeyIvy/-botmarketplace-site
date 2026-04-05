import { buildApp } from "./app.js";
import { startBotWorker } from "./lib/botWorker.js";
import cron from "node-cron";
import { runIngestion } from "./lib/funding/ingestJob.js";
import { prisma } from "./lib/prisma.js";
import { logger } from "./lib/logger.js";

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
  const app = await buildApp();

  try {
    await app.listen({ port: PORT, host: HOST });
    app.log.info(`API server listening on http://${HOST}:${PORT}`);

    // Start bot worker background loop
    const stopWorker = startBotWorker();

    // Funding ingestion cron — every 8 hours (matches Bybit settlement schedule)
    const fundingCron = cron.schedule("0 */8 * * *", () => {
      logger.info("Funding cron triggered");
      runIngestion(prisma);
    });

    // Graceful shutdown
    for (const signal of ["SIGINT", "SIGTERM"]) {
      process.once(signal, async () => {
        fundingCron.stop();
        stopWorker();
        await prisma.$disconnect();
        await app.close();
        process.exit(0);
      });
    }
  } catch (err) {
    app.log.error(err);
    process.exit(1);
  }
}

main();
