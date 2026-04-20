import { randomUUID } from "node:crypto";
import Fastify from "fastify";
import cors from "@fastify/cors";
import jwt from "@fastify/jwt";
import rateLimit from "@fastify/rate-limit";
import { healthzRoutes } from "./routes/healthz.js";
import { readyzRoutes } from "./routes/readyz.js";
import { metricsRoutes } from "./routes/metrics.js";
import { httpRequestDurationSeconds } from "./lib/metrics.js";
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
import { fundingRoutes } from "./routes/funding.js";
import { hedgeRoutes } from "./routes/hedges.js";
import { notificationRoutes } from "./routes/notifications.js";
import { clientErrorRoutes } from "./routes/clientErrors.js";

/**
 * Wrap a route plugin with a per-route rate-limit override.
 *
 * Uses the `rateLimit()` decorator provided by @fastify/rate-limit
 * instead of the onRoute hook approach (which suffers from hook ordering
 * issues — the global rate-limit plugin's onRoute runs before ours).
 */
function withRateLimit(
  plugin: import("fastify").FastifyPluginAsync,
  max: number,
  timeWindow: string,
): import("fastify").FastifyPluginAsync {
  return async function rateLimitedPlugin(scope) {
    scope.addHook("onRoute", (routeOptions) => {
      // Disable the global rate limit for this route (avoid double-counting)
      routeOptions.config = {
        ...(routeOptions.config as Record<string, unknown> | undefined),
        rateLimit: false,
      };
    });
    // Apply custom rate limit as a scope-level onRequest hook
    scope.addHook("onRequest", scope.rateLimit({ max, timeWindow: timeWindow as never }));
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
  await scope.register(labRoutes);   // backtest routes have per-route rateLimit (5 req/min)
  await scope.register(datasetRoutes);
  await scope.register(exchangeRoutes);
  await scope.register(withRateLimit(terminalRoutes, 30, "1 minute")); // /terminal/*: 30 req/min
  await scope.register(withRateLimit(fundingRoutes, 30, "1 minute"));  // /terminal/funding/*: 30 req/min
  await scope.register(withRateLimit(hedgeRoutes, 30, "1 minute"));   // /hedges/*: 30 req/min
  await scope.register(aiRoutes);
  await scope.register(preferencesRoutes);
  await scope.register(notificationRoutes);
  await scope.register(usersRoutes);
  await scope.register(demoRoutes);
  await scope.register(withRateLimit(clientErrorRoutes, 3, "1 minute")); // 3 req/min
}

export async function buildApp() {
  const app = Fastify({
    logger: {
      transport:
        process.env.NODE_ENV !== "production"
          ? { target: "pino-pretty" }
          : undefined,
    },
    trustProxy: process.env.TRUST_PROXY || "127.0.0.1",
    genReqId: (req) =>
      (req.headers["x-request-id"] as string) || randomUUID(),
  });

  const corsOrigin = process.env.CORS_ORIGIN
    ? process.env.CORS_ORIGIN.split(",")
    : (process.env.NODE_ENV === "production" ? ["https://botmarketplace.store"] : true);

  await app.register(cors, {
    origin: corsOrigin,
    credentials: true,
  });

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

  // JWT plugin — secret from env; dev fallback only in non-production
  const jwtSecret = process.env.JWT_SECRET ?? (
    process.env.NODE_ENV === "production"
      ? (() => { throw new Error("JWT_SECRET must be set in production"); })()
      : "dev-secret-change-in-production-please"
  );
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

  // Security headers (CSP enforcement + hardening)
  app.addHook("onSend", async (request, reply) => {
    reply.header("X-Request-Id", request.id);
    reply.header("X-Content-Type-Options", "nosniff");
    reply.header("X-Frame-Options", "DENY");
    reply.header("Referrer-Policy", "strict-origin-when-cross-origin");
    reply.header(
      "Content-Security-Policy",
      "default-src 'none'; frame-ancestors 'none'",
    );
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

  // Top-level /health for nginx/monitoring (no auth, no prefix)
  app.get("/health", { config: { rateLimit: false } }, async (_request, reply) => {
    return reply.send({
      status: "ok",
      uptime: process.uptime(),
      timestamp: new Date().toISOString(),
    });
  });

  // Prometheus scrape endpoint (no auth, no prefix) — scraped from loopback only
  await app.register(metricsRoutes);

  // HTTP request duration histogram — observe every response
  app.addHook("onResponse", async (request, reply) => {
    const route = request.routeOptions?.url ?? request.url;
    httpRequestDurationSeconds
      .labels(request.method, route, String(reply.statusCode))
      .observe(reply.elapsedTime / 1000);
  });

  // Primary versioned routes: /api/v1/*
  await app.register(registerRoutes, { prefix: "/api/v1" });

  // Legacy aliases: /api/* (backward-compatible, will be removed in v2)
  await app.register(registerRoutes, { prefix: "/api" });

  return app;
}
