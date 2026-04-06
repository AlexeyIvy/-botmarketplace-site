/**
 * Bybit private WS channels: execution reports, position updates.
 *
 * Private endpoint: wss://stream.bybit.com/v5/private
 * Requires HMAC auth on connect.
 *
 * Channels:
 *   - execution            (order fills, status changes)
 *   - position             (position updates)
 *
 * Roadmap V3, Task #19 — Slice B.
 */

import { EventEmitter } from "node:events";
import { BybitWsClient, type BybitWsMessage } from "./BybitWsClient.js";
import { logger } from "../logger.js";

const privLog = logger.child({ module: "bybit-ws-private" });

// ---------------------------------------------------------------------------
// URLs
// ---------------------------------------------------------------------------

export const BYBIT_PRIVATE_WS_URL =
  process.env.BYBIT_PRIVATE_WS_URL ?? "wss://stream.bybit.com/v5/private";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ExecutionReport {
  symbol: string;
  orderId: string;
  orderLinkId: string;
  side: "Buy" | "Sell";
  orderType: string;
  orderStatus: string;
  execType: string;
  execQty: number;
  execPrice: number;
  execFee: number;
  leavesQty: number;
  cumExecQty: number;
  cumExecValue: number;
  cumExecFee: number;
  createdTime: number;
  updatedTime: number;
}

export interface PositionUpdate {
  symbol: string;
  side: "Buy" | "Sell" | "None";
  size: number;
  entryPrice: number;
  unrealisedPnl: number;
  markPrice: number;
  leverage: number;
  updatedTime: number;
}

// ---------------------------------------------------------------------------
// Private channel handler
// ---------------------------------------------------------------------------

export class BybitPrivateWs extends EventEmitter {
  private client: BybitWsClient;

  constructor(apiKey: string, apiSecret: string, url?: string) {
    super();
    this.client = new BybitWsClient({
      url: url ?? BYBIT_PRIVATE_WS_URL,
      auth: { apiKey, apiSecret },
    });
    this.client.on("message", (msg: BybitWsMessage) => this.route(msg));
    this.client.on("connected", () => this.emit("connected"));
    this.client.on("authenticated", () => {
      privLog.info("Private WS authenticated — subscribing to channels");
      this.subscribeDefaults();
      this.emit("authenticated");
    });
    this.client.on("authError", (reason: string) => {
      privLog.error({ reason }, "Private WS auth failed");
      this.emit("authError", reason);
    });
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

  private subscribeDefaults(): void {
    this.client.subscribe(["execution", "position"]);
  }

  // -------------------------------------------------------------------------
  // Message routing
  // -------------------------------------------------------------------------

  private route(msg: BybitWsMessage): void {
    if (!msg.topic) return;

    try {
      if (msg.topic === "execution") {
        this.handleExecution(msg);
      } else if (msg.topic === "position") {
        this.handlePosition(msg);
      }
    } catch (err) {
      privLog.error({ err, topic: msg.topic }, "Error handling private WS message");
    }
  }

  // -------------------------------------------------------------------------
  // Parsers
  // -------------------------------------------------------------------------

  private handleExecution(msg: BybitWsMessage): void {
    const items = msg.data as Array<{
      symbol: string;
      orderId: string;
      orderLinkId: string;
      side: "Buy" | "Sell";
      orderType: string;
      orderStatus: string;
      execType: string;
      execQty: string;
      execPrice: string;
      execFee: string;
      leavesQty: string;
      cumExecQty: string;
      cumExecValue: string;
      cumExecFee: string;
      createdTime: string;
      updatedTime: string;
    }>;
    if (!Array.isArray(items)) return;

    for (const item of items) {
      const report: ExecutionReport = {
        symbol: item.symbol,
        orderId: item.orderId,
        orderLinkId: item.orderLinkId,
        side: item.side,
        orderType: item.orderType,
        orderStatus: item.orderStatus,
        execType: item.execType,
        execQty: Number(item.execQty),
        execPrice: Number(item.execPrice),
        execFee: Number(item.execFee),
        leavesQty: Number(item.leavesQty),
        cumExecQty: Number(item.cumExecQty),
        cumExecValue: Number(item.cumExecValue),
        cumExecFee: Number(item.cumExecFee),
        createdTime: Number(item.createdTime),
        updatedTime: Number(item.updatedTime),
      };
      this.emit("execution", report);
    }
  }

  private handlePosition(msg: BybitWsMessage): void {
    const items = msg.data as Array<{
      symbol: string;
      side: "Buy" | "Sell" | "None";
      size: string;
      entryPrice: string;
      unrealisedPnl: string;
      markPrice: string;
      leverage: string;
      updatedTime: string;
    }>;
    if (!Array.isArray(items)) return;

    for (const item of items) {
      const pos: PositionUpdate = {
        symbol: item.symbol,
        side: item.side,
        size: Number(item.size),
        entryPrice: Number(item.entryPrice),
        unrealisedPnl: Number(item.unrealisedPnl),
        markPrice: Number(item.markPrice),
        leverage: Number(item.leverage),
        updatedTime: Number(item.updatedTime),
      };
      this.emit("position", pos);
    }
  }
}
