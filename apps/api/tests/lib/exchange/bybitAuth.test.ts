/**
 * bybitAuth — deterministic-output unit coverage for the shared
 * Bybit V5 HMAC signature helpers.
 *
 * The signature is the linchpin every Bybit caller (`bybitOrder`,
 * `balanceReconciler`, `windowDetector`) depends on, so the test
 * suite pins the exact spec layout — `${ts}${apiKey}${recvWindow}${payload}`
 * — and asserts every part of the header bundle. If any of these
 * drift, every Bybit request from the platform would silently start
 * returning Bybit's `-101` "invalid signature" response.
 */

import { createHmac } from "node:crypto";
import { describe, it, expect } from "vitest";

import {
  signBybit,
  bybitAuthHeaders,
  BYBIT_RECV_WINDOW,
} from "../../../src/lib/exchange/bybitAuth.js";

// Reference inputs — chosen so the signature is easy to recompute by
// hand if the spec ever needs to be re-verified.
const SECRET = "test-secret-abc";
const API_KEY = "test-key-123";
const TIMESTAMP = "1714665600000";
const PAYLOAD_GET = "category=linear&symbol=BTCUSDT";
const PAYLOAD_POST = JSON.stringify({ category: "spot", side: "Buy" });
const USER_AGENT = "test-suite/1";

function expectedSig(payload: string, recvWindow: string = BYBIT_RECV_WINDOW): string {
  return createHmac("sha256", SECRET)
    .update(`${TIMESTAMP}${API_KEY}${recvWindow}${payload}`)
    .digest("hex");
}

describe("signBybit", () => {
  it("matches the V5 pre-sign layout: ts + apiKey + recvWindow + payload", () => {
    const got = signBybit(SECRET, TIMESTAMP, API_KEY, PAYLOAD_GET);
    expect(got).toBe(expectedSig(PAYLOAD_GET));
  });

  it("is deterministic — same inputs produce the same hex", () => {
    const a = signBybit(SECRET, TIMESTAMP, API_KEY, PAYLOAD_POST);
    const b = signBybit(SECRET, TIMESTAMP, API_KEY, PAYLOAD_POST);
    expect(a).toBe(b);
  });

  it("changes when ANY input changes — defence against silent partial-input bugs", () => {
    const baseline = signBybit(SECRET, TIMESTAMP, API_KEY, PAYLOAD_GET);
    expect(signBybit("other-secret", TIMESTAMP, API_KEY, PAYLOAD_GET)).not.toBe(baseline);
    expect(signBybit(SECRET, "9999999999999", API_KEY, PAYLOAD_GET)).not.toBe(baseline);
    expect(signBybit(SECRET, TIMESTAMP, "other-key", PAYLOAD_GET)).not.toBe(baseline);
    expect(signBybit(SECRET, TIMESTAMP, API_KEY, "other=payload")).not.toBe(baseline);
  });

  it("honours an explicit non-default recvWindow", () => {
    const got = signBybit(SECRET, TIMESTAMP, API_KEY, PAYLOAD_GET, "10000");
    expect(got).toBe(expectedSig(PAYLOAD_GET, "10000"));
    // And differs from the default recvWindow signature.
    expect(got).not.toBe(signBybit(SECRET, TIMESTAMP, API_KEY, PAYLOAD_GET));
  });

  it("returns lowercase hex — Bybit V5 expects this format on the wire", () => {
    const got = signBybit(SECRET, TIMESTAMP, API_KEY, PAYLOAD_GET);
    expect(got).toMatch(/^[0-9a-f]{64}$/);
  });
});

describe("bybitAuthHeaders", () => {
  it("returns the four X-BAPI-* headers + User-Agent", () => {
    const headers = bybitAuthHeaders(API_KEY, SECRET, TIMESTAMP, PAYLOAD_GET, USER_AGENT);
    expect(Object.keys(headers).sort()).toEqual([
      "User-Agent",
      "X-BAPI-API-KEY",
      "X-BAPI-RECV-WINDOW",
      "X-BAPI-SIGN",
      "X-BAPI-TIMESTAMP",
    ]);
  });

  it("X-BAPI-SIGN matches signBybit() for the same inputs", () => {
    const headers = bybitAuthHeaders(API_KEY, SECRET, TIMESTAMP, PAYLOAD_GET, USER_AGENT);
    expect(headers["X-BAPI-SIGN"]).toBe(signBybit(SECRET, TIMESTAMP, API_KEY, PAYLOAD_GET));
  });

  it("populates the simple-passthrough headers verbatim", () => {
    const headers = bybitAuthHeaders(API_KEY, SECRET, TIMESTAMP, PAYLOAD_GET, USER_AGENT);
    expect(headers["X-BAPI-API-KEY"]).toBe(API_KEY);
    expect(headers["X-BAPI-TIMESTAMP"]).toBe(TIMESTAMP);
    expect(headers["X-BAPI-RECV-WINDOW"]).toBe(BYBIT_RECV_WINDOW);
    expect(headers["User-Agent"]).toBe(USER_AGENT);
  });

  it("propagates a custom recvWindow into both X-BAPI-RECV-WINDOW and the signature", () => {
    const headers = bybitAuthHeaders(
      API_KEY,
      SECRET,
      TIMESTAMP,
      PAYLOAD_GET,
      USER_AGENT,
      "10000",
    );
    expect(headers["X-BAPI-RECV-WINDOW"]).toBe("10000");
    expect(headers["X-BAPI-SIGN"]).toBe(expectedSig(PAYLOAD_GET, "10000"));
  });

  it("does NOT leak the secret in any header", () => {
    const headers = bybitAuthHeaders(API_KEY, SECRET, TIMESTAMP, PAYLOAD_GET, USER_AGENT);
    for (const value of Object.values(headers)) {
      expect(value).not.toContain(SECRET);
    }
  });
});

describe("BYBIT_RECV_WINDOW", () => {
  it("is the legacy 5000ms value the inline copies all used", () => {
    // Pinning this prevents a quiet bump that would invalidate every
    // production signature on Bybit.
    expect(BYBIT_RECV_WINDOW).toBe("5000");
  });
});
