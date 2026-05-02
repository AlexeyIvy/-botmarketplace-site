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
    expect(out).toEqual({ open: false, paymentReceived: false, nextFundingAtMs: null });
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
