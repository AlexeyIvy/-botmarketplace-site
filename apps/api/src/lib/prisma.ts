import { PrismaClient } from "@prisma/client";
import { logger } from "./logger.js";

const prismaLog = logger.child({ module: "prisma" });

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient };

export const prisma = globalForPrisma.prisma || new PrismaClient();

if (process.env.NODE_ENV !== "production") {
  globalForPrisma.prisma = prisma;
}

// ---------------------------------------------------------------------------
// Pool metrics (Rec C — Roadmap V3)
// ---------------------------------------------------------------------------

export interface PoolMetrics {
  activeConnections: number;
  idleConnections: number;
  waitCount: number;
  available: boolean;
}

/**
 * Fetch Prisma connection pool metrics.
 * Returns null if metrics are unavailable (e.g., preview feature not enabled).
 */
export async function getPoolMetrics(): Promise<PoolMetrics | null> {
  try {
    const metrics = await prisma.$metrics.json();

    const find = (name: string) =>
      metrics.gauges.find((g: { key: string; value: number }) => g.key === name)?.value ?? 0;

    return {
      activeConnections: find("prisma_pool_connections_busy"),
      idleConnections: find("prisma_pool_connections_idle"),
      waitCount: find("prisma_pool_wait_count"),
      available: true,
    };
  } catch {
    return null;
  }
}

// Periodic pool metrics logging (every 60s in production)
const POOL_LOG_INTERVAL_MS = 60_000;
let poolLogTimer: ReturnType<typeof setInterval> | null = null;

export function startPoolMetricsLogging(): void {
  if (poolLogTimer) return;
  poolLogTimer = setInterval(async () => {
    const metrics = await getPoolMetrics();
    if (metrics) {
      prismaLog.info(
        {
          active: metrics.activeConnections,
          idle: metrics.idleConnections,
          waiting: metrics.waitCount,
        },
        "pool metrics",
      );
    }
  }, POOL_LOG_INTERVAL_MS);

  // Don't prevent process exit
  if (poolLogTimer.unref) poolLogTimer.unref();
}

export function stopPoolMetricsLogging(): void {
  if (poolLogTimer) {
    clearInterval(poolLogTimer);
    poolLogTimer = null;
  }
}
