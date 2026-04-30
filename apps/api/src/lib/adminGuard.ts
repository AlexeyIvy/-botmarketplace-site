/**
 * Admin guard — minimal env-based authentication for catalog-management
 * endpoints (e.g. POST /presets in docs/51-T2).
 *
 * The platform does not yet have a global "platform admin" role. Until that
 * lands, endpoints that mutate cross-workspace catalogs gate on a shared
 * secret carried in the `X-Admin-Token` header and matched against
 * `process.env.ADMIN_API_TOKEN` in constant time. If the env var is unset
 * the guard refuses every request — so a misconfigured deploy fails closed.
 */

import { timingSafeEqual } from "node:crypto";
import type { FastifyRequest } from "fastify";

const ADMIN_TOKEN_HEADER = "x-admin-token";

/**
 * Returns true when the request carries a valid admin token.
 *
 * Behaviour:
 * - `ADMIN_API_TOKEN` env var unset → always false (fails closed).
 * - Header missing or wrong length → false.
 * - Otherwise constant-time comparison.
 */
export function isAdminRequest(request: FastifyRequest): boolean {
  const expected = process.env.ADMIN_API_TOKEN;
  if (!expected) return false;

  const provided = request.headers[ADMIN_TOKEN_HEADER];
  if (typeof provided !== "string" || provided.length === 0) return false;

  const a = Buffer.from(provided);
  const b = Buffer.from(expected);
  if (a.length !== b.length) return false;
  return timingSafeEqual(a, b);
}
