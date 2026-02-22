"use client";

import { useState, useEffect } from "react";
import { apiFetchNoWorkspace, apiFetch } from "../factory/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Ticker {
  symbol: string;
  lastPrice: number;
  bidPrice: number;
  askPrice: number;
  prevPrice24h: number;
  price24hPcnt: number;
  highPrice24h: number;
  lowPrice24h: number;
  volume24h: number;
}

interface Candle {
  openTime: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface ExchangeConnection {
  id: string;
  name: string;
  exchange: string;
  status: string;
}

interface TerminalOrder {
  id: string;
  symbol: string;
  side: string;
  type: string;
  qty: string;
  price: string | null;
  status: string;
  exchangeOrderId: string | null;
  error: string | null;
  createdAt: string;
}

type LoadState = "idle" | "loading" | "success" | "error";
type OrderState = "idle" | "loading" | "success" | "error";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const INTERVALS = ["1", "5", "15", "30", "60", "240", "D"] as const;
const DEFAULT_SYMBOL = "BTCUSDT";
const DEFAULT_INTERVAL = "15";

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function TerminalPage() {
  // --- Market Data state ---
  const [symbol, setSymbol] = useState(DEFAULT_SYMBOL);
  const [interval, setInterval] = useState(DEFAULT_INTERVAL);
  const [limit, setLimit] = useState("50");

  const [tickerState, setTickerState] = useState<LoadState>("idle");
  const [ticker, setTicker] = useState<Ticker | null>(null);
  const [tickerError, setTickerError] = useState<string | null>(null);

  const [candlesState, setCandlesState] = useState<LoadState>("idle");
  const [candles, setCandles] = useState<Candle[]>([]);
  const [candlesError, setCandlesError] = useState<string | null>(null);

  // --- Order state ---
  const [connections, setConnections] = useState<ExchangeConnection[]>([]);
  const [selectedConnection, setSelectedConnection] = useState("");
  const [orderSide, setOrderSide] = useState<"BUY" | "SELL">("BUY");
  const [orderType, setOrderType] = useState<"MARKET" | "LIMIT">("MARKET");
  const [orderQty, setOrderQty] = useState("");
  const [orderPrice, setOrderPrice] = useState("");
  const [orderState, setOrderState] = useState<OrderState>("idle");
  const [lastOrder, setLastOrder] = useState<TerminalOrder | null>(null);
  const [orderError, setOrderError] = useState<string | null>(null);

  // Load exchange connections on mount
  useEffect(() => {
    apiFetch<ExchangeConnection[]>("/exchanges").then((res) => {
      if (res.ok) {
        setConnections(res.data);
        if (res.data.length > 0) setSelectedConnection(res.data[0].id);
      }
    });
  }, []);

  // --- Market Data actions ---

  async function loadTicker() {
    const sym = symbol.trim().toUpperCase();
    if (!sym) return;
    setTickerState("loading");
    setTickerError(null);
    setTicker(null);

    const res = await apiFetchNoWorkspace<Ticker>(
      `/terminal/ticker?symbol=${encodeURIComponent(sym)}`,
    );
    if (res.ok) {
      setTicker(res.data);
      setTickerState("success");
    } else {
      setTickerError(`${res.problem.title}: ${res.problem.detail}`);
      setTickerState("error");
    }
  }

  async function loadCandles() {
    const sym = symbol.trim().toUpperCase();
    if (!sym) return;
    setCandlesState("loading");
    setCandlesError(null);
    setCandles([]);

    const lim = Math.min(Math.max(1, Number(limit) || 50), 1000);
    const res = await apiFetchNoWorkspace<Candle[]>(
      `/terminal/candles?symbol=${encodeURIComponent(sym)}&interval=${interval}&limit=${lim}`,
    );
    if (res.ok) {
      setCandles(res.data);
      setCandlesState("success");
    } else {
      setCandlesError(`${res.problem.title}: ${res.problem.detail}`);
      setCandlesState("error");
    }
  }

  async function loadAll() {
    await Promise.all([loadTicker(), loadCandles()]);
  }

  // --- Order actions ---

  async function submitOrder() {
    if (!selectedConnection) {
      setOrderError("Select an exchange connection first");
      setOrderState("error");
      return;
    }
    const sym = symbol.trim().toUpperCase() || DEFAULT_SYMBOL;
    const qty = Number(orderQty);
    if (!Number.isFinite(qty) || qty <= 0) {
      setOrderError("Quantity must be a positive number");
      setOrderState("error");
      return;
    }
    if (orderType === "LIMIT") {
      const pr = Number(orderPrice);
      if (!Number.isFinite(pr) || pr <= 0) {
        setOrderError("Price must be a positive number for LIMIT orders");
        setOrderState("error");
        return;
      }
    }

    setOrderState("loading");
    setOrderError(null);
    setLastOrder(null);

    const body: Record<string, unknown> = {
      exchangeConnectionId: selectedConnection,
      symbol: sym,
      side: orderSide,
      type: orderType,
      qty,
    };
    if (orderType === "LIMIT") body.price = Number(orderPrice);

    const res = await apiFetch<TerminalOrder>("/terminal/orders", {
      method: "POST",
      body: JSON.stringify(body),
    });

    if (res.ok) {
      setLastOrder(res.data);
      setOrderState("success");
    } else {
      setOrderError(`${res.problem.title}: ${res.problem.detail}`);
      setOrderState("error");
    }
  }

  async function refreshOrderStatus() {
    if (!lastOrder) return;
    const res = await apiFetch<TerminalOrder>(`/terminal/orders/${lastOrder.id}`);
    if (res.ok) setLastOrder(res.data);
  }

  // --- Helpers ---

  function pctColor(pct: number) {
    if (pct > 0) return "#3fb950";
    if (pct < 0) return "#f85149";
    return "var(--text-secondary)";
  }

  function fmt(n: number) {
    return n.toLocaleString(undefined, { maximumFractionDigits: 6 });
  }

  const loading = tickerState === "loading" || candlesState === "loading";

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div style={{ padding: "32px 24px", maxWidth: 960, margin: "0 auto" }}>
      <h1 style={{ fontSize: 26, marginBottom: 24 }}>Terminal — Market Data</h1>

      {/* ── Controls ── */}
      <div style={{ ...card, marginBottom: 20 }}>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <input
            style={{ ...input, width: 140 }}
            placeholder="Symbol (e.g. BTCUSDT)"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            onKeyDown={(e) => e.key === "Enter" && loadAll()}
          />
          <select
            style={{ ...input, width: 100 }}
            value={interval}
            onChange={(e) => setInterval(e.target.value)}
          >
            {INTERVALS.map((iv) => (
              <option key={iv} value={iv}>
                {iv === "D" ? "1D" : `${iv}m`}
              </option>
            ))}
          </select>
          <input
            style={{ ...input, width: 80 }}
            type="number"
            min={1}
            max={1000}
            placeholder="Limit"
            value={limit}
            onChange={(e) => setLimit(e.target.value)}
          />
          <button style={btn} onClick={loadAll} disabled={loading}>
            {loading ? "Loading..." : "Load"}
          </button>
        </div>
      </div>

      {/* ── Ticker ── */}
      <div style={{ ...card, marginBottom: 20 }}>
        <h2 style={{ fontSize: 16, marginBottom: 12 }}>Ticker</h2>

        {tickerState === "idle" && (
          <p style={hint}>Select a symbol and click Load.</p>
        )}
        {tickerState === "loading" && <p style={hint}>Loading ticker...</p>}
        {tickerState === "error" && (
          <p style={{ color: "#f85149", fontSize: 13 }}>{tickerError}</p>
        )}
        {tickerState === "success" && ticker && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 12 }}>
            <TickerCell label="Last Price" value={fmt(ticker.lastPrice)} />
            <TickerCell label="Bid" value={fmt(ticker.bidPrice)} />
            <TickerCell label="Ask" value={fmt(ticker.askPrice)} />
            <TickerCell
              label="24h Change"
              value={`${(ticker.price24hPcnt * 100).toFixed(2)}%`}
              color={pctColor(ticker.price24hPcnt)}
            />
            <TickerCell label="24h High" value={fmt(ticker.highPrice24h)} />
            <TickerCell label="24h Low" value={fmt(ticker.lowPrice24h)} />
            <TickerCell label="24h Volume" value={fmt(ticker.volume24h)} />
            <TickerCell label="Prev Close" value={fmt(ticker.prevPrice24h)} />
          </div>
        )}
      </div>

      {/* ── Order Panel ── */}
      <div style={{ ...card, marginBottom: 20 }}>
        <h2 style={{ fontSize: 16, marginBottom: 14 }}>Place Order</h2>

        {connections.length === 0 ? (
          <p style={hint}>
            No exchange connections found. Create one in Exchange Connections before placing orders.
          </p>
        ) : (
          <>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "flex-end", marginBottom: 12 }}>
              {/* Connection selector */}
              <div>
                <div style={fieldLabel}>Connection</div>
                <select
                  style={{ ...input, width: 200 }}
                  value={selectedConnection}
                  onChange={(e) => setSelectedConnection(e.target.value)}
                >
                  {connections.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.exchange})
                    </option>
                  ))}
                </select>
              </div>

              {/* Side */}
              <div>
                <div style={fieldLabel}>Side</div>
                <div style={{ display: "flex", gap: 4 }}>
                  <button
                    style={{
                      ...sideBtn,
                      background: orderSide === "BUY" ? "#3fb950" : "var(--bg-secondary)",
                      color: orderSide === "BUY" ? "#fff" : "var(--text-primary)",
                    }}
                    onClick={() => setOrderSide("BUY")}
                  >
                    BUY
                  </button>
                  <button
                    style={{
                      ...sideBtn,
                      background: orderSide === "SELL" ? "#f85149" : "var(--bg-secondary)",
                      color: orderSide === "SELL" ? "#fff" : "var(--text-primary)",
                    }}
                    onClick={() => setOrderSide("SELL")}
                  >
                    SELL
                  </button>
                </div>
              </div>

              {/* Type */}
              <div>
                <div style={fieldLabel}>Type</div>
                <select
                  style={{ ...input, width: 110 }}
                  value={orderType}
                  onChange={(e) => setOrderType(e.target.value as "MARKET" | "LIMIT")}
                >
                  <option value="MARKET">Market</option>
                  <option value="LIMIT">Limit</option>
                </select>
              </div>

              {/* Qty */}
              <div>
                <div style={fieldLabel}>Qty</div>
                <input
                  style={{ ...input, width: 100 }}
                  type="number"
                  min={0}
                  step="any"
                  placeholder="e.g. 0.001"
                  value={orderQty}
                  onChange={(e) => setOrderQty(e.target.value)}
                />
              </div>

              {/* Price (LIMIT only) */}
              {orderType === "LIMIT" && (
                <div>
                  <div style={fieldLabel}>Price</div>
                  <input
                    style={{ ...input, width: 120 }}
                    type="number"
                    min={0}
                    step="any"
                    placeholder="e.g. 60000"
                    value={orderPrice}
                    onChange={(e) => setOrderPrice(e.target.value)}
                  />
                </div>
              )}

              {/* Submit */}
              <button
                style={{
                  ...btn,
                  background: orderSide === "BUY" ? "#3fb950" : "#f85149",
                  alignSelf: "flex-end",
                }}
                onClick={submitOrder}
                disabled={orderState === "loading"}
              >
                {orderState === "loading"
                  ? "Placing..."
                  : `${orderSide} ${orderType}`}
              </button>
            </div>

            {/* Order result */}
            {orderState === "error" && (
              <p style={{ color: "#f85149", fontSize: 13, marginTop: 8 }}>{orderError}</p>
            )}
            {orderState === "success" && lastOrder && (
              <div style={{ marginTop: 8 }}>
                <OrderStatusRow order={lastOrder} onRefresh={refreshOrderStatus} />
              </div>
            )}
          </>
        )}
      </div>

      {/* ── Candles ── */}
      <div style={card}>
        <h2 style={{ fontSize: 16, marginBottom: 12 }}>
          Candles{candlesState === "success" ? ` (${candles.length})` : ""}
        </h2>

        {candlesState === "idle" && <p style={hint}>Click Load to fetch candles.</p>}
        {candlesState === "loading" && <p style={hint}>Loading candles...</p>}
        {candlesState === "error" && (
          <p style={{ color: "#f85149", fontSize: 13 }}>{candlesError}</p>
        )}
        {candlesState === "success" && candles.length === 0 && (
          <p style={hint}>No candles returned.</p>
        )}
        {candlesState === "success" && candles.length > 0 && (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr>
                  {["Time", "Open", "High", "Low", "Close", "Volume"].map((h) => (
                    <th
                      key={h}
                      style={{
                        textAlign: "right",
                        padding: "4px 8px",
                        borderBottom: "1px solid var(--border)",
                        color: "var(--text-secondary)",
                        fontWeight: 600,
                      }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[...candles].reverse().map((c) => {
                  const bullish = c.close >= c.open;
                  return (
                    <tr key={c.openTime}>
                      <td style={td}>{new Date(c.openTime).toLocaleString()}</td>
                      <td style={td}>{fmt(c.open)}</td>
                      <td style={td}>{fmt(c.high)}</td>
                      <td style={td}>{fmt(c.low)}</td>
                      <td style={{ ...td, color: bullish ? "#3fb950" : "#f85149" }}>
                        {fmt(c.close)}
                      </td>
                      <td style={td}>{fmt(c.volume)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function TickerCell({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div style={{ padding: "10px 12px", background: "var(--bg-secondary)", borderRadius: 6 }}>
      <div style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 16, fontWeight: 600, color: color ?? "var(--text-primary)" }}>
        {value}
      </div>
    </div>
  );
}

function OrderStatusRow({
  order,
  onRefresh,
}: {
  order: TerminalOrder;
  onRefresh: () => void;
}) {
  const statusColors: Record<string, string> = {
    FILLED: "#3fb950",
    FAILED: "#f85149",
    REJECTED: "#f85149",
    SUBMITTED: "#e3b341",
    PARTIALLY_FILLED: "#e3b341",
    CANCELLED: "var(--text-secondary)",
    PENDING: "var(--text-secondary)",
  };
  const color = statusColors[order.status] ?? "var(--text-secondary)";

  return (
    <div
      style={{
        background: "var(--bg-secondary)",
        borderRadius: 6,
        padding: "10px 14px",
        fontSize: 13,
        display: "flex",
        flexWrap: "wrap",
        gap: 16,
        alignItems: "center",
      }}
    >
      <span style={{ fontWeight: 600, color }}>
        {order.status}
      </span>
      <span style={{ fontFamily: "monospace" }}>
        {order.side} {order.type} {order.qty} {order.symbol}
        {order.price ? ` @ ${order.price}` : ""}
      </span>
      {order.exchangeOrderId && (
        <span style={{ color: "var(--text-secondary)" }}>
          #{order.exchangeOrderId.slice(0, 12)}...
        </span>
      )}
      {order.error && (
        <span style={{ color: "#f85149" }}>{order.error}</span>
      )}
      {(order.status === "SUBMITTED" || order.status === "PARTIALLY_FILLED") && (
        <button style={{ ...btn, padding: "4px 10px", fontSize: 12 }} onClick={onRefresh}>
          Refresh
        </button>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const card: React.CSSProperties = {
  background: "var(--bg-card)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  padding: 16,
};

const input: React.CSSProperties = {
  padding: "8px 12px",
  background: "var(--bg-secondary)",
  border: "1px solid var(--border)",
  borderRadius: 6,
  color: "var(--text-primary)",
  fontSize: 14,
};

const btn: React.CSSProperties = {
  padding: "8px 20px",
  background: "var(--accent)",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  cursor: "pointer",
  fontSize: 14,
  fontWeight: 600,
};

const sideBtn: React.CSSProperties = {
  padding: "8px 16px",
  border: "1px solid var(--border)",
  borderRadius: 6,
  cursor: "pointer",
  fontSize: 13,
  fontWeight: 600,
};

const hint: React.CSSProperties = {
  color: "var(--text-secondary)",
  fontSize: 13,
};

const fieldLabel: React.CSSProperties = {
  fontSize: 11,
  color: "var(--text-secondary)",
  marginBottom: 4,
};

const td: React.CSSProperties = {
  padding: "4px 8px",
  textAlign: "right",
  borderBottom: "1px solid var(--border)",
  fontFamily: "monospace",
};
