/**
 * Balance reconciler for funding-arbitrage hedges (docs/55-T5).
 *
 * Calls two Bybit private endpoints in parallel and produces a per-symbol
 * hedge classification used by `hedgeBotWorker` (55-T4):
 *
 *   1. `GET /v5/position/list?category=linear&settleCoin=USDT` — perp side.
 *   2. `GET /v5/account/wallet-balance?accountType=UNIFIED`     — spot side.
 *
 * Dual API key (docs/55-T5):
 *   * If `connection.spotApiKey` AND `connection.spotEncryptedSecret` are
 *     both set, the spot call is signed with that pair.
 *   * Otherwise the spot call is signed with the linear pair — Bybit unified
 *     accounts can issue a single key with both scopes (single-key fallback).
 *     A warning is logged so operators know they're running unified.
 *
 * Hedge classification (per symbol):
 *   - 'flat'        — no position on either side.
 *   - 'perp_only'   — perp position exists, no matching spot holding.
 *   - 'spot_only'   — spot holding exists, no matching perp position.
 *   - 'balanced'    — both legs present and `||perp| - spot| / max ≤ 0.5%`.
 *   - 'imbalanced'  — both legs present, sizes diverge above tolerance.
 *
 * Funding-arb expects perp-short + spot-long, so 'balanced' is the success
 * state for an OPEN hedge; 'flat' is the success state for an idle slot.
 *
 * Errors funnel through `BalanceReconcilerError` with a `cause` discriminator
 * so callers can branch without parsing free-form messages.
 */

import { logger } from "../logger.js";
import { decryptWithFallback } from "../crypto.js";
import { getBybitBaseUrl } from "../bybitOrder.js";
import { bybitAuthHeaders } from "./bybitAuth.js";

const log = logger.child({ module: "balanceReconciler" });

const USER_AGENT = "botmarketplace-reconciler/1";
/** `||perp| - spot| / max(|perp|, spot)` accepted as 'balanced'. */
const HEDGE_BALANCE_TOLERANCE = 0.005;

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

export interface ExchangeConnectionCreds {
  apiKey: string;
  encryptedSecret: string;
  /** Optional dedicated spot API key (docs/55-T5). NULL ⇒ single-key fallback. */
  spotApiKey?: string | null;
  /** Optional dedicated spot encrypted secret. NULL ⇒ single-key fallback. */
  spotEncryptedSecret?: string | null;
}

export type HedgeBalanceClassification =
  | "flat"
  | "perp_only"
  | "spot_only"
  | "balanced"
  | "imbalanced";

export interface HedgeBalanceStatus {
  symbol: string;
  /** Signed perp position size (positive = long, negative = short). 0 if absent. */
  perpQty: number;
  /** Spot base-asset holding inferred from `walletBalance`. 0 if absent. */
  spotQty: number;
  status: HedgeBalanceClassification;
  /** `|perpQty| - spotQty` when both legs present; `undefined` otherwise. */
  delta?: number;
}

export interface ReconcileResult {
  /** symbol → signed perp size. */
  perp: Map<string, number>;
  /** baseAsset (e.g. "BTC") → spot wallet balance. */
  spot: Map<string, number>;
  hedgeStatus: HedgeBalanceStatus[];
  /** False ⇒ spot call was signed with linear creds (single-key fallback). */
  spotKeyAvailable: boolean;
}

export class BalanceReconcilerError extends Error {
  readonly cause: "http" | "api" | "parse";
  readonly statusCode?: number;
  readonly retCode?: number;
  constructor(
    message: string,
    cause: BalanceReconcilerError["cause"],
    extras: { statusCode?: number; retCode?: number } = {},
  ) {
    super(message);
    this.name = "BalanceReconcilerError";
    this.cause = cause;
    this.statusCode = extras.statusCode;
    this.retCode = extras.retCode;
  }
}

// ---------------------------------------------------------------------------
// Bybit response shapes (only the fields we read)
// ---------------------------------------------------------------------------

interface PositionListResponse {
  retCode: number;
  retMsg: string;
  result: {
    list: Array<{
      symbol: string;
      side: string; // "Buy" | "Sell" | "" (empty when flat)
      size: string;
    }>;
  };
}

interface WalletBalanceResponse {
  retCode: number;
  retMsg: string;
  result: {
    list: Array<{
      coin: Array<{
        coin: string;
        walletBalance: string;
      }>;
    }>;
  };
}

// ---------------------------------------------------------------------------
// HTTP wrapper — auth helpers live in `./bybitAuth.ts`.
// ---------------------------------------------------------------------------

async function bybitGet<T extends { retCode: number; retMsg: string }>(
  apiKey: string,
  secret: string,
  path: string,
  query: Record<string, string>,
): Promise<T> {
  const qs = new URLSearchParams(query).toString();
  const timestamp = Date.now().toString();
  const url = `${getBybitBaseUrl()}${path}?${qs}`;

  const res = await fetch(url, {
    headers: bybitAuthHeaders(apiKey, secret, timestamp, qs, USER_AGENT),
  });
  if (!res.ok) {
    throw new BalanceReconcilerError(
      `Bybit reconciler HTTP ${res.status} ${res.statusText} for ${path}`,
      "http",
      { statusCode: res.status },
    );
  }
  let json: T;
  try {
    json = (await res.json()) as T;
  } catch (err) {
    throw new BalanceReconcilerError(
      `Bybit reconciler parse error for ${path}: ${(err as Error).message}`,
      "parse",
    );
  }
  if (json.retCode !== 0) {
    throw new BalanceReconcilerError(
      `Bybit API error ${json.retCode}: ${json.retMsg}`,
      "api",
      { retCode: json.retCode },
    );
  }
  return json;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** BTCUSDT → BTC, ETHUSD → ETH, etc. Funding-arb is positive-funding only,
 *  so quote stable-coins are stripped to recover the base asset matching the
 *  spot wallet entry. */
export function baseAssetOf(symbol: string): string {
  if (symbol.endsWith("USDT")) return symbol.slice(0, -4);
  if (symbol.endsWith("USDC")) return symbol.slice(0, -4);
  if (symbol.endsWith("USD")) return symbol.slice(0, -3);
  return symbol;
}

function classify(perpQty: number, spotQty: number): HedgeBalanceClassification {
  const hasPerp = Math.abs(perpQty) > 0;
  const hasSpot = spotQty > 0;
  if (!hasPerp && !hasSpot) return "flat";
  if (hasPerp && !hasSpot) return "perp_only";
  if (!hasPerp && hasSpot) return "spot_only";
  const absPerp = Math.abs(perpQty);
  const denom = Math.max(absPerp, spotQty);
  const mismatch = Math.abs(absPerp - spotQty) / denom;
  return mismatch <= HEDGE_BALANCE_TOLERANCE ? "balanced" : "imbalanced";
}

// ---------------------------------------------------------------------------
// Public entry point
// ---------------------------------------------------------------------------

/**
 * Reconcile perp + spot balances for `symbols` against Bybit.
 *
 * Calls (in parallel) `/v5/position/list?category=linear` and
 * `/v5/account/wallet-balance?accountType=UNIFIED`. The spot call is signed
 * with `connection.spotApiKey` / `spotEncryptedSecret` when both are set,
 * otherwise with `connection.apiKey` / `encryptedSecret` (single-key
 * fallback — Bybit unified scope).
 *
 * @param connection — credentials; the linear pair is required.
 * @param symbols    — list of perp symbols (e.g. ["BTCUSDT"]) to classify.
 * @returns parsed maps + per-symbol `hedgeStatus`.
 * @throws {@link BalanceReconcilerError} on HTTP / API / parse failure.
 */
export async function reconcileBalances(
  connection: ExchangeConnectionCreds,
  symbols: string[],
): Promise<ReconcileResult> {
  const useDualKeys = !!(connection.spotApiKey && connection.spotEncryptedSecret);

  const linearSecret = decryptWithFallback(connection.encryptedSecret);
  const spotApiKey = useDualKeys ? connection.spotApiKey! : connection.apiKey;
  const spotSecret = useDualKeys
    ? decryptWithFallback(connection.spotEncryptedSecret!)
    : linearSecret;

  if (!useDualKeys) {
    log.warn(
      { apiKey: connection.apiKey },
      "Dual API key absent — falling back to linear creds for spot wallet (single-key mode)",
    );
  }

  const [perpJson, spotJson] = await Promise.all([
    bybitGet<PositionListResponse>(
      connection.apiKey,
      linearSecret,
      "/v5/position/list",
      { category: "linear", settleCoin: "USDT" },
    ),
    bybitGet<WalletBalanceResponse>(
      spotApiKey,
      spotSecret,
      "/v5/account/wallet-balance",
      { accountType: "UNIFIED" },
    ),
  ]);

  const perp = new Map<string, number>();
  for (const pos of perpJson.result?.list ?? []) {
    const size = Number(pos.size);
    if (!Number.isFinite(size) || size === 0) continue;
    const signed = pos.side === "Sell" ? -size : size;
    perp.set(pos.symbol, signed);
  }

  const spot = new Map<string, number>();
  for (const bucket of spotJson.result?.list ?? []) {
    for (const c of bucket.coin ?? []) {
      const qty = Number(c.walletBalance);
      if (!Number.isFinite(qty) || qty <= 0) continue;
      // Sum across buckets — Bybit may return one entry per account-type bucket.
      spot.set(c.coin, (spot.get(c.coin) ?? 0) + qty);
    }
  }

  const hedgeStatus: HedgeBalanceStatus[] = symbols.map((symbol) => {
    const perpQty = perp.get(symbol) ?? 0;
    const spotQty = spot.get(baseAssetOf(symbol)) ?? 0;
    const status = classify(perpQty, spotQty);
    const both = Math.abs(perpQty) > 0 && spotQty > 0;
    return {
      symbol,
      perpQty,
      spotQty,
      status,
      delta: both ? Math.abs(perpQty) - spotQty : undefined,
    };
  });

  return { perp, spot, hedgeStatus, spotKeyAvailable: useDualKeys };
}
