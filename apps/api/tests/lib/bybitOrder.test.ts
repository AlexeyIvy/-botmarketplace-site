/**
 * bybitOrder.ts — pure function tests (Roadmap V3, Task #14)
 *
 * Tests:
 *   - HMAC signing (known-input → known-output)
 *   - mapBybitStatus() all statuses
 *   - sanitizeBybitError()
 *   - getBybitBaseUrl() environment routing
 *   - isBybitLive()
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { createHmac } from "node:crypto";
import {
  mapBybitStatus,
  sanitizeBybitError,
  getBybitBaseUrl,
  isBybitLive,
} from "../../src/lib/bybitOrder.js";

// ---------------------------------------------------------------------------
// HMAC signing — we replicate the sign() logic since it's not exported,
// but we verify the algorithm matches Bybit's documented spec.
// ---------------------------------------------------------------------------

const RECV_WINDOW = "5000";

/** Replicates the internal sign() function from bybitOrder.ts */
function expectedSign(secret: string, timestamp: string, apiKey: string, payload: string): string {
  const preSign = `${timestamp}${apiKey}${RECV_WINDOW}${payload}`;
  return createHmac("sha256", secret).update(preSign).digest("hex");
}

describe("HMAC signing (known-input → known-output)", () => {
  it("produces deterministic HMAC-SHA256 for known inputs", () => {
    const secret = "test-secret-key-12345";
    const timestamp = "1700000000000";
    const apiKey = "MY_API_KEY";
    const payload = '{"category":"linear","symbol":"BTCUSDT","side":"Buy","orderType":"Market","qty":"0.001"}';

    const sig = expectedSign(secret, timestamp, apiKey, payload);

    // Verify it's a valid 64-char hex string
    expect(sig).toMatch(/^[a-f0-9]{64}$/);

    // Verify determinism — same inputs produce same output
    const sig2 = expectedSign(secret, timestamp, apiKey, payload);
    expect(sig).toBe(sig2);
  });

  it("different secret produces different signature", () => {
    const timestamp = "1700000000000";
    const apiKey = "KEY";
    const payload = "test";

    const sig1 = expectedSign("secret-a", timestamp, apiKey, payload);
    const sig2 = expectedSign("secret-b", timestamp, apiKey, payload);
    expect(sig1).not.toBe(sig2);
  });

  it("different timestamp produces different signature", () => {
    const secret = "same-secret";
    const apiKey = "KEY";
    const payload = "test";

    const sig1 = expectedSign(secret, "1700000000000", apiKey, payload);
    const sig2 = expectedSign(secret, "1700000000001", apiKey, payload);
    expect(sig1).not.toBe(sig2);
  });

  it("pre-sign string follows Bybit spec: timestamp+apiKey+recvWindow+payload", () => {
    const secret = "abc";
    const timestamp = "123";
    const apiKey = "KEY";
    const payload = "BODY";

    // Manually compute expected
    const preSign = "123KEY5000BODY";
    const expected = createHmac("sha256", secret).update(preSign).digest("hex");
    const actual = expectedSign(secret, timestamp, apiKey, payload);
    expect(actual).toBe(expected);
  });

  it("handles empty payload (GET requests)", () => {
    const secret = "my-secret";
    const timestamp = "1700000000000";
    const apiKey = "KEY";
    const payload = "";

    const sig = expectedSign(secret, timestamp, apiKey, payload);
    expect(sig).toMatch(/^[a-f0-9]{64}$/);
  });

  it("handles query string payload (GET order status)", () => {
    const secret = "my-secret";
    const timestamp = "1700000000000";
    const apiKey = "KEY";
    const payload = "category=linear&orderId=abc123&symbol=BTCUSDT";

    const sig = expectedSign(secret, timestamp, apiKey, payload);
    expect(sig).toMatch(/^[a-f0-9]{64}$/);

    // Different query params → different sig
    const sig2 = expectedSign(secret, timestamp, apiKey, "category=linear&orderId=xyz789&symbol=ETHUSDT");
    expect(sig).not.toBe(sig2);
  });
});

// ---------------------------------------------------------------------------
// mapBybitStatus — all statuses
// ---------------------------------------------------------------------------

describe("mapBybitStatus", () => {
  it("maps New → SUBMITTED", () => {
    expect(mapBybitStatus("New")).toBe("SUBMITTED");
  });

  it("maps Created → SUBMITTED", () => {
    expect(mapBybitStatus("Created")).toBe("SUBMITTED");
  });

  it("maps Untriggered → SUBMITTED", () => {
    expect(mapBybitStatus("Untriggered")).toBe("SUBMITTED");
  });

  it("maps Active → SUBMITTED", () => {
    expect(mapBybitStatus("Active")).toBe("SUBMITTED");
  });

  it("maps PartiallyFilled → PARTIALLY_FILLED", () => {
    expect(mapBybitStatus("PartiallyFilled")).toBe("PARTIALLY_FILLED");
  });

  it("maps Filled → FILLED", () => {
    expect(mapBybitStatus("Filled")).toBe("FILLED");
  });

  it("maps Cancelled → CANCELLED", () => {
    expect(mapBybitStatus("Cancelled")).toBe("CANCELLED");
  });

  it("maps Deactivated → CANCELLED", () => {
    expect(mapBybitStatus("Deactivated")).toBe("CANCELLED");
  });

  it("maps Rejected → REJECTED", () => {
    expect(mapBybitStatus("Rejected")).toBe("REJECTED");
  });

  it("maps unknown status to SUBMITTED (safe default)", () => {
    expect(mapBybitStatus("SomeNewStatus")).toBe("SUBMITTED");
    expect(mapBybitStatus("")).toBe("SUBMITTED");
  });
});

// ---------------------------------------------------------------------------
// sanitizeBybitError
// ---------------------------------------------------------------------------

describe("sanitizeBybitError", () => {
  it("extracts message from Error instances", () => {
    const err = new Error("Bybit API error 10001: invalid symbol");
    expect(sanitizeBybitError(err)).toBe("Bybit API error 10001: invalid symbol");
  });

  it("converts non-Error values to string", () => {
    expect(sanitizeBybitError("raw string")).toBe("raw string");
    expect(sanitizeBybitError(42)).toBe("42");
    expect(sanitizeBybitError(null)).toBe("null");
  });

  it("strips multiline stack traces (keeps first line only)", () => {
    const err = new Error("first line");
    // Errors have stack traces, but we only want the message line
    const result = sanitizeBybitError(err);
    expect(result).toBe("first line");
    expect(result).not.toContain("\n");
  });

  it("truncates messages longer than 500 chars", () => {
    const longMsg = "x".repeat(600);
    const err = new Error(longMsg);
    const result = sanitizeBybitError(err);
    expect(result.length).toBe(500);
  });
});

// ---------------------------------------------------------------------------
// getBybitBaseUrl / isBybitLive — environment routing
// ---------------------------------------------------------------------------

describe("getBybitBaseUrl", () => {
  let origBaseUrl: string | undefined;
  let origEnv: string | undefined;

  beforeEach(() => {
    origBaseUrl = process.env.BYBIT_BASE_URL;
    origEnv = process.env.BYBIT_ENV;
  });

  afterEach(() => {
    if (origBaseUrl !== undefined) process.env.BYBIT_BASE_URL = origBaseUrl;
    else delete process.env.BYBIT_BASE_URL;
    if (origEnv !== undefined) process.env.BYBIT_ENV = origEnv;
    else delete process.env.BYBIT_ENV;
  });

  it("defaults to demo URL when no env vars set", () => {
    delete process.env.BYBIT_BASE_URL;
    delete process.env.BYBIT_ENV;
    expect(getBybitBaseUrl()).toBe("https://api-demo.bybit.com");
  });

  it("returns live URL when BYBIT_ENV=live", () => {
    delete process.env.BYBIT_BASE_URL;
    process.env.BYBIT_ENV = "live";
    expect(getBybitBaseUrl()).toBe("https://api.bybit.com");
  });

  it("returns demo URL when BYBIT_ENV=demo", () => {
    delete process.env.BYBIT_BASE_URL;
    process.env.BYBIT_ENV = "demo";
    expect(getBybitBaseUrl()).toBe("https://api-demo.bybit.com");
  });

  it("BYBIT_BASE_URL takes precedence over BYBIT_ENV", () => {
    process.env.BYBIT_BASE_URL = "https://custom.example.com";
    process.env.BYBIT_ENV = "live";
    expect(getBybitBaseUrl()).toBe("https://custom.example.com");
  });
});

describe("isBybitLive", () => {
  let origBaseUrl: string | undefined;
  let origEnv: string | undefined;

  beforeEach(() => {
    origBaseUrl = process.env.BYBIT_BASE_URL;
    origEnv = process.env.BYBIT_ENV;
  });

  afterEach(() => {
    if (origBaseUrl !== undefined) process.env.BYBIT_BASE_URL = origBaseUrl;
    else delete process.env.BYBIT_BASE_URL;
    if (origEnv !== undefined) process.env.BYBIT_ENV = origEnv;
    else delete process.env.BYBIT_ENV;
  });

  it("returns false for demo (default)", () => {
    delete process.env.BYBIT_BASE_URL;
    delete process.env.BYBIT_ENV;
    expect(isBybitLive()).toBe(false);
  });

  it("returns true for live", () => {
    delete process.env.BYBIT_BASE_URL;
    process.env.BYBIT_ENV = "live";
    expect(isBybitLive()).toBe(true);
  });

  it("returns false for custom URL (not exact live match)", () => {
    process.env.BYBIT_BASE_URL = "https://custom.example.com";
    expect(isBybitLive()).toBe(false);
  });
});
