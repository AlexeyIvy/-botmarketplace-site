/**
 * Verify a Bybit API key by calling the read-only `/v5/user/query-api`
 * endpoint and parsing the credential metadata it returns.
 *
 * Used by `POST /exchanges/:id/test` to give operators an instant
 * answer when they wire up a fresh demo / live key — was the key
 * accepted, against which environment, with what permissions, and when
 * does it expire.
 *
 * Network/HTTP/Bybit-side errors are funnelled into a single typed
 * result so the route handler does not have to discriminate between
 * `throw` and "valid but failed" — both surface as
 * `{ ok: false, code, detail }`.
 */

import { bybitAuthHeaders } from "./bybitAuth.js";
import { getBybitBaseUrl, isBybitLive } from "../bybitOrder.js";

const USER_AGENT = "botmarketplace-verify/1";
const QUERY_API_PATH = "/v5/user/query-api";
const REQUEST_TIMEOUT_MS = 10_000;

/** Bybit-side response shape — only the fields we need; extra fields ignored. */
interface BybitQueryApiResult {
  apiKey?: string;
  readOnly?: number;
  /** ISO timestamp string, empty string, or "0" when no expiry set. */
  expiredAt?: string;
  /** Object whose keys are permission groups, each mapped to a string[] of granted scopes. */
  permissions?: Record<string, string[]>;
  type?: number;
}

interface BybitEnvelope {
  retCode: number;
  retMsg: string;
  result?: BybitQueryApiResult;
}

export type VerifyFailureCode =
  | "NETWORK"
  | "TIMEOUT"
  | "HTTP"
  | "BYBIT"
  | "MALFORMED";

export interface VerifySuccess {
  ok: true;
  /** Inferred from the configured base URL — `live` if BYBIT_ENV=live or BYBIT_BASE_URL points at the live host, else `demo`. */
  env: "demo" | "live";
  /** Flat list of granted permissions in `Group:Scope` form (e.g. `ContractTrade:Order`). */
  permissions: string[];
  /** ISO timestamp when the key expires, or `null` when Bybit reports no expiry. */
  expiresAt: string | null;
  /** True when Bybit reports `readOnly: 1` — i.e. no Trade/Order scope was granted. */
  readOnly: boolean;
}

export interface VerifyFailure {
  ok: false;
  code: VerifyFailureCode;
  /** Human-friendly reason. Already operator-readable; safe to render verbatim. */
  detail: string;
  /** Bybit `retCode` when `code === "BYBIT"`. */
  retCode?: number;
  /** HTTP status when `code === "HTTP"`. */
  httpStatus?: number;
}

export type VerifyResult = VerifySuccess | VerifyFailure;

/**
 * Hit Bybit `/v5/user/query-api` with the given credentials and translate
 * the response into a `VerifyResult`. Never throws — every failure mode
 * is a typed `VerifyFailure`.
 *
 * Optional `fetchImpl` is exposed only for tests; production callers use
 * the global `fetch`.
 */
export async function bybitVerifyApiKey(
  apiKey: string,
  secret: string,
  fetchImpl: typeof fetch = fetch,
): Promise<VerifyResult> {
  const baseUrl = getBybitBaseUrl();
  const env: "demo" | "live" = isBybitLive() ? "live" : "demo";
  const timestamp = Date.now().toString();
  // GET signing payload is the URL-encoded query string. /v5/user/query-api
  // takes no query parameters, so the payload is the empty string.
  const headers = bybitAuthHeaders(apiKey, secret, timestamp, "", USER_AGENT);

  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), REQUEST_TIMEOUT_MS);

  let res: Response;
  try {
    res = await fetchImpl(`${baseUrl}${QUERY_API_PATH}`, {
      method: "GET",
      headers,
      signal: ac.signal,
    });
  } catch (err) {
    if ((err as { name?: string }).name === "AbortError") {
      return { ok: false, code: "TIMEOUT", detail: "Bybit request timed out" };
    }
    return {
      ok: false,
      code: "NETWORK",
      detail: `Bybit unreachable: ${(err as Error).message ?? "network error"}`,
    };
  } finally {
    clearTimeout(timer);
  }

  if (!res.ok) {
    return {
      ok: false,
      code: "HTTP",
      httpStatus: res.status,
      detail: `Bybit returned HTTP ${res.status} ${res.statusText}`,
    };
  }

  let body: BybitEnvelope;
  try {
    body = (await res.json()) as BybitEnvelope;
  } catch {
    return {
      ok: false,
      code: "MALFORMED",
      detail: "Bybit response was not valid JSON",
    };
  }

  if (typeof body.retCode !== "number") {
    return {
      ok: false,
      code: "MALFORMED",
      detail: "Bybit response missing retCode",
    };
  }

  if (body.retCode !== 0) {
    return {
      ok: false,
      code: "BYBIT",
      retCode: body.retCode,
      detail: `Bybit error ${body.retCode}: ${body.retMsg || "(no message)"}`,
    };
  }

  const result = body.result;
  if (!result) {
    return {
      ok: false,
      code: "MALFORMED",
      detail: "Bybit retCode=0 but no result payload",
    };
  }

  return {
    ok: true,
    env,
    permissions: flattenPermissions(result.permissions),
    expiresAt: normaliseExpiry(result.expiredAt),
    readOnly: result.readOnly === 1,
  };
}

/**
 * Bybit returns permissions as `{ Group: [Scope, Scope] }`. Flatten to
 * `Group:Scope` strings sorted alphabetically — gives a stable, easily
 * rendered list in the UI.
 */
function flattenPermissions(
  raw: Record<string, string[]> | undefined,
): string[] {
  if (!raw) return [];
  const flat: string[] = [];
  for (const [group, scopes] of Object.entries(raw)) {
    if (!Array.isArray(scopes)) continue;
    for (const scope of scopes) {
      if (typeof scope === "string" && scope.length > 0) {
        flat.push(`${group}:${scope}`);
      }
    }
  }
  flat.sort();
  return flat;
}

/**
 * Bybit reports `expiredAt` either as an ISO timestamp ("2023-04-19T03:25:05Z"),
 * the literal string "0" (no expiry), an empty string (no expiry), or the
 * field is absent. Normalise to `string | null`.
 */
function normaliseExpiry(raw: string | undefined): string | null {
  if (!raw) return null;
  if (raw === "0") return null;
  return raw;
}
