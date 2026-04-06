/**
 * Singleton WebSocket manager for the bot worker.
 *
 * Creates and manages BybitPublicWs and BybitPrivateWs instances.
 * Designed to be started when the worker boots and stopped on shutdown.
 *
 * REST fallback remains — WS supplements, REST stays as backup.
 *
 * Roadmap V3, Task #19 — Slice C.
 */

import { BybitPublicWs } from "./publicChannels.js";
import { BybitPrivateWs } from "./privateChannels.js";
import { logger } from "../logger.js";

const mgrLog = logger.child({ module: "ws-manager" });

// ---------------------------------------------------------------------------
// Singleton
// ---------------------------------------------------------------------------

let publicWs: BybitPublicWs | null = null;
let privateInstances: Map<string, BybitPrivateWs> = new Map();

/**
 * Start the public WS connection.
 * Called once when worker boots. Safe to call multiple times (idempotent).
 */
export function startPublicWs(): BybitPublicWs {
  if (publicWs) return publicWs;

  publicWs = new BybitPublicWs();
  publicWs.on("connected", () => mgrLog.info("Public WS connected"));
  publicWs.on("disconnected", (code: number, reason: string) =>
    mgrLog.warn({ code, reason }, "Public WS disconnected"),
  );
  publicWs.on("error", (err: unknown) =>
    mgrLog.error({ err }, "Public WS error"),
  );
  publicWs.connect();

  return publicWs;
}

/**
 * Get the current public WS instance (null if not started).
 */
export function getPublicWs(): BybitPublicWs | null {
  return publicWs;
}

/**
 * Start a private WS connection for a specific exchange connection.
 *
 * @param connectionId  Unique identifier (e.g. exchangeConnection.id)
 * @param apiKey        Bybit API key
 * @param apiSecret     Decrypted Bybit API secret
 */
export function startPrivateWs(
  connectionId: string,
  apiKey: string,
  apiSecret: string,
): BybitPrivateWs {
  const existing = privateInstances.get(connectionId);
  if (existing) return existing;

  const ws = new BybitPrivateWs(apiKey, apiSecret);
  ws.on("authenticated", () =>
    mgrLog.info({ connectionId }, "Private WS authenticated"),
  );
  ws.on("authError", (reason: string) =>
    mgrLog.error({ connectionId, reason }, "Private WS auth failed"),
  );
  ws.on("execution", (report) =>
    mgrLog.debug({ connectionId, orderId: report.orderId }, "Execution report"),
  );
  ws.on("disconnected", (code: number, reason: string) =>
    mgrLog.warn({ connectionId, code, reason }, "Private WS disconnected"),
  );

  privateInstances.set(connectionId, ws);
  ws.connect();

  return ws;
}

/**
 * Get a private WS instance by connection ID.
 */
export function getPrivateWs(connectionId: string): BybitPrivateWs | null {
  return privateInstances.get(connectionId) ?? null;
}

/**
 * Stop a specific private WS connection.
 */
export function stopPrivateWs(connectionId: string): void {
  const ws = privateInstances.get(connectionId);
  if (ws) {
    ws.close();
    privateInstances.delete(connectionId);
    mgrLog.info({ connectionId }, "Private WS stopped");
  }
}

/**
 * Stop all WS connections (public + all private).
 * Called on worker shutdown.
 */
export function stopAllWs(): void {
  if (publicWs) {
    publicWs.close();
    publicWs = null;
    mgrLog.info("Public WS stopped");
  }

  for (const [id, ws] of privateInstances) {
    ws.close();
    mgrLog.info({ connectionId: id }, "Private WS stopped");
  }
  privateInstances.clear();
}

/**
 * Reset manager state (for testing).
 */
export function _resetForTest(): void {
  stopAllWs();
}
