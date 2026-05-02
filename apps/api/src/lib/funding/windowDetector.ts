/**
 * Funding-window detector — derives the two upstream signals the
 * funding-arb runtime needs (`fundingWindowOpen`, `fundingPaymentReceived`)
 * from the most recent `FundingSnapshot.nextFundingAt` for a symbol.
 *
 * This is the timestamp-based approximation. The "real" payment check
 * (Bybit `/v5/account/transaction-log` query) lands with docs/55-T2
 * once private API wiring is complete; until then the worker treats
 * the funding event timestamp itself as the proxy for "payment landed",
 * with a small lag buffer to absorb settlement latency.
 *
 * Bybit perpetual funding settles every 8 hours (00:00, 08:00, 16:00 UTC).
 * `FundingSnapshot.nextFundingAt` is populated by the ingestion cron
 * every 8 hours (`apps/api/src/lib/funding/ingestJob.ts`); the value is
 * read-only here — we never write to it.
 *
 * Window definitions:
 *   - Entry window: `nextFundingAt - now ∈ (0, ENTRY_PRE_BUFFER_MS]`.
 *     Opens 30 minutes before the funding event by default. Pre-buffer
 *     keeps the worker from racing the settlement tick.
 *   - Payment window: `now - nextFundingAt ∈ [PAYMENT_LAG_MS, PAYMENT_WINDOW_MS]`.
 *     Treats funding as "received" 1 minute after settlement and stays
 *     open for 30 minutes — long enough for a tick (60s cadence) to
 *     pick it up at least once but short enough that a stale snapshot
 *     does not falsely re-trigger an exit on a hedge that already
 *     closed.
 */

import { prisma } from "../prisma.js";

export const ENTRY_PRE_BUFFER_MS = 30 * 60_000; // 30 min before funding
export const PAYMENT_LAG_MS = 60_000;           // 1 min after funding
export const PAYMENT_WINDOW_MS = 30 * 60_000;   // 30 min payment window

export interface FundingWindow {
  /** True when `now` is in the entry pre-buffer (before settlement). */
  open: boolean;
  /** True when settlement has cleared and the payment window is still open. */
  paymentReceived: boolean;
  /** ms epoch of the next funding settlement, or null if no snapshot. */
  nextFundingAtMs: number | null;
}

/**
 * Read the latest `FundingSnapshot.nextFundingAt` for `symbol` and
 * derive the entry / payment signals at `nowMs`.
 *
 * Returns `{ open: false, paymentReceived: false, nextFundingAtMs: null }`
 * when no snapshot exists for the symbol (the funding ingestion cron
 * has not seen it yet, or symbol is not on Bybit perpetuals).
 */
export async function detectFundingWindow(
  symbol: string,
  nowMs: number,
): Promise<FundingWindow> {
  const snap = await prisma.fundingSnapshot.findFirst({
    where: { symbol },
    orderBy: { timestamp: "desc" },
    select: { nextFundingAt: true },
  });
  if (!snap) {
    return { open: false, paymentReceived: false, nextFundingAtMs: null };
  }

  const nextFundingAtMs = snap.nextFundingAt.getTime();
  const untilFunding = nextFundingAtMs - nowMs;
  const sinceFunding = nowMs - nextFundingAtMs;

  return {
    open: untilFunding > 0 && untilFunding <= ENTRY_PRE_BUFFER_MS,
    paymentReceived:
      sinceFunding >= PAYMENT_LAG_MS && sinceFunding <= PAYMENT_WINDOW_MS,
    nextFundingAtMs,
  };
}
