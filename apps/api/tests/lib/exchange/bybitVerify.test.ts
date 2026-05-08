/**
 * Unit tests for `bybitVerifyApiKey` — covers every branch in the result
 * matrix: success (with and without expiry), Bybit error retCode, HTTP
 * non-2xx, malformed body, network error, timeout, env detection.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

import { bybitVerifyApiKey } from "../../../src/lib/exchange/bybitVerify.js";

const ORIGINAL_ENV = { ...process.env };

beforeEach(() => {
  process.env = { ...ORIGINAL_ENV };
  // Force demo env for predictable URL/permission checks.
  delete process.env.BYBIT_BASE_URL;
  delete process.env.BYBIT_ENV;
});

afterEach(() => {
  process.env = { ...ORIGINAL_ENV };
});

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("bybitVerifyApiKey — success paths", () => {
  it("returns ok=true with flattened permissions, env=demo, parsed expiry", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        retCode: 0,
        retMsg: "",
        result: {
          apiKey: "key-1",
          readOnly: 0,
          expiredAt: "2026-12-31T00:00:00Z",
          permissions: {
            ContractTrade: ["Order", "Position"],
            Spot: ["SpotTrade"],
            BlockTrade: [],
          },
        },
      }),
    );

    const out = await bybitVerifyApiKey("key-1", "secret-1", fetchMock);

    expect(out.ok).toBe(true);
    if (!out.ok) throw new Error("expected ok");
    expect(out.env).toBe("demo");
    expect(out.readOnly).toBe(false);
    expect(out.expiresAt).toBe("2026-12-31T00:00:00Z");
    expect(out.permissions).toEqual([
      "ContractTrade:Order",
      "ContractTrade:Position",
      "Spot:SpotTrade",
    ]);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url] = fetchMock.mock.calls[0];
    expect(url).toBe("https://api-demo.bybit.com/v5/user/query-api");
  });

  it("returns env=live when BYBIT_ENV=live", async () => {
    process.env.BYBIT_ENV = "live";
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        retCode: 0,
        result: { permissions: {}, readOnly: 1 },
      }),
    );

    const out = await bybitVerifyApiKey("k", "s", fetchMock);
    if (!out.ok) throw new Error("expected ok");
    expect(out.env).toBe("live");
    expect(out.readOnly).toBe(true);
  });

  it("normalises expiredAt='0' to null", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        retCode: 0,
        result: { permissions: {}, expiredAt: "0", readOnly: 0 },
      }),
    );
    const out = await bybitVerifyApiKey("k", "s", fetchMock);
    if (!out.ok) throw new Error("expected ok");
    expect(out.expiresAt).toBeNull();
  });

  it("normalises absent expiredAt to null", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        retCode: 0,
        result: { permissions: {}, readOnly: 0 },
      }),
    );
    const out = await bybitVerifyApiKey("k", "s", fetchMock);
    if (!out.ok) throw new Error("expected ok");
    expect(out.expiresAt).toBeNull();
  });
});

describe("bybitVerifyApiKey — failure paths", () => {
  it("Bybit retCode!=0 → ok=false code=BYBIT", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        retCode: 33004,
        retMsg: "Your api key has expired.",
      }),
    );
    const out = await bybitVerifyApiKey("k", "s", fetchMock);
    expect(out.ok).toBe(false);
    if (out.ok) throw new Error("expected failure");
    expect(out.code).toBe("BYBIT");
    expect(out.retCode).toBe(33004);
    expect(out.detail).toContain("33004");
    expect(out.detail).toContain("expired");
  });

  it("HTTP 401 → ok=false code=HTTP", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response("forbidden", { status: 401, statusText: "Unauthorized" }),
    );
    const out = await bybitVerifyApiKey("k", "s", fetchMock);
    expect(out.ok).toBe(false);
    if (out.ok) throw new Error("expected failure");
    expect(out.code).toBe("HTTP");
    expect(out.httpStatus).toBe(401);
  });

  it("non-JSON body → ok=false code=MALFORMED", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response("<html>oops</html>", { status: 200, headers: { "Content-Type": "text/html" } }),
    );
    const out = await bybitVerifyApiKey("k", "s", fetchMock);
    expect(out.ok).toBe(false);
    if (out.ok) throw new Error("expected failure");
    expect(out.code).toBe("MALFORMED");
  });

  it("retCode=0 but no result → ok=false code=MALFORMED", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({ retCode: 0, retMsg: "" }),
    );
    const out = await bybitVerifyApiKey("k", "s", fetchMock);
    expect(out.ok).toBe(false);
    if (out.ok) throw new Error("expected failure");
    expect(out.code).toBe("MALFORMED");
  });

  it("retCode missing → ok=false code=MALFORMED", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ result: {} }));
    const out = await bybitVerifyApiKey("k", "s", fetchMock);
    expect(out.ok).toBe(false);
    if (out.ok) throw new Error("expected failure");
    expect(out.code).toBe("MALFORMED");
  });

  it("network error → ok=false code=NETWORK", async () => {
    const fetchMock = vi.fn().mockRejectedValue(new Error("ECONNREFUSED"));
    const out = await bybitVerifyApiKey("k", "s", fetchMock);
    expect(out.ok).toBe(false);
    if (out.ok) throw new Error("expected failure");
    expect(out.code).toBe("NETWORK");
    expect(out.detail).toContain("ECONNREFUSED");
  });

  it("AbortError → ok=false code=TIMEOUT", async () => {
    const fetchMock = vi.fn().mockImplementation(() => {
      const err = new Error("aborted");
      (err as { name?: string }).name = "AbortError";
      return Promise.reject(err);
    });
    const out = await bybitVerifyApiKey("k", "s", fetchMock);
    expect(out.ok).toBe(false);
    if (out.ok) throw new Error("expected failure");
    expect(out.code).toBe("TIMEOUT");
  });
});

describe("bybitVerifyApiKey — request shape", () => {
  it("sends signed GET with X-BAPI-* headers, no body", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({ retCode: 0, result: { permissions: {}, readOnly: 0 } }),
    );

    await bybitVerifyApiKey("api-key-xyz", "secret-xyz", fetchMock);

    const [, init] = fetchMock.mock.calls[0];
    expect(init.method).toBe("GET");
    expect(init.body).toBeUndefined();
    const headers = init.headers as Record<string, string>;
    expect(headers["X-BAPI-API-KEY"]).toBe("api-key-xyz");
    expect(headers["X-BAPI-SIGN"]).toMatch(/^[a-f0-9]{64}$/);
    expect(headers["X-BAPI-TIMESTAMP"]).toMatch(/^\d+$/);
    expect(headers["X-BAPI-RECV-WINDOW"]).toBe("5000");
    expect(headers["User-Agent"]).toBe("botmarketplace-verify/1");
  });
});
