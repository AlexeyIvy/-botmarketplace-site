import type { FastifyInstance } from "fastify";
import { register } from "../lib/metrics.js";

/**
 * Prometheus scrape endpoint. Intentionally unauthenticated — Prometheus
 * scrapes it over the loopback interface only (see deploy/nginx.conf).
 */
export async function metricsRoutes(app: FastifyInstance) {
  app.get("/metrics", { config: { rateLimit: false } }, async (_request, reply) => {
    const body = await register.metrics();
    return reply
      .header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
      .send(body);
  });
}
