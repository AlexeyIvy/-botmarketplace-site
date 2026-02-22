import type { FastifyInstance } from "fastify";
import { problem } from "../lib/problem.js";
import { fetchTicker } from "../lib/bybitCandles.js";
import { fetchCandles } from "../lib/bybitCandles.js";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/**
 * Supported Bybit kline intervals for Terminal read-only view.
 * Superset of lab.ts intervals; includes intraday + daily.
 */
const VALID_INTERVALS = ["1", "5", "15", "30", "60", "240", "D"] as const;
type TerminalInterval = (typeof VALID_INTERVALS)[number];

const DEFAULT_LIMIT = 200;
const MAX_LIMIT = 1000; // Bybit single-page cap

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function isValidInterval(v: string): v is TerminalInterval {
  return (VALID_INTERVALS as readonly string[]).includes(v);
}

/** Map an error from the Bybit helper to a stable Problem Details response. */
function bybitErrorToProblem(
  reply: import("fastify").FastifyReply,
  err: unknown,
  context: string,
) {
  const msg = err instanceof Error ? err.message : String(err);

  // "Symbol not found" or "symbol invalid" → 422
  if (
    msg.toLowerCase().includes("symbol not found") ||
    msg.includes("not found") ||
    msg.toLowerCase().includes("symbol invalid")
  ) {
    return problem(reply, 422, "Unprocessable Content", `Unknown symbol. ${msg}`);
  }

  // Bybit API-level error (retCode ≠ 0) → 502
  if (msg.startsWith("Bybit API error")) {
    return problem(reply, 502, "Bad Gateway", `Upstream market data error: ${msg}`);
  }

  // Bybit HTTP error → 502
  if (msg.startsWith("Bybit ")) {
    return problem(reply, 502, "Bad Gateway", `Upstream request failed: ${msg}`);
  }

  // Fallback
  return problem(reply, 500, "Internal Server Error", `Failed to fetch ${context}`);
}

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

export async function terminalRoutes(app: FastifyInstance) {
  /**
   * GET /terminal/ticker?symbol=BTCUSDT
   *
   * Returns current ticker data for a linear perpetual symbol.
   * Requires authentication (JWT). No workspace required — Bybit data is public.
   */
  app.get<{ Querystring: { symbol?: string } }>(
    "/terminal/ticker",
    { onRequest: [app.authenticate] },
    async (request, reply) => {
      const { symbol } = request.query;

      if (!symbol || typeof symbol !== "string" || !symbol.trim()) {
        return problem(reply, 400, "Bad Request", "Query parameter 'symbol' is required");
      }

      const sym = symbol.trim().toUpperCase();

      try {
        const ticker = await fetchTicker(sym);
        return reply.send(ticker);
      } catch (err) {
        request.log.warn({ symbol: sym, err }, "terminal ticker fetch failed");
        return bybitErrorToProblem(reply, err, "ticker");
      }
    },
  );

  /**
   * GET /terminal/candles?symbol=BTCUSDT&interval=15&limit=200
   *
   * Returns recent OHLCV candles for a linear perpetual symbol.
   * Requires authentication (JWT). No workspace required — Bybit data is public.
   *
   * Parameters:
   *   symbol   — required; e.g. "BTCUSDT"
   *   interval — optional; one of: 1, 5, 15, 30, 60, 240, D (default: 15)
   *   limit    — optional; 1–1000 (default: 200)
   */
  app.get<{ Querystring: { symbol?: string; interval?: string; limit?: string } }>(
    "/terminal/candles",
    { onRequest: [app.authenticate] },
    async (request, reply) => {
      const { symbol, interval: intervalParam, limit: limitParam } = request.query;

      // --- Validate symbol ---
      if (!symbol || typeof symbol !== "string" || !symbol.trim()) {
        return problem(reply, 400, "Bad Request", "Query parameter 'symbol' is required");
      }
      const sym = symbol.trim().toUpperCase();

      // --- Validate interval ---
      const interval = (intervalParam ?? "15").trim();
      if (!isValidInterval(interval)) {
        return problem(
          reply,
          400,
          "Bad Request",
          `Invalid 'interval'. Allowed values: ${VALID_INTERVALS.join(", ")}`,
        );
      }

      // --- Validate limit ---
      const limitRaw = limitParam !== undefined ? Number(limitParam) : DEFAULT_LIMIT;
      if (!Number.isInteger(limitRaw) || limitRaw < 1 || limitRaw > MAX_LIMIT) {
        return problem(
          reply,
          400,
          "Bad Request",
          `Invalid 'limit'. Must be an integer between 1 and ${MAX_LIMIT}`,
        );
      }
      const limit = limitRaw;

      // --- Fetch candles ---
      // Use a rolling window ending now, sized by interval × limit
      const toMs = Date.now();
      const intervalMs = intervalToMs(interval);
      const fromMs = toMs - intervalMs * limit * 2; // fetch 2× to ensure enough data after dedup

      try {
        const candles = await fetchCandles(sym, interval, fromMs, toMs, limit);
        return reply.send(candles);
      } catch (err) {
        request.log.warn({ symbol: sym, interval, limit, err }, "terminal candles fetch failed");
        return bybitErrorToProblem(reply, err, "candles");
      }
    },
  );
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

/** Convert Bybit interval string to approximate milliseconds (for window sizing). */
function intervalToMs(interval: string): number {
  if (interval === "D") return 24 * 60 * 60 * 1000;
  const mins = Number(interval);
  if (Number.isFinite(mins) && mins > 0) return mins * 60 * 1000;
  return 15 * 60 * 1000; // fallback
}
