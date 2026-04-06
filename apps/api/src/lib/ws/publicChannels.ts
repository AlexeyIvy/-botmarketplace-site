/**
 * Bybit public WS channels: orderbook, kline, ticker.
 *
 * Public endpoint: wss://stream.bybit.com/v5/public/linear
 * Channels:
 *   - orderbook.{depth}.{symbol}  (depth: 25 or 50)
 *   - kline.{interval}.{symbol}   (interval: 1, 5, 15, 60)
 *   - tickers.{symbol}
 *
 * Roadmap V3, Task #19 — Slice A.
 */

import { EventEmitter } from "node:events";
import { BybitWsClient, type BybitWsMessage } from "./BybitWsClient.js";
import { logger } from "../logger.js";

const pubLog = logger.child({ module: "bybit-ws-public" });

// ---------------------------------------------------------------------------
// URLs
// ---------------------------------------------------------------------------

export const BYBIT_PUBLIC_WS_URL =
  process.env.BYBIT_PUBLIC_WS_URL ?? "wss://stream.bybit.com/v5/public/linear";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface OrderbookEntry {
  price: number;
  qty: number;
}

export interface OrderbookSnapshot {
  symbol: string;
  bids: OrderbookEntry[];
  asks: OrderbookEntry[];
  updateId: number;
  ts: number;
}

export interface KlineUpdate {
  symbol: string;
  interval: string;
  openTime: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  confirm: boolean; // true = candle closed
  ts: number;
}

export interface TickerUpdate {
  symbol: string;
  lastPrice: number;
  bidPrice: number;
  askPrice: number;
  highPrice24h: number;
  lowPrice24h: number;
  volume24h: number;
  turnover24h: number;
  price24hPcnt: number;
  ts: number;
}

// ---------------------------------------------------------------------------
// Public channel handler
// ---------------------------------------------------------------------------

export class BybitPublicWs extends EventEmitter {
  private client: BybitWsClient;

  constructor(url?: string) {
    super();
    this.client = new BybitWsClient({ url: url ?? BYBIT_PUBLIC_WS_URL });
    this.client.on("message", (msg: BybitWsMessage) => this.route(msg));
    this.client.on("connected", () => this.emit("connected"));
    this.client.on("disconnected", (code: number, reason: string) =>
      this.emit("disconnected", code, reason),
    );
    this.client.on("error", (err: unknown) => this.emit("error", err));
  }

  /** Expose underlying client for testing / advanced use. */
  getClient(): BybitWsClient {
    return this.client;
  }

  connect(): void {
    this.client.connect();
  }

  close(): void {
    this.client.close();
  }

  // -------------------------------------------------------------------------
  // Subscription helpers
  // -------------------------------------------------------------------------

  subscribeOrderbook(symbol: string, depth: 25 | 50 = 25): void {
    this.client.subscribe([`orderbook.${depth}.${symbol}`]);
  }

  subscribeKline(symbol: string, interval: string): void {
    this.client.subscribe([`kline.${interval}.${symbol}`]);
  }

  subscribeTicker(symbol: string): void {
    this.client.subscribe([`tickers.${symbol}`]);
  }

  unsubscribeOrderbook(symbol: string, depth: 25 | 50 = 25): void {
    this.client.unsubscribe([`orderbook.${depth}.${symbol}`]);
  }

  unsubscribeKline(symbol: string, interval: string): void {
    this.client.unsubscribe([`kline.${interval}.${symbol}`]);
  }

  unsubscribeTicker(symbol: string): void {
    this.client.unsubscribe([`tickers.${symbol}`]);
  }

  // -------------------------------------------------------------------------
  // Message routing
  // -------------------------------------------------------------------------

  private route(msg: BybitWsMessage): void {
    if (!msg.topic) return;

    try {
      if (msg.topic.startsWith("orderbook.")) {
        this.handleOrderbook(msg);
      } else if (msg.topic.startsWith("kline.")) {
        this.handleKline(msg);
      } else if (msg.topic.startsWith("tickers.")) {
        this.handleTicker(msg);
      }
    } catch (err) {
      pubLog.error({ err, topic: msg.topic }, "Error handling public WS message");
    }
  }

  // -------------------------------------------------------------------------
  // Parsers
  // -------------------------------------------------------------------------

  private handleOrderbook(msg: BybitWsMessage): void {
    const data = msg.data as {
      s: string;
      b: [string, string][];
      a: [string, string][];
      u: number;
    };
    if (!data) return;

    const snapshot: OrderbookSnapshot = {
      symbol: data.s,
      bids: (data.b ?? []).map(([p, q]) => ({
        price: Number(p),
        qty: Number(q),
      })),
      asks: (data.a ?? []).map(([p, q]) => ({
        price: Number(p),
        qty: Number(q),
      })),
      updateId: data.u,
      ts: msg.ts ?? Date.now(),
    };

    this.emit("orderbook", snapshot);
  }

  private handleKline(msg: BybitWsMessage): void {
    const items = msg.data as Array<{
      start: number;
      end: number;
      interval: string;
      open: string;
      close: string;
      high: string;
      low: string;
      volume: string;
      confirm: boolean;
    }>;
    if (!Array.isArray(items)) return;

    // Extract symbol from topic: "kline.1.BTCUSDT" → "BTCUSDT"
    const parts = msg.topic!.split(".");
    const symbol = parts[2] ?? "";

    for (const item of items) {
      const kline: KlineUpdate = {
        symbol,
        interval: item.interval,
        openTime: item.start,
        open: Number(item.open),
        high: Number(item.high),
        low: Number(item.low),
        close: Number(item.close),
        volume: Number(item.volume),
        confirm: item.confirm,
        ts: msg.ts ?? Date.now(),
      };
      this.emit("kline", kline);
    }
  }

  private handleTicker(msg: BybitWsMessage): void {
    const data = msg.data as {
      symbol: string;
      lastPrice: string;
      bid1Price: string;
      ask1Price: string;
      highPrice24h: string;
      lowPrice24h: string;
      volume24h: string;
      turnover24h: string;
      price24hPcnt: string;
    };
    if (!data) return;

    const ticker: TickerUpdate = {
      symbol: data.symbol,
      lastPrice: Number(data.lastPrice),
      bidPrice: Number(data.bid1Price),
      askPrice: Number(data.ask1Price),
      highPrice24h: Number(data.highPrice24h),
      lowPrice24h: Number(data.lowPrice24h),
      volume24h: Number(data.volume24h),
      turnover24h: Number(data.turnover24h),
      price24hPcnt: Number(data.price24hPcnt),
      ts: msg.ts ?? Date.now(),
    };

    this.emit("ticker", ticker);
  }
}
