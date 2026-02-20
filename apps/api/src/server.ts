import { buildApp } from "./app.js";
import { startBotWorker } from "./lib/botWorker.js";

const PORT = parseInt(process.env.API_PORT || "4000", 10);
const HOST = process.env.API_HOST || "0.0.0.0";

async function main() {
  const app = await buildApp();

  try {
    await app.listen({ port: PORT, host: HOST });
    app.log.info(`API server listening on http://${HOST}:${PORT}`);

    // Start bot worker background loop
    const stopWorker = startBotWorker();

    // Graceful shutdown
    for (const signal of ["SIGINT", "SIGTERM"]) {
      process.once(signal, async () => {
        stopWorker();
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
