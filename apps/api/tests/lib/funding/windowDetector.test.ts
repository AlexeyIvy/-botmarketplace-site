/**
 * windowDetector — unit coverage (docs/55-T4 follow-up).
 *
 * Mocks prisma.fundingSnapshot.findFirst to feed canned `nextFundingAt`
 * values, then pins the entry / payment signals at carefully-chosen
 * `now` offsets. Confirms:
 *
 *   1. No snapshot present → both signals false, nextFundingAtMs null.
 *   2. now >> nextFundingAt → both signals false (stale snapshot,
 *      payment window has long since closed).
 *   3. now ∈ (next - 30min, next) → entry window OPEN, payment false.
 *   4. now ∈ (next - 31min, next - 30min) → both false (one minute
 *      before the entry window opens — pin the boundary).
 *   5. now ∈ (next + 1min, next + 30min) → payment received, entry false.
 *   6. now > next + 30min → both false (payment window closed).
 *   7. Exact boundaries — `now == next` → both false (atomic settlement
 *      window; need at least the lag buffer to claim "received").
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

let canned: { nextFundingAt: Date } | null = null;

vi.mock("../../../src/lib/prisma.js", () => ({
  prisma: {
    fundingSnapshot: {
      findFirst: vi.fn(async () => canned),
    },
  },
}));

import {
  detectFundingWindow,
  ENTRY_PRE_BUFFER_MS,
  PAYMENT_LAG_MS,
  PAYMENT_WINDOW_MS,
} from "../../../src/lib/funding/windowDetector.js";

const NEXT_FUNDING_MS = Date.UTC(2026, 4, 2, 16, 0, 0); // 2026-05-02T16:00:00Z
const NEXT_FUNDING_DATE = new Date(NEXT_FUNDING_MS);

beforeEach(() => {
  canned = { nextFundingAt: NEXT_FUNDING_DATE };
});

afterEach(() => {
  canned = null;
});

describe("detectFundingWindow — no snapshot", () => {
  it("returns all-false / null when fundingSnapshot.findFirst yields nothing", async () => {
    canned = null;
    const out = await detectFundingWindow("BTCUSDT", NEXT_FUNDING_MS - 60_000);
    expect(out).toMatchObject({
      open: false,
      paymentReceived: false,
      nextFundingAtMs: null,
    });
    // Without a snapshot the source is "proxy" — there is nothing for the
    // ledger path to anchor a query window to, so it never runs.
    expect(out.paymentSource).toBe("proxy");
  });
});

describe("detectFundingWindow — entry window", () => {
  it("OPEN when now is 1 minute before funding", async () => {
    const out = await detectFundingWindow("BTCUSDT", NEXT_FUNDING_MS - 60_000);
    expect(out.open).toBe(true);
    expect(out.paymentReceived).toBe(false);
    expect(out.nextFundingAtMs).toBe(NEXT_FUNDING_MS);
  });

  it("OPEN at the exact pre-buffer boundary (now = next - 30min)", async () => {
    const out = await detectFundingWindow("BTCUSDT", NEXT_FUNDING_MS - ENTRY_PRE_BUFFER_MS);
    expect(out.open).toBe(true);
  });

  it("CLOSED 1ms before the entry window opens", async () => {
    const out = await detectFundingWindow("BTCUSDT", NEXT_FUNDING_MS - ENTRY_PRE_BUFFER_MS - 1);
    expect(out.open).toBe(false);
    expect(out.paymentReceived).toBe(false);
  });
});

describe("detectFundingWindow — payment window", () => {
  it("OPEN at PAYMENT_LAG_MS after funding", async () => {
    const out = await detectFundingWindow("BTCUSDT", NEXT_FUNDING_MS + PAYMENT_LAG_MS);
    expect(out.open).toBe(false);
    expect(out.paymentReceived).toBe(true);
  });

  it("OPEN at the far edge (next + PAYMENT_WINDOW_MS)", async () => {
    const out = await detectFundingWindow("BTCUSDT", NEXT_FUNDING_MS + PAYMENT_WINDOW_MS);
    expect(out.paymentReceived).toBe(true);
  });

  it("CLOSED 1ms beyond the payment window", async () => {
    const out = await detectFundingWindow("BTCUSDT", NEXT_FUNDING_MS + PAYMENT_WINDOW_MS + 1);
    expect(out.paymentReceived).toBe(false);
    expect(out.open).toBe(false);
  });

  it("CLOSED in the gap between funding and the lag (now < next + LAG)", async () => {
    const out = await detectFundingWindow("BTCUSDT", NEXT_FUNDING_MS + 30_000);
    expect(out.paymentReceived).toBe(false);
    expect(out.open).toBe(false);
  });
});

describe("detectFundingWindow — exact funding moment", () => {
  it("now == nextFundingAt → both false (atomic settlement)", async () => {
    const out = await detectFundingWindow("BTCUSDT", NEXT_FUNDING_MS);
    expect(out).toMatchObject({ open: false, paymentReceived: false });
  });
});

// ---------------------------------------------------------------------------
// Real-ledger path (creds passed) — overrides the timestamp proxy.
// ---------------------------------------------------------------------------

interface LedgerCall {
  url: string;
  apiKey: string;
}

const realFetch = globalThis.fetch;

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function installLedgerFetch(opts: {
  body?: unknown;
  status?: number;
  bodyFn?: (call: LedgerCall) => unknown;
}): LedgerCall[] {
  const calls: LedgerCall[] = [];
  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input.toString();
    const headers = (init?.headers ?? {}) as Record<string, string>;
    const call = { url, apiKey: headers["X-BAPI-API-KEY"] ?? "" };
    calls.push(call);
    const body = opts.bodyFn ? opts.bodyFn(call) : opts.body;
    return jsonResponse(body, opts.status ?? 200);
  }) as typeof fetch;
  return calls;
}

afterEach(() => {
  globalThis.fetch = realFetch;
});

const TEST_CREDS = { apiKey: "test-key", secret: "test-secret" };

describe("detectFundingWindow — ledger path (creds supplied)", () => {
  it("ledger has SETTLEMENT row → paymentReceived=true, paymentSource='ledger'", async () => {
    const calls = installLedgerFetch({
      body: {
        retCode: 0,
        retMsg: "OK",
        result: {
          list: [
            {
              symbol: "BTCUSDT",
              type: "SETTLEMENT",
              transactionTime: String(NEXT_FUNDING_MS + 5_000),
            },
          ],
        },
      },
    });

    const out = await detectFundingWindow(
      "BTCUSDT",
      NEXT_FUNDING_MS + 5 * 60_000,
      { creds: TEST_CREDS },
    );

    expect(out.paymentReceived).toBe(true);
    expect(out.paymentSource).toBe("ledger");
    expect(out.nextFundingAtMs).toBe(NEXT_FUNDING_MS);
    expect(calls).toHaveLength(1);
    expect(calls[0]?.url).toContain("/v5/account/transaction-log");
    expect(calls[0]?.url).toContain("symbol=BTCUSDT");
    expect(calls[0]?.url).toContain("type=SETTLEMENT");
    expect(calls[0]?.apiKey).toBe("test-key");
  });

  it("ledger empty → paymentReceived=false even when timestamp proxy would say true", async () => {
    // now is INSIDE the proxy window (would have returned true), but
    // ledger is empty — authoritative override.
    installLedgerFetch({
      body: { retCode: 0, retMsg: "OK", result: { list: [] } },
    });

    const out = await detectFundingWindow(
      "BTCUSDT",
      NEXT_FUNDING_MS + 5 * 60_000,
      { creds: TEST_CREDS },
    );

    expect(out.paymentReceived).toBe(false);
    expect(out.paymentSource).toBe("ledger-empty");
  });

  it("ledger HTTP error → falls back to timestamp proxy + paymentSource='proxy'", async () => {
    installLedgerFetch({ body: { retCode: 0, result: {} }, status: 503 });

    const out = await detectFundingWindow(
      "BTCUSDT",
      NEXT_FUNDING_MS + 5 * 60_000,
      { creds: TEST_CREDS },
    );

    // proxy says paymentReceived=true at this offset; we get that.
    expect(out.paymentReceived).toBe(true);
    expect(out.paymentSource).toBe("proxy");
  });

  it("ledger retCode != 0 → falls back to timestamp proxy", async () => {
    installLedgerFetch({
      body: { retCode: 10001, retMsg: "params error" },
    });

    const out = await detectFundingWindow(
      "BTCUSDT",
      NEXT_FUNDING_MS + 5 * 60_000,
      { creds: TEST_CREDS },
    );

    expect(out.paymentReceived).toBe(true); // proxy fallback
    expect(out.paymentSource).toBe("proxy");
  });

  it("pre-settlement (sinceFunding ≤ 0) → no ledger call, paymentReceived=false", async () => {
    const calls = installLedgerFetch({
      body: { retCode: 0, result: { list: [] } },
    });

    // 1 minute BEFORE funding — we are inside the entry window, but the
    // ledger query is meaningless because no payment can have landed yet.
    const out = await detectFundingWindow(
      "BTCUSDT",
      NEXT_FUNDING_MS - 60_000,
      { creds: TEST_CREDS },
    );

    expect(out.open).toBe(true);
    expect(out.paymentReceived).toBe(false);
    expect(out.paymentSource).toBe("proxy");
    expect(calls).toHaveLength(0);
  });

  it("ledger row for a different symbol → paymentReceived=false (filter pinned)", async () => {
    installLedgerFetch({
      body: {
        retCode: 0,
        result: {
          list: [
            {
              symbol: "ETHUSDT",
              type: "SETTLEMENT",
              transactionTime: String(NEXT_FUNDING_MS + 5_000),
            },
          ],
        },
      },
    });

    const out = await detectFundingWindow(
      "BTCUSDT",
      NEXT_FUNDING_MS + 5 * 60_000,
      { creds: TEST_CREDS },
    );

    expect(out.paymentReceived).toBe(false);
    expect(out.paymentSource).toBe("ledger-empty");
  });

  it("no snapshot + creds supplied → no ledger call (nothing to anchor window to)", async () => {
    canned = null;
    const calls = installLedgerFetch({ body: { retCode: 0, result: { list: [] } } });

    const out = await detectFundingWindow("BTCUSDT", NEXT_FUNDING_MS + 5 * 60_000, {
      creds: TEST_CREDS,
    });

    expect(out.paymentReceived).toBe(false);
    expect(out.nextFundingAtMs).toBeNull();
    expect(calls).toHaveLength(0);
  });
});

describe("detectFundingWindow — far future / past", () => {
  it("hours after the payment window → both false", async () => {
    const out = await detectFundingWindow("BTCUSDT", NEXT_FUNDING_MS + 4 * 60 * 60_000);
    expect(out.open).toBe(false);
    expect(out.paymentReceived).toBe(false);
  });

  it("days before the funding event → both false", async () => {
    const out = await detectFundingWindow("BTCUSDT", NEXT_FUNDING_MS - 2 * 24 * 60 * 60_000);
    expect(out.open).toBe(false);
    expect(out.paymentReceived).toBe(false);
  });
});
