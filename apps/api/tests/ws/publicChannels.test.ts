/**
 * Public WS channels tests — Roadmap V3, Task #19
 *
 * Tests: orderbook parsing, kline parsing, ticker parsing,
 * subscription helpers.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// ---------------------------------------------------------------------------
// Mock WebSocket
// ---------------------------------------------------------------------------

type WsListener = (event: unknown) => void;

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  url: string;
  readyState = 1;
  onopen: WsListener | null = null;
  onclose: WsListener | null = null;
  onmessage: WsListener | null = null;
  onerror: WsListener | null = null;
  sent: string[] = [];

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
    queueMicrotask(() => {
      if (this.onopen) this.onopen(new Event("open"));
    });
  }
  send(data: string) { this.sent.push(data); }
  close() {
    this.readyState = 3;
    if (this.onclose) this.onclose({ code: 1000, reason: "" });
  }
  simulateMessage(data: unknown) {
    if (this.onmessage) {
      this.onmessage({ data: typeof data === "string" ? data : JSON.stringify(data) });
    }
  }
}

const OriginalWebSocket = globalThis.WebSocket;

vi.mock("../../src/lib/logger.js", () => ({
  logger: {
    child: () => ({
      info: vi.fn(),
      warn: vi.fn(),
      error: vi.fn(),
      debug: vi.fn(),
    }),
  },
}));

import { BybitPublicWs, type OrderbookSnapshot, type KlineUpdate, type TickerUpdate } from "../../src/lib/ws/publicChannels.js";

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("BybitPublicWs", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    MockWebSocket.instances = [];
    (globalThis as unknown as Record<string, unknown>).WebSocket = MockWebSocket as unknown as typeof WebSocket;
  });

  afterEach(() => {
    vi.useRealTimers();
    (globalThis as unknown as Record<string, unknown>).WebSocket = OriginalWebSocket;
  });

  it("connects to public WS endpoint", async () => {
    const pub = new BybitPublicWs("wss://test.example.com/v5/public/linear");
    const connected = vi.fn();
    pub.on("connected", connected);

    pub.connect();
    await vi.advanceTimersByTimeAsync(0);

    expect(connected).toHaveBeenCalledTimes(1);
    expect(MockWebSocket.instances[0].url).toBe("wss://test.example.com/v5/public/linear");

    pub.close();
  });

  describe("subscriptions", () => {
    it("subscribeOrderbook sends correct topic", async () => {
      const pub = new BybitPublicWs("wss://test/ws");
      pub.connect();
      await vi.advanceTimersByTimeAsync(0);

      pub.subscribeOrderbook("BTCUSDT", 50);

      const ws = MockWebSocket.instances[0];
      const sub = ws.sent.find((s) => JSON.parse(s).op === "subscribe");
      expect(sub).toBeDefined();
      expect(JSON.parse(sub!).args).toContain("orderbook.50.BTCUSDT");

      pub.close();
    });

    it("subscribeKline sends correct topic", async () => {
      const pub = new BybitPublicWs("wss://test/ws");
      pub.connect();
      await vi.advanceTimersByTimeAsync(0);

      pub.subscribeKline("ETHUSDT", "5");

      const ws = MockWebSocket.instances[0];
      const sub = ws.sent.find((s) => JSON.parse(s).op === "subscribe");
      expect(JSON.parse(sub!).args).toContain("kline.5.ETHUSDT");

      pub.close();
    });

    it("subscribeTicker sends correct topic", async () => {
      const pub = new BybitPublicWs("wss://test/ws");
      pub.connect();
      await vi.advanceTimersByTimeAsync(0);

      pub.subscribeTicker("BTCUSDT");

      const ws = MockWebSocket.instances[0];
      const sub = ws.sent.find((s) => JSON.parse(s).op === "subscribe");
      expect(JSON.parse(sub!).args).toContain("tickers.BTCUSDT");

      pub.close();
    });
  });

  describe("orderbook parsing", () => {
    it("emits parsed orderbook snapshot", async () => {
      const pub = new BybitPublicWs("wss://test/ws");
      const handler = vi.fn();
      pub.on("orderbook", handler);

      pub.connect();
      await vi.advanceTimersByTimeAsync(0);

      const ws = MockWebSocket.instances[0];
      ws.simulateMessage({
        topic: "orderbook.25.BTCUSDT",
        type: "snapshot",
        data: {
          s: "BTCUSDT",
          b: [["50000.00", "1.5"], ["49999.50", "2.0"]],
          a: [["50001.00", "0.8"], ["50002.00", "1.2"]],
          u: 12345,
        },
        ts: 1700000000000,
      });

      expect(handler).toHaveBeenCalledTimes(1);
      const snapshot: OrderbookSnapshot = handler.mock.calls[0][0];
      expect(snapshot.symbol).toBe("BTCUSDT");
      expect(snapshot.bids).toHaveLength(2);
      expect(snapshot.bids[0]).toEqual({ price: 50000, qty: 1.5 });
      expect(snapshot.asks).toHaveLength(2);
      expect(snapshot.asks[0]).toEqual({ price: 50001, qty: 0.8 });
      expect(snapshot.updateId).toBe(12345);
      expect(snapshot.ts).toBe(1700000000000);

      pub.close();
    });

    it("handles empty orderbook data", async () => {
      const pub = new BybitPublicWs("wss://test/ws");
      const handler = vi.fn();
      pub.on("orderbook", handler);

      pub.connect();
      await vi.advanceTimersByTimeAsync(0);

      const ws = MockWebSocket.instances[0];
      ws.simulateMessage({
        topic: "orderbook.25.BTCUSDT",
        type: "snapshot",
        data: { s: "BTCUSDT", b: [], a: [], u: 1 },
        ts: 1700000000000,
      });

      expect(handler).toHaveBeenCalledTimes(1);
      expect(handler.mock.calls[0][0].bids).toHaveLength(0);
      expect(handler.mock.calls[0][0].asks).toHaveLength(0);

      pub.close();
    });
  });

  describe("kline parsing", () => {
    it("emits parsed kline update", async () => {
      const pub = new BybitPublicWs("wss://test/ws");
      const handler = vi.fn();
      pub.on("kline", handler);

      pub.connect();
      await vi.advanceTimersByTimeAsync(0);

      const ws = MockWebSocket.instances[0];
      ws.simulateMessage({
        topic: "kline.1.BTCUSDT",
        type: "snapshot",
        data: [{
          start: 1700000000000,
          end: 1700000060000,
          interval: "1",
          open: "50000.00",
          close: "50100.00",
          high: "50200.00",
          low: "49900.00",
          volume: "150.5",
          confirm: false,
        }],
        ts: 1700000001000,
      });

      expect(handler).toHaveBeenCalledTimes(1);
      const kline: KlineUpdate = handler.mock.calls[0][0];
      expect(kline.symbol).toBe("BTCUSDT");
      expect(kline.interval).toBe("1");
      expect(kline.openTime).toBe(1700000000000);
      expect(kline.open).toBe(50000);
      expect(kline.close).toBe(50100);
      expect(kline.high).toBe(50200);
      expect(kline.low).toBe(49900);
      expect(kline.volume).toBe(150.5);
      expect(kline.confirm).toBe(false);

      pub.close();
    });

    it("emits confirmed kline (candle closed)", async () => {
      const pub = new BybitPublicWs("wss://test/ws");
      const handler = vi.fn();
      pub.on("kline", handler);

      pub.connect();
      await vi.advanceTimersByTimeAsync(0);

      const ws = MockWebSocket.instances[0];
      ws.simulateMessage({
        topic: "kline.15.ETHUSDT",
        type: "snapshot",
        data: [{
          start: 1700000000000,
          end: 1700000900000,
          interval: "15",
          open: "2000.00",
          close: "2050.00",
          high: "2060.00",
          low: "1990.00",
          volume: "500",
          confirm: true,
        }],
        ts: 1700000900000,
      });

      expect(handler).toHaveBeenCalledTimes(1);
      const kline: KlineUpdate = handler.mock.calls[0][0];
      expect(kline.confirm).toBe(true);
      expect(kline.symbol).toBe("ETHUSDT");

      pub.close();
    });
  });

  describe("ticker parsing", () => {
    it("emits parsed ticker update", async () => {
      const pub = new BybitPublicWs("wss://test/ws");
      const handler = vi.fn();
      pub.on("ticker", handler);

      pub.connect();
      await vi.advanceTimersByTimeAsync(0);

      const ws = MockWebSocket.instances[0];
      ws.simulateMessage({
        topic: "tickers.BTCUSDT",
        type: "snapshot",
        data: {
          symbol: "BTCUSDT",
          lastPrice: "50000.50",
          bid1Price: "50000.00",
          ask1Price: "50001.00",
          highPrice24h: "51000.00",
          lowPrice24h: "49000.00",
          volume24h: "10000",
          turnover24h: "500000000",
          price24hPcnt: "0.015",
        },
        ts: 1700000000000,
      });

      expect(handler).toHaveBeenCalledTimes(1);
      const ticker: TickerUpdate = handler.mock.calls[0][0];
      expect(ticker.symbol).toBe("BTCUSDT");
      expect(ticker.lastPrice).toBe(50000.5);
      expect(ticker.bidPrice).toBe(50000);
      expect(ticker.askPrice).toBe(50001);
      expect(ticker.highPrice24h).toBe(51000);
      expect(ticker.lowPrice24h).toBe(49000);
      expect(ticker.volume24h).toBe(10000);
      expect(ticker.price24hPcnt).toBe(0.015);

      pub.close();
    });
  });

  describe("unsubscribe", () => {
    it("unsubscribeOrderbook sends correct topic", async () => {
      const pub = new BybitPublicWs("wss://test/ws");
      pub.connect();
      await vi.advanceTimersByTimeAsync(0);

      pub.subscribeOrderbook("BTCUSDT", 25);
      pub.unsubscribeOrderbook("BTCUSDT", 25);

      const ws = MockWebSocket.instances[0];
      const unsub = ws.sent.find((s) => JSON.parse(s).op === "unsubscribe");
      expect(unsub).toBeDefined();
      expect(JSON.parse(unsub!).args).toContain("orderbook.25.BTCUSDT");

      pub.close();
    });
  });
});
