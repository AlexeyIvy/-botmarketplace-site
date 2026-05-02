/**
 * balanceReconciler — unit coverage (docs/55-T5).
 *
 * Mocks `decryptWithFallback` (so encrypted-secret payloads can be plain
 * strings in fixtures) and `globalThis.fetch` (so each test feeds canned
 * Bybit `/v5/position/list` + `/v5/account/wallet-balance` JSON). Pins:
 *
 *   1. Dual-key path  — both spot creds present ⇒ spot call uses spotApiKey,
 *      perp call uses linear apiKey, `spotKeyAvailable === true`.
 *   2. Single-key fallback — spot creds absent ⇒ both calls signed with the
 *      same linear apiKey, `spotKeyAvailable === false`.
 *   3. Classification — balanced / imbalanced / perp_only / spot_only / flat
 *      cover the five branches; tolerance = 0.5%.
 *   4. Error surface — non-zero `retCode` ⇒ `BalanceReconcilerError {cause:"api"}`.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../../src/lib/crypto.js", () => ({
  decryptWithFallback: (payload: string) => {
    // Convention used in this test: encrypted payloads are prefixed with
    // "enc:" — strip it to recover the "plaintext" the reconciler will
    // hand to HMAC. Anything else is returned verbatim.
    return payload.startsWith("enc:") ? payload.slice(4) : payload;
  },
}));

import {
  BalanceReconcilerError,
  baseAssetOf,
  reconcileBalances,
  type ExchangeConnectionCreds,
} from "../../../src/lib/exchange/balanceReconciler.js";

// ---------------------------------------------------------------------------
// Test scaffolding
// ---------------------------------------------------------------------------

const realFetch = globalThis.fetch;

interface FetchCall {
  url: string;
  apiKeyHeader: string;
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

/**
 * Routes by URL: `/v5/position/list` ⇒ perp body, `/v5/account/wallet-balance`
 * ⇒ spot body. Records every call so each test can assert which apiKey
 * signed which request.
 */
function installFetch(opts: {
  perp: unknown;
  spot: unknown;
  perpStatus?: number;
  spotStatus?: number;
}): FetchCall[] {
  const calls: FetchCall[] = [];
  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input.toString();
    const headers = (init?.headers ?? {}) as Record<string, string>;
    calls.push({ url, apiKeyHeader: headers["X-BAPI-API-KEY"] ?? "" });
    if (url.includes("/v5/position/list")) {
      return jsonResponse(opts.perp, opts.perpStatus ?? 200);
    }
    if (url.includes("/v5/account/wallet-balance")) {
      return jsonResponse(opts.spot, opts.spotStatus ?? 200);
    }
    return jsonResponse({ retCode: -1, retMsg: `Unhandled URL ${url}` }, 404);
  }) as typeof fetch;
  return calls;
}

beforeEach(() => {
  // No-op — each test installs its own fetch.
});

afterEach(() => {
  globalThis.fetch = realFetch;
});

// ---------------------------------------------------------------------------
// Fixture helpers
// ---------------------------------------------------------------------------

function dualKeyCreds(): ExchangeConnectionCreds {
  return {
    apiKey: "linear-key",
    encryptedSecret: "enc:linear-secret",
    spotApiKey: "spot-key",
    spotEncryptedSecret: "enc:spot-secret",
  };
}

function singleKeyCreds(): ExchangeConnectionCreds {
  return {
    apiKey: "linear-key",
    encryptedSecret: "enc:linear-secret",
    spotApiKey: null,
    spotEncryptedSecret: null,
  };
}

function perpListBody(items: Array<{ symbol: string; side: string; size: string }>) {
  return { retCode: 0, retMsg: "OK", result: { list: items } };
}

function walletBody(coins: Array<{ coin: string; walletBalance: string }>) {
  return { retCode: 0, retMsg: "OK", result: { list: [{ coin: coins }] } };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("baseAssetOf", () => {
  it("strips USDT/USDC/USD suffixes; passes through unknown", () => {
    expect(baseAssetOf("BTCUSDT")).toBe("BTC");
    expect(baseAssetOf("ETHUSDC")).toBe("ETH");
    expect(baseAssetOf("XRPUSD")).toBe("XRP");
    expect(baseAssetOf("DOGEEUR")).toBe("DOGEEUR");
  });
});

describe("reconcileBalances — dual-key path", () => {
  it("signs perp call with linear key + spot call with spot key; classifies balanced hedge", async () => {
    const calls = installFetch({
      perp: perpListBody([{ symbol: "BTCUSDT", side: "Sell", size: "1.0" }]),
      spot: walletBody([{ coin: "BTC", walletBalance: "1.0" }]),
    });

    const out = await reconcileBalances(dualKeyCreds(), ["BTCUSDT"]);

    expect(out.spotKeyAvailable).toBe(true);

    // Perp call signed with linear key; spot call with spot key.
    const perpCall = calls.find((c) => c.url.includes("/v5/position/list"))!;
    const spotCall = calls.find((c) => c.url.includes("/v5/account/wallet-balance"))!;
    expect(perpCall.apiKeyHeader).toBe("linear-key");
    expect(spotCall.apiKeyHeader).toBe("spot-key");

    // Maps populated.
    expect(out.perp.get("BTCUSDT")).toBe(-1.0); // Sell ⇒ negative
    expect(out.spot.get("BTC")).toBe(1.0);

    // Hedge status: -1 perp + 1 spot ⇒ balanced.
    expect(out.hedgeStatus).toHaveLength(1);
    expect(out.hedgeStatus[0]).toMatchObject({
      symbol: "BTCUSDT",
      perpQty: -1.0,
      spotQty: 1.0,
      status: "balanced",
      delta: 0,
    });
  });

  it("flags imbalanced hedge when |perp| - spot exceeds tolerance", async () => {
    installFetch({
      perp: perpListBody([{ symbol: "BTCUSDT", side: "Sell", size: "1.0" }]),
      spot: walletBody([{ coin: "BTC", walletBalance: "0.5" }]),
    });

    const out = await reconcileBalances(dualKeyCreds(), ["BTCUSDT"]);

    expect(out.hedgeStatus[0]).toMatchObject({
      symbol: "BTCUSDT",
      perpQty: -1.0,
      spotQty: 0.5,
      status: "imbalanced",
      delta: 0.5,
    });
  });
});

describe("reconcileBalances — single-key fallback", () => {
  it("signs both calls with linear key when spot creds are NULL; warns operator", async () => {
    const calls = installFetch({
      perp: perpListBody([{ symbol: "BTCUSDT", side: "Sell", size: "0.5" }]),
      spot: walletBody([{ coin: "BTC", walletBalance: "0.5" }]),
    });

    const out = await reconcileBalances(singleKeyCreds(), ["BTCUSDT"]);

    expect(out.spotKeyAvailable).toBe(false);
    expect(calls).toHaveLength(2);
    expect(calls[0].apiKeyHeader).toBe("linear-key");
    expect(calls[1].apiKeyHeader).toBe("linear-key");
    expect(out.hedgeStatus[0].status).toBe("balanced");
  });
});

describe("reconcileBalances — classification branches", () => {
  it("perp_only — perp open, no matching spot holding", async () => {
    installFetch({
      perp: perpListBody([{ symbol: "BTCUSDT", side: "Sell", size: "1.0" }]),
      spot: walletBody([]), // no BTC holding
    });

    const out = await reconcileBalances(dualKeyCreds(), ["BTCUSDT"]);

    expect(out.hedgeStatus[0]).toMatchObject({
      symbol: "BTCUSDT",
      perpQty: -1.0,
      spotQty: 0,
      status: "perp_only",
    });
    expect(out.hedgeStatus[0].delta).toBeUndefined();
  });

  it("spot_only — spot held, no matching perp position", async () => {
    installFetch({
      perp: perpListBody([]),
      spot: walletBody([{ coin: "ETH", walletBalance: "10" }]),
    });

    const out = await reconcileBalances(dualKeyCreds(), ["ETHUSDT"]);

    expect(out.hedgeStatus[0]).toMatchObject({
      symbol: "ETHUSDT",
      perpQty: 0,
      spotQty: 10,
      status: "spot_only",
    });
  });

  it("flat — neither side holds the symbol", async () => {
    installFetch({
      perp: perpListBody([]),
      spot: walletBody([{ coin: "USDT", walletBalance: "1000" }]),
    });

    const out = await reconcileBalances(dualKeyCreds(), ["BTCUSDT"]);

    expect(out.hedgeStatus[0].status).toBe("flat");
    expect(out.hedgeStatus[0].perpQty).toBe(0);
    expect(out.hedgeStatus[0].spotQty).toBe(0);
  });
});

describe("reconcileBalances — error surface", () => {
  it("throws BalanceReconcilerError {cause:'api'} when Bybit returns non-zero retCode", async () => {
    installFetch({
      perp: { retCode: 10003, retMsg: "Invalid signature", result: { list: [] } },
      spot: walletBody([]),
    });

    await expect(reconcileBalances(dualKeyCreds(), ["BTCUSDT"]))
      .rejects.toMatchObject({
        name: "BalanceReconcilerError",
        cause: "api",
        retCode: 10003,
      });
  });

  it("throws BalanceReconcilerError {cause:'http'} on non-2xx", async () => {
    installFetch({
      perp: perpListBody([]),
      spot: { whatever: true },
      spotStatus: 503,
    });

    await expect(reconcileBalances(dualKeyCreds(), ["BTCUSDT"]))
      .rejects.toMatchObject({
        name: "BalanceReconcilerError",
        cause: "http",
        statusCode: 503,
      });
  });
});
