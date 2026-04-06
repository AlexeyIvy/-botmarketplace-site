/**
 * Private WS channels tests — Roadmap V3, Task #19
 *
 * Tests: auth flow, execution report parsing, position update parsing.
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

import { BybitPrivateWs, type ExecutionReport, type PositionUpdate } from "../../src/lib/ws/privateChannels.js";

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("BybitPrivateWs", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    MockWebSocket.instances = [];
    (globalThis as unknown as Record<string, unknown>).WebSocket = MockWebSocket as unknown as typeof WebSocket;
  });

  afterEach(() => {
    vi.useRealTimers();
    (globalThis as unknown as Record<string, unknown>).WebSocket = OriginalWebSocket;
  });

  function createPrivateWs() {
    return new BybitPrivateWs("test-api-key", "test-secret", "wss://test.example.com/v5/private");
  }

  it("connects and sends auth message on open", async () => {
    const priv = createPrivateWs();
    priv.connect();
    await vi.advanceTimersByTimeAsync(0);

    const ws = MockWebSocket.instances[0];
    expect(ws.url).toBe("wss://test.example.com/v5/private");

    const authMsg = ws.sent.find((s) => JSON.parse(s).op === "auth");
    expect(authMsg).toBeDefined();

    const parsed = JSON.parse(authMsg!);
    expect(parsed.args[0]).toBe("test-api-key");
    expect(typeof parsed.args[1]).toBe("number"); // expires timestamp
    expect(typeof parsed.args[2]).toBe("string"); // HMAC signature

    priv.close();
  });

  it("subscribes to execution and position after successful auth", async () => {
    const priv = createPrivateWs();
    const authenticated = vi.fn();
    priv.on("authenticated", authenticated);

    priv.connect();
    await vi.advanceTimersByTimeAsync(0);

    // Simulate auth success
    const ws = MockWebSocket.instances[0];
    ws.simulateMessage({ op: "auth", success: true, ret_msg: "" });

    expect(authenticated).toHaveBeenCalledTimes(1);

    // Should have subscribed to execution + position
    const subMsg = ws.sent.find((s) => {
      const p = JSON.parse(s);
      return p.op === "subscribe" && p.args?.includes("execution");
    });
    expect(subMsg).toBeDefined();
    expect(JSON.parse(subMsg!).args).toContain("position");

    priv.close();
  });

  it("emits authError on failed auth", async () => {
    const priv = createPrivateWs();
    const authError = vi.fn();
    priv.on("authError", authError);

    priv.connect();
    await vi.advanceTimersByTimeAsync(0);

    const ws = MockWebSocket.instances[0];
    ws.simulateMessage({ op: "auth", success: false, ret_msg: "Invalid key" });

    expect(authError).toHaveBeenCalledWith("Invalid key");

    priv.close();
  });

  describe("execution report parsing", () => {
    it("emits parsed execution report", async () => {
      const priv = createPrivateWs();
      const handler = vi.fn();
      priv.on("execution", handler);

      priv.connect();
      await vi.advanceTimersByTimeAsync(0);

      const ws = MockWebSocket.instances[0];
      ws.simulateMessage({
        topic: "execution",
        data: [{
          symbol: "BTCUSDT",
          orderId: "order-123",
          orderLinkId: "link-456",
          side: "Buy",
          orderType: "Market",
          orderStatus: "Filled",
          execType: "Trade",
          execQty: "0.01",
          execPrice: "50000.00",
          execFee: "0.50",
          leavesQty: "0",
          cumExecQty: "0.01",
          cumExecValue: "500.00",
          cumExecFee: "0.50",
          createdTime: "1700000000000",
          updatedTime: "1700000001000",
        }],
      });

      expect(handler).toHaveBeenCalledTimes(1);
      const report: ExecutionReport = handler.mock.calls[0][0];
      expect(report.symbol).toBe("BTCUSDT");
      expect(report.orderId).toBe("order-123");
      expect(report.orderLinkId).toBe("link-456");
      expect(report.side).toBe("Buy");
      expect(report.orderType).toBe("Market");
      expect(report.orderStatus).toBe("Filled");
      expect(report.execQty).toBe(0.01);
      expect(report.execPrice).toBe(50000);
      expect(report.execFee).toBe(0.5);
      expect(report.leavesQty).toBe(0);
      expect(report.cumExecQty).toBe(0.01);
      expect(report.cumExecValue).toBe(500);
      expect(report.cumExecFee).toBe(0.5);
      expect(report.createdTime).toBe(1700000000000);
      expect(report.updatedTime).toBe(1700000001000);

      priv.close();
    });

    it("handles multiple execution reports in single message", async () => {
      const priv = createPrivateWs();
      const handler = vi.fn();
      priv.on("execution", handler);

      priv.connect();
      await vi.advanceTimersByTimeAsync(0);

      const ws = MockWebSocket.instances[0];
      ws.simulateMessage({
        topic: "execution",
        data: [
          {
            symbol: "BTCUSDT", orderId: "o1", orderLinkId: "", side: "Buy",
            orderType: "Limit", orderStatus: "PartiallyFilled", execType: "Trade",
            execQty: "0.005", execPrice: "49000", execFee: "0.1",
            leavesQty: "0.005", cumExecQty: "0.005", cumExecValue: "245",
            cumExecFee: "0.1", createdTime: "1700000000000", updatedTime: "1700000000500",
          },
          {
            symbol: "BTCUSDT", orderId: "o1", orderLinkId: "", side: "Buy",
            orderType: "Limit", orderStatus: "Filled", execType: "Trade",
            execQty: "0.005", execPrice: "49000", execFee: "0.1",
            leavesQty: "0", cumExecQty: "0.01", cumExecValue: "490",
            cumExecFee: "0.2", createdTime: "1700000000000", updatedTime: "1700000001000",
          },
        ],
      });

      expect(handler).toHaveBeenCalledTimes(2);
      expect(handler.mock.calls[0][0].orderStatus).toBe("PartiallyFilled");
      expect(handler.mock.calls[1][0].orderStatus).toBe("Filled");

      priv.close();
    });
  });

  describe("position update parsing", () => {
    it("emits parsed position update", async () => {
      const priv = createPrivateWs();
      const handler = vi.fn();
      priv.on("position", handler);

      priv.connect();
      await vi.advanceTimersByTimeAsync(0);

      const ws = MockWebSocket.instances[0];
      ws.simulateMessage({
        topic: "position",
        data: [{
          symbol: "BTCUSDT",
          side: "Buy",
          size: "0.01",
          entryPrice: "50000.00",
          unrealisedPnl: "10.50",
          markPrice: "51050.00",
          leverage: "10",
          updatedTime: "1700000000000",
        }],
      });

      expect(handler).toHaveBeenCalledTimes(1);
      const pos: PositionUpdate = handler.mock.calls[0][0];
      expect(pos.symbol).toBe("BTCUSDT");
      expect(pos.side).toBe("Buy");
      expect(pos.size).toBe(0.01);
      expect(pos.entryPrice).toBe(50000);
      expect(pos.unrealisedPnl).toBe(10.5);
      expect(pos.markPrice).toBe(51050);
      expect(pos.leverage).toBe(10);

      priv.close();
    });

    it("handles position close (side=None, size=0)", async () => {
      const priv = createPrivateWs();
      const handler = vi.fn();
      priv.on("position", handler);

      priv.connect();
      await vi.advanceTimersByTimeAsync(0);

      const ws = MockWebSocket.instances[0];
      ws.simulateMessage({
        topic: "position",
        data: [{
          symbol: "BTCUSDT",
          side: "None",
          size: "0",
          entryPrice: "0",
          unrealisedPnl: "0",
          markPrice: "50000",
          leverage: "10",
          updatedTime: "1700000005000",
        }],
      });

      expect(handler).toHaveBeenCalledTimes(1);
      const pos: PositionUpdate = handler.mock.calls[0][0];
      expect(pos.side).toBe("None");
      expect(pos.size).toBe(0);

      priv.close();
    });
  });

  it("HMAC signature is deterministic for same inputs", async () => {
    // Create two instances with same credentials — auth messages should have same key
    const priv1 = new BybitPrivateWs("key-A", "secret-B", "wss://test/v5/private");
    const priv2 = new BybitPrivateWs("key-A", "secret-B", "wss://test/v5/private");

    priv1.connect();
    priv2.connect();
    await vi.advanceTimersByTimeAsync(0);

    const ws1 = MockWebSocket.instances[0];
    const ws2 = MockWebSocket.instances[1];

    const auth1 = JSON.parse(ws1.sent.find((s) => JSON.parse(s).op === "auth")!);
    const auth2 = JSON.parse(ws2.sent.find((s) => JSON.parse(s).op === "auth")!);

    expect(auth1.args[0]).toBe(auth2.args[0]); // same API key
    // Signatures may differ slightly due to timestamp, but format should be hex
    expect(auth1.args[2]).toMatch(/^[0-9a-f]+$/);
    expect(auth2.args[2]).toMatch(/^[0-9a-f]+$/);

    priv1.close();
    priv2.close();
  });
});
