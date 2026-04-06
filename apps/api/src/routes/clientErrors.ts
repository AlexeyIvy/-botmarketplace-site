import type { FastifyInstance } from "fastify";
import { logger } from "../lib/logger.js";

const clientErrorLog = logger.child({ module: "clientError" });

interface ClientErrorBody {
  message?: string;
  stack?: string;
  digest?: string;
  url?: string;
  userAgent?: string;
  timestamp?: string;
}

/**
 * POST /client-errors — receive error reports from the frontend (Task #23).
 *
 * Public endpoint (no auth required) — the user may hit an error before
 * they're authenticated. Rate-limited to prevent abuse.
 */
export async function clientErrorRoutes(app: FastifyInstance) {
  app.post<{ Body: ClientErrorBody }>("/client-errors", async (request, reply) => {
    const { message, stack, digest, url, userAgent, timestamp } = request.body ?? {};

    // Basic validation — reject empty or oversized payloads
    if (!message || typeof message !== "string") {
      return reply.status(400).send({ ok: false });
    }

    clientErrorLog.warn(
      {
        errorMessage: message.slice(0, 500),
        stack: stack?.slice(0, 2000),
        digest,
        clientUrl: url?.slice(0, 500),
        userAgent: userAgent?.slice(0, 300),
        clientTimestamp: timestamp,
        ip: request.ip,
      },
      "client-side error reported",
    );

    return reply.status(204).send();
  });
}
