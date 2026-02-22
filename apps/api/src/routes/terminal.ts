import type { FastifyInstance } from "fastify";
import { problem } from "../lib/problem.js";
import { fetchTicker } from "../lib/bybitCandles.js";
import { fetchCandles } from "../lib/bybitCandles.js";
import { prisma } from "../lib/prisma.js";
import { resolveWorkspace } from "../lib/workspace.js";
import { getEncryptionKey, decrypt } from "../lib/crypto.js";
import {
  bybitPlaceOrder,
  bybitGetOrderStatus,
  mapBybitStatus,
  sanitizeBybitError,
} from "../lib/bybitOrder.js";

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
  // Register order routes (Stage 9b)
  registerOrderRoutes(app);

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
// Order endpoints
// ---------------------------------------------------------------------------

interface CreateOrderBody {
  exchangeConnectionId: string;
  symbol: string;
  side: string;
  type: string;
  qty: number | string;
  price?: number | string;
}

/** Safe projection — never return encryptedSecret or apiKey. */
function orderView(o: {
  id: string;
  workspaceId: string;
  exchangeConnectionId: string;
  symbol: string;
  side: string;
  type: string;
  qty: { toString(): string };
  price: { toString(): string } | null;
  status: string;
  exchangeOrderId: string | null;
  error: string | null;
  createdAt: Date;
  updatedAt: Date;
}) {
  return {
    id: o.id,
    workspaceId: o.workspaceId,
    exchangeConnectionId: o.exchangeConnectionId,
    symbol: o.symbol,
    side: o.side,
    type: o.type,
    qty: o.qty.toString(),
    price: o.price !== null ? o.price.toString() : null,
    status: o.status,
    exchangeOrderId: o.exchangeOrderId,
    error: o.error,
    createdAt: o.createdAt,
    updatedAt: o.updatedAt,
  };
}

export function registerOrderRoutes(app: FastifyInstance) {
  /**
   * POST /terminal/orders
   *
   * Create a manual Market or Limit order.
   * Requires authentication + workspace membership.
   * Uses ExchangeConnection (Stage 8) for credentials.
   */
  app.post<{ Body: CreateOrderBody }>(
    "/terminal/orders",
    { onRequest: [app.authenticate] },
    async (request, reply) => {
      const workspace = await resolveWorkspace(request, reply);
      if (!workspace) return;

      const key = getEncryptionKey(reply);
      if (!key) return;

      const { exchangeConnectionId, symbol, side, type, qty, price } = request.body ?? {};

      // --- Input validation ---
      const errors: Array<{ field: string; message: string }> = [];

      if (!exchangeConnectionId || typeof exchangeConnectionId !== "string") {
        errors.push({ field: "exchangeConnectionId", message: "exchangeConnectionId is required" });
      }
      if (!symbol || typeof symbol !== "string" || !symbol.trim()) {
        errors.push({ field: "symbol", message: "symbol is required" });
      }
      const normalizedSide = typeof side === "string" ? side.toUpperCase() : "";
      if (!["BUY", "SELL"].includes(normalizedSide)) {
        errors.push({ field: "side", message: "side must be BUY or SELL" });
      }
      const normalizedType = typeof type === "string" ? type.toUpperCase() : "";
      if (!["MARKET", "LIMIT"].includes(normalizedType)) {
        errors.push({ field: "type", message: "type must be MARKET or LIMIT" });
      }
      const qtyNum = Number(qty);
      if (!qty || !Number.isFinite(qtyNum) || qtyNum <= 0) {
        errors.push({ field: "qty", message: "qty must be a positive number" });
      }
      // LIMIT requires price; MARKET must not have price (we reject to enforce clean contract)
      if (normalizedType === "LIMIT") {
        const priceNum = Number(price);
        if (price === undefined || price === null || price === "" || !Number.isFinite(priceNum) || priceNum <= 0) {
          errors.push({ field: "price", message: "price is required and must be a positive number for LIMIT orders" });
        }
      }
      if (normalizedType === "MARKET" && price !== undefined && price !== null && price !== "") {
        return problem(reply, 400, "Bad Request", "price must not be set for MARKET orders");
      }

      if (errors.length > 0) {
        return problem(reply, 400, "Validation Error", "Invalid order payload", { errors });
      }

      // --- Resolve ExchangeConnection ---
      const conn = await prisma.exchangeConnection.findUnique({
        where: { id: exchangeConnectionId },
      });
      if (!conn || conn.workspaceId !== workspace.id) {
        return problem(reply, 404, "Not Found", "Exchange connection not found");
      }

      // --- Decrypt secret ---
      let secret: string;
      try {
        secret = decrypt(conn.encryptedSecret, key);
      } catch (err) {
        request.log.error({ connectionId: conn.id, err }, "failed to decrypt exchange secret");
        return problem(reply, 500, "Internal Server Error", "Failed to decrypt exchange credentials");
      }

      const sym = symbol.trim().toUpperCase();
      const priceStr = normalizedType === "LIMIT" ? String(Number(price)) : undefined;
      const qtyStr = String(qtyNum);

      // --- Create DB record (PENDING) ---
      const order = await prisma.terminalOrder.create({
        data: {
          workspaceId: workspace.id,
          exchangeConnectionId: conn.id,
          symbol: sym,
          side: normalizedSide as "BUY" | "SELL",
          type: normalizedType as "MARKET" | "LIMIT",
          qty: qtyStr,
          price: priceStr ?? null,
          status: "PENDING",
        },
      });

      // --- Place order on Bybit ---
      try {
        const result = await bybitPlaceOrder(conn.apiKey, secret, {
          symbol: sym,
          side: normalizedSide === "BUY" ? "Buy" : "Sell",
          orderType: normalizedType === "MARKET" ? "Market" : "Limit",
          qty: qtyStr,
          price: priceStr,
        });

        const updated = await prisma.terminalOrder.update({
          where: { id: order.id },
          data: {
            status: "SUBMITTED",
            exchangeOrderId: result.orderId,
          },
        });

        // Update connection status to CONNECTED (first real successful call)
        await prisma.exchangeConnection.update({
          where: { id: conn.id },
          data: { status: "CONNECTED" },
        });

        return reply.status(201).send(orderView(updated));
      } catch (err) {
        const msg = sanitizeBybitError(err);
        request.log.warn({ orderId: order.id, symbol: sym, err }, "bybit place order failed");

        // Determine error HTTP code
        const errMsg = err instanceof Error ? err.message : String(err);
        let httpStatus = 502;
        let httpTitle = "Bad Gateway";
        if (
          errMsg.toLowerCase().includes("invalid symbol") ||
          errMsg.toLowerCase().includes("symbol invalid") ||
          errMsg.toLowerCase().includes("params error")
        ) {
          httpStatus = 422;
          httpTitle = "Unprocessable Content";
        } else if (
          errMsg.toLowerCase().includes("insufficient") ||
          errMsg.toLowerCase().includes("balance") ||
          errMsg.toLowerCase().includes("risk limit")
        ) {
          httpStatus = 422;
          httpTitle = "Unprocessable Content";
        }

        // Persist failure
        await prisma.terminalOrder.update({
          where: { id: order.id },
          data: { status: "FAILED", error: msg },
        });

        // Update connection status to FAILED only on auth errors
        if (errMsg.toLowerCase().includes("api key") || errMsg.toLowerCase().includes("signature")) {
          await prisma.exchangeConnection.update({
            where: { id: conn.id },
            data: { status: "FAILED" },
          });
        }

        return problem(reply, httpStatus, httpTitle, `Exchange rejected order: ${msg}`);
      }
    },
  );

  /**
   * GET /terminal/orders/:id
   *
   * Get the stored order record. If the order is in SUBMITTED/PARTIALLY_FILLED state,
   * fetches live status from Bybit and syncs it before returning.
   * Requires authentication + workspace membership.
   */
  app.get<{ Params: { id: string } }>(
    "/terminal/orders/:id",
    { onRequest: [app.authenticate] },
    async (request, reply) => {
      const workspace = await resolveWorkspace(request, reply);
      if (!workspace) return;

      const order = await prisma.terminalOrder.findUnique({
        where: { id: request.params.id },
      });
      if (!order || order.workspaceId !== workspace.id) {
        return problem(reply, 404, "Not Found", "Order not found");
      }

      // Sync live status from Bybit when order is still open
      if (
        order.exchangeOrderId &&
        (order.status === "SUBMITTED" || order.status === "PARTIALLY_FILLED")
      ) {
        const key = getEncryptionKey(reply);
        if (!key) return;

        const conn = await prisma.exchangeConnection.findUnique({
          where: { id: order.exchangeConnectionId },
        });
        if (conn) {
          try {
            const secret = decrypt(conn.encryptedSecret, key);
            const liveStatus = await bybitGetOrderStatus(
              conn.apiKey,
              secret,
              order.exchangeOrderId,
              order.symbol,
            );
            const mapped = mapBybitStatus(liveStatus.orderStatus);
            if (mapped !== order.status) {
              const synced = await prisma.terminalOrder.update({
                where: { id: order.id },
                data: { status: mapped },
              });
              return reply.send(orderView(synced));
            }
          } catch (err) {
            // Non-fatal: return stored status if live sync fails
            request.log.warn({ orderId: order.id, err }, "live order status sync failed — returning stored status");
          }
        }
      }

      return reply.send(orderView(order));
    },
  );

  /**
   * GET /terminal/orders
   *
   * List recent terminal orders for the workspace (latest 50).
   * Requires authentication + workspace membership.
   */
  app.get(
    "/terminal/orders",
    { onRequest: [app.authenticate] },
    async (request, reply) => {
      const workspace = await resolveWorkspace(request, reply);
      if (!workspace) return;

      const orders = await prisma.terminalOrder.findMany({
        where: { workspaceId: workspace.id },
        orderBy: { createdAt: "desc" },
        take: 50,
      });

      return reply.send(orders.map(orderView));
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
