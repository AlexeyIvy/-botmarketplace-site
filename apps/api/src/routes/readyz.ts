import type { FastifyInstance } from "fastify";
import { prisma } from "../lib/prisma.js";

export async function readyzRoutes(app: FastifyInstance) {
  app.get("/readyz", async (_request, reply) => {
    try {
      await prisma.$queryRaw`SELECT 1`;
      return reply.send({ status: "ok" });
    } catch {
      return reply.status(503).send({
        type: "about:blank",
        title: "Service Unavailable",
        status: 503,
        detail: "Database connection failed",
      });
    }
  });
}
