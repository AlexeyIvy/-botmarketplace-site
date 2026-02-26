import type { FastifyInstance } from "fastify";

export async function healthzRoutes(app: FastifyInstance) {
  app.get("/healthz", async (_request, reply) => {
    return reply.send({
      status: "ok",
      uptime: process.uptime(),
      timestamp: new Date().toISOString(),
    });
  });
}
