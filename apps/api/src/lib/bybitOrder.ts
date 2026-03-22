/**
 * Bybit V5 private order API helpers (requires API key + secret).
 * Used by: terminal order routes (Stage 9b), botWorker (Stage 11).
 *
 * Authentication: HMAC-SHA256 over timestamp + apiKey + recvWindow + payload.
 * Ref: https://bybit-exchange.github.io/docs/v5/guide/authentication
 *
 * Environment routing (Stage 3, #129):
 *   BYBIT_ENV=demo  → https://api-demo.bybit.com (default)
 *   BYBIT_ENV=live  → https://api.bybit.com
 *   BYBIT_BASE_URL  → explicit override (takes precedence)
 */

import { createHmac } from "node:crypto";

// ---------------------------------------------------------------------------
// Environment-aware base URL
// ---------------------------------------------------------------------------

const BYBIT_LIVE_URL = "https://api.bybit.com";
const BYBIT_DEMO_URL = "https://api-demo.bybit.com";

/**
 * Resolve the Bybit base URL from environment config.
 *
 * Priority:
 *   1. BYBIT_BASE_URL env var (explicit override)
 *   2. BYBIT_ENV=live → live endpoint
 *   3. BYBIT_ENV=demo or unset → demo endpoint (safe default)
 */
export function getBybitBaseUrl(): string {
  if (process.env.BYBIT_BASE_URL) {
    return process.env.BYBIT_BASE_URL;
  }
  if (process.env.BYBIT_ENV === "live") {
    return BYBIT_LIVE_URL;
  }
  // Default to demo — safe for development
  return BYBIT_DEMO_URL;
}

/** Check if currently configured for live trading. */
export function isBybitLive(): boolean {
  return getBybitBaseUrl() === BYBIT_LIVE_URL;
}

const RECV_WINDOW = "5000";

// ---------------------------------------------------------------------------
// Signing
// ---------------------------------------------------------------------------

function sign(secret: string, timestamp: string, apiKey: string, payload: string): string {
  const preSign = `${timestamp}${apiKey}${RECV_WINDOW}${payload}`;
  return createHmac("sha256", secret).update(preSign).digest("hex");
}

function authHeaders(
  apiKey: string,
  secret: string,
  timestamp: string,
  payload: string,
): Record<string, string> {
  return {
    "X-BAPI-API-KEY": apiKey,
    "X-BAPI-SIGN": sign(secret, timestamp, apiKey, payload),
    "X-BAPI-TIMESTAMP": timestamp,
    "X-BAPI-RECV-WINDOW": RECV_WINDOW,
    "User-Agent": "botmarketplace-terminal/1",
  };
}

// ---------------------------------------------------------------------------
// Place order
// ---------------------------------------------------------------------------

export interface PlaceOrderParams {
  /** Bybit instrument (e.g. "BTCUSDT") */
  symbol: string;
  side: "Buy" | "Sell";
  orderType: "Market" | "Limit";
  /** Quantity as string (Bybit requires string representation) */
  qty: string;
  /** Required for Limit orders */
  price?: string;
  /** Time-in-force; defaults to GTC for Limit, IOC for Market */
  timeInForce?: string;
}

export interface PlaceOrderResult {
  orderId: string;
  orderLinkId: string;
}

/**
 * Place a linear perpetual order on Bybit.
 * Throws on network error or non-zero retCode.
 */
export async function bybitPlaceOrder(
  apiKey: string,
  secret: string,
  params: PlaceOrderParams,
): Promise<PlaceOrderResult> {
  const body = JSON.stringify({
    category: "linear",
    symbol: params.symbol,
    side: params.side,
    orderType: params.orderType,
    qty: params.qty,
    ...(params.price !== undefined ? { price: params.price } : {}),
    timeInForce: params.timeInForce ?? (params.orderType === "Market" ? "IOC" : "GTC"),
  });

  const timestamp = Date.now().toString();

  const res = await fetch(`${getBybitBaseUrl()}/v5/order/create`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(apiKey, secret, timestamp, body),
    },
    body,
  });

  if (!res.ok) {
    throw new Error(`Bybit order request failed: ${res.status} ${res.statusText}`);
  }

  const json = (await res.json()) as {
    retCode: number;
    retMsg: string;
    result: { orderId: string; orderLinkId: string };
  };

  if (json.retCode !== 0) {
    throw new Error(`Bybit API error ${json.retCode}: ${json.retMsg}`);
  }

  return { orderId: json.result.orderId, orderLinkId: json.result.orderLinkId };
}

// ---------------------------------------------------------------------------
// Get order status
// ---------------------------------------------------------------------------

export interface OrderStatusResult {
  orderId: string;
  symbol: string;
  side: string;
  orderType: string;
  qty: string;
  price: string;
  cumExecQty: string;
  orderStatus: string; // Bybit raw status: New | PartiallyFilled | Filled | Cancelled | Rejected
  createdTime: string;
  updatedTime: string;
}

/**
 * Fetch live order status from Bybit order history endpoint.
 * Falls back to open-orders endpoint if not found in history (race condition on very new orders).
 *
 * Throws if the order cannot be found or Bybit returns an error.
 */
export async function bybitGetOrderStatus(
  apiKey: string,
  secret: string,
  orderId: string,
  symbol: string,
): Promise<OrderStatusResult> {
  // Try history first (covers all terminal statuses)
  const historyResult = await _fetchOrderFromEndpoint(
    apiKey,
    secret,
    "/v5/order/history",
    { category: "linear", orderId, symbol },
  );
  if (historyResult) return historyResult;

  // Fallback: open orders (very new order not yet in history)
  const realtimeResult = await _fetchOrderFromEndpoint(
    apiKey,
    secret,
    "/v5/order/realtime",
    { category: "linear", orderId, symbol },
  );
  if (realtimeResult) return realtimeResult;

  throw new Error(`Order not found: ${orderId}`);
}

async function _fetchOrderFromEndpoint(
  apiKey: string,
  secret: string,
  path: string,
  params: Record<string, string>,
): Promise<OrderStatusResult | null> {
  const qs = new URLSearchParams(params).toString();
  const timestamp = Date.now().toString();

  const res = await fetch(`${getBybitBaseUrl()}${path}?${qs}`, {
    headers: authHeaders(apiKey, secret, timestamp, qs),
  });

  if (!res.ok) {
    throw new Error(`Bybit status request failed: ${res.status} ${res.statusText}`);
  }

  const json = (await res.json()) as {
    retCode: number;
    retMsg: string;
    result: {
      list: Array<{
        orderId: string;
        symbol: string;
        side: string;
        orderType: string;
        qty: string;
        price: string;
        cumExecQty: string;
        orderStatus: string;
        createdTime: string;
        updatedTime: string;
      }>;
    };
  };

  if (json.retCode !== 0) {
    throw new Error(`Bybit API error ${json.retCode}: ${json.retMsg}`);
  }

  const item = json.result?.list?.find((o) => o.orderId === params.orderId);
  if (!item) return null;

  return {
    orderId: item.orderId,
    symbol: item.symbol,
    side: item.side,
    orderType: item.orderType,
    qty: item.qty,
    price: item.price,
    cumExecQty: item.cumExecQty,
    orderStatus: item.orderStatus,
    createdTime: item.createdTime,
    updatedTime: item.updatedTime,
  };
}

// ---------------------------------------------------------------------------
// Map Bybit status → TerminalOrderStatus
// ---------------------------------------------------------------------------

export function mapBybitStatus(
  bybitStatus: string,
): "SUBMITTED" | "FILLED" | "PARTIALLY_FILLED" | "CANCELLED" | "REJECTED" | "FAILED" {
  switch (bybitStatus) {
    case "New":
    case "Created":
    case "Untriggered":
    case "Active":
      return "SUBMITTED";
    case "PartiallyFilled":
      return "PARTIALLY_FILLED";
    case "Filled":
      return "FILLED";
    case "Cancelled":
    case "Deactivated":
      return "CANCELLED";
    case "Rejected":
      return "REJECTED";
    default:
      return "SUBMITTED";
  }
}

// ---------------------------------------------------------------------------
// Sanitize Bybit error message (never leak raw internal details)
// ---------------------------------------------------------------------------

export function sanitizeBybitError(err: unknown): string {
  const msg = err instanceof Error ? err.message : String(err);
  // Keep the structured Bybit error message but strip any stack trace
  const firstLine = msg.split("\n")[0] ?? msg;
  return firstLine.slice(0, 500); // hard cap
}
