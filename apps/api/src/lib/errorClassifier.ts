/**
 * Error Classifier — pure classification of execution errors (#141)
 *
 * Classifies errors from the Bybit order execution path into:
 *   - transient: retriable (rate limits, network timeouts, temporary outages)
 *   - permanent: not retriable (invalid params, insufficient margin, config errors)
 *   - unknown: conservative default for unrecognized errors
 *
 * Used by botWorker.executeIntent to record structured failure metadata
 * and inform circuit breaker decisions.
 *
 * Design:
 *   - Pure function: string in → classification out, no I/O
 *   - Deterministic: same error message always produces same classification
 *   - Conservative: unknown errors are classified as "unknown" (not silently
 *     treated as transient or permanent)
 *
 * Error message formats from bybitOrder.ts:
 *   HTTP-level:  "Bybit order request failed: {status} {statusText}"
 *   API-level:   "Bybit API error {retCode}: {retMsg}"
 *   Other:       free-form Error.message strings
 *
 * Stage 8, issue #141 — slice 3: retry classification + dead-letter handling.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ErrorClass = "transient" | "permanent" | "unknown";

export interface ErrorClassification {
  errorClass: ErrorClass;
  retryable: boolean;
  reason: string;
}

// ---------------------------------------------------------------------------
// Bybit retCode classification
// ---------------------------------------------------------------------------

/**
 * Bybit V5 API retCodes that indicate transient/rate-limit issues.
 * These are safe to retry with backoff.
 *
 * Ref: https://bybit-exchange.github.io/docs/v5/error
 */
const TRANSIENT_RET_CODES = new Set([
  10006,  // too many requests (rate limit)
  10016,  // server error
  10018,  // server timeout
]);

/**
 * Bybit V5 API retCodes that indicate permanent order rejection.
 * These should NOT be retried — the order is fundamentally invalid.
 */
const PERMANENT_RET_CODES = new Set([
  10001,  // parameter error
  10003,  // invalid API key
  10004,  // sign error
  10005,  // permission denied
  10010,  // IP not whitelisted
  10027,  // banned
  110001, // order not modified (duplicate)
  110003, // insufficient balance / margin
  110004, // price is too high
  110005, // price is too low
  110006, // qty exceeds max
  110007, // insufficient available balance
  110008, // order already filled or cancelled
  110009, // max active orders exceeded
  110010, // post-only order would trade immediately
  110012, // insufficient close qty
  110013, // close order size exceeds position
  110015, // trading is paused
  110017, // reduce-only not allowed
  110025, // trading is banned
  110043, // set leverage not allowed
  110044, // insufficient balance after position assignment
  170124, // invalid symbol
]);

/**
 * HTTP status codes that indicate transient server/network issues.
 */
const TRANSIENT_HTTP_STATUSES = new Set([
  408, // Request Timeout
  429, // Too Many Requests
  500, // Internal Server Error
  502, // Bad Gateway
  503, // Service Unavailable
  504, // Gateway Timeout
]);

/**
 * HTTP status codes that indicate permanent client errors.
 */
const PERMANENT_HTTP_STATUSES = new Set([
  400, // Bad Request
  401, // Unauthorized
  403, // Forbidden
  404, // Not Found
  405, // Method Not Allowed
  422, // Unprocessable Entity
]);

// ---------------------------------------------------------------------------
// Network / system error patterns (transient)
// ---------------------------------------------------------------------------

const TRANSIENT_ERROR_PATTERNS = [
  /ECONNREFUSED/i,
  /ECONNRESET/i,
  /ETIMEDOUT/i,
  /ENETUNREACH/i,
  /EHOSTUNREACH/i,
  /ENOTFOUND/i,
  /socket hang up/i,
  /network/i,
  /timeout/i,
  /fetch failed/i,
  /abort/i,
  // Global kill-switch — operator can re-enable; treat as transient so
  // the worker retry loop picks the order up on the next tick once
  // TRADING_ENABLED flips back. See lib/tradingKillSwitch.ts.
  /trading disabled/i,
];

// ---------------------------------------------------------------------------
// Config / normalization error patterns (permanent)
// ---------------------------------------------------------------------------

const PERMANENT_ERROR_PATTERNS = [
  /SECRET_ENCRYPTION_KEY not configured/i,
  /normalization failed/i,
  /invalid.*symbol/i,
  /insufficient.*margin/i,
  /insufficient.*balance/i,
];

// ---------------------------------------------------------------------------
// Classifier
// ---------------------------------------------------------------------------

/**
 * Classify an execution error as transient, permanent, or unknown.
 *
 * Classification priority:
 *   1. Parse Bybit API retCode → known retCode sets
 *   2. Parse HTTP status → known HTTP status sets
 *   3. Match against known error message patterns
 *   4. Fall through to "unknown" (conservative)
 *
 * Pure function: no I/O, deterministic.
 */
export function classifyExecutionError(error: unknown): ErrorClassification {
  const message = error instanceof Error ? error.message : String(error);

  // 1. Try to parse Bybit API error with retCode
  const apiMatch = message.match(/Bybit API error (\d+):/);
  if (apiMatch) {
    const retCode = parseInt(apiMatch[1], 10);

    if (TRANSIENT_RET_CODES.has(retCode)) {
      return {
        errorClass: "transient",
        retryable: true,
        reason: `Bybit retCode ${retCode} is transient`,
      };
    }

    if (PERMANENT_RET_CODES.has(retCode)) {
      return {
        errorClass: "permanent",
        retryable: false,
        reason: `Bybit retCode ${retCode} is permanent`,
      };
    }

    // Unknown retCode — conservative
    return {
      errorClass: "unknown",
      retryable: false,
      reason: `Bybit retCode ${retCode} is not in known classification`,
    };
  }

  // 2. Try to parse HTTP-level error
  const httpMatch = message.match(/Bybit (?:order|status) request failed: (\d+)/);
  if (httpMatch) {
    const status = parseInt(httpMatch[1], 10);

    if (TRANSIENT_HTTP_STATUSES.has(status)) {
      return {
        errorClass: "transient",
        retryable: true,
        reason: `HTTP ${status} is transient`,
      };
    }

    if (PERMANENT_HTTP_STATUSES.has(status)) {
      return {
        errorClass: "permanent",
        retryable: false,
        reason: `HTTP ${status} is permanent`,
      };
    }

    return {
      errorClass: "unknown",
      retryable: false,
      reason: `HTTP ${status} is not in known classification`,
    };
  }

  // 3. Match against known error patterns
  for (const pattern of TRANSIENT_ERROR_PATTERNS) {
    if (pattern.test(message)) {
      return {
        errorClass: "transient",
        retryable: true,
        reason: `error message matches transient pattern: ${pattern.source}`,
      };
    }
  }

  for (const pattern of PERMANENT_ERROR_PATTERNS) {
    if (pattern.test(message)) {
      return {
        errorClass: "permanent",
        retryable: false,
        reason: `error message matches permanent pattern: ${pattern.source}`,
      };
    }
  }

  // 4. Unknown — conservative: do not retry
  return {
    errorClass: "unknown",
    retryable: false,
    reason: "error does not match any known classification pattern",
  };
}
