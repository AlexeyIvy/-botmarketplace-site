/**
 * WsManager tests — Roadmap V3, Task #19
 *
 * Tests: singleton lifecycle, start/stop, private instance management.
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

import {
  startPublicWs,
  getPublicWs,
  startPrivateWs,
  getPrivateWs,
  stopPrivateWs,
  stopAllWs,
  _resetForTest,
} from "../../src/lib/ws/WsManager.js";

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("WsManager", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    MockWebSocket.instances = [];
    (globalThis as unknown as Record<string, unknown>).WebSocket = MockWebSocket as unknown as typeof WebSocket;
    _resetForTest();
  });

  afterEach(() => {
    vi.useRealTimers();
    (globalThis as unknown as Record<string, unknown>).WebSocket = OriginalWebSocket;
    _resetForTest();
  });

  it("startPublicWs creates singleton", async () => {
    const ws1 = startPublicWs();
    const ws2 = startPublicWs();

    expect(ws1).toBe(ws2); // same instance
    expect(MockWebSocket.instances.length).toBe(1);

    stopAllWs();
  });

  it("getPublicWs returns null before start", () => {
    expect(getPublicWs()).toBeNull();
  });

  it("getPublicWs returns instance after start", () => {
    startPublicWs();
    expect(getPublicWs()).not.toBeNull();
    stopAllWs();
  });

  it("startPrivateWs creates per-connection instances", async () => {
    const ws1 = startPrivateWs("conn-1", "key1", "secret1");
    const ws2 = startPrivateWs("conn-2", "key2", "secret2");

    expect(ws1).not.toBe(ws2);
    expect(MockWebSocket.instances.length).toBe(2);

    // Same connection ID returns existing
    const ws1again = startPrivateWs("conn-1", "key1", "secret1");
    expect(ws1again).toBe(ws1);

    stopAllWs();
  });

  it("getPrivateWs returns null for unknown connection", () => {
    expect(getPrivateWs("nonexistent")).toBeNull();
  });

  it("getPrivateWs returns instance after start", () => {
    startPrivateWs("conn-1", "key", "secret");
    expect(getPrivateWs("conn-1")).not.toBeNull();
    stopAllWs();
  });

  it("stopPrivateWs removes specific connection", () => {
    startPrivateWs("conn-1", "key1", "secret1");
    startPrivateWs("conn-2", "key2", "secret2");

    stopPrivateWs("conn-1");

    expect(getPrivateWs("conn-1")).toBeNull();
    expect(getPrivateWs("conn-2")).not.toBeNull();

    stopAllWs();
  });

  it("stopAllWs clears everything", () => {
    startPublicWs();
    startPrivateWs("conn-1", "key1", "secret1");
    startPrivateWs("conn-2", "key2", "secret2");

    stopAllWs();

    expect(getPublicWs()).toBeNull();
    expect(getPrivateWs("conn-1")).toBeNull();
    expect(getPrivateWs("conn-2")).toBeNull();
  });
});
