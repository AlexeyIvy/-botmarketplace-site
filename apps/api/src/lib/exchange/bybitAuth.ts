/**
 * Bybit V5 private-API authentication helpers — shared by every module
 * that signs HMAC requests against Bybit (`bybitOrder.ts`,
 * `balanceReconciler.ts`, `funding/windowDetector.ts`).
 *
 * Before this module the same `sign` + `authHeaders` pair had been
 * duplicated three times. Extracting them into one place removes the
 * obvious DRY violation and gives every Bybit caller a single canonical
 * implementation of the V5 signature scheme to test against.
 *
 * Spec reference:
 *   https://bybit-exchange.github.io/docs/v5/guide/authentication
 *
 * Pre-sign string layout (HMAC-SHA256 input):
 *   `${timestamp}${apiKey}${recvWindow}${payload}`
 *
 * Where:
 *   - `timestamp`   — ms epoch as decimal string (matches `Date.now().toString()`).
 *   - `apiKey`      — the public half of the credential pair.
 *   - `recvWindow`  — Bybit-side allowed clock skew, in ms. Default 5000.
 *   - `payload`     — for POST: the JSON request body (exact bytes Bybit
 *                     receives). For GET: the URL-encoded query string
 *                     (no leading `?`).
 *
 * The header set returned by `bybitAuthHeaders` is intentionally minimal:
 * just the four required `X-BAPI-*` headers plus a caller-supplied
 * User-Agent. Callers add `Content-Type` themselves on the request side
 * because GETs do not need it.
 */

import { createHmac } from "node:crypto";

/** Default Bybit `recvWindow` (ms) — five seconds, which is what every
 *  inline copy in the codebase used. Bybit's documented max is 60_000ms
 *  but the project does not need a wider window. */
export const BYBIT_RECV_WINDOW = "5000";

/** Compute the Bybit V5 HMAC-SHA256 signature.
 *
 *  Returns the signature as a lowercase hex string — same format Bybit's
 *  `X-BAPI-SIGN` header expects. The output is deterministic for a given
 *  set of inputs, which is what makes the unit tests in
 *  `tests/lib/exchange/bybitAuth.test.ts` possible. */
export function signBybit(
  secret: string,
  timestamp: string,
  apiKey: string,
  payload: string,
  recvWindow: string = BYBIT_RECV_WINDOW,
): string {
  return createHmac("sha256", secret)
    .update(`${timestamp}${apiKey}${recvWindow}${payload}`)
    .digest("hex");
}

/** Build the four standard `X-BAPI-*` headers plus a User-Agent string.
 *
 *  `userAgent` is required (no default) — Bybit-side traffic logs are
 *  much easier to debug when each module identifies itself, and we never
 *  want a generic Node-default UA leaking out. The existing call sites
 *  use:
 *    - bybitOrder         → "botmarketplace-terminal/1"
 *    - balanceReconciler  → "botmarketplace-balance/1"
 *    - windowDetector     → "botmarketplace-funding/1"
 */
export function bybitAuthHeaders(
  apiKey: string,
  secret: string,
  timestamp: string,
  payload: string,
  userAgent: string,
  recvWindow: string = BYBIT_RECV_WINDOW,
): Record<string, string> {
  return {
    "X-BAPI-API-KEY": apiKey,
    "X-BAPI-SIGN": signBybit(secret, timestamp, apiKey, payload, recvWindow),
    "X-BAPI-TIMESTAMP": timestamp,
    "X-BAPI-RECV-WINDOW": recvWindow,
    "User-Agent": userAgent,
  };
}
