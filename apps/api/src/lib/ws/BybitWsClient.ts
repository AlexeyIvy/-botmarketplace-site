/**
 * Core Bybit WebSocket client with automatic reconnection and heartbeat.
 *
 * Uses Node.js built-in WebSocket (Node 22+).
 * Bybit WS V5 requires:
 *   - Ping every 20s to keep connection alive
 *   - Reconnect on disconnect with exponential backoff
 *
 * Roadmap V3, Task #19.
 */

import { EventEmitter } from "node:events";
import { createHmac } from "node:crypto";
import { logger } from "../logger.js";

const wsLog = logger.child({ module: "bybit-ws" });

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface BybitWsClientOptions {
  /** WebSocket URL (e.g. wss://stream.bybit.com/v5/public/linear) */
  url: string;
  /** If true, authenticate on connect (private channels) */
  auth?: { apiKey: string; apiSecret: string };
  /** Ping interval in ms (default: 20_000) */
  pingIntervalMs?: number;
  /** Max reconnect delay in ms (default: 30_000) */
  maxReconnectDelayMs?: number;
  /** Initial reconnect delay in ms (default: 1_000) */
  initialReconnectDelayMs?: number;
  /** Pong timeout in ms — if no pong within this, reconnect (default: 10_000) */
  pongTimeoutMs?: number;
}

export interface BybitWsMessage {
  topic?: string;
  type?: string;
  data?: unknown;
  ts?: number;
  op?: string;
  success?: boolean;
  ret_msg?: string;
  conn_id?: string;
}

type WsState = "disconnected" | "connecting" | "connected" | "closing";

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

export class BybitWsClient extends EventEmitter {
  private ws: WebSocket | null = null;
  private state: WsState = "disconnected";
  private reconnectAttempt = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private pingTimer: ReturnType<typeof setInterval> | null = null;
  private pongTimer: ReturnType<typeof setTimeout> | null = null;
  private subscriptions: Set<string> = new Set();
  private intentionalClose = false;

  readonly url: string;
  private readonly auth?: { apiKey: string; apiSecret: string };
  private readonly pingIntervalMs: number;
  private readonly maxReconnectDelayMs: number;
  private readonly initialReconnectDelayMs: number;
  private readonly pongTimeoutMs: number;

  constructor(options: BybitWsClientOptions) {
    super();
    this.url = options.url;
    this.auth = options.auth;
    this.pingIntervalMs = options.pingIntervalMs ?? 20_000;
    this.maxReconnectDelayMs = options.maxReconnectDelayMs ?? 30_000;
    this.initialReconnectDelayMs = options.initialReconnectDelayMs ?? 1_000;
    this.pongTimeoutMs = options.pongTimeoutMs ?? 10_000;
  }

  /** Current connection state. */
  getState(): WsState {
    return this.state;
  }

  /** Number of active subscriptions. */
  getSubscriptionCount(): number {
    return this.subscriptions.size;
  }

  // -------------------------------------------------------------------------
  // Connection lifecycle
  // -------------------------------------------------------------------------

  connect(): void {
    if (this.state === "connected" || this.state === "connecting") return;
    this.intentionalClose = false;
    this.state = "connecting";
    this.doConnect();
  }

  private doConnect(): void {
    try {
      this.ws = new WebSocket(this.url);
    } catch (err) {
      wsLog.error({ err, url: this.url }, "WebSocket constructor failed");
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      this.state = "connected";
      this.reconnectAttempt = 0;
      wsLog.info({ url: this.url }, "WebSocket connected");
      this.startHeartbeat();
      this.emit("connected");

      // Authenticate if private channel
      if (this.auth) {
        this.authenticate();
      }

      // Re-subscribe to all channels
      if (this.subscriptions.size > 0) {
        this.sendSubscribe([...this.subscriptions]);
      }
    };

    this.ws.onmessage = (event: MessageEvent) => {
      this.handleMessage(event.data);
    };

    this.ws.onerror = (event: Event) => {
      wsLog.error({ url: this.url, event: String(event) }, "WebSocket error");
      this.emit("error", event);
    };

    this.ws.onclose = (event: CloseEvent) => {
      this.state = "disconnected";
      this.stopHeartbeat();
      wsLog.warn(
        { url: this.url, code: event.code, reason: event.reason },
        "WebSocket closed",
      );
      this.emit("disconnected", event.code, event.reason);

      if (!this.intentionalClose) {
        this.scheduleReconnect();
      }
    };
  }

  /** Gracefully close the connection. */
  close(): void {
    this.intentionalClose = true;
    this.state = "closing";
    this.stopHeartbeat();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close(1000, "Client closing");
      this.ws = null;
    }
    this.state = "disconnected";
    this.subscriptions.clear();
  }

  // -------------------------------------------------------------------------
  // Reconnection
  // -------------------------------------------------------------------------

  private scheduleReconnect(): void {
    if (this.intentionalClose) return;

    const delay = Math.min(
      this.initialReconnectDelayMs * Math.pow(2, this.reconnectAttempt),
      this.maxReconnectDelayMs,
    );
    this.reconnectAttempt++;

    wsLog.info(
      { delay, attempt: this.reconnectAttempt, url: this.url },
      "Scheduling WebSocket reconnect",
    );

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.state = "connecting";
      this.doConnect();
    }, delay);

    this.emit("reconnecting", delay, this.reconnectAttempt);
  }

  // -------------------------------------------------------------------------
  // Heartbeat (ping/pong)
  // -------------------------------------------------------------------------

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.pingTimer = setInterval(() => {
      this.sendPing();
    }, this.pingIntervalMs);
  }

  private stopHeartbeat(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
    if (this.pongTimer) {
      clearTimeout(this.pongTimer);
      this.pongTimer = null;
    }
  }

  private sendPing(): void {
    if (this.state !== "connected" || !this.ws) return;

    try {
      this.ws.send(JSON.stringify({ op: "ping" }));
    } catch {
      wsLog.warn("Failed to send ping");
      return;
    }

    // Set pong timeout — if no pong received, force reconnect
    this.pongTimer = setTimeout(() => {
      wsLog.warn({ url: this.url }, "Pong timeout — reconnecting");
      this.pongTimer = null;
      this.forceReconnect();
    }, this.pongTimeoutMs);
  }

  private handlePong(): void {
    if (this.pongTimer) {
      clearTimeout(this.pongTimer);
      this.pongTimer = null;
    }
  }

  /** Force close + reconnect. */
  private forceReconnect(): void {
    this.stopHeartbeat();
    if (this.ws) {
      try {
        this.ws.close();
      } catch {
        // ignore
      }
      this.ws = null;
    }
    this.state = "disconnected";
    this.scheduleReconnect();
  }

  // -------------------------------------------------------------------------
  // Authentication (private channels)
  // -------------------------------------------------------------------------

  private authenticate(): void {
    if (!this.auth || !this.ws) return;

    const expires = Date.now() + 10_000; // 10s validity
    const signPayload = `GET/realtime${expires}`;
    const signature = createHmac("sha256", this.auth.apiSecret)
      .update(signPayload)
      .digest("hex");

    const authMsg = {
      op: "auth",
      args: [this.auth.apiKey, expires, signature],
    };

    this.ws.send(JSON.stringify(authMsg));
    wsLog.info("Sent WebSocket auth request");
  }

  // -------------------------------------------------------------------------
  // Subscriptions
  // -------------------------------------------------------------------------

  subscribe(topics: string[]): void {
    for (const t of topics) {
      this.subscriptions.add(t);
    }
    if (this.state === "connected") {
      this.sendSubscribe(topics);
    }
  }

  unsubscribe(topics: string[]): void {
    for (const t of topics) {
      this.subscriptions.delete(t);
    }
    if (this.state === "connected" && this.ws) {
      const msg = { op: "unsubscribe", args: topics };
      this.ws.send(JSON.stringify(msg));
    }
  }

  private sendSubscribe(topics: string[]): void {
    if (!this.ws || topics.length === 0) return;
    const msg = { op: "subscribe", args: topics };
    this.ws.send(JSON.stringify(msg));
    wsLog.info({ topics }, "Subscribed to WS topics");
  }

  // -------------------------------------------------------------------------
  // Message handling
  // -------------------------------------------------------------------------

  private handleMessage(raw: unknown): void {
    const text = typeof raw === "string" ? raw : String(raw);

    let parsed: BybitWsMessage;
    try {
      parsed = JSON.parse(text);
    } catch {
      wsLog.warn({ raw: text.slice(0, 200) }, "Non-JSON WS message");
      return;
    }

    // Pong response
    if (parsed.op === "pong" || parsed.ret_msg === "pong") {
      this.handlePong();
      this.emit("pong");
      return;
    }

    // Auth response
    if (parsed.op === "auth") {
      if (parsed.success) {
        wsLog.info("WebSocket auth successful");
        this.emit("authenticated");
      } else {
        wsLog.error({ msg: parsed.ret_msg }, "WebSocket auth failed");
        this.emit("authError", parsed.ret_msg);
      }
      return;
    }

    // Subscription confirmation
    if (parsed.op === "subscribe") {
      if (parsed.success) {
        this.emit("subscribed", parsed.ret_msg);
      } else {
        wsLog.warn({ msg: parsed.ret_msg }, "Subscription failed");
        this.emit("subscribeError", parsed.ret_msg);
      }
      return;
    }

    // Topic data
    if (parsed.topic) {
      this.emit("message", parsed);
      this.emit(`topic:${parsed.topic}`, parsed);
      return;
    }

    // Unknown message
    this.emit("message", parsed);
  }
}
