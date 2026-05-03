/**
 * Funding-window detector — derives the two upstream signals the
 * funding-arb runtime needs (`fundingWindowOpen`, `fundingPaymentReceived`)
 * for a symbol at a given moment in time.
 *
 * Two layers:
 *
 *   1. Timestamp proxy (no creds path).
 *      Reads the most recent `FundingSnapshot.nextFundingAt` for the
 *      symbol and approximates payment-received based on `nowMs - next`.
 *      This is the path that runs when no Bybit credentials are
 *      available (tests, demo workspaces, ExchangeConnection without
 *      private API access). Behaviour is unchanged from the original
 *      55-T4 implementation so that existing callers — including the
 *      windowDetector unit suite — keep their assumptions intact.
 *
 *   2. Real ledger query (creds path, this PR).
 *      When the caller supplies decrypted Bybit credentials, the
 *      proxy `paymentReceived` signal is replaced by an authoritative
 *      check against `/v5/account/transaction-log` filtered to
 *      `category=linear`, `type=SETTLEMENT`, the funding event symbol,
 *      and the time window (`nextFundingAt - 60s`, `nowMs`]. A
 *      SETTLEMENT row in that window proves the funding payment landed;
 *      no row means it has not, regardless of what the timestamp proxy
 *      would have said. Transient ledger errors (HTTP non-OK, parse
 *      failure, retCode != 0) fall back to the timestamp proxy with a
 *      warning log — the worker must keep ticking even when Bybit's
 *      private API is briefly unhappy.
 *
 * Bybit perpetual funding settles every 8 hours (00:00, 08:00, 16:00 UTC).
 * The ingestion cron (`apps/api/src/lib/funding/ingestJob.ts`) populates
 * `FundingSnapshot.nextFundingAt`; this module is read-only on that table.
 */

import { createHmac } from "node:crypto";
import { prisma } from "../prisma.js";
import { getBybitBaseUrl } from "../bybitOrder.js";
import { logger } from "../logger.js";

const log = logger.child({ module: "windowDetector" });

export const ENTRY_PRE_BUFFER_MS = 30 * 60_000; // 30 min before funding
export const PAYMENT_LAG_MS = 60_000;           // 1 min after funding
export const PAYMENT_WINDOW_MS = 30 * 60_000;   // 30 min payment window

const RECV_WINDOW = "5000";
const USER_AGENT = "botmarketplace-funding/1";
/** Pull a few rows in case multiple SETTLEMENT events land in the same
 *  query window; we only need to know that ≥1 matches. Bybit's max here
 *  is 50; 10 is a comfortable cushion without paying for what we don't read. */
const LEDGER_PAGE_LIMIT = "10";

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

/** Decrypted Bybit credentials for the linear scope. Funding settles on
 *  the perpetual side, so the linear pair is always the right one to sign
 *  the ledger query — no spot-key fallback needed here. */
export interface FundingLedgerCreds {
  apiKey: string;
  /** Plaintext secret. Caller is responsible for decryption. */
  secret: string;
}

export interface DetectFundingWindowOptions {
  /** When provided AND the symbol has a `FundingSnapshot`, the
   *  `paymentReceived` signal is sourced from a real Bybit
   *  `/v5/account/transaction-log` query. Without creds the timestamp
   *  proxy is used (legacy behaviour). */
  creds?: FundingLedgerCreds;
}

export interface FundingWindow {
  /** True when `now` is in the entry pre-buffer (before settlement). */
  open: boolean;
  /** True when the funding payment has landed AND we are still inside
   *  the (creds path: real-ledger) / (proxy path: 30-min) post-window. */
  paymentReceived: boolean;
  /** ms epoch of the next funding settlement, or null if no snapshot. */
  nextFundingAtMs: number | null;
  /** Where `paymentReceived` came from. Useful for operator dashboards
   *  + debugging "why did my hedge not exit yet". */
  paymentSource: "ledger" | "ledger-empty" | "proxy";
}

// ---------------------------------------------------------------------------
// Public entry-point
// ---------------------------------------------------------------------------

/**
 * Read the latest `FundingSnapshot.nextFundingAt` for `symbol` and
 * derive the entry / payment signals at `nowMs`. When `options.creds`
 * is supplied, `paymentReceived` is sourced from the Bybit ledger
 * (authoritative); otherwise the timestamp proxy is used.
 *
 * Returns `{ open: false, paymentReceived: false, nextFundingAtMs: null,
 * paymentSource: "proxy" }` when no snapshot exists for the symbol —
 * the caller has nothing to anchor the time window to, so consulting
 * the ledger would be meaningless.
 */
export async function detectFundingWindow(
  symbol: string,
  nowMs: number,
  options: DetectFundingWindowOptions = {},
): Promise<FundingWindow> {
  const snap = await prisma.fundingSnapshot.findFirst({
    where: { symbol },
    orderBy: { timestamp: "desc" },
    select: { nextFundingAt: true },
  });
  if (!snap) {
    return {
      open: false,
      paymentReceived: false,
      nextFundingAtMs: null,
      paymentSource: "proxy",
    };
  }

  const nextFundingAtMs = snap.nextFundingAt.getTime();
  const untilFunding = nextFundingAtMs - nowMs;
  const sinceFunding = nowMs - nextFundingAtMs;

  const open = untilFunding > 0 && untilFunding <= ENTRY_PRE_BUFFER_MS;
  const proxyPaymentReceived =
    sinceFunding >= PAYMENT_LAG_MS && sinceFunding <= PAYMENT_WINDOW_MS;

  // No-creds path → unchanged legacy behaviour.
  if (!options.creds) {
    return {
      open,
      paymentReceived: proxyPaymentReceived,
      nextFundingAtMs,
      paymentSource: "proxy",
    };
  }

  // Pre-settlement: no payment can possibly exist on Bybit's books yet,
  // so skip the network call entirely.
  if (sinceFunding <= 0) {
    return { open, paymentReceived: false, nextFundingAtMs, paymentSource: "proxy" };
  }

  // Creds path: query the ledger. On any error, fall back to the
  // timestamp proxy + log — the worker must keep ticking.
  try {
    const settled = await queryFundingLedger({
      creds: options.creds,
      symbol,
      startTimeMs: nextFundingAtMs - 60_000,
      endTimeMs: nowMs,
    });
    return {
      open,
      paymentReceived: settled,
      nextFundingAtMs,
      paymentSource: settled ? "ledger" : "ledger-empty",
    };
  } catch (err) {
    log.warn(
      { err: err instanceof Error ? err.message : String(err), symbol },
      "Bybit ledger query failed — falling back to timestamp proxy",
    );
    return {
      open,
      paymentReceived: proxyPaymentReceived,
      nextFundingAtMs,
      paymentSource: "proxy",
    };
  }
}

// ---------------------------------------------------------------------------
// Bybit /v5/account/transaction-log query
// ---------------------------------------------------------------------------

interface FundingLedgerQuery {
  creds: FundingLedgerCreds;
  symbol: string;
  startTimeMs: number;
  endTimeMs: number;
}

interface BybitTransactionLogResponse {
  retCode: number;
  retMsg: string;
  result?: {
    list?: Array<{
      symbol: string;
      type: string;
      transactionTime: string;
    }>;
  };
}

/** Returns true iff the ledger has at least one `type=SETTLEMENT` row
 *  for `symbol` in `(startTimeMs, endTimeMs]`. Throws on transport,
 *  parse, or Bybit-API errors so the caller can fall back to the proxy. */
async function queryFundingLedger(q: FundingLedgerQuery): Promise<boolean> {
  const params = {
    accountType: "UNIFIED",
    category: "linear",
    symbol: q.symbol,
    type: "SETTLEMENT",
    startTime: q.startTimeMs.toString(),
    endTime: q.endTimeMs.toString(),
    limit: LEDGER_PAGE_LIMIT,
  };
  const qs = new URLSearchParams(params).toString();
  const timestamp = Date.now().toString();
  const sign = createHmac("sha256", q.creds.secret)
    .update(`${timestamp}${q.creds.apiKey}${RECV_WINDOW}${qs}`)
    .digest("hex");

  const url = `${getBybitBaseUrl()}/v5/account/transaction-log?${qs}`;
  const res = await fetch(url, {
    headers: {
      "X-BAPI-API-KEY": q.creds.apiKey,
      "X-BAPI-SIGN": sign,
      "X-BAPI-TIMESTAMP": timestamp,
      "X-BAPI-RECV-WINDOW": RECV_WINDOW,
      "User-Agent": USER_AGENT,
    },
  });
  if (!res.ok) {
    throw new Error(`Bybit ledger HTTP ${res.status} ${res.statusText}`);
  }
  let json: BybitTransactionLogResponse;
  try {
    json = (await res.json()) as BybitTransactionLogResponse;
  } catch (err) {
    throw new Error(
      `Bybit ledger parse error: ${err instanceof Error ? err.message : String(err)}`,
    );
  }
  if (json.retCode !== 0) {
    throw new Error(`Bybit ledger retCode=${json.retCode}: ${json.retMsg}`);
  }
  const list = json.result?.list ?? [];
  return list.some((row) => row.symbol === q.symbol && row.type === "SETTLEMENT");
}
