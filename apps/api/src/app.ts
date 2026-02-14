import Fastify from "fastify";
import cors from "@fastify/cors";
import { healthzRoutes } from "./routes/healthz.js";
import { readyzRoutes } from "./routes/readyz.js";
import { authRoutes } from "./routes/auth.js";

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

  // All routes under /api prefix
  await app.register(
    async (api) => {
      await api.register(healthzRoutes);
      await api.register(readyzRoutes);
      await api.register(authRoutes);
    },
    { prefix: "/api" },
  );

  return app;
}
