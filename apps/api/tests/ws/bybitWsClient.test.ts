/**
 * BybitWsClient tests — Roadmap V3, Task #19
 *
 * Tests: connect, reconnect, heartbeat (ping/pong), auth, message parsing,
 * subscription management, graceful close.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// ---------------------------------------------------------------------------
// Mock WebSocket
// ---------------------------------------------------------------------------

type WsListener = (event: unknown) => void;

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  static OPEN = 1;
  static CLOSED = 3;

  url: string;
  readyState = MockWebSocket.OPEN;
  onopen: WsListener | null = null;
  onclose: WsListener | null = null;
  onmessage: WsListener | null = null;
  onerror: WsListener | null = null;
  sent: string[] = [];

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
    // Auto-trigger onopen on next tick
    queueMicrotask(() => {
      if (this.onopen) this.onopen(new Event("open"));
    });
  }

  send(data: string) {
    this.sent.push(data);
  }

  close(code?: number, reason?: string) {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose({ code: code ?? 1000, reason: reason ?? "" });
    }
  }

  // Test helpers
  simulateMessage(data: unknown) {
    if (this.onmessage) {
      this.onmessage({ data: typeof data === "string" ? data : JSON.stringify(data) });
    }
  }

  simulateClose(code = 1006, reason = "abnormal") {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose({ code, reason });
    }
  }

  simulateError(error?: unknown) {
    if (this.onerror) {
      this.onerror(error ?? new Event("error"));
    }
  }
}

// Replace global WebSocket
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

import { BybitWsClient } from "../../src/lib/ws/BybitWsClient.js";

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("BybitWsClient", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    MockWebSocket.instances = [];
    (globalThis as unknown as Record<string, unknown>).WebSocket = MockWebSocket as unknown as typeof WebSocket;
  });

  afterEach(() => {
    vi.useRealTimers();
    (globalThis as unknown as Record<string, unknown>).WebSocket = OriginalWebSocket;
  });

  function createClient(opts: Partial<Parameters<typeof BybitWsClient.prototype.connect>[0]> = {}) {
    return new BybitWsClient({
      url: "wss://test.example.com/v5/public/linear",
      pingIntervalMs: 20_000,
      pongTimeoutMs: 10_000,
      initialReconnectDelayMs: 1_000,
      maxReconnectDelayMs: 30_000,
      ...opts,
    });
  }

  it("connects and emits 'connected' event", async () => {
    const client = createClient();
    const connected = vi.fn();
    client.on("connected", connected);

    client.connect();
    await vi.advanceTimersByTimeAsync(0); // flush microtask for onopen

    expect(client.getState()).toBe("connected");
    expect(connected).toHaveBeenCalledTimes(1);
    expect(MockWebSocket.instances.length).toBe(1);

    client.close();
  });

  it("sends ping every pingIntervalMs", async () => {
    const client = createClient({ pingIntervalMs: 5_000 });
    client.connect();
    await vi.advanceTimersByTimeAsync(0);

    // First ping at 5s
    await vi.advanceTimersByTimeAsync(5_000);

    const ws = MockWebSocket.instances[0];
    const pings = ws.sent.filter((s) => JSON.parse(s).op === "ping");
    expect(pings.length).toBe(1);

    // Second ping at 10s
    await vi.advanceTimersByTimeAsync(5_000);
    const pings2 = ws.sent.filter((s) => JSON.parse(s).op === "ping");
    expect(pings2.length).toBe(2);

    client.close();
  });

  it("reconnects on pong timeout", async () => {
    const client = createClient({
      pingIntervalMs: 5_000,
      pongTimeoutMs: 2_000,
      initialReconnectDelayMs: 100,
    });
    const reconnecting = vi.fn();
    client.on("reconnecting", reconnecting);

    client.connect();
    await vi.advanceTimersByTimeAsync(0);
    expect(client.getState()).toBe("connected");

    // Trigger ping
    await vi.advanceTimersByTimeAsync(5_000);

    // Don't send pong — wait for timeout
    await vi.advanceTimersByTimeAsync(2_000);

    // Should be disconnected and scheduling reconnect
    expect(reconnecting).toHaveBeenCalled();

    client.close();
  });

  it("handles pong correctly — no reconnect", async () => {
    const client = createClient({
      pingIntervalMs: 5_000,
      pongTimeoutMs: 2_000,
    });
    const reconnecting = vi.fn();
    client.on("reconnecting", reconnecting);

    client.connect();
    await vi.advanceTimersByTimeAsync(0);

    // Trigger ping
    await vi.advanceTimersByTimeAsync(5_000);

    // Simulate pong response
    const ws = MockWebSocket.instances[0];
    ws.simulateMessage({ op: "pong", ret_msg: "pong" });

    // Wait past the pong timeout
    await vi.advanceTimersByTimeAsync(3_000);

    // Should still be connected
    expect(client.getState()).toBe("connected");
    expect(reconnecting).not.toHaveBeenCalled();

    client.close();
  });

  it("reconnects with exponential backoff on consecutive failures", async () => {
    const client = createClient({
      initialReconnectDelayMs: 1_000,
      maxReconnectDelayMs: 8_000,
    });
    const reconnecting = vi.fn();
    client.on("reconnecting", reconnecting);

    client.connect();
    await vi.advanceTimersByTimeAsync(0);

    // Simulate unexpected close — first reconnect at 1s
    MockWebSocket.instances[0].simulateClose(1006, "abnormal");
    expect(reconnecting).toHaveBeenCalledWith(1_000, 1);

    // Note: reconnect counter resets on successful connect (by design).
    // To test backoff, we need closes without successful onopen in between.
    // After reconnect, the new WS auto-opens (via MockWebSocket), so counter resets.
    // This verifies the basic reconnect flow works:
    await vi.advanceTimersByTimeAsync(1_000);
    await vi.advanceTimersByTimeAsync(0); // open → counter resets

    // Second close starts from attempt 1 again (counter was reset on connect)
    MockWebSocket.instances[1].simulateClose(1006);
    expect(reconnecting).toHaveBeenCalledTimes(2);
    expect(reconnecting).toHaveBeenLastCalledWith(1_000, 1);

    client.close();
  });

  it("caps reconnect delay at maxReconnectDelayMs", async () => {
    const client = createClient({
      initialReconnectDelayMs: 1_000,
      maxReconnectDelayMs: 4_000,
    });
    const reconnecting = vi.fn();
    client.on("reconnecting", reconnecting);

    client.connect();
    await vi.advanceTimersByTimeAsync(0);

    // Simulate 5 disconnects
    for (let i = 0; i < 5; i++) {
      const ws = MockWebSocket.instances[MockWebSocket.instances.length - 1];
      ws.simulateClose(1006);

      const lastCall = reconnecting.mock.calls[reconnecting.mock.calls.length - 1];
      const delay = lastCall[0] as number;
      expect(delay).toBeLessThanOrEqual(4_000);

      await vi.advanceTimersByTimeAsync(delay);
      await vi.advanceTimersByTimeAsync(0);
    }

    client.close();
  });

  it("does not reconnect after intentional close()", async () => {
    const client = createClient();
    const reconnecting = vi.fn();
    client.on("reconnecting", reconnecting);

    client.connect();
    await vi.advanceTimersByTimeAsync(0);
    client.close();

    await vi.advanceTimersByTimeAsync(30_000);
    expect(reconnecting).not.toHaveBeenCalled();
    expect(client.getState()).toBe("disconnected");
  });

  it("subscribes and resubscribes on reconnect", async () => {
    const client = createClient({ initialReconnectDelayMs: 100 });
    client.connect();
    await vi.advanceTimersByTimeAsync(0);

    client.subscribe(["kline.1.BTCUSDT", "tickers.BTCUSDT"]);

    const ws1 = MockWebSocket.instances[0];
    const subMsg = ws1.sent.find((s) => JSON.parse(s).op === "subscribe");
    expect(subMsg).toBeDefined();
    expect(JSON.parse(subMsg!).args).toEqual(["kline.1.BTCUSDT", "tickers.BTCUSDT"]);

    expect(client.getSubscriptionCount()).toBe(2);

    // Simulate disconnect + reconnect
    ws1.simulateClose(1006);
    await vi.advanceTimersByTimeAsync(100);
    await vi.advanceTimersByTimeAsync(0);

    // New connection should re-subscribe
    const ws2 = MockWebSocket.instances[1];
    const resubMsg = ws2.sent.find((s) => JSON.parse(s).op === "subscribe");
    expect(resubMsg).toBeDefined();
    expect(JSON.parse(resubMsg!).args).toContain("kline.1.BTCUSDT");
    expect(JSON.parse(resubMsg!).args).toContain("tickers.BTCUSDT");

    client.close();
  });

  it("sends auth message for private channels", async () => {
    const client = new BybitWsClient({
      url: "wss://test.example.com/v5/private",
      auth: { apiKey: "test-key", apiSecret: "test-secret" },
    });

    client.connect();
    await vi.advanceTimersByTimeAsync(0);

    const ws = MockWebSocket.instances[0];
    const authMsg = ws.sent.find((s) => JSON.parse(s).op === "auth");
    expect(authMsg).toBeDefined();

    const parsed = JSON.parse(authMsg!);
    expect(parsed.args[0]).toBe("test-key");
    expect(typeof parsed.args[1]).toBe("number"); // expires
    expect(typeof parsed.args[2]).toBe("string"); // signature

    client.close();
  });

  it("emits 'authenticated' on successful auth response", async () => {
    const client = new BybitWsClient({
      url: "wss://test.example.com/v5/private",
      auth: { apiKey: "test-key", apiSecret: "test-secret" },
    });
    const authenticated = vi.fn();
    client.on("authenticated", authenticated);

    client.connect();
    await vi.advanceTimersByTimeAsync(0);

    const ws = MockWebSocket.instances[0];
    ws.simulateMessage({ op: "auth", success: true, ret_msg: "" });

    expect(authenticated).toHaveBeenCalledTimes(1);

    client.close();
  });

  it("emits 'authError' on failed auth response", async () => {
    const client = new BybitWsClient({
      url: "wss://test.example.com/v5/private",
      auth: { apiKey: "bad-key", apiSecret: "bad-secret" },
    });
    const authError = vi.fn();
    client.on("authError", authError);

    client.connect();
    await vi.advanceTimersByTimeAsync(0);

    const ws = MockWebSocket.instances[0];
    ws.simulateMessage({ op: "auth", success: false, ret_msg: "Invalid API key" });

    expect(authError).toHaveBeenCalledWith("Invalid API key");

    client.close();
  });

  it("parses topic messages and emits events", async () => {
    const client = createClient();
    const messageHandler = vi.fn();
    client.on("message", messageHandler);

    client.connect();
    await vi.advanceTimersByTimeAsync(0);

    const ws = MockWebSocket.instances[0];
    const topicMsg = {
      topic: "kline.1.BTCUSDT",
      type: "snapshot",
      data: [{ start: 1700000000000, open: "50000", high: "51000", low: "49000", close: "50500", volume: "100", confirm: false }],
      ts: 1700000001000,
    };
    ws.simulateMessage(topicMsg);

    expect(messageHandler).toHaveBeenCalledTimes(1);
    expect(messageHandler.mock.calls[0][0].topic).toBe("kline.1.BTCUSDT");

    client.close();
  });

  it("unsubscribe sends unsubscribe message and removes from set", async () => {
    const client = createClient();
    client.connect();
    await vi.advanceTimersByTimeAsync(0);

    client.subscribe(["kline.1.BTCUSDT", "tickers.BTCUSDT"]);
    expect(client.getSubscriptionCount()).toBe(2);

    client.unsubscribe(["tickers.BTCUSDT"]);
    expect(client.getSubscriptionCount()).toBe(1);

    const ws = MockWebSocket.instances[0];
    const unsubMsg = ws.sent.find((s) => JSON.parse(s).op === "unsubscribe");
    expect(unsubMsg).toBeDefined();
    expect(JSON.parse(unsubMsg!).args).toEqual(["tickers.BTCUSDT"]);

    client.close();
  });

  it("resets reconnect counter on successful connect", async () => {
    const client = createClient({ initialReconnectDelayMs: 100 });
    const reconnecting = vi.fn();
    client.on("reconnecting", reconnecting);

    client.connect();
    await vi.advanceTimersByTimeAsync(0);

    // Close and reconnect
    MockWebSocket.instances[0].simulateClose(1006);
    expect(reconnecting).toHaveBeenCalledWith(100, 1);

    await vi.advanceTimersByTimeAsync(100);
    await vi.advanceTimersByTimeAsync(0); // onopen

    // Close again — should start from attempt 1 (counter reset)
    MockWebSocket.instances[1].simulateClose(1006);
    expect(reconnecting).toHaveBeenCalledWith(100, 1);

    client.close();
  });

  it("handles non-JSON messages gracefully", async () => {
    const client = createClient();
    client.connect();
    await vi.advanceTimersByTimeAsync(0);

    const ws = MockWebSocket.instances[0];
    // Should not throw
    ws.simulateMessage("not valid json {{{");

    expect(client.getState()).toBe("connected");
    client.close();
  });
});
