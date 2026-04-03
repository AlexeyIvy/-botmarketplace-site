import { randomUUID } from "node:crypto";
import Fastify from "fastify";
import cors from "@fastify/cors";
import jwt from "@fastify/jwt";
import rateLimit from "@fastify/rate-limit";
import { healthzRoutes } from "./routes/healthz.js";
import { readyzRoutes } from "./routes/readyz.js";
import { authRoutes } from "./routes/auth.js";
import { strategyRoutes } from "./routes/strategies.js";
import { botRoutes } from "./routes/bots.js";
import { runRoutes } from "./routes/runs.js";
import { intentRoutes } from "./routes/intents.js";
import { workspacesRoutes } from "./routes/workspaces.js";
import { labRoutes } from "./routes/lab.js";
import { datasetRoutes } from "./routes/datasets.js";
import { exchangeRoutes } from "./routes/exchanges.js";
import { terminalRoutes } from "./routes/terminal.js";
import { aiRoutes } from "./routes/ai.js";
import { preferencesRoutes } from "./routes/preferences.js";
import { usersRoutes } from "./routes/users.js";
import { demoRoutes } from "./routes/demo.js";

/** Wrap a route plugin with a per-route rate-limit override. */
function withRateLimit(
  plugin: import("fastify").FastifyPluginAsync,
  max: number,
  timeWindow: string,
): import("fastify").FastifyPluginAsync {
  return async function rateLimitedPlugin(scope) {
    scope.addHook("onRoute", (routeOptions) => {
      routeOptions.config = {
        ...(routeOptions.config as Record<string, unknown> | undefined),
        rateLimit: { max, timeWindow },
      };
    });
    await scope.register(plugin);
  };
}

/** Registers all domain routes. */
async function registerRoutes(scope: import("fastify").FastifyInstance) {
  await scope.register(healthzRoutes);
  await scope.register(readyzRoutes);
  await scope.register(authRoutes);
  await scope.register(workspacesRoutes);
  await scope.register(strategyRoutes);
  await scope.register(botRoutes);
  await scope.register(runRoutes);
  await scope.register(intentRoutes);
  await scope.register(withRateLimit(labRoutes, 10, "1 minute"));   // /lab/backtest*: 10 req/min
  await scope.register(datasetRoutes);
  await scope.register(exchangeRoutes);
  await scope.register(withRateLimit(terminalRoutes, 30, "1 minute")); // /terminal/*: 30 req/min
  await scope.register(aiRoutes);
  await scope.register(preferencesRoutes);
  await scope.register(usersRoutes);
  await scope.register(demoRoutes);
}

export async function buildApp() {
  const app = Fastify({
    logger: {
      transport:
        process.env.NODE_ENV !== "production"
          ? { target: "pino-pretty" }
          : undefined,
    },
    genReqId: (req) =>
      (req.headers["x-request-id"] as string) || randomUUID(),
  });

  await app.register(cors, { origin: true });

  // Global rate limit — 100 req/min baseline; lab & terminal routes override below
  await app.register(rateLimit, {
    global: true,
    max: 100,
    timeWindow: "1 minute",
    errorResponseBuilder: (_req, context) => ({
      type: "about:blank",
      title: "Too Many Requests",
      status: 429,
      detail: `Rate limit exceeded. Try again in ${Math.ceil(context.ttl / 1000)}s`,
    }),
  });

  // JWT plugin — secret from env or a fallback for dev
  const jwtSecret = process.env.JWT_SECRET ?? "dev-secret-change-in-production-please";
  await app.register(jwt, { secret: jwtSecret });

  // Authenticate decorator used by protected routes
  app.decorate("authenticate", async function (request: import("fastify").FastifyRequest, reply: import("fastify").FastifyReply) {
    try {
      await request.jwtVerify();
    } catch {
      return reply.status(401).send({
        type: "about:blank",
        title: "Unauthorized",
        status: 401,
        detail: "Valid Bearer token required",
      });
    }
  });

  // Echo X-Request-Id back to caller
  app.addHook("onSend", async (request, reply) => {
    reply.header("X-Request-Id", request.id);
  });

  // Global catch-all for unhandled errors
  app.setErrorHandler((error: Error & { statusCode?: number; status?: number }, request, reply) => {
    const statusCode = error.statusCode ?? error.status ?? 500;
    if (statusCode < 500) {
      // Non-server errors (validation, rate-limit, etc.) — pass through as-is
      void reply.status(statusCode).send(error);
      return;
    }
    request.log.error({ err: error, reqId: request.id }, "Unhandled error");
    void reply.status(500).send({
      type: "about:blank",
      title: "Internal Server Error",
      status: 500,
      detail:
        process.env.NODE_ENV === "production"
          ? "An unexpected error occurred"
          : error.message,
    });
  });

  // Primary versioned routes: /api/v1/*
  await app.register(registerRoutes, { prefix: "/api/v1" });

  // Legacy aliases: /api/* (backward-compatible, will be removed in v2)
  await app.register(registerRoutes, { prefix: "/api" });

  return app;
}
