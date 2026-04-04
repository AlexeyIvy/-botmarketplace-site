import { buildApp } from "./app.js";
import { startBotWorker } from "./lib/botWorker.js";
import cron from "node-cron";
import { runIngestion } from "./lib/funding/ingestJob.js";
import { PrismaClient } from "@prisma/client";
import { logger } from "./lib/logger.js";

const PORT = parseInt(process.env.API_PORT || "4000", 10);
const HOST = process.env.API_HOST || "0.0.0.0";

async function main() {
  const app = await buildApp();

  try {
    await app.listen({ port: PORT, host: HOST });
    app.log.info(`API server listening on http://${HOST}:${PORT}`);

    // Start bot worker background loop
    const stopWorker = startBotWorker();

    // Funding ingestion cron — every 8 hours (matches Bybit settlement schedule)
    const prisma = new PrismaClient();
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
