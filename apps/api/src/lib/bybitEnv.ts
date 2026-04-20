import { getBybitBaseUrl, isBybitLive } from "./bybitOrder.js";
import { logger } from "./logger.js";

const bybitLog = logger.child({ module: "bybitEnv" });

/**
 * Validate exchange environment at startup and log the active mode loudly.
 *
 * Prevents the §5.10 scenario: operator accidentally deploys with a live
 * Bybit URL → real-money orders get placed silently. We:
 *   1. Log `[BYBIT MODE: LIVE|DEMO]` with the effective base URL
 *   2. In production, require explicit opt-in to LIVE via BYBIT_ALLOW_LIVE=true
 *   3. Warn on URLs that don't match any known Bybit host
 *
 * Throws in production when LIVE is active without BYBIT_ALLOW_LIVE=true.
 * Otherwise never throws — just logs.
 */
export function validateBybitEnv(): void {
  const baseUrl = getBybitBaseUrl();
  const live = isBybitLive();
  const mode = live ? "LIVE" : "DEMO";

  bybitLog.info({ mode, baseUrl }, `[BYBIT MODE: ${mode}]`);

  if (live && process.env.NODE_ENV === "production") {
    if (process.env.BYBIT_ALLOW_LIVE !== "true") {
      throw new Error(
        "Refusing to start: BYBIT_ENV=live in production without BYBIT_ALLOW_LIVE=true. " +
          "Set BYBIT_ALLOW_LIVE=true explicitly to acknowledge real-money trading.",
      );
    }
    bybitLog.warn(
      { baseUrl },
      "[BYBIT LIVE TRADING ENABLED] real-money orders will be placed",
    );
  }

  // Suspicious URL sanity check — help catch typos like `api.bybit.co` etc.
  const knownHosts = ["api.bybit.com", "api-demo.bybit.com", "api-testnet.bybit.com"];
  try {
    const u = new URL(baseUrl);
    if (u.protocol !== "https:" && u.hostname !== "localhost" && u.hostname !== "127.0.0.1") {
      bybitLog.warn({ baseUrl }, "BYBIT_BASE_URL is not https — unexpected in production");
    }
    if (!knownHosts.includes(u.hostname) && u.hostname !== "localhost" && u.hostname !== "127.0.0.1") {
      bybitLog.warn(
        { baseUrl, knownHosts },
        "BYBIT_BASE_URL host does not match any known Bybit endpoint",
      );
    }
  } catch {
    bybitLog.warn({ baseUrl }, "BYBIT_BASE_URL is not a valid URL");
  }
}
