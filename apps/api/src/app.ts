import Fastify from "fastify";
import cors from "@fastify/cors";
import { healthzRoutes } from "./routes/healthz.js";
import { readyzRoutes } from "./routes/readyz.js";
import { authRoutes } from "./routes/auth.js";
import { strategyRoutes } from "./routes/strategies.js";
import { botRoutes } from "./routes/bots.js";
import { runRoutes } from "./routes/runs.js";

/** Registers all domain routes. */
async function registerRoutes(scope: import("fastify").FastifyInstance) {
  await scope.register(healthzRoutes);
  await scope.register(readyzRoutes);
  await scope.register(authRoutes);
  await scope.register(strategyRoutes);
  await scope.register(botRoutes);
  await scope.register(runRoutes);
}

export async function buildApp() {
  const app = Fastify({
    logger: {
      transport:
        process.env.NODE_ENV !== "production"
          ? { target: "pino-pretty" }
          : undefined,
    },
  });

  await app.register(cors, { origin: true });

  // Primary versioned routes: /api/v1/*
  await app.register(registerRoutes, { prefix: "/api/v1" });

  // Legacy aliases: /api/* (backward-compatible, will be removed in v2)
  await app.register(registerRoutes, { prefix: "/api" });

  return app;
}
